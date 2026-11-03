# Undo, redeploy, and what changed

Everything below refers to the project folder
`C:\Users\Abin ag\Downloads\Sales-Operations-Intelligence-Copilot`.

## Live site

| Environment | URL |
| --- | --- |
| Production (published) | https://site-50a26237741b45e5b516b7088d0511af.freebuff.page |
| Preview | https://site-fac97d5bfa5c417e84db036b92ddf7f5.freebuff.page |

Only the static `web/` folder was published. The FastAPI service, the scikit-learn
artifact, ChromaDB and Ollama still run on this machine — a static host cannot start
Python or a local LLM. The Model Lab re-implements the exported pipeline in JavaScript,
so its scores match `POST /predict` exactly; the Knowledge page runs the real BM25
retrieval in the browser and shows a recorded `POST /ask` answer with citations.

## What was added

| Path | Purpose |
| --- | --- |
| `web/` | The five-page showcase site (Overview, Analytics, Model Lab, Knowledge, System) |
| `scripts/run_api.py`, `scripts/run_dashboard.py` | One-command launchers for the two services |
| `scripts/ingest_knowledge.py` | Rebuilds the Chroma index from `data/documents/` |
| `scripts/train_model.py` | Reproduces training/evaluation without overwriting the shipped artifact |
| `scripts/export_web_data.py` | Regenerates `web/assets/data/*.json` from the dataset and the model |
| `scripts/check_stack.py` | Verifies model, index, API and Ollama in one pass |
| `tests/test_prediction.py`, `tests/test_api_app.py` | Unit and API-contract tests (no services needed) |
| `undo_my_changes.py` | Restores the original project state |

## What was edited

Small, surgical fixes only — no rewrites of your own code:

- `requirements.txt` — added the packages the code actually imports (streamlit, ollama,
  chromadb, sentence-transformers, pytest, ...).
- `.env.example`, `.gitignore` — added (both were missing).
- `README.md` — written to match the code as it exists.
- `src/dashboard/app.py` — uses the shared `load_model`/`predict_lead` helpers instead of
  its own duplicate model loading, and reads the dataset with an explicit path.
- `src/llm/ollama_client.py` — model name, host and generation limits are configurable via
  environment variables (defaults unchanged: `llama3.2:1b`).
- `tests/test_api_integration.py` — skipped automatically when the API is not running.

## Undo everything (back to your original code)

A snapshot was taken **before** any edit:

```
C:\Users\Abin ag\Downloads\Sales-Operations-Intelligence-Copilot_BACKUP_20261102-230224\original\project-files.tar.gz
```

From the project root:

```powershell
python undo_my_changes.py --dry-run   # lists the added files that would be deleted
python undo_my_changes.py --yes       # restores the original files and removes the additions
```

The restore writes back all 46 original files, deletes `web/`, `scripts/`, the two new test
modules and this document, and leaves `.venv/`, `logs/` and caches alone. It was tested
against a throwaway copy of the project: the result is byte-identical to the backup.

The published website is hosted separately — restoring the repo does not take it down.
Ask for the site to be unpublished if you want it offline (that keeps the deployment and
its URL for later).

## Republishing after edits

1. `python scripts/export_web_data.py` (only if data or the model changed)
2. Ask Buffy to redeploy, or copy `web/` over the deployed asset folder and publish again
   through the Sites panel in Freebuff.

## Local preview

```powershell
python -m http.server 8080 --directory web
# http://127.0.0.1:8080
```
