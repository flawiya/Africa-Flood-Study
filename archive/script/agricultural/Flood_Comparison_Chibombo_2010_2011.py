import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm

# =============================================================================
# 1. CONFIGURATION
# =============================================================================
BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE_PATH, "output", "agricultural")
VIZ_DIR = os.path.join(OUT_DIR, "visualizations")
os.makedirs(VIZ_DIR, exist_ok=True)

# THRESHOLDS
RUNOFF_LIMIT = 10.0
SSI_LIMIT    = 1.5
RAIN_ONSET   = 100.0
SAT_PERCENT  = 0.35
T_VALUE      = 10

TARGET_DIST = "CHIBOMBO"
TARGET_YEAR = 2010 # Season: Oct 2010 - May 2011

# =============================================================================
# 2. SCIENCE FUNCTIONS
# =============================================================================
def compute_gringorten(series):
    ranks = series.rank(method="average")
    n = len(series.dropna())
    if n == 0: return series
    return norm.ppf(((ranks - 0.44) / (n + 0.12)).clip(0.001, 0.999))

def axis_id(n): 
    return "" if n == 1 else str(n)

def identify_sci_trigger(df):
    lag_status = np.zeros(len(df))
    sustained_status = np.zeros(len(df))
    in_lag = False
    is_fully_saturated = False
    
    dist_max = df['swi_value'].quantile(0.99)
    sat_threshold = 0.35

    for i in range(len(df)):
        surface_trigger = (df.iloc[i]['Runoff_7d'] >= RUNOFF_LIMIT) and (df.iloc[i]['SSI_7d'] >= SSI_LIMIT)
        saturated = df.iloc[i]['swi_value'] >= sat_threshold
        
        if surface_trigger and not is_fully_saturated:
            in_lag = True
        if in_lag and saturated:
            in_lag = False
            is_fully_saturated = True
        if not saturated:
            is_fully_saturated = False

        lag_status[i] = 1 if in_lag else 0
        sustained_status[i] = 1 if is_fully_saturated else 0
        
    return lag_status, sustained_status

def apply_ins_trigger(df):
    status = np.zeros(len(df))
    active = False
    sat_95 = 0.35

    for i in range(len(df)):
        ro_spike   = df.iloc[i]['Runoff_7d'] >= RUNOFF_LIMIT
        rain_spike = df.iloc[i]['Rain_7d'] >= RAIN_ONSET
        ssi_high   = df.iloc[i]['SSI_7d'] >= SSI_LIMIT
        saturated  = df.iloc[i]['swi_value'] >= sat_95
        
        if not active:
            # All 4 keys needed to start
            if ro_spike and rain_spike and ssi_high and saturated:
                active = True
        else:
            if not saturated:
                active = False
        
        status[i] = 1 if active else 0
    return status

# =============================================================================
# 3. DATA PROCESSING
# =============================================================================
print("Loading Data...")
df_sm = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv"))
df_ro = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Daily_Runoff_2000_2025.csv"))
df_rf = pd.read_csv(os.path.join(OUT_DIR, "CHIRPS_Standardized_Master.csv"))

df_cop = pd.read_csv(os.path.join(OUT_DIR, "Zambia_ERA5_Computed_SWI_T10_2000_2025.csv"))
df_cop['Date'] = pd.to_datetime(df_cop['Date'])
df_cop['Dist'] = df_cop['Dist'].str.upper().str.strip()

for d in [df_sm, df_ro, df_rf]:
    d.columns = [c.replace('date', 'Date') for c in d.columns]
    d["Date"] = pd.to_datetime(d["Date"])
    d["Dist"] = d["District_Name"].str.upper().str.strip()

print("Standardizing and merging...")
df_sm["vwc_0_28"] = (df_sm["soil_0_7cm"] * 0.25) + (df_sm["soil_7_28cm"] * 0.75)
df_sm["SSI_7d"] = df_sm.groupby("Dist")["vwc_0_28"].transform(lambda x: compute_gringorten(x.rolling(7).mean()))
df_ro["Runoff_7d"] = df_ro.groupby("Dist")["total_runoff_mm"].transform(lambda x: x.rolling(7, min_periods=1).sum())
df_rf["Rain_7d"] = df_rf.groupby("Dist")["precipitation"].transform(lambda x: x.rolling(7, min_periods=1).sum())

df = df_cop[["Dist", "Date", "swi_value"]].merge(df_sm[["Dist", "Date", "SSI_7d"]], on=["Dist", "Date"]).merge(df_ro[["Dist", "Date", "Runoff_7d"]], on=["Dist", "Date"]).merge(df_rf[["Dist", "Date", "Rain_7d"]], on=["Dist", "Date"])

df = df.drop_duplicates(subset=["Dist", "Date"]).reset_index(drop=True)

# Filter for CHIBOMBO
dist_df = df[df["Dist"] == TARGET_DIST].copy()
dist_df = dist_df.sort_values("Date")

# Calculate Triggers before filtering by year so percentiles/history is complete
lag_status, sustained_status = identify_sci_trigger(dist_df)
dist_df["Sci_Lag"] = lag_status
dist_df["Sci_Sustained"] = sustained_status
dist_df["Ins_Trigger"] = apply_ins_trigger(dist_df)

# Add Sustained 7d Trigger
dist_df["Sus7d_Cond"] = ((dist_df["SSI_7d"] >= SSI_LIMIT) & (dist_df["Runoff_7d"] >= RUNOFF_LIMIT)).astype(int)
dist_df["Sus7d_Trigger"] = (dist_df["Sus7d_Cond"].rolling(7).sum() == 7).astype(int)

dist_max = dist_df['swi_value'].quantile(0.99)
sat_threshold = 0.35

# Filter for Oct 2010 - May 2011 season
start_dt = pd.to_datetime(f"{TARGET_YEAR}-10-01")
end_dt = pd.to_datetime(f"{TARGET_YEAR+1}-05-31")
dist_df = dist_df[(dist_df["Date"] >= start_dt) & (dist_df["Date"] <= end_dt)]

# =============================================================================
# 4. VISUALIZATION
# =============================================================================
print("Generating Plot...")
fig = make_subplots(rows=15, cols=1, shared_xaxes=False, vertical_spacing=0.02)

def plot_5_panels(df, rb, trigger_type):
    # 1. RAINFALL
    fig.add_trace(go.Bar(x=df["Date"], y=df["Rain_7d"], name="7d Rain", marker_color="#3b82f6"), row=rb+1, col=1)
    if trigger_type == "INS":
        fig.add_hline(y=RAIN_ONSET, line_dash="dash", line_color="black", row=rb+1, col=1)
        
    # 2. RUNOFF
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Runoff_7d"], name="7d Runoff", line=dict(color="#f59e0b")), row=rb+2, col=1)
    fig.add_hline(y=RUNOFF_LIMIT, line_dash="dash", line_color="orange", row=rb+2, col=1)
    
    # 3. SSI
    fig.add_trace(go.Scatter(x=df["Date"], y=df["SSI_7d"], name="SSI", line=dict(color="#10b981")), row=rb+3, col=1)
    fig.add_hline(y=SSI_LIMIT, line_dash="dot", line_color="green", row=rb+3, col=1)
    
    # 4. SWI
    fig.add_trace(go.Scatter(x=df["Date"], y=df["swi_value"], name="SWI", line=dict(color="#8b5cf6", width=2)), row=rb+4, col=1)
    fig.add_hline(y=sat_threshold, line_dash="dot", line_color="purple", annotation_text="95% Capacity", row=rb+4, col=1)
    
    # 5. TRIGGER
    if trigger_type == "SCI":
        fig.add_trace(go.Bar(x=df["Date"], y=df["Sci_Lag"], name="Filling Phase", marker_color="#fbbf24"), row=rb+5, col=1)
        fig.add_trace(go.Bar(x=df["Date"], y=df["Sci_Sustained"], name="Saturation Phase", marker_color="#dc2626"), row=rb+5, col=1)
    elif trigger_type == "INS":
        fig.add_trace(go.Bar(x=df["Date"], y=df["Ins_Trigger"], name="Insurance Trigger", marker_color="#fbbf24"), row=rb+5, col=1)
    elif trigger_type == "SUS7D":
        fig.add_trace(go.Bar(x=df["Date"], y=df["Sus7d_Trigger"], name="Sustained 7d Trigger", marker_color="#dc2626"), row=rb+5, col=1)
    
    # LABELS
    if trigger_type == "SCI":
        prefix = "SCIENTIFIC TRIGGER"
        trig_desc = "Yellow=Infiltration (SSI>1.5 & Q>20mm) | Red=Total Saturation (SWI>95%)"
    elif trigger_type == "INS":
        prefix = "INSURANCE TRIGGER"
        trig_desc = "Yellow=4-Key Lock (Rain>100, Q>20, SSI>1.5, SWI>95%)"
    else:
        prefix = "SUSTAINED 7D TRIGGER"
        trig_desc = "Red=SSI>1.5 & Q>20mm sustained for 7 consecutive days"
    
    titles = [
        f"<b>{TARGET_DIST} ({TARGET_YEAR}-{TARGET_YEAR+1}) [{prefix}]</b>: Rainfall (7-day cumulative sum)",
        "<b>Runoff</b>: (7-day cumulative sum)",
        "<b>SSI</b>: 0-28cm Integrated 7d rolling avg",
        "<b>Root Persistence</b>: Copernicus SWI (T=10)",
        f"<b>Trigger</b>: {trig_desc}"
    ]
    for i, text in enumerate(titles):
        current_row = rb + i + 1
        ax_num = axis_id(current_row)
        fig.layout.annotations += (
            go.layout.Annotation(
                text=text, x=0, y=1.1, xref=f"x{ax_num} domain", yref=f"y{ax_num} domain", 
                showarrow=False, xanchor="left"
            ),
        )

# Plot Scientific (rows 1-5)
plot_5_panels(dist_df, 0, "SCI")
# Plot Insurance (rows 6-10)
plot_5_panels(dist_df, 5, "INS")
# Plot Sustained 7d (rows 11-15)
plot_5_panels(dist_df, 10, "SUS7D")

fig.update_layout(barmode='stack', height=4500, width=1300, template="plotly_white", title_text="Trigger Formula Comparison: SCI vs INS vs SUS7D", showlegend=False)

for i in [4, 9, 14]:
    fig.update_yaxes(range=[0, 2], tickvals=[0, 1], ticktext=["None", "ACTIVE"], row=i+1, col=1)

html_out = os.path.join(VIZ_DIR, "Flood_Comparison_Chibombo_2010_2011.html")
fig.write_html(html_out)
print(f"Saved to {html_out}")
