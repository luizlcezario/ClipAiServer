"""
ClipsAI ClipFinder Service

This module provides a clean interface for finding clips in transcribed content
using the ClipsAI ClipFinder with TextTiling algorithm and BERT embeddings.

Documentation: https://github.com/dyang108/ClipsAI#clip
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class ClipFinderService:
    """
    Service for finding clips in transcribed audio/video content.
    
    Uses the TextTiling algorithm with BERT embeddings to detect topic shifts
    and segment content into coherent clips. The algorithm operates at sentence
    granularity and is optimized for identifying distinct sections within content.
    
    Example:
        clipfinder = ClipFinderService()
        clips = clipfinder.find_clips(transcription=transcription)
        for clip in clips:
            print(f"Clip: {clip.start_time:.2f}s - {clip.end_time:.2f}s")
    """

    def __init__(self):
        """Initialize the ClipFinder service."""
        logger.info("Initializing ClipFinderService")
        self._initialize_clip_finder()

    def _initialize_clip_finder(self) -> None:
        """
        Initialize the ClipsAI ClipFinder instance.
        
        Raises:
            ImportError: If ClipsAI is not installed
        """
        try:
            from clipsai import ClipFinder
            self.clip_finder = ClipFinder()
            logger.info("ClipsAI ClipFinder initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import ClipsAI ClipFinder: {e}")
            raise ImportError(
                "ClipsAI is not installed. Install it with: "
                "pip install clipsai"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize ClipFinder: {e}")
            raise

    def find_clips(self, transcription) -> List:
        """
        Find clips in a transcription using TextTiling algorithm.
        
        This method follows the ClipsAI documentation exactly:
        https://github.com/dyang108/ClipsAI#clip
        
        The algorithm segments the transcription at sentence granularity
        and detects topic shifts using BERT embeddings to identify
        coherent and engaging clips.
        
        Args:
            transcription: ClipsAI Transcription object returned from
                          TranscriberService.transcribe()
        
        Returns:
            List[Clip]: List of Clip objects with:
                - start_time: Start time in seconds
                - end_time: End time in seconds
                - start_char: Start character index in transcription
                - end_char: End character index in transcription
                - Methods: copy(), to_dict()
        
        Raises:
            ValueError: If transcription is None or invalid
            Exception: If clip detection fails
        
        Example:
            >>> clipfinder = ClipFinderService()
            >>> clips = clipfinder.find_clips(transcription=transcription)
            >>> print(f"Found {len(clips)} clips")
            >>> for i, clip in enumerate(clips):
            ...     duration = clip.end_time - clip.start_time
            ...     print(f"Clip {i+1}: {clip.start_time:.2f}s - {clip.end_time:.2f}s ({duration:.2f}s)")
        """
        if transcription is None:
            logger.error("Transcription is None")
            raise ValueError("Transcription cannot be None")

        logger.info(
            f"Finding clips in transcription with {len(transcription.sentences)} sentences"
        )

        try:
            # Call ClipsAI ClipFinder as documented
            clips = self.clip_finder.find_clips(
                transcription=transcription
            )

            if not clips:
                logger.warning("No clips found in transcription")
                return []

            logger.info(
                f"Found {len(clips)} clips. "
                f"Duration range: {clips[0].start_time:.2f}s - {clips[-1].end_time:.2f}s"
            )

            return clips

        except Exception as e:
            logger.error(f"Clip finding failed: {str(e)}")
            raise

    def get_clip_info(self, clip) -> dict:
        """
        Extract clip information as a dictionary.
        
        Args:
            clip: ClipsAI Clip object
        
        Returns:
            dict: Clip information including:
                - start_time: Start time in seconds
                - end_time: End time in seconds
                - start_char: Start character index
                - end_char: End character index
                - duration: Duration in seconds
        """
        try:
            clip_dict = clip.to_dict()
            clip_dict['duration'] = clip.end_time - clip.start_time
            return clip_dict
        except Exception as e:
            logger.error(f"Failed to extract clip info: {str(e)}")
            raise
