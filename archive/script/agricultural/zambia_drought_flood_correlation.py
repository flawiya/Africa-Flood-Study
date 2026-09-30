import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback
from scipy.stats import pearsonr

print("Starting Drought vs Flood Correlation Analysis for Zambia...")

import logging
logging.basicConfig(filename='corr_trace.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')
logging.info("Starting script...")

# ── 1. Setup Paths ────────────────────────────────────────────────────────
BASE_FLOOD = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
BASE_DROUGHT = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Drought-Study"

FILE_FLOOD = os.path.join(BASE_FLOOD, "output", "agricultural", "SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")
FILE_DROUGHT = os.path.join(BASE_DROUGHT, "outputs", "1 Africa_agricultural_districts_correlation_crop_calendar", "drought_annual.csv")

OUT_DIR = os.path.join(BASE_FLOOD, "output", "agricultural", "visualizations")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_HTML = os.path.join(OUT_DIR, "Zambia_Drought_vs_Flood_Correlation.html")

# ── 2. Load Data ─────────────────────────────────────────────────────────
print("Loading datasets...")

# Load Flood Data (SWI > P95 for >= 7 days)
df_flood = pd.read_csv(FILE_FLOOD)
df_flood = df_flood[df_flood['COUNTRY'] == 'Zambia'].copy()
df_flood = df_flood[['ADM_NAME', 'crop_year', 'flood_days_7plus']]
df_flood.rename(columns={'crop_year': 'year', 'flood_days_7plus': 'flood_days'}, inplace=True)
df_flood['year'] = df_flood['year'].astype(int)

# Load Drought Data (Gamma-SSI WMO Moderate Drought)
df_drought = pd.read_csv(FILE_DROUGHT)
# The drought script uses 'feature_id' for ADM_NAME and 'Drought_Days'
df_drought = df_drought[['feature_id', 'year', 'Drought_Days']]
df_drought.rename(columns={'feature_id': 'ADM_NAME', 'Drought_Days': 'drought_days'}, inplace=True)
df_flood['ADM_NAME'] = df_flood['ADM_NAME'].str.strip().str.title()
df_drought['ADM_NAME'] = df_drought['ADM_NAME'].str.strip().str.title()
df_drought['year'] = df_drought['year'].astype(int)

print("Flood unique names:", df_flood['ADM_NAME'].unique()[:5])
print("Drought unique names:", df_drought['ADM_NAME'].unique()[:5])
print("Flood years:", sorted(df_flood['year'].unique()))
print("Drought years:", sorted(df_drought['year'].unique()))

# ── 3. Merge Data (Overlapping years: 2007-2024/25) ──────────────────────
print("Merging data...")
logging.info(f"Flood len: {len(df_flood)}, Drought len: {len(df_drought)}")
df_merged = pd.merge(df_flood, df_drought, on=['ADM_NAME', 'year'], how='inner')
logging.info(f"Merged len: {len(df_merged)}")

if len(df_merged) == 0:
    logging.info("Error: No overlapping data found after merge. Check district names and years.")
    sys.exit(1)

min_year = df_merged['year'].min()
max_year = df_merged['year'].max()
print(f"Overlapping data found from {min_year} to {max_year} for {df_merged['ADM_NAME'].nunique()} Zambia districts.")

# ── 4. Compute Correlation per District ──────────────────────────────────
results = []
for dist in sorted(df_merged['ADM_NAME'].unique()):
    dist_df = df_merged[df_merged['ADM_NAME'] == dist]
    if len(dist_df) >= 5: # Require at least 5 years of data
        x = dist_df['flood_days'].values
        y = dist_df['drought_days'].values
        
        if dist_df['flood_days'].nunique() <= 1 or dist_df['drought_days'].nunique() <= 1:
            pearson_r = 0.0
            spearman_rho = 0.0
        else:
            # We expect ANTI-CORRELATION (negative r). High flood days -> Low drought days
            pearson_r = pearsonr(dist_df['flood_days'], dist_df['drought_days']).statistic
            x_rank = dist_df['flood_days'].rank()
            y_rank = dist_df['drought_days'].rank()
            spearman_rho = pearsonr(x_rank, y_rank).statistic
            
            if pd.isna(pearson_r): pearson_r = 0.0
            if pd.isna(spearman_rho): spearman_rho = 0.0
            
        results.append({
            'District': dist,
            'Pearson_R': pearson_r,
            'Spearman_Rho': spearman_rho,
            'Avg_Flood_Days': np.mean(x),
            'Avg_Drought_Days': np.mean(y)
        })

df_corr = pd.DataFrame(results).sort_values('Spearman_Rho')

logging.info("DEBUG 1")
# Print summary to terminal
print("\n" + "="*50)
print(f"CORRELATION SUMMARY (Zambia, {min_year}-{max_year})")
print("Expected Result: Negative correlation (Anti-correlation)")
print("="*50)
print(f"Overall average Spearman correlation: {df_corr['Spearman_Rho'].mean():.2f}")
print(f"Districts with negative (expected) correlation: {(df_corr['Spearman_Rho'] < 0).sum()} out of {len(df_corr)}")
print(f"Districts with positive (unexpected) correlation: {(df_corr['Spearman_Rho'] > 0).sum()} out of {len(df_corr)}")
print("\nTop 5 Strongest Anti-Correlations:")
print(df_corr.head(5)[['District', 'Spearman_Rho', 'Pearson_R']].to_string(index=False))

logging.info("DEBUG 2")
# Calculate overall pooled correlation
pooled_x_rank = df_merged['flood_days'].rank()
pooled_y_rank = df_merged['drought_days'].rank()
if df_merged['flood_days'].nunique() <= 1 or df_merged['drought_days'].nunique() <= 1:
    pooled_spearman = 0.0
else:
    pooled_spearman = pearsonr(pooled_x_rank, pooled_y_rank).statistic
    if pd.isna(pooled_spearman): pooled_spearman = 0.0
print(f"\nPOOLED (All Districts Combined) Spearman Correlation: {pooled_spearman:.2f}")

logging.info("DEBUG 3")
# ── 5. Generate Interactive Visualization ────────────────────────────────
print("\nGenerating interactive HTML report...")

# Save CSV of the correlations
csv_out = os.path.join(OUT_DIR, "Zambia_Drought_vs_Flood_Correlation.csv")
df_corr.to_csv(csv_out, index=False)
logging.info(f"Saved CSV data to: {csv_out}")

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.4, 0.6],
    subplot_titles=(
        "District-Level Correlation (Spearman ρ)",
        "Pooled Scatter Plot (All Zambia Districts)"
    )
)

# Panel 1: Bar chart of correlations
colors = ['#dc2626' if val > 0 else '#16a34a' for val in df_corr['Spearman_Rho']] # Green if anti-correlated, Red if positively correlated

fig.add_trace(
    go.Bar(
        y=df_corr['District'],
        x=df_corr['Spearman_Rho'],
        orientation='h',
        marker_color=colors,
        name="Spearman ρ",
        hovertemplate="<b>%{y}</b><br>Spearman ρ: %{x:.2f}<extra></extra>"
    ),
    row=1, col=1
)

# Panel 2: Overall Scatter Plot (Jittered slightly to show overlapping points)
jitter_x = df_merged['flood_days'] + np.random.uniform(-0.3, 0.3, size=len(df_merged))
jitter_y = df_merged['drought_days'] + np.random.uniform(-0.3, 0.3, size=len(df_merged))

fig.add_trace(
    go.Scatter(
        x=jitter_x,
        y=jitter_y,
        mode='markers',
        marker=dict(size=6, color='rgba(37, 99, 235, 0.5)', line=dict(width=0.5, color='white')),
        name="District-Year",
        text=df_merged['ADM_NAME'] + " (" + df_merged['year'].astype(str) + ")",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Flood Days: %{x:.0f}<br>"
            "Drought Days: %{y:.0f}<extra></extra>"
        )
    ),
    row=1, col=2
)

fig.update_layout(
    title=f"Zambia Drought vs Flood Correlation Check ({min_year}-{max_year})<br><sup>Expected: Anti-Correlation (Negative ρ) -> High flood days = Low drought days</sup>",
    height=900,
    showlegend=False,
    template="plotly_white",
    margin=dict(l=20, r=20, t=80, b=20)
)

# Add reference line at x=0 for the bar chart
fig.add_vline(x=0, line_dash="dash", line_color="black", row=1, col=1)

fig.update_xaxes(title_text="Spearman Correlation (ρ)", row=1, col=1)
fig.update_xaxes(title_text="Flood Days (>=7 Consecutive days)", row=1, col=2)
fig.update_yaxes(title_text="Drought Days", row=1, col=2)

fig.write_html(OUT_HTML, include_plotlyjs='cdn')
print(f"Saved visualization to: {OUT_HTML}")

logging.info("Done!")
