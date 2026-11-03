import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.ml.predict import load_model, predict_lead
from src.rag.rag_assistant import ask_company_assistant


# ==========================================
# 1. CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Sales & Operations Intelligence Copilot",
    description="AI-powered Sales and Operations Backend API",
    version="1.0.0"
)


# ==========================================
# 2. REQUEST VALIDATION SCHEMAS
# ==========================================

class LeadRequest(BaseModel):

    lead_source: str
    industry: str
    company_size: str

    budget: float = Field(ge=0)
    website_visits: int = Field(ge=0)
    emails_opened: int = Field(ge=0)
    calls_made: int = Field(ge=0)
    previous_interactions: int = Field(ge=0)
    response_time_hours: float = Field(ge=0)


class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=3,
        max_length=500
    )


# ==========================================
# 3. LOAD ML MODEL
# ==========================================

ml_artifact = load_model()


# ==========================================
# 4. ROOT ENDPOINT
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Welcome to Sales & Operations Intelligence Copilot",
        "status": "Backend is running"
    }


# ==========================================
# 5. HEALTH CHECK ENDPOINT
# ==========================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "Sales & Operations Intelligence Copilot",
        "version": "1.0.0"
    }


# ==========================================
# 5b. READINESS CHECK (hosts + container probes)
# ==========================================

@app.get("/ready")
def readiness_check():

    # Model artifact
    model_ready = ml_artifact is not None

    # Vector store
    try:
        from src.rag.retriever import collection

        knowledge_chunks = collection.count()
        knowledge_ready = knowledge_chunks > 0

    except Exception as error:  # missing index or embedding model
        knowledge_chunks = 0
        knowledge_ready = False
        print(f"[ready] knowledge store unavailable: {error}")

    # Language model (optional: hosted deploys may run retrieval only)
    llm_ready = False

    try:
        from src.llm.ollama_client import MODEL_NAME, OLLAMA_HOST, _get_client

        _get_client().list()
        llm_ready = True
        llm_model = MODEL_NAME
        llm_host = OLLAMA_HOST or "http://127.0.0.1:11434"

    except Exception:
        llm_model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
        llm_host = os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"

    ready = model_ready and knowledge_ready

    return {
        "status": "ready" if ready else "degraded",
        "model": model_ready,
        "knowledge_chunks": knowledge_chunks,
        "knowledge": knowledge_ready,
        "llm": llm_ready,
        "llm_model": llm_model,
        "llm_host": llm_host
    }


# ==========================================
# 6. ML LEAD PREDICTION API
# ==========================================

@app.post("/predict")
def predict_lead_api(lead: LeadRequest):

    try:

        lead_data = lead.model_dump()

        result = predict_lead(
            lead_data=lead_data,
            artifact=ml_artifact
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Lead prediction failed: {str(error)}"
        )


# ==========================================
# 7. COMPANY KNOWLEDGE ASSISTANT API
# ==========================================

@app.post("/ask")
def ask_company_api(request: QuestionRequest):

    try:

        result = ask_company_assistant(
            request.question
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI assistant failed: {str(error)}"
        )