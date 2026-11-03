# Sales & Operations Intelligence Copilot — API image
#
# Builds an image that can score leads and answer company-knowledge questions
# from the artefacts committed in this repository (model, Chroma index,
# documents). The language model is optional: point OLLAMA_HOST at a reachable
# Ollama runtime and /ask returns a generated answer, otherwise it returns the
# retrieved passages with a clear note.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    API_HOST=0.0.0.0 \
    HF_HOME=/app/.cache/huggingface

# libgomp1 is needed by scikit-learn / torch wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only torch keeps the image roughly 2 GB smaller than the CUDA wheels
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch

COPY requirements-api.txt ./
RUN pip install -r requirements-api.txt

# Bake the sentence-transformers model into the image so the first request does
# not pay an ~90 MB download (and works on hosts without outbound HF access).
RUN python -c "from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Application code and artefacts
COPY src ./src
COPY scripts ./scripts
COPY models ./models
COPY data/documents ./data/documents
COPY data/raw ./data/raw
COPY data/vector_db ./data/vector_db

# Run as an unprivileged user
RUN useradd --create-home --uid 10001 app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

CMD ["sh", "-c", "python scripts/run_api.py --host 0.0.0.0 --port ${PORT:-8000}"]
