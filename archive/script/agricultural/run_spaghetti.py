import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE, "output", "agricultural", "visualizations")
os.makedirs(OUT_DIR, exist_ok=True)

pv_summary_csv = os.path.join(BASE, "output", "agricultural", "SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")
df_pv = pd.read_csv(pv_summary_csv)

# 1. Prepare the Data
# Ensure we have the full range of years for every district
districts_list = df_pv[['COUNTRY', 'ADM_NAME']].drop_duplicates()
years = list(range(2007, 2026))

grid = pd.MultiIndex.from_product(
    [districts_list['ADM_NAME'], years], 
    names=['ADM_NAME', 'crop_year']
).to_frame(index=False)

grid = grid.merge(districts_list, on='ADM_NAME', how='left')

# Merge with your actual flood data (using max consecutive days)
df_plot = grid.merge(
    df_pv[['ADM_NAME', 'crop_year', 'total_flood_streak_days']], 
    on=['ADM_NAME', 'crop_year'], 
    how='left'
).fillna(0)

# 2. Calculate the Overall Africa Average
overall_avg = df_plot.groupby('crop_year')['total_flood_streak_days'].mean().reset_index()

# 3. Optimization Trick: Combine all 3,333 districts into ONE background trace
# This prevents the browser from lagging
x_grey = []
y_grey = []

for dist in districts_list['ADM_NAME'].unique():
    d_df = df_plot[df_plot['ADM_NAME'] == dist].sort_values('crop_year')
    x_grey.extend(d_df['crop_year'].tolist())
    y_grey.extend(d_df['total_flood_streak_days'].tolist())
    # Add None to break the line so it doesn't connect the end of one district to the start of the next
    x_grey.append(None)
    y_grey.append(None)

# 4. Create the Figure
fig = go.Figure()

# Add the FAINT GREY background (All Districts)
fig.add_trace(go.Scatter(
    x=x_grey,
    y=y_grey,
    mode='lines',
    line=dict(color='rgba(200, 200, 200, 0.08)', width=0.5), # Extremely faint for 3,000+ lines
    name='Individual Districts',
    hoverinfo='skip', # Don't show hover for background lines to keep it clean
    showlegend=False
))

# Add the BOLD ORANGE line (All Africa Average)
fig.add_trace(go.Scatter(
    x=overall_avg['crop_year'],
    y=overall_avg['total_flood_streak_days'],
    mode='lines+markers',
    line=dict(color='#FF8C00', width=4), # Bold Orange
    marker=dict(size=8, symbol='circle'),
    name='Avg. Flood Days (All Africa)',
    showlegend=True
))

# 5. Styling to match your Index 2 image
fig.update_layout(
    title="<b>Index 3: All-Africa Agricultural Flood Risk (2007-2025)</b><br>Max Consecutive Days where SWI > 95th Percentile",
    xaxis_title="Crop Year",
    yaxis_title="Number of Consecutive Days",
    template="plotly_white",
    hovermode="x",
    xaxis=dict(
        tickmode='linear', 
        dtick=1, 
        gridcolor='rgba(230, 230, 230, 0.5)',
        range=[2006.5, 2025.5]
    ),
    yaxis=dict(
        gridcolor='rgba(230, 230, 230, 0.5)',
        zerolinecolor='rgba(200, 200, 200, 0.8)',
        range=[0, df_plot['total_flood_streak_days'].max() + 5]
    ),
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99,
        bgcolor="rgba(255, 255, 255, 0.7)"
    )
)

html_path = os.path.join(OUT_DIR, "SWI_Flood_Spaghetti_Plot.html")
fig.write_html(html_path)
print(f"Updated Spaghetti Plot saved to: {html_path}")
