"""
Unit tests for API routes.

This module tests the FastAPI endpoints for clip generation and job status tracking.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest


class TestHealthCheck:
    """Tests for the health check endpoint."""
    
    def test_ping_endpoint(self, test_client: TestClient) -> None:
        """
        Test the /ping endpoint.
        
        Verifies that the health check endpoint returns a successful response
        with the expected structure.
        """
        response = test_client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        assert "pong" in data
        assert data["pong"] is True


class TestGenerateClip:
    """Tests for the clip generation endpoint."""
    
    def test_generate_clip_success(
        self,
        test_client: TestClient,
        test_db: Session,
        sample_clip_request: ClipGenerationRequest,
    ) -> None:
        """
        Test successful clip generation request.
        
        Verifies that a valid clip generation request:
        - Returns 202 Accepted status
        - Contains a valid job_id
        - Has the correct status "pending"
        - Contains a success message
        - Creates a database record
        """
        response = test_client.post(
            "/api/clips/generate",
            json=sample_clip_request.model_dump()
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify response structure
        assert "job_id" in data
        assert "status" in data
        assert "message" in data
        
        # Verify response values
        assert len(data["job_id"]) > 0
        assert data["status"] == "pending"
        assert "queued successfully" in data["message"].lower()
        
        # Verify database record was created
        job = test_db.query(ClipJob).filter(
            ClipJob.job_id == data["job_id"]
        ).first()
        assert job is not None
        assert job.status == JobStatus.PENDING
        assert job.input_file == sample_clip_request.video_path
    
    def test_generate_clip_minimal_request(
        self,
        test_client: TestClient,
        test_db: Session,
    ) -> None:
        """
        Test clip generation with minimal required fields.
        
        Verifies that a request with only the required video_path field
        is accepted and processed correctly.
        """
        response = test_client.post(
            "/api/clips/generate",
            json={"video_path": "/path/to/video.mp4"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
        
        # Verify optional fields are preserved as None
        job = test_db.query(ClipJob).filter(
            ClipJob.job_id == data["job_id"]
        ).first()
        assert job is not None
    
    def test_generate_clip_missing_required_field(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test clip generation with missing required field.
        
        Verifies that a request without the required video_path field
        returns a validation error.
        """
        response = test_client.post(
            "/api/clips/generate",
            json={"start_time": 10.0}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_generate_clip_invalid_times(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test clip generation with invalid time values.
        
        Verifies that negative time values are rejected by validation.
        """
        response = test_client.post(
            "/api/clips/generate",
            json={
                "video_path": "/path/to/video.mp4",
                "start_time": -10.0,  # Invalid: negative
                "end_time": 30.0
            }
        )
        
        assert response.status_code == 422
    
    def test_generate_clip_title_too_long(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test clip generation with title exceeding max length.
        
        Verifies that titles longer than the max_length constraint
        are rejected by validation.
        """
        response = test_client.post(
            "/api/clips/generate",
            json={
                "video_path": "/path/to/video.mp4",
                "title": "x" * 300  # Exceeds max_length of 256
            }
        )
        
        assert response.status_code == 422
    
    def test_generate_clip_description_too_long(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test clip generation with description exceeding max length.
        
        Verifies that descriptions longer than the max_length constraint
        are rejected by validation.
        """
        response = test_client.post(
            "/api/clips/generate",
            json={
                "video_path": "/path/to/video.mp4",
                "description": "x" * 1100  # Exceeds max_length of 1024
            }
        )
        
        assert response.status_code == 422


class TestGetJobStatus:
    """Tests for the job status endpoint."""
    
    def test_get_job_status_pending(
        self,
        test_client: TestClient,
        sample_clip_job: ClipJob,
    ) -> None:
        """
        Test getting status of a pending job.
        
        Verifies that the endpoint returns correct information for
        a job in pending state.
        """
        response = test_client.get(
            f"/api/clips/status/{sample_clip_job.job_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["job_id"] == sample_clip_job.job_id
        assert data["status"] == "pending"
        assert "output_file" in data
        assert "error_message" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_job_status_completed(
        self,
        test_client: TestClient,
        test_db: Session,
    ) -> None:
        """
        Test getting status of a completed job.
        
        Verifies that the endpoint returns correct information for
        a job in completed state with output file path.
        """
        # Create a completed job
        job = ClipJob(
            job_id="completed-job-123",
            status=JobStatus.COMPLETED,
            input_file="/path/to/video.mp4",
            output_file="/path/to/output/clip.mp4",
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/api/clips/status/{job.job_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job.job_id
        assert data["status"] == "completed"
        assert data["output_file"] == "/path/to/output/clip.mp4"
        assert data["error_message"] is None
    
    def test_get_job_status_failed(
        self,
        test_client: TestClient,
        test_db: Session,
    ) -> None:
        """
        Test getting status of a failed job.
        
        Verifies that the endpoint returns correct information for
        a job in failed state with error message.
        """
        # Create a failed job
        job = ClipJob(
            job_id="failed-job-123",
            status=JobStatus.FAILED,
            input_file="/path/to/video.mp4",
            error_message="Video file not found",
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/api/clips/status/{job.job_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job.job_id
        assert data["status"] == "failed"
        assert data["error_message"] == "Video file not found"
        assert data["output_file"] is None
    
    def test_get_job_status_processing(
        self,
        test_client: TestClient,
        test_db: Session,
    ) -> None:
        """
        Test getting status of a processing job.
        
        Verifies that the endpoint returns correct information for
        a job in processing state.
        """
        # Create a processing job
        job = ClipJob(
            job_id="processing-job-123",
            status=JobStatus.PROCESSING,
            input_file="/path/to/video.mp4",
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/api/clips/status/{job.job_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "processing"
    
    def test_get_job_status_invalid_job_id(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test getting status with non-existent job ID.
        
        Verifies that the endpoint returns 404 Not Found when
        the job ID doesn't exist in the database.
        """
        response = test_client.get(
            "/api/clips/status/non-existent-job-id-xyz"
        )
        
        assert response.status_code == 404
    
    def test_get_job_status_empty_job_id(
        self,
        test_client: TestClient,
    ) -> None:
        """
        Test getting status with empty job ID.
        
        Verifies proper handling of empty job ID in the URL.
        """
        response = test_client.get("/api/clips/status/")
        
        # FastAPI should either return 404 or redirect
        assert response.status_code in [404, 307]
