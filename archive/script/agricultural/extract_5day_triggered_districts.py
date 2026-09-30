"""
extract_5day_triggered_districts.py
===================================
Extracts triggered districts and their triggered crop years (2008-2024) for Kenya, Malawi, and Nigeria
under Option 2 (P95 + 85% SWI Floor on 5-Day Continuous Basis).
"""

import os
import pandas as pd

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
CSV_PATH = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output\Africa_Maize_Flood_Annual_Option2_5Day.csv")

def main():
    df = pd.read_csv(CSV_PATH)
    
    # Filter for Kenya (KEN), Malawi (MWI), Nigeria (NGA)
    df_sub = df[df["ISO3"].isin(["KEN", "MWI", "NGA"])].copy()
    
    # Filter for triggered years (Flood_Events_Opt2_5Day > 0 or Flood_Days_Opt2_5Day >= 5)
    triggered_df = df_sub[df_sub["Flood_Days_Opt2_5Day"] >= 5].copy()
    
    # Group by ISO3, COUNTRY, ADM_NAME and collect triggered years as sorted list
    grouped = triggered_df.groupby(["ISO3", "COUNTRY", "ADM_NAME"]).agg(
        triggered_years=("crop_year", lambda y: sorted(list(y.unique()))),
        total_triggered_years=("crop_year", "nunique"),
        total_flood_days=("Flood_Days_Opt2_5Day", "sum"),
        max_streak=("Max_Flood_Streak_Opt2_5Day", "max")
    ).reset_index()

    # Save to CSV and Markdown
    out_csv = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output\Triggered_Districts_5Day_Kenya_Malawi_Nigeria.csv")
    grouped.to_csv(out_csv, index=False)
    
    print(f"Successfully extracted triggered districts summary to {out_csv}")
    print(f"Total triggered districts found: Kenya={len(grouped[grouped['ISO3']=='KEN'])}, Malawi={len(grouped[grouped['ISO3']=='MWI'])}, Nigeria={len(grouped[grouped['ISO3']=='NGA'])}")

if __name__ == "__main__":
    main()
