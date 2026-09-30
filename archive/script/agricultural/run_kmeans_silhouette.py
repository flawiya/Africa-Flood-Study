import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MiniBatchKMeans as KMeans
from sklearn.metrics import silhouette_score

os.environ["OMP_NUM_THREADS"] = "1"


import warnings

# Paths
BASE_DIR = r"C:\\Users\\FlawiyaShirishMore\\OneDrive - Africa Specialty Risks Ltd\\ASR-Parametric_Research_Study\\Africa-Flood-Study"
# Use the aggregated district summary for clustering
DATA_CSV = os.path.join(BASE_DIR, r"output\\agricultural\\kmeans_district_summary.csv")


def load_data(csv_path):
    """Load the SWI dataset and prepare features for clustering.
    Uses the mean swi_t10 values and other numeric columns.
    """
    df = pd.read_csv(csv_path)
    # Drop rows with any missing values in numeric columns
    df = df.dropna(subset=[col for col in df.columns if df[col].dtype != "object"])
    # Select numeric columns (exclude identifiers like ADM_NAME, COUNTRY, crop_year)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude = ['crop_year']
    feature_cols = [c for c in numeric_cols if c not in exclude]
    X = df[feature_cols].values
    # Standardise features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, feature_cols

def run_kmeans(X, ks):
    for k in ks:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        print(f"k={k}: silhouette_score={score:.4f}")

if __name__ == "__main__":
    X, cols = load_data(DATA_CSV)
    ks = [2, 3, 4, 5]
    run_kmeans(X, ks)
