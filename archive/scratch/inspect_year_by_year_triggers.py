"""
inspect_year_by_year_triggers.py
================================
Inspects triggered districts for Kenya, Malawi, and Nigeria for every year 2008-2024
under Option 2 (5-day and 7-day continuous streak rules).
"""

import os
import pandas as pd

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")

def main():
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year

    plant_doy = pd.to_numeric(df["planting"], errors='coerce')
    harvest_doy = pd.to_numeric(df["harvest"], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1

    df = df[~df["crop_year"].isin([2007, 2025])]
    df = df[df["COUNTRY"] != "Morocco"]
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])

    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)

    # 5-day continuous
    df["block5"] = (df["flag_opt2"] != df.groupby(["COUNTRY", "ADM_NAME"])["flag_opt2"].shift()).cumsum()
    len5 = df.groupby(["COUNTRY", "ADM_NAME", "block5"])["flag_opt2"].transform(lambda s: s.sum() if s.iloc[0] else 0)
    df["valid5"] = df["flag_opt2"] & (len5 >= 5)

    # 7-day continuous
    df["block7"] = (df["flag_opt2"] != df.groupby(["COUNTRY", "ADM_NAME"])["flag_opt2"].shift()).cumsum()
    len7 = df.groupby(["COUNTRY", "ADM_NAME", "block7"])["flag_opt2"].transform(lambda s: s.sum() if s.iloc[0] else 0)
    df["valid7"] = df["flag_opt2"] & (len7 >= 7)

    summary5 = df.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"])["valid5"].sum().reset_index()
    summary7 = df.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"])["valid7"].sum().reset_index()

    merged = summary5.merge(summary7, on=["ISO3", "COUNTRY", "ADM_NAME", "crop_year"])
    merged = merged[merged["ISO3"].isin(["KEN", "MWI", "NGA"])].copy()

    print("\n================ YEAR BY YEAR TRIGGER SUMMARY ================")
    for iso3, country_name in [("KEN", "Kenya"), ("MWI", "Malawi"), ("NGA", "Nigeria")]:
        c_df = merged[merged["ISO3"] == iso3]
        print(f"\n---------------- {country_name} ({iso3}) ----------------")
        for yr in sorted(c_df["crop_year"].unique()):
            sub = c_df[c_df["crop_year"] == yr]
            t5 = sub[sub["valid5"] >= 5]["ADM_NAME"].tolist()
            t7 = sub[sub["valid7"] >= 7]["ADM_NAME"].tolist()
            print(f"Year {yr}: 5-Day Triggers={len(t5)}, 7-Day Triggers={len(t7)}")
            if len(t5) > 0:
                print(f"   Top 5-Day districts: {t5[:6]}")

if __name__ == "__main__":
    main()
