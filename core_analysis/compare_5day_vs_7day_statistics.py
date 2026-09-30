"""
compare_5day_vs_7day_statistics.py
==================================
Produces a single CSV comparing Option 2 (5-Day) vs Option 2 (7-Day) flood statistics
at country level, with a Pan-Africa totals row.

Output:
  - output/agricultural/outputs/Option2_5Day_vs_7Day_Comparison.csv
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

CSV_5DAY = os.path.join(OUT_DIR, "Africa_Maize_Flood_Annual_Option2_5Day.csv")
CSV_7DAY = os.path.join(OUT_DIR, "Africa_Maize_Flood_Annual_Option2_7Day.csv")


def main():
    df_5 = pd.read_csv(CSV_5DAY)
    df_7 = pd.read_csv(CSV_7DAY)

    # Country-level aggregation — 5-Day
    c5 = df_5.groupby(["ISO3", "COUNTRY"]).agg(
        Total_Districts=("ADM_NAME", "nunique"),
        Flood_Days_5Day=("flood_days_5plus", "sum"),
        Flood_Events_5Day=("num_flood_events", "sum")
    ).reset_index()

    trig5 = df_5[df_5["flood_days_5plus"] > 0].groupby("ISO3")["ADM_NAME"].nunique().reset_index()
    trig5.rename(columns={"ADM_NAME": "Triggered_Districts_5Day"}, inplace=True)
    c5 = c5.merge(trig5, on="ISO3", how="left").fillna({"Triggered_Districts_5Day": 0})
    c5["Triggered_Districts_5Day"] = c5["Triggered_Districts_5Day"].astype(int)

    # Country-level aggregation — 7-Day
    c7 = df_7.groupby("ISO3").agg(
        Flood_Days_7Day=("flood_days_7plus", "sum"),
        Flood_Events_7Day=("num_flood_events", "sum")
    ).reset_index()

    trig7 = df_7[df_7["flood_days_7plus"] > 0].groupby("ISO3")["ADM_NAME"].nunique().reset_index()
    trig7.rename(columns={"ADM_NAME": "Triggered_Districts_7Day"}, inplace=True)
    c7 = c7.merge(trig7, on="ISO3", how="left").fillna({"Triggered_Districts_7Day": 0})
    c7["Triggered_Districts_7Day"] = c7["Triggered_Districts_7Day"].astype(int)

    # Merge
    comp = c5.merge(c7, on="ISO3", how="left").fillna(0)

    # Increase columns (5-Day over 7-Day)
    comp["Days_Increase"] = (comp["Flood_Days_5Day"] - comp["Flood_Days_7Day"]).astype(int)
    comp["Days_Increase_Pct"] = np.where(
        comp["Flood_Days_7Day"] > 0,
        ((comp["Days_Increase"] / comp["Flood_Days_7Day"]) * 100).round(2),
        np.where(comp["Flood_Days_5Day"] > 0, 100.0, 0.0)
    )
    comp["Events_Increase"] = (comp["Flood_Events_5Day"] - comp["Flood_Events_7Day"]).astype(int)
    comp["Events_Increase_Pct"] = np.where(
        comp["Flood_Events_7Day"] > 0,
        ((comp["Events_Increase"] / comp["Flood_Events_7Day"]) * 100).round(2),
        np.where(comp["Flood_Events_5Day"] > 0, 100.0, 0.0)
    )
    comp["Extra_Flash_Flood_Districts"] = (comp["Triggered_Districts_5Day"] - comp["Triggered_Districts_7Day"]).astype(int)

    comp = comp.sort_values("Flood_Days_5Day", ascending=False).reset_index(drop=True)

    # Cast integer columns
    for col in ["Flood_Days_5Day", "Flood_Days_7Day", "Flood_Events_5Day", "Flood_Events_7Day",
                "Triggered_Districts_5Day", "Triggered_Districts_7Day"]:
        comp[col] = comp[col].astype(int)

    # Add Pan-Africa totals row
    totals = {
        "ISO3": "ALL",
        "COUNTRY": "PAN-AFRICA TOTAL",
        "Total_Districts": int(comp["Total_Districts"].sum()),
        "Flood_Days_5Day": int(comp["Flood_Days_5Day"].sum()),
        "Flood_Events_5Day": int(comp["Flood_Events_5Day"].sum()),
        "Triggered_Districts_5Day": int(comp["Triggered_Districts_5Day"].sum()),
        "Flood_Days_7Day": int(comp["Flood_Days_7Day"].sum()),
        "Flood_Events_7Day": int(comp["Flood_Events_7Day"].sum()),
        "Triggered_Districts_7Day": int(comp["Triggered_Districts_7Day"].sum()),
        "Days_Increase": int(comp["Days_Increase"].sum()),
        "Days_Increase_Pct": round((comp["Days_Increase"].sum() / comp["Flood_Days_7Day"].sum()) * 100, 2) if comp["Flood_Days_7Day"].sum() > 0 else 0.0,
        "Events_Increase": int(comp["Events_Increase"].sum()),
        "Events_Increase_Pct": round((comp["Events_Increase"].sum() / comp["Flood_Events_7Day"].sum()) * 100, 2) if comp["Flood_Events_7Day"].sum() > 0 else 0.0,
        "Extra_Flash_Flood_Districts": int(comp["Extra_Flash_Flood_Districts"].sum()),
    }
    comp = pd.concat([comp, pd.DataFrame([totals])], ignore_index=True)

    # Select final columns
    out_cols = [
        "COUNTRY", "ISO3", "Total_Districts",
        "Flood_Days_5Day", "Flood_Days_7Day", "Days_Increase", "Days_Increase_Pct",
        "Flood_Events_5Day", "Flood_Events_7Day", "Events_Increase", "Events_Increase_Pct",
        "Triggered_Districts_5Day", "Triggered_Districts_7Day", "Extra_Flash_Flood_Districts"
    ]

    out_path = os.path.join(OUT_DIR, "Option2_5Day_vs_7Day_Comparison.csv")
    comp[out_cols].to_csv(out_path, index=False)
    print(f"[OK] Saved Country Comparison CSV: {out_path}")

    # District-level aggregation — 5-Day vs 7-Day with gadm_id
    d5 = df_5.groupby(["ISO3", "COUNTRY", "ADM_NAME", "gadm_id"]).agg(
        Flood_Days_5Day=("flood_days_5plus", "sum"),
        Flood_Events_5Day=("num_flood_events", "sum")
    ).reset_index()

    d7 = df_7.groupby(["ISO3", "COUNTRY", "ADM_NAME", "gadm_id"]).agg(
        Flood_Days_7Day=("flood_days_7plus", "sum"),
        Flood_Events_7Day=("num_flood_events", "sum")
    ).reset_index()

    dist_comp = d5.merge(d7, on=["ISO3", "COUNTRY", "ADM_NAME", "gadm_id"], how="outer").fillna(0)
    
    for col in ["Flood_Days_5Day", "Flood_Days_7Day", "Flood_Events_5Day", "Flood_Events_7Day"]:
        dist_comp[col] = dist_comp[col].astype(int)

    dist_comp["Days_Increase"] = dist_comp["Flood_Days_5Day"] - dist_comp["Flood_Days_7Day"]
    dist_comp["Days_Increase_Pct"] = np.where(
        dist_comp["Flood_Days_7Day"] > 0,
        ((dist_comp["Days_Increase"] / dist_comp["Flood_Days_7Day"]) * 100).round(2),
        np.where(dist_comp["Flood_Days_5Day"] > 0, 100.0, 0.0)
    )
    dist_comp["Events_Increase"] = dist_comp["Flood_Events_5Day"] - dist_comp["Flood_Events_7Day"]
    dist_comp["Events_Increase_Pct"] = np.where(
        dist_comp["Flood_Events_7Day"] > 0,
        ((dist_comp["Events_Increase"] / dist_comp["Flood_Events_7Day"]) * 100).round(2),
        np.where(dist_comp["Flood_Events_5Day"] > 0, 100.0, 0.0)
    )

    dist_cols = [
        "ISO3", "COUNTRY", "ADM_NAME", "gadm_id",
        "Flood_Days_5Day", "Flood_Days_7Day", "Days_Increase", "Days_Increase_Pct",
        "Flood_Events_5Day", "Flood_Events_7Day", "Events_Increase", "Events_Increase_Pct"
    ]
    dist_out_path = os.path.join(OUT_DIR, "Option2_5Day_vs_7Day_District_Comparison.csv")
    dist_comp[dist_cols].to_csv(dist_out_path, index=False)
    print(f"[OK] Saved District Comparison CSV (with gadm_id): {dist_out_path}")


if __name__ == "__main__":
    main()
