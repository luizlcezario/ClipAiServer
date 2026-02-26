# Clips AI Server

A FastAPI-based server for generating video clips using ClipsAI library with WhisperX transcription. Supports downloading videos directly from the web.

## Features

- **Web Video Download** - Automatically download videos from HTTP/HTTPS URLs
- **WhisperX Transcription** for accurate speech-to-text before clip detection
- **Asynchronous clip generation** using FastAPI background tasks
- **Multi-clip detection** automatically finds optimal clip segments
- **Database tracking** of clip generation jobs with SQLAlchemy ORM
- **File storage management** for uploads and outputs
- **Type-safe schemas** with Pydantic
- **Environment configuration** with .env file support
- **RESTful API** with comprehensive error handling
- **Progress tracking** with detailed status messages
- **Clip metadata** including start/end times and durations

## How It Works

```
Video Input (Local or URL)
    ↓
[VideoDownloader] - Download from web if URL provided
    ↓
[WhisperX Transcription] - Converts audio to text
    ↓
[ClipsAI ClipFinder] - Detects optimal clip segments from transcription
    ↓
[MediaEditor] - Trims video at detected clip boundaries
    ↓
Generated Clips (output)
```

## Project Structure

```
ClipsAiServer/
├── app/                      # Main application package
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── clip_job.py      # ClipJob model with clip metadata
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── clip_request.py  # Request schemas
│   │   └── clip_response.py # Response schemas
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── clip_generator.py # Clip generation + transcription
│   │   ├── transcriber.py   # WhisperX transcription service
│   │   ├── downloader.py    # Video download service
│   │   └── storage.py       # File storage operations
│   └── api/                 # API routes
│       ├── __init__.py
│       └── routes.py        # Route handlers
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

1. **Clone the repository:**
   ```bash
   cd /home/lcezario/code/ClipsAiServer
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   - Copy `.env` file and adjust settings as needed:
   ```bash
   cp .env .env.local  # Optional: use local overrides
   ```

## Running the Server

### Option 1: Using the main.py script
```bash
python main.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Production with gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

The server will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /api/clips/health
```
Check if the API server is running and healthy.

### Generate Clip
```
POST /api/clips/generate
Content-Type: application/json

{
  "video_path": "/path/to/video.mp4",
  "description": "Generate clips from this video"
}
```

Response (HTTP 202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Clip generation job queued successfully. Use /status/{job_id} to check progress."
}
```

### Check Job Status
```
GET /api/clips/status/{job_id}
```

Response when processing:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "status_message": "Detectando clips...",
  "generated_clips": null,
  "error_message": null,
  "created_at": "2026-02-26T10:00:00",
  "updated_at": "2026-02-26T10:00:05",
  "completed_at": null
}
```

Response when completed:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "status_message": "Concluído: 3 clips gerados",
  "generated_clips": [
    {
      "filename": "clip_550e8400-e29b-41d4-a716-446655440000_001.mp4",
      "path": "/clips_output/550e8400-e29b-41d4-a716-446655440000/clip_550e8400-e29b-41d4-a716-446655440000_001.mp4",
      "start_time": 0.0,
      "end_time": 5.5,
      "duration": 5.5
    },
    {
      "filename": "clip_550e8400-e29b-41d4-a716-446655440000_002.mp4",
      "path": "/clips_output/550e8400-e29b-41d4-a716-446655440000/clip_550e8400-e29b-41d4-a716-446655440000_002.mp4",
      "start_time": 15.2,
      "end_time": 22.8,
      "duration": 7.6
    },
    {
      "filename": "clip_550e8400-e29b-41d4-a716-446655440000_003.mp4",
      "path": "/clips_output/550e8400-e29b-41d4-a716-446655440000/clip_550e8400-e29b-41d4-a716-446655440000_003.mp4",
      "start_time": 30.1,
      "end_time": 38.9,
      "duration": 8.8
    }
  ],
  "error_message": null,
  "created_at": "2026-02-26T10:00:00",
  "updated_at": "2026-02-26T10:02:30",
  "completed_at": "2026-02-26T10:02:30"
}
```

Response when failed:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "status_message": "Erro: File not found",
  "generated_clips": null,
  "error_message": "File not found",
  "created_at": "2026-02-26T10:00:00",
  "updated_at": "2026-02-26T10:00:05",
  "completed_at": "2026-02-26T10:00:05"
}
```

## Processing Flow

### Step 0: Download (if URL provided)
If the `video_path` is an HTTP/HTTPS URL, the server downloads it to a temporary cache.
Status: "processing" - "Baixando vídeo da web..."

### Step 1: Submit Video
Submit a video file path or URL with `POST /api/clips/generate`. The job is queued with status "pending".

### Step 2: Transcription
The system transcribes the video using WhisperX to convert audio to text.
Status: "processing" - "Transcrevendo vídeo..."

### Step 3: Clip Detection
ClipsAI analyzes the transcription to automatically detect optimal clip segments.
Status: "processing" - "Detectando clips..."

### Step 4: Video Trimming
Video is trimmed at the detected clip boundaries to generate final output files.
Status: "processing" - "Gerando N clips..."

### Step 5: Completion
All clips are saved and metadata is stored in the database.
Status: "completed" - "Concluído: N clips gerados"

## Usage Examples

### Example 1: Submit local video file
```bash
curl -X POST http://localhost:8000/api/clips/generate \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/path/to/local/video.mp4"}'
```

### Example 2: Submit video URL (auto-download)
```bash
curl -X POST http://localhost:8000/api/clips/generate \
  -H "Content-Type: application/json" \
  -d '{"video_path": "https://example.com/video.mp4"}'
```

### Example 3: Python client with local video
```python
import requests
import time

# 1. Submit video for clip generation
response = requests.post(
    "http://localhost:8000/api/clips/generate",
    json={"video_path": "/path/to/video.mp4"}
)
job_id = response.json()["job_id"]

# 2. Poll for status
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/clips/status/{job_id}"
    )
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        print(f"✓ Generated {len(status_data['generated_clips'])} clips")
```

### Example 4: Python client with URL (auto-download)
```python
import requests
import time

# 1. Submit video URL for clip generation (will auto-download)
response = requests.post(
    "http://localhost:8000/api/clips/generate",
    json={"video_path": "https://example.com/myvideos/speech.mp4"}
)
job_id = response.json()["job_id"]
print(f"Job submitted: {job_id}")

# 2. Monitor progress with status messages
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/clips/status/{job_id}"
    )
    status_data = status_response.json()
    
    status = status_data["status"]
    message = status_data.get("status_message", "")
    
    print(f"[{status}] {message}")
    
    if status == "completed":
        print(f"✓ Generated {len(status_data['generated_clips'])} clips:")
        for i, clip in enumerate(status_data['generated_clips'], 1):
            print(f"  {i}. {clip['filename']} ({clip['duration']:.2f}s)")
        break
    elif status == "failed":
        print(f"✗ Job failed: {status_data['error_message']}")
        break
    
    time.sleep(5)
```

### Video Download Features

- **Automatic format detection**: Determines file type from Content-Type header
- **Resume support**: Compatible with servers that support range requests
- **File size validation**: Prevents downloading files > 2GB (configurable)
- **Timeout protection**: 5-minute default timeout per download (configurable)
- **Automatic cleanup**: Old cached videos cleaned up after 24 hours
- **User-Agent handling**: Proper browser-like headers for compatibility

## Usage Example

```python
import requests
import time

# 1. Submit video for clip generation
response = requests.post(
    "http://localhost:8000/api/clips/generate",
    json={"video_path": "/path/to/video.mp4"}
)
job_id = response.json()["job_id"]

# 2. Poll for status
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/clips/status/{job_id}"
    )
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        print(f"✓ Generated {len(status_data['generated_clips'])} clips")
        for clip in status_data["generated_clips"]:
            print(f"  - {clip['filename']}: {clip['duration']:.2f}s")
        break
    elif status_data["status"] == "failed":
        print(f"✗ Job failed: {status_data['error_message']}")
        break
    else:
        print(f"Processing: {status_data['status_message']}")
        time.sleep(5)
```
  "created_at": "2024-02-26T10:30:00",
  "updated_at": "2024-02-26T10:35:00",
  "completed_at": "2024-02-26T10:35:00"
}
```

## Configuration

Environment variables in `.env`:

- `DATABASE_URL` - SQLAlchemy database URL (default: `sqlite:///clips.db`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `TEMP_UPLOAD_DIR` - Directory for temporary uploads (default: `./temp_uploads`)
- `CLIPS_OUTPUT_DIR` - Directory for generated clips (default: `./clips_output`)

## Database Models

### ClipJob
Tracks the status of clip generation jobs with transcription:
- `id` - Primary key
- `job_id` - Unique UUID identifier
- `status` - Job status (pending, processing, completed, failed)
- `input_file` - Path to input video
- `status_message` - Detailed progress message
- `generated_clips` - JSON array of clip metadata (filename, path, start_time, end_time, duration)
- `error_message` - Error details if job failed
- `created_at`, `updated_at`, `completed_at` - Timestamps

## Services

### ClipGenerator
Handles clip generation with WhisperX transcription:
- Transcribes video using WhisperX
- Detects clip segments using ClipsAI
- Trims video at detected boundaries
- Manages job status updates
- Error handling and logging

### TranscriberService
Manages WhisperX transcription:
- Loads and caches the Whisper model
- Handles audio/video transcription
- Supports language selection
- GPU/CPU device management

### StorageService
Manages file operations:
- Save uploaded files
- Generate output paths
- File cleanup
- File existence checks

## Development

### Running tests
```bash
pytest tests/
```

### Code formatting
```bash
black app/
isort app/
```

### Type checking
```bash
mypy app/
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue in the repository.
