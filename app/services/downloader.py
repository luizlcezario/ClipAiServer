"""
Video downloader service for downloading videos from web URLs.

This module handles downloading videos from various sources (direct URLs, YouTube, etc.)
and caching them for processing.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Service for downloading videos from web URLs."""

    def __init__(self, cache_dir: str = "./temp_uploads"):
        """
        Initialize video downloader.

        Args:
            cache_dir: Directory to store downloaded videos
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"VideoDownloader initialized with cache_dir={self.cache_dir}")

    def download_video(
        self,
        url: str,
        timeout: int = 300,
        max_size_mb: int = 2048,
    ) -> str:
        """
        Download video from URL to local cache.

        Args:
            url: URL of the video to download (HTTP/HTTPS)
            timeout: Download timeout in seconds (default: 300s = 5min)
            max_size_mb: Maximum file size in MB (default: 2048MB = 2GB)

        Returns:
            Path to downloaded video file

        Raises:
            ValueError: If URL is invalid or file too large
            requests.RequestException: If download fails
            OSError: If file cannot be written
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid URL scheme. Expected http/https, got: {parsed.scheme}")

            logger.info(f"Starting download from URL: {url}")

            # Create download session with streaming
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                stream=True,
                allow_redirects=True,
            )
            response.raise_for_status()

            # Check content length
            content_length = response.headers.get("content-length")
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    raise ValueError(
                        f"File too large: {size_mb:.2f}MB > {max_size_mb}MB limit"
                    )

            # Generate output filename
            filename = self._generate_filename(url, response)
            output_path = self.cache_dir / filename

            logger.info(f"Downloading to: {output_path}")

            # Download with progress tracking
            downloaded_size = 0
            chunk_size = 8192  # 8KB chunks

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Check file size during download
                        if downloaded_size > (max_size_mb * 1024 * 1024):
                            output_path.unlink()  # Delete incomplete file
                            raise ValueError(f"File exceeded {max_size_mb}MB limit")

            logger.info(
                f"Download completed: {downloaded_size / (1024*1024):.2f}MB "
                f"saved to {output_path}"
            )
            return str(output_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            raise
        except OSError as e:
            logger.error(f"File write error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise

    def _generate_filename(self, url: str, response: requests.Response) -> str:
        """
        Generate a unique filename for the downloaded video.

        Args:
            url: Original URL
            response: Response object from requests

        Returns:
            Filename (without path)
        """
        # Try to get filename from content-disposition header
        content_disposition = response.headers.get("content-disposition", "")
        if "filename" in content_disposition:
            filename = content_disposition.split("filename=")[1].strip('"\'')
            if filename:
                return filename

        # Try to get filename from URL path
        parsed = urlparse(url)
        if parsed.path:
            filename = Path(parsed.path).name
            if filename and "." in filename:
                return filename

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self._get_extension(response)
        return f"video_{timestamp}{extension}"

    def _get_extension(self, response: requests.Response) -> str:
        """
        Determine file extension from content-type header.

        Args:
            response: Response object from requests

        Returns:
            File extension (e.g., '.mp4')
        """
        content_type = response.headers.get("content-type", "").lower()

        extension_map = {
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/x-msvideo": ".avi",
            "video/x-matroska": ".mkv",
            "video/webm": ".webm",
            "video/mpeg": ".mpeg",
            "application/octet-stream": ".mp4",  # Default to mp4
        }

        for content_type_key, ext in extension_map.items():
            if content_type_key in content_type:
                return ext

        # Default to .mp4 if unknown
        return ".mp4"

    def delete_cached_video(self, file_path: str) -> bool:
        """
        Delete a cached video file.

        Args:
            file_path: Path to cached video file

        Returns:
            True if file was deleted, False if not found
        """
        try:
            path = Path(file_path)
            if path.exists() and path.parent == self.cache_dir:
                path.unlink()
                logger.info(f"Deleted cached video: {file_path}")
                return True
            return False
        except OSError as e:
            logger.error(f"Failed to delete cached video: {e}")
            return False

    def cleanup_old_videos(self, max_age_hours: int = 24) -> int:
        """
        Clean up cached videos older than specified time.

        Args:
            max_age_hours: Maximum age in hours (default: 24)

        Returns:
            Number of files deleted
        """
        try:
            from time import time

            current_time = time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0

            for file_path in self.cache_dir.glob("video_*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Cleaned up old video: {file_path}")

            if deleted_count > 0:
                logger.info(f"Cleanup removed {deleted_count} old video files")

            return deleted_count

        except OSError as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def is_url(self, path: str) -> bool:
        """
        Check if a string is a valid URL.

        Args:
            path: String to check

        Returns:
            True if valid HTTP/HTTPS URL, False otherwise
        """
        try:
            parsed = urlparse(path)
            return parsed.scheme in ("http", "https") and parsed.netloc
        except Exception:
            return False
