import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure UTF-8 encoding for standard outputs to prevent UnicodeEncodeError on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# =============================================================================
# METHODOLOGY & SCIENTIFIC CITATIONS
# =============================================================================
# 1. SATURATION-EXCESS HYDROLOGY (Tramblay et al., 2021)
#    Citation: Tramblay, Y., et al. (2021). "Stronger evidence for the role of 
#              land-use change and human activities on increased flood risk in Africa."
#              Environmental Research Letters, 16(2), p.024028.
#    Justification: Agricultural floods in tropical/sub-tropical Africa are primarily
#                   driven by saturation overland flow. We use a Standardized Soil
#                   Moisture Index (SSI) >= 1.5 (top 6.7% wetness anomaly) as the
#                   indicator that the soil sponge is fully saturated.
#
# 2. SCS CURVE NUMBER OVERLAND RUNOFF (USDA-SCS, 1972; WMO No. 1103)
#    Citation: USDA Soil Conservation Service (1972). "National Engineering Handbook,
#              Section 4: Hydrology."
#              World Meteorological Organization (2018). WMO-No. 1103 Guidelines.
#    Equation: Q = (P_7d - Ia)^2 / (P_7d - Ia + S) for P_7d > Ia else 0
#              S = (25400 / CN) - 254 (Potential Max Soil Retention)
#              Ia = 0.2 * S (Initial Abstraction)
#              CN = 85 (Standard for cultivated agricultural croplands in Zambia)
#    Threshold: Runoff depth Q >= 20.0 mm (representing significant surface water 
#               accumulation that exceeds crop drainage thresholds).
# =============================================================================

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIGURATION
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
output_folder = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\agricultural"
ssi_csv = os.path.join(output_folder, "Zambia_Agricultural_Districts_Final_Study_SSI_Gringorten_Full_Season.csv")
chirps_csv = os.path.join(output_folder, "CHIRPS_Standardized_Master.csv")
viz_folder = os.path.join(output_folder, "visualizations")
os.makedirs(viz_folder, exist_ok=True)

# List of targets to plot (District: Year)
requested_targets = {
    'KAPIRI MPOSHI': 2007,
    'CHIBOMBO': 2011,
    'MONZE': 2007
}

def normalize_name(name):
    return str(name).replace('-', ' ').replace('_', ' ').strip().upper()

def get_runoff_threshold(district_name):
    dist = normalize_name(district_name)
    # Steep slopes (Escarpments): Q >= 15.0mm
    if dist in ['SIAVONGA', 'CHAMA', 'ITEZHI-TEZHI', 'ITEZHI THEZI', 'GWEMBE', 'SINAZONGWE']:
        return 15.0
    # Moderate slopes (Plateau/Hills): Q >= 10.0mm
    elif dist in ['MBALA', 'MKUSHI', 'LIVINGSTONE', 'SESHEKE', 'KAOMA', 'PETAUKE', 'CHOMA']:
        return 10.0
    # Gentle slopes (Flat Plains/River Basins): Q >= 5.0mm
    else:
        return 5.0

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LOAD & MERGE DATASETS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("ðŸ”„ Loading Gringorten SSI dataset...")
if not os.path.exists(ssi_csv):
    print(f"âŒ ERROR: SSI dataset not found at: {ssi_csv}")
    sys.exit(1)

df_ssi = pd.read_csv(ssi_csv)
df_ssi['Date'] = pd.to_datetime(df_ssi['Date'])
df_ssi['District_Upper'] = df_ssi['District_Name'].apply(normalize_name)

print("ðŸ”„ Loading CHIRPS master rainfall dataset...")
if not os.path.exists(chirps_csv):
    print(f"âŒ ERROR: CHIRPS master rainfall not found at: {chirps_csv}")
    sys.exit(1)

df_chirps = pd.read_csv(chirps_csv, low_memory=False)
df_chirps['date'] = pd.to_datetime(df_chirps['date'])
df_chirps['District_Upper'] = df_chirps['District_Name'].apply(normalize_name)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MERGE DATASETS FIRST (Needed for dynamic CN)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("ðŸ”— Merging SSI and rainfall data for dynamic runoff calculation...")
df_merged = df_ssi.merge(
    df_chirps[['District_Upper', 'date', 'precipitation']],
    left_on=['District_Upper', 'Date'],
    right_on=['District_Upper', 'date'],
    how='inner'
).drop(columns=['date'])

df_merged = df_merged.sort_values(['District_Upper', 'Date'])

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CALCULATE DYNAMIC RUNOFF (SSI-adjusted Curve Number)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("ðŸ“Š Calculating dynamic daily Runoff (CN adjusted by SSI)...")

def get_district_cn(district_name):
    dist = str(district_name).upper().strip()
    sandy_steep = ['SIAVONGA', 'CHAMA', 'ITEZHI-TEZHI', 'ITEZHI THEZI', 'GWEMBE', 'SINAZONGWE', 'CHIRUNDU', 'ZIMBA', 'LUANGWA']
    if dist in sandy_steep: return 75.0
    loamy_moderate = ['MBALA', 'MKUSHI', 'LIVINGSTONE', 'SESHEKE', 'KAOMA', 'PETAUKE', 'CHOMA', 'LUNDAZI', 'CHIPATA', 'SOLWEZI', 'MANSA', 'KASAMA', 'MPIKA', 'ISOKA', 'CHINSALI', 'MUFULIRA', 'NDOLA', 'KITWE', 'KALULUSHI', 'LUANSHYA', 'CHILILABOMBWE', 'CHINGOLA']
    if dist in loamy_moderate: return 80.0
    return 85.0

df_merged['CN_II'] = df_merged['District_Upper'].apply(get_district_cn)

# Adjust CN based on Antecedent Moisture Condition (AMC) using SSI
# AMC I (Dry) if SSI < -0.5
# AMC II (Normal) if -0.5 <= SSI <= 1.0
# AMC III (Wet) if SSI > 1.0
df_merged['CN_I'] = df_merged['CN_II'] / (2.281 - 0.01281 * df_merged['CN_II'])
df_merged['CN_III'] = df_merged['CN_II'] / (0.427 + 0.00573 * df_merged['CN_II'])

conditions = [
    (df_merged['SSI'] < -0.5),
    (df_merged['SSI'] > 1.0)
]
choices = [df_merged['CN_I'], df_merged['CN_III']]
df_merged['CN_Dynamic'] = np.select(conditions, choices, default=df_merged['CN_II'])

df_merged['S'] = (25400.0 / df_merged['CN_Dynamic']) - 254.0
df_merged['Ia'] = 0.2 * df_merged['S']

df_merged['Daily_Q'] = np.where(
    df_merged['precipitation'] > df_merged['Ia'],
    ((df_merged['precipitation'] - df_merged['Ia']) ** 2) / (df_merged['precipitation'] - df_merged['Ia'] + df_merged['S']),
    0.0
)

# Use Runoff_Q_mm to hold the Daily sum for compatibility
df_merged['Runoff_Q_mm'] = df_merged['Daily_Q']

# Calculate daily mean of SSI chronologically
df_merged['SSI_3d_mean'] = df_merged['SSI']

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CALCULATE HISTORICAL CLIMATOLOGY (DOY MEAN OF daily VARIABLES)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("ðŸ“ˆ Computing 25-year historical mean climatology (per DOY)...")
climatology = df_merged.groupby(['District_Upper', 'doy']).agg(
    mean_precipitation=('precipitation', 'mean'),
    mean_Runoff_Q_mm=('Runoff_Q_mm', 'mean'),
    mean_SSI_3d_mean=('SSI_3d_mean', 'mean')
).reset_index()

df_plot = df_merged.merge(climatology, on=['District_Upper', 'doy'], how='left')

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Daily PRECIPITATION & THRESHOLD (mean + 2Ïƒ)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Citation: Flood Strategy Introduction (ASR, 2026). The threshold for
#   anomalous Daily Precipitation is defined as mean + 2Ïƒ of the 25-year
#   historical distribution for the same day-of-year window, following
#   standard practice in parametric insurance trigger design.
print("ðŸ“Š Computing Daily precipitation and mean+2Ïƒ thresholds...")
df_plot = df_plot.sort_values(['District_Upper', 'Date'])
df_plot['precip_3d'] = df_plot['precipitation']

# Compute historic 25-year mean and std of Daily Precip per DOY per district
precip_3d_stats = df_plot.groupby(['District_Upper', 'doy'])['precip_3d'].agg(
    ['mean', 'std']
).reset_index().rename(columns={'mean': 'precip_daily_mean', 'std': 'precip_daily_std'})

df_plot = df_plot.merge(precip_3d_stats, on=['District_Upper', 'doy'], how='left')
df_plot['precip_3d_threshold'] = df_plot['precip_daily_mean'] + 2 * df_plot['precip_daily_std']
df_plot['precip_above_thr'] = df_plot['precip_3d'] > df_plot['precip_3d_threshold']

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# AGRICULTURE FLOOD INDEX (Placeholder)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Citation: ASR Flood Strategy (2026). The Agriculture-Flood Index flags
#   days based on the Combined Agricultural Flood Matrix (computed below).
#   It captures saturated-soil conditions paired with surface runoff.
print("ðŸ“Š Computing Agriculture Flood Index...")
# We will use Trigger_Fired below as the true parametric flood index.

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# VERIFY TRIGGER CONDITIONS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("ðŸ›¡ï¸ Verifying trigger calculation logic via Combined Agricultural Flood Matrix...")
# Identify triggers using the Combined Agricultural Flood Matrix
conditions = [
    (df_plot['Runoff_Q_mm'] < 2.0),
    (df_plot['Runoff_Q_mm'] >= 2.0) & (df_plot['Runoff_Q_mm'] < 10.0),
    (df_plot['Runoff_Q_mm'] >= 10.0) & (df_plot['Runoff_Q_mm'] < 25.0),
    (df_plot['Runoff_Q_mm'] >= 25.0) & (df_plot['Runoff_Q_mm'] < 50.0),
    (df_plot['Runoff_Q_mm'] >= 50.0)
]
choices = [0, 1, 2, 3, 4]
df_plot['Runoff_Severity_Class'] = np.select(conditions, choices, default=0)

ssi_col = df_plot['SSI_3d_mean']
q_class_col = df_plot['Runoff_Severity_Class']

# FLOOD_TRIGGER condition
df_plot['Trigger_Fired'] = (
    ((ssi_col >= 1.5) & (q_class_col >= 2)) | 
    (((ssi_col >= 0.0) & (ssi_col < 1.5)) & (q_class_col >= 3))
)

# Filter targets
available_districts = df_plot['District_Upper'].unique()
targets_to_plot = []
for dist_name, yr in requested_targets.items():
    norm_dist = normalize_name(dist_name)
    if norm_dist in available_districts:
        targets_to_plot.append((norm_dist, yr))

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# STATIC PLOT: CLIMATOLOGY VS TARGET YEAR (Matplotlib PNG)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
n_plots = len(targets_to_plot)
if n_plots > 0:
    fig, axes = plt.subplots(n_plots, 3, figsize=(20, 4.0 * n_plots), sharex=False)
    if n_plots == 1:
        axes = np.array([axes])
        
    for idx, (dist, yr) in enumerate(targets_to_plot):
        d_df = df_plot[(df_plot['District_Upper'] == dist) & (df_plot['Crop_Year'] == yr)].sort_values('Date')
        trigger_dates = d_df[d_df['Trigger_Fired']]
        
        # Col 0: Precipitation vs Historic Mean
        ax_p = axes[idx, 0]
        # Target year rain (Blue)
        ax_p.plot(d_df['Date'], d_df['precipitation'], color='#1d4ed8', linewidth=1.5, label=f'Daily Rain {yr}-{yr+1} (Blue)')
        # Historic Mean rain (Red)
        ax_p.plot(d_df['Date'], d_df['mean_precipitation'], color='#ef4444', linewidth=1.2, linestyle='--', label='Historic Mean Daily Rain (Red)')
        
        # Mark triggers
        if not trigger_dates.empty:
            ax_p.scatter(trigger_dates['Date'], trigger_dates['precipitation'], color='#ef4444', s=45, marker='X', zorder=5, label='Trigger Event (X)')
            
        ax_p.set_title(f"{dist.title()} â€” Daily Rain vs Climatology", fontsize=10, fontweight='bold')
        ax_p.set_ylabel("Rain Depth (mm)", fontsize=9)
        ax_p.grid(True, color='#e2e8f0', alpha=0.4)
        ax_p.legend(loc='upper left', fontsize=8)
        ax_p.tick_params(axis='x', rotation=15)
        
        # Col 1: Runoff vs Historic Mean
        ax_q = axes[idx, 1]
        # Target year runoff (Orange)
        ax_q.plot(d_df['Date'], d_df['Runoff_Q_mm'], color='#f59e0b', linewidth=2, label=f'Daily Runoff {yr}-{yr+1} (Orange)')
        # Historic Mean runoff (Red)
        ax_q.plot(d_df['Date'], d_df['mean_Runoff_Q_mm'], color='#ef4444', linewidth=1.5, linestyle='--', label='Historic Mean Daily Runoff (Red)')
        # Runoff thresholds
        ax_q.axhline(10.0, color='#f1c40f', linestyle='--', linewidth=1.0, alpha=0.8, label='Moderate Threshold (10mm)')
        ax_q.axhline(25.0, color='#c0392b', linestyle='-', linewidth=1.2, alpha=0.8, label='Severe Threshold (25mm)')
        
        # Mark triggers
        if not trigger_dates.empty:
            ax_q.scatter(trigger_dates['Date'], trigger_dates['Runoff_Q_mm'], color='#ef4444', s=45, marker='X', zorder=5, label='Trigger Event (X)')
            
        ax_q.set_title(f"{dist.title()} â€” Daily Runoff vs Climatology", fontsize=10, fontweight='bold')
        ax_q.set_ylabel("Runoff Depth (mm)", fontsize=9)
        ax_q.grid(True, color='#e2e8f0', alpha=0.4)
        ax_q.legend(loc='upper left', fontsize=8)
        ax_q.tick_params(axis='x', rotation=15)
        
        # Col 2: SSI vs Historic Mean
        ax_ssi = axes[idx, 2]
        # Target year SSI (Green)
        line_ssi, = ax_ssi.plot(d_df['Date'], d_df['SSI_3d_mean'], color='#10b981', linewidth=2, label=f'Daily SSI {yr}-{yr+1} (Green)')
        # Historic Mean SSI (Red)
        ax_ssi.plot(d_df['Date'], d_df['mean_SSI_3d_mean'], color='#ef4444', linewidth=1.5, linestyle='--', label='Historic Mean Daily SSI (Red)')
        
        # Moderate / Severe Wetness Markers
        mod_df = d_df[(d_df['SSI_3d_mean'] >= 1.0) & (d_df['SSI_3d_mean'] < 1.5)]
        sev_df = d_df[d_df['SSI_3d_mean'] >= 1.5]
        sc_mod = None
        sc_sev = None
        if not mod_df.empty:
            sc_mod = ax_ssi.scatter(mod_df['Date'], mod_df['SSI_3d_mean'], color='#f59e0b', s=20, marker='o', zorder=4, label='Moderately Wet (1.0-1.5)')
        if not sev_df.empty:
            sc_sev = ax_ssi.scatter(sev_df['Date'], sev_df['SSI_3d_mean'], color='#dc2626', s=20, marker='o', zorder=4, label='Severely Wet (>=1.5)')
            
        # SSI Trigger line
        ax_ssi.axhline(1.5, color='#10b981', linestyle=':', linewidth=1.2, alpha=0.7, label='Trigger Threshold (1.5)')
        
        # Mark triggers
        if not trigger_dates.empty:
            ax_ssi.scatter(trigger_dates['Date'], trigger_dates['SSI_3d_mean'], color='#ef4444', s=60, marker='X', zorder=5, label='Trigger Event (X)')
            
        ax_ssi.set_title(f"{dist.title()} â€” Daily Mean SSI vs Climatology", fontsize=10, fontweight='bold')
        ax_ssi.set_ylabel("Standardized SSI Value", fontsize=9)
        ax_ssi.grid(True, color='#e2e8f0', alpha=0.4)
        
        # Combine handles for legends
        lines = [line_ssi]
        if sc_mod is not None: lines.append(sc_mod)
        if sc_sev is not None: lines.append(sc_sev)
        labels = [l.get_label() for l in lines]
        ax_ssi.legend(lines, labels, loc='lower left', fontsize=8)
        
        ax_ssi.tick_params(axis='x', rotation=15)

    plt.suptitle("Zambia Agricultural Flood Study â€” daily/rolling variables vs 25-Year Climatology", 
                 fontsize=14, fontweight='bold', color='#0f172a', y=0.99)
    plt.tight_layout()
    static_plot_path = os.path.join(viz_folder, "Daily_Agri_Trigger_Baseline_Dynamic_CN_Daily.png")
    plt.savefig(static_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\n  âœ… Static comparison plot saved: {static_plot_path}")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# INTERACTIVE PLOT (Plotly HTML) â€” 4 panels per district
# Meeting requirements (25 Jun 2026):
#   Panel A: Daily precipitation BAR (red > mean+2Ïƒ, blue otherwise)
#   Panel B: Daily Runoff vs 25-year mean (UNCHANGED)
#   Panel C: Agriculture Flood Index (days with runoff>0 AND precip>mean+2Ïƒ)
#   Panel D: Daily mean SSI vs 25-year mean (UNCHANGED)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PANELS_PER_DISTRICT = 4
if n_plots > 0:
    fig_plotly = make_subplots(
        rows=n_plots * PANELS_PER_DISTRICT, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.025,
        subplot_titles=[
            item for dist, yr in targets_to_plot
            for item in (
                f"{dist.title()} â€” Daily Precipitation ({yr}-{yr+1})",
                f"{dist.title()} â€” Daily Runoff vs 25-Year Mean ({yr}-{yr+1})",
                f"{dist.title()} â€” Agriculture Flood Index ({yr}-{yr+1})",
                f"{dist.title()} â€” Daily Mean SSI vs 25-Year Mean ({yr}-{yr+1})"
            )
        ]
    )

    for idx, (dist, yr) in enumerate(targets_to_plot, 1):
        d_df = df_plot[(df_plot['District_Upper'] == dist) & (df_plot['Crop_Year'] == yr)].sort_values('Date')
        trigger_dates = d_df[d_df['Trigger_Fired']]

        row_precip  = (idx - 1) * PANELS_PER_DISTRICT + 1
        row_runoff  = (idx - 1) * PANELS_PER_DISTRICT + 2
        row_flood = (idx - 1) * PANELS_PER_DISTRICT + 3
        row_ssi     = (idx - 1) * PANELS_PER_DISTRICT + 4

        # â”€â”€ PANEL A: Daily Precipitation Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Citation: Flood Strategy Introduction (ASR, 2026).
        #   Bars are RED when Daily Precip > mean + 2Ïƒ, BLUE otherwise.
        bar_colours = ['#ef4444' if above else '#1d4ed8'
                       for above in d_df['precip_above_thr'].fillna(False)]
        fig_plotly.add_trace(
            go.Bar(
                x=d_df['Date'], y=d_df['precip_3d'],
                marker_color=bar_colours,
                name='Daily Precip',
                showlegend=(idx == 1),
                legendgroup='precip_3d',
                hovertemplate='%{x|%Y-%m-%d}<br>Daily Precip: %{y:.1f} mm<extra></extra>'
            ),
            row=row_precip, col=1
        )
        # Mean + 2Ïƒ threshold line
        fig_plotly.add_trace(
            go.Scatter(
                x=d_df['Date'], y=d_df['precip_3d_threshold'],
                mode='lines', name='Mean + 2Ïƒ Threshold',
                showlegend=(idx == 1), legendgroup='thr_line',
                line=dict(color='#ef4444', width=1.5, dash='dash'),
                hovertemplate='Threshold: %{y:.1f} mm<extra></extra>'
            ),
            row=row_precip, col=1
        )
        # Historic mean line
        fig_plotly.add_trace(
            go.Scatter(
                x=d_df['Date'], y=d_df['precip_daily_mean'],
                mode='lines', name='25-Year Mean (Daily)',
                showlegend=(idx == 1), legendgroup='mean_line',
                line=dict(color='#64748b', width=1.2, dash='dot'),
                hovertemplate='Mean: %{y:.1f} mm<extra></extra>'
            ),
            row=row_precip, col=1
        )
        fig_plotly.update_yaxes(title_text="Daily Precip (mm)", row=row_precip, col=1)

        # â”€â”€ PANEL B: Runoff (UNCHANGED) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        fig_plotly.add_trace(
            go.Scatter(x=d_df['Date'], y=d_df['Runoff_Q_mm'], mode='lines',
                       name='Daily Runoff (Target Year)',
                       showlegend=(idx == 1), legendgroup='runoff_target',
                       line=dict(color='#f59e0b', width=2)),
            row=row_runoff, col=1
        )
        fig_plotly.add_trace(
            go.Scatter(x=d_df['Date'], y=d_df['mean_Runoff_Q_mm'], mode='lines',
                       name='Historic Mean Daily Runoff',
                       showlegend=(idx == 1), legendgroup='runoff_mean',
                       line=dict(color='#ef4444', width=1.5, dash='dash')),
            row=row_runoff, col=1
        )
        if not trigger_dates.empty:
            fig_plotly.add_trace(
                go.Scatter(x=trigger_dates['Date'], y=trigger_dates['Runoff_Q_mm'],
                           mode='markers', name='Trigger Events',
                           showlegend=(idx == 1), legendgroup='triggers',
                           marker=dict(color='#ef4444', size=8, symbol='x')),
                row=row_runoff, col=1
            )
        # Runoff threshold shapes
        fig_plotly.add_shape(
            type="line", x0=d_df['Date'].min(), x1=d_df['Date'].max(), y0=10.0, y1=10.0,
            line=dict(color="#f1c40f", width=1.0, dash="dash"), row=row_runoff, col=1
        )
        fig_plotly.add_shape(
            type="line", x0=d_df['Date'].min(), x1=d_df['Date'].max(), y0=25.0, y1=25.0,
            line=dict(color="#c0392b", width=1.2, dash="solid"), row=row_runoff, col=1
        )
        fig_plotly.update_yaxes(title_text="Runoff (mm)", row=row_runoff, col=1)

        # â”€â”€ PANEL C: Agriculture Flood Index â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Citation: ASR Flood Strategy (2026). Days flagged when
        #   the Combined Agricultural Flood Matrix condition is met.
        flood_days = d_df[d_df['Trigger_Fired'] == True]
        non_flood_days = d_df[d_df['Trigger_Fired'] == False]
        # Show all days as a baseline (grey)
        fig_plotly.add_trace(
            go.Bar(
                x=non_flood_days['Date'],
                y=non_flood_days['precip_3d'].fillna(0),
                marker_color='#cbd5e1',
                name='Normal Days',
                showlegend=(idx == 1), legendgroup='normal_days',
                hovertemplate='%{x|%Y-%m-%d}<br>Daily Precip: %{y:.1f} mm<br>Status: Normal<extra></extra>'
            ),
            row=row_flood, col=1
        )
        # Highlight flood-flagged days (dark red)
        if not flood_days.empty:
            fig_plotly.add_trace(
                go.Bar(
                    x=flood_days['Date'],
                    y=flood_days['precip_3d'],
                    marker_color='#dc2626',
                    name='Agri Flood Days',
                    showlegend=(idx == 1), legendgroup='flood_days',
                    hovertemplate='%{x|%Y-%m-%d}<br>Daily Precip: %{y:.1f} mm<br>Status: FLOOD<extra></extra>'
                ),
                row=row_flood, col=1
            )
        fig_plotly.update_yaxes(title_text="Flood Index (mm)", row=row_flood, col=1)

        # â”€â”€ PANEL D: SSI (UNCHANGED) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Citation: Gringorten SSI â€” Farahmand & AghaKouchak (2015);
        #   Wang et al. (2019). Non-parametric distribution-free index.
        fig_plotly.add_trace(
            go.Scatter(x=d_df['Date'], y=d_df['SSI_3d_mean'], mode='lines',
                       name='Daily SSI (Target Year)',
                       showlegend=(idx == 1), legendgroup='ssi_target',
                       line=dict(color='#10b981', width=2)),
            row=row_ssi, col=1
        )
        mod_df = d_df[(d_df['SSI_3d_mean'] >= 1.0) & (d_df['SSI_3d_mean'] < 1.5)]
        if not mod_df.empty:
            fig_plotly.add_trace(
                go.Scatter(x=mod_df['Date'], y=mod_df['SSI_3d_mean'], mode='markers',
                           name="Moderately Wet (1.0-1.5)", legendgroup="ModWet",
                           showlegend=(idx == 1),
                           marker=dict(color='#f59e0b', size=5)),
                row=row_ssi, col=1
            )
        sev_df = d_df[d_df['SSI_3d_mean'] >= 1.5]
        if not sev_df.empty:
            fig_plotly.add_trace(
                go.Scatter(x=sev_df['Date'], y=sev_df['SSI_3d_mean'], mode='markers',
                           name="Severely Wet (>=1.5)", legendgroup="SevWet",
                           showlegend=(idx == 1),
                           marker=dict(color='#dc2626', size=5)),
                row=row_ssi, col=1
            )
        fig_plotly.add_trace(
            go.Scatter(x=d_df['Date'], y=d_df['mean_SSI_3d_mean'], mode='lines',
                       name='Historic Mean Daily SSI',
                       showlegend=(idx == 1), legendgroup='ssi_mean',
                       line=dict(color='#ef4444', width=1.5, dash='dash')),
            row=row_ssi, col=1
        )
        if not trigger_dates.empty:
            fig_plotly.add_trace(
                go.Scatter(x=trigger_dates['Date'], y=trigger_dates['SSI_3d_mean'],
                           mode='markers', name='Trigger Events',
                           showlegend=False, legendgroup='triggers',
                           marker=dict(color='#ef4444', size=8, symbol='x')),
                row=row_ssi, col=1
            )
        fig_plotly.add_shape(
            type="line", x0=d_df['Date'].min(), x1=d_df['Date'].max(), y0=1.5, y1=1.5,
            line=dict(color="#10b981", width=1.2, dash="dot"), row=row_ssi, col=1
        )
        fig_plotly.update_yaxes(title_text="SSI Value", row=row_ssi, col=1)

    fig_plotly.update_layout(
        template="plotly_white",
        title={
            'text': "Agricultural Flood Trigger Profiles vs 25-Year Historical Baseline<br>"
                    "<sup>Panels: Daily Precip | Runoff | Agriculture Flood Index | SSI</sup>",
            'y': 0.995,
            'yanchor': 'top',
            'x': 0.5,
            'xanchor': 'center'
        },
        margin=dict(t=180),
        height=250 * n_plots * PANELS_PER_DISTRICT,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.03, xanchor='center', x=0.5),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#f8fafc',
        font_family="Inter, sans-serif"
    )

    interactive_plot_path = os.path.join(viz_folder, "Daily_Agri_Trigger_Baseline_Dynamic_CN_Daily.html")
    fig_plotly.write_html(interactive_plot_path, include_plotlyjs='cdn')
    print(f"  âœ… Interactive comparison plot saved: {interactive_plot_path}")

print("\nðŸŽ‰ Done!")




