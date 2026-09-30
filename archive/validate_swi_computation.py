import os
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

OUT_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural"

print("Loading data...")
df_sm = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv"))
df_sm.columns = [c.replace('date', 'Date') for c in df_sm.columns]
df_sm["Date"] = pd.to_datetime(df_sm["Date"])
df_sm["Dist"] = df_sm["District_Name"].str.upper().str.strip()

df_cop = pd.read_csv(os.path.join(OUT_DIR, "Africa_and_Zambia_SWI_Maize_Merged_Long.csv"))
df_cop = df_cop[(df_cop['COUNTRY'] == 'Zambia') & (df_cop['swi_band'] == 'swi_010')].copy()
df_cop['Date'] = pd.to_datetime(df_cop['date'])
df_cop['Dist'] = df_cop['ADM_NAME'].str.upper().str.strip()

# Test for CHIBOMBO
dist = "CHIBOMBO"
d_sm = df_sm[df_sm["Dist"] == dist].sort_values("Date").reset_index(drop=True)
d_cop = df_cop[df_cop["Dist"] == dist].sort_values("Date").reset_index(drop=True)

# 1. Scale ERA5 soil_0_7cm to 0-100 Index
min_val = d_sm["soil_0_7cm"].min()
max_val = d_sm["soil_0_7cm"].max()
d_sm["SSM_Index"] = ((d_sm["soil_0_7cm"] - min_val) / (max_val - min_val)) * 100

# 2. Apply Wagner Exponential Filter (T=10)
T = 10.0
swi = np.zeros(len(d_sm))
k = np.zeros(len(d_sm))

swi[0] = d_sm["SSM_Index"].iloc[0]
k[0] = 1.0

for i in range(1, len(d_sm)):
    # Assuming daily timestep, dt = 1
    dt = (d_sm["Date"].iloc[i] - d_sm["Date"].iloc[i-1]).days
    if dt == 0: dt = 1
    
    k[i] = k[i-1] / (k[i-1] + np.exp(-dt / T))
    swi[i] = swi[i-1] + k[i] * (d_sm["SSM_Index"].iloc[i] - swi[i-1])

d_sm["Computed_SWI"] = swi

# Merge with Copernicus and calculate correlation
merged = d_sm[["Date", "Computed_SWI", "SSM_Index", "soil_0_7cm"]].merge(d_cop[["Date", "swi_value"]], on="Date", how="inner")
merged = merged.dropna()

corr, _ = pearsonr(merged["Computed_SWI"], merged["swi_value"])
print(f"[{dist}] Pearson Correlation between Computed SWI (T=10) and Copernicus SWI: {corr:.4f}")
print("Sample comparison:")
print(merged[["Date", "swi_value", "Computed_SWI", "soil_0_7cm"]].iloc[500:510])

# Also check correlation using the direct VWC without 0-100 scaling (since the filter is linear, correlation should be identical, but scale differs)
