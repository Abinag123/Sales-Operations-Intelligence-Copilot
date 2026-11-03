"""Check that the copilot stack and its artifacts are ready.

Usage:
    python scripts/check_stack.py

Reports imports, dataset, model, vector store, API and Ollama status. Exits
non-zero when a required local artifact is missing.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "lead_conversion_pipeline.joblib"
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "sales_leads_raw.csv"
CHROMA_DIR = PROJECT_ROOT / "data" / "vector_db"

REQUIRED_PACKAGES = [
    "pandas",
    "sklearn",
    "joblib",
    "fastapi",
    "uvicorn",
    "streamlit",
    "plotly",
    "chromadb",
    "sentence_transformers",
    "rank_bm25",
    "ollama",
    "requests",
]

failures = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def main() -> None:
    print(f"Python {sys.version.split()[0]} · project {PROJECT_ROOT}\n")

    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except Exception:
            missing.append(package)
    check("Python dependencies", not missing, f"missing: {', '.join(missing)}" if missing else "all importable")

    check("Lead dataset", DATA_PATH.exists(), str(DATA_PATH.relative_to(PROJECT_ROOT)) if DATA_PATH.exists() else "not found")

    if MODEL_PATH.exists():
        try:
            import joblib

            artifact = joblib.load(MODEL_PATH)
            check(
                "Model artifact",
                "pipeline" in artifact,
                f"threshold={artifact.get('threshold')} version={artifact.get('model_version')}",
            )
        except Exception as error:
            check("Model artifact", False, str(error))
    else:
        check("Model artifact", False, "models/lead_conversion_pipeline.joblib not found")

    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name="company_knowledge")
        count = collection.count()
        check("Vector store", count > 0, f"{count} chunks in company_knowledge")
    except Exception as error:
        check("Vector store", False, str(error))

    try:
        import requests

        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        check("FastAPI service", response.status_code == 200, response.text.strip()[:80])
    except Exception:
        check("FastAPI service", False, "not running (start scripts/run_api.py)")

    try:
        import requests

        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        models = [item["name"] for item in response.json().get("models", [])]
        check("Ollama runtime", True, ", ".join(models[:3]) or "no models pulled")
    except Exception:
        check("Ollama runtime", False, "not reachable on 127.0.0.1:11434")

    print()
    if failures:
        print(f"{len(failures)} check(s) need attention: {', '.join(failures)}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
