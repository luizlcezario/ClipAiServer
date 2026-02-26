"""
Application entry point.

This module serves as the main entry point for running the FastAPI server
with uvicorn. Run this file to start the server:

    python main.py

Or use uvicorn directly:

    uvicorn main:app --reload
"""

import uvicorn
from app.main import app


def main() -> None:
    """
    Start the FastAPI server using uvicorn.

    Configuration can be customized by modifying the uvicorn.run() parameters
    or by setting environment variables.
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
