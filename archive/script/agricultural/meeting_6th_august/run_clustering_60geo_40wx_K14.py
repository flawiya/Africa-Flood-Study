"""
run_clustering_60geo_40wx_K14.py
================================
Executes Spatial Regionalization Agglomerative Risk Clustering for Option 2 5-Day Flood Model
under 60% Geographic Contiguity / 40% Weather & Event Co-occurrence weighting strictly for FORCED K = 14.

Outputs to:
  `output/agricultural/meeting_6th_august/MultiMethod_Clustering_60geo_40wx_K14.html`
  `output/agricultural/meeting_6th_august/cluster_labels_60geo_40wx_K14.json`
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\meeting_6th_august\Africa_Maize_Flood_Annual_Option2_5Day.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\meeting_6th_august")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_HTML = os.path.join(OUT_DIR, "MultiMethod_Clustering_60geo_40wx_K14.html")
OUT_JSON = os.path.join(OUT_DIR, "cluster_labels_60geo_40wx_K14.json")

WEIGHT_GEO = 0.60
WEIGHT_WX  = 0.40
TARGET_K   = 14

DISTINCT_COLORS = [
    "#e6194b", "#4363d8", "#3cb44b", "#ffe119", "#f58231", "#911eb4", "#46f0f0",
    "#f032e6", "#bcfd4c", "#9a6324", "#008080", "#e6beff", "#fffac8", "#800000"
]


def make_discrete_colorscale(k, colors):
    discrete_scale = []
    for i in range(k):
        c = colors[i % len(colors)]
        low = i / k
        high = (i + 1) / k
        discrete_scale.append([low, c])
        discrete_scale.append([high, c])
    return discrete_scale


def main():
    print("=" * 70)
    print(f"1. Running Spatial Risk Regionalization ({int(WEIGHT_GEO*100)}% Geo / {int(WEIGHT_WX*100)}% Weather) FORCED K = {TARGET_K}...")
    print("=" * 70)

    # 1. Load Option 2 5-day flood data
    df = pd.read_csv(DATA_CSV)
    df["DISTRICT_KEY"] = df["COUNTRY"].astype(str).str.strip() + "||" + df["ADM_NAME"].astype(str).str.strip()
    df_pivot = df.pivot_table(index="DISTRICT_KEY", columns="crop_year", values="flood_days_5plus", aggfunc="first").fillna(0)
    district_keys = df_pivot.index.tolist()

    df_binary = (df_pivot > 0).astype(int)

    # 2. Load shapefile for centroids
    gdf = gpd.read_file(SHP_PATH)[["ADM_NAME", "COUNTRY", "geometry"]]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["ADM_NAME"] = gdf["ADM_NAME"].astype(str).str.strip()
    gdf["COUNTRY"]  = gdf["COUNTRY"].astype(str).str.strip()
    gdf["DISTRICT_KEY"] = gdf["COUNTRY"] + "||" + gdf["ADM_NAME"]

    gdf = gdf[gdf["DISTRICT_KEY"].isin(district_keys)].drop_duplicates(subset=["DISTRICT_KEY"]).copy()
    gdf = gdf.set_index("DISTRICT_KEY").loc[district_keys].reset_index()

    gdf_proj = gdf.to_crs(epsg=3857)
    centroids = gdf_proj.geometry.centroid
    coords = np.column_stack([centroids.x, centroids.y])

    # 3. Compute Distance Matrices
    print("\n2. Computing Geography and Weather Distance Matrices...")
    d_geo = squareform(pdist(coords, metric="euclidean"))
    d_geo_norm = d_geo / d_geo.max()

    d_wx = squareform(pdist(df_binary.values, metric="jaccard"))
    d_wx_norm = np.nan_to_num(d_wx, 0.0)
    if d_wx_norm.max() > 0:
        d_wx_norm = d_wx_norm / d_wx_norm.max()

    d_combined = (WEIGHT_GEO * d_geo_norm) + (WEIGHT_WX * d_wx_norm)

    # 4. Agglomerative Hierarchical Linkage
    print("\n3. Performing Agglomerative Clustering (Ward Linkage)...")
    condensed_d = squareform(d_combined)
    Z = linkage(condensed_d, method="ward")

    # 5. Forced K = 14
    labs = fcluster(Z, t=TARGET_K, criterion="maxclust")
    sil = silhouette_score(d_combined, labs, metric="precomputed")
    print(f"\n   -> Forced Cluster Count: K = {TARGET_K} (Silhouette Score: {sil:.4f})")

    output_meta = {
        "weight_geo": WEIGHT_GEO,
        "weight_weather": WEIGHT_WX,
        "forced_k": TARGET_K,
        "silhouette_score": round(float(sil), 4),
        "district_keys": district_keys,
        "clusters": [int(l) for l in labs]
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_meta, f, indent=2)
    print(f"   [OK] Saved Cluster Metadata JSON: {OUT_JSON}")

    # 6. Generate Interactive HTML Map Dashboard for Forced K = 14
    print(f"\n4. Generating Dashboard for Forced K={TARGET_K} with High-Contrast Discrete Palette...")
    gdf_filtered = gdf.copy()
    gdf_filtered["cluster_k14"] = labs
    gdf_filtered["geometry"] = gdf_filtered["geometry"].simplify(0.05, preserve_topology=True)
    geojson_dict = json.loads(gdf_filtered.set_index("DISTRICT_KEY").to_json())

    discrete_colorscale = make_discrete_colorscale(TARGET_K, DISTINCT_COLORS)

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson_dict,
        locations=gdf_filtered["DISTRICT_KEY"],
        z=gdf_filtered["cluster_k14"],
        zmin=0.5,
        zmax=TARGET_K + 0.5,
        colorscale=discrete_colorscale,
        marker_line_width=0.4,
        marker_line_color="rgba(0,0,0,0.5)",
        marker_opacity=0.9,
        customdata=np.stack([gdf_filtered["ADM_NAME"], gdf_filtered["COUNTRY"], gdf_filtered["cluster_k14"]], axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            f"Risk Zone (K={TARGET_K}): <b>Zone %{{customdata[2]}}</b><br>"
            "<extra></extra>"
        ),
        showscale=False
    ))

    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=2.5, lon=17.5), zoom=2.1),
        title=dict(
            text=f"<b>Pan-African Flood Risk Regionalization — {int(WEIGHT_GEO*100)}% Geo / {int(WEIGHT_WX*100)}% Weather (95th %ile + 85% SWI Floor, 5-Day Basis)</b><br><sup>Forced Executive Baseline Cluster Count: K={TARGET_K} (Silhouette Score: {sil:.4f}) — High-Contrast Discrete Palette</sup>",
            font=dict(size=14, color="#0f172a"),
            x=0.5
        ),
        height=800,
        margin=dict(l=10, r=10, t=65, b=10)
    )

    fig.write_html(
        OUT_HTML,
        full_html=True,
        include_plotlyjs="cdn",
        config={"scrollZoom": True, "responsive": True, "displayModeBar": True}
    )
    print(f"   [OK] Saved Clustering Dashboard: {OUT_HTML}")


if __name__ == "__main__":
    main()
