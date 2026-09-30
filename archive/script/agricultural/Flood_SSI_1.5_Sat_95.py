import os, sys, traceback
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm

# CONFIG
BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE_PATH, "output", "agricultural")
VIZ_DIR = os.path.join(OUT_DIR, "visualizations")
os.makedirs(VIZ_DIR, exist_ok=True)

PLOT_TARGETS = {"MONZE": 2007, "KAPIRI MPOSHI": 2007, "CHIBOMBO": 2011}

def calculate_swi(series, T=10):
    swi = np.zeros(len(series)); gain = 1.0; swi[0] = series.iloc[0]
    for t in range(1, len(series)):
        gain = gain / (gain + np.exp(-1/T))
        swi[t] = swi[t-1] + gain * (series.iloc[t] - swi[t-1])
    return swi

def compute_universal_index(series, window):
    rolling_val = series.rolling(window).mean()
    ranks = rolling_val.rank(method="average")
    n = len(series.dropna())
    if n == 0: return series
    pp = (ranks - 0.44) / (n + 0.12)
    return norm.ppf(pp.clip(0.001, 0.999))

def apply_latch(df):
    status = np.zeros(len(df)); active = False
    for i in range(len(df)):
        # FORMULA 3: SSI >= 1.5 
        if not active:
            if df.iloc[i]['SSI_14d'] >= 1.5 and i > 14:
                active = True
        else:
            if df.iloc[i]['sat_index'] < 95: active = False
        status[i] = 1 if active else 0
    return status

try:
    df_sm = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv"))
    df_ro = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Runoff_2000_2025.csv"))
    df_rf = pd.read_csv(os.path.join(OUT_DIR, "CHIRPS_Standardized_Master.csv"))
    for d in [df_sm, df_ro, df_rf]:
        d["Date"] = pd.to_datetime(d["Date"] if "Date" in d.columns else d["date"])
        d["Dist"] = d["District_Name" if "District_Name" in d.columns else "Dist"].str.upper().str.strip()
    df_sm = df_sm.sort_values(["Dist", "Date"]).reset_index(drop=True)
    df_sm["vwc_root"] = (df_sm["soil_0_7cm"] * 0.25) + (df_sm["soil_7_28cm"] * 0.75)
    df_sm["swi_raw"] = df_sm.groupby("Dist")["vwc_root"].transform(lambda x: calculate_swi(x, 10))
    df_sm["sat_index"] = df_sm.groupby("Dist")["swi_raw"].transform(lambda x: (x / x.quantile(0.99)) * 100)
    df_sm["SSI_14d"] = df_sm.groupby("Dist")["vwc_root"].transform(lambda x: compute_universal_index(x, 14))
    df_ro["SRI_7d"]  = df_ro.groupby("Dist")["total_runoff_mm"].transform(lambda x: compute_universal_index(x, 7))
    df_rf["SPI_7d"]  = df_rf.groupby("Dist")["precipitation"].transform(lambda x: compute_universal_index(x, 7))
    df = df_sm.merge(df_ro[["Dist", "Date", "SRI_7d"]], on=["Dist", "Date"]).merge(df_rf[["Dist", "Date", "SPI_7d"]], on=["Dist", "Date"])
    df["Trigger"] = df.groupby("Dist").apply(lambda x: pd.Series(apply_latch(x), index=x.index)).reset_index(level=0, drop=True)

    n = len(PLOT_TARGETS)
    fig = make_subplots(rows=n*5, cols=1, vertical_spacing=0.02, shared_xaxes=False)
    for idx, (name, yr) in enumerate(PLOT_TARGETS.items()):
        d = df[(df["Dist"] == name) & (df["Date"] >= f"{yr}-11-01") & (df["Date"] <= f"{yr+1}-05-31")]
        rb = idx*5
        fig.add_trace(go.Bar(x=d["Date"], y=d["SPI_7d"], marker_color="royalblue"), row=rb+1, col=1)
        fig.add_trace(go.Bar(x=d["Date"], y=d["SRI_7d"], marker_color="gold"), row=rb+2, col=1)
        fig.add_trace(go.Scatter(x=d["Date"], y=d["SSI_14d"], line=dict(color="green")), row=rb+3, col=1)
        fig.add_hline(y=1.5, line_dash="dash", line_color="red", row=rb+3, col=1)
        fig.add_trace(go.Scatter(x=d["Date"], y=d["sat_index"], line=dict(color="purple")), row=rb+4, col=1)
        fig.add_hline(y=95, line_dash="dash", line_color="red", row=rb+4, col=1)
        fig.add_trace(go.Bar(x=d["Date"], y=d["Trigger"], marker_color="red"), row=rb+5, col=1)
        titles = [f"<b>{name}</b>: SPI-7d (7-day Rainfall Anomaly)", "SRI-7d (7-day Cumulative Runoff Anomaly)", "SSI-14d (14-day Rolling Mean Soil Anomaly)", "Saturation Index (Root-Zone Fullness %)", "<b>PAYOUT STATUS</b>: SSI >= 1.5 | Latch @ 95%"]
        for i, t in enumerate(titles):
            ax = "" if rb+i+1 == 1 else str(rb+i+1)
            fig.layout.annotations += (go.layout.Annotation(text=t, x=0, y=1.05, xref=f"x{ax} domain", yref=f"y{ax} domain", showarrow=False, xanchor="left"),)
    fig.update_layout(height=n*1300, width=1200, template="plotly_white", showlegend=False)
    fig.write_html(os.path.join(VIZ_DIR, "Flood_SSI_1.5_Sat_95.html"))
except Exception as e: traceback.print_exc()