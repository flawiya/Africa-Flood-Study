import os
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt

# Restrict BLAS threads for Windows stability
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

# ---- Custom KMeans implementation (same as in run_kmeans_silhouette_custom) ----
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

# Run K=3 clustering
k = 3
labels, _ = kmeans_custom(X, n_clusters=k)
summary_df['cluster_k3'] = labels

# Save assignments CSV
assign_path = os.path.join(BASE_DIR, r"output\\agricultural\\district_cluster_assignments_k3.csv")
summary_df[['ISO3', 'COUNTRY', 'ADM_NAME', 'cluster_k3']].to_csv(assign_path, index=False)

# Load geometry and merge for mapping
geo_df = gpd.read_file(SHAPEFILE)
merged = geo_df.merge(summary_df, left_on="ADM_NAME", right_on="ADM_NAME")

# Plot map
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
merged.plot(column='cluster_k3', cmap='tab10', legend=True, ax=ax, edgecolor='black', linewidth=0.2)
ax.set_title('Africa Agricultural Districts – KMeans (k=3)')
ax.axis('off')
# Ensure output directory exists
maps_dir = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_maps")
os.makedirs(maps_dir, exist_ok=True)
map_path = os.path.join(maps_dir, 'kmeans_map_k3.png')
plt.savefig(map_path, dpi=300, bbox_inches='tight')
plt.close(fig)

print('Cluster assignments saved to', assign_path)
print('Cluster map saved to', map_path)
