"""
Pydantic response schemas for clip generation endpoints.

This module defines response schemas for clip generation API endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
                "status": "pending",
                "message": "Clip generation job queued successfully"
            }
        }


class JobStatusResponse(BaseModel):
    """
    Schema for job status response.

    Attributes:
        job_id: Unique identifier for the job
        status: Current status of the job
        output_file: Path to the generated clip file (if completed)
        error_message: Error message (if failed)
        created_at: Timestamp when job was created
        updated_at: Timestamp when job was last updated
        completed_at: Timestamp when job completed
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    output_file: Optional[str] = Field(None, description="Path to output clip file")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
