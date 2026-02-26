"""
Database models for clip job tracking.

This module defines the ClipJob model for tracking the progress
and status of clip generation jobs with transcription and multi-clip support.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import declarative_base
from typing import Optional, List
import json


Base = declarative_base()


class JobStatus(str, Enum):
    """Enumeration for clip job status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipJob(Base):
    """
    Database model for tracking clip generation jobs.

    Attributes:
        id: Primary key
        job_id: Unique identifier for the job (UUID string)
        status: Current status of the job (pending, processing, completed, failed)
        input_file: Path to the input video file
        status_message: Detailed status message for progress tracking
        generated_clips: JSON array of generated clip metadata
        error_message: Error message if job failed
        created_at: Timestamp when job was created
        updated_at: Timestamp when job was last updated
        completed_at: Timestamp when job completed
    """
    __tablename__ = "clip_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    input_file = Column(String(255), nullable=False)
    status_message = Column(String(512), nullable=True, default="")
    generated_clips = Column(JSON, nullable=True, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """Return string representation of ClipJob."""
        return f"<ClipJob(id={self.id}, job_id={self.job_id}, status={self.status})>"

    def get_generated_clips(self) -> List[dict]:
        """
        Get list of generated clips.
        
        Returns:
            List of clip dictionaries with metadata
        """
        if isinstance(self.generated_clips, str):
            return json.loads(self.generated_clips) if self.generated_clips else []
        return self.generated_clips or []

    def set_generated_clips(self, clips: List[dict]) -> None:
        """
        Set generated clips metadata.
        
        Args:
            clips: List of clip dictionaries
        """
        self.generated_clips = clips
