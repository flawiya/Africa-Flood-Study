"""
generate_clustering_methods_dashboard.py
========================================
Generates an ultra-fast multi-method 60% Geography / 40% Weather weighted spatial regionalization dashboard
for Pan-African Parametric Flood Risk Study (1,638 districts).

Restricted to 2 Methods (K = 14, 15, 16):
1. Spatially Constrained Average Linkage (Initial Underwriting Baseline) (K=14, 15, 16)
2. Spatially Constrained Ward Minimum Variance Linkage (K=14, 15, 16)

Saves output HTML to:
`output/agricultural/meeting_30th_july_output/MultiMethod_Clustering_Dashboard.html`
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import kneighbors_graph
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "output", "agricultural", "Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, "data", "africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print("1. Loading dataset & computing Option 2 5-day flood metrics...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year
    
    plant_doy = pd.to_numeric(df["planting"], errors='coerce')
    harvest_doy = pd.to_numeric(df["harvest"], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1
    
    df = df[~df["crop_year"].isin([2007, 2025])]
    df = df[df["COUNTRY"] != "Morocco"]
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)
    
    df["block"] = (df["flag_opt2"] != df.groupby(["COUNTRY", "ADM_NAME"])["flag_opt2"].shift()).cumsum()
    block_info = df[df["flag_opt2"]].groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year", "block"]).size().reset_index(name="streak_days")
    valid_info = block_info[block_info["streak_days"] >= 5]
    
    seasonal_agg = valid_info.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        triggered=("streak_days", lambda x: 1 if len(x) > 0 else 0),
        max_streak=("streak_days", "max"),
        sum_streak_days=("streak_days", "sum")
    ).reset_index()

    all_districts = df[["ISO3", "COUNTRY", "ADM_NAME"]].drop_duplicates()
    all_years = pd.DataFrame({"crop_year": df["crop_year"].unique()})
    master_grid = all_districts.merge(all_years, how="cross")
    
    full_seasonal = master_grid.merge(seasonal_agg, on=["ISO3", "COUNTRY", "ADM_NAME", "crop_year"], how="left").fillna(0)
    full_seasonal["ADM_NAME"] = full_seasonal["ADM_NAME"].astype(str).str.strip().str.upper()

    binary_pivot = full_seasonal.pivot_table(index="ADM_NAME", columns="crop_year", values="triggered").fillna(0)
    
    district_profile = full_seasonal.groupby("ADM_NAME").agg(
        trigger_freq=("triggered", "mean"),
        overall_max_duration=("max_streak", "max"),
        avg_annual_flood_days=("sum_streak_days", "mean")
    )

    print("2. Aligning spatial geometries & computing projected centroids...", flush=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["ADM_NAME"] = gdf["ADM_NAME"].astype(str).str.strip().str.upper()
    gdf_unique = gdf.drop_duplicates(subset="ADM_NAME").set_index("ADM_NAME").to_crs(epsg=3857)
    
    common = sorted(list(set(binary_pivot.index) & set(gdf_unique.index)))
    binary_pivot = binary_pivot.loc[common]
    district_profile = district_profile.loc[common]
    gdf_c = gdf_unique.loc[common]

    centroids = gdf_c.centroid
    coords = np.column_stack([centroids.x, centroids.y])
    
    print("3. Building 60% Geography / 40% Weather Feature Space & Jaccard Co-Failure Matrix...", flush=True)
    scaler_geo = StandardScaler()
    coords_std = scaler_geo.fit_transform(coords)
    geo_dist = squareform(pdist(coords_std, metric="euclidean"))
    geo_dist_norm = geo_dist / geo_dist.max()

    # Jaccard Co-Occurrence Distance across 2008-2024 flood events
    jaccard_dist = squareform(pdist(binary_pivot.values, metric="jaccard"))
    weather_std = StandardScaler().fit_transform(district_profile.values)
    dur_dist = squareform(pdist(weather_std, metric="euclidean"))
    dur_dist_norm = dur_dist / dur_dist.max()
    
    weather_dist = (0.60 * jaccard_dist) + (0.40 * dur_dist_norm)
    weather_dist_norm = weather_dist / weather_dist.max()

    COMBINED_DIST = (0.60 * geo_dist_norm) + (0.40 * weather_dist_norm)
    F_weighted = np.hstack([0.60 * coords_std, 0.40 * weather_std])
    spatial_graph_15 = kneighbors_graph(coords, n_neighbors=15, mode="connectivity")

    df_out = pd.DataFrame({"ADM_NAME": common})
    df_out["COUNTRY"] = gdf_c["COUNTRY"].values
    df_out["trigger_freq"] = district_profile["trigger_freq"].values
    df_out["max_dur"] = district_profile["overall_max_duration"].values
    df_out["avg_days"] = district_profile["avg_annual_flood_days"].values

    models_meta = {}

    print("4. Executing 2 Core Spatial Linkage Models (K=14, 15, 16)...", flush=True)

    # Method 1: Average Linkage Baseline
    for k in [14, 15, 16]:
        agg = AgglomerativeClustering(n_clusters=k, metric="precomputed", connectivity=spatial_graph_15, linkage="average")
        labels = agg.fit_predict(COMBINED_DIST)
        sil = silhouette_score(COMBINED_DIST, labels, metric="precomputed")
        col_key = f"m1_avg_k{k}"
        df_out[col_key] = labels
        models_meta[col_key] = {
            "name": f"Method 1: Average Linkage Baseline (K={k})",
            "method_group": "Method 1: Average Linkage Baseline",
            "k": k,
            "sil": round(float(sil), 4),
            "spatial_constraint": "15-Nearest Neighbors Spatial Connectivity Graph (60% Geography / 40% Weather Profile)",
            "underwriting_purpose": "Groups neighboring districts that behave similarly by combining physical geographic location (60% weight) with historical flood event co-occurrence during 2008–2024 (40% weight). It merges adjacent districts based on their overall average similarity, forming balanced regional risk pools where districts share consistent background flood risk.",
            "citation": "Murtagh, F. & Legendre, P. (2014). Ward's Hierarchical Agglomerative Clustering Method. Journal of Classification, 31(3), 274–295."
        }

    # Method 2: Ward Minimum Variance Linkage
    for k in [14, 15, 16]:
        ward = AgglomerativeClustering(n_clusters=k, linkage="ward", connectivity=spatial_graph_15)
        labels = ward.fit_predict(F_weighted)
        sil = silhouette_score(F_weighted, labels)
        col_key = f"m2_ward_k{k}"
        df_out[col_key] = labels
        models_meta[col_key] = {
            "name": f"Method 2: Ward Minimum Variance Linkage (K={k})",
            "method_group": "Method 2: Ward Minimum Variance Linkage",
            "k": k,
            "sil": round(float(sil), 4),
            "spatial_constraint": "15-Nearest Neighbors Spatial Connectivity Graph (60% Geography / 40% Weather Profile)",
            "underwriting_purpose": "Groups neighboring districts by minimizing flood risk differences inside each cluster. It forces districts in the same risk pool to have nearly identical historical trigger frequencies and flood durations (Option 2 5-day rule). This prevents mixing high-risk districts with low-risk districts, producing highly uniform risk pools for underwriting.",
            "citation": "Ward, J.H. (1963). Hierarchical Grouping to Optimize an Objective Function. Journal of the American Statistical Association, 58(301), 236–244."
        }

    print("5. Preparing Ultra-Fast Single-Layer Map & Client-Side JS Switcher...", flush=True)

    gdf_map = gdf_c.to_crs(epsg=4326).reset_index()
    gdf_map = gdf_map.merge(df_out, on="ADM_NAME")
    geojson_dict = json.loads(gdf_map.set_index('ADM_NAME').to_json())

    model_keys = list(models_meta.keys())
    
    all_cluster_data = {}
    country_col = gdf_map['COUNTRY_x'] if 'COUNTRY_x' in gdf_map.columns else gdf_map['COUNTRY']

    for key in model_keys:
        labels = gdf_map[key]
        custom_data = np.stack([
            country_col,
            labels.apply(lambda c: f"Zone {int(c)+1:02d}"),
            gdf_map['trigger_freq'].apply(lambda v: f"{v:.3f}"),
            gdf_map['max_dur'].apply(lambda v: f"{int(v)} days"),
            gdf_map['avg_days'].apply(lambda v: f"{v:.1f} days")
        ], axis=-1).tolist()
        
        all_cluster_data[key] = {
            "z": labels.tolist(),
            "customdata": custom_data
        }

    default_key = "m1_avg_k15"
    init_z = all_cluster_data[default_key]["z"]
    init_customdata = all_cluster_data[default_key]["customdata"]

    fig = go.Figure()
    fig.add_trace(
        go.Choroplethmap(
            geojson=geojson_dict,
            locations=gdf_map['ADM_NAME'],
            z=init_z,
            colorscale='Turbo',
            showscale=False,
            marker_line_width=0.3,
            marker_line_color='rgba(0,0,0,0.35)',
            marker_opacity=0.85,
            customdata=init_customdata,
            hovertemplate=(
                "<b>%{location}</b> (%{customdata[0]})<br>" +
                "Risk Zone: <b>%{customdata[1]}</b><br>" +
                "Trigger Frequency: <b>%{customdata[2]} / yr</b><br>" +
                "Max Flood Streak: <b>%{customdata[3]}</b><br>" +
                "Avg Annual Flood Days: <b>%{customdata[4]}</b>" +
                "<extra></extra>"
            ),
            name="Parametric Risk Map"
        )
    )

    fig.update_layout(
        map=dict(
            style='carto-positron',
            center=dict(lat=2.0, lon=18.0),
            zoom=2.3
        ),
        height=680,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    plotly_div = fig.to_html(full_html=False, include_plotlyjs='cdn', div_id="cluster_map_div")

    cluster_profiles = {}
    for key in model_keys:
        grouped = df_out.groupby(key).agg(
            district_count=("ADM_NAME", "count"),
            mean_trigger_freq=("trigger_freq", "mean"),
            mean_max_streak=("max_dur", "mean")
        ).reset_index()
        cluster_profiles[key] = {
            "zones": [f"Zone {int(r[key])+1:02d}" for _, r in grouped.iterrows()],
            "district_counts": grouped["district_count"].tolist(),
            "mean_trigger_freqs": [round(float(v), 4) for v in grouped["mean_trigger_freq"].tolist()],
            "mean_max_streaks": [round(float(v), 1) for v in grouped["mean_max_streak"].tolist()]
        }

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>60/40 Weighted Spatial Regionalization Dashboard — ASR Study</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --accent-blue: #38bdf8;
            --accent-indigo: #6366f1;
            --accent-emerald: #34d399;
            --accent-amber: #fbbf24;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
        
        body {{
            background-color: var(--bg-primary);
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header-title h1 {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header-title p {{
            font-size: 0.825rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .badge-tag {{
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.4);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .dashboard-container {{
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 16px;
            padding: 16px;
            flex: 1;
        }}

        .sidebar-panel {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }}

        .card-header {{
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--accent-blue);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .select-group {{
            margin-bottom: 12px;
        }}
        label {{
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}
        select {{
            width: 100%;
            background-color: #0f172a;
            color: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 0.85rem;
            font-weight: 500;
            outline: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        select:hover, select:focus {{
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }}

        .info-box {{
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-left: 4px solid var(--accent-indigo);
            border-radius: 10px;
            padding: 16px;
        }}
        .info-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        .info-metric-badge {{
            display: inline-block;
            background: rgba(52, 211, 153, 0.15);
            color: var(--accent-emerald);
            border: 1px solid rgba(52, 211, 153, 0.3);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 6px;
            margin-bottom: 12px;
        }}
        .info-section {{
            margin-bottom: 10px;
        }}
        .info-section-title {{
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--accent-amber);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }}
        .info-text {{
            font-size: 0.8rem;
            color: #cbd5e1;
            line-height: 1.45;
        }}
        .code-block {{
            background-color: #090d16;
            border: 1px solid #334155;
            color: #38bdf8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.725rem;
            padding: 8px;
            border-radius: 6px;
            margin-top: 4px;
            word-break: break-all;
        }}

        .main-panel {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .map-card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            height: 780px;
            position: relative;
        }}

        footer {{
            text-align: center;
            padding: 12px;
            font-size: 0.75rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>

    <header>
        <div class="header-title">
            <h1>🌐 60/40 Weighted Spatial Regionalization Dashboard</h1>
            <p>Comparing Average Linkage vs Ward Minimum Variance (K = 14, 15, 16) — Option 2 Event Co-Occurrence</p>
        </div>
        <div class="badge-tag">ASR Reinsurance Research</div>
    </header>

    <div class="dashboard-container">
        <div class="sidebar-panel">
            <div class="card">
                <div class="card-header">
                    <span>🎛️ Spatial Method Selector</span>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">K=14, 15, 16</span>
                </div>
                
                <div class="select-group">
                    <label for="methodSelect">Spatial Regionalization Method</label>
                    <select id="methodSelect" onchange="updateDashboard()">
                        <optgroup label="1. Average Linkage Baseline">
                            <option value="m1_avg_k15" selected>Average Linkage (K=15)</option>
                            <option value="m1_avg_k14">Average Linkage (K=14)</option>
                            <option value="m1_avg_k16">Average Linkage (K=16)</option>
                        </optgroup>
                        <optgroup label="2. Ward Minimum Variance Linkage">
                            <option value="m2_ward_k15">Ward Minimum Variance (K=15)</option>
                            <option value="m2_ward_k14">Ward Minimum Variance (K=14)</option>
                            <option value="m2_ward_k16">Ward Minimum Variance (K=16)</option>
                        </optgroup>
                    </select>
                </div>
            </div>

            <div class="card info-box">
                <div class="info-title" id="infoTitle">Method Title</div>
                <div class="info-metric-badge" id="infoMetric">Silhouette Score: 0.0000</div>

                <div class="info-section">
                    <div class="info-section-title">🔗 Spatial Constraint & Event Co-Occurrence</div>
                    <div class="info-text" id="infoSpatialConstraint">Constraint</div>
                </div>

                <div class="info-section">
                    <div class="info-section-title">💡 How Districts Are Clustered & Underwriting Purpose</div>
                    <div class="info-text" id="infoPurpose">Underwriting Purpose</div>
                </div>

                <div class="info-section" style="margin-bottom:0;">
                    <div class="info-section-title">📚 Citation & Reference</div>
                    <div class="info-text" style="font-size: 0.725rem; font-style: italic; color: #94a3b8;" id="infoCitation">Citation</div>
                </div>
            </div>
        </div>

        <div class="main-panel">
            <div class="map-card">
                {plotly_div}
            </div>
        </div>
    </div>

    <footer>
        Africa Specialty Risks (ASR) Parametric Research Study • Master Daily Soil Water Index Dataset (2007–2025) • 1,638 Agricultural Districts
    </footer>

    <script>
        const modelsMeta = {json.dumps(models_meta)};
        const allClusterData = {json.dumps(all_cluster_data)};

        function updateDashboard() {{
            const selectedKey = document.getElementById("methodSelect").value;
            const meta = modelsMeta[selectedKey];
            
            document.getElementById("infoTitle").innerText = meta.name;
            document.getElementById("infoMetric").innerText = `Spatial Silhouette Score: ${{meta.sil}} | Clusters (K): ${{meta.k}}`;
            document.getElementById("infoSpatialConstraint").innerText = meta.spatial_constraint;
            document.getElementById("infoPurpose").innerText = meta.underwriting_purpose;
            document.getElementById("infoCitation").innerText = meta.citation;

            const newData = allClusterData[selectedKey];
            Plotly.restyle("cluster_map_div", {{
                z: [newData.z],
                customdata: [newData.customdata]
            }}, [0]);
        }}

        document.addEventListener("DOMContentLoaded", function() {{
            updateDashboard();
        }});
    </script>
</body>
</html>
"""

    out_map_path = os.path.join(OUT_DIR, "MultiMethod_Clustering_Dashboard.html")
    with open(out_map_path, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"Successfully generated 60/40 2-method dashboard: {out_map_path}", flush=True)

if __name__ == "__main__":
    main()
