# Clips AI Server

A FastAPI-based server for generating video clips using the clipsai library.

## Features

- **Asynchronous clip generation** using FastAPI background tasks
- **Database tracking** of clip generation jobs with SQLAlchemy ORM
- **File storage management** for uploads and outputs
- **Type-safe schemas** with Pydantic
- **Environment configuration** with .env file support
- **RESTful API** with comprehensive error handling

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
│   │   └── clip_job.py      # ClipJob model
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── clip_request.py  # Request schemas
│   │   └── clip_response.py # Response schemas
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── clip_generator.py # Clip generation logic
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
  "start_time": 10.5,
  "end_time": 45.2,
  "title": "Awesome Moment",
  "description": "A great clip from the video",
  "tags": ["gaming", "highlight"]
}
```

Response (HTTP 202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Clip generation job queued successfully"
}
```

### Check Job Status
```
GET /api/clips/status/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output_file": "/path/to/clip.mp4",
  "error_message": null,
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
Tracks the status of clip generation jobs:
- `id` - Primary key
- `job_id` - Unique UUID identifier
- `status` - Job status (pending, processing, completed, failed)
- `input_file` - Path to input video
- `output_file` - Path to generated clip
- `error_message` - Error details if job failed
- `created_at`, `updated_at`, `completed_at` - Timestamps

## Services

### ClipGenerator
Handles clip generation using the clipsai library:
- Manages job status updates
- Processes videos with clipsai
- Error handling and logging

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
