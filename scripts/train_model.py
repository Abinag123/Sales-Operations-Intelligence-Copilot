"""Reproduce the lead-conversion model.

Mirrors the notebook pipeline: 64% train / 16% validation / 20% reserved test,
median imputation + standardization for numeric features, most-frequent
imputation + one-hot encoding for categorical features, and a logistic
regression classifier.

The decision threshold is tuned on the validation split for macro F1.

Usage:
    python scripts/train_model.py                     # writes a .retrained artifact
    python scripts/train_model.py --force             # overwrite the deployed artifact
    python scripts/train_model.py --output /tmp/m.joblib
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "sales_leads_raw.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "lead_conversion_pipeline.joblib"

FEATURES = [
    "lead_source",
    "industry",
    "company_size",
    "budget",
    "website_visits",
    "emails_opened",
    "calls_made",
    "previous_interactions",
    "response_time_hours",
]
CATEGORICAL = ["lead_source", "industry", "company_size"]
NUMERICAL = [column for column in FEATURES if column not in CATEGORICAL]


def build_pipeline() -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return Pipeline(
        steps=[
            (
                "preprocessor",
                ColumnTransformer(
                    transformers=[
                        ("num", numeric, NUMERICAL),
                        ("cat", categorical, CATEGORICAL),
                    ]
                ),
            ),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the lead conversion model")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.data.exists():
        raise SystemExit(f"Dataset not found: {args.data}")

    frame = pd.read_csv(args.data)
    frame = frame[frame["converted"].isin([0, 1])].reset_index(drop=True)

    X = frame[FEATURES]
    y = frame["converted"]

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
    )

    print(f"Rows: {len(frame)}  train: {len(X_train)}  val: {len(X_val)}  test: {len(X_test)}")

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    validation_probabilities = pipeline.predict_proba(X_val)[:, 1]

    best_threshold, best_f1 = 0.5, -1.0
    for step in range(30, 91):
        threshold = step / 100
        predictions = (validation_probabilities >= threshold).astype(int)
        score = f1_score(y_val, predictions, average="macro")
        if score > best_f1:
            best_threshold, best_f1 = threshold, score

    test_probabilities = pipeline.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= best_threshold).astype(int)

    print(f"Selected threshold: {best_threshold:.2f} (validation macro F1 {best_f1:.4f})")
    print(f"Test accuracy: {accuracy_score(y_test, test_predictions):.4f}")
    print(f"Test macro F1: {f1_score(y_test, test_predictions, average='macro'):.4f}")
    print(f"Test ROC-AUC:  {roc_auc_score(y_test, test_probabilities):.4f}")

    artifact = {
        "pipeline": pipeline,
        "threshold": round(float(best_threshold), 2),
        "model_name": "Logistic Regression",
        "feature_columns": FEATURES,
        "target_column": "converted",
        "model_version": "1.0.0",
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "training_dataset": args.data.name,
        "validation_macro_f1": round(float(best_f1), 2),
    }

    output = args.output or MODEL_PATH
    if output == MODEL_PATH and MODEL_PATH.exists() and not args.force:
        output = MODEL_PATH.with_name("lead_conversion_pipeline.retrained.joblib")
        print(
            "Existing deployed artifact left untouched. "
            "Writing a comparison artifact instead (use --force to overwrite)."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output)
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
