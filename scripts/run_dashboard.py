"""Start the Streamlit command center.

Usage:
    python scripts/run_dashboard.py
    python scripts/run_dashboard.py --port 8502

The dashboard talks to the FastAPI backend, so run scripts/run_api.py first.
Set DASHBOARD_API_URL to point the dashboard at a different API origin.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = PROJECT_ROOT / "src" / "dashboard" / "app.py"


def main() -> None:
    if not DASHBOARD.exists():
        raise SystemExit(f"Dashboard not found: {DASHBOARD}")

    port = "8501"
    args = sys.argv[1:]
    if "--port" in args:
        port = args[args.index("--port") + 1]

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DASHBOARD),
        "--server.port",
        port,
        "--server.headless",
        "true",
    ]

    print(f"Starting Streamlit dashboard on http://127.0.0.1:{port}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=False)


if __name__ == "__main__":
    main()
