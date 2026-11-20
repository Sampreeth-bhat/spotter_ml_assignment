"""
Exploratory Data Analysis for Freight Rate Prediction.
Prints statistics and saves plots to scorer_results/eda/

Usage:
    python src/eda.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "scorer_results" / "eda"
OUTPUT.mkdir(parents=True, exist_ok=True)


def main():
    print("Loading training data...")
    df = pd.read_csv(ROOT / "train-test.csv")
    df["date"] = pd.to_datetime(df["date"])

    print(f"\n{'='*60}")
    print("BASIC INFO")
    print(f"Shape: {df.shape}")
    print(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"\nColumns:\n{df.dtypes}")
    print(f"\nMissing values:\n{df.isnull().sum()}")

    print(f"\n{'='*60}")
    print("TARGET VARIABLE (posted_rate)")
    print(df["posted_rate"].describe().round(2))

    print(f"\n{'='*60}")
    print("EQUIPMENT DISTRIBUTION")
    print(df["equipment"].value_counts())

    print(f"\n{'='*60}")
    print("RATE BY EQUIPMENT")
    print(df.groupby("equipment")["posted_rate"].agg(["mean", "median", "std"]).round(2))

    print(f"\n{'='*60}")
    print("CORRELATION WITH TARGET")
    numerics = ["distance", "weight", "market_index", "quote_signal", "posted_rate"]
    print(df[numerics].corr()["posted_rate"].sort_values(ascending=False).round(4))

    # ── Plot 1: Rate distribution ─────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(df["posted_rate"], bins=100, color="#064A56", alpha=0.7)
    axes[0].set_title("posted_rate distribution")
    axes[0].set_xlabel("Rate ($)")
    axes[1].hist(np.log1p(df["posted_rate"]), bins=100, color="#064A56", alpha=0.7)
    axes[1].set_title("log(posted_rate + 1) distribution")
    axes[1].set_xlabel("log(Rate)")
    plt.tight_layout()
    plt.savefig(OUTPUT / "01_rate_distribution.png", dpi=120)
    plt.close()

    # ── Plot 2: Rate over time ────────────────────────────────────────────────
    daily = df.groupby("date")["posted_rate"].mean()
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(daily.index, daily.values, color="#064A56", linewidth=1.5)
    ax.set_title("Average Freight Rate Over Time (Jan–Oct 2025)")
    ax.set_ylabel("Avg Rate ($)")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT / "02_rate_over_time.png", dpi=120)
    plt.close()

    # ── Plot 3: Rate by equipment ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 4))
    df.boxplot(column="posted_rate", by="equipment", ax=ax)
    ax.set_title("Rate by Equipment Type")
    ax.set_ylabel("Rate ($)")
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig(OUTPUT / "03_rate_by_equipment.png", dpi=120)
    plt.close()

    # ── Plot 4: Distance vs Rate scatter ──────────────────────────────────────
    sample = df.sample(5000, random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {"Dry Van": "#064A56", "Reefer": "#F4A261", "Flatbed": "#E76F51"}
    for equip, grp in sample.groupby("equipment"):
        ax.scatter(grp["distance"], grp["posted_rate"], alpha=0.3, s=5,
                   color=colors.get(equip, "gray"), label=equip)
    ax.set_title("Distance vs Rate")
    ax.set_xlabel("Distance (miles)")
    ax.set_ylabel("Rate ($)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT / "04_distance_vs_rate.png", dpi=120)
    plt.close()

    # ── Plot 5: Market signals ────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].scatter(df["market_index"], df["posted_rate"], alpha=0.1, s=2, color="#064A56")
    axes[0].set_title("market_index vs Rate")
    axes[1].scatter(df["quote_signal"], df["posted_rate"], alpha=0.1, s=2, color="#E76F51")
    axes[1].set_title("quote_signal vs Rate")
    plt.tight_layout()
    plt.savefig(OUTPUT / "05_market_signals.png", dpi=120)
    plt.close()

    print(f"\nEDA plots saved to: {OUTPUT}")
    print("\nDone!")


if __name__ == "__main__":
    main()
