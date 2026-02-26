import os
import logging
from typing import Optional
import whisperx
import torch

logger = logging.getLogger(__name__)


class TranscriberService:
    """Service for transcribing audio/video files using WhisperX."""
    
    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: str = "float16"
    ):
        """
        Initialize TranscriberService.
        
        Args:
            model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to use ('cuda' or 'cpu'). Auto-detects if None
            compute_type: Compute type for model ('float16' or 'int8')
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = compute_type
        self.model = None
        
        logger.info(f"TranscriberService initialized with model={model_name}, device={self.device}")
    
    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            logger.info(f"Loading WhisperX model: {self.model_name}")
            try:
                self.model = whisperx.load_model(
                    self.model_name,
                    self.device,
                    compute_type=self.compute_type
                )
                logger.info("WhisperX model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load WhisperX model: {str(e)}")
                raise
    
    async def transcribe(self, audio_file_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe audio/video file.
        
        Args:
            audio_file_path: Path to audio or video file
            language: Language code (e.g., 'en', 'pt'). Auto-detect if None
        
        Returns:
            Dictionary containing transcription results with segments
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If transcription fails
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            self._load_model()
            
            logger.info(f"Starting transcription of {audio_file_path}")
            
            # Transcribe audio
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                batch_size=16
            )
            
            logger.info(f"Transcription completed with {len(result.get('segments', []))} segments")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed for {audio_file_path}: {str(e)}")
            raise
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
            logger.info("WhisperX model unloaded")
