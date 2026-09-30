import os
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt

# Restrict BLAS/OpenBLAS threads for Windows stability
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

BASE_DIR = r"C:\\Users\\FlawiyaShirishMore\\OneDrive - Africa Specialty Risks Ltd\\ASR-Parametric_Research_Study\\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\\agricultural\\kmeans_district_summary.csv")
SHAPEFILE = os.path.join(BASE_DIR, r"data\\africa_agricultural_domain_2019.shp")

# Load aggregated district summary
summary_df = pd.read_csv(DATA_CSV)
# Identify numeric feature columns (exclude identifiers)
exclude_cols = ["ISO3", "COUNTRY", "ADM_NAME"]
feature_cols = [c for c in summary_df.columns if summary_df[c].dtype != object and c not in exclude_cols]
X = summary_df[feature_cols].values.astype(float)

# Custom KMeans implementation (same as used for silhouette scores)
def kmeans_custom(X, n_clusters, max_iter=100, tol=1e-4, random_state=42):
    rng = np.random.default_rng(random_state)
    init_idx = rng.choice(len(X), size=n_clusters, replace=False)
    centroids = X[init_idx]
    for _ in range(max_iter):
        distances = cdist(X, centroids, metric='euclidean')
        labels = np.argmin(distances, axis=1)
        new_centroids = np.array([
            X[labels == k].mean(axis=0) if np.any(labels == k) else centroids[k]
            for k in range(n_clusters)
        ])
        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift <= tol:
            break
    return labels, centroids

# Load geometry
geo_df = gpd.read_file(SHAPEFILE)

# Output directories
maps_dir = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_maps")
os.makedirs(maps_dir, exist_ok=True)
assignments_dir = os.path.join(BASE_DIR, r"output\\agricultural")

ks = [2, 3, 4]
# We'll store labels for each k in the summary dataframe
for k in ks:
    labels, _ = kmeans_custom(X, n_clusters=k)
    col_name = f'cluster_k{k}'
    summary_df[col_name] = labels
    # Merge with geometry for mapping
    merged = geo_df.merge(summary_df, left_on="ADM_NAME", right_on="ADM_NAME")
    # Plot map
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    merged.plot(column=col_name, cmap='tab10', legend=True, ax=ax, edgecolor='black', linewidth=0.2)
    ax.set_title(f'Africa Agricultural Districts – KMeans (k={k})')
    ax.axis('off')
    map_path = os.path.join(maps_dir, f'kmeans_map_k{k}.png')
    plt.savefig(map_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    # Save assignment CSV for this k
    assign_path = os.path.join(assignments_dir, f'district_cluster_assignments_k{k}.csv')
    summary_df[["ISO3", "COUNTRY", "ADM_NAME", col_name]].to_csv(assign_path, index=False)
    print(f'Cluster map for k={k} saved to {map_path}')
    print(f'Cluster assignments for k={k} saved to {assign_path}')

# Optionally save a combined CSV with all cluster columns
combined_path = os.path.join(assignments_dir, 'district_cluster_assignments_all.csv')
summary_df[["ISO3", "COUNTRY", "ADM_NAME"] + [f'cluster_k{k}' for k in ks]].to_csv(combined_path, index=False)
print('Combined cluster assignment CSV saved to', combined_path)
