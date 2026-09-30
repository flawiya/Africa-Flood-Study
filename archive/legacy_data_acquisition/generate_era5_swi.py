import os
import pandas as pd
import numpy as np

# Configuration
BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE_PATH, "output", "agricultural")
INPUT_FILE = os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv")
OUTPUT_FILE = os.path.join(OUT_DIR, "Zambia_ERA5_Computed_SWI_T10_2000_2025.csv")
T_VALUE = 10.0

print("Loading ERA5 Surface Soil Moisture...")
df = pd.read_csv(INPUT_FILE)
df.columns = [c.replace('date', 'Date') for c in df.columns]
df["Date"] = pd.to_datetime(df["Date"])
df["Dist"] = df["District_Name"].str.upper().str.strip()

computed_frames = []

print("Computing T=10 Exponential Filter for each district...")
for dist in df["Dist"].unique():
    d_sm = df[df["Dist"] == dist].sort_values("Date").reset_index(drop=True)
    
    # Scale to 0-100 index (Surface Soil Moisture)
    min_val = d_sm["soil_0_7cm"].min()
    max_val = d_sm["soil_0_7cm"].max()
    d_sm["SSM_Index"] = ((d_sm["soil_0_7cm"] - min_val) / (max_val - min_val)) * 100
    
    # Apply Wagner Exponential Filter
    swi = np.zeros(len(d_sm))
    k = np.zeros(len(d_sm))
    
    swi[0] = d_sm["SSM_Index"].iloc[0]
    k[0] = 1.0
    
    for i in range(1, len(d_sm)):
        dt = (d_sm["Date"].iloc[i] - d_sm["Date"].iloc[i-1]).days
        if dt == 0: dt = 1
        
        k[i] = k[i-1] / (k[i-1] + np.exp(-dt / T_VALUE))
        swi[i] = swi[i-1] + k[i] * (d_sm["SSM_Index"].iloc[i] - swi[i-1])
        
    d_sm["swi_value"] = swi
    computed_frames.append(d_sm[["Dist", "Date", "swi_value"]])

print("Compiling final dataset...")
final_df = pd.concat(computed_frames, ignore_index=True)
final_df = final_df.sort_values(["Dist", "Date"]).reset_index(drop=True)
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"Success! 25-Year SWI dataset saved to {OUTPUT_FILE}")
