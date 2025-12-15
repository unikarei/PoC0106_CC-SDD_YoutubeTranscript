"""
Database models for YouTube Transcription App
"""
from sqlalchemy import (
    Column, String, Integer, Text, BigInteger,
    DateTime, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class Job(Base):
    """
    Job model represents a transcription job
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    youtube_url = Column(String(2048), nullable=False)
    language = Column(String(10), nullable=False)
    model = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    audio_file = relationship("AudioFile", back_populates="job", uselist=False, cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="job", uselist=False, cascade="all, delete-orphan")
    corrected_transcript = relationship("CorrectedTranscript", back_populates="job", uselist=False, cascade="all, delete-orphan")
    qa_results = relationship("QaResult", back_populates="job", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'transcribing', 'correcting', 'completed', 'failed')",
            name="check_job_status"
        ),
        CheckConstraint(
            "language IN ('ja', 'en')",
            name="check_language"
        ),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_created_at", "created_at"),
    )


class AudioFile(Base):
    """
    AudioFile model represents extracted audio from YouTube
    """
    __tablename__ = "audio_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1024), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="audio_file")

    # Indexes
    __table_args__ = (
        Index("ix_audio_files_job_id", "job_id"),
    )


class Transcript(Base):
    """
    Transcript model represents transcribed text from audio
    """
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    language_detected = Column(String(10), nullable=True)
    transcription_model = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="transcript")

    # Indexes
    __table_args__ = (
        Index("ix_transcripts_job_id", "job_id"),
    )


class CorrectedTranscript(Base):
    """
    CorrectedTranscript model represents LLM-corrected transcription text
    """
    __tablename__ = "corrected_transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    corrected_text = Column(Text, nullable=False)
    original_text = Column(Text, nullable=False)
    correction_model = Column(String(50), nullable=True)
    changes_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="corrected_transcript")

    # Indexes
    __table_args__ = (
        Index("ix_corrected_transcripts_job_id", "job_id"),
    )


class QaResult(Base):
    """
    QaResult model represents Q&A entries associated with a job
    """

    __tablename__ = "qa_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    qa_model = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="qa_results")

    # Indexes
    __table_args__ = (
        Index("ix_qa_results_job_id", "job_id"),
    )
