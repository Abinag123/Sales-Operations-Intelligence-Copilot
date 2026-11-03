"""API contract tests using FastAPI's TestClient (no live server required)."""

from fastapi.testclient import TestClient

import src.api.main as api_main

client = TestClient(api_main.app)

VALID_LEAD = {
    "lead_source": "Website",
    "industry": "IT",
    "company_size": "Large",
    "budget": 150000,
    "website_visits": 40,
    "emails_opened": 15,
    "calls_made": 10,
    "previous_interactions": 8,
    "response_time_hours": 1,
}


def test_root_banner():
    response = client.get("/")
    assert response.status_code == 200
    assert "Copilot" in response.json()["message"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_returns_probability():
    response = client.post("/predict", json=VALID_LEAD)
    assert response.status_code == 200

    payload = response.json()
    assert 0.0 <= payload["conversion_probability"] <= 1.0
    assert payload["prediction"] in {"Likely to Convert", "Unlikely to Convert"}
    assert payload["threshold"] == 0.75


def test_predict_rejects_negative_values():
    invalid = {**VALID_LEAD, "budget": -10}
    response = client.post("/predict", json=invalid)
    assert response.status_code == 422


def test_predict_rejects_missing_fields():
    response = client.post("/predict", json={"lead_source": "Website"})
    assert response.status_code == 422


def test_ask_returns_answer_and_citations(monkeypatch):
    def fake_assistant(question):
        return {
            "question": question,
            "answer": "The authorized business representative approves discounts.",
            "citations": [
                {
                    "citation": "Source 1",
                    "filename": "sales_policy.txt",
                    "chunk_id": 2,
                    "distance": 0.36,
                    "supporting_text": "Any discount must be approved...",
                }
            ],
        }

    monkeypatch.setattr(api_main, "ask_company_assistant", fake_assistant)

    response = client.post("/ask", json={"question": "Who approves discounts?"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["citations"][0]["filename"] == "sales_policy.txt"
    assert payload["answer"]


def test_ask_validates_question_length():
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 422
