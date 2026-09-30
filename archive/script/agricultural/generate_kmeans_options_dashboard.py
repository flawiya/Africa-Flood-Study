"""
generate_kmeans_options_dashboard.py
====================================
Runs K-Means clustering (K=2, K=3, K=4) on Option 1 (99th Percentile),
Option 2 (95th %ile + Absolute 85%), and Option 3 (Pure Absolute 85%) summary data.

For each Option and each K:
  - Aggregates district-level metrics across 2007-2025.
  - Clusters districts into K clusters.
  - Computes the annual trajectory (mean flood days per year 2007-2025) for each cluster.
  - Generates interactive Plotly HTML cluster maps and cluster trajectory charts.
  - Outputs HTML reports to `output/agricultural/meeting_24th_july_output/`
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ----------------- Setup Paths -----------------
BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
IN_DIR   = os.path.join(BASE_DIR, "output", "agricultural", "meeting_17th_july_output")
OUT_DIR  = os.path.join(BASE_DIR, "output", "agricultural", "meeting_24th_july_output")
SHP_PATH = os.path.join(BASE_DIR, "data", "africa_agricultural_domain_2019.shp")
os.makedirs(OUT_DIR, exist_ok=True)

print("Starting K-Means Clustering on Meeting Options...", flush=True)

# Load shapefile once
gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
gdf = gdf[gdf['COUNTRY'] != 'Morocco'].copy()
gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)
geojson_dict = json.loads(gdf.set_index('ADM_NAME').to_json())

# Defined Options
options_config = [
    {
        "name": "Option 1 (99th Percentile)",
        "short_id": "Option1_99P",
        "csv_file": os.path.join(IN_DIR, "option1_99th_percentile_summary.csv"),
        "rule_desc": "SWI >= P99 (>= 7 Consec Days)"
    },
    {
        "name": "Option 2 (95th %ile + Absolute SWI >= 85%)",
        "short_id": "Option2_95P_Abs85",
        "csv_file": os.path.join(IN_DIR, "option2_95th_plus_absolute_summary.csv"),
        "rule_desc": "SWI >= P95 & SWI >= 85% (>= 7 Consec Days)"
    },
    {
        "name": "Option 3 (Pure Absolute SWI >= 85%)",
        "short_id": "Option3_Abs85",
        "csv_file": os.path.join(IN_DIR, "option3_pure_absolute_summary.csv"),
        "rule_desc": "SWI >= 85% (>= 7 Consec Days)"
    }
]

# Simple, robust implementation of K-Means clustering (using K-Means++ initialization)
def run_kmeans(X, k, seed=42):
    np.random.seed(seed)
    n_samples, n_features = X.shape
    # Z-score normalize
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std[std == 0] = 1.0
    X_norm = (X - mean) / std
    
    # Initialize centroids using kmeans++
    centroids = [X_norm[np.random.choice(n_samples)]]
    for _ in range(1, k):
        dists = np.array([min([np.sum((x - c)**2) for c in centroids]) for x in X_norm])
        probs = dists / dists.sum()
        cumprobs = np.cumsum(probs)
        r = np.random.rand()
        for i, p in enumerate(cumprobs):
            if r < p:
                centroids.append(X_norm[i])
                break
    centroids = np.array(centroids)
    
    # Iterate
    labels = np.zeros(n_samples, dtype=int)
    for _ in range(50):
        # Assign
        dists = np.linalg.norm(X_norm[:, np.newaxis] - centroids, axis=2)
        new_labels = np.argmin(dists, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        # Update
        for j in range(k):
            mask = (labels == j)
            if np.any(mask):
                centroids[j] = np.mean(X_norm[mask], axis=0)
                
    # Sort cluster labels by mean risk level so Cluster 0 is lowest risk, Cluster K-1 is highest risk
    cluster_severity = [np.mean(X_norm[labels == j, 0]) for j in range(k)]
    rank_order = np.argsort(cluster_severity)
    remap = {old_l: new_l for new_l, old_l in enumerate(rank_order)}
    labels = np.array([remap[l] for l in labels])
    
    return labels

# Palette for clusters
COLOR_PALETTE = ['#3b82f6', '#eab308', '#ef4444', '#8b5cf6', '#10b981']
CLUSTER_NAMES = {
    2: ["Low Flood Hazard", "High Flood Hazard"],
    3: ["Low Flood Hazard", "Moderate Flood Hazard", "Severe Flood Hazard"],
    4: ["Low Flood Hazard", "Moderate Flood Hazard", "High Flood Hazard", "Severe / Frequent Disaster Hazard"]
}

# Main loop over Options and K values
summary_results = []

for opt in options_config:
    if not os.path.isfile(opt["csv_file"]):
        print(f"Skipping {opt['name']} - file missing: {opt['csv_file']}", flush=True)
        continue
        
    print(f"\nProcessing {opt['name']}...", flush=True)
    df_opt = pd.read_csv(opt["csv_file"])
    df_opt['crop_year'] = df_opt['crop_year'].astype(int)
    years = sorted(df_opt['crop_year'].unique())
    
    # Aggregate district features for clustering
    dist_features = df_opt.groupby(['ISO3', 'COUNTRY', 'ADM_NAME']).agg(
        avg_flood_days=('flood_days_7plus', 'mean'),
        max_flood_days=('flood_days_7plus', 'max'),
        avg_max_consec=('max_consec_days', 'mean'),
        total_events=('num_flood_events', 'sum'),
        mean_swi=('mean_swi', 'mean'),
        p95_swi=('max_swi', lambda x: np.percentile(x, 95))
    ).reset_index()
    
    X = dist_features[['avg_flood_days', 'max_flood_days', 'avg_max_consec', 'total_events']].values
    
    for k in [2, 3, 4]:
        print(f"  Clustering K={k}...", flush=True)
        labels = run_kmeans(X, k)
        col_name = f"cluster_k{k}"
        dist_features[col_name] = labels
        
        # Merge cluster labels back into yearly dataset
        df_merged = df_opt.merge(dist_features[['ADM_NAME', col_name]], on='ADM_NAME', how='left')
        
        # Calculate Yearly Cluster Trajectories (mean flood days for each cluster per year)
        trajectories = df_merged.groupby(['crop_year', col_name])['flood_days_7plus'].mean().unstack(level=col_name).fillna(0)
        
        # ── Build Combined Interactive Plotly Figure (Panel 1: Map, Panel 2: Trajectories) ──
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.55, 0.45],
            specs=[[{"type": "map"}], [{"type": "xy"}]],
            subplot_titles=[
                f"District Hazard Cluster Map (K={k})",
                f"Cluster Trajectories over Time (2007–2025) — Average Annual Flood Days"
            ],
            vertical_spacing=0.1
        )
        
        # Add GeoJSON Choropleth Map for Clusters
        dist_meta = dist_features.merge(gdf[['ADM_NAME']], on='ADM_NAME', how='inner')
        
        for c in range(k):
            c_name = CLUSTER_NAMES[k][c]
            c_color = COLOR_PALETTE[c]
            c_districts = dist_features[dist_features[col_name] == c]
            
            # Map trace for cluster c
            sub_gdf = gdf[gdf['ADM_NAME'].isin(c_districts['ADM_NAME'])].copy()
            c_geojson = json.loads(sub_gdf.set_index('ADM_NAME').to_json())
            
            fig.add_trace(
                go.Choroplethmap(
                    geojson=c_geojson,
                    locations=c_districts['ADM_NAME'].tolist(),
                    z=[c] * len(c_districts),
                    colorscale=[[0, c_color], [1, c_color]],
                    showscale=False,
                    name=f"Cluster {c+1}: {c_name}",
                    legendgroup=f"c{c}",
                    marker_line_width=0.4,
                    marker_line_color='rgba(0,0,0,0.3)',
                    marker_opacity=0.8,
                    customdata=np.stack([
                        c_districts['COUNTRY'].tolist(),
                        c_districts['avg_flood_days'].round(1).tolist(),
                        c_districts['total_events'].tolist()
                    ], axis=-1),
                    hovertemplate=(
                        "<b>%{location}</b> (%{customdata[0]})<br>"
                        f"Cluster: <b>{c+1} - {c_name}</b><br>"
                        "Avg Annual Flood Days: <b>%{customdata[1]}d</b><br>"
                        "Total Flood Events (2007-2025): <b>%{customdata[2]}</b>"
                        "<extra></extra>"
                    )
                ),
                row=1, col=1
            )
            
            # Trajectory trace for cluster c
            c_traj = trajectories[c] if c in trajectories.columns else pd.Series(0, index=years)
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=c_traj.values,
                    mode='lines+markers',
                    name=f"Cluster {c+1}: {c_name}",
                    legendgroup=f"c{c}",
                    line=dict(color=c_color, width=3),
                    marker=dict(size=7, color=c_color),
                    hovertemplate=f"<b>Cluster {c+1} ({c_name})</b><br>Year: <b>%{{x}}</b><br>Avg Flood Days: <b>%{{y:.1f}}d</b><extra></extra>"
                ),
                row=2, col=1
            )
            
        fig.update_layout(
            map=dict(style="carto-positron", center=dict(lat=2.0, lon=18.0), zoom=2.2),
            height=950,
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40)
        )
        fig.update_xaxes(title_text="Crop Year", tickmode="array", tickvals=years, row=2, col=1)
        fig.update_yaxes(title_text="Avg Flood Days per District", row=2, col=1)
        
        # Save HTML
        html_filename = f"ClusterMap_{opt['short_id']}_K{k}.html"
        html_path = os.path.join(OUT_DIR, html_filename)
        
        plotly_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config={'scrollZoom': True, 'displayModeBar': True})
        
        # Build summary table of clusters
        cluster_table_rows = ""
        for c in range(k):
            c_districts = dist_features[dist_features[col_name] == c]
            c_name = CLUSTER_NAMES[k][c]
            c_color = COLOR_PALETTE[c]
            cluster_table_rows += f"""
            <tr>
                <td><span style="display:inline-block;width:12px;height:12px;background:{c_color};border-radius:2px;margin-right:6px;"></span>Cluster {c+1}</td>
                <td><strong>{c_name}</strong></td>
                <td>{len(c_districts)}</td>
                <td>{c_districts['avg_flood_days'].mean():.1f} days/yr</td>
                <td>{c_districts['max_flood_days'].max():.0f} days</td>
                <td>{c_districts['total_events'].mean():.1f}</td>
            </tr>
            """
            
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{opt['name']} - K={k} Hazard Cluster Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
        .header {{ background: #1e293b; color: white; padding: 20px 28px; border-radius: 12px; margin-bottom: 24px; }}
        .header h1 {{ margin: 0 0 6px 0; font-size: 1.5rem; }}
        .header p {{ margin: 0; opacity: 0.8; font-size: 0.9rem; }}
        .card {{ background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th {{ background: #f1f5f9; text-align: left; padding: 10px 14px; font-size: 0.85rem; color: #475569; }}
        td {{ border-top: 1px solid #e2e8f0; padding: 10px 14px; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{opt['name']} &mdash; K-Means Hazard Clustering (K={k})</h1>
        <p>Threshold Strategy: <strong>{opt['rule_desc']}</strong> | 1,638 African Agricultural Districts (2007&ndash;2025)</p>
    </div>

    <div class="card">
        {plotly_html}
    </div>

    <div class="card">
        <h3>Cluster Summary Statistics</h3>
        <table>
            <tr>
                <th>Cluster ID</th>
                <th>Hazard Profile</th>
                <th>District Count</th>
                <th>Avg Annual Flood Days</th>
                <th>Peak Streak Duration</th>
                <th>Avg Total Events</th>
            </tr>
            {cluster_table_rows}
        </table>
    </div>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"    Saved: {html_filename}", flush=True)

print("\nAll K-Means Option dashboards generated successfully!", flush=True)
