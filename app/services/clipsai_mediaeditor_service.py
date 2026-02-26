"""
ClipsAI MediaEditor Service

This module provides a clean interface for trimming and editing audio/video files
using the ClipsAI MediaEditor.

Documentation: https://github.com/dyang108/ClipsAI#clip
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class MediaEditorService:
    """
    Service for trimming and editing audio/video files.
    
    Handles both audio-only and audio+video files, trimming them to
    specified time ranges and saving the results.
    
    Example:
        media_editor = MediaEditorService()
        media_file = media_editor.create_audio_video_file("/path/to/video.mp4")
        trimmed = media_editor.trim(
            media_file=media_file,
            start_time=0.0,
            end_time=10.5,
            output_path="/path/to/output.mp4"
        )
    """

    def __init__(self):
        """Initialize the MediaEditor service."""
        logger.info("Initializing MediaEditorService")
        self._initialize_media_editor()

    def _initialize_media_editor(self) -> None:
        """
        Initialize the ClipsAI MediaEditor instance.
        
        Raises:
            ImportError: If ClipsAI is not installed
        """
        try:
            from clipsai import MediaEditor
            self.media_editor = MediaEditor()
            logger.info("ClipsAI MediaEditor initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import ClipsAI MediaEditor: {e}")
            raise ImportError(
                "ClipsAI is not installed. Install it with: "
                "pip install clipsai"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize MediaEditor: {e}")
            raise

    def create_audio_video_file(self, file_path: str):
        """
        Create an AudioVideoFile object for video files.
        
        Use this for files containing both audio and video streams.
        
        Args:
            file_path: Absolute path to the video file
        
        Returns:
            AudioVideoFile: ClipsAI AudioVideoFile object
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ImportError: If ClipsAI is not installed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        try:
            from clipsai import AudioVideoFile
            logger.info(f"Creating AudioVideoFile: {file_path}")
            return AudioVideoFile(file_path)
        except ImportError as e:
            logger.error(f"Failed to import AudioVideoFile: {e}")
            raise

    def create_audio_file(self, file_path: str):
        """
        Create an AudioFile object for audio-only files.
        
        Use this for audio-only streams (no video).
        
        Args:
            file_path: Absolute path to the audio file
        
        Returns:
            AudioFile: ClipsAI AudioFile object
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ImportError: If ClipsAI is not installed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            from clipsai import AudioFile
            logger.info(f"Creating AudioFile: {file_path}")
            return AudioFile(file_path)
        except ImportError as e:
            logger.error(f"Failed to import AudioFile: {e}")
            raise

    def trim(
        self,
        media_file,
        start_time: float,
        end_time: float,
        output_path: str,
    ):
        """
        Trim a media file to a specified time range.
        
        This method follows the ClipsAI documentation exactly:
        https://github.com/dyang108/ClipsAI#clip
        
        Args:
            media_file: AudioFile or AudioVideoFile object created with
                       create_audio_file() or create_audio_video_file()
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path where the trimmed file will be saved
                        (file doesn't need to exist yet)
        
        Returns:
            AudioFile or AudioVideoFile: The media file object
        
        Raises:
            ValueError: If start_time >= end_time or invalid parameters
            OSError: If output directory can't be created or file can't be written
            Exception: If trimming fails
        
        Example:
            >>> media_editor = MediaEditorService()
            >>> media_file = media_editor.create_audio_video_file("/path/to/video.mp4")
            >>> result = media_editor.trim(
            ...     media_file=media_file,
            ...     start_time=5.0,
            ...     end_time=15.5,
            ...     output_path="/path/to/clip.mp4"
            ... )
        """
        # Validate parameters
        if start_time < 0:
            raise ValueError(f"start_time must be >= 0, got {start_time}")

        if start_time >= end_time:
            raise ValueError(
                f"start_time ({start_time}) must be < end_time ({end_time})"
            )

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")

        logger.info(
            f"Trimming media: {start_time:.2f}s - {end_time:.2f}s "
            f"to {output_path}"
        )

        try:
            # Call ClipsAI MediaEditor as documented
            result = self.media_editor.trim(
                media_file=media_file,
                start_time=start_time,
                end_time=end_time,
                trimmed_media_file_path=output_path,
            )

            duration = end_time - start_time
            logger.info(
                f"Trim completed successfully. "
                f"Output: {output_path} (Duration: {duration:.2f}s)"
            )

            return result

        except Exception as e:
            logger.error(f"Trimming failed: {str(e)}")
            # Clean up partial output file if it exists
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.debug(f"Cleaned up partial output file: {output_path}")
                except OSError:
                    pass
            raise
