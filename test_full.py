#!/usr/bin/env python3
"""
Complete test suite and demonstration of ClipsAI Server functionality.

This module provides examples for:
1. Health checks
2. Submitting local videos
3. Submitting video URLs
4. Monitoring job progress
5. Error handling
"""

import requests
import time
import json
from pathlib import Path


class ClipsAITestClient:
    """Test client for ClipsAI Server API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/clips"):
        """Initialize test client."""
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Test health endpoint."""
        print("\n" + "=" * 70)
        print("TEST 1: Health Check")
        print("=" * 70)
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✓ Server is healthy")
                print(f"  Response: {response.json()}")
                return True
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to server")
            print(f"  Make sure server is running at {self.base_url}")
            return False

    def test_local_video(self, video_path: str) -> bool:
        """Test with local video file."""
        print("\n" + "=" * 70)
        print("TEST 2: Submit Local Video")
        print("=" * 70)
        
        if not Path(video_path).exists():
            print(f"✗ Video file not found: {video_path}")
            return False
        
        print(f"Video: {video_path}")
        print(f"File size: {Path(video_path).stat().st_size / (1024*1024):.2f}MB")
        
        # Submit
        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json={"video_path": video_path}
            )
            
            if response.status_code == 202:
                job_id = response.json()["job_id"]
                print(f"✓ Job submitted: {job_id}")
                
                # Monitor
                return self._monitor_job(job_id)
            else:
                print(f"✗ Failed (HTTP {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def test_url_video(self, video_url: str) -> bool:
        """Test with video URL."""
        print("\n" + "=" * 70)
        print("TEST 3: Submit Video URL (Auto-Download)")
        print("=" * 70)
        
        print(f"URL: {video_url}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json={"video_path": video_url}
            )
            
            if response.status_code == 202:
                job_id = response.json()["job_id"]
                print(f"✓ Job submitted: {job_id}")
                
                # Monitor with longer timeout for downloads
                return self._monitor_job(job_id, check_interval=5, max_attempts=180)
            else:
                print(f"✗ Failed (HTTP {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def test_invalid_url(self) -> bool:
        """Test error handling with invalid URL."""
        print("\n" + "=" * 70)
        print("TEST 4: Error Handling - Invalid URL")
        print("=" * 70)
        
        invalid_url = "https://example.com/nonexistent/video.mp4"
        print(f"URL: {invalid_url}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json={"video_path": invalid_url},
                timeout=10
            )
            
            if response.status_code == 202:
                job_id = response.json()["job_id"]
                print(f"Job submitted: {job_id}")
                
                # Wait for failure
                for _ in range(30):
                    status = self.session.get(
                        f"{self.base_url}/status/{job_id}"
                    ).json()
                    
                    if status["status"] == "failed":
                        print(f"✓ Job failed as expected")
                        print(f"  Error: {status['error_message']}")
                        return True
                    elif status["status"] == "processing":
                        print(f"  Status: {status.get('status_message')}")
                    
                    time.sleep(1)
                
                print("✗ Job did not fail in time")
                return False
            else:
                print(f"✗ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def _monitor_job(self, job_id: str, check_interval: int = 3, max_attempts: int = 120) -> bool:
        """Monitor a job until completion."""
        print(f"\nMonitoring job progress:")
        
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.base_url}/status/{job_id}")
                status_data = response.json()
                
                status = status_data.get("status")
                message = status_data.get("status_message", "")
                
                if status == "processing":
                    print(f"  [{attempt + 1:3d}] {message or 'Processing...'}")
                elif status == "completed":
                    clips = status_data.get("generated_clips", [])
                    print(f"\n✓ Completed with {len(clips)} clips")
                    for i, clip in enumerate(clips, 1):
                        print(f"    {i}. {clip['filename']} ({clip['duration']:.2f}s)")
                    return True
                elif status == "failed":
                    print(f"\n✗ Job failed: {status_data.get('error_message')}")
                    return False
                else:
                    print(f"  [{attempt + 1:3d}] Status: {status}")
                
                time.sleep(check_interval)
            except Exception as e:
                print(f"✗ Error checking status: {e}")
                return False
        
        print("\n✗ Monitoring timeout")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ClipsAI Server - Full Test Suite")
    print("=" * 70)
    
    client = ClipsAITestClient()
    
    # Test 1: Health
    if not client.health_check():
        print("\n✗ Server not available. Start it with:")
        print("  source venv/bin/activate")
        print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return 1
    
    # Test 2: Local video (if available)
    test_video = Path("test_video.mp4")
    if test_video.exists():
        client.test_local_video(str(test_video))
    else:
        print("\n⚠ Skipping local video test (create one with: bash create_test_video.sh)")
    
    # Test 3: Invalid URL (demonstrates error handling)
    client.test_invalid_url()
    
    print("\n" + "=" * 70)
    print("Tests completed!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())
