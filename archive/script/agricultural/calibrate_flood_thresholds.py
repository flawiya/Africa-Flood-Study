"""
SWI Flood Index Calibration Engine
=============================================================================
Evaluates Models 1, 2, and 3 across 2007-2025 data to calibrate flood sensitivity:
- Target: Severe "bad years" should trigger ~10 to 20 flood days max per season.
- Model 1: P99 Percentile threshold per district.
- Model 2: P95 Percentile + Absolute Cap (SWI >= 85%).
- Model 3: Pure Absolute Cap (SWI >= 90% for 3+ consecutive days).

Compares Area-Weighted Mean (swi_t10_mean) vs Raw Unweighted (swi_t10_raw).
Output saved to output/agricultural/flood_threshold_calibration_results.csv
"""

import os, pandas as pd, numpy as np

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
OUT_CSV  = os.path.join(BASE_DIR, r"output\agricultural\flood_threshold_calibration_results.csv")

def run_calibration():
    print("[Calibration] Loading master dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    print(f"Total rows loaded: {len(df):,}", flush=True)

    results = []

    for metric in ["swi_t10_mean", "swi_t10_raw"]:
        print(f"\n--- Calibrating Metric: {metric} ---", flush=True)

        # 1. Compute District-Level Percentiles (P95 & P99)
        p95 = df.groupby(["COUNTRY", "ADM_NAME"])[metric].transform(lambda x: np.percentile(x, 95))
        p99 = df.groupby(["COUNTRY", "ADM_NAME"])[metric].transform(lambda x: np.percentile(x, 99))

        df_calc = df.copy()
        df_calc["p95"] = p95
        df_calc["p99"] = p99

        # --- MODEL 1: P99 Percentile ---
        df_calc["m1_trigger"] = df_calc[metric] >= df_calc["p99"]

        # --- MODEL 2: P95 + Absolute Cap (>= 85%) ---
        df_calc["m2_trigger"] = (df_calc[metric] >= df_calc["p95"]) & (df_calc[metric] >= 85.0)

        # --- MODEL 3: Absolute Cap (>= 90% for 3+ consecutive days) ---
        df_calc["is_90"] = df_calc[metric] >= 90.0
        # Group by consecutive days per district
        df_calc["block"] = (df_calc["is_90"] != df_calc.groupby(["COUNTRY", "ADM_NAME"])["is_90"].shift()).cumsum()
        streak = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])["is_90"].transform("sum")
        df_calc["m3_trigger"] = df_calc["is_90"] & (streak >= 3)

        # Aggregate annual trigger counts per district
        annual = df_calc.groupby(["COUNTRY", "ADM_NAME", "year"])[["m1_trigger", "m2_trigger", "m3_trigger"]].sum().reset_index()

        for m_col, m_name in [("m1_trigger", "Model 1 (P99 Percentile)"), 
                             ("m2_trigger", "Model 2 (P95 + SWI>=85%)"), 
                             ("m3_trigger", "Model 3 (SWI>=90% 3-Day Consecutive)")]:
            
            mean_days = annual[m_col].mean()
            median_days = annual[m_col].median()
            p90_days = np.percentile(annual[m_col], 90)
            p95_days = np.percentile(annual[m_col], 95)
            p99_days = np.percentile(annual[m_col], 99)
            max_days = annual[m_col].max()

            results.append({
                "metric": metric,
                "model_name": m_name,
                "mean_days_per_year": round(mean_days, 2),
                "median_days_per_year": round(median_days, 2),
                "90th_percentile_bad_year_days": round(p90_days, 1),
                "95th_percentile_bad_year_days": round(p95_days, 1),
                "99th_percentile_worst_year_days": round(p99_days, 1),
                "absolute_max_days": int(max_days)
            })

    res_df = pd.DataFrame(results)
    res_df.to_csv(OUT_CSV, index=False)
    print("\n[Calibration Complete] Results summary:")
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    run_calibration()
