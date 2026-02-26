"""
Pytest configuration and fixtures for the test suite.

This module provides shared fixtures used across all tests, including
database sessions, FastAPI test clients, and sample data fixtures.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.clip_job import Base, ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest


@pytest.fixture(scope="session")
def temp_test_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.
    
    Yields:
        Path: Temporary directory path
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="clips_ai_test_"))
    yield temp_dir
    # Cleanup after all tests
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def test_db(temp_test_dir: Path) -> Generator[Session, None, None]:
    """
    Create an in-memory SQLite database for testing.
    
    Creates a fresh database session for each test and cleans up after.
    
    Args:
        temp_test_dir: Temporary directory fixture
        
    Yields:
        Session: SQLAlchemy database session for testing
    """
    # Create in-memory SQLite database for tests
    database_url = f"sqlite:///{temp_test_dir / 'test.db'}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    
    # Create session
    db = TestingSessionLocal()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_client(test_db: Session) -> TestClient:
    """
    Create a FastAPI test client with a test database session.
    
    Overrides the get_db dependency to use the test database.
    
    Args:
        test_db: Test database session fixture
        
    Returns:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_clip_request() -> ClipGenerationRequest:
    """
    Create a sample clip generation request for testing.
    
    Returns:
        ClipGenerationRequest: Sample request with typical values
    """
    return ClipGenerationRequest(
        video_path="/path/to/video.mp4",
        start_time=10.0,
        end_time=30.0,
        title="Test Clip",
        description="A test clip for unit testing",
        tags=["test", "sample"]
    )


@pytest.fixture
def sample_clip_job(test_db: Session) -> ClipJob:
    """
    Create a sample clip job in the test database.
    
    Args:
        test_db: Test database session fixture
        
    Returns:
        ClipJob: Sample clip job instance
    """
    job = ClipJob(
        job_id="test-job-123-abc-456",
        status=JobStatus.PENDING,
        input_file="/path/to/video.mp4",
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture
def cleanup_temp_files(temp_test_dir: Path) -> Generator[None, None, None]:
    """
    Cleanup fixture for temporary test files.
    
    Ensures that all temporary files created during tests are cleaned up.
    
    Args:
        temp_test_dir: Temporary directory fixture
        
    Yields:
        None
    """
    yield
    
    # Cleanup temp files after test
    temp_upload = Path(settings.temp_upload_dir)
    clips_output = Path(settings.clips_output_dir)
    
    if temp_upload.exists():
        import shutil
        for item in temp_upload.glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    
    if clips_output.exists():
        import shutil
        for item in clips_output.glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


@pytest.fixture(autouse=True)
def reset_app_dependencies():
    """
    Reset FastAPI dependency overrides between tests.
    
    This ensures that test-specific dependency overrides don't
    affect other tests.
    """
    yield
    app.dependency_overrides.clear()
