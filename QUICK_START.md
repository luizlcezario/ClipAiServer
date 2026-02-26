# Quick Start Guide - Video Download Feature

## 🚀 Get Started in 5 Minutes

### Step 1: Start the Server
```bash
cd /home/lcezario/code/ClipsAiServer
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 2: Test in Another Terminal
```bash
cd /home/lcezario/code/ClipsAiServer
source venv/bin/activate
```

#### Option A: Test with Local Video
```bash
# Create a test video first
bash create_test_video.sh

# Then process it
python test_api.py test_video.mp4
```

#### Option B: Test with URL
```bash
python test_api.py "https://example.com/video.mp4"
```

#### Option C: Manual curl Test
```bash
# Submit a URL
curl -X POST http://127.0.0.1:8000/api/clips/generate \
  -H "Content-Type: application/json" \
  -d '{"video_path": "https://example.com/video.mp4"}'

# Get response with job_id
# {"job_id":"550e8400-e29b-41d4-a716-446655440000","status":"processing","message":"..."}

# Check status
curl http://127.0.0.1:8000/api/clips/status/550e8400-e29b-41d4-a716-446655440000
```

## 📋 What Happens

When you submit a video URL:

1. **[Downloaded]** Server downloads the video to `./temp_uploads/`
2. **[Transcribed]** WhisperX converts audio to text
3. **[Detected]** ClipsAI finds optimal clip segments
4. **[Trimmed]** Video is split into individual clips
5. **[Stored]** Clips saved to `./clips_output/{job_id}/`

## 💻 API Endpoints

### Submit Video (Local or URL)
```
POST /api/clips/generate
Content-Type: application/json

{
  "video_path": "https://example.com/video.mp4"
}

Response (202 Accepted):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Clip generation job queued successfully..."
}
```

### Check Status
```
GET /api/clips/status/{job_id}

Response (200 OK):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "status_message": "Baixando vídeo da web...",
  "generated_clips": null,
  "error_message": null,
  "created_at": "2026-02-26T10:00:00",
  "updated_at": "2026-02-26T10:00:05",
  "completed_at": null
}
```

### Health Check
```
GET /api/clips/health

Response:
{
  "status": "healthy",
  "message": "Clips AI Server is running"
}
```

## 🎯 Real-World Examples

### Example 1: Download & Process Meeting Recording
```bash
python test_api.py "https://storage.example.com/meetings/2026-02-26.mp4"
```

### Example 2: Process Webinar with High Timeout
```bash
python test_api.py \
  "https://webinar.example.com/recording.mp4" \
  --timeout 900 \
  --interval 10
```

### Example 3: Python Script
```python
import requests
import time

def process_video(url):
    # Submit
    job = requests.post(
        "http://127.0.0.1:8000/api/clips/generate",
        json={"video_path": url}
    ).json()
    
    job_id = job["job_id"]
    print(f"Job: {job_id}")
    
    # Wait for completion
    while True:
        status = requests.get(
            f"http://127.0.0.1:8000/api/clips/status/{job_id}"
        ).json()
        
        if status["status"] == "completed":
            return status["generated_clips"]
        elif status["status"] == "failed":
            raise Exception(status["error_message"])
        
        print(f"... {status.get('status_message')}")
        time.sleep(5)

# Process a video
clips = process_video("https://example.com/video.mp4")
print(f"Generated {len(clips)} clips!")
```

## 📊 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Download 100MB video | 30-60s | Depends on server & connection |
| Transcribe 30min video | 2-5 min | Uses WhisperX |
| Detect clips | 10-30s | Analyzes transcription |
| Trim clips | 10-30s | Video processing |
| **Total** | **3-6 min** | For typical 30-min video |

## 🐛 Troubleshooting

### Server not starting?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
pkill -f "uvicorn app.main"

# Try different port
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Download fails?
```bash
# Check URL is accessible
curl -I "https://example.com/video.mp4"

# Check file size (limit is 2GB by default)
# Check internet connection
ping example.com
```

### Clips not generating?
```bash
# Check if temp files were downloaded
ls -la ./temp_uploads/

# Check output directory
ls -la ./clips_output/

# Check server logs for errors
tail -f server.log
```

### Test videos not found?
```bash
# Create test video
bash create_test_video.sh

# Verify it exists
ls -lah test_video.mp4
```

## 📚 Full Documentation

For complete documentation, see:
- `README.md` - Project overview
- `SETUP_GUIDE.md` - Installation and configuration
- `DOWNLOAD_FEATURE_SUMMARY.md` - Download feature details

## 🎓 Next Steps

1. ✅ Start the server
2. ✅ Run test_api.py with a video
3. ✅ Monitor the status
4. ✅ Retrieve generated clips
5. 🔄 Integrate into your application

Good luck! 🚀
