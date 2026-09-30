"""
run_clustering_30geo_70wx.py
============================
Performs Ward Agglomerative Hierarchical Clustering with:
  - 30% Physical Geography Weight (centroid Euclidean distance in Web Mercator EPSG:3857)
  - 70% Weather Dissimilarity Weight (Jaccard dissimilarity of 5-day continuous flood occurrence vectors)
  - 95th Percentile + 85% SWI Floor Threshold (5-Day Continuous Streak Basis)
  - Evaluates K = 2 to 15 to find natural optimal cluster count via Silhouette Score
  - High-Contrast Discrete Color Palette

Outputs to:
  - output/agricultural/outputs/MultiMethod_Clustering_30geo_70wx.html
  - output/agricultural/outputs/cluster_labels_30geo_70wx.json
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "outputs", "Africa_Maize_Flood_Annual_Option2_5Day.csv")
SHP_PATH = os.path.join(BASE_DIR, "data", "africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

WEIGHT_GEO = 0.30
WEIGHT_WX  = 0.70

DISCRETE_PALETTE_15 = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5"
]


def classify_risk_tier(rank, total_clusters, avg_days):
    if total_clusters == 2:
        return "High Risk Cluster" if rank == 1 else "Low Risk Cluster"
    elif total_clusters <= 4:
        if rank == 1:
            return "High Risk Cluster"
        elif rank == total_clusters:
            return "Low Risk Cluster"
        else:
            return "Moderate Risk Cluster"
    else:
        third = total_clusters / 3.0
        if rank <= third:
            return "High Risk Cluster"
        elif rank > (total_clusters - third):
            return "Low Risk Cluster"
        else:
            return "Moderate Risk Cluster"


def main():
    print("=" * 70)
    print(f"1. Running Spatial Risk Regionalization ({int(WEIGHT_GEO*100)}% Geo / {int(WEIGHT_WX*100)}% Weather) for K = 2 to 15...")
    print("   Using standard metric .centroid coordinates (EPSG:3857).")
    print("=" * 70)

    df = pd.read_csv(DATA_CSV)
    df["DISTRICT_KEY"] = df["COUNTRY"].astype(str).str.strip() + "||" + df["ADM_NAME"].astype(str).str.strip()
    years = sorted(df["crop_year"].unique())

    pivot_df = df.pivot_table(index="DISTRICT_KEY", columns="crop_year", values="flood_days_5plus", aggfunc="first").fillna(0)
    district_keys = pivot_df.index.tolist()

    gdf = gpd.read_file(SHP_PATH)[["ADM_NAME", "COUNTRY", "geometry"]]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["ADM_NAME"] = gdf["ADM_NAME"].astype(str).str.strip()
    gdf["COUNTRY"]  = gdf["COUNTRY"].astype(str).str.strip()
    gdf["DISTRICT_KEY"] = gdf["COUNTRY"] + "||" + gdf["ADM_NAME"]

    gdf_sub = gdf[gdf["DISTRICT_KEY"].isin(district_keys)].drop_duplicates(subset=["DISTRICT_KEY"]).copy()
    gdf_sub = gdf_sub.set_index("DISTRICT_KEY").loc[district_keys].reset_index()

    gdf_projected = gdf_sub.to_crs(epsg=3857)
    centroids = gdf_projected.geometry.centroid
    coords = np.column_stack([centroids.x, centroids.y])

    print("\n2. Computing Geography and Weather Distance Matrices...")
    d_geo = pdist(coords, metric="euclidean")
    if d_geo.max() > 0:
        d_geo_norm = d_geo / d_geo.max()
    else:
        d_geo_norm = d_geo

    binary_matrix = (pivot_df.values > 0).astype(int)
    d_wx_jaccard = pdist(binary_matrix, metric="jaccard")

    d_combined = (WEIGHT_GEO * d_geo_norm) + (WEIGHT_WX * d_wx_jaccard)

    print("\n3. Performing Agglomerative Clustering (Ward Linkage)...")
    Z = linkage(d_combined, method="ward")

    d_combined_sq = squareform(d_combined)

    print("\n4. Evaluating K = 2 to 15 (Silhouette Optimization)...")
    sil_scores = {}
    clusters_by_k = {}
    for k in range(2, 16):
        labels = fcluster(Z, k, criterion="maxclust")
        score = silhouette_score(d_combined_sq, labels, metric="precomputed")
        sil_scores[k] = round(float(score), 4)
        clusters_by_k[k] = [int(x) for x in labels]
        print(f"   K = {k:2d}: Silhouette Score = {score:.4f}")

    best_k = max(sil_scores, key=sil_scores.get)
    print(f"\n   -> Optimal Natural Cluster Count (K=2..15): K = {best_k} (Score: {sil_scores[best_k]:.4f})")

    meta_payload = {
        "best_k": best_k,
        "weight_geo": WEIGHT_GEO,
        "weight_wx": WEIGHT_WX,
        "district_keys": district_keys,
        "sil_scores": sil_scores,
        "clusters_by_k": clusters_by_k
    }

    json_path = os.path.join(OUT_DIR, "cluster_labels_30geo_70wx.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)
    print(f"   [OK] Saved Cluster Metadata JSON: {json_path}")

    best_labels = clusters_by_k[best_k]
    gdf_sub["cluster"] = best_labels

    cluster_tot_days = {}
    cluster_counts   = {}
    for idx, row in gdf_sub.iterrows():
        c_id = row["cluster"]
        key  = row["DISTRICT_KEY"]
        days_sum = pivot_df.loc[key].sum() / len(years)
        cluster_tot_days[c_id] = cluster_tot_days.get(c_id, 0.0) + days_sum
        cluster_counts[c_id]   = cluster_counts.get(c_id, 0) + 1

    cluster_avg_days = {c: round(cluster_tot_days[c] / cluster_counts[c], 2) for c in cluster_tot_days}
    sorted_clusters  = sorted(cluster_avg_days.keys(), key=lambda c: cluster_avg_days[c], reverse=True)

    cluster_risk_label = {}
    for rank_idx, c_id in enumerate(sorted_clusters):
        tier = classify_risk_tier(rank_idx + 1, best_k, cluster_avg_days[c_id])
        cluster_risk_label[c_id] = f"{tier} (Zone {c_id} - Avg {cluster_avg_days[c_id]} d/yr)"

    gdf_sub["risk_desc"] = gdf_sub["cluster"].map(cluster_risk_label)
    gdf_sub["color"] = [DISCRETE_PALETTE_15[(c - 1) % len(DISCRETE_PALETTE_15)] for c in gdf_sub["cluster"]]
    gdf_sub["geometry"] = gdf_sub["geometry"].simplify(0.04, preserve_topology=True)

    print(f"\n5. Generating Dashboard for Optimal Natural Clusters (K={best_k}) with High-Contrast Discrete Palette...")
    fig = go.Figure()

    for c_id in sorted_clusters:
        sub = gdf_sub[gdf_sub["cluster"] == c_id]
        c_color = DISCRETE_PALETTE_15[(c_id - 1) % len(DISCRETE_PALETTE_15)]
        risk_name = cluster_risk_label[c_id]

        geojson_layer = json.loads(sub.to_json())

        fig.add_trace(go.Choroplethmap(
            geojson=geojson_layer,
            locations=sub.index,
            z=[c_id] * len(sub),
            colorscale=[[0, c_color], [1, c_color]],
            showscale=False,
            name=risk_name,
            text=sub["ADM_NAME"] + " (" + sub["COUNTRY"] + ")",
            hovertemplate="<b>%{text}</b><br>" + risk_name + "<extra></extra>",
            marker=dict(opacity=0.85, line=dict(width=0.4, color="rgba(0,0,0,0.3)"))
        ))

    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=2.5, lon=17.5), zoom=2.1),
        title=dict(
            text=f"<b>Pan-African Flood Risk Regionalization — {int(WEIGHT_GEO*100)}% Geo / {int(WEIGHT_WX*100)}% Weather (95th %ile + 85% SWI Floor, 5-Day Basis)</b><br><sup>Optimal Natural Cluster Count (Evaluated K=2..15): K={best_k} (Silhouette Score: {sil_scores[best_k]:.4f}) — High-Contrast Discrete Palette</sup>",
            font=dict(size=14, color="#0f172a"),
            x=0.5
        ),
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(
            title=dict(text="<b>Risk Clusters (Ward Linkage)</b>", font=dict(size=11, color="#0f172a")),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#cbd5e1",
            borderwidth=1,
            x=0.01, y=0.01,
            font=dict(size=10, color="#1e293b")
        )
    )

    out_html = os.path.join(OUT_DIR, "MultiMethod_Clustering_30geo_70wx.html")
    fig.write_html(out_html, include_plotlyjs="cdn")
    print(f"   [OK] Saved Clustering Dashboard: {out_html}")


if __name__ == "__main__":
    main()
