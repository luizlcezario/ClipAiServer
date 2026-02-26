"""
API route handlers for clip generation endpoints.

This module defines the FastAPI endpoints for submitting clip generation
jobs and checking job status with WhisperX transcription support.
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest
from app.schemas.clip_response import ClipGenerationResponse, JobStatusResponse, ClipMetadata
from app.services.clip_generator import ClipGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clips", tags=["clips"])


@router.post(
    "/generate",
    response_model=ClipGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate clips from video",
    description="Submit a clip generation job with WhisperX transcription. Returns immediately with a job ID."
)
async def generate_clip(
    request: ClipGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ClipGenerationResponse:
    """
    Submit a clip generation job.

    This endpoint accepts a video file and submits it for asynchronous
    clip generation using WhisperX transcription and ClipsAI clip detection.
    Returns immediately with a job ID that can be used to check the status
    and retrieve generated clips.

    Args:
        request: Clip generation request parameters (video path, etc.)
        background_tasks: FastAPI background tasks for async processing
        db: Database session dependency

    Returns:
        ClipGenerationResponse: Job ID and status information

    Raises:
        HTTPException: If request validation fails
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create database record for the job
        clip_job = ClipJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            input_file=request.video_path,
            status_message="Aguardando processamento",
        )
        db.add(clip_job)
        db.commit()
        db.refresh(clip_job)

        # Add background task for clip generation
        generator = ClipGenerator(db)
        background_tasks.add_task(generator.generate_clip, job_id, request)

        logger.info(f"Clip generation job created: {job_id}")

        return ClipGenerationResponse(
            job_id=job_id,
            status=JobStatus.PENDING.value,
            message="Clip generation job queued successfully. Use /status/{job_id} to check progress.",
        )

    except Exception as e:
        logger.error(f"Failed to create clip generation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create clip generation job: {str(e)}",
        )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get clip generation job status",
    description="Check the status of a previously submitted clip generation job."
)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """
    Get the status of a clip generation job.

    Provides detailed information about job progress, including:
    - Current status (pending, processing, completed, failed)
    - Detailed status message showing current step
    - Generated clips metadata (when completed)
    - Error details (if failed)
    - Timestamps for creation, update, and completion

    Args:
        job_id: The unique job identifier returned from the generate endpoint
        db: Database session dependency

    Returns:
        JobStatusResponse: Current job status and details

    Raises:
        HTTPException: If job not found
    """
    try:
        job = db.query(ClipJob).filter(ClipJob.job_id == job_id).first()

        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Convert generated_clips to ClipMetadata objects if present
        generated_clips = None
        if job.generated_clips:
            generated_clips = [
                ClipMetadata(**clip) if isinstance(clip, dict) else clip
                for clip in (job.generated_clips if isinstance(job.generated_clips, list) else [])
            ]

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            status_message=job.status_message,
            generated_clips=generated_clips,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status",
        )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the API server is running and healthy."
)
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "message": "Clips AI Server is running",
    }
