"""Debug: Compare SRI_7d values vs raw runoff to understand the visual discrepancy."""
import os, pandas as pd, numpy as np
from scipy.stats import norm

BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE_PATH, "output", "agricultural")

def compute_universal_index(series, window):
    rolling_val = series.rolling(window).mean()
    ranks = rolling_val.rank(method="average")
    n = len(series.dropna())
    if n == 0: return series
    pp = (ranks - 0.44) / (n + 0.12)
    return norm.ppf(pp.clip(0.001, 0.999))

df_ro = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Runoff_2000_2025.csv"))
df_ro["Date"] = pd.to_datetime(df_ro["Date"] if "Date" in df_ro.columns else df_ro["date"])
df_ro["Dist"] = df_ro["District_Name" if "District_Name" in df_ro.columns else "Dist"].str.upper().str.strip()

df_ro["SRI_7d"] = df_ro.groupby("Dist")["total_runoff_mm"].transform(lambda x: compute_universal_index(x, 7))

for name in ["LUSAKA", "CHONGWE"]:
    d = df_ro[(df_ro["Dist"] == name) & (df_ro["Date"] >= "2007-11-01") & (df_ro["Date"] <= "2008-05-31")]
    print(f"\n{'='*70}")
    print(f"  {name} — Nov 2007 to May 2008")
    print(f"{'='*70}")
    print(f"  Raw runoff (total_runoff_mm) — min: {d['total_runoff_mm'].min():.4f}, max: {d['total_runoff_mm'].max():.4f}, mean: {d['total_runoff_mm'].mean():.4f}")
    print(f"  SRI_7d                       — min: {d['SRI_7d'].min():.4f}, max: {d['SRI_7d'].max():.4f}, mean: {d['SRI_7d'].mean():.4f}")
    print(f"\n  Days with SRI_7d > 1.5: {(d['SRI_7d'] > 1.5).sum()}")
    print(f"  Days with SRI_7d > 1.0: {(d['SRI_7d'] > 1.0).sum()}")
    print(f"\n  Top 10 SRI days:")
    top = d.nlargest(10, "SRI_7d")[["Date", "total_runoff_mm", "SRI_7d"]]
    print(top.to_string(index=False))
    print(f"\n  Top 10 Raw Runoff days:")
    top_raw = d.nlargest(10, "total_runoff_mm")[["Date", "total_runoff_mm", "SRI_7d"]]
    print(top_raw.to_string(index=False))
