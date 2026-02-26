"""
Clips AI Server - FastAPI application for generating video clips using clipsai library.

A complete FastAPI project structure for clip generation with:
- Asynchronous background task processing
- SQLAlchemy ORM for job tracking
- Type-safe Pydantic schemas
- Comprehensive error handling
- File storage management
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "FastAPI server for generating video clips using clipsai"

from app.main import app

__all__ = ["app"]
