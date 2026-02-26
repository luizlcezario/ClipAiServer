"""
Clip generation service using clipsai library.

This module handles the actual clip generation process using the clipsai
library with WhisperX transcription and manages job status updates in the database.
"""

import logging
import os
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from clipsai import ClipFinder, Transcriber, MediaEditor, AudioVideoFile
from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest
from app.services.storage import StorageService
from app.services.transcriber import TranscriberService

logger = logging.getLogger(__name__)


class ClipGenerator:
    """Service for generating clips using clipsai library with WhisperX transcription."""

    def __init__(self, db: Session):
        """
        Initialize clip generator.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.storage = StorageService()
        self.transcriber = Transcriber()  # ClipsAI transcriber
        self.clip_finder = ClipFinder()  # ClipsAI clip finder
        self.media_editor = MediaEditor()  # ClipsAI media editor
        logger.info("ClipGenerator initialized with ClipsAI components")

    async def generate_clip(
        self,
        job_id: str,
        request: ClipGenerationRequest,
    ) -> None:
        """
        Generate clips asynchronously using ClipsAI with WhisperX transcription.

        This method is designed to run as a background task.

        Args:
            job_id: Unique identifier for the clip job
            request: Clip generation request parameters

        Note:
            This function updates the job status in the database throughout
            the generation process. Flow:
            1. Transcribe video using ClipsAI Transcriber
            2. Find clips using ClipsAI ClipFinder based on transcription
            3. Trim video for each detected clip
            4. Save results to database
        """
        try:
            # Update status to processing
            self._update_job_status(job_id, JobStatus.PROCESSING, "Iniciando transcrição")
            logger.info(f"Starting clip generation for job {job_id}")

            # Validate input file exists
            if not self.storage.file_exists(request.video_path):
                raise FileNotFoundError(f"Input video file not found: {request.video_path}")

            # Step 1: Transcribe video
            self._update_job_status(job_id, JobStatus.PROCESSING, "Transcrevendo vídeo...")
            logger.info(f"Transcribing video for job {job_id}")
            
            try:
                transcription = self.transcriber.transcribe(
                    audio_file_path=request.video_path
                )
                logger.info(f"Transcription completed for job {job_id}")
            except Exception as e:
                raise Exception(f"Transcription failed: {str(e)}")

            # Step 2: Find clips based on transcription
            self._update_job_status(job_id, JobStatus.PROCESSING, "Detectando clips...")
            logger.info(f"Finding clips for job {job_id}")
            
            try:
                clips = self.clip_finder.find_clips(transcription=transcription)
                logger.info(f"Found {len(clips)} clips for job {job_id}")
            except Exception as e:
                raise Exception(f"Clip finding failed: {str(e)}")

            if not clips:
                raise Exception("No clips detected in video")

            # Step 3: Trim and save clips
            self._update_job_status(job_id, JobStatus.PROCESSING, f"Gerando {len(clips)} clips...")
            
            generated_clips = []
            media_file = AudioVideoFile(request.video_path)

            for idx, clip in enumerate(clips, 1):
                try:
                    output_filename = f"clip_{job_id}_{idx:03d}.mp4"
                    output_path = self.storage.get_output_path(job_id, output_filename)
                    
                    # Ensure output directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    logger.info(
                        f"Trimming clip {idx}/{len(clips)}: "
                        f"start={clip.start_time:.2f}s, end={clip.end_time:.2f}s"
                    )
                    
                    # Trim video
                    self.media_editor.trim(
                        media_file=media_file,
                        start_time=clip.start_time,
                        end_time=clip.end_time,
                        trimmed_media_file_path=output_path,
                    )
                    
                    generated_clips.append({
                        "filename": output_filename,
                        "path": output_path,
                        "start_time": clip.start_time,
                        "end_time": clip.end_time,
                        "duration": clip.end_time - clip.start_time,
                    })
                    
                    logger.info(f"Clip {idx} saved: {output_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate clip {idx} for job {job_id}: {str(e)}")
                    # Continue with next clip instead of failing
                    continue

            if not generated_clips:
                raise Exception("Failed to generate any clips")

            # Update job with success
            self._update_job_success(job_id, generated_clips)
            logger.info(f"Clip generation completed for job {job_id} with {len(generated_clips)} clips")

        except Exception as e:
            logger.error(f"Clip generation failed for job {job_id}: {str(e)}")
            self._update_job_failure(job_id, str(e))

    def _update_job_status(self, job_id: str, status: JobStatus, message: str = "") -> None:
        """
        Update job status in database.

        Args:
            job_id: Unique job identifier
            status: New job status
            message: Optional status message for progress tracking
        """
        try:
            job = self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
            if job:
                job.status = status
                job.status_message = message
                job.updated_at = datetime.utcnow()
                self.db.commit()
                logger.debug(f"Job {job_id} status updated to {status}: {message}")
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}: {e}")
            self.db.rollback()

    def _update_job_success(self, job_id: str, generated_clips: List[dict]) -> None:
        """
        Mark job as completed with generated clips information.

        Args:
            job_id: Unique job identifier
            generated_clips: List of dictionaries with clip information
        """
        try:
            job = self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
            if job:
                job.status = JobStatus.COMPLETED
                job.status_message = f"Concluído: {len(generated_clips)} clips gerados"
                job.generated_clips = generated_clips  # Store clips metadata
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Job {job_id} marked as completed with {len(generated_clips)} clips")
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as completed: {e}")
            self.db.rollback()

    def _update_job_failure(self, job_id: str, error_message: str) -> None:
        """
        Mark job as failed with error message.

        Args:
            job_id: Unique job identifier
            error_message: Error message describing the failure
        """
        try:
            job = self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.status_message = f"Erro: {error_message}"
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Job {job_id} marked as failed")
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
            self.db.rollback()

    def get_job_status(self, job_id: str) -> Optional[ClipJob]:
        """
        Retrieve job status from database.

        Args:
            job_id: Unique job identifier

        Returns:
            ClipJob: Job details if found, None otherwise
        """
        return self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
