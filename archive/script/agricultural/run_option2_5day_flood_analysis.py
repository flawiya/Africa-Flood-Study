"""
run_option2_5day_flood_analysis.py
===================================
Standalone script for computing Option 2 ONLY (5-Day Continuous Basis):
  - 95th Percentile (P95) SWI + 85% Absolute Physical SWI Floor
  - 5-Day Continuous Streak Basis
  - Crop Years 2008 to 2024 (17 crop years) across all 1,638 African agricultural districts

Outputs to:
  - output/agricultural/meeting_30th_july_output/Africa_Maize_Flood_Annual_Option2_5Day.csv
  - output/agricultural/meeting_30th_july_output/Option2_95th_plus_Absolute_5Day_Dashboard.html
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_CSV  = os.path.join(OUT_DIR, "Africa_Maize_Flood_Annual_Option2_5Day.csv")
OUT_HTML = os.path.join(OUT_DIR, "Option2_95th_plus_Absolute_5Day_Dashboard.html")


def compute_streak_summary(df_in, flag_col, min_streak=5):
    """Compute 5-day continuous streak flood metrics per district per crop year."""
    df_calc = df_in.copy()
    df_calc["block"] = (df_calc[flag_col] != df_calc.groupby(["COUNTRY", "ADM_NAME"])[flag_col].shift()).cumsum()
    block_len = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])[flag_col].transform(lambda s: s.sum() if s.iloc[0] else 0)

    df_calc["valid_streak_day"] = df_calc[flag_col] & (block_len >= min_streak)
    df_calc["max_streak_len"]   = block_len

    summary = df_calc.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        planting=("planting", "first"),
        harvest=("harvest", "first"),
        mean_swi=("swi_t10_mean", "mean"),
        max_swi=("swi_t10_mean", "max"),
        flood_days_5plus=("valid_streak_day", "sum"),
        max_consec_days=("max_streak_len", "max")
    ).reset_index()

    summary["mean_swi"] = summary["mean_swi"].round(2)
    summary["max_swi"]  = summary["max_swi"].round(2)

    events = df_calc[df_calc["valid_streak_day"]].groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"])["block"].nunique().reset_index()
    events.rename(columns={"block": "num_flood_events"}, inplace=True)

    summary = summary.merge(events, on=["ISO3", "COUNTRY", "ADM_NAME", "crop_year"], how="left").fillna({"num_flood_events": 0})
    summary["num_flood_events"] = summary["num_flood_events"].astype(int)

    return summary


def main():
    print("=" * 70)
    print("1. Loading raw daily SWI dataset for Option 2 (5-Day Basis)...")
    print("=" * 70)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year

    plant_doy = pd.to_numeric(df["planting"], errors="coerce")
    harvest_doy = pd.to_numeric(df["harvest"], errors="coerce")
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1

    df = df[df["COUNTRY"] != "Morocco"]
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])

    print("\n2. Filtering dataset to 2008–2024 (17 crop years)...")
    df = df[~df["crop_year"].isin([2007, 2025])]
    print(f"   Observation records: {len(df):,}")
    print(f"   Districts: {df['ADM_NAME'].nunique()}")

    print("\n3. Computing Option 2 Flag (P95 SWI Threshold + 85% Absolute SWI Floor)...")
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    df["p95_threshold"] = p95.round(2)
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)

    print("\n4. Computing 5-day continuous streak flood metrics...")
    summary = compute_streak_summary(df, "flag_opt2", min_streak=5)

    summary.to_csv(OUT_CSV, index=False)
    print(f"\n[OK] Saved Option 2 5-Day Master CSV: {OUT_CSV}")
    print(f"     Total District-Year Records: {len(summary):,}")
    print(f"     Total Flood Days Triggered: {summary['flood_days_5plus'].sum():,}")
    print(f"     Total Flood Events Triggered: {summary['num_flood_events'].sum():,}")


if __name__ == "__main__":
    main()
