"""
Model training script for Freight Rate Prediction.

Usage (from project root with venv activated):
    python src/train.py

Outputs:
    models/best_model.pkl    — trained model pipeline
    models/route_stats.pkl   — route encoding stats
    models/metrics.txt       — validation metrics
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import lightgbm as lgb

# Local imports
import sys
sys.path.insert(0, str(Path(__file__).parent))
from features import build_features, compute_route_stats

# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)


def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def evaluate(name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape_val = mape(y_true, y_pred)
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"  RMSE : {rmse:,.2f}")
    print(f"  MAE  : {mae:,.2f}")
    print(f"  R²   : {r2:.4f}")
    print(f"  MAPE : {mape_val:.2f}%")
    return {"model": name, "rmse": rmse, "mae": mae, "r2": r2, "mape": mape_val}


def main():
    print("Loading training data...")
    train_full = pd.read_csv(DATA_DIR / "train-test.csv")
    print(f"  Shape: {train_full.shape}")
    print(f"  Date range: {train_full['date'].min()} → {train_full['date'].max()}")

    # ── Temporal train/val split ──────────────────────────────────────────────
    # Train: Jan–Sep 2025 (80%), Local Val: Oct 2025 (20%)
    train_full["date"] = pd.to_datetime(train_full["date"])
    split_date = "2025-10-01"
    train_df = train_full[train_full["date"] < split_date].copy()
    val_df   = train_full[train_full["date"] >= split_date].copy()
    print(f"\nTemporal split at {split_date}:")
    print(f"  Train: {len(train_df):,} rows ({train_df['date'].min().date()} → {train_df['date'].max().date()})")
    print(f"  Local val: {len(val_df):,} rows ({val_df['date'].min().date()} → {val_df['date'].max().date()})")

    # ── Feature engineering ──────────────────────────────────────────────────
    print("\nBuilding features...")
    route_stats = compute_route_stats(train_df)
    joblib.dump(route_stats, MODEL_DIR / "route_stats.pkl")

    X_train = build_features(train_df, train_route_stats=route_stats)
    X_val   = build_features(val_df, train_route_stats=route_stats)
    y_train = np.log1p(train_df["posted_rate"].values)   # log-transform target
    y_val   = np.log1p(val_df["posted_rate"].values)
    y_val_raw = val_df["posted_rate"].values

    print(f"  Feature count: {X_train.shape[1]}")
    print(f"  Features: {list(X_train.columns)}")

    # ── Model definitions ────────────────────────────────────────────────────
    models = {
        "Ridge": Ridge(alpha=10.0),
        "XGBoost": xgb.XGBRegressor(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        ),
        "LightGBM": lgb.LGBMRegressor(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),
    }

    # ── Train and evaluate all models ─────────────────────────────────────────
    results = []
    trained_models = {}
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model

        # Predict on local val (un-transform from log)
        y_pred_log = model.predict(X_val)
        y_pred = np.expm1(y_pred_log)
        y_pred = np.clip(y_pred, 1.0, None)   # enforce positivity

        metrics = evaluate(name, y_val_raw, y_pred)
        results.append(metrics)

    # ── Select best model by RMSE ─────────────────────────────────────────────
    best = min(results, key=lambda x: x["rmse"])
    best_model = trained_models[best["model"]]
    print(f"\n{'='*50}")
    print(f"Best model: {best['model']}  (RMSE={best['rmse']:,.2f})")

    # Retrain best model on ALL training data before saving
    print(f"\nRetraining {best['model']} on full training data...")
    route_stats_full = compute_route_stats(train_full)
    joblib.dump(route_stats_full, MODEL_DIR / "route_stats.pkl")  # overwrite with full stats
    X_full = build_features(train_full, train_route_stats=route_stats_full)
    y_full = np.log1p(train_full["posted_rate"].values)
    best_model.fit(X_full, y_full)

    # ── Save model ────────────────────────────────────────────────────────────
    model_path = MODEL_DIR / "best_model.pkl"
    joblib.dump({"model": best_model, "model_name": best["model"]}, model_path)
    print(f"Saved model → {model_path}")

    # ── Save metrics ──────────────────────────────────────────────────────────
    metrics_path = MODEL_DIR / "metrics.txt"
    with open(metrics_path, "w") as f:
        f.write("Freight Rate Prediction — Validation Metrics\n")
        f.write(f"Temporal split: train < {split_date}, val >= {split_date}\n\n")
        for r in results:
            f.write(f"{r['model']}: RMSE={r['rmse']:.2f}, MAE={r['mae']:.2f}, R2={r['r2']:.4f}, MAPE={r['mape']:.2f}%\n")
        f.write(f"\nBest: {best['model']}\n")
    print(f"Metrics saved → {metrics_path}")


if __name__ == "__main__":
    main()
