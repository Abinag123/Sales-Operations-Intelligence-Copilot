"""Start the FastAPI backend.

Usage:
    python scripts/run_api.py
    python scripts/run_api.py --reload
    python scripts/run_api.py --port 8010

Environment (optional, a .env file is loaded when python-dotenv is installed):
    API_HOST  default 127.0.0.1
    API_PORT  default 8000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:  # optional convenience, already listed in requirements.txt
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:  # pragma: no cover
    pass

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the copilot API")
    parser.add_argument("--host", default=os.getenv("API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("API_PORT", "8000")))
    parser.add_argument("--reload", action="store_true", help="Reload on source changes")
    args = parser.parse_args()

    print(f"Starting Sales & Operations Intelligence API on http://{args.host}:{args.port}")
    print("Docs: /docs  ·  Health: /health")

    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
