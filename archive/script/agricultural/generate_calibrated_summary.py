"""
SWI Calibrated Summary Generator (Ultra-Fast Quantile Version)
=============================================================================
Processes the 2007-2025 master dataset and generates the calibrated annual summary
file `SWI_PlantingVeg_Flood_Summary_AllDistricts.csv` for the interactive dashboard.
"""

import os, numpy as np, pandas as pd

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
OUT_SUMMARY_CSV = os.path.join(BASE_DIR, r"output\agricultural\SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")

def main():
    print("[Summary Generator] Loading master dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["crop_year"] = df["date"].dt.year
    
    print(f"Total rows: {len(df):,}", flush=True)

    # 1. Compute per-district P99 and P95 thresholds across historical record using fast quantile
    print("Computing per-district P99 and P95 thresholds (fast quantile)...", flush=True)
    p99_mean = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].quantile(0.99).rename("p99_mean")
    p95_mean = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].quantile(0.95).rename("p95_mean")
    p99_raw  = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_raw"].quantile(0.99).rename("p99_raw")

    df = df.merge(p99_mean, on=["COUNTRY", "ADM_NAME"], how="left")
    df = df.merge(p95_mean, on=["COUNTRY", "ADM_NAME"], how="left")
    df = df.merge(p99_raw,  on=["COUNTRY", "ADM_NAME"], how="left")

    # 2. Flag flood triggers
    print("Flagging flood triggers...", flush=True)
    df["is_flood_m1"]  = (df["swi_t10_mean"] >= df["p99_mean"]).astype(int)
    df["is_flood_m2"]  = ((df["swi_t10_mean"] >= df["p95_mean"]) & (df["swi_t10_mean"] >= 85.0)).astype(int)
    df["is_flood_raw"] = (df["swi_t10_raw"] >= df["p99_raw"]).astype(int)

    # Vectorized streak calculation for Model 1
    print("Calculating streaks...", flush=True)
    df["block"] = (df["is_flood_m1"] != df.groupby(["COUNTRY", "ADM_NAME"])["is_flood_m1"].shift()).cumsum()
    streak_m1 = df.groupby(["COUNTRY", "ADM_NAME", "block"])["is_flood_m1"].transform(lambda s: s.sum() if s.iloc[0] == 1 else 0)
    df["streak_m1"] = streak_m1

    print("Aggregating annual flood metrics per district...", flush=True)
    summary = df.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        planting=("planting", "first"),
        harvest=("harvest", "first"),
        mean_swi=("swi_t10_mean", "mean"),
        max_swi=("swi_t10_mean", "max"),
        flood_days_m1_p99=("is_flood_m1", "sum"),
        max_consec_days_m1=("streak_m1", "max"),
        flood_days_m2_p95cap=("is_flood_m2", "sum"),
        flood_days_raw_p99=("is_flood_raw", "sum")
    ).reset_index()

    summary["mean_swi"] = summary["mean_swi"].round(2)
    summary["max_swi"]  = summary["max_swi"].round(2)

    # Backwards compatibility columns for dashboard
    summary["flood_days_7plus"] = summary["flood_days_m1_p99"]
    summary["num_flood_events_7plus"] = (summary["max_consec_days_m1"] >= 7).astype(int)
    summary["max_consec_days"] = summary["max_consec_days_m1"]

    summary.to_csv(OUT_SUMMARY_CSV, index=False)
    print(f"[Done] Summary written to {OUT_SUMMARY_CSV} ({len(summary):,} rows)", flush=True)

if __name__ == "__main__":
    main()
