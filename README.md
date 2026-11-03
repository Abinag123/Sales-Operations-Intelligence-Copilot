# Sales & Operations Intelligence Copilot

An end-to-end sales intelligence system: a machine-learning lead-conversion
scorer, a hybrid retrieval-augmented knowledge assistant, a FastAPI backend, a
Streamlit command center, and a static showcase website.

> **Data note:** the 5,000-row lead dataset and the company documents are
> synthetic demonstration material. Model performance here proves the pipeline
> works; it does not establish real-world business impact.

---

## What it does

| Capability | Implementation |
| --- | --- |
| Lead conversion probability | scikit-learn logistic-regression pipeline (9 features, 0.75 cut-off) |
| Explainable scoring | standardised coefficient contributions per prediction |
| Company knowledge Q&A | hybrid semantic + BM25 retrieval, reciprocal rank fusion, Llama 3.2 via Ollama |
| Cited answers | every response returns the supporting chunks, file names and distances |
| Analytics dashboard | Streamlit command center with filters and Plotly charts |
| API | FastAPI with Pydantic validation and OpenAPI docs |
| Showcase website | static HTML/CSS/JS with exact in-browser inference |

---

## Architecture

```
dashboard (Streamlit :8501) ─┐
static website (web/)        ├─► FastAPI (:8000) ─► ML pipeline (joblib)
API clients / curl           ┘                  └─► RAG: Chroma + BM25 ─► Ollama (llama3.2:1b)
                                                    └─► data/documents/*.txt
```

Nothing is hidden: the model, the vector index and the documents are local
files. The only external process is the local Ollama runtime.

---

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# generate web data files (required for the static site)
python scripts/export_web_data.py

# local language model + knowledge index (optional, for RAG assistant)
ollama pull llama3.2:1b
python scripts/ingest_knowledge.py

# services
python scripts/run_api.py         # http://127.0.0.1:8000  (docs at /docs)
python scripts/run_dashboard.py   # http://127.0.0.1:8501

# verify
python scripts/check_stack.py
```

On macOS/Linux use `source .venv/bin/activate` and the equivalent commands.

Copy `.env.example` to `.env` to override the API host/port, the dashboard's API
origin, or the Ollama model name.

---

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Service banner |
| GET | `/health` | Liveness check used by the dashboard |
| POST | `/predict` | Score one lead and return probability + decision |
| POST | `/ask` | Answer a company question with citations |

### `POST /predict`

```json
{
  "lead_source": "Website",
  "industry": "IT",
  "company_size": "Large",
  "budget": 150000,
  "website_visits": 40,
  "emails_opened": 15,
  "calls_made": 10,
  "previous_interactions": 8,
  "response_time_hours": 1
}
```

```json
{
  "conversion_probability": 0.9658,
  "prediction": "Likely to Convert",
  "threshold": 0.75
}
```

### `POST /ask`

```json
{ "question": "Who approves discounts?" }
```

Returns a grounded answer plus `citations[]` with `filename`, `chunk_id`,
`distance` and the supporting text.

---

## Model

| Item | Value |
| --- | --- |
| Algorithm | Logistic Regression (scikit-learn `Pipeline`) |
| Preprocessing | median impute + StandardScaler; most-frequent impute + OneHotEncoder |
| Split | 64% train / 16% validation / 20% held-out test, stratified |
| Decision threshold | 0.75 (tuned on validation macro F1) |
| Hold-out accuracy | 0.746 |
| Hold-out macro F1 | 0.584 |
| Hold-out ROC-AUC | 0.659 |
| Artifact | `models/lead_conversion_pipeline.joblib` |

Reproduce training (the deployed artifact is never overwritten unless `--force`):

```powershell
python scripts/train_model.py
```

---

## Website

`web/` is a dependency-free static site with five pages:

- **Overview** — hero, live score console, KPI band, conversion analytics.
- **Analytics** — filter by industry and channel; every KPI and chart recomputes
  in the browser from the 5,000 raw rows.
- **Model Lab** — score any lead with the exported pipeline, see driver
  attribution, model card, threshold sweep and confusion matrix.
- **Knowledge** — BM25 retrieval over the real indexed chunks plus a recorded
  grounded answer with citations.
- **System** — architecture, API reference, dataset schema, quickstart,
  limitations.

Data for the site is generated from project artifacts:

```powershell
python scripts/export_web_data.py      # writes web/assets/data/*.json
python -m http.server 8080 --directory web
```

The site must be served over HTTP (browsers block `fetch` on `file://`).

### Local preview

Serve the static site locally:

```powershell
python -m http.server 8080 --directory web
# http://127.0.0.1:8080
```

The site must be served over HTTP (browsers block `fetch` on `file://`).

The `web/` folder is a self-contained static site. The Python services
(and Ollama) stay local. See [UNDO_AND_DEPLOY.md](UNDO_AND_DEPLOY.md) for how to
undo the changes made to this project.

---

## Project structure

```
src/api/main.py            FastAPI application
src/ml/predict.py          validation + inference
src/rag/                   loaders, chunking, embeddings, Chroma, BM25, fusion
src/llm/ollama_client.py   local Llama call with low-memory options
src/dashboard/app.py       Streamlit command center
scripts/                   run, ingest, train, export, verify
data/raw/                  sales_leads_raw.csv
data/documents/            company profile, services, sales policy
data/vector_db/            Chroma persistence
models/                    serialized pipeline
notebooks/ML_Pipeline.ipynb  analysis + model selection record
tests/                     unit + integration tests
web/                       static showcase website
```

---

## Tests

```powershell
python -m pytest tests -q
```

- `tests/test_prediction.py` — model scenarios, validation rules (no services needed).
- `tests/test_api_app.py` — API contract via `TestClient` (no services needed).
- `tests/test_api_integration.py` — live end-to-end checks; skipped automatically
  when the API is not running on `127.0.0.1:8000`.

---

## Limitations

- Synthetic dataset, no timestamps: drift, seasonality and leakage are unmeasured.
- ROC-AUC 0.659 is modest; ranking quality is limited.
- The 0.75 threshold favours precision over recall for converted leads.
- Segment-level fairness and calibration have not been evaluated.
- The API has no authentication, rate limiting, structured logging or monitoring.
- The assistant can still hallucinate despite grounding; review before acting.
- Discounts, quotations and customer commitments require human approval.

## License / usage

Demonstration project. Replace the synthetic data and the company documents
with verified material before any production use.
