# Sales & Operations Intelligence Copilot
## Day 1 - Machine Learning Development Report

### 1. Project Objective
Build a machine learning system that estimates the
probability of sales lead conversion.

### 2. Dataset
- Total records: 5,000
- Input features: 9
- Target: converted
- Converted leads: 82.68%
- Not converted leads: 17.32%
- Dataset: Synthetic sales lead data

### 3. Data Processing
- Numerical imputation
- Categorical imputation
- StandardScaler
- OneHotEncoder
- ColumnTransformer
- Stratified train-validation-test split

### 4. Models Evaluated
- DummyClassifier
- Logistic Regression
- Random Forest
- Gradient Boosting

### 5. Selected Model
- Model: Logistic Regression
- Decision threshold: 0.75
- Validation Macro F1: 0.62
- Test Accuracy: 0.746
- Test ROC-AUC: approximately 0.66

### 6. Inference Pipeline
The saved pipeline combines preprocessing
and Logistic Regression classification.

Artifact:
models/lead_conversion_pipeline.joblib

Inference module:
src/ml/predict.py

### 7. Scenario Testing
- High-engagement lead: 96.58%
- Low-engagement lead: 33.98%
- Unseen-category lead: 66.08%

All three inference scenarios executed successfully.

### 8. Limitations
- Dataset is synthetic.
- Results do not establish real-world business performance.
- Predictions are estimates, not guaranteed outcomes.
- Model requires validation on real business data.

### 9. Day 1 Outcome
ML training, model evaluation, model serialization,
inference implementation and scenario testing completed.