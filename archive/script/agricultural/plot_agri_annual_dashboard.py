import pandas as pd
import numpy as np
import geopandas as gpd
import os
import json
import sys
from scipy.stats import norm
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Set folder paths
base_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
output_folder = os.path.join(base_path, "output", "agricultural")
shp_path = os.path.join(base_path, "output", "agricultural", "Zambia_agri_districts.shp")
raw_soil_csv = os.path.join(output_folder, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv")
chirps_csv = os.path.join(output_folder, "CHIRPS_Standardized_Master.csv")
viz_folder = os.path.join(output_folder, "visualizations")
os.makedirs(viz_folder, exist_ok=True)

print("🔄 Step 1: Loading spatial boundary of all 70 Agricultural Districts...")
if not os.path.exists(shp_path):
    print(f"❌ ERROR: Agricultural shapefile not found at: {shp_path}")
    sys.exit(1)

gdf = gpd.read_file(shp_path)
gdf['District_Upper'] = gdf['ADM_NAME'].astype(str).str.strip().str.upper()
districts_70 = gdf['District_Upper'].unique().tolist()
districts_70_names = {d: gdf[gdf['District_Upper'] == d]['ADM_NAME'].values[0] for d in districts_70}
print(f"Loaded {len(districts_70)} agricultural districts.")

print("\n🔄 Step 2: Loading daily soil moisture and computing Gringorten SSI for all 70 districts...")
if not os.path.exists(raw_soil_csv):
    print(f"❌ ERROR: Raw soil moisture CSV not found at: {raw_soil_csv}")
    sys.exit(1)

# Load daily soil moisture, skipping bad lines
df_sm = pd.read_csv(raw_soil_csv, on_bad_lines='skip', low_memory=False)
df_sm['District_Upper'] = df_sm['District_Name'].astype(str).str.strip().str.upper()
df_sm = df_sm[df_sm['District_Upper'].isin(districts_70)].copy()
df_sm = df_sm.drop_duplicates(subset=['District_Upper', 'Date'])
df_sm['Date'] = pd.to_datetime(df_sm['Date'])
df_sm['Month'] = df_sm['Date'].dt.month
df_sm['doy'] = df_sm['Date'].apply(lambda d: d.dayofyear if not d.is_leap_year or d.dayofyear < 60 else d.dayofyear - 1)

print(f"Extracted {len(df_sm):,} rows of soil moisture data.")

# Apply growing season filter (Nov-Apr)
df_sm = df_sm[(df_sm['Month'] >= 11) | (df_sm['Month'] <= 4)].copy()
df_sm['Crop_Year'] = np.where(df_sm['Month'] >= 11, df_sm['Date'].dt.year, df_sm['Date'].dt.year - 1)

# Compute depth-weighted root zone soil moisture
df_sm['sm_root_zone'] = (df_sm['soil_0_7cm'] * 0.07) + \
                         (df_sm['soil_7_28cm'] * 0.21) + \
                         (df_sm['soil_28_100cm'] * 0.72)

# Compute Gringorten SSI anomalies
def calculate_gringorten_ssi(series):
    valid_series = series.dropna()
    n = len(valid_series)
    if n < 10:
        return pd.Series([np.nan] * len(series), index=series.index)
    ranks = series.rank(method='average')
    prob = (ranks - 0.44) / (n + 0.12)
    return norm.ppf(np.clip(prob, 0.0001, 0.9999))

df_sm['SSI'] = df_sm.groupby(['District_Upper', 'doy'])['sm_root_zone'].transform(calculate_gringorten_ssi)
print("Soil Moisture Index (SSI) calculation completed.")

def get_runoff_threshold(district_name):
    dist = str(district_name).upper().strip()
    # Steep slopes (Escarpments): Q >= 15.0mm
    if dist in ['SIAVONGA', 'CHAMA', 'ITEZHI-TEZHI', 'ITEZHI THEZI', 'GWEMBE', 'SINAZONGWE']:
        return 15.0
    # Moderate slopes (Plateau/Hills): Q >= 10.0mm
    elif dist in ['MBALA', 'MKUSHI', 'LIVINGSTONE', 'SESHEKE', 'KAOMA', 'PETAUKE', 'CHOMA']:
        return 10.0
    # Gentle slopes (Flat Plains/River Basins): Q >= 5.0mm
    else:
        return 5.0

print("\n🔄 Step 3: Loading daily rainfall and calculating SCS Curve Number Runoff for all 70 districts...")
if not os.path.exists(chirps_csv):
    print(f"❌ ERROR: CHIRPS rainfall master CSV not found at: {chirps_csv}")
    sys.exit(1)

df_rain = pd.read_csv(chirps_csv, low_memory=False)
df_rain['District_Upper'] = df_rain['District_Name'].astype(str).str.strip().str.upper()
df_rain = df_rain[df_rain['District_Upper'].isin(districts_70)].copy()
df_rain['date'] = pd.to_datetime(df_rain['date'])
df_rain = df_rain.sort_values(['District_Upper', 'date'])

print(f"Extracted {len(df_rain):,} rows of daily rainfall data.")

def get_district_cn(district_name):
    dist = str(district_name).upper().strip()
    sandy_steep = [
        'SIAVONGA', 'CHAMA', 'ITEZHI-TEZHI', 'ITEZHI THEZI', 'GWEMBE', 'SINAZONGWE', 
        'CHIRUNDU', 'ZIMBA', 'LUANGWA'
    ]
    if dist in sandy_steep:
        return 75.0
    loamy_moderate = [
        'MBALA', 'MKUSHI', 'LIVINGSTONE', 'SESHEKE', 'KAOMA', 'PETAUKE', 'CHOMA', 
        'LUNDAZI', 'CHIPATA', 'SOLWEZI', 'MANSA', 'KASAMA', 'MPIKA', 'ISOKA', 
        'CHINSALI', 'MUFULIRA', 'NDOLA', 'KITWE', 'KALULUSHI', 'LUANSHYA', 
        'CHILILABOMBWE', 'CHINGOLA'
    ]
    if dist in loamy_moderate:
        return 80.0
    return 85.0

df_rain['CN'] = df_rain['District_Upper'].apply(get_district_cn)
df_rain['S'] = (25400.0 / df_rain['CN']) - 254.0
df_rain['Ia'] = 0.2 * df_rain['S']

# Daily runoff (using daily precipitation)
df_rain['Daily_Runoff_Q_mm'] = np.where(
    df_rain['precipitation'] > df_rain['Ia'],
    ((df_rain['precipitation'] - df_rain['Ia']) ** 2) / (df_rain['precipitation'] - df_rain['Ia'] + df_rain['S']),
    0.0
)

# 3-day rolling runoff sum
df_rain['Runoff_Q_3d_sum'] = df_rain.groupby('District_Upper')['Daily_Runoff_Q_mm'].transform(
    lambda x: x.rolling(3, min_periods=3).sum()
)
print("Precipitation runoff modeling completed.")

print("\n🔄 Step 4: Merging and identifying triggers...")
df_merged = df_sm.merge(
    df_rain[['District_Upper', 'date', 'precipitation', 'Daily_Runoff_Q_mm', 'Runoff_Q_3d_sum']],
    left_on=['District_Upper', 'Date'],
    right_on=['District_Upper', 'date'],
    how='inner'
).drop(columns=['date'])

# Calculate 3-day rolling mean of SSI chronologically
df_merged = df_merged.sort_values(['District_Upper', 'Date'])
df_merged['SSI_3d_mean'] = df_merged.groupby('District_Upper')['SSI'].transform(
    lambda x: x.rolling(3, min_periods=3).mean()
)

# Identify triggers using the Combined Agricultural Flood Matrix
# Runoff Severity Classification
conditions = [
    (df_merged['Runoff_Q_3d_sum'] < 2.0),
    (df_merged['Runoff_Q_3d_sum'] >= 2.0) & (df_merged['Runoff_Q_3d_sum'] < 10.0),
    (df_merged['Runoff_Q_3d_sum'] >= 10.0) & (df_merged['Runoff_Q_3d_sum'] < 25.0),
    (df_merged['Runoff_Q_3d_sum'] >= 25.0) & (df_merged['Runoff_Q_3d_sum'] < 50.0),
    (df_merged['Runoff_Q_3d_sum'] >= 50.0)
]
choices = [0, 1, 2, 3, 4]
df_merged['Runoff_Severity_Class'] = np.select(conditions, choices, default=0)

ssi = df_merged['SSI_3d_mean']
q_class = df_merged['Runoff_Severity_Class']

# FLOOD_TRIGGER condition
df_merged['Trigger_Implemented'] = (
    ((ssi >= 1.5) & (q_class >= 2)) | 
    (((ssi >= 0.0) & (ssi < 1.5)) & (q_class >= 3))
)
print(f"Identified {df_merged['Trigger_Implemented'].sum():,} total implemented trigger events.")

print("\n🔄 Step 5: Aggregating annually per district...")
# Group by Crop_Year and District to get annual metrics
# For precipitation and daily runoff, we calculate the sum over the Nov-Apr season
# For triggers, we count the number of days the trigger fired
# For SSI, we calculate the mean SSI over the season
agri_annual = df_merged.groupby(['Crop_Year', 'District_Upper']).agg(
    precipitation_sum=('precipitation', 'sum'),
    runoff_sum=('Daily_Runoff_Q_mm', 'sum'),
    trigger_count=('Trigger_Implemented', 'sum'),
    ssi_peak=('SSI_3d_mean', 'max')
).reset_index()

# Clean up crop years to only include complete study years (2000 to 2024)
agri_annual = agri_annual[(agri_annual['Crop_Year'] >= 2000) & (agri_annual['Crop_Year'] <= 2024)].copy()

# Add printable district name
agri_annual['District_Name'] = agri_annual['District_Upper'].map(districts_70_names)

print("\n🔄 Step 6: Calculating National average for each year...")
national_annual = agri_annual.groupby('Crop_Year').agg(
    precipitation_sum=('precipitation_sum', 'mean'),
    runoff_sum=('runoff_sum', 'mean'),
    trigger_count=('trigger_count', 'mean'),
    ssi_peak=('ssi_peak', 'mean')
).reset_index()

print("\n🔄 Step 7: Generating 4-Panel Interactive HTML Dashboard...")
fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    subplot_titles=(
        "Panel A: Annual Precipitation (Nov–Apr Seasonal Sum per District)",
        "Panel B: Annual SCS Runoff (Nov–Apr Seasonal Sum per District)",
        "Panel C: Annual Peak Soil Moisture Index (Annual Peak Event Condition)",
        "Panel D: Annual Agricultural Flood Triggers (Nov–Apr Total Trigger Days)"
    )
)

# Color variables for premium light theme
COLOR_AVG = "#1e293b" # Dark Slate
COLOR_GRID = "#f1f5f9" # Very Light Slate Grey
COLOR_BG = "#f8fafc" # Light grey card BG

# Ensemble (Spaghetti) Plot Styling parameters
# Background cloud lines representing the 70 individual districts (faint and thin)
line_style_district = dict(width=0.8, color='rgba(148, 163, 184, 0.18)')

# Curated colors for national averages (mean trends)
COLOR_PRECIP_AVG = "#1d4ed8"  # Premium Blue
COLOR_RUNOFF_AVG = "#ea580c"  # Premium Rust Orange
COLOR_TRIGGER_AVG = "#059669" # Premium Emerald Green
COLOR_SSI_AVG = "#2563eb"     # Vibrant Water Blue

# Year x-axis values
crop_years = sorted(agri_annual['Crop_Year'].unique())

# Add traces for each district in each panel (ensemble cloud)
show_legend_flag = True # Only show legend once per district
for dist in sorted(districts_70):
    dist_data = agri_annual[agri_annual['District_Upper'] == dist].sort_values('Crop_Year')
    dist_name = districts_70_names[dist]
    
    # Trace A: Precipitation
    fig.add_trace(
        go.Scatter(
            x=dist_data['Crop_Year'], y=dist_data['precipitation_sum'],
            mode='lines', name=dist_name, legendgroup=dist_name,
            showlegend=show_legend_flag, line=line_style_district,
            hovertemplate=f"<b>{dist_name}</b><br>Crop Year: %{{x}}<br>Precipitation: %{{y:.1f}} mm<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Trace B: Runoff
    fig.add_trace(
        go.Scatter(
            x=dist_data['Crop_Year'], y=dist_data['runoff_sum'],
            mode='lines', name=dist_name, legendgroup=dist_name,
            showlegend=False, line=line_style_district,
            hovertemplate=f"<b>{dist_name}</b><br>Crop Year: %{{x}}<br>Runoff Q: %{{y:.1f}} mm<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Trace C: Triggers (Moved to Row 4)
    fig.add_trace(
        go.Scatter(
            x=dist_data['Crop_Year'], y=dist_data['trigger_count'],
            mode='lines', name=dist_name, legendgroup=dist_name,
            showlegend=False, line=line_style_district,
            hovertemplate=f"<b>{dist_name}</b><br>Crop Year: %{{x}}<br>Trigger Days: %{{y}} days<extra></extra>"
        ),
        row=4, col=1
    )
    
    # Trace D: SSI (Moved to Row 3)
    fig.add_trace(
        go.Scatter(
            x=dist_data['Crop_Year'], y=dist_data['ssi_peak'],
            mode='lines', name=dist_name, legendgroup=dist_name,
            showlegend=False, line=line_style_district,
            hovertemplate=f"<b>{dist_name}</b><br>Crop Year: %{{x}}<br>Peak SSI: %{{y:.3f}}<extra></extra>"
        ),
        row=3, col=1
    )

# Add prominent national averages to each panel (ensemble mean trends)
# Panel A: Precipitation average
fig.add_trace(
    go.Scatter(
        x=national_annual['Crop_Year'], y=national_annual['precipitation_sum'],
        mode='lines+markers', name='National Average (Precipitation)', legendgroup='National Average',
        showlegend=True, line=dict(width=3.5, color=COLOR_PRECIP_AVG), marker=dict(size=6, color=COLOR_PRECIP_AVG),
        hovertemplate="<b>National Average</b><br>Crop Year: %{x}<br>Avg Precipitation: %{y:.1f} mm<extra></extra>"
    ),
    row=1, col=1
)

# Panel B: Runoff average
fig.add_trace(
    go.Scatter(
        x=national_annual['Crop_Year'], y=national_annual['runoff_sum'],
        mode='lines+markers', name='National Average (Runoff)', legendgroup='National Average',
        showlegend=False, line=dict(width=3.5, color=COLOR_RUNOFF_AVG), marker=dict(size=6, color=COLOR_RUNOFF_AVG),
        hovertemplate="<b>National Average</b><br>Crop Year: %{x}<br>Avg Runoff Q: %{y:.1f} mm<extra></extra>"
    ),
    row=2, col=1
)

# Panel D: Trigger days average (Moved to Row 4)
fig.add_trace(
    go.Scatter(
        x=national_annual['Crop_Year'], y=national_annual['trigger_count'],
        mode='lines+markers', name='National Average (Triggers)', legendgroup='National Average',
        showlegend=False, line=dict(width=3.5, color=COLOR_TRIGGER_AVG), marker=dict(size=6, color=COLOR_TRIGGER_AVG),
        hovertemplate="<b>National Average</b><br>Crop Year: %{x}<br>Avg Trigger Days: %{y:.2f} days<extra></extra>"
    ),
    row=4, col=1
)

# Panel C: SSI average with transparent anomaly area fill to baseline (y=0) (Moved to Row 3)
fig.add_trace(
    go.Scatter(
        x=national_annual['Crop_Year'], y=national_annual['ssi_peak'],
        mode='lines+markers', name='National Average (Peak SSI)', legendgroup='National Average',
        showlegend=False, 
        line=dict(width=3.5, color=COLOR_SSI_AVG), 
        marker=dict(size=6, color=COLOR_SSI_AVG),
        fill='tozeroy',
        fillcolor='rgba(37, 99, 235, 0.15)', # Soft transparent blue fill for anomaly visual
        hovertemplate="<b>National Average</b><br>Crop Year: %{x}<br>Avg Peak SSI: %{y:.3f}<extra></extra>"
    ),
    row=3, col=1
)

# Update layout for premium design and light theme
fig.update_layout(
    template="plotly_white",
    height=1300,
    title={
        'text': "Zambia Agricultural Flood Risk Model — 25-Year Seasonal Climatological Trends (2000–2024)<br>"
                "<span style='font-size:12px; color:#64748b;'>Rural Saturation Flood Monitoring (Regime B) — 70 Agricultural Districts</span>",
        'y': 0.98,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {'size': 20, 'family': 'Inter, sans-serif', 'color': '#0f172a'}
    },
    hovermode="x unified",
    paper_bgcolor='#ffffff',
    plot_bgcolor=COLOR_BG,
    font_family="Inter, sans-serif",
    font_color='#0f172a',
    margin=dict(l=60, r=40, t=100, b=40),
    legend=dict(
        title=dict(text="Agricultural Districts", font=dict(size=12, family="Inter, sans-serif")),
        orientation="v",
        yanchor="top",
        y=1.0,
        xanchor="left",
        x=1.02,
        font=dict(size=10)
    )
)

# Calculate long-term national average baselines and peak flood year
long_term_precip = national_annual['precipitation_sum'].mean()
long_term_runoff = national_annual['runoff_sum'].mean()
long_term_triggers = national_annual['trigger_count'].mean()
peak_year = int(national_annual.loc[national_annual['trigger_count'].idxmax(), 'Crop_Year'])

# Add horizontal baselines to each panel
fig.add_hline(
    y=long_term_precip, 
    line_dash="dash", 
    line_color="#475569", 
    line_width=1.5,
    annotation_text=f"Long-term National Mean ({long_term_precip:.1f} mm)", 
    annotation_position="top left",
    annotation_font=dict(size=10, family="Inter, sans-serif", color="#475569"),
    row=1, col=1
)

fig.add_hline(
    y=long_term_runoff, 
    line_dash="dash", 
    line_color="#b45309", 
    line_width=1.5,
    annotation_text=f"Long-term National Mean ({long_term_runoff:.1f} mm)", 
    annotation_position="top left",
    annotation_font=dict(size=10, family="Inter, sans-serif", color="#b45309"),
    row=2, col=1
)

# Panel C (SSI): Neutral baseline at 0.0 and extreme saturation flood threshold at 1.5 (Moved to Row 3)
fig.add_hline(
    y=0.0, 
    line_color="#64748b", 
    line_width=1.2,
    line_dash="solid", 
    annotation_text="Climatological Neutral Baseline (0.0)", 
    annotation_position="bottom left",
    annotation_font=dict(size=10, family="Inter, sans-serif", color="#64748b"),
    row=3, col=1
)

fig.add_hline(
    y=1.5, 
    line_dash="dash", 
    line_color="#dc2626", 
    line_width=1.5,
    annotation_text="Extreme Saturation Threshold (1.5)", 
    annotation_position="top left",
    annotation_font=dict(size=10, family="Inter, sans-serif", color="#dc2626"),
    row=3, col=1
)

# Panel D (Triggers): Long-term triggers mean (Moved to Row 4)
fig.add_hline(
    y=long_term_triggers, 
    line_dash="dash", 
    line_color="#047857", 
    line_width=1.5,
    annotation_text=f"Long-term National Mean ({long_term_triggers:.2f} days)", 
    annotation_position="top left",
    annotation_font=dict(size=10, family="Inter, sans-serif", color="#047857"),
    row=4, col=1
)

# Add vertical peak flood year line across all 4 subplots
for r in range(1, 5):
    fig.add_vline(
        x=peak_year, 
        line_dash="dot", 
        line_color="#ef4444", 
        line_width=1.5,
        annotation_text=f"Peak Flood Season ({peak_year}/{str(peak_year+1)[2:]})" if r == 1 else None, 
        annotation_position="top right",
        annotation_font=dict(size=10, family="Inter, sans-serif", color="#ef4444"),
        row=r, col=1
    )

# Update axes titles and grids
fig.update_yaxes(title_text="Precipitation Sum (mm)", row=1, col=1, gridcolor=COLOR_GRID, linecolor='#cbd5e1')
fig.update_yaxes(title_text="Runoff Q Sum (mm)", row=2, col=1, gridcolor=COLOR_GRID, linecolor='#cbd5e1')
fig.update_yaxes(title_text="Peak 3-Day Mean SSI", row=3, col=1, gridcolor=COLOR_GRID, linecolor='#cbd5e1')
fig.update_yaxes(title_text="Trigger Days (Count)", row=4, col=1, gridcolor=COLOR_GRID, linecolor='#cbd5e1')

for r in range(1, 5):
    fig.update_xaxes(
        gridcolor=COLOR_GRID,
        linecolor='#cbd5e1',
        tickmode='array',
        tickvals=crop_years,
        ticktext=[f"{y}/{str(y+1)[2:]}" for y in crop_years],
        tickangle=45,
        row=r, col=1
    )

fig.update_xaxes(title_text="Crop Year (November to April Season)", row=4, col=1)

# Save HTML file
dashboard_file = os.path.join(viz_folder, "Zambia_Agri_Annual_Dashboard.html")
fig.write_html(dashboard_file, include_plotlyjs='cdn')

print(f"\n🚀 SUCCESS: Interactive 4-Panel Dashboard created successfully!")
print(f"Output File Location: {dashboard_file}")
