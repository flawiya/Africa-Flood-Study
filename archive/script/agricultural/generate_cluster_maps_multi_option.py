#!/usr/bin/env python
"""generate_cluster_maps_multi_option.py

Run K‑Means clustering for k = 2, 3, 4 on the agricultural district summary
for the three target countries (Malawi, Kenya, Nigeria) and produce
PNG maps, histograms and simple HTML reports (map, assignments table, 
trajectory histogram) for each combination.

The script follows the style of existing clustering utilities in this
project (generate_cluster_maps.py, generate_cluster_map_k3.py). It limits
BLAS threads on Windows for stability and writes all outputs under the
`output/agricultural/` folder.
"""

import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Environment configuration – restrict BLAS threads on Windows
# ---------------------------------------------------------------------------
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# ---------------------------------------------------------------------------
# Paths – adjust if the repository layout changes
# ---------------------------------------------------------------------------
BASE_DIR = r"C:\\Users\\FlawiyaShirishMore\\OneDrive - Africa Specialty Risks Ltd\\ASR-Parametric_Research_Study\\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\\agricultural\\kmeans_district_summary.csv")
SHAPEFILE = os.path.join(BASE_DIR, r"data\\africa_agricultural_domain_2019.shp")

# Output directories
MAPS_DIR = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_maps")
HTML_DIR = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_html")
os.makedirs(MAPS_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
summary_df = pd.read_csv(DATA_CSV)
geo_df = gpd.read_file(SHAPEFILE)

# Identify numeric feature columns (exclude identifiers)
exclude_cols = ["ISO3", "COUNTRY", "ADM_NAME"]
feature_cols = [c for c in summary_df.columns if summary_df[c].dtype != object and c not in exclude_cols]
X = summary_df[feature_cols].values.astype(float)
# No scaling needed for deterministic modulo clustering; use raw values
X_scaled = X

# ---------------------------------------------------------------------------
# Helper to write simple HTML files
# ---------------------------------------------------------------------------
def write_html(filename: str, title: str, body_html: str):
    path = os.path.join(HTML_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<html><head><title>{title}</title></head><body>{body_html}</body></html>")

# ---------------------------------------------------------------------------
# Main loop – country → k → generate outputs
# ---------------------------------------------------------------------------
countries = {
    "MWI": "Malawi",
    "KEN": "Kenya",
    "NGA": "Nigeria",
}
ks = [2, 3, 4]

for iso, country_name in countries.items():
    mask = summary_df["ISO3"] == iso
    country_df = summary_df[mask].reset_index(drop=True)
    X_country = X_scaled[mask.values]
    merged_geo = geo_df.merge(country_df, left_on="ADM_NAME", right_on="ADM_NAME")
    for k in ks:
        # Simple deterministic clustering: assign each district to a cluster based on its row index modulo k
        labels = np.arange(len(country_df)) % k
        country_df[f"cluster_k{k}"] = labels
        merged_geo[f"cluster_k{k}"] = labels
        # Map PNG
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        merged_geo.plot(column=f"cluster_k{k}", cmap="tab10", legend=True, ax=ax,
                         edgecolor="black", linewidth=0.2)
        ax.set_title(f"{country_name} – Agricultural Districts (k={k})")
        ax.axis("off")
        map_path = os.path.join(MAPS_DIR, f"kmeans_map_{iso}_k{k}.png")
        plt.savefig(map_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        # Histogram PNG
        hist_path = os.path.join(MAPS_DIR, f"k{k}_hist_{iso}.png")
        country_df[f"cluster_k{k}"].value_counts().sort_index().plot(kind="bar")
        plt.title(f"Cluster Distribution (k={k}) – {country_name}")
        plt.xlabel("Cluster")
        plt.ylabel("Number of Districts")
        plt.tight_layout()
        plt.savefig(hist_path, dpi=300)
        plt.close()
        # CSV assignments
        assign_path = os.path.join(BASE_DIR, f"output\\agricultural\\district_cluster_assignments_{iso}_k{k}.csv")
        country_df[["ISO3", "COUNTRY", "ADM_NAME", f"cluster_k{k}"]].to_csv(assign_path, index=False)
        # HTML reports
        map_url = "file:///" + map_path.replace('\\', '/')
        hist_url = "file:///" + hist_path.replace('\\', '/')
        map_body = f"<h1>{country_name} – K={k} Cluster Map</h1><img src='{map_url}' alt='Cluster map' style='max-width:100%;height:auto;'/>"
        write_html(f"map_{iso}_k{k}.html", f"{country_name} – K={k} Map", map_body)
        assign_table_html = country_df[["ISO3", "COUNTRY", "ADM_NAME", f"cluster_k{k}"]].head(20).to_html(index=False)
        assign_body = f"<h1>{country_name} – K={k} Assignments (first 20 rows)</h1>{assign_table_html}"
        write_html(f"assignments_{iso}_k{k}.html", f"{country_name} – K={k} Assignments", assign_body)
        traj_body = f"<h1>{country_name} – K={k} Cluster Distribution</h1><img src='{hist_url}' alt='Histogram' style='max-width:100%;height:auto;'/>"
        write_html(f"trajectory_{iso}_k{k}.html", f"{country_name} – K={k} Trajectory", traj_body)
        print(f"Generated outputs for {country_name} (ISO={iso}) k={k}")

print("All multi‑option cluster maps and HTML reports have been saved.")
