# Freight Rate Prediction — ML Solution

> **Spotter Machine Learning Engineer Assessment**
> Predict freight load rates (USD) for US trucking shipments.

---

## Solution Overview

A **LightGBM** regression model trained on 48,000 historical loads (Jan–Oct 2025) using a temporal train/validation split. The model achieves:

| Metric | Score |
|--------|-------|
| RMSE | \$668.69 |
| MAE  | \$182.90 |
| R²   | 0.8086 |
| MAPE | 8.72% |

---

## Project Structure

```
spotter_ml_assignment/
├── src/
│   ├── eda.py              # Exploratory data analysis + plots
│   ├── features.py         # Feature engineering pipeline (35 features)
│   ├── train.py            # Model training with temporal split
│   └── predict.py          # Validation & December predictions
├── models/
│   └── metrics.txt         # Validation metrics for all models tested
├── scorer_results/
│   ├── candidate_december.png   # Required December 2025 chart
│   └── eda/                     # EDA plots
├── score.py                # Provided scorer (unchanged)
├── requirements.txt        # Scorer dependencies
├── requirements_ml.txt     # Full ML dependencies
├── validation_predictions.csv       # Final predictions (12,000 rows)
├── december-chart-inputs.csv        # Filled December predictions
└── run_all.ps1             # One-click full pipeline runner
```

---

## Quickstart

### 1. Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
pip install -r requirements_ml.txt
```

### 3. Run full pipeline

```powershell
# One command — EDA → Train → Predict → Score
.\run_all.ps1
```

**Or step by step:**

```powershell
.\venv\Scripts\python.exe src\eda.py       # EDA + plots
.\venv\Scripts\python.exe src\train.py     # Train all models, select best
.\venv\Scripts\python.exe src\predict.py   # Generate predictions
.\venv\Scripts\python.exe score.py --predictions validation_predictions.csv --december-predictions december-chart-inputs.csv
```

---

## Data Split Strategy

**Temporal split** — no random shuffling to preserve time-series integrity:

- **Training**: Jan 1 – Sep 30, 2025 (43,147 rows)
- **Local validation**: Oct 1 – Oct 31, 2025 (4,853 rows)
- **Final model**: Retrained on all 48,000 rows before predicting

Walk-forward validation across 4 consecutive months confirmed consistent generalization (mean RMSE \$655.96 ± \$15.11).

---

## Feature Engineering (35 features)

| Group | Features |
|-------|---------|
| **Distance & weight** | `distance`, `log_distance`, `weight`, `log_weight`, `distance × weight` |
| **Geographic** | `pickup_lat/lon`, `delivery_lat/lon`, `lat_delta`, `lon_delta`, `haversine_dist`, `mid_lat/lon` |
| **Equipment** | `equipment_code`, one-hot for Dry Van / Reefer / Flatbed |
| **Market signals** | `market_index`, `quote_signal`, and 3 interaction terms |
| **Temporal** | `day_of_week`, `month`, `week_of_year`, `day_of_year`, `quarter`, `is_weekend`, `is_holiday`, `days_since_start` |
| **Route encoding** | `route_mean_rate`, `route_count` (computed from training data only) |

---

## Models Compared

| Model | RMSE | MAE | R² | MAPE |
|-------|------|-----|----|------|
| **LightGBM** ✅ | **\$668.69** | \$182.90 | **0.8086** | 8.72% |
| Ridge | \$668.75 | **\$141.65** | 0.8086 | 6.19% |
| Random Forest | \$681.14 | \$172.49 | 0.8014 | 7.90% |
| XGBoost | \$683.15 | \$206.14 | 0.8003 | 9.93% |

LightGBM selected as the best model by RMSE. Final model retrained on all 48,000 training rows.

---

## Scorer Output

```
Validated 12,000 final predictions.
Validated 31 fixed December predictions.
Created chart: scorer_results/candidate_december.png
Final validation metrics are calculated by Spotter after submission.
```

---

## Dependencies

**Scorer (`requirements.txt`):**
```
matplotlib>=3.8,<4
numpy>=1.26,<3
pandas>=2.0,<3
```

**Full ML stack (`requirements_ml.txt`):**
```
scikit-learn>=1.9
xgboost>=3.4
lightgbm>=4.7
joblib>=1.6
```
