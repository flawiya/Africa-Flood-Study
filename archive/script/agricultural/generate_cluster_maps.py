import os
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Restrict BLAS threads to avoid Windows threading issues
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\kmeans_district_summary.csv")
SHAPEFILE = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")

# Load aggregated district summary
summary_df = pd.read_csv(DATA_CSV)
# Identify numeric feature columns (exclude identifiers)
exclude_cols = ["ISO3", "COUNTRY", "ADM_NAME"]
feature_cols = [c for c in summary_df.columns if summary_df[c].dtype != object and c not in exclude_cols]
X = summary_df[feature_cols].values.astype(float)
# Standardise features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Load districts geometry
geo_df = gpd.read_file(SHAPEFILE)
# Merge geometry with summary on district name – adjust column name if necessary
merged = geo_df.merge(summary_df, left_on="ADM_NAME", right_on="ADM_NAME")

# Prepare a DataFrame to hold cluster assignments for each k
assignments = summary_df[exclude_cols].copy()

# Define the k values you want to explore
ks = [2, 3, 4, 5]

# Output directory for maps
maps_dir = os.path.join(BASE_DIR, r"output\agricultural\cluster_maps")
os.makedirs(maps_dir, exist_ok=True)

for k in ks:
    # Run MiniBatchKMeans (fast and lightweight)
    kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=100)
    labels = kmeans.fit_predict(X_scaled)
    # Record assignments
    assignments[f'cluster_{k}'] = labels
    # Add labels to the merged GeoDataFrame for visualisation
    merged[f'cluster_{k}'] = labels
    # Plot map with a qualitative colormap (tab10 works up to 10 clusters)
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    merged.plot(column=f'cluster_{k}', cmap='tab10', legend=True, ax=ax,
                edgecolor='black', linewidth=0.2)
    ax.set_title(f'Africa Agricultural Districts – KMeans (k={k})')
    ax.axis('off')
    map_path = os.path.join(maps_dir, f'kmeans_map_k{k}.png')
    plt.savefig(map_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# Save the cluster assignment CSV for downstream analysis
assign_path = os.path.join(BASE_DIR, r"output\agricultural\district_cluster_assignments.csv")
assignments.to_csv(assign_path, index=False)
print('Cluster maps saved to', maps_dir)
print('Cluster assignment CSV saved to', assign_path)
