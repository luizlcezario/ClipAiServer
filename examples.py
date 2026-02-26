"""
Practical examples for using the Clips AI Server API.

This module provides practical examples of:
- Using the API endpoints with curl commands
- Python client code to submit clip generation requests
- How to poll for job status
- How to download completed clips
- Example requests with proper JSON payloads

Before running examples:
1. Start the server: python -m uvicorn app.main:app --reload
2. The API will be available at http://localhost:8000
3. API documentation: http://localhost:8000/docs
"""

import requests
import json
import time
from typing import Dict, Optional
from pathlib import Path


# ============================================================================
# API CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"
API_ENDPOINT_GENERATE = f"{API_BASE_URL}/api/clips/generate"
API_ENDPOINT_STATUS = f"{API_BASE_URL}/api/clips/status"
API_ENDPOINT_HEALTH = f"{API_BASE_URL}/api/clips/health"


# ============================================================================
# CURL EXAMPLES
# ============================================================================

CURL_EXAMPLES = """
CURL COMMAND EXAMPLES
====================

1. HEALTH CHECK
   Check if the API server is running:

   curl -X GET http://localhost:8000/api/clips/health


2. SUBMIT A CLIP GENERATION JOB
   Submit a clip generation request:

   curl -X POST http://localhost:8000/api/clips/generate \\
     -H "Content-Type: application/json" \\
     -d '{
       "video_path": "/path/to/video.mp4",
       "start_time": 10.5,
       "end_time": 45.2,
       "title": "Awesome Moment",
       "description": "A great clip from the video",
       "tags": ["gaming", "highlight"]
     }'

   Response (example):
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "pending",
     "message": "Clip generation job queued successfully"
   }


3. CHECK JOB STATUS
   Check the status of a clip generation job:

   curl -X GET http://localhost:8000/api/clips/status/550e8400-e29b-41d4-a716-446655440000

   Response (example - pending):
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "pending",
     "output_file": null,
     "error_message": null,
     "created_at": "2026-02-26T10:30:45.123456",
     "updated_at": "2026-02-26T10:30:45.123456",
     "completed_at": null
   }

   Response (example - completed):
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "completed",
     "output_file": "./clips_output/550e8400-e29b-41d4-a716-446655440000.mp4",
     "error_message": null,
     "created_at": "2026-02-26T10:30:45.123456",
     "updated_at": "2026-02-26T10:30:52.654321",
     "completed_at": "2026-02-26T10:30:52.654321"
   }


4. MINIMAL REQUEST (required fields only)
   Minimal request with just the video path:

   curl -X POST http://localhost:8000/api/clips/generate \\
     -H "Content-Type: application/json" \\
     -d '{
       "video_path": "/path/to/video.mp4"
     }'
"""


# ============================================================================
# PYTHON CLIENT CLASS
# ============================================================================

class ClipsAIClient:
    """
    Python client for interacting with the Clips AI Server API.

    Example usage:
        client = ClipsAIClient("http://localhost:8000")
        job = client.generate_clip("/path/to/video.mp4", title="My Clip")
        print(f"Job ID: {job['job_id']}")
    """

    def __init__(self, base_url: str = API_BASE_URL):
        """
        Initialize the Clips AI client.

        Args:
            base_url: Base URL of the Clips AI Server (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict:
        """
        Check if the API server is running and healthy.

        Returns:
            dict: Health status information

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        response = self.session.get(f"{self.base_url}/api/clips/health")
        response.raise_for_status()
        return response.json()

    def generate_clip(
        self,
        video_path: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> Dict:
        """
        Submit a clip generation request.

        Args:
            video_path: Path to the input video file
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            title: Title for the clip (optional)
            description: Description for the clip (optional)
            tags: List of tags for the clip (optional)

        Returns:
            dict: Job ID and initial status

        Raises:
            requests.exceptions.RequestException: If request fails
            ValueError: If response is invalid
        """
        payload = {
            "video_path": video_path,
        }

        # Add optional fields if provided
        if start_time is not None:
            payload["start_time"] = start_time
        if end_time is not None:
            payload["end_time"] = end_time
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags

        response = self.session.post(
            f"{self.base_url}/api/clips/generate",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a clip generation job.

        Args:
            job_id: The unique job identifier from generate_clip()

        Returns:
            dict: Current job status and details

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        response = self.session.get(
            f"{self.base_url}/api/clips/status/{job_id}",
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> Dict:
        """
        Wait for a clip generation job to complete.

        Args:
            job_id: The unique job identifier
            max_wait_seconds: Maximum time to wait in seconds (default: 300)
            poll_interval: Time between status checks in seconds (default: 2.0)

        Returns:
            dict: Final job status

        Raises:
            TimeoutError: If job doesn't complete within max_wait_seconds
            requests.exceptions.RequestException: If request fails
        """
        start_time = time.time()
        elapsed = 0

        while elapsed < max_wait_seconds:
            status = self.get_job_status(job_id)

            if status["status"] in ["completed", "failed"]:
                return status

            elapsed = time.time() - start_time
            print(
                f"Job {job_id} is {status['status']}... "
                f"({elapsed:.1f}s elapsed)"
            )
            time.sleep(poll_interval)

        raise TimeoutError(
            f"Job {job_id} did not complete within {max_wait_seconds} seconds"
        )

    def close(self):
        """Close the client session."""
        self.session.close()


# ============================================================================
# PRACTICAL USAGE EXAMPLES
# ============================================================================

def example_1_basic_usage():
    """
    Example 1: Basic usage - submit a clip and check status.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Usage - Submit Clip and Check Status")
    print("=" * 70)

    client = ClipsAIClient()

    try:
        # Check if server is running
        print("\n1. Health check...")
        health = client.health_check()
        print(f"   Server status: {health['status']}")

        # Submit a clip generation request
        print("\n2. Submitting clip generation request...")
        request_payload = {
            "video_path": "/path/to/sample_video.mp4",
            "start_time": 10.0,
            "end_time": 30.0,
            "title": "Amazing Highlight",
            "description": "Best moment from the video",
            "tags": ["highlight", "action"],
        }
        print(f"   Request payload: {json.dumps(request_payload, indent=2)}")

        job = client.generate_clip(**request_payload)
        job_id = job["job_id"]
        print(f"   ✓ Job submitted successfully")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {job['status']}")

        # Check status
        print("\n3. Checking job status...")
        status = client.get_job_status(job_id)
        print(f"   Status: {status['status']}")
        print(f"   Created at: {status['created_at']}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        client.close()


def example_2_wait_for_completion():
    """
    Example 2: Submit a clip and wait for completion.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Wait for Job Completion")
    print("=" * 70)

    client = ClipsAIClient()

    try:
        # Submit request
        print("\n1. Submitting clip generation request...")
        job = client.generate_clip(
            video_path="/path/to/sample_video.mp4",
            start_time=5.0,
            end_time=25.0,
            title="Quick Clip",
        )
        job_id = job["job_id"]
        print(f"   Job ID: {job_id}")

        # Wait for completion
        print("\n2. Waiting for job to complete (checking every 2 seconds)...")
        final_status = client.wait_for_completion(
            job_id,
            max_wait_seconds=60,
            poll_interval=2.0,
        )

        print(f"\n3. Job completed!")
        print(f"   Status: {final_status['status']}")

        if final_status["status"] == "completed":
            print(f"   Output file: {final_status['output_file']}")
            print(f"   Completed at: {final_status['completed_at']}")
        else:
            print(f"   Error: {final_status['error_message']}")

    except TimeoutError as e:
        print(f"   ✗ {e}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        client.close()


def example_3_batch_requests():
    """
    Example 3: Submit multiple clip generation requests.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Batch Requests - Submit Multiple Clips")
    print("=" * 70)

    client = ClipsAIClient()

    try:
        # Submit multiple requests
        print("\n1. Submitting 3 clip generation requests...")
        job_ids = []

        clip_configs = [
            {
                "video_path": "/path/to/video1.mp4",
                "title": "Clip 1",
                "tags": ["action"],
            },
            {
                "video_path": "/path/to/video2.mp4",
                "start_time": 10.0,
                "end_time": 30.0,
                "title": "Clip 2",
            },
            {
                "video_path": "/path/to/video3.mp4",
                "title": "Clip 3",
                "tags": ["comedy", "funny"],
            },
        ]

        for i, config in enumerate(clip_configs, 1):
            job = client.generate_clip(**config)
            job_ids.append(job["job_id"])
            print(f"   {i}. {config['title']}: {job['job_id']}")

        # Check status of all jobs
        print("\n2. Checking status of all jobs...")
        for job_id in job_ids:
            status = client.get_job_status(job_id)
            print(f"   {job_id}: {status['status']}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        client.close()


def example_4_error_handling():
    """
    Example 4: Error handling - dealing with various error scenarios.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Error Handling")
    print("=" * 70)

    client = ClipsAIClient()

    try:
        # Example 1: Invalid job ID
        print("\n1. Checking status of non-existent job...")
        try:
            status = client.get_job_status("invalid-job-id-12345")
        except requests.exceptions.HTTPError as e:
            print(f"   ✓ Handled error: {e.response.status_code} - {e.response.json()['detail']}")

        # Example 2: Invalid request (missing required field)
        print("\n2. Submitting invalid request (missing video_path)...")
        try:
            response = client.session.post(
                f"{API_BASE_URL}/api/clips/generate",
                json={"title": "Incomplete Request"},
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"   ✓ Handled error: {e.response.status_code}")

        # Example 3: Unreachable server
        print("\n3. Attempting to connect to unreachable server...")
        bad_client = ClipsAIClient("http://localhost:9999")
        try:
            bad_client.health_check()
        except requests.exceptions.ConnectionError as e:
            print(f"   ✓ Handled error: Connection refused")
        finally:
            bad_client.close()

    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    finally:
        client.close()


# ============================================================================
# JSON PAYLOAD EXAMPLES
# ============================================================================

JSON_EXAMPLES = """
JSON PAYLOAD EXAMPLES
====================

1. MINIMAL REQUEST
   Only required fields:
   
   {
     "video_path": "/path/to/video.mp4"
   }


2. FULL REQUEST
   All available fields:
   
   {
     "video_path": "/path/to/video.mp4",
     "start_time": 10.5,
     "end_time": 45.2,
     "title": "Awesome Moment",
     "description": "A great clip from the video with interesting content",
     "tags": ["gaming", "highlight", "reaction"]
   }


3. WITH TIME BOUNDS
   Extract a specific segment:
   
   {
     "video_path": "/path/to/long_video.mp4",
     "start_time": 120.0,
     "end_time": 180.0,
     "title": "Middle Section"
   }


4. WITH METADATA
   Include descriptive information:
   
   {
     "video_path": "/videos/livestream.mp4",
     "title": "Epic Gaming Moment",
     "description": "Incredible play from the championship finals",
     "tags": ["esports", "championship", "highlight", "2024"]
   }


5. RESPONSE - PENDING JOB
   Immediate response when job is submitted:
   
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "pending",
     "message": "Clip generation job queued successfully"
   }


6. RESPONSE - COMPLETED JOB
   Status response when job is complete:
   
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "completed",
     "output_file": "./clips_output/550e8400-e29b-41d4-a716-446655440000.mp4",
     "error_message": null,
     "created_at": "2026-02-26T10:30:45.123456",
     "updated_at": "2026-02-26T10:30:52.654321",
     "completed_at": "2026-02-26T10:30:52.654321"
   }


7. RESPONSE - FAILED JOB
   Status response when job fails:
   
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "failed",
     "output_file": null,
     "error_message": "File not found: /path/to/video.mp4",
     "created_at": "2026-02-26T10:30:45.123456",
     "updated_at": "2026-02-26T10:30:47.987654",
     "completed_at": "2026-02-26T10:30:47.987654"
   }
"""


# ============================================================================
# MAIN - RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "CLIPS AI SERVER - PRACTICAL EXAMPLES" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")

    print("\nBefore running examples:")
    print("1. Ensure the Clips AI Server is running:")
    print("   python -m uvicorn app.main:app --reload")
    print("2. Ensure you have sample video files at the paths used in examples")
    print("3. Check API documentation at: http://localhost:8000/docs")

    # Print curl examples
    print(CURL_EXAMPLES)

    # Print JSON examples
    print(JSON_EXAMPLES)

    # Uncomment to run actual examples (requires running server and valid video files):
    # example_1_basic_usage()
    # example_2_wait_for_completion()
    # example_3_batch_requests()
    # example_4_error_handling()

    print("\n" + "=" * 70)
    print("To run the Python examples, uncomment them at the bottom of this file")
    print("=" * 70 + "\n")
