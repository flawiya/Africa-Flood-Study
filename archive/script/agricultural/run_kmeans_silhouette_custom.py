import os
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

# Set single thread for BLAS/OpenBLAS
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Paths
BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\kmeans_district_summary.csv")

def load_data(csv_path):
    """Load aggregated district summary for clustering.
    Uses all numeric columns except identifiers.
    """
    df = pd.read_csv(csv_path)
    # Drop rows with any missing numeric values
    df = df.dropna()
    # Identify numeric feature columns (exclude identifiers)
    exclude_cols = [c for c in df.columns if df[c].dtype == object]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    X = df[feature_cols].values.astype(float)
    return X, df, feature_cols

def kmeans_custom(X, n_clusters, max_iter=100, tol=1e-4, random_state=42):
    rng = np.random.default_rng(random_state)
    # Initialize centroids by sampling without replacement
    init_idx = rng.choice(len(X), size=n_clusters, replace=False)
    centroids = X[init_idx]
    for i in range(max_iter):
        # Compute distances to centroids
        distances = cdist(X, centroids, metric='euclidean')
        labels = np.argmin(distances, axis=1)
        new_centroids = np.array([X[labels == k].mean(axis=0) if np.any(labels == k) else centroids[k]
                                  for k in range(n_clusters)])
        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift <= tol:
            break
    return labels, centroids

def silhouette_score_custom(X, labels):
    # Compute pairwise distance matrix
    distance_matrix = cdist(X, X, metric='euclidean')
    n_samples = len(X)
    unique_labels = np.unique(labels)
    if len(unique_labels) == 1:
        return 0.0
    a = np.zeros(n_samples)
    b = np.full(n_samples, np.inf)
    for i in range(n_samples):
        same_cluster = labels == labels[i]
        # intra-cluster distance (exclude self)
        if np.sum(same_cluster) > 1:
            a[i] = np.mean(distance_matrix[i, same_cluster][distance_matrix[i, same_cluster] != 0])
        else:
            a[i] = 0.0
        # nearest-cluster distance
        for lbl in unique_labels:
            if lbl == labels[i]:
                continue
            cluster_mask = labels == lbl
            if np.any(cluster_mask):
                b[i] = min(b[i], np.mean(distance_matrix[i, cluster_mask]))
    sil = (b - a) / np.maximum(a, b)
    return np.mean(sil)

def run_kmeans_and_score(X, ks):
    for k in ks:
        labels, _ = kmeans_custom(X, n_clusters=k)
        score = silhouette_score_custom(X, labels)
        print(f"k={k}: silhouette_score={score:.4f}")

if __name__ == "__main__":
    X, df, feature_cols = load_data(DATA_CSV)
    ks = [2, 3, 4, 5]
    run_kmeans_and_score(X, ks)
