"""
Pydantic schemas for API request/response models
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, validator


class TranscribeJobRequest(BaseModel):
    """
    Request schema for creating a new transcription job
    """
    youtube_url: str = Field(..., description="YouTube video URL")
    language: str = Field(..., description="Target language (ja or en)")
    model: str = Field(default="gpt-4o-mini-transcribe", description="Transcription model")
    
    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        """Validate YouTube URL format"""
        if not v:
            raise ValueError('YouTube URL is required')
        
        valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        if not any(domain in v.lower() for domain in valid_domains):
            raise ValueError('Invalid YouTube URL')
        
        return v
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        if v not in ['ja', 'en']:
            raise ValueError('Language must be "ja" or "en"')
        return v
    
    @validator('model')
    def validate_model(cls, v):
        """Validate transcription model"""
        valid_models = ['gpt-4o-mini-transcribe', 'gpt-4o-transcribe']
        if v not in valid_models:
            raise ValueError(f'Model must be one of {valid_models}')
        return v


class TranscribeJobResponse(BaseModel):
    """
    Response schema for job creation
    """
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """
    Response schema for job status
    """
    job_id: str
    status: str
    progress: int
    youtube_url: str
    language: str
    model: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AudioFileInfo(BaseModel):
    """
    Audio file information
    """
    title: Optional[str] = None
    duration_seconds: Optional[int] = None
    format: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    class Config:
        from_attributes = True


class TranscriptInfo(BaseModel):
    """
    Transcript information
    """
    text: str
    language_detected: Optional[str] = None
    transcription_model: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CorrectedTranscriptInfo(BaseModel):
    """
    Corrected transcript information
    """
    corrected_text: str
    original_text: str
    correction_model: Optional[str] = None
    changes_summary: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobResultResponse(BaseModel):
    """
    Response schema for job result
    """
    job_id: str
    status: str
    model: Optional[str] = None
    audio_file: Optional[AudioFileInfo] = None
    transcript: Optional[TranscriptInfo] = None
    corrected_transcript: Optional[CorrectedTranscriptInfo] = None
    qa_results: Optional[List["QaResultInfo"]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class CorrectTranscriptRequest(BaseModel):
    """
    Request schema for LLM correction
    """
    correction_model: str = Field(default="gpt-4o-mini", description="LLM model for correction")
    
    @validator('correction_model')
    def validate_correction_model(cls, v):
        """Validate correction model"""
        valid_models = ['gpt-4o-mini', 'gpt-4o']
        if v not in valid_models:
            raise ValueError(f'Correction model must be one of {valid_models}')
        return v


class CorrectTranscriptResponse(BaseModel):
    """
    Response schema for correction request
    """
    job_id: str
    status: str
    message: str


class ProofreadRequest(BaseModel):
    proofread_model: str = Field(default="gpt-4o-mini", description="LLM model for proofreading")

    @validator('proofread_model')
    def validate_proofread_model(cls, v):
        valid_models = ['gpt-4o-mini', 'gpt-4o']
        if v not in valid_models:
            raise ValueError(f'Proofread model must be one of {valid_models}')
        return v


class ProofreadResponse(BaseModel):
    job_id: str
    status: str
    message: str


class QaRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question for QA")
    qa_model: str = Field(default="gpt-4o-mini", description="LLM model for QA")

    @validator('qa_model')
    def validate_qa_model(cls, v):
        valid_models = ['gpt-4o-mini', 'gpt-4o']
        if v not in valid_models:
            raise ValueError(f'QA model must be one of {valid_models}')
        return v


class QaResponse(BaseModel):
    job_id: str
    status: str
    message: str


class QaResultInfo(BaseModel):
    question: str
    answer: str
    qa_model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Resolve forward references (Pydantic v1/v2 compatible)
try:
    JobResultResponse.model_rebuild()
except AttributeError:
    JobResultResponse.update_forward_refs()


class HealthResponse(BaseModel):
    """
    Response schema for health check
    """
    status: str
    database: str
    redis: str
    timestamp: datetime
