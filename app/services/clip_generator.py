"""
Clip Generation Service

This module orchestrates the complete clip generation pipeline:
1. Download video from URL (if provided)
2. Transcribe video using ClipsAI Transcriber with WhisperX
3. Find clips using ClipsAI ClipFinder with TextTiling algorithm
4. Trim video for each detected clip using ClipsAI MediaEditor
5. Store results in database

Clean Architecture:
- Separation of concerns with dedicated service classes
- Each ClipsAI component in its own service module
- Async support for non-blocking operations
- Comprehensive error handling and logging
"""

import logging
import os
import asyncio
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest
from app.services.storage import StorageService
from app.services.downloader import AsyncVideoDownloader
from app.services.clipsai_transcriber_service import TranscriberService
from app.services.clipsai_clipfinder_service import ClipFinderService
from app.services.clipsai_mediaeditor_service import MediaEditorService

logger = logging.getLogger(__name__)


class ClipGenerator:
    """
    Orchestrates the complete clip generation pipeline.
    
    Pipeline stages:
    1. Download: Fetch video from URL if needed (async, non-blocking)
    2. Transcribe: Extract text and timestamps using WhisperX
    3. Detect: Find coherent clips using TextTiling + BERT
    4. Trim: Cut video for each detected clip
    5. Store: Save results to database
    
    Uses clean architecture with dedicated service classes for each component.
    All ClipsAI operations are real (no mocks) and follow documentation exactly.
    """

    def __init__(self, db: Session):
        """
        Initialize clip generator with all required services.

        Args:
            db: SQLAlchemy database session
        
        Raises:
            ImportError: If ClipsAI components are not installed
        """
        self.db = db
        self.storage = StorageService()
        self.downloader = AsyncVideoDownloader()
        
        # Initialize ClipsAI services - these will raise ImportError if ClipsAI not installed
        self.transcriber_service = TranscriberService()
        self.clipfinder_service = ClipFinderService()
        self.mediaeditor_service = MediaEditorService()
        
        logger.info("ClipGenerator initialized with all ClipsAI services")

    async def generate_clip(
        self,
        job_id: str,
        request: ClipGenerationRequest,
    ) -> None:
        """
        Generate clips asynchronously through complete pipeline.

        Pipeline:
        1. Download: Video from URL if provided (async, non-blocking)
        2. Transcribe: Using ClipsAI Transcriber with WhisperX
        3. Find Clips: Using ClipsAI ClipFinder with TextTiling algorithm
        4. Trim: Each detected clip using ClipsAI MediaEditor
        5. Store: Results to database with metadata

        Args:
            job_id: Unique identifier for the clip job
            request: Clip generation request parameters

        Raises:
            FileNotFoundError: If input video not found
            ImportError: If ClipsAI components not installed
            Exception: If any pipeline step fails
        
        Note:
            Updates job status in database throughout the process.
            All exceptions are caught and logged as job failures.
        """
        video_path = request.video_path
        
        try:
            # ===== STAGE 1: DOWNLOAD VIDEO (ASYNC, NON-BLOCKING) =====
            if self.downloader.is_url(video_path):
                self._update_job_status(
                    job_id,
                    JobStatus.PROCESSING,
                    "Baixando vídeo da web..."
                )
                logger.info(f"Stage 1: Downloading from URL: {video_path}")
                
                try:
                    video_path = await self.downloader.download_video(
                        url=video_path,
                        timeout=3600,  # 1 hour
                        max_size_mb=2048,
                    )
                    logger.info(f"Stage 1: Download complete: {video_path}")
                except Exception as e:
                    raise Exception(f"Download failed: {str(e)}")
            else:
                # Validate local file exists
                if not self.storage.file_exists(video_path):
                    raise FileNotFoundError(
                        f"Input video file not found: {video_path}"
                    )
                logger.info(f"Stage 1: Using local file: {video_path}")

            # Update job with downloaded video path
            job = self.db.query(ClipJob).filter(
                ClipJob.job_id == job_id
            ).first()
            if job:
                job.input_file = video_path
                self.db.commit()

            # ===== STAGE 2: TRANSCRIBE VIDEO =====
            self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                "Transcrevendo vídeo com WhisperX..."
            )
            logger.info(f"Stage 2: Starting transcription")
            
            try:
                transcription = self.transcriber_service.transcribe(
                    audio_file_path=video_path
                )
                logger.info(
                    f"Stage 2: Transcription complete. "
                    f"Language: {transcription.language}, "
                    f"Sentences: {len(transcription.sentences)}"
                )
            except Exception as e:
                raise Exception(f"Transcription failed: {str(e)}")

            # ===== STAGE 3: FIND CLIPS USING TEXTTILING =====
            self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                "Detectando clips com TextTiling..."
            )
            logger.info(f"Stage 3: Finding clips in transcription")
            
            try:
                clips = self.clipfinder_service.find_clips(
                    transcription=transcription
                )
                logger.info(f"Stage 3: Found {len(clips)} clips")
            except Exception as e:
                raise Exception(f"Clip finding failed: {str(e)}")

            if not clips:
                raise Exception("No clips detected in transcription")

            # ===== STAGE 4: TRIM VIDEO FOR EACH CLIP =====
            self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                f"Gerando {len(clips)} clips..."
            )
            logger.info(f"Stage 4: Trimming {len(clips)} clips")
            
            generated_clips = self._trim_clips(
                job_id=job_id,
                video_path=video_path,
                clips=clips
            )

            if not generated_clips:
                raise Exception("Failed to generate any clips")

            # ===== STAGE 5: STORE RESULTS =====
            self._update_job_success(job_id, generated_clips)
            logger.info(
                f"Clip generation completed for job {job_id}. "
                f"Generated {len(generated_clips)} clips"
            )

        except Exception as e:
            logger.error(
                f"Clip generation failed for job {job_id}: {str(e)}"
            )
            self._update_job_failure(job_id, str(e))

    def _trim_clips(
        self,
        job_id: str,
        video_path: str,
        clips: List,
    ) -> List[dict]:
        """
        Trim video for each clip and save to storage.

        Args:
            job_id: Unique job identifier
            video_path: Path to input video file
            clips: List of Clip objects from ClipFinder

        Returns:
            List of dictionaries with clip metadata:
            - filename: Output filename
            - path: Full output path
            - start_time: Start time in seconds
            - end_time: End time in seconds
            - duration: Clip duration in seconds
        """
        generated_clips = []
        
        # Create media file reference
        media_file = self.mediaeditor_service.create_audio_video_file(
            file_path=video_path
        )

        for idx, clip in enumerate(clips, 1):
            try:
                output_filename = f"clip_{job_id}_{idx:03d}.mp4"
                output_path = self.storage.get_output_path(job_id, output_filename)
                
                logger.debug(
                    f"Trimming clip {idx}/{len(clips)}: "
                    f"{clip.start_time:.2f}s - {clip.end_time:.2f}s"
                )
                
                # Trim video using MediaEditor
                self.mediaeditor_service.trim(
                    media_file=media_file,
                    start_time=clip.start_time,
                    end_time=clip.end_time,
                    output_path=output_path,
                )
                
                clip_duration = clip.end_time - clip.start_time
                generated_clips.append({
                    "filename": output_filename,
                    "path": output_path,
                    "start_time": clip.start_time,
                    "end_time": clip.end_time,
                    "duration": clip_duration,
                })
                
                logger.debug(f"Saved clip {idx}: {output_filename}")
                
            except Exception as e:
                logger.error(
                    f"Failed to generate clip {idx} for job {job_id}: {str(e)}"
                )
                # Continue with next clip - don't fail entire job
                continue

        return generated_clips

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
