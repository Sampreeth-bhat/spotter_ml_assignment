"""
Feature engineering pipeline for Freight Rate Prediction.
Applies consistent transformations to train, validation, and December data.
"""

import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
EQUIPMENT_MAP = {"Dry Van": 0, "Reefer": 1, "Flatbed": 2}

US_HOLIDAYS_2025 = {
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # MLK Day
    "2025-02-17",  # Presidents' Day
    "2025-05-26",  # Memorial Day
    "2025-06-19",  # Juneteenth
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving
    "2025-11-28",  # Day after Thanksgiving
    "2025-12-24",  # Christmas Eve
    "2025-12-25",  # Christmas Day
    "2025-12-31",  # New Year's Eve
}


# ──────────────────────────────────────────────────────────────────────────────
# Core feature builder
# ──────────────────────────────────────────────────────────────────────────────
def build_features(df: pd.DataFrame, train_route_stats: dict | None = None) -> pd.DataFrame:
    """
    Build features from raw dataframe.

    Parameters
    ----------
    df : raw dataframe (train, validation, or december)
    train_route_stats : dict of route_pair -> (mean_rate, count) from training data
                        Pass None to skip route-encoding (computed from training only).

    Returns
    -------
    Feature matrix ready for model (no string columns).
    """
    df = df.copy()

    # ── Date features ────────────────────────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.dayofweek          # 0=Mon, 6=Sun
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_year"] = df["date"].dt.dayofyear
    df["quarter"] = df["date"].dt.quarter
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_holiday"] = df["date"].dt.strftime("%Y-%m-%d").isin(US_HOLIDAYS_2025).astype(int)
    df["days_since_start"] = (df["date"] - pd.Timestamp("2025-01-01")).dt.days

    # ── Equipment encoding ───────────────────────────────────────────────────
    df["equipment_code"] = df["equipment"].map(EQUIPMENT_MAP).fillna(-1).astype(int)
    # One-hot
    for equip, code in EQUIPMENT_MAP.items():
        df[f"equip_{equip.lower().replace(' ', '_')}"] = (df["equipment"] == equip).astype(int)

    # ── Handle missing values BEFORE feature computation ────────────────────
    # weight: fill with median (300 missing in train)
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df["weight"] = df["weight"].fillna(df["weight"].median() if not df["weight"].isna().all() else 30000.0)
    # market_index: fill with 1.0 (neutral market) — 374 missing in train
    if "market_index" in df.columns:
        df["market_index"] = pd.to_numeric(df["market_index"], errors="coerce").fillna(1.0)

    # ── Distance & weight features ───────────────────────────────────────────
    df["distance"] = df["distance"].astype(float)
    df["weight"] = df["weight"].astype(float)
    df["log_distance"] = np.log1p(df["distance"])
    df["log_weight"] = np.log1p(df["weight"])
    df["distance_x_weight"] = df["distance"] * df["weight"] / 1e6  # normalize

    # ── Geographic features ──────────────────────────────────────────────────
    df["pickup_lat"] = df["pickup_lat"].astype(float)
    df["pickup_lon"] = df["pickup_lon"].astype(float)
    df["delivery_lat"] = df["delivery_lat"].astype(float)
    df["delivery_lon"] = df["delivery_lon"].astype(float)

    # Lat/lon delta (direction indicators)
    df["lat_delta"] = df["delivery_lat"] - df["pickup_lat"]
    df["lon_delta"] = df["delivery_lon"] - df["pickup_lon"]
    df["abs_lat_delta"] = df["lat_delta"].abs()
    df["abs_lon_delta"] = df["lon_delta"].abs()

    # Haversine distance (cross-check vs reported distance)
    df["haversine_dist"] = haversine_distance(
        df["pickup_lat"], df["pickup_lon"],
        df["delivery_lat"], df["delivery_lon"]
    )

    # Geographic centroid
    df["mid_lat"] = (df["pickup_lat"] + df["delivery_lat"]) / 2
    df["mid_lon"] = (df["pickup_lon"] + df["delivery_lon"]) / 2

    # ── Market signals ───────────────────────────────────────────────────────
    df["market_index"] = df["market_index"].astype(float)
    df["quote_signal"] = df["quote_signal"].astype(float)
    df["market_x_quote"] = df["market_index"] * df["quote_signal"]
    df["market_x_distance"] = df["market_index"] * df["distance"]
    df["quote_x_distance"] = df["quote_signal"] * df["distance"]

    # ── Route encoding ───────────────────────────────────────────────────────
    df["route_pair"] = df["pickup"] + " -> " + df["delivery"]
    if train_route_stats is not None:
        df["route_mean_rate"] = df["route_pair"].map(
            lambda r: train_route_stats.get(r, {}).get("mean", np.nan)
        )
        df["route_count"] = df["route_pair"].map(
            lambda r: train_route_stats.get(r, {}).get("count", 0)
        )
        # Fill unseen routes with global mean
        global_mean = np.nanmean(list(s["mean"] for s in train_route_stats.values()))
        df["route_mean_rate"] = df["route_mean_rate"].fillna(global_mean)
        df["route_count"] = df["route_count"].fillna(0)

    # ── Feature list (returned as numeric columns only) ───────────────────────
    feature_cols = [
        # Distance/weight
        "distance", "log_distance", "weight", "log_weight", "distance_x_weight",
        # Geography
        "pickup_lat", "pickup_lon", "delivery_lat", "delivery_lon",
        "lat_delta", "lon_delta", "abs_lat_delta", "abs_lon_delta",
        "haversine_dist", "mid_lat", "mid_lon",
        # Equipment
        "equipment_code", "equip_dry_van", "equip_reefer", "equip_flatbed",
        # Market signals
        "market_index", "quote_signal",
        "market_x_quote", "market_x_distance", "quote_x_distance",
        # Date
        "day_of_week", "month", "week_of_year", "day_of_year",
        "quarter", "is_weekend", "is_holiday", "days_since_start",
    ]

    if train_route_stats is not None:
        feature_cols += ["route_mean_rate", "route_count"]

    result = df[feature_cols].copy()
    # Final safety: fill any remaining NaN with column median (or 0 for counts/flags)
    result = result.fillna(result.median(numeric_only=True))
    return result


def haversine_distance(lat1, lon1, lat2, lon2):
    """Compute haversine distance in miles."""
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def compute_route_stats(train_df: pd.DataFrame) -> dict:
    """
    Compute per-route mean rate and count from training data.
    Returns dict: route_pair -> {'mean': float, 'count': int}
    """
    train_df = train_df.copy()
    train_df["route_pair"] = train_df["pickup"] + " -> " + train_df["delivery"]
    stats = (
        train_df.groupby("route_pair")["posted_rate"]
        .agg(["mean", "count"])
        .to_dict(orient="index")
    )
    return stats
