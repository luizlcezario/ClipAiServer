# Clips AI Server - Setup Guide

A comprehensive FastAPI server for generating clips using the clipsai library. This guide covers installation, configuration, testing, and extending the server.

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Dependencies](#system-dependencies)
3. [Python Environment Setup](#python-environment-setup)
4. [Configuration](#configuration)
5. [Running the Server](#running-the-server)
6. [Testing the API](#testing-the-api)
7. [API Endpoints](#api-endpoints)
8. [Extending the ClipGenerator](#extending-the-clipgenerator)
9. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
10. [Project Structure](#project-structure)

---

## Quick Start

The fastest way to get up and running:

```bash
# 1. Clone or navigate to the project directory
cd /path/to/ClipsAiServer

# 2. Install system dependencies (see below for your OS)
# Ubuntu/Debian: sudo apt-get install ffmpeg libmagic1
# macOS: brew install ffmpeg libmagic
# Windows: Download from official websites

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Set up environment variables (optional)
cp .env.example .env  # If available, or create your own

# 6. Run the server
python -m uvicorn app.main:app --reload

# 7. Access the API
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# API Health: http://localhost:8000/api/clips/health
```

---

## System Dependencies

The Clips AI Server requires several system-level dependencies before you can run it.

### Ubuntu / Debian

```bash
# Update package manager
sudo apt-get update

# Install FFmpeg (for video processing)
sudo apt-get install ffmpeg

# Install libmagic (for file type detection)
sudo apt-get install libmagic1

# Verify installation
ffmpeg -version
file --version
```

### macOS

```bash
# Using Homebrew (install from https://brew.sh if needed)
brew install ffmpeg libmagic

# Verify installation
ffmpeg -version
file --version
```

### Windows

#### FFmpeg

1. Download from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Open System Environment Variables
   - Edit PATH and add the ffmpeg bin folder
   - Restart your terminal

Verify:
```powershell
ffmpeg -version
```

#### libmagic

1. Download pre-built binaries or use Windows binaries from: https://github.com/pidydx/libmagicwin64
2. Add to PATH similar to FFmpeg
3. Or install via conda:
   ```powershell
   conda install -c conda-forge libmagic
   ```

### Docker (Optional)

If you want to avoid installing system dependencies manually, use Docker:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t clips-ai-server .
docker run -p 8000:8000 clips-ai-server
```

---

## Python Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

### Using conda

```bash
# Create conda environment
conda create -n clips-ai python=3.10

# Activate environment
conda activate clips-ai

# Install dependencies
pip install -r requirements.txt

# Install system dependencies via conda (optional)
conda install -c conda-forge ffmpeg libmagic
```

### Using Poetry

If your project includes a `pyproject.toml`:

```bash
# Install Poetry (if not already installed)
pip install poetry

# Install dependencies
poetry install

# Activate environment
poetry shell

# Run server
poetry run uvicorn app.main:app --reload
```

### Python Version

This project requires **Python 3.10 or higher**.

Check your Python version:
```bash
python --version
# or
python3 --version
```

If you need to install a specific Python version, use:
- **pyenv** (Linux/macOS): `pyenv install 3.10.13 && pyenv local 3.10.13`
- **conda**: `conda install python=3.10`
- **Official installers**: https://www.python.org/downloads/

---

## Configuration

### Environment Variables

The server reads configuration from environment variables. Create a `.env` file in the project root:

```env
# Database configuration
DATABASE_URL=sqlite:///clips.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/clips_ai

# Logging
LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# File paths
TEMP_UPLOAD_DIR=./temp_uploads
CLIPS_OUTPUT_DIR=./clips_output

# HuggingFace token (for clipsai features - optional)
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx

# API configuration
API_TITLE=Clips AI Server
API_VERSION=1.0.0
API_DESCRIPTION=FastAPI server for generating clips using clipsai library
```

### Default Configuration

If no `.env` file is provided, the server uses these defaults:

```python
database_url: str = "sqlite:///clips.db"
log_level: str = "INFO"
temp_upload_dir: str = "./temp_uploads"
clips_output_dir: str = "./clips_output"
api_title: str = "Clips AI Server"
api_version: str = "1.0.0"
api_description: str = "FastAPI server for generating clips using clipsai library"
```

### HuggingFace Token Setup (Optional)

If using advanced clipsai features that require HuggingFace models:

1. Create a HuggingFace account at https://huggingface.co
2. Generate an access token:
   - Go to Settings → Access Tokens
   - Click "New token"
   - Select "read" permissions
   - Copy the token
3. Add to `.env`:
   ```env
   HUGGINGFACE_TOKEN=hf_your_token_here
   ```
4. The server will automatically use this token when initializing clipsai

---

## Running the Server

### Development Mode (with auto-reload)

```bash
python -m uvicorn app.main:app --reload
```

The server will:
- Start on `http://localhost:8000`
- Automatically reload when code changes
- Show detailed logs
- Enable Swagger UI documentation at `/docs`

### Production Mode

```bash
# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### With Environment Variables

```bash
# Linux/macOS
export DATABASE_URL=postgresql://user:pass@localhost:5432/clips
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload

# Windows
set DATABASE_URL=postgresql://user:pass@localhost:5432/clips
set LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

### With Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  clips-ai-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/clips
      LOG_LEVEL: INFO
    depends_on:
      - db
    volumes:
      - ./temp_uploads:/app/temp_uploads
      - ./clips_output:/app/clips_output

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: clips
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up
```

---

## Testing the API

### 1. Health Check

Test that the server is running:

```bash
# Using curl
curl -X GET http://localhost:8000/api/clips/health

# Expected response:
# {"status":"healthy","message":"Clips AI Server is running"}
```

### 2. Submit a Clip Generation Request

```bash
curl -X POST http://localhost:8000/api/clips/generate \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/path/to/video.mp4",
    "start_time": 10.5,
    "end_time": 45.2,
    "title": "My Awesome Clip",
    "tags": ["highlight", "gaming"]
  }'

# Expected response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "pending",
#   "message": "Clip generation job queued successfully"
# }
```

### 3. Check Job Status

```bash
curl -X GET http://localhost:8000/api/clips/status/550e8400-e29b-41d4-a716-446655440000

# Response will show current status: pending, processing, completed, or failed
```

### 4. Using the Interactive API Documentation

Visit `http://localhost:8000/docs` in your browser for Swagger UI where you can:
- View all available endpoints
- See request/response schemas
- Test endpoints directly from the browser

### 5. Using Python Client

See `examples.py` for complete Python client examples:

```python
from examples import ClipsAIClient

client = ClipsAIClient("http://localhost:8000")

# Health check
health = client.health_check()

# Submit clip
job = client.generate_clip(
    video_path="/path/to/video.mp4",
    title="My Clip"
)

# Wait for completion
result = client.wait_for_completion(job["job_id"])
```

### 6. Automated Testing

Create a test file `test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/clips/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_generate_clip(client):
    response = client.post(
        "/api/clips/generate",
        json={"video_path": "/test/video.mp4"}
    )
    assert response.status_code == 202
    assert "job_id" in response.json()
```

Run tests:
```bash
pip install pytest pytest-asyncio
pytest test_api.py -v
```

---

## API Endpoints

### Health Check
- **Endpoint**: `GET /api/clips/health`
- **Description**: Check if the API server is running
- **Response**: `{"status": "healthy", "message": "Clips AI Server is running"}`

### Generate Clip
- **Endpoint**: `POST /api/clips/generate`
- **Status Code**: `202 Accepted` (job is queued)
- **Request Body**:
  ```json
  {
    "video_path": "/path/to/video.mp4",
    "start_time": 10.5,
    "end_time": 45.2,
    "title": "Clip Title",
    "description": "Clip description",
    "tags": ["tag1", "tag2"]
  }
  ```
- **Response**:
  ```json
  {
    "job_id": "uuid-string",
    "status": "pending",
    "message": "Clip generation job queued successfully"
  }
  ```

### Get Job Status
- **Endpoint**: `GET /api/clips/status/{job_id}`
- **Status Code**: `200 OK`
- **Response**:
  ```json
  {
    "job_id": "uuid-string",
    "status": "pending|processing|completed|failed",
    "output_file": "/path/to/output.mp4",
    "error_message": "Error details if failed",
    "created_at": "2026-02-26T10:30:45",
    "updated_at": "2026-02-26T10:30:45",
    "completed_at": "2026-02-26T10:30:52"
  }
  ```

---

## Extending the ClipGenerator

### Understanding the Current Implementation

The `ClipGenerator` class in `app/services/clip_generator.py` is where the actual clip generation logic lives. Currently it's a template ready for integration.

### Basic Structure

```python
# app/services/clip_generator.py
from sqlalchemy.orm import Session
from app.models.clip_job import ClipJob, JobStatus
from app.schemas.clip_request import ClipGenerationRequest

class ClipGenerator:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_clip(self, job_id: str, request: ClipGenerationRequest):
        # Update job status to processing
        # Perform clip generation
        # Update job with output file path or error
        pass
```

### Integration with ClipsAI Library

To use the actual `clipsai` library for clip generation:

```python
from clipsai import ClipsAI
import os

class ClipGenerator:
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize ClipsAI with HuggingFace token if available
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.clips_ai = ClipsAI(hf_token=hf_token)
    
    def generate_clip(self, job_id: str, request: ClipGenerationRequest):
        job = self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
        
        try:
            # Update status
            job.status = JobStatus.PROCESSING
            self.db.commit()
            
            # Generate clip using clipsai
            output_path = self.clips_ai.generate(
                video=request.video_path,
                start_time=request.start_time,
                end_time=request.end_time,
                title=request.title,
            )
            
            # Update job with success
            job.status = JobStatus.COMPLETED
            job.output_file = output_path
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        
        finally:
            self.db.commit()
```

### Custom Integration Example

```python
from pathlib import Path
import subprocess
from datetime import datetime

class CustomClipGenerator:
    """Example custom implementation using FFmpeg."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_clip(self, job_id: str, request: ClipGenerationRequest):
        job = self.db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
        
        try:
            job.status = JobStatus.PROCESSING
            self.db.commit()
            
            # Custom implementation: use FFmpeg directly
            output_path = self._generate_with_ffmpeg(
                request.video_path,
                request.start_time,
                request.end_time,
                job_id,
            )
            
            job.status = JobStatus.COMPLETED
            job.output_file = output_path
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        finally:
            self.db.commit()
    
    def _generate_with_ffmpeg(
        self,
        input_file: str,
        start_time: float,
        end_time: float,
        job_id: str,
    ) -> str:
        """Generate clip using FFmpeg."""
        output_dir = Path("./clips_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{job_id}.mp4"
        
        duration = (end_time or 0) - (start_time or 0)
        
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-ss", str(start_time or 0),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output_path),
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)
```

### Adding New Features

Example: Add watermark support:

```python
def generate_clip(self, job_id: str, request: ClipGenerationRequest):
    # ... existing code ...
    
    # Add new field to request
    if hasattr(request, 'watermark_path') and request.watermark_path:
        output_path = self._apply_watermark(output_path, request.watermark_path)

def _apply_watermark(self, video_path: str, watermark_path: str) -> str:
    """Apply watermark to generated clip."""
    output_with_wm = video_path.replace(".mp4", "_watermarked.mp4")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", watermark_path,
        "-filter_complex", "[1]scale=iw*0.2:-1[wm];[0][wm]overlay=main_w-overlay_w-10:10",
        str(output_with_wm),
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_with_wm
```

### Testing Your Custom Implementation

```python
# Create a test file to verify your implementation
import pytest
from app.services.clip_generator import ClipGenerator
from app.models.clip_job import ClipJob, JobStatus
from sqlalchemy.orm import Session

def test_clip_generation(db: Session):
    generator = ClipGenerator(db)
    job_id = "test-job-123"
    
    # Create a test job
    job = ClipJob(job_id=job_id, status=JobStatus.PENDING, input_file="/test/video.mp4")
    db.add(job)
    db.commit()
    
    # Generate clip
    from app.schemas.clip_request import ClipGenerationRequest
    request = ClipGenerationRequest(video_path="/test/video.mp4", title="Test")
    
    generator.generate_clip(job_id, request)
    
    # Verify results
    updated_job = db.query(ClipJob).filter(ClipJob.job_id == job_id).first()
    assert updated_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
```

---

## Common Issues and Troubleshooting

### Issue 1: "ffmpeg: command not found"

**Solution**: Install FFmpeg

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows - Download from https://ffmpeg.org/download.html and add to PATH
```

Verify:
```bash
ffmpeg -version
```

### Issue 2: "libmagic not found" or "magic import error"

**Solution**: Install libmagic

```bash
# Ubuntu/Debian
sudo apt-get install libmagic1

# macOS
brew install libmagic

# Windows via conda
conda install -c conda-forge libmagic
```

### Issue 3: "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Install dependencies

```bash
pip install -r requirements.txt

# Or install FastAPI directly
pip install fastapi uvicorn
```

### Issue 4: "Database connection failed"

**Symptoms**: `sqlalchemy.exc.OperationalError`

**Solution**: 

```bash
# Check if SQLite database can be created
# Default location: ./clips.db
# Ensure directory is writable
ls -la clips.db

# For PostgreSQL, verify connection string
# DATABASE_URL=postgresql://user:password@host:port/dbname
```

### Issue 5: Port 8000 already in use

**Solution**: Use a different port

```bash
# Use port 8001 instead
python -m uvicorn app.main:app --port 8001

# Or kill the process using port 8000
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 6: "File not found" when generating clips

**Symptoms**: Job fails with file-related errors

**Solution**:

```bash
# Ensure input video files exist and paths are correct
ls -la /path/to/video.mp4

# Use absolute paths, not relative paths
# ❌ Wrong: "video.mp4"
# ✓ Correct: "/home/user/videos/video.mp4"

# Check permissions
chmod 644 /path/to/video.mp4
```

### Issue 7: Job stuck in "processing" status

**Symptoms**: Job never completes

**Solution**:

```bash
# Check server logs for errors
# Look for exceptions in ClipGenerator.generate_clip()

# Check if temporary files are taking up disk space
du -sh ./temp_uploads/

# Clear old temporary files
rm -rf ./temp_uploads/*

# Restart the server
```

### Issue 8: Output directory permission denied

**Symptoms**: `PermissionError` when writing output files

**Solution**:

```bash
# Ensure clips_output directory is writable
mkdir -p ./clips_output
chmod 755 ./clips_output
chmod 755 ./temp_uploads

# Or run with appropriate user permissions
sudo chown -R $USER:$USER ./clips_output
```

### Issue 9: Out of disk space during clip generation

**Symptoms**: Job fails with "No space left on device"

**Solution**:

```bash
# Check disk usage
df -h

# Clean up temporary files
rm -rf ./temp_uploads/*
rm -rf ./clips_output/*

# Or increase disk space / move directories to larger partition
```

### Issue 10: Server crashes on startup

**Symptoms**: Server exits immediately with no output

**Solution**:

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload

# Check for initialization errors in database
python -c "from app.database import init_db; init_db()"

# Verify Python version
python --version  # Should be 3.10+

# Check for missing dependencies
pip install -r requirements.txt
```

---

## Project Structure

```
ClipsAiServer/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview
├── SETUP_GUIDE.md                   # This file
├── examples.py                      # API usage examples
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration settings
│   ├── database.py                  # Database setup and session
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # API endpoint handlers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── clip_job.py              # SQLAlchemy models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── clip_request.py          # Request validation schemas
│   │   └── clip_response.py         # Response schemas
│   │
│   └── services/
│       ├── __init__.py
│       ├── clip_generator.py        # Clip generation logic
│       └── storage.py               # File storage utilities
│
├── clips_output/                    # Generated clips directory
└── temp_uploads/                    # Temporary upload directory
```

### Key Files

- **app/main.py**: FastAPI application factory and middleware setup
- **app/config.py**: Environment variable configuration
- **app/api/routes.py**: API endpoints (generate, status, health)
- **app/services/clip_generator.py**: Core logic for clip generation (extend this)
- **app/models/clip_job.py**: Database model for tracking jobs
- **app/database.py**: Database initialization and session management

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **ClipsAI Documentation**: https://github.com/deshraj/clipsai (if available)
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
- **Uvicorn Documentation**: https://www.uvicorn.org/

---

## Support and Troubleshooting

For additional help:

1. Check the `examples.py` file for usage patterns
2. Review API documentation at `http://localhost:8000/docs`
3. Check server logs for detailed error messages
4. Verify all system dependencies are installed
5. Ensure video file paths are absolute and accessible
6. Check disk space and file permissions

Good luck! 🚀
