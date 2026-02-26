"""
Pydantic request schemas for clip generation endpoints.

This module defines validation schemas for incoming clip generation requests.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ClipGenerationRequest(BaseModel):
    """
    Schema for clip generation request.

    Attributes:
        video_path: Path to the input video file
        start_time: Start time in seconds (optional)
        end_time: End time in seconds (optional)
        title: Title for the generated clip (optional)
        description: Description for the generated clip (optional)
        tags: List of tags for the clip (optional)
    """
    video_path: str = Field(..., description="Path to the input video file")
    start_time: Optional[float] = Field(None, ge=0, description="Start time in seconds")
    end_time: Optional[float] = Field(None, ge=0, description="End time in seconds")
    title: Optional[str] = Field(None, max_length=256, description="Clip title")
    description: Optional[str] = Field(None, max_length=1024, description="Clip description")
    tags: Optional[List[str]] = Field(None, description="List of tags for the clip")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "video_path": "/path/to/video.mp4",
                "start_time": 10.5,
                "end_time": 45.2,
                "title": "Awesome Moment",
                "description": "A great clip from the video",
                "tags": ["gaming", "highlight"]
            }
        }
