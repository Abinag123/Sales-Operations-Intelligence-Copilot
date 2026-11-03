"""Offline tests for the ML inference layer (no services required)."""

import pytest

from src.ml.predict import load_model, predict_lead, validate_lead_data


@pytest.fixture(scope="module")
def artifact():
    return load_model()


def test_high_engagement_scenario(artifact):
    result = predict_lead(
        {
            "lead_source": "Website",
            "industry": "IT",
            "company_size": "Large",
            "budget": 150000,
            "website_visits": 40,
            "emails_opened": 15,
            "calls_made": 10,
            "previous_interactions": 8,
            "response_time_hours": 1,
        },
        artifact,
    )

    assert result["conversion_probability"] == pytest.approx(0.9658, abs=1e-3)
    assert result["prediction"] == "Likely to Convert"
    assert result["threshold"] == artifact["threshold"]


def test_low_engagement_scenario(artifact):
    result = predict_lead(
        {
            "lead_source": "Social Media",
            "industry": "Retail",
            "company_size": "Small",
            "budget": 5000,
            "website_visits": 1,
            "emails_opened": 0,
            "calls_made": 0,
            "previous_interactions": 0,
            "response_time_hours": 48,
        },
        artifact,
    )

    assert result["conversion_probability"] == pytest.approx(0.3398, abs=1e-3)
    assert result["prediction"] == "Unlikely to Convert"


def test_unseen_category_scenario(artifact):
    result = predict_lead(
        {
            "lead_source": "Referral",
            "industry": "Healthcare",
            "company_size": "Medium",
            "budget": 30000,
            "website_visits": 8,
            "emails_opened": 3,
            "calls_made": 2,
            "previous_interactions": 1,
            "response_time_hours": 6,
        },
        artifact,
    )

    assert result["conversion_probability"] == pytest.approx(0.6608, abs=1e-3)


def test_missing_field_rejected():
    with pytest.raises(ValueError, match="Missing required fields"):
        validate_lead_data({"lead_source": "Website"})


def test_unexpected_field_rejected():
    with pytest.raises(ValueError, match="Unexpected fields"):
        validate_lead_data(
            {
                "lead_source": "Website",
                "industry": "IT",
                "company_size": "Large",
                "budget": 1000,
                "website_visits": 1,
                "emails_opened": 1,
                "calls_made": 1,
                "previous_interactions": 1,
                "response_time_hours": 1,
                "lead_id": 42,
            }
        )


def test_negative_budget_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_lead_data(
            {
                "lead_source": "Website",
                "industry": "IT",
                "company_size": "Large",
                "budget": -1,
                "website_visits": 1,
                "emails_opened": 1,
                "calls_made": 1,
                "previous_interactions": 1,
                "response_time_hours": 1,
            }
        )
