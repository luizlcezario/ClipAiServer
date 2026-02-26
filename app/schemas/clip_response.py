"""
Pydantic response schemas for clip generation endpoints.

This module defines response schemas for clip generation API endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ClipMetadata(BaseModel):
    """Metadata for a single generated clip."""
    filename: str = Field(..., description="Output filename")
    path: str = Field(..., description="Full path to clip file")
    start_time: float = Field(..., description="Clip start time in seconds")
    end_time: float = Field(..., description="Clip end time in seconds")
    duration: float = Field(..., description="Clip duration in seconds")


class ClipGenerationResponse(BaseModel):
    """
    Schema for clip generation response.

    Attributes:
        job_id: Unique identifier for the clip generation job
        status: Current status of the job
        message: Status message
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "message": "Clip generation job queued successfully"
            }
        }


class JobStatusResponse(BaseModel):
    """
    Schema for job status response.

    Attributes:
        job_id: Unique identifier for the job
        status: Current status of the job
        status_message: Detailed status message for progress tracking
        generated_clips: List of generated clip metadata (if completed)
        error_message: Error message (if failed)
        created_at: Timestamp when job was created
        updated_at: Timestamp when job was last updated
        completed_at: Timestamp when job completed
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    status_message: Optional[str] = Field(None, description="Detailed status message")
    generated_clips: Optional[List[ClipMetadata]] = Field(None, description="List of generated clips")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "status_message": "Concluído: 3 clips gerados",
                "generated_clips": [
                    {
                        "filename": "clip_550e8400-e29b-41d4-a716-446655440000_001.mp4",
                        "path": "/path/to/clip_001.mp4",
                        "start_time": 0.0,
                        "end_time": 5.5,
                        "duration": 5.5
                    }
                ],
                "error_message": None,
                "created_at": "2026-02-26T10:00:00",
                "updated_at": "2026-02-26T10:05:00",
                "completed_at": "2026-02-26T10:05:00"
            }
        }
