#!/usr/bin/env python3
"""
Test script for ClipsAI Server API with video download support.

This script demonstrates how to use the API with both local files and URLs.
"""

import requests
import time
import argparse
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/clips"


def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running at", f"{BASE_URL}/health")
            return True
    except requests.exceptions.ConnectionError:
        pass
    print("✗ Server is not running. Start it with: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
    return False


def submit_job(video_path: str):
    """Submit a clip generation job."""
    print(f"\n📥 Submitting job with video: {video_path}")
    print(f"   Is URL: {video_path.startswith('http')}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"video_path": video_path},
            timeout=10
        )
        
        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print(f"✓ Job submitted successfully")
            print(f"  Job ID: {job_id}")
            return job_id
        else:
            print(f"✗ Failed to submit job (HTTP {response.status_code})")
            print(f"  Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Error submitting job: {e}")
        return None


def check_status(job_id: str):
    """Check job status."""
    try:
        response = requests.get(
            f"{BASE_URL}/status/{job_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to get status (HTTP {response.status_code})")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Error checking status: {e}")
        return None


def monitor_job(job_id: str, check_interval: int = 3, max_attempts: int = 300):
    """Monitor job progress."""
    print(f"\n⏳ Monitoring job {job_id}")
    print(f"   Checking every {check_interval}s (timeout in {max_attempts * check_interval}s)\n")
    
    for attempt in range(max_attempts):
        status_data = check_status(job_id)
        
        if not status_data:
            print("Failed to check status")
            return False
        
        status = status_data.get("status")
        message = status_data.get("status_message", "")
        
        if status == "processing":
            print(f"  [{attempt + 1:3d}] {message or 'Processing...'}")
            time.sleep(check_interval)
        elif status == "completed":
            clips = status_data.get("generated_clips", [])
            print(f"\n✓ Job completed!")
            print(f"  Generated {len(clips)} clips:")
            for i, clip in enumerate(clips, 1):
                print(f"    {i}. {clip['filename']}")
                print(f"       Duration: {clip['duration']:.2f}s ({clip['start_time']:.2f}s - {clip['end_time']:.2f}s)")
            return True
        elif status == "failed":
            print(f"\n✗ Job failed!")
            print(f"  Error: {status_data.get('error_message')}")
            return False
        else:
            print(f"  [{attempt + 1:3d}] Status: {status}")
            time.sleep(check_interval)
    
    print("\n✗ Job monitoring timed out")
    return False


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test ClipsAI Server API with video download support"
    )
    parser.add_argument(
        "video_path",
        help="Path to local video file or URL (http/https)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Status check interval in seconds (default: 3)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum monitoring time in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("ClipsAI Server - API Test Script")
    print("=" * 70)
    
    # Check server
    if not check_server():
        return 1
    
    # Validate input
    video_path = args.video_path
    is_url = video_path.startswith("http://") or video_path.startswith("https://")
    
    if not is_url:
        if not Path(video_path).exists():
            print(f"\n✗ File not found: {video_path}")
            return 1
    
    # Submit job
    job_id = submit_job(video_path)
    if not job_id:
        return 1
    
    # Monitor job
    max_checks = max(1, args.timeout // args.interval)
    success = monitor_job(job_id, args.interval, max_checks)
    
    print("\n" + "=" * 70)
    if success:
        print("✓ Test completed successfully!")
        return 0
    else:
        print("✗ Test failed")
        return 1


if __name__ == "__main__":
    exit(main())
