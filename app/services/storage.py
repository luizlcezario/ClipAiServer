"""
Storage service for handling file operations.

This module provides utilities for managing temporary uploads,
clip output files, and file cleanup operations.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import aiofiles
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage operations."""

    def __init__(self):
        """Initialize storage service with configured directories."""
        self.temp_dir = Path(settings.temp_upload_dir)
        self.output_dir = Path(settings.clips_output_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save an uploaded file to temporary directory.

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            str: Path to the saved file

        Raises:
            IOError: If file save operation fails
        """
        try:
            filepath = self.temp_dir / filename
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(file_content)
            logger.info(f"Saved uploaded file to {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise

    def get_output_path(self, job_id: str, filename: str) -> str:
        """
        Get path for output clip file.

        Args:
            job_id: Unique job identifier
            filename: Output filename

        Returns:
            str: Full path for the output file
        """
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return str(job_dir / filename)

    def cleanup_temp_file(self, filepath: str) -> None:
        """
        Delete a temporary file.

        Args:
            filepath: Path to file to delete

        Note:
            Silently ignores if file doesn't exist
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted temporary file: {filepath}")
        except OSError as e:
            logger.warning(f"Failed to delete temporary file {filepath}: {e}")

    def cleanup_job_directory(self, job_id: str) -> None:
        """
        Delete all files in a job's output directory.

        Args:
            job_id: Unique job identifier
        """
        try:
            job_dir = self.output_dir / job_id
            if job_dir.exists():
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up job directory: {job_dir}")
        except OSError as e:
            logger.warning(f"Failed to cleanup job directory for {job_id}: {e}")

    def file_exists(self, filepath: str) -> bool:
        """
        Check if a file exists.

        Args:
            filepath: Path to file

        Returns:
            bool: True if file exists, False otherwise
        """
        return os.path.exists(filepath)

    def get_file_size(self, filepath: str) -> int:
        """
        Get size of a file in bytes.

        Args:
            filepath: Path to file

        Returns:
            int: File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        return os.path.getsize(filepath)
