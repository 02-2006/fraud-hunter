"""
FraudHunter AI — Model Training Pipeline
Trains XGBoost + Isolation Forest ensemble on labeled transaction data
Run: python train_model.py --data ./data/transactions.csv --output ./models/fraud_model.pkl
"""
import argparse
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "amount", "amount_log", "hour_of_day", "day_of_week",
    "is_weekend", "is_night", "is_card_present", "country_mismatch",
    "amount_velocity_1h", "count_velocity_1h",
    "amount_velocity_24h", "count_velocity_24h",
    "avg_tx_amount_30d", "std_tx_amount_30d", "amount_zscore",
    "is_new_device", "is_new_merchant", "merchant_risk_score",
    "geo_distance_km", "time_since_last_tx_min",
]
LABEL_COL = "is_fraud"


def generate_synthetic_data(n_samples: int = 100_000) -> pd.DataFrame:
    """
    Generate synthetic transaction data for training.
    In production: replace with real labeled data from your warehouse.
    Fraud rate: ~1% (realistic imbalance).
    """
    logger.info(f"Generating {n_samples:,} synthetic transactions...")
    np.random.seed(42)
    n_fraud = int(n_samples * 0.01)
    n_legit = n_samples - n_fraud

    def legit_batch(n):
        return {
            "amount": np.random.lognormal(mean=4.5, sigma=1.2, size=n),
            "hour_of_day": np.random.randint(8, 22, n),
            "day_of_week": np.random.randint(0, 7, n),
            "is_weekend": np.random.choice([0, 1], n, p=[0.72, 0.28]),
            "is_night": np.zeros(n),
            "is_card_present": np.ones(n),
            "country_mismatch": np.random.choice([0, 1], n, p=[0.95, 0.05]),
            "amount_velocity_1h": np.random.exponential(200, n),
            "count_velocity_1h": np.random.poisson(1.5, n),
            "amount_velocity_24h": np.random.exponential(800, n),
            "count_velocity_24h": np.random.poisson(5, n),
            "avg_tx_amount_30d": np.random.lognormal(4.3, 0.8, n),
            "std_tx_amount_30d": np.random.exponential(80, n),
            "is_new_device": np.random.choice([0, 1], n, p=[0.92, 0.08]),
            "is_new_merchant": np.random.choice([0, 1], n, p=[0.75, 0.25]),
            "merchant_risk_score": np.random.beta(1, 9, n),
            "geo_distance_km": np.random.exponential(30, n),
            "time_since_last_tx_min": np.random.exponential(180, n),
            "is_fraud": np.zeros(n, dtype=int),
        }

    def fraud_batch(n):
        return {
            "amount": np.random.lognormal(mean=7.0, sigma=1.5, size=n),
            "hour_of_day": np.random.choice(list(range(0, 6)) + list(range(22, 24)), n),
            "day_of_week": np.random.randint(0, 7, n),
            "is_weekend": np.random.choice([0, 1], n, p=[0.5, 0.5]),
            "is_night": np.ones(n),
            "is_card_present": np.random.choice([0, 1], n, p=[0.7, 0.3]),
            "country_mismatch": np.random.choice([0, 1], n, p=[0.3, 0.7]),
            "amount_velocity_1h": np.random.exponential(5000, n),
            "count_velocity_1h": np.random.poisson(12, n),
            "amount_velocity_24h": np.random.exponential(15000, n),
            "count_velocity_24h": np.random.poisson(25, n),
            "avg_tx_amount_30d": np.random.lognormal(4.0, 0.7, n),
            "std_tx_amount_30d": np.random.exponential(60, n),
            "is_new_device": np.random.choice([0, 1], n, p=[0.2, 0.8]),
            "is_new_merchant": np.random.choice([0, 1], n, p=[0.3, 0.7]),
            "merchant_risk_score": np.random.beta(5, 2, n),
            "geo_distance_km": np.random.exponential(3000, n),
            "time_since_last_tx_min": np.random.exponential(5, n),
            "is_fraud": np.ones(n, dtype=int),
        }

    df_legit = pd.DataFrame(legit_batch(n_legit))
    df_fraud = pd.DataFrame(fraud_batch(n_fraud))
    df = pd.concat([df_legit, df_fraud], ignore_index=True)

    # Derived features
    df["amount_log"] = np.log1p(df["amount"])
    df["amount_zscore"] = (df["amount"] - df["avg_tx_amount_30d"]) / (df["std_tx_amount_30d"] + 1e-6)

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    logger.info(f"Dataset: {len(df):,} rows | Fraud rate: {df[LABEL_COL].mean():.2%}")
    return df


def build_model() -> Pipeline:
    """XGBoost classifier with preprocessing pipeline"""
    xgb = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=99,       # accounts for 1% fraud rate
        eval_metric="aucpr",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", xgb),
    ])


def evaluate(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = {
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "false_positive_rate": (
            confusion_matrix(y_test, y_pred)[0][1] /
            (confusion_matrix(y_test, y_pred)[0].sum() + 1e-9)
        ),
    }
    logger.info("─── Evaluation Results ───────────────────────────")
    for k, v in metrics.items():
        logger.info(f"  {k:<25} {v:.4f}")
    logger.info(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    return metrics


def train(data_path: str, output_path: str, n_synthetic: int = 100_000):
    if data_path and Path(data_path).exists():
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
    else:
        logger.warning("No data file found — using synthetic data.")
        df = generate_synthetic_data(n_synthetic)

    X = df[FEATURE_COLS].fillna(0)
    y = df[LABEL_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    logger.info(f"Training on {len(X_train):,} samples...")
    model = build_model()
    model.fit(X_train, y_train)

    metrics = evaluate(model, X_test, y_test)

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="f1", n_jobs=-1)
    logger.info(f"Cross-val F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Save model with metadata
    artifact = {
        "model": model,
        "feature_cols": FEATURE_COLS,
        "metrics": metrics,
        "trained_at": datetime.utcnow().isoformat(),
        "model_version": "4.2.0",
        "n_train": len(X_train),
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)
    logger.info(f"Model saved to {output_path}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FraudHunter ML model")
    parser.add_argument("--data", default="", help="Path to labeled CSV dataset")
    parser.add_argument("--output", default="./models/fraud_model.pkl")
    parser.add_argument("--samples", type=int, default=100_000, help="Synthetic samples if no data")
    args = parser.parse_args()
    train(args.data, args.output, args.samples)
