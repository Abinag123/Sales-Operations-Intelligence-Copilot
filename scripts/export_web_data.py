"""Export the real project artifacts into JSON consumed by the static website.

Everything on the deployed site is generated from the artifacts in this
repository: the lead dataset, the serialized scikit-learn pipeline and the
Chroma knowledge base. No numbers are hardcoded in the front-end.

Usage:
    python scripts/export_web_data.py
    python scripts/export_web_data.py --out web/assets/data
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "sales_leads_raw.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "lead_conversion_pipeline.joblib"
DOCS_DIR = PROJECT_ROOT / "data" / "documents"
CHROMA_DIR = PROJECT_ROOT / "data" / "vector_db"
COMPARISON_PATH = PROJECT_ROOT / "docs" / "day2_model_comparison.csv"
INFERENCE_PATH = PROJECT_ROOT / "docs" / "inference_test_results.csv"

CATEGORICAL = ["lead_source", "industry", "company_size"]
NUMERICAL = [
    "budget",
    "website_visits",
    "emails_opened",
    "calls_made",
    "previous_interactions",
    "response_time_hours",
]
RAW_COLUMNS = CATEGORICAL + NUMERICAL + ["converted"]


def round_list(values, digits=4):
    return [round(float(value), digits) for value in values]


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def conversion_table(df: pd.DataFrame, column: str) -> list[dict]:
    grouped = df.groupby(column)["converted"].agg(["count", "sum", "mean"])
    grouped = grouped.sort_values("mean", ascending=False)
    return [
        {
            "name": str(name),
            "leads": int(row["count"]),
            "converted": int(row["sum"]),
            "rate": round(float(row["mean"]) * 100, 2),
        }
        for name, row in grouped.iterrows()
    ]


def response_buckets(df: pd.DataFrame) -> list[dict]:
    bins = [-0.01, 6, 12, 24, 36, 48, 60, 72.01]
    labels = ["0-6h", "6-12h", "12-24h", "24-36h", "36-48h", "48-60h", "60-72h"]
    bucket = pd.cut(df["response_time_hours"], bins=bins, labels=labels)
    out = []
    for label in labels:
        subset = df[bucket == label]
        if subset.empty:
            continue
        out.append(
            {
                "label": label,
                "leads": int(len(subset)),
                "rate": round(float(subset["converted"].mean()) * 100, 2),
            }
        )
    return out


def engagement_buckets(df: pd.DataFrame) -> list[dict]:
    engagement = (
        df["website_visits"]
        + df["emails_opened"]
        + df["calls_made"]
        + df["previous_interactions"]
    )
    bins = [-1, 20, 35, 50, 65, 80, 200]
    labels = ["0-20", "21-35", "36-50", "51-65", "66-80", "80+"]
    bucket = pd.cut(engagement, bins=bins, labels=labels)
    out = []
    for label in labels:
        subset = df[bucket == label]
        if subset.empty:
            continue
        out.append(
            {
                "label": label,
                "leads": int(len(subset)),
                "rate": round(float(subset["converted"].mean()) * 100, 2),
            }
        )
    return out


def budget_quartiles(df: pd.DataFrame) -> list[dict]:
    labels = ["Q1 lowest", "Q2", "Q3", "Q4 highest"]
    bucket = pd.qcut(df["budget"], 4, labels=labels)
    out = []
    for label in labels:
        subset = df[bucket == label]
        out.append(
            {
                "label": label,
                "leads": int(len(subset)),
                "rate": round(float(subset["converted"].mean()) * 100, 2),
                "avgBudget": round(float(subset["budget"].mean()), 0),
            }
        )
    return out


def build_analytics(df: pd.DataFrame, artifact: dict, raw: dict, knowledge: dict) -> dict:
    pipeline = artifact["pipeline"]
    threshold = float(artifact["threshold"])

    X = df.drop(columns=["lead_id", "converted"])
    y = df["converted"]
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()

    threshold_sweep = []
    for cut in [0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85]:
        cut_predictions = (probabilities >= cut).astype(int)
        threshold_sweep.append(
            {
                "threshold": cut,
                "accuracy": round(float(accuracy_score(y_test, cut_predictions)), 4),
                "macroF1": round(
                    float(f1_score(y_test, cut_predictions, average="macro")), 4
                ),
                "predictedConversions": int(cut_predictions.sum()),
            }
        )

    correlation = (
        df[NUMERICAL + ["converted"]]
        .corr(numeric_only=True)["converted"]
        .drop("converted")
        .sort_values(ascending=False)
    )

    rng = df.sample(n=320, random_state=7)

    model_comparison = []
    if COMPARISON_PATH.exists():
        comparison_df = pd.read_csv(COMPARISON_PATH)
        for _, row in comparison_df.iterrows():
            model_comparison.append(
                {
                    "model": str(row["Model"]),
                    "threshold": round(float(row["Best_Threshold"]), 2),
                    "accuracy": round(float(row["Accuracy"]), 4),
                    "macroF1": round(float(row["Macro_F1"]), 4),
                    "rocAuc": round(float(row["ROC_AUC"]), 4),
                    "notConvertedRecall": round(float(row["Not_Converted_Recall"]), 4),
                    "convertedRecall": round(float(row["Converted_Recall"]), 4),
                }
            )

    scenarios = []
    if INFERENCE_PATH.exists():
        inference_df = pd.read_csv(INFERENCE_PATH)
        for _, row in inference_df.iterrows():
            scenarios.append(
                {
                    "leadId": str(row["lead_id"]),
                    "leadSource": str(row["lead_source"]),
                    "industry": str(row["industry"]),
                    "companySize": str(row["company_size"]),
                    "budget": float(row["budget"]),
                    "websiteVisits": int(row["website_visits"]),
                    "emailsOpened": int(row["emails_opened"]),
                    "callsMade": int(row["calls_made"]),
                    "previousInteractions": int(row["previous_interactions"]),
                    "responseTimeHours": float(row["response_time_hours"]),
                    "probability": round(float(row["conversion_probability"]), 4),
                    "prediction": str(row["prediction"]),
                    "threshold": float(row["threshold"]),
                }
            )

    total_leads = int(len(df))
    converted = int(df["converted"].sum())

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": {
            "file": "data/raw/sales_leads_raw.csv",
            "rows": total_leads,
            "columns": len(df.columns),
            "features": 9,
            "missingValues": int(df.isna().sum().sum()),
            "duplicateRows": int(df.duplicated().sum()),
            "targetPositiveRate": round(float(df["converted"].mean()) * 100, 2),
        },
        "kpis": {
            "totalLeads": total_leads,
            "convertedLeads": converted,
            "notConvertedLeads": total_leads - converted,
            "conversionRate": round(converted / total_leads * 100, 2),
            "averageBudget": round(float(df["budget"].mean()), 0),
            "medianBudget": round(float(df["budget"].median()), 0),
            "averageResponseHours": round(float(df["response_time_hours"].mean()), 2),
            "averageWebsiteVisits": round(float(df["website_visits"].mean()), 2),
            "knowledgeDocuments": len(knowledge["documents"]),
            "knowledgeChunks": len(knowledge["chunks"]),
        },
        "bySource": conversion_table(df, "lead_source"),
        "byIndustry": conversion_table(df, "industry"),
        "byCompanySize": conversion_table(df, "company_size"),
        "responseBuckets": response_buckets(df),
        "engagementBuckets": engagement_buckets(df),
        "budgetQuartiles": budget_quartiles(df),
        "correlation": [
            {"feature": feature, "value": round(float(value), 4)}
            for feature, value in correlation.items()
        ],
        "scatter": [
            {
                "visits": int(row["website_visits"]),
                "budget": round(float(row["budget"]), 0),
                "converted": int(row["converted"]),
                "calls": int(row["calls_made"]),
            }
            for _, row in rng.iterrows()
        ],
        "holdout": {
            "rows": int(len(y_test)),
            "threshold": threshold,
            "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "macroF1": round(
                float(f1_score(y_test, predictions, average="macro")), 4
            ),
            "rocAuc": round(float(roc_auc_score(y_test, probabilities)), 4),
            "precision": round(
                float(precision_score(y_test, predictions, zero_division=0)), 4
            ),
            "recall": round(
                float(recall_score(y_test, predictions, zero_division=0)), 4
            ),
            "confusion": {
                "trueNegative": int(tn),
                "falsePositive": int(fp),
                "falseNegative": int(fn),
                "truePositive": int(tp),
            },
            "note": (
                "Reproduced on the reserved 20% hold-out split "
                "(train_test_split, random_state=42, stratified) using the "
                "serialized pipeline at its 0.75 decision threshold."
            ),
        },
        "thresholdSweep": threshold_sweep,
        "modelComparison": model_comparison,
        "scenarios": scenarios,
        "raw": raw,
    }


# ---------------------------------------------------------------------------
# Model export (browser-exact inference)
# ---------------------------------------------------------------------------

def build_model(artifact: dict) -> dict:
    pipeline = artifact["pipeline"]
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    numeric_block = preprocessor.named_transformers_["num"]
    categorical_block = preprocessor.named_transformers_["cat"]

    medians = numeric_block.named_steps["imputer"].statistics_
    means = numeric_block.named_steps["scaler"].mean_
    scales = numeric_block.named_steps["scaler"].scale_
    categories = categorical_block.named_steps["encoder"].categories_

    coefficients = classifier.coef_[0].tolist()
    names = list(preprocessor.get_feature_names_out())

    numeric_features = []
    cursor = 0
    for index, feature in enumerate(NUMERICAL):
        numeric_features.append(
            {
                "name": feature,
                "median": round(float(medians[index]), 6),
                "mean": round(float(means[index]), 6),
                "scale": round(float(scales[index]), 6),
                "coef": round(float(coefficients[cursor]), 6),
            }
        )
        cursor += 1

    categorical_features = []
    for column_index, feature in enumerate(CATEGORICAL):
        options = []
        for value in categories[column_index]:
            options.append(
                {
                    "value": str(value),
                    "coef": round(float(coefficients[cursor]), 6),
                }
            )
            cursor += 1
        categorical_features.append(
            {"name": feature, "options": options}
        )

    return {
        "modelName": artifact.get("model_name", "Logistic Regression"),
        "modelVersion": artifact.get("model_version", "1.0.0"),
        "savedAt": artifact.get("saved_at"),
        "trainingDataset": artifact.get("training_dataset"),
        "threshold": float(artifact["threshold"]),
        "intercept": round(float(classifier.intercept_[0]), 6),
        "numeric": numeric_features,
        "categorical": categorical_features,
        "featureNames": [str(name) for name in names],
        "validationMacroF1": artifact.get("validation_macro_f1"),
        "categoricalFields": CATEGORICAL,
        "numericalFields": NUMERICAL,
    }


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

def build_knowledge() -> dict:
    documents = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        title = text.strip().splitlines()[0].strip().title()
        documents.append(
            {"name": path.name, "title": title, "text": text, "chars": len(text)}
        )

    chunks = []
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name="company_knowledge")
        stored = collection.get(include=["documents", "metadatas"])
        for index, content in enumerate(stored["documents"]):
            metadata = stored["metadatas"][index]
            chunks.append(
                {
                    "id": stored["ids"][index],
                    "source": metadata["source"],
                    "chunkId": int(metadata["chunk_id"]),
                    "content": content,
                }
            )
    except Exception as error:  # pragma: no cover - browser demo fallback
        print(f"Chroma export skipped: {error}")

    transcript = {
        "question": "Who approves discounts?",
        "answer": (
            "According to the provided company context, the authorized business "
            "representative approves discounts. This is stated in the "
            '"Discount Policy" section within the "Sales Policy" document: '
            '"Any discount must be approved by the authorized business '
            'representative." Therefore, the correct answer is: Authorized '
            "business representative."
        ),
        "model": "llama3.2:1b",
        "latencySeconds": 9.6,
        "citations": [
            {"source": "sales_policy.txt", "chunkId": 2, "distance": 0.3688},
            {"source": "sales_policy.txt", "chunkId": 1, "distance": 0.6303},
            {"source": "product_and_services.txt", "chunkId": 2, "distance": 0.7635},
        ],
        "note": "Captured from a real local API call to POST /ask.",
    }

    return {
        "documents": documents,
        "chunks": chunks,
        "transcript": transcript,
        "sampleQuestions": [
            "Who approves discounts?",
            "What services does the company offer?",
            "How should sales leads be prioritized?",
            "How are customer quotations prepared?",
            "Who are the target customers?",
            "Where is the company located?",
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "web" / "assets" / "data",
        help="Directory that receives analytics.json, model.json and knowledge.json",
    )
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        raise SystemExit(
            f"Model artifact missing: {MODEL_PATH}. Run the training notebook first."
        )

    artifact = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    df = df[df["converted"].isin([0, 1])].reset_index(drop=True)

    raw = {
        "columns": RAW_COLUMNS,
        "categories": {
            column: sorted(df[column].unique().tolist()) for column in CATEGORICAL
        },
        "rows": [],
    }

    source_index = {value: i for i, value in enumerate(raw["categories"]["lead_source"])}
    industry_index = {value: i for i, value in enumerate(raw["categories"]["industry"])}
    size_index = {value: i for i, value in enumerate(raw["categories"]["company_size"])}

    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                source_index[row["lead_source"]],
                industry_index[row["industry"]],
                size_index[row["company_size"]],
                round(float(row["budget"]), 2),
                int(row["website_visits"]),
                int(row["emails_opened"]),
                int(row["calls_made"]),
                int(row["previous_interactions"]),
                round(float(row["response_time_hours"]), 2),
                int(row["converted"]),
            ]
        )
    raw["rows"] = rows

    knowledge = build_knowledge()
    analytics = build_analytics(df, artifact, raw, knowledge)
    model = build_model(artifact)

    args.out.mkdir(parents=True, exist_ok=True)
    for name, payload, compact in (
        ("analytics.json", analytics, True),
        ("model.json", model, False),
        ("knowledge.json", knowledge, False),
    ):
        target = args.out / name
        text = (
            json.dumps(payload, separators=(",", ":"))
            if compact
            else json.dumps(payload, indent=2)
        )
        target.write_text(text, encoding="utf-8")
        print(
            f"Wrote {target.relative_to(PROJECT_ROOT)} "
            f"({target.stat().st_size / 1024:.1f} KB)"
        )

    print(
        f"Rows={analytics['dataset']['rows']} "
        f"conversion={analytics['kpis']['conversionRate']}% "
        f"holdout-acc={analytics['holdout']['accuracy']} "
        f"chunks={len(knowledge['chunks'])}"
    )


if __name__ == "__main__":
    main()
