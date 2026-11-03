import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


def api_is_running():
    try:
        return requests.get(f"{BASE_URL}/health", timeout=1).status_code == 200
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not api_is_running(),
    reason="Live API not running on 127.0.0.1:8000 (start scripts/run_api.py)",
)


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("Health API: PASS")


def test_ml_prediction():
    lead = {
        "lead_source": "Website",
        "industry": "IT",
        "company_size": "Medium",
        "budget": 50000,
        "website_visits": 12,
        "emails_opened": 5,
        "calls_made": 3,
        "previous_interactions": 2,
        "response_time_hours": 4
    }

    response = requests.post(f"{BASE_URL}/predict", json=lead)
    assert response.status_code == 200

    result = response.json()
    assert "conversion_probability" in result
    assert "prediction" in result
    assert "threshold" in result

    print("ML Prediction API: PASS")
    print(result)


def test_rag_assistant():
    question = {"question": "Who approves discounts?"}

    response = requests.post(f"{BASE_URL}/ask", json=question)
    assert response.status_code == 200

    result = response.json()
    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) > 0

    print("RAG Assistant API: PASS")
    print("Answer:", result["answer"])
    print("Citations:", len(result["citations"]))


if __name__ == "__main__":
    test_health()
    test_ml_prediction()
    test_rag_assistant()

    print("\nAll integration tests passed!")