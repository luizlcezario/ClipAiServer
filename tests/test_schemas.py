"""
Unit tests for Pydantic schemas.

This module tests validation and serialization of request and response schemas.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.clip_request import ClipGenerationRequest
from app.schemas.clip_response import ClipGenerationResponse, JobStatusResponse


class TestClipGenerationRequest:
    """Tests for ClipGenerationRequest validation schema."""
    
    def test_valid_request_with_all_fields(self) -> None:
        """
        Test valid request with all fields populated.
        
        Verifies that a complete request with all optional fields
        validates successfully.
        """
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            start_time=10.5,
            end_time=45.2,
            title="Awesome Moment",
            description="A great clip from the video",
            tags=["gaming", "highlight"]
        )
        
        assert request.video_path == "/path/to/video.mp4"
        assert request.start_time == 10.5
        assert request.end_time == 45.2
        assert request.title == "Awesome Moment"
        assert request.description == "A great clip from the video"
        assert request.tags == ["gaming", "highlight"]
    
    def test_valid_request_minimal_fields(self) -> None:
        """
        Test valid request with only required fields.
        
        Verifies that a request with only the required video_path field
        validates successfully, with optional fields defaulting to None.
        """
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4"
        )
        
        assert request.video_path == "/path/to/video.mp4"
        assert request.start_time is None
        assert request.end_time is None
        assert request.title is None
        assert request.description is None
        assert request.tags is None
    
    def test_missing_required_field(self) -> None:
        """
        Test that missing required field raises validation error.
        
        Verifies that video_path is required and cannot be omitted.
        """
        with pytest.raises(ValidationError) as exc_info:
            ClipGenerationRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "video_path" in str(errors)
    
    def test_negative_start_time_validation(self) -> None:
        """
        Test that negative start_time is rejected.
        
        Verifies that the ge=0 constraint prevents negative time values.
        """
        with pytest.raises(ValidationError):
            ClipGenerationRequest(
                video_path="/path/to/video.mp4",
                start_time=-10.0
            )
    
    def test_negative_end_time_validation(self) -> None:
        """
        Test that negative end_time is rejected.
        
        Verifies that the ge=0 constraint prevents negative time values.
        """
        with pytest.raises(ValidationError):
            ClipGenerationRequest(
                video_path="/path/to/video.mp4",
                end_time=-5.0
            )
    
    def test_zero_times_are_valid(self) -> None:
        """
        Test that zero is a valid time value.
        
        Verifies that ge=0 constraint allows zero values.
        """
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            start_time=0.0,
            end_time=0.0
        )
        
        assert request.start_time == 0.0
        assert request.end_time == 0.0
    
    def test_title_max_length(self) -> None:
        """
        Test that title exceeding max_length is rejected.
        
        Verifies that titles longer than 256 characters are rejected.
        """
        with pytest.raises(ValidationError):
            ClipGenerationRequest(
                video_path="/path/to/video.mp4",
                title="x" * 257
            )
    
    def test_title_at_max_length(self) -> None:
        """
        Test that title at max_length is valid.
        
        Verifies that a title exactly 256 characters is accepted.
        """
        long_title = "x" * 256
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            title=long_title
        )
        
        assert len(request.title) == 256
    
    def test_description_max_length(self) -> None:
        """
        Test that description exceeding max_length is rejected.
        
        Verifies that descriptions longer than 1024 characters are rejected.
        """
        with pytest.raises(ValidationError):
            ClipGenerationRequest(
                video_path="/path/to/video.mp4",
                description="x" * 1025
            )
    
    def test_description_at_max_length(self) -> None:
        """
        Test that description at max_length is valid.
        
        Verifies that a description exactly 1024 characters is accepted.
        """
        long_description = "x" * 1024
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            description=long_description
        )
        
        assert len(request.description) == 1024
    
    def test_empty_tags_list(self) -> None:
        """
        Test that empty tags list is valid.
        
        Verifies that an empty list is accepted for tags.
        """
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            tags=[]
        )
        
        assert request.tags == []
    
    def test_tags_with_multiple_items(self) -> None:
        """
        Test that tags can contain multiple items.
        
        Verifies that tags can be a list with various items.
        """
        tags = ["action", "adventure", "comedy", "drama"]
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            tags=tags
        )
        
        assert request.tags == tags
        assert len(request.tags) == 4
    
    def test_request_serialization(self) -> None:
        """
        Test that request can be serialized to dict.
        
        Verifies that the request model can be converted to a dictionary.
        """
        request = ClipGenerationRequest(
            video_path="/path/to/video.mp4",
            start_time=10.0,
            title="Test"
        )
        
        data = request.model_dump()
        assert isinstance(data, dict)
        assert data["video_path"] == "/path/to/video.mp4"
        assert data["start_time"] == 10.0
        assert data["title"] == "Test"


class TestClipGenerationResponse:
    """Tests for ClipGenerationResponse serialization schema."""
    
    def test_response_creation(self) -> None:
        """
        Test creating a ClipGenerationResponse.
        
        Verifies that the response model can be instantiated with required fields.
        """
        response = ClipGenerationResponse(
            job_id="550e8400-e29b-41d4-a716-446655440000",
            status="pending",
            message="Clip generation job queued successfully"
        )
        
        assert response.job_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.status == "pending"
        assert response.message == "Clip generation job queued successfully"
    
    def test_response_serialization(self) -> None:
        """
        Test that response can be serialized to dict.
        
        Verifies that the response model can be converted to a dictionary.
        """
        response = ClipGenerationResponse(
            job_id="test-job-id",
            status="processing",
            message="Processing..."
        )
        
        data = response.model_dump()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "processing"
        assert data["message"] == "Processing..."
    
    def test_response_missing_required_field(self) -> None:
        """
        Test that missing required field raises validation error.
        
        Verifies that all fields are required in the response.
        """
        with pytest.raises(ValidationError):
            ClipGenerationResponse(
                job_id="test-job",
                status="pending"
                # Missing message
            )


class TestJobStatusResponse:
    """Tests for JobStatusResponse serialization schema."""
    
    def test_response_creation_pending(self) -> None:
        """
        Test creating a JobStatusResponse for pending job.
        
        Verifies that the response model can be created with pending status.
        """
        response = JobStatusResponse(
            job_id="test-job-id",
            status="pending",
            output_file=None,
            error_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
        )
        
        assert response.job_id == "test-job-id"
        assert response.status == "pending"
        assert response.output_file is None
        assert response.error_message is None
    
    def test_response_creation_completed(self) -> None:
        """
        Test creating a JobStatusResponse for completed job.
        
        Verifies that the response model includes output_file for completed jobs.
        """
        response = JobStatusResponse(
            job_id="test-job-id",
            status="completed",
            output_file="/path/to/output/clip.mp4",
            error_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        
        assert response.status == "completed"
        assert response.output_file == "/path/to/output/clip.mp4"
        assert response.completed_at is not None
    
    def test_response_creation_failed(self) -> None:
        """
        Test creating a JobStatusResponse for failed job.
        
        Verifies that the response model includes error_message for failed jobs.
        """
        response = JobStatusResponse(
            job_id="test-job-id",
            status="failed",
            output_file=None,
            error_message="Video file not found",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
        )
        
        assert response.status == "failed"
        assert response.error_message == "Video file not found"
        assert response.output_file is None
    
    def test_response_serialization(self) -> None:
        """
        Test that response can be serialized to dict with timestamps.
        
        Verifies that datetime fields are properly serialized.
        """
        now = datetime.utcnow()
        response = JobStatusResponse(
            job_id="test-job",
            status="pending",
            output_file=None,
            error_message=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
        
        data = response.model_dump()
        assert data["job_id"] == "test-job"
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
    
    def test_response_missing_required_field(self) -> None:
        """
        Test that missing required field raises validation error.
        
        Verifies that job_id is required.
        """
        with pytest.raises(ValidationError):
            JobStatusResponse(
                status="pending",
                output_file=None,
                error_message=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=None,
                # Missing job_id
            )
    
    def test_response_with_all_timestamps(self) -> None:
        """
        Test response with all timestamp fields populated.
        
        Verifies that all timestamp fields can be set and retrieved.
        """
        created = datetime(2026, 1, 1, 10, 0, 0)
        updated = datetime(2026, 1, 1, 12, 0, 0)
        completed = datetime(2026, 1, 1, 14, 0, 0)
        
        response = JobStatusResponse(
            job_id="test-job",
            status="completed",
            output_file="/output/clip.mp4",
            error_message=None,
            created_at=created,
            updated_at=updated,
            completed_at=completed,
        )
        
        assert response.created_at == created
        assert response.updated_at == updated
        assert response.completed_at == completed
