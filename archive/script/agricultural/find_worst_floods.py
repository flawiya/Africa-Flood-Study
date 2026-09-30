import os
import pandas as pd

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")

def main():
    print("Loading data...")
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year
    
    plant_doy = pd.to_numeric(df["planting"], errors='coerce')
    harvest_doy = pd.to_numeric(df["harvest"], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1
    
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    df = df[~df["crop_year"].isin([2007, 2025])]
    
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)
    
    df["block"] = (df["flag_opt2"] != df.groupby(["COUNTRY", "ADM_NAME"])["flag_opt2"].shift()).cumsum()
    block_len = df.groupby(["COUNTRY", "ADM_NAME", "block"])["flag_opt2"].transform(lambda s: s.sum() if s.iloc[0] else 0)
    
    df["valid_streak_day"] = df["flag_opt2"] & (block_len >= 7)
    
    summary = df.groupby(["COUNTRY", "ADM_NAME", "crop_year"]).agg(
        flood_days=("valid_streak_day", "sum")
    ).reset_index()
    
    countries_to_check = ['Morocco', 'Ghana', 'Ethiopia', 'Uganda', 'Mozambique']
    print("\n--- PHASE 2: WORST EVENT PER COUNTRY ---")
    for c in countries_to_check:
        s = summary[(summary['COUNTRY'] == c) & (summary['flood_days'] >= 7)].sort_values('flood_days', ascending=False)
        if not s.empty:
            top = s.iloc[0]
            print(f"{c} | District: {top['ADM_NAME']} | Year: {top['crop_year']} | Days: {top['flood_days']}")
        else:
            print(f"{c} | No severe events found >= 7 days.")
            
    # Phase 3 logic
    print("\n--- PHASE 3: TOP 3 EVENTS FOR 5 COUNTRIES (N/S/E/W/C) ---")
    countries_phase3 = ['Sudan', 'Mozambique', 'Kenya', 'Nigeria', 'Democratic Republic of the Congo']
    for c in countries_phase3:
        s = summary[(summary['COUNTRY'] == c) & (summary['flood_days'] >= 7)].sort_values('flood_days', ascending=False)
        print(f"\n[{c}]")
        if not s.empty:
            for idx, row in s.head(3).iterrows():
                print(f"  Year: {row['crop_year']} | District: {row['ADM_NAME']} | Days: {row['flood_days']}")
        else:
            print(f"  No severe events found >= 7 days.")

if __name__ == "__main__":
    main()
