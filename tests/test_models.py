"""
Unit tests for database models.

This module tests the SQLAlchemy ORM models for clip job tracking.
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.clip_job import ClipJob, JobStatus


class TestJobStatusEnum:
    """Tests for the JobStatus enumeration."""
    
    def test_job_status_values(self) -> None:
        """
        Test that JobStatus enum has all expected values.
        
        Verifies that the enum contains the required status values.
        """
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
    
    def test_job_status_count(self) -> None:
        """
        Test that JobStatus enum has the correct number of values.
        
        Verifies that exactly 4 status values are defined.
        """
        assert len(JobStatus) == 4
    
    def test_job_status_from_string(self) -> None:
        """
        Test creating JobStatus from string values.
        
        Verifies that JobStatus can be instantiated from string values.
        """
        assert JobStatus("pending") == JobStatus.PENDING
        assert JobStatus("processing") == JobStatus.PROCESSING
        assert JobStatus("completed") == JobStatus.COMPLETED
        assert JobStatus("failed") == JobStatus.FAILED
    
    def test_job_status_invalid_value(self) -> None:
        """
        Test that invalid JobStatus value raises an error.
        
        Verifies that attempting to create a JobStatus with an invalid
        string value raises a ValueError.
        """
        with pytest.raises(ValueError):
            JobStatus("invalid_status")


class TestClipJobModel:
    """Tests for the ClipJob database model."""
    
    def test_clip_job_creation(self, test_db: Session) -> None:
        """
        Test basic ClipJob model creation.
        
        Verifies that a ClipJob can be created and persisted
        to the database with required fields.
        """
        job = ClipJob(
            job_id="test-job-001",
            status=JobStatus.PENDING,
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        
        assert job.id is not None
        assert job.job_id == "test-job-001"
        assert job.status == JobStatus.PENDING
        assert job.input_file == "/path/to/video.mp4"
        assert job.output_file is None
        assert job.error_message is None
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_clip_job_with_all_fields(self, test_db: Session) -> None:
        """
        Test ClipJob creation with all fields populated.
        
        Verifies that all optional fields can be set and persisted correctly.
        """
        job = ClipJob(
            job_id="test-job-002",
            status=JobStatus.COMPLETED,
            input_file="/path/to/video.mp4",
            output_file="/path/to/output/clip.mp4",
            error_message=None,
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        
        assert job.output_file == "/path/to/output/clip.mp4"
    
    def test_clip_job_with_error_message(self, test_db: Session) -> None:
        """
        Test ClipJob creation with error message.
        
        Verifies that error messages can be stored for failed jobs.
        """
        error_msg = "Video codec not supported"
        job = ClipJob(
            job_id="test-job-003",
            status=JobStatus.FAILED,
            input_file="/path/to/video.mp4",
            error_message=error_msg,
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        
        assert job.error_message == error_msg
    
    def test_clip_job_unique_job_id(self, test_db: Session) -> None:
        """
        Test that job_id must be unique.
        
        Verifies that attempting to create two jobs with the same job_id
        raises a database integrity error.
        """
        job1 = ClipJob(
            job_id="unique-job-id",
            status=JobStatus.PENDING,
            input_file="/path/to/video1.mp4",
        )
        job2 = ClipJob(
            job_id="unique-job-id",  # Duplicate
            status=JobStatus.PENDING,
            input_file="/path/to/video2.mp4",
        )
        
        test_db.add(job1)
        test_db.commit()
        
        test_db.add(job2)
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_clip_job_status_update(self, test_db: Session) -> None:
        """
        Test updating job status.
        
        Verifies that job status can be updated and persisted correctly.
        """
        job = ClipJob(
            job_id="test-job-004",
            status=JobStatus.PENDING,
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        
        # Update status
        job.status = JobStatus.PROCESSING
        test_db.commit()
        test_db.refresh(job)
        
        assert job.status == JobStatus.PROCESSING
    
    def test_clip_job_default_values(self, test_db: Session) -> None:
        """
        Test default values for ClipJob fields.
        
        Verifies that default values are applied correctly
        (e.g., status defaults to PENDING).
        """
        job = ClipJob(
            job_id="test-job-005",
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        
        assert job.status == JobStatus.PENDING
        assert job.output_file is None
        assert job.error_message is None
    
    def test_clip_job_timestamps(self, test_db: Session) -> None:
        """
        Test that timestamps are set automatically.
        
        Verifies that created_at and updated_at are automatically
        set when a job is created.
        """
        before_creation = datetime.utcnow()
        job = ClipJob(
            job_id="test-job-006",
            status=JobStatus.PENDING,
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        after_creation = datetime.utcnow()
        
        assert before_creation <= job.created_at <= after_creation
        assert before_creation <= job.updated_at <= after_creation
    
    def test_clip_job_query_by_job_id(self, test_db: Session) -> None:
        """
        Test querying ClipJob by job_id.
        
        Verifies that jobs can be retrieved from the database
        by their unique job_id.
        """
        job = ClipJob(
            job_id="queryable-job-id",
            status=JobStatus.PENDING,
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved_job = test_db.query(ClipJob).filter(
            ClipJob.job_id == "queryable-job-id"
        ).first()
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == job.job_id
        assert retrieved_job.status == job.status
    
    def test_clip_job_query_by_status(self, test_db: Session) -> None:
        """
        Test querying ClipJob by status.
        
        Verifies that multiple jobs can be queried by their status.
        """
        # Create multiple jobs with different statuses
        job1 = ClipJob(job_id="job-1", status=JobStatus.PENDING, input_file="vid1.mp4")
        job2 = ClipJob(job_id="job-2", status=JobStatus.PROCESSING, input_file="vid2.mp4")
        job3 = ClipJob(job_id="job-3", status=JobStatus.PENDING, input_file="vid3.mp4")
        
        test_db.add_all([job1, job2, job3])
        test_db.commit()
        
        pending_jobs = test_db.query(ClipJob).filter(
            ClipJob.status == JobStatus.PENDING
        ).all()
        
        assert len(pending_jobs) == 2
        assert all(j.status == JobStatus.PENDING for j in pending_jobs)
    
    def test_clip_job_table_name(self) -> None:
        """
        Test that ClipJob model uses correct table name.
        
        Verifies that the model is mapped to the correct database table.
        """
        assert ClipJob.__tablename__ == "clip_jobs"
