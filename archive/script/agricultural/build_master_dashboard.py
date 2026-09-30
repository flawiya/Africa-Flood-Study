import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
SHP_PATH = os.path.join(BASE, "data", "africa_agricultural_domain_maize_calendar.shp")
CSV_PATH = os.path.join(BASE, "output", "agricultural", "SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")
OUT_HTML = os.path.join(BASE, "output", "agricultural", "visualizations", "SWI_Ultimate_Flood_Dashboard.html")
os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)

# ── 1. Load Summary Data ───────────────────────────────────────────────────
print("Loading summary data...")
df = pd.read_csv(CSV_PATH)
df['crop_year'] = df['crop_year'].astype(int)
for col in ['flood_days_7plus', 'num_flood_events_7plus', 'max_consec_days']:
    if col not in df.columns:
        df[col] = 0
df = df.fillna(0)

# ── 2. Padded Grid (every district x every year) ──────────────────────────
print("Building padded district-year grid...")
districts = df[['COUNTRY', 'ADM_NAME']].drop_duplicates()
years = sorted(df['crop_year'].unique())

grid = pd.MultiIndex.from_product(
    [districts['ADM_NAME'], years], names=['ADM_NAME', 'crop_year']
).to_frame(index=False)
grid = grid.merge(districts, on='ADM_NAME', how='left')
df_plot = grid.merge(
    df[['ADM_NAME', 'crop_year', 'COUNTRY', 'flood_days_7plus', 'num_flood_events_7plus', 'max_consec_days']],
    on=['ADM_NAME', 'crop_year'], how='left'
)
if 'COUNTRY_x' in df_plot.columns:
    df_plot['COUNTRY'] = df_plot['COUNTRY_x'].fillna(df_plot['COUNTRY_y'])
    df_plot.drop(columns=['COUNTRY_x', 'COUNTRY_y'], inplace=True)
df_plot = df_plot.fillna(0)
df_plot['crop_year'] = df_plot['crop_year'].astype(int)
print(f"  {df_plot['ADM_NAME'].nunique()} districts | {len(years)} years")

# ── 3. Simplified GeoJSON ─────────────────────────────────────────────────
print("Loading shapefile...")
gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY_x', 'geometry']]
gdf = gdf.rename(columns={'COUNTRY_x': 'COUNTRY'})
gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)
gdf = gdf[gdf['ADM_NAME'].isin(districts['ADM_NAME'])].copy()
geojson_dict = json.loads(gdf.set_index('ADM_NAME').to_json())
print(f"  {len(geojson_dict['features'])} features")

COLOR_MAX = 30

# ── 4. Animated Choropleth Map (using Mapbox for CartoDB style) ────────────
print("Building animated map...")

def make_choropleth(year_df, geojson):
    return go.Choroplethmapbox(
        geojson=geojson,
        locations=year_df['ADM_NAME'].tolist(),
        z=year_df['flood_days_7plus'].tolist(),
        colorscale="Blues",
        zmin=0,
        zmax=COLOR_MAX,
        colorbar=dict(
            title=dict(text="Days in >=7<br>Consecutive<br>Flood Streaks", font=dict(size=11)),
            tickvals=[0, 7, 14, 21, 30],
            ticktext=["0", "7", "14", "21", "30+"],
            len=0.55, x=1.0
        ),
        marker_line_width=0.4,
        marker_line_color='rgba(0,0,0,0.3)',
        marker_opacity=0.8,
        customdata=np.stack([
            year_df['COUNTRY'].tolist(),
            year_df['flood_days_7plus'].tolist(),
            year_df['max_consec_days'].tolist(),
        ], axis=-1),
        hovertemplate=(
            "<b>%{location}</b>  (%{customdata[0]})<br>"
            "<br>"
            "Days in >=7-day streaks: <b>%{customdata[1]:.0f}</b><br>"
            "Longest streak this year: <b>%{customdata[2]:.0f} days</b>"
            "<extra></extra>"
        ),
        name=""
    )

base_trace = make_choropleth(df_plot[df_plot['crop_year'] == years[0]], geojson_dict)

frames = [
    go.Frame(
        data=[make_choropleth(df_plot[df_plot['crop_year'] == yr], geojson_dict)],
        name=str(yr),
        layout=go.Layout(
            annotations=[dict(
                text=f"Year: <b>{yr}</b>",
                xref="paper", yref="paper", x=0.5, y=0.98,
                xanchor='center', font=dict(size=22, color='#0f172a'), showarrow=False,
                bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1, borderpad=4
            )]
        )
    )
    for yr in years
]

sliders = [dict(
    active=0,
    steps=[dict(
        args=[[str(yr)], dict(frame=dict(duration=600, redraw=True),
                              mode='immediate', transition=dict(duration=300))],
        label=str(yr), method='animate'
    ) for yr in years],
    x=0.1, y=-0.05, len=0.9,
    currentvalue=dict(prefix="Year: ", visible=False),
    pad=dict(b=10, t=20)
)]

fig_map = go.Figure(
    data=[base_trace], frames=frames,
    layout=go.Layout(
        mapbox=dict(
            style="carto-positron",  # CartoDB Light style exactly like the drought study
            center=dict(lat=2.0, lon=18.0),
            zoom=2.3
        ),
        updatemenus=[dict(
            type='buttons', showactive=False,
            y=-0.05, x=0.0, xanchor='left', yanchor='top',
            direction='right',
            pad={"r": 10, "t": 20},
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=700, redraw=True),
                                      fromcurrent=True, mode='immediate',
                                      transition=dict(duration=300))]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode='immediate', transition=dict(duration=0))])
            ]
        )],
        sliders=sliders,
        height=680, margin=dict(l=0, r=0, t=30, b=80),
        paper_bgcolor='white',
    )
)
print("  Map done.")

# ── 5. Spaghetti Plot with Highlighted Extremes ──────────────────────────
print("Building spaghetti plot (highlighting extremes)...")
fig_spag = go.Figure()

# Identify affected districts (any year >= 7 days)
extreme_districts = df_plot[df_plot['flood_days_7plus'] >= 7]['ADM_NAME'].unique()

for dist in sorted(df_plot['ADM_NAME'].unique()):
    d_df = df_plot[df_plot['ADM_NAME'] == dist].sort_values('crop_year')
    country = d_df['COUNTRY'].iloc[0] if len(d_df) > 0 else ''
    
    is_extreme = dist in extreme_districts
    
    # Add a tiny district-specific constant jitter so perfectly overlapping lines (like 0) can be individually hovered
    y_jitter_offset = np.random.uniform(-0.4, 0.4)
    y_jittered = d_df['flood_days_7plus'] + y_jitter_offset
    
    if is_extreme:
        line_color = 'rgba(56,189,248,0.2)' # Transparent Light Blue
        line_width = 1
        hover_marker = dict(size=5, opacity=0.7, color='rgba(56,189,248,0.8)')
    else:
        line_color = 'rgba(148,163,184,0.05)' # Faint Grey with high transparency
        line_width = 1
        hover_marker = dict(size=4, opacity=0.2, color='rgba(148,163,184,0.2)')
        
    fig_spag.add_trace(go.Scatter(
        x=d_df['crop_year'],
        y=y_jittered,
        mode='lines+markers',
        name=f"{dist} ({country})",
        showlegend=False,
        marker=hover_marker,
        line=dict(color=line_color, width=line_width),
        customdata=np.stack([
            [country] * len(d_df),
            d_df['flood_days_7plus'].tolist(),
            d_df['max_consec_days'].tolist(),
        ], axis=-1),
        hovertemplate=(
            f"<b>{dist}</b>  ({country})<br>"
            "Year: <b>%{x}</b><br>"
            "Days in >=7-day streaks: <b>%{customdata[1]:.0f}</b><br>"
            "Longest streak: <b>%{customdata[2]:.0f} days</b>"
            "<extra></extra>"
        )
    ))

# Average of Affected Districts (exclude zeros)
df_affected = df_plot[df_plot['flood_days_7plus'] >= 7]
avg_affected = df_affected.groupby('crop_year')['flood_days_7plus'].mean().reset_index()
avg_affected_full = pd.DataFrame({'crop_year': years}).merge(avg_affected, on='crop_year', how='left').fillna(0)

fig_spag.add_trace(go.Scatter(
    x=avg_affected_full['crop_year'], y=avg_affected_full['flood_days_7plus'],
    mode='lines+markers', name='Avg of Affected',
    line=dict(color='#f97316', width=4),
    marker=dict(size=8, color='#f97316', line=dict(color='white', width=1.5)),
    hovertemplate=(
        "<b>Average of Affected Districts</b><br>"
        "Year: <b>%{x}</b><br>"
        "Avg Flood Days: <b>%{y:.1f}</b>"
        "<extra></extra>"
    )
))

# Add 7-Day Threshold Line
fig_spag.add_hline(y=7, line_dash='dash', line_color='#ef4444', line_width=1.5,
                   annotation_text='7 days (Minimum Flood Threshold)',
                   annotation_position='bottom right',
                   annotation_font=dict(size=12, color='#dc2626'))

fig_spag.update_layout(
    title=dict(
        text="Flood Days per District (Extremes >40 Days Highlighted in Red)",
        font=dict(size=14, family='Inter, sans-serif')
    ),
    xaxis=dict(tickmode='array', tickvals=years, tickangle=45,
               title='Crop Year', gridcolor='#f1f5f9'),
    yaxis=dict(title='Total Days in >=7-Day Consecutive Flood Streaks', gridcolor='#f1f5f9'),
    hovermode='closest',
    height=520, template='plotly_white',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.85)'),
    margin=dict(l=70, r=20, t=60, b=80)
)
print("  Spaghetti plot done.")

# ── 7. Write HTML ─────────────────────────────────────────────────────────
print("Saving HTML...")
html_map  = fig_map.to_html(full_html=False, include_plotlyjs='cdn', config={'scrollZoom': True, 'displayModeBar': True})
html_spag = fig_spag.to_html(full_html=False, include_plotlyjs=False, config={'scrollZoom': True, 'displayModeBar': True})

with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Africa SWI Flood Dashboard (2007-2025)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: #f1f5f9; color: #0f172a; }}
    .header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
      color: white; padding: 28px 40px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .header h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 6px; }}
    .header p  {{ font-size: 0.85rem; opacity: 0.7; margin-top: 4px; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 18px; border-radius: 24px; font-size: 0.82rem; font-weight: 600;
      background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3);
      margin-top: 10px;
    }}
    .container {{ max-width: 1500px; margin: 0 auto; padding: 24px; }}
    .panel {{
      background: white; border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.07);
      padding: 20px 20px 10px; margin-bottom: 24px;
    }}
    .panel-title   {{ font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 3px; }}
    .panel-sub     {{ font-size: 0.78rem; color: #64748b; margin-bottom: 10px; line-height: 1.5; }}
    .def-box {{
      background: #fef2f2; border-left: 4px solid #ef4444;
      padding: 10px 16px; border-radius: 4px;
      font-size: 0.78rem; color: #7f1d1d; margin-bottom: 12px; line-height: 1.6;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Africa SWI Agricultural Flood Dashboard (2007-2025)</h1>
    <p>Full Crop Calendar (Planting to Harvest) &nbsp;|&nbsp; {df_plot['ADM_NAME'].nunique()} Maize Districts</p>
    <div class="badge">
      Metric: SWI &gt; P95 for &gt;=7 CONSECUTIVE Days (Severe Waterlogging, ~30-60% yield loss)
    </div>
  </div>

  <div class="container">
    <div class="panel">
      <p class="panel-title">Panel A &mdash; Animated Time-Series Map</p>
      <p class="panel-sub">
        Colour = total days in the crop year belonging to unbroken &gt;=7-day flood streaks.
        Scale fixed at 0&ndash;30 days across all years &mdash; same colour = same intensity every year.
      </p>
      <div class="def-box">
        <b>Definition:</b> For each district in each crop year, count all days that were part of an unbroken
        run of &ge;7 consecutive days where SWI continuously exceeded that district's climatological 95th percentile (P95).
        Streaks shorter than 7 days are excluded entirely.
      </div>
      {html_map}
    </div>

    <div class="panel">
      <p class="panel-title">Panel B &mdash; District Spaghetti Plot (Affected Districts Highlighted)</p>
      <p class="panel-sub">
        Faint grey lines represent districts that never flooded. <b>Light blue lines</b> highlight all districts that experienced at least 7 consecutive days of severe flooding (SWI > 95P) in any year.
        The orange line shows the <b>Average of Affected Districts</b>.
      </p>
      {html_spag}
    </div>
  </div>
</body>
</html>""")

print(f"Dashboard saved to: {OUT_HTML}")
