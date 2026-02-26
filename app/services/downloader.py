"""
Async video downloader service for downloading videos from web URLs.

This module handles asynchronous downloading of videos from various sources
and caching them for processing without blocking requests.
"""

import logging
import os
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse
import aiohttp

logger = logging.getLogger(__name__)


class AsyncVideoDownloader:
    """Service for asynchronously downloading videos from web URLs."""

    def __init__(self, cache_dir: str = "./temp_uploads"):
        """
        Initialize async video downloader.

        Args:
            cache_dir: Directory to store downloaded videos
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AsyncVideoDownloader initialized with cache_dir={self.cache_dir}")

    async def download_video(
        self,
        url: str,
        timeout: int = 3600,
        max_size_mb: int = 2048,
        chunk_size: int = 8192,
    ) -> str:
        """
        Asynchronously download video from URL to local cache.

        This method runs asynchronously and does NOT block the request.

        Args:
            url: URL of the video to download (HTTP/HTTPS)
            timeout: Download timeout in seconds (default: 3600s = 1 hour)
            max_size_mb: Maximum file size in MB (default: 2048MB = 2GB)
            chunk_size: Download chunk size in bytes (default: 8192)

        Returns:
            Path to downloaded video file

        Raises:
            ValueError: If URL is invalid or file too large
            aiohttp.ClientError: If download fails
            OSError: If file cannot be written
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid URL scheme. Expected http/https, got: {parsed.scheme}")

            logger.info(f"Starting async download from URL: {url}")

            # Create timeout and session
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
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

                    with open(output_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
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

        except aiohttp.ClientError as e:
            logger.error(f"Download failed: {e}")
            raise
        except OSError as e:
            logger.error(f"File write error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise

    async def download_video_with_progress(
        self,
        url: str,
        progress_callback=None,
        timeout: int = 3600,
        max_size_mb: int = 2048,
    ) -> str:
        """
        Download video with progress callback for monitoring.

        Args:
            url: URL of the video to download
            progress_callback: Async callback function(downloaded_mb, total_mb) for progress
            timeout: Download timeout in seconds
            max_size_mb: Maximum file size in MB

        Returns:
            Path to downloaded video file
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid URL scheme. Expected http/https, got: {parsed.scheme}")

            logger.info(f"Starting progress-tracked download from: {url}")

            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    response.raise_for_status()

                    # Get total size
                    total_size = int(response.headers.get("content-length", 0))
                    if total_size > max_size_mb * 1024 * 1024:
                        raise ValueError(
                            f"File too large: {total_size / (1024*1024):.2f}MB > {max_size_mb}MB limit"
                        )

                    total_mb = total_size / (1024 * 1024) if total_size else 0

                    # Generate output filename
                    filename = self._generate_filename(url, response)
                    output_path = self.cache_dir / filename

                    logger.info(f"Downloading to: {output_path} (Total: {total_mb:.2f}MB)")

                    # Download with progress tracking
                    downloaded_size = 0
                    chunk_size = 8192

                    with open(output_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                downloaded_mb = downloaded_size / (1024 * 1024)

                                # Call progress callback
                                if progress_callback:
                                    try:
                                        if asyncio.iscoroutinefunction(progress_callback):
                                            await progress_callback(downloaded_mb, total_mb)
                                        else:
                                            progress_callback(downloaded_mb, total_mb)
                                    except Exception as e:
                                        logger.warning(f"Progress callback error: {e}")

                                # Check file size limit
                                if downloaded_size > (max_size_mb * 1024 * 1024):
                                    output_path.unlink()
                                    raise ValueError(f"File exceeded {max_size_mb}MB limit")

                    logger.info(f"Download completed: {downloaded_mb:.2f}MB saved to {output_path}")
                    return str(output_path)

        except aiohttp.ClientError as e:
            logger.error(f"Download failed: {e}")
            raise
        except OSError as e:
            logger.error(f"File write error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise

    def _generate_filename(self, url: str, response) -> str:
        """
        Generate a unique filename for the downloaded video.

        Args:
            url: Original URL
            response: aiohttp response object

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

    def _get_extension(self, response) -> str:
        """
        Determine file extension from content-type header.

        Args:
            response: aiohttp response object

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
            "application/octet-stream": ".mp4",
        }

        for content_type_key, ext in extension_map.items():
            if content_type_key in content_type:
                return ext

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


# Keep the old synchronous class for backward compatibility
class VideoDownloader:
    """Backward compatible synchronous wrapper. For new code, use AsyncVideoDownloader."""

    def __init__(self, cache_dir: str = "./temp_uploads"):
        """Initialize video downloader."""
        self.async_downloader = AsyncVideoDownloader(cache_dir)
        self.cache_dir = self.async_downloader.cache_dir

    def download_video(self, url: str, timeout: int = 300, max_size_mb: int = 2048) -> str:
        """Synchronous wrapper for backward compatibility."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.async_downloader.download_video(url, timeout, max_size_mb)
            )
        finally:
            loop.close()

    def delete_cached_video(self, file_path: str) -> bool:
        """Delete cached video."""
        return self.async_downloader.delete_cached_video(file_path)

    def cleanup_old_videos(self, max_age_hours: int = 24) -> int:
        """Clean up old videos."""
        return self.async_downloader.cleanup_old_videos(max_age_hours)

    def is_url(self, path: str) -> bool:
        """Check if string is URL."""
        return self.async_downloader.is_url(path)
