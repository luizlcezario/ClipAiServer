"""
Configuration management for the Clips AI Server application.

This module handles environment variables and application settings
using Pydantic settings for type-safe configuration.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///clips.db"

    # Logging
    log_level: str = "INFO"

    # File paths
    temp_upload_dir: str = "./temp_uploads"
    clips_output_dir: str = "./clips_output"

    # API settings
    api_title: str = "Clips AI Server"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI server for generating clips using clipsai library"

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **data):
        """Initialize settings and create required directories."""
        super().__init__(**data)
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.temp_upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.clips_output_dir).mkdir(parents=True, exist_ok=True)


# Singleton settings instance
settings = Settings()
