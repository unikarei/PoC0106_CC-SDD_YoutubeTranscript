"""
Job management endpoints
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Job
from routers.schemas import (
    TranscribeJobRequest,
    TranscribeJobResponse,
    JobStatusResponse,
    JobResultResponse,
    CorrectTranscriptRequest,
    CorrectTranscriptResponse,
    ProofreadRequest,
    ProofreadResponse,
    QaRequest,
    QaResponse,
)
from services.job_manager import JobManager
from worker import transcription_task, correction_task, proofread_task, qa_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeJobResponse, status_code=status.HTTP_201_CREATED)
async def create_transcription_job(
    request: TranscribeJobRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Create a new transcription job
    
    Args:
        request: Job creation request
        db: Database session
        
    Returns:
        Job creation response with job ID
    """
    try:
        # Create job in database
        job_manager = JobManager(db)
        job = job_manager.create_job(
            youtube_url=request.youtube_url,
            language=request.language,
            model=request.model
        )
        
        # Submit job to task queue
        transcription_task.delay(job.id)
        
        logger.info(f"Created transcription job: {job.id}")
        
        return TranscribeJobResponse(
            job_id=job.id,
            status=job.status,
            message="Transcription job created successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transcription job"
        )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get job status
    
    Args:
        job_id: Job ID
        db: Database session
        
    Returns:
        Job status information
    """
    try:
        job_manager = JobManager(db)
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            youtube_url=job.youtube_url,
            language=job.language,
            model=job.model,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(
    job_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get job result including transcription
    
    Args:
        job_id: Job ID
        db: Database session
        
    Returns:
        Complete job result with transcript
    """
    try:
        job_manager = JobManager(db)
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Build response
        response = JobResultResponse(
            job_id=job.id,
            status=job.status,
            model=job.model,
            error_message=job.error_message
        )
        
        # Add audio file info if available
        if job.audio_file:
            response.audio_file = {
                "title": job.audio_file.title,
                "duration_seconds": job.audio_file.duration_seconds,
                "format": job.audio_file.format,
                "file_size_bytes": job.audio_file.file_size_bytes
            }
        
        # Add transcript if available
        if job.transcript:
            response.transcript = {
                "text": job.transcript.text,
                "language_detected": job.transcript.language_detected,
                "transcription_model": job.transcript.transcription_model,
                "created_at": job.transcript.created_at
            }
        
        # Add corrected transcript if available
        if job.corrected_transcript:
            response.corrected_transcript = {
                "corrected_text": job.corrected_transcript.corrected_text,
                "original_text": job.corrected_transcript.original_text,
                "correction_model": job.corrected_transcript.correction_model,
                "changes_summary": job.corrected_transcript.changes_summary,
                "created_at": job.corrected_transcript.created_at
            }

        if job.qa_results:
            response.qa_results = [
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "qa_model": qa.qa_model,
                    "created_at": qa.created_at,
                }
                for qa in job.qa_results
            ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job result"
        )


@router.post("/{job_id}/correct", response_model=CorrectTranscriptResponse)
async def correct_transcript(
    job_id: str,
    request: CorrectTranscriptRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Request LLM correction for transcript
    
    Args:
        job_id: Job ID
        request: Correction request
        db: Database session
        
    Returns:
        Correction request response
    """
    try:
        job_manager = JobManager(db)
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if transcription is complete
        if job.status not in ['completed', 'correcting']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcription not complete. Current status: {job.status}"
            )
        
        # Check if transcript exists
        if not job.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for correction"
            )
        
        # Update job status
        job_manager.update_job_status(job_id, "correcting")
        
        # Submit correction task
        correction_task.delay(job_id, request.correction_model)
        
        logger.info(f"Started correction for job: {job_id}")
        
        return CorrectTranscriptResponse(
            job_id=job_id,
            status="correcting",
            message="Correction task started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start correction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start correction task"
        )


@router.post("/{job_id}/proofread", response_model=ProofreadResponse)
async def proofread_transcript(
    job_id: str,
    request: ProofreadRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """Request proofreading for transcript"""
    try:
        job_manager = JobManager(db)
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        if job.status not in ['completed', 'correcting']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcription not complete. Current status: {job.status}"
            )

        if not job.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for proofreading"
            )

        job_manager.update_job_status(job_id, "correcting", 0)
        proofread_task.delay(job_id, request.proofread_model)

        logger.info(f"Started proofread for job: {job_id} with model {request.proofread_model}")

        return ProofreadResponse(
            job_id=job_id,
            status="correcting",
            message="Proofread task started successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start proofread: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start proofread task"
        )


@router.post("/{job_id}/qa", response_model=QaResponse)
async def qa_on_transcript(
    job_id: str,
    request: QaRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """Request QA generation based on transcript"""
    try:
        job_manager = JobManager(db)
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        if job.status not in ['completed', 'correcting']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcription not complete. Current status: {job.status}"
            )

        if not job.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for QA"
            )

        qa_task.delay(job_id, request.question, request.qa_model)

        logger.info(f"Started QA for job: {job_id} with model {request.qa_model}")

        return QaResponse(
            job_id=job_id,
            status="pending",
            message="QA task started successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start QA: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start QA task"
        )
