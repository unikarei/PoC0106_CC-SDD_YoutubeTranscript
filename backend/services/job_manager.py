"""
Job Manager Service
Handles job lifecycle, status updates, and database operations
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json

from database import SessionLocal
from models import Job, AudioFile, Transcript, CorrectedTranscript, QaResult

logger = logging.getLogger(__name__)


class JobManager:
    """
    Service for managing transcription jobs
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize JobManager
        
        Args:
            db: Optional database session. If not provided, creates new sessions for each operation.
        """
        self.db = db
        self._owns_session = db is None
    
    def _get_db(self) -> Session:
        """Get database session"""
        if self.db:
            return self.db
        return SessionLocal()
    
    def _close_db(self, db: Session):
        """Close database session if we own it"""
        if self._owns_session and db:
            db.close()
    
    def create_job(self, youtube_url: str, language: str, model: str) -> Job:
        """
        Create a new transcription job
        
        Args:
            youtube_url: YouTube video URL
            language: Target language (ja or en)
            model: Whisper model to use
            
        Returns:
            Job: Created job object
        """
        db = self._get_db()
        try:
            job = Job(
                youtube_url=youtube_url,
                language=language,
                model=model,
                status="pending",
                progress=0
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Created job {job.id} for {youtube_url}")
            return job
            
        finally:
            self._close_db(db)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object or None
        """
        db = self._get_db()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            return job
        finally:
            self._close_db(db)
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        stage: Optional[str] = None,
        stage_detail: Optional[Dict[str, Any]] = None,
    ):
        """
        Update job status
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Error message if status is failed
            stage: Optional granular stage (download_extract|preprocess|transcribe|merge|export)
            stage_detail: Optional structured detail (e.g., chunk index/count)
        """
        db = self._get_db()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = status
                if error_message:
                    job.error_message = error_message

                if stage is not None:
                    job.stage = stage

                if stage_detail is not None:
                    job.stage_detail = json.dumps(stage_detail, ensure_ascii=False)

                job.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Updated job {job_id} status to {status}")
            else:
                logger.warning(f"Job {job_id} not found")
                
        finally:
            self._close_db(db)
    
    def update_job_progress(self, job_id: str, progress: int, message: Optional[str] = None):
        """
        Update job progress
        
        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        db = self._get_db()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.progress = progress
                job.updated_at = datetime.utcnow()
                db.commit()
                
                logger.debug(f"Updated job {job_id} progress to {progress}%")
            else:
                logger.warning(f"Job {job_id} not found")
                
        finally:
            self._close_db(db)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status information
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict with job status info or None
        """
        db = self._get_db()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return None
            
            return {
                "job_id": job.id,
                "status": job.status,
                "stage": job.stage,
                "stage_detail": job.stage_detail,
                "progress": job.progress,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            
        finally:
            self._close_db(db)
    
    def create_audio_file(
        self,
        job_id: str,
        file_path: str,
        duration_seconds: int,
        title: str,
        file_format: str,
        file_size_bytes: Optional[int] = None
    ) -> str:
        """
        Create audio file record
        
        Args:
            job_id: Job identifier
            file_path: Path to audio file
            duration_seconds: Audio duration
            title: Video title
            file_format: Audio format (m4a, mp3, etc)
            file_size_bytes: File size in bytes
            
        Returns:
            str: Audio file ID
        """
        db = self._get_db()
        try:
            audio_file = AudioFile(
                job_id=job_id,
                file_path=file_path,
                duration_seconds=duration_seconds,
                title=title,
                format=file_format,
                file_size_bytes=file_size_bytes
            )
            db.add(audio_file)
            db.commit()
            db.refresh(audio_file)
            
            logger.info(f"Created audio file record {audio_file.id} for job {job_id}")
            return audio_file.id
            
        finally:
            self._close_db(db)
    
    def save_job_result(self, job_id: str, transcript: str, metadata: Dict[str, Any]):
        """
        Save transcription result
        
        Args:
            job_id: Job identifier
            transcript: Transcribed text
            metadata: Additional metadata
        """
        db = self._get_db()
        try:
            segments = metadata.get("segments")
            segments_json = None
            # Only persist segments when we actually have timestamped data.
            # Treat empty list as "no timestamps".
            if segments:
                try:
                    segments_json = json.dumps(segments, ensure_ascii=False)
                except TypeError:
                    # Best-effort fallback
                    segments_json = json.dumps(list(segments), ensure_ascii=False)

            transcript_record = Transcript(
                job_id=job_id,
                text=transcript,
                language_detected=metadata.get('language_detected'),
                transcription_model=metadata.get('model'),
                segments_json=segments_json,
            )
            db.add(transcript_record)
            db.commit()
            
            logger.info(f"Saved transcript for job {job_id}")
            
        finally:
            self._close_db(db)

    def upsert_corrected_transcript(
        self,
        job_id: str,
        corrected_text: str,
        original_text: str,
        correction_model: str,
        changes_summary: str,
    ) -> None:
        """Save or replace corrected transcript"""
        db = self._get_db()
        try:
            existing = db.query(CorrectedTranscript).filter(CorrectedTranscript.job_id == job_id).first()
            if existing:
                db.delete(existing)
                db.commit()

            corrected = CorrectedTranscript(
                job_id=job_id,
                corrected_text=corrected_text,
                original_text=original_text,
                correction_model=correction_model,
                changes_summary=changes_summary,
            )
            db.add(corrected)
            db.commit()
            logger.info(f"Upserted corrected transcript for job {job_id}")
        finally:
            self._close_db(db)

    def create_qa_result(self, job_id: str, question: str, answer: str, qa_model: str) -> str:
        """Persist QA result"""
        db = self._get_db()
        try:
            qa = QaResult(
                job_id=job_id,
                question=question,
                answer=answer,
                qa_model=qa_model,
            )
            db.add(qa)
            db.commit()
            db.refresh(qa)
            logger.info(f"Saved QA result for job {job_id}")
            return qa.id
        finally:
            self._close_db(db)
