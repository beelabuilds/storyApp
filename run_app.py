"""StoryApp - Unified Application Launcher.

Starts the FastAPI server on port 8000 with reload=False.
FastAPI's lifespan context manager automatically owns and manages the lifecycle of:
  1. The SQLite database (storyapp.db)
  2. The dedicated local Qwen worker process and multiprocessing IPC queues
  3. The bundled web UI and API endpoints
"""

import os
import sys
from pathlib import Path
import uvicorn

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure the project root directory is in sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    print("=" * 65)
    print("               STORYAPP -- UNIFIED DEMO LAUNCHER")
    print("=" * 65)
    print("  * Web Demo URL    : http://localhost:8000")
    print("  * API Docs        : http://localhost:8000/docs")
    print("  * SQLite Database : backend/storyapp.db")
    print("  * AI Engine       : Local Qwen Worker Process (multiprocessing IPC)")
    print("  * Reload Mode     : Disabled (reload=False)")
    print("=" * 65)
    print("Starting server... Press Ctrl+C to shut down cleanly.\n")

    # Run Uvicorn directly; lifespan handles the Qwen worker and SQLite initialization
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
