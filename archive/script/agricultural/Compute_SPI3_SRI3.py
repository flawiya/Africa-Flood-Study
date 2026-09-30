import os, pandas as pd, numpy as np
from datetime import datetime
from scipy.stats import norm

# =============================================================================
# 1. CONFIGURATION
# =============================================================================
BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_DIR = os.path.join(BASE_PATH, "output", "agricultural")
OUT_DIR  = os.path.join(DATA_DIR, "indices")
os.makedirs(OUT_DIR, exist_ok=True)

# =============================================================================
# 2. CORE MATH FUNCTIONS
# =============================================================================
def compute_gringorten(series):
    """Computes Standardized Index using Gringorten plotting position."""
    ranks = series.rank(method="average")
    n = len(series.dropna())
    if n == 0: return series
    return norm.ppf(((ranks - 0.44) / (n + 0.12)).clip(0.001, 0.999))

def normalize(name): 
    return str(name).strip().upper()

# =============================================================================
# 3. MAIN PIPELINE
# =============================================================================
def main():
    print("Step 1: Loading Runoff and Precipitation data streams...")
    df_ro = pd.read_csv(os.path.join(DATA_DIR, "Zambia_ERA5_Daily_Runoff_2000_2025.csv"))
    df_rf = pd.read_csv(os.path.join(DATA_DIR, "CHIRPS_Standardized_Master.csv"))

    # Normalize Dates and District Names
    for d in [df_ro, df_rf]:
        d.columns = [c.replace('date', 'Date') for c in d.columns]
        d["Date"] = pd.to_datetime(d["Date"])
        dist_col = 'District_Name' if 'District_Name' in d.columns else 'ADM_NAME'
        d["Dist"] = d[dist_col].apply(normalize)

    print("Step 2: Merging data streams...")
    # Keep only the relevant columns to save memory
    df_ro = df_ro[["Dist", "Date", "total_runoff_mm"]]
    df_rf = df_rf[["Dist", "Date", "precipitation"]]
    
    df = pd.merge(df_ro, df_rf, on=["Dist", "Date"], how="inner").sort_values(["Dist", "Date"])

    print("Step 3: Computing 90-day (3-Month) Rolling Sums...")
    # 90-day sums for 3-month scales
    df["Runoff_90d"] = df.groupby("Dist")["total_runoff_mm"].transform(lambda x: x.rolling(90, min_periods=30).sum())
    df["Rain_90d"]   = df.groupby("Dist")["precipitation"].transform(lambda x: x.rolling(90, min_periods=30).sum())

    print("Step 4: Standardizing to SRI-3 and SPI-3 using Gringorten...")
    # To properly compute SPI/SRI, we should standardize against the same day-of-year across historical records
    # to eliminate seasonality. 
    df['DOY'] = df['Date'].dt.dayofyear
    
    df["SRI_3"] = df.groupby(["Dist", "DOY"])["Runoff_90d"].transform(compute_gringorten)
    df["SPI_3"] = df.groupby(["Dist", "DOY"])["Rain_90d"].transform(compute_gringorten)
    
    # Drop DOY helper column
    df = df.drop(columns=['DOY'])

    print("Step 5: Filtering to Crop Calendar (Nov 1 - May 31)...")
    # A generic way to filter to the crop calendar
    df['Month'] = df['Date'].dt.month
    crop_calendar_mask = (df['Month'] >= 11) | (df['Month'] <= 5)
    df_crop = df[crop_calendar_mask].copy()

    # Save outputs
    out_file = os.path.join(OUT_DIR, "Zambia_SPI3_SRI3_CropCalendar_2000_2025.csv")
    df_crop.to_csv(out_file, index=False)
    print(f"Success! Output saved to: {out_file}")

if __name__ == "__main__":
    main()
