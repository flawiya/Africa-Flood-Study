import os, pandas as pd, numpy as np
import plotly.graph_objects as go
from scipy.stats import pearsonr

# CONFIG
BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_DIR = os.path.join(BASE_PATH, "output", "agricultural")

ERA5_SM_CSV = os.path.join(DATA_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv")
COP_SWI_CSV = os.path.join(DATA_DIR, "Africa_and_Zambia_SWI_Maize_Merged_Long.csv")

def calculate_swi(series, T=10):
    swi = np.zeros(len(series)); gain = 1.0; swi[0] = series.iloc[0]
    for t in range(1, len(series)):
        gain = gain / (gain + np.exp(-1/T))
        swi[t] = swi[t-1] + gain * (series.iloc[t] - swi[t-1])
    return swi

try:
    print("Loading datasets for calibration...")
    df_sm = pd.read_csv(ERA5_SM_CSV)
    df_cop = pd.read_csv(COP_SWI_CSV)
    
    # Filter Copernicus to Zambia T=10 (swi_010)
    df_cop = df_cop[(df_cop['COUNTRY'] == 'Zambia') & (df_cop['swi_band'] == 'swi_010')].copy()
    
    # Standardize names and dates
    for d, date_col, dist_col in [(df_sm, 'Date', 'District_Name'), (df_cop, 'date', 'ADM_NAME')]:
        d["Date"] = pd.to_datetime(d[date_col])
        d["Dist"] = d[dist_col].str.upper().str.strip()

    # Calculate SWI from ERA5
    df_sm = df_sm.sort_values(["Dist", "Date"])
    df_sm["vwc_0_28"] = (df_sm["soil_0_7cm"] * 0.25) + (df_sm["soil_7_28cm"] * 0.75)
    df_sm["era5_swi"] = df_sm.groupby("Dist")["vwc_0_28"].transform(lambda x: calculate_swi(x, 10))

    # Merge for 2007-2024 overlap
    df = df_sm.merge(df_cop[["Dist", "Date", "swi_value"]], on=["Dist", "Date"], how="inner")
    
    print("\n" + "="*60)
    print(f"{'DISTRICT':<15} | {'CORRELATION (R)':<15} | {'RMSE (m3/m3)':<15}")
    print("-" * 60)

    for dist in ["MONZE", "KAPIRI MPOSHI", "CHIBOMBO"]:
        d = df[df["Dist"] == dist].dropna()
        
        # Pure Numpy/Scipy Math (No sklearn needed)
        r_val, _ = pearsonr(d["era5_swi"], d["swi_value"])
        rmse_val = np.sqrt(np.mean((d["era5_swi"] - (d["swi_value"]/200))**2)) # Scaled to VWC

        print(f"{dist:<15} | {r_val:<15.4f} | {rmse_val:<15.4f}")
    print("="*60)

except Exception as e: print(f"Error: {e}")