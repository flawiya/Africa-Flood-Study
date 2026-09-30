import os, pandas as pd, numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm

BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_DIR = os.path.join(BASE_PATH, "output", "agricultural")

def normalize(name): return str(name).replace("-", " ").replace("_", " ").strip().upper()
def find_dist_col(df):
    possible = ['DISTRICT_NAME', 'ADM_NAME', 'DIST', 'DISTRICT']
    cols = [c.upper() for c in df.columns]
    for p in possible:
        if p in cols: return df.columns[cols.index(p)]
    raise KeyError(f"Could not find District column in: {df.columns.tolist()}")

df_sm = pd.read_csv(os.path.join(DATA_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv"))
df_ro = pd.read_csv(os.path.join(DATA_DIR, "Zambia_ERA5_Daily_Runoff_2000_2025.csv"))
df_rf = pd.read_csv(os.path.join(DATA_DIR, "CHIRPS_Standardized_Master.csv"))
df_swi = pd.read_csv(os.path.join(DATA_DIR, "Africa_and_Zambia_SWI_Maize_Merged_Long.csv"))
df_swi = df_swi[(df_swi['COUNTRY'] == 'Zambia') & (df_swi['swi_band'] == 'swi_010')].copy()

for d in [df_sm, df_ro, df_rf]:
    date_col = 'date' if 'date' in d.columns else 'Date'
    d["Date"] = pd.to_datetime(d[date_col])
    d["Dist"] = d[find_dist_col(d)].apply(normalize)
df_swi["Date"] = pd.to_datetime(df_swi['date' if 'date' in df_swi.columns else 'Date'])
df_swi["Dist"] = df_swi[find_dist_col(df_swi)].apply(normalize)

df_sm["vwc_0_28"] = (df_sm["soil_0_7cm"] * 0.25) + (df_sm["soil_7_28cm"] * 0.75)
df_sm["SSI_7d"] = df_sm.groupby("Dist")["vwc_0_28"].transform(lambda x: norm.ppf(((x.rolling(7).mean().rank(pct=True)-0.44)/1.12).clip(0.001,0.999)))
df_ro["RO_7d"] = df_ro.groupby("Dist")["total_runoff_mm"].transform(lambda x: x.rolling(7, min_periods=1).sum())
df_rf["Rain_7d"] = df_rf.groupby("Dist")["precipitation"].transform(lambda x: x.rolling(7, min_periods=1).sum())

df = df_swi[["Dist", "Date", "swi_value"]].rename(columns={"swi_value": "swi_val"})
df = df.merge(df_sm[["Dist", "Date", "SSI_7d"]], on=["Dist", "Date"]).merge(df_ro[["Dist", "Date", "RO_7d"]], on=["Dist", "Date"]).merge(df_rf[["Dist", "Date", "Rain_7d"]], on=["Dist", "Date"])
df = df.drop_duplicates(subset=["Dist", "Date"]).reset_index(drop=True)
df = df[df['Dist'] == 'CHIBOMBO']

def apply_insurance_latch(sub):
    sat_limit = sub['swi_val'].quantile(0.99) * 0.95
    status = np.zeros(len(sub)); active = False
    for i in range(len(sub)):
        if not active and sub.iloc[i]['Rain_7d'] > 100 and sub.iloc[i]['RO_7d'] > 20 and sub.iloc[i]['SSI_7d'] > 1.5 and i > 14:
            active = True
        elif active and sub.iloc[i]['swi_val'] < sat_limit:
            active = False
        status[i] = 1 if active else 0
    return pd.Series(status, index=sub.index)

df["Trigger"] = apply_insurance_latch(df)
print("Total Trigger Days (CHIBOMBO):", df["Trigger"].sum())
