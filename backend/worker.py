"""
Celery worker for YouTube Transcription App
Defines background tasks for audio extraction, transcription, and correction
"""
from celery import Celery
from celery.utils.log import get_task_logger
import os
from dotenv import load_dotenv

from database import SessionLocal
from models import Job
from backend.services.audio_extractor import AudioExtractor
from backend.services.transcription_service import TranscriptionService
from backend.services.correction_service import CorrectionService
from backend.services.job_manager import JobManager

load_dotenv()

# Initialize Celery app
celery_app = Celery(
    "youtube_transcription",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

# Load configuration from celery_config
celery_app.config_from_object("celery_config")

# Setup logger
logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="worker.transcription_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def transcription_task(self, job_id: str):
    """
    Background task for transcribing YouTube audio
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        dict: Result containing job_id and status
    """
    logger.info(f"Starting transcription task for job {job_id}")
    
    db = SessionLocal()
    job_manager = JobManager()
    
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"job_id": job_id, "status": "failed", "error": "Job not found"}
        
        # Update status to processing
        job_manager.update_job_status(job_id, "processing")
        job_manager.update_job_progress(job_id, 10)
        
        # Step 1: Extract audio from YouTube
        logger.info(f"Extracting audio for job {job_id}")
        audio_extractor = AudioExtractor()
        
        extraction_result = audio_extractor.extract_audio(
            job_id=job_id,
            youtube_url=job.youtube_url
        )
        
        if not extraction_result.success:
            logger.error(f"Audio extraction failed for job {job_id}: {extraction_result.error}")
            job_manager.update_job_status(job_id, "failed", extraction_result.error)
            return {"job_id": job_id, "status": "failed", "error": extraction_result.error}
        
        # Save audio file info
        job_manager.create_audio_file(
            job_id=job_id,
            file_path=extraction_result.audio_path,
            duration_seconds=extraction_result.duration_seconds,
            title=extraction_result.title,
            file_format=extraction_result.format,
            file_size_bytes=extraction_result.file_size_bytes
        )
        
        job_manager.update_job_progress(job_id, 40)
        
        # Step 2: Transcribe audio
        logger.info(f"Transcribing audio for job {job_id}")
        job_manager.update_job_status(job_id, "transcribing")
        
        transcription_service = TranscriptionService()
        transcription_result = transcription_service.transcribe_audio(
            audio_path=extraction_result.audio_path,
            language=job.language,
            model=job.model
        )
        
        if not transcription_result.success:
            logger.error(f"Transcription failed for job {job_id}: {transcription_result.error}")
            job_manager.update_job_status(job_id, "failed", transcription_result.error)
            return {"job_id": job_id, "status": "failed", "error": transcription_result.error}
        
        # Save transcript
        job_manager.save_job_result(
            job_id=job_id,
            transcript=transcription_result.text,
            metadata={
                "language_detected": transcription_result.language_detected,
                "model": job.model
            }
        )
        
        job_manager.update_job_progress(job_id, 100)
        job_manager.update_job_status(job_id, "completed")
        
        logger.info(f"Transcription task completed for job {job_id}")
        return {
            "job_id": job_id,
            "status": "completed",
            "transcript_length": len(transcription_result.text)
        }
        
    except Exception as exc:
        logger.error(f"Transcription task failed for job {job_id}: {exc}", exc_info=True)
        job_manager.update_job_status(job_id, "failed", str(exc))
        # Retry the task with exponential backoff
        raise self.retry(exc=exc)
    
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="worker.correction_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def correction_task(self, job_id: str, correction_model: str = "gpt-4o-mini"):
    """
    Background task for correcting transcription with LLM
    
    Args:
        job_id: Unique job identifier
        correction_model: LLM model to use for correction
    
    Returns:
        dict: Result containing job_id and corrected text
    """
    logger.info(f"Starting correction task for job {job_id}")
    
    db = SessionLocal()
    job_manager = JobManager()
    
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"job_id": job_id, "status": "failed", "error": "Job not found"}
        
        # Check if transcript exists
        if not job.transcript:
            logger.error(f"No transcript found for job {job_id}")
            job_manager.update_job_status(job_id, "failed", "No transcript available")
            return {"job_id": job_id, "status": "failed", "error": "No transcript available"}
        
        # Update status to correcting
        job_manager.update_job_status(job_id, "correcting")
        job_manager.update_job_progress(job_id, 10)
        
        # Perform LLM correction
        logger.info(f"Correcting transcript for job {job_id}")
        correction_service = CorrectionService()
        
        correction_result = correction_service.correct_transcript(
            transcript=job.transcript.text,
            language=job.language,
            model=correction_model
        )
        
        if not correction_result.success:
            logger.error(f"Correction failed for job {job_id}: {correction_result.error}")
            job_manager.update_job_status(job_id, "failed", correction_result.error)
            return {"job_id": job_id, "status": "failed", "error": correction_result.error}
        
        # Save corrected transcript
        from models import CorrectedTranscript
        corrected_transcript = CorrectedTranscript(
            job_id=job_id,
            corrected_text=correction_result.corrected_text,
            original_text=job.transcript.text,
            correction_model=correction_model,
            changes_summary=correction_result.changes_summary
        )
        db.add(corrected_transcript)
        db.commit()
        
        job_manager.update_job_progress(job_id, 100)
        job_manager.update_job_status(job_id, "completed")
        
        logger.info(f"Correction task completed for job {job_id}")
        return {
            "job_id": job_id,
            "status": "completed",
            "corrected_length": len(correction_result.corrected_text)
        }
        
    except Exception as exc:
        logger.error(f"Correction task failed for job {job_id}: {exc}", exc_info=True)
        job_manager.update_job_status(job_id, "failed", str(exc))
        # Retry the task with exponential backoff
        raise self.retry(exc=exc)
    
    finally:
        db.close()


if __name__ == "__main__":
    # Start worker when run directly
    celery_app.worker_main(["worker", "--loglevel=info"])
