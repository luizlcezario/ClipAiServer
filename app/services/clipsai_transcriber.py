"""
Transcriber service using ClipsAI Transcriber class.

This module provides a wrapper around ClipsAI's Transcriber for audio transcription.
Follows the ClipsAI documentation: https://github.com/dyang108/ClipsAI
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import ClipsAI transcriber
try:
    from clipsai import Transcriber as ClipsAITranscriber
    CLIPSAI_TRANSCRIBER_AVAILABLE = True
except (ImportError, NameError) as e:
    logger.warning(f"ClipsAI Transcriber not available: {e}. Using mock implementation.")
    CLIPSAI_TRANSCRIBER_AVAILABLE = False
    
    # Mock implementation for when ClipsAI is not available
    class ClipsAITranscriber:
        """Mock Transcriber for testing without ClipsAI."""
        
        def __init__(self):
            logger.info("Using mock ClipsAI Transcriber")
        
        def transcribe(self, audio_file_path: str):
            """
            Mock transcription method.
            
            Args:
                audio_file_path: Path to audio/video file
            
            Returns:
                Mock transcription object with segments
            """
            logger.warning(f"Mock transcription for: {audio_file_path}")
            
            class MockTranscription:
                def __init__(self):
                    self.segments = [
                        {
                            "id": 0,
                            "seek": 0,
                            "start": 0.0,
                            "end": 5.0,
                            "text": "This is a mock transcription segment one.",
                            "tokens": [],
                            "temperature": 0.0,
                            "avg_logprob": 0.0,
                            "compression_ratio": 1.0,
                            "no_speech_prob": 0.0
                        },
                        {
                            "id": 1,
                            "seek": 0,
                            "start": 5.0,
                            "end": 10.0,
                            "text": "This is mock transcription segment two.",
                            "tokens": [],
                            "temperature": 0.0,
                            "avg_logprob": 0.0,
                            "compression_ratio": 1.0,
                            "no_speech_prob": 0.0
                        }
                    ]
            
            return MockTranscription()


class Transcriber:
    """
    Wrapper for ClipsAI Transcriber.
    
    Usage:
        transcriber = Transcriber()
        transcription = transcriber.transcribe(audio_file_path="/path/to/video.mp4")
        print(transcription.segments)
    """
    
    def __init__(self):
        """Initialize the Transcriber using ClipsAI's Transcriber."""
        logger.info("Initializing Transcriber with ClipsAI")
        self.transcriber = ClipsAITranscriber()
        logger.info(f"Transcriber initialized. ClipsAI available: {CLIPSAI_TRANSCRIBER_AVAILABLE}")
    
    def transcribe(self, audio_file_path: str):
        """
        Transcribe audio/video file.
        
        This method follows the ClipsAI documentation exactly:
        https://github.com/dyang108/ClipsAI#usage
        
        Args:
            audio_file_path: Absolute path to video or audio file
                            (e.g., "/abs/path/to/video.mp4")
        
        Returns:
            Transcription object with segments containing:
            - text: Transcribed text for the segment
            - start: Start time in seconds
            - end: End time in seconds
            - tokens, temperature, etc.
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If transcription fails
        
        Example:
            >>> from app.services.clipsai_transcriber import Transcriber
            >>> transcriber = Transcriber()
            >>> transcription = transcriber.transcribe("/path/to/video.mp4")
            >>> for segment in transcription.segments:
            ...     print(f"{segment['start']:.2f}s - {segment['end']:.2f}s: {segment['text']}")
        """
        import os
        
        # Validate file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        logger.info(f"Starting transcription of: {audio_file_path}")
        
        try:
            # Call ClipsAI Transcriber exactly as documented
            transcription = self.transcriber.transcribe(audio_file_path=audio_file_path)
            
            logger.info(
                f"Transcription completed. "
                f"Segments: {len(transcription.segments) if hasattr(transcription, 'segments') else '?'}"
            )
            
            return transcription
        
        except Exception as e:
            logger.error(f"Transcription failed for {audio_file_path}: {str(e)}")
            raise
