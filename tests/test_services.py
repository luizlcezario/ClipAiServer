"""
Unit tests for service layer classes.

This module tests the StorageService and ClipGenerator functionality.
"""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.config import settings
from app.services.storage import StorageService
from app.services.clip_generator import ClipGenerator


class TestStorageService:
    """Tests for the StorageService class."""
    
    def test_storage_service_initialization(self) -> None:
        """
        Test StorageService initialization.
        
        Verifies that StorageService initializes correctly with
        configured temp and output directories.
        """
        service = StorageService()
        
        assert service.temp_dir is not None
        assert service.output_dir is not None
        assert isinstance(service.temp_dir, Path)
        assert isinstance(service.output_dir, Path)
    
    def test_directories_created_on_init(self) -> None:
        """
        Test that directories are created during initialization.
        
        Verifies that _ensure_directories() creates required directories.
        """
        service = StorageService()
        
        # Both directories should exist after initialization
        assert service.temp_dir.exists()
        assert service.output_dir.exists()
    
    def test_get_output_path(self) -> None:
        """
        Test getting output path for a job.
        
        Verifies that output paths are generated correctly
        and job subdirectories are created.
        """
        service = StorageService()
        job_id = "test-job-output-path"
        filename = "clip_test.mp4"
        
        output_path = service.get_output_path(job_id, filename)
        
        # Verify path structure
        assert job_id in output_path
        assert filename in output_path
        assert output_path.startswith(str(service.output_dir))
        
        # Verify directory was created
        job_dir = Path(output_path).parent
        assert job_dir.exists()
    
    def test_get_output_path_creates_job_directory(self) -> None:
        """
        Test that job directory is created when getting output path.
        
        Verifies that the job subdirectory is created automatically.
        """
        service = StorageService()
        job_id = "test-job-mkdir"
        filename = "clip.mp4"
        
        job_dir_before = service.output_dir / job_id
        assert not job_dir_before.exists()
        
        service.get_output_path(job_id, filename)
        
        assert job_dir_before.exists()
    
    def test_cleanup_temp_file_existing(self, temp_test_dir: Path) -> None:
        """
        Test cleaning up an existing temporary file.
        
        Verifies that cleanup_temp_file removes the file from disk.
        """
        service = StorageService()
        
        # Create a temp file
        temp_file = temp_test_dir / "test_temp_file.txt"
        temp_file.write_text("test content")
        
        assert temp_file.exists()
        
        # Cleanup
        service.cleanup_temp_file(str(temp_file))
        
        assert not temp_file.exists()
    
    def test_cleanup_temp_file_nonexistent(self) -> None:
        """
        Test cleaning up a non-existent temporary file.
        
        Verifies that cleanup handles missing files gracefully
        without raising an error.
        """
        service = StorageService()
        
        # This should not raise an error
        service.cleanup_temp_file("/nonexistent/path/to/file.txt")
    
    def test_cleanup_job_directory(self, temp_test_dir: Path) -> None:
        """
        Test cleaning up a job's output directory.
        
        Verifies that cleanup_job_directory removes the entire
        job directory and its contents.
        """
        service = StorageService()
        job_id = "test-job-cleanup"
        
        # Create job directory with some files
        output_path = service.get_output_path(job_id, "clip.mp4")
        job_dir = Path(output_path).parent
        
        # Create some test files
        (job_dir / "file1.txt").write_text("content1")
        (job_dir / "file2.txt").write_text("content2")
        
        assert job_dir.exists()
        assert (job_dir / "file1.txt").exists()
        
        # Cleanup
        service.cleanup_job_directory(job_id)
        
        assert not job_dir.exists()
    
    def test_cleanup_job_directory_nonexistent(self) -> None:
        """
        Test cleaning up a non-existent job directory.
        
        Verifies that cleanup handles missing directories gracefully
        without raising an error.
        """
        service = StorageService()
        
        # This should not raise an error
        service.cleanup_job_directory("nonexistent-job-id")
    
    def test_file_exists_true(self, temp_test_dir: Path) -> None:
        """
        Test file_exists returns True for existing files.
        
        Verifies that file_exists correctly identifies existing files.
        """
        service = StorageService()
        
        # Create a test file
        test_file = temp_test_dir / "existing_file.txt"
        test_file.write_text("content")
        
        assert service.file_exists(str(test_file)) is True
    
    def test_file_exists_false(self) -> None:
        """
        Test file_exists returns False for non-existent files.
        
        Verifies that file_exists correctly identifies missing files.
        """
        service = StorageService()
        
        assert service.file_exists("/nonexistent/path/file.txt") is False
    
    def test_file_exists_directory(self, temp_test_dir: Path) -> None:
        """
        Test file_exists with a directory path.
        
        Verifies that file_exists returns True for directories.
        """
        service = StorageService()
        
        assert service.file_exists(str(temp_test_dir)) is True


class TestClipGenerator:
    """Tests for the ClipGenerator service class."""
    
    def test_clip_generator_initialization(self, test_db: Session) -> None:
        """
        Test ClipGenerator initialization.
        
        Verifies that ClipGenerator can be instantiated with a database session.
        """
        generator = ClipGenerator(test_db)
        
        assert generator.db is test_db
        assert generator.storage is not None
        assert isinstance(generator.storage, StorageService)
    
    def test_clip_generator_clipsai_initialization(self, test_db: Session) -> None:
        """
        Test ClipGenerator clipsai library initialization.
        
        Verifies that clipsai library handling works correctly
        (either successfully imported or gracefully handles missing library).
        """
        generator = ClipGenerator(test_db)
        
        # clipsai may or may not be available, but initialization should handle both cases
        # No exception should be raised during initialization
        assert generator is not None
    
    def test_clip_generator_has_storage(self, test_db: Session) -> None:
        """
        Test that ClipGenerator has StorageService instance.
        
        Verifies that the storage service is properly initialized.
        """
        generator = ClipGenerator(test_db)
        
        assert hasattr(generator, "storage")
        assert generator.storage.temp_dir is not None
        assert generator.storage.output_dir is not None
    
    def test_clip_generator_multiple_instances(self, test_db: Session) -> None:
        """
        Test creating multiple ClipGenerator instances.
        
        Verifies that multiple generators can be created independently.
        """
        generator1 = ClipGenerator(test_db)
        generator2 = ClipGenerator(test_db)
        
        assert generator1 is not generator2
        assert generator1.db is generator2.db
        # Storage services are separate instances
        assert generator1.storage is not generator2.storage
