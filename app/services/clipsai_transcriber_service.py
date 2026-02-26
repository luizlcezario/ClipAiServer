"""
ClipsAI Transcriber Service

This module provides a clean interface for transcribing audio/video files
using the ClipsAI Transcriber with WhisperX.

Documentation: https://github.com/dyang108/ClipsAI#transcribe
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class TranscriberService:
    """
    Service for transcribing audio/video files using ClipsAI's Transcriber.
    
    This service provides a clean interface to the ClipsAI Transcriber,
    which uses WhisperX for accurate audio transcription with word-level,
    character-level, and sentence-level timestamps.
    
    Example:
        transcriber = TranscriberService()
        transcription = transcriber.transcribe(
            audio_file_path="/path/to/video.mp4"
        )
        print(f"Text: {transcription.text}")
        print(f"Language: {transcription.language}")
        print(f"Segments: {len(transcription.sentences)}")
    """

    def __init__(self):
        """Initialize the Transcriber service."""
        logger.info("Initializing TranscriberService")
        self._initialize_transcriber()

    def _initialize_transcriber(self) -> None:
        """
        Initialize the ClipsAI Transcriber instance.
        
        Raises:
            ImportError: If ClipsAI is not installed
        """
        try:
            from clipsai import Transcriber
            self.transcriber = Transcriber()
            logger.info("ClipsAI Transcriber initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import ClipsAI Transcriber: {e}")
            raise ImportError(
                "ClipsAI is not installed. Install it with: "
                "pip install clipsai"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize Transcriber: {e}")
            raise

    def transcribe(
        self,
        audio_file_path: str,
        language_code: Optional[str] = None,
        batch_size: int = 16,
    ):
        """
        Transcribe an audio or video file.
        
        This method follows the ClipsAI documentation exactly:
        https://github.com/dyang108/ClipsAI#transcribe
        
        Args:
            audio_file_path: Absolute path to the audio or video file
                            (e.g., "/abs/path/to/video.mp4")
            language_code: ISO 639-1 language code (e.g., 'en', 'pt').
                          None for auto-detection. Default: None
            batch_size: WhisperX batch size. Reduce if low on GPU memory.
                       Default: 16
        
        Returns:
            Transcription: ClipsAI Transcription object with:
                - text: Full transcribed text
                - words: List of Word objects with start/end times
                - sentences: List of Sentence objects with start/end times
                - characters: List of Character objects
                - language: Detected language (ISO 639-1 code)
                - start_time: Start time in seconds
                - end_time: End time in seconds
                - source_software: "whisperx"
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If invalid language code
            Exception: If transcription fails
        
        Example:
            >>> transcriber = TranscriberService()
            >>> transcription = transcriber.transcribe("/path/to/video.mp4")
            >>> for sentence in transcription.sentences:
            ...     print(f"{sentence.start_time:.2f}s: {sentence.text}")
        """
        # Validate file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            raise FileNotFoundError(
                f"Audio file not found: {audio_file_path}"
            )

        if not os.path.isfile(audio_file_path):
            logger.error(f"Path is not a file: {audio_file_path}")
            raise ValueError(
                f"Path is not a file: {audio_file_path}"
            )

        logger.info(
            f"Starting transcription of: {audio_file_path} "
            f"(language_code={language_code}, batch_size={batch_size})"
        )

        try:
            # Call ClipsAI Transcriber as documented
            transcription = self.transcriber.transcribe(
                audio_file_path=audio_file_path,
                iso6391_lang_code=language_code,
                batch_size=batch_size,
            )

            logger.info(
                f"Transcription completed successfully. "
                f"Language: {transcription.language}, "
                f"Duration: {transcription.end_time - transcription.start_time:.2f}s, "
                f"Sentences: {len(transcription.sentences)}"
            )

            return transcription

        except Exception as e:
            logger.error(
                f"Transcription failed for {audio_file_path}: {str(e)}"
            )
            raise

    def detect_language(
        self,
        audio_file_path: str,
        batch_size: int = 16,
    ) -> str:
        """
        Detect the language of an audio or video file.
        
        Args:
            audio_file_path: Absolute path to the audio or video file
            batch_size: WhisperX batch size. Default: 16
        
        Returns:
            str: ISO 639-1 language code (e.g., 'en', 'pt')
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If detection fails
        """
        # Validate file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(
                f"Audio file not found: {audio_file_path}"
            )

        logger.info(f"Detecting language of: {audio_file_path}")

        try:
            language_code = self.transcriber.detect_language(
                audio_file_path=audio_file_path,
                batch_size=batch_size,
            )
            logger.info(f"Detected language: {language_code}")
            return language_code
        except Exception as e:
            logger.error(
                f"Language detection failed for {audio_file_path}: {str(e)}"
            )
            raise
