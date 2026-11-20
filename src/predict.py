"""
Prediction script for Freight Rate Prediction.

Generates:
  - validation_predictions.csv    (12,000 rows: load_id, predicted_rate)
  - december-chart-inputs.csv     (31 rows: filled with predicted_rate)

Usage (from project root with venv activated):
    python src/predict.py
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from features import build_features

# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
MODEL_DIR = ROOT / "models"


def predict_positive(model, X):
    """Predict, un-log-transform, and enforce positivity."""
    y_log = model.predict(X)
    y = np.expm1(y_log)
    return np.clip(y, 1.0, None)


def infer_december_signals(train_df: pd.DataFrame) -> tuple[float, float]:
    """
    Estimate market_index and quote_signal for December 2025.
    Strategy: use the mean of the last 30 days of training data (October).
    """
    train_df = train_df.copy()
    train_df["date"] = pd.to_datetime(train_df["date"])
    last_month = train_df[train_df["date"] >= "2025-10-01"]
    if len(last_month) == 0:
        last_month = train_df.tail(1000)
    market_mean = last_month["market_index"].mean()
    quote_mean  = last_month["quote_signal"].mean()
    return float(market_mean), float(quote_mean)


def main():
    # ── Load model and route stats ─────────────────────────────────────────────
    print("Loading model...")
    bundle = joblib.load(MODEL_DIR / "best_model.pkl")
    model = bundle["model"]
    model_name = bundle["model_name"]
    route_stats = joblib.load(MODEL_DIR / "route_stats.pkl")
    print(f"  Model: {model_name}")

    # ── Load training data (for signal inference) ──────────────────────────────
    print("Loading data...")
    train_df = pd.read_csv(ROOT / "train-test.csv")
    val_df   = pd.read_csv(ROOT / "validation.csv")
    dec_df   = pd.read_csv(ROOT / "december-chart-inputs.csv")
    template = pd.read_csv(ROOT / "validation-predictions-template.csv")
    print(f"  Validation rows: {len(val_df):,}")
    print(f"  December rows:   {len(dec_df)}")

    # ── Validation predictions ─────────────────────────────────────────────────
    print("\nGenerating validation predictions...")
    X_val = build_features(val_df, train_route_stats=route_stats)
    val_preds = predict_positive(model, X_val)

    # Build output: match to template load_id order
    output = template.copy()
    id_to_pred = dict(zip(val_df["load_id"].astype(str), val_preds))
    output["predicted_rate"] = output["load_id"].astype(str).map(id_to_pred)

    if output["predicted_rate"].isna().any():
        print(f"WARNING: {output['predicted_rate'].isna().sum()} missing predictions!")

    output.to_csv(ROOT / "validation_predictions.csv", index=False)
    print(f"  Saved → validation_predictions.csv")
    print(f"  Rate range: ${output['predicted_rate'].min():.2f} – ${output['predicted_rate'].max():.2f}")
    print(f"  Rate mean:  ${output['predicted_rate'].mean():.2f}")

    # ── December predictions ───────────────────────────────────────────────────
    print("\nGenerating December 2025 predictions...")
    market_mean, quote_mean = infer_december_signals(train_df)
    print(f"  Inferred market_index: {market_mean:.5f}")
    print(f"  Inferred quote_signal: {quote_mean:.5f}")

    # Enrich december inputs with signal estimates and coordinates for Lexington→Fort Wayne
    # Lexington, KY: ~38.0406° N, 84.5037° W
    # Fort Wayne, IN: ~41.0793° N, 85.1394° W
    dec_df["pickup_lat"]    = 38.0406
    dec_df["pickup_lon"]    = -84.5037
    dec_df["delivery_lat"]  = 41.0793
    dec_df["delivery_lon"]  = -85.1394
    dec_df["market_index"]  = market_mean
    dec_df["quote_signal"]  = quote_mean

    X_dec = build_features(dec_df, train_route_stats=route_stats)
    dec_preds = predict_positive(model, X_dec)

    # Fill predicted_rate and save
    dec_out = pd.read_csv(ROOT / "december-chart-inputs.csv")
    dec_out["predicted_rate"] = np.round(dec_preds, 2)
    dec_out.to_csv(ROOT / "december-chart-inputs.csv", index=False)
    print(f"  Saved → december-chart-inputs.csv")
    print(f"  Rate range: ${dec_out['predicted_rate'].min():.2f} – ${dec_out['predicted_rate'].max():.2f}")
    print(f"  Rate mean:  ${dec_out['predicted_rate'].mean():.2f}")

    print("\nDone! Now run:")
    print("  .\\venv\\Scripts\\python.exe score.py --predictions validation_predictions.csv --december-predictions december-chart-inputs.csv")


if __name__ == "__main__":
    main()
