"""
API route handlers for clip generation endpoints.

This module defines the FastAPI endpoints for submitting clip generation
jobs and checking job status with WhisperX transcription support.
"""

import uuid
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import zipfile
import io

from app.database import get_db
from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest
from app.schemas.clip_response import ClipGenerationResponse, JobStatusResponse, ClipMetadata
from app.services.clip_generator import ClipGenerator
from app.services.storage import StorageService

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


@router.get(
    "/download/{job_id}/{clip_index}",
    summary="Download a specific clip",
    description="Download a single clip from a completed clip generation job."
)
async def download_clip(
    job_id: str,
    clip_index: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Download a specific generated clip.

    Args:
        job_id: The unique job identifier
        clip_index: Index of the clip to download (0-based)
        db: Database session dependency

    Returns:
        FileResponse: The clip file for download

    Raises:
        HTTPException: If job not found, clip index invalid, or file not found
    """
    try:
        # Retrieve the job
        job = db.query(ClipJob).filter(ClipJob.job_id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Check if job is completed
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed. Current status: {job.status.value}",
            )

        # Get the generated clips
        if not job.generated_clips:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No clips found for this job",
            )

        clips_list = job.generated_clips if isinstance(job.generated_clips, list) else []

        # Validate clip index
        if clip_index < 0 or clip_index >= len(clips_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid clip index. Job has {len(clips_list)} clips (0-{len(clips_list)-1})",
            )

        # Get the clip metadata
        clip_metadata = clips_list[clip_index]
        clip_path = clip_metadata.get("path") if isinstance(clip_metadata, dict) else clip_metadata.path

        # Validate file exists
        clip_file = Path(clip_path)
        if not clip_file.exists():
            logger.error(f"Clip file not found: {clip_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clip file not found on server",
            )

        logger.info(f"Downloading clip {clip_index} from job {job_id}: {clip_path}")

        return FileResponse(
            path=clip_file,
            filename=clip_file.name,
            media_type="video/mp4",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download clip {clip_index} from job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download clip",
        )


@router.get(
    "/download-all/{job_id}",
    summary="Download all clips as ZIP",
    description="Download all generated clips from a completed job as a single ZIP file."
)
async def download_all_clips(
    job_id: str,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Download all clips from a job as a ZIP file.

    Args:
        job_id: The unique job identifier
        db: Database session dependency

    Returns:
        StreamingResponse: ZIP file containing all clips

    Raises:
        HTTPException: If job not found or clip files not found
    """
    try:
        # Retrieve the job
        job = db.query(ClipJob).filter(ClipJob.job_id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Check if job is completed
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed. Current status: {job.status.value}",
            )

        # Get the generated clips
        if not job.generated_clips:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No clips found for this job",
            )

        clips_list = job.generated_clips if isinstance(job.generated_clips, list) else []

        # Validate all clip files exist
        clip_files = []
        for idx, clip_metadata in enumerate(clips_list):
            clip_path = clip_metadata.get("path") if isinstance(clip_metadata, dict) else clip_metadata.path
            clip_file = Path(clip_path)
            
            if not clip_file.exists():
                logger.warning(f"Clip file not found: {clip_path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Clip file {clip_file.name} not found on server",
                )
            
            clip_files.append(clip_file)

        logger.info(f"Creating ZIP with {len(clip_files)} clips from job {job_id}")

        # Create ZIP file in memory
        def generate_zip():
            with zipfile.ZipFile(io.BytesIO(), 'w', zipfile.ZIP_DEFLATED) as zip_buffer:
                # Need to write to a BytesIO instead
                pass

        # Better approach: create ZIP in memory and stream it
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for clip_file in clip_files:
                # Add file to ZIP with relative path
                arcname = f"clips/{clip_file.name}"
                zip_file.write(clip_file, arcname=arcname)

        zip_buffer.seek(0)

        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=clips_{job_id}.zip"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download clips from job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ZIP file",
        )


@router.delete(
    "/delete/{job_id}",
    summary="Delete job and clips",
    description="Delete a completed job and all its generated clips from the server."
)
async def delete_job_clips(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete a job and all its generated clips.

    Args:
        job_id: The unique job identifier
        db: Database session dependency

    Returns:
        dict: Deletion status information

    Raises:
        HTTPException: If job not found
    """
    try:
        # Retrieve the job
        job = db.query(ClipJob).filter(ClipJob.job_id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        deleted_count = 0

        # Delete generated clip files
        if job.generated_clips:
            clips_list = job.generated_clips if isinstance(job.generated_clips, list) else []
            
            for clip_metadata in clips_list:
                clip_path = clip_metadata.get("path") if isinstance(clip_metadata, dict) else clip_metadata.path
                clip_file = Path(clip_path)
                
                try:
                    if clip_file.exists():
                        clip_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted clip file: {clip_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete clip file {clip_path}: {e}")

        # Delete input video file if it was downloaded from URL
        if job.input_file:
            try:
                input_file = Path(job.input_file)
                # Only delete if it's in temp_uploads (was downloaded from URL)
                if "temp_uploads" in str(input_file) and input_file.exists():
                    input_file.unlink()
                    logger.info(f"Deleted input video file: {job.input_file}")
            except OSError as e:
                logger.warning(f"Failed to delete input file {job.input_file}: {e}")

        # Delete job from database
        db.delete(job)
        db.commit()

        logger.info(f"Deleted job {job_id} and {deleted_count} clip files")

        return {
            "status": "success",
            "message": f"Job {job_id} deleted successfully",
            "clips_deleted": deleted_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job",
        )
