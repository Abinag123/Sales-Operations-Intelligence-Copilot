
from pathlib import Path
import joblib
import pandas as pd
import math


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Model artifact
MODEL_PATH = PROJECT_ROOT / "models" / "lead_conversion_pipeline.joblib"


# Expected input features
REQUIRED_FIELDS = [
    "lead_source",
    "industry",
    "company_size",
    "budget",
    "website_visits",
    "emails_opened",
    "calls_made",
    "previous_interactions",
    "response_time_hours"
]

CATEGORICAL_FIELDS = [
    "lead_source",
    "industry",
    "company_size"
]

NUMERICAL_FIELDS = [
    "budget",
    "website_visits",
    "emails_opened",
    "calls_made",
    "previous_interactions",
    "response_time_hours"
]


def load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


def validate_lead_data(lead_data):

    if not isinstance(lead_data, dict):
        raise TypeError("Lead data must be a dictionary.")

    # Check missing fields
    missing_fields = [
        field for field in REQUIRED_FIELDS
        if field not in lead_data
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {missing_fields}"
        )

    # Check unexpected fields
    unexpected_fields = [
        field for field in lead_data
        if field not in REQUIRED_FIELDS
    ]

    if unexpected_fields:
        raise ValueError(
            f"Unexpected fields: {unexpected_fields}"
        )

    # Validate categorical fields
    for field in CATEGORICAL_FIELDS:

        value = lead_data[field]

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field} must be a non-empty string."
            )

    # Validate numerical fields
    for field in NUMERICAL_FIELDS:

        value = lead_data[field]

        if isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise TypeError(
                f"{field} must be a numeric value."
            )

        if not math.isfinite(value):
            raise ValueError(
                f"{field} must be a finite number."
            )

        if value < 0:
            raise ValueError(
                f"{field} cannot be negative."
            )

    return lead_data


def predict_lead(lead_data, artifact):

    # Validate incoming data
    validated_data = validate_lead_data(lead_data)

    pipeline = artifact["pipeline"]
    threshold = artifact["threshold"]

    lead_df = pd.DataFrame([validated_data])

    probability = float(
        pipeline.predict_proba(lead_df)[0, 1]
    )

    prediction = int(probability >= threshold)

    return {
        "conversion_probability": round(probability, 4),
        "prediction": (
            "Likely to Convert"
            if prediction == 1
            else "Unlikely to Convert"
        ),
        "threshold": threshold
    }
