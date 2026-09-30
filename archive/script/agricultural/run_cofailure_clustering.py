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
import plotly.express as px

warnings.filterwarnings("ignore")

# Regionalization libraries
try:
    import libpysal
    from spopt.region import Skater, WardSpatial, AZP
    SPOPT_AVAILABLE = True
except ImportError:
    SPOPT_AVAILABLE = False

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\co_failure_clustering")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. COMPUTE DURATION & STREAKS PER DISTRICT PER SEASON
# ---------------------------------------------------------
def extract_flood_events(df_in, swi_col="swi_t10_mean", threshold=85.0, min_duration=7):
    """
    Identifies continuous flood streaks >= min_duration days during the crop calendar.
    Returns seasonal summaries including trigger flag, max duration, and total flood days.
    """
    df_calc = df_in.copy()
    df_calc["is_flood"] = df_calc[swi_col] >= threshold
    
    # Identify continuous blocks
    df_calc["block"] = (df_calc["is_flood"] != df_calc.groupby(["COUNTRY", "ADM_NAME"])["is_flood"].shift()).cumsum()
    
    # Calculate length of each continuous flood block
    block_lengths = df_calc[df_calc["is_flood"]].groupby(["COUNTRY", "ADM_NAME", "crop_year", "block"]).size().reset_index(name="streak_len")
    
    # Filter streaks >= min_duration (e.g. 7 days)
    valid_streaks = block_lengths[block_lengths["streak_len"] >= min_duration]
    
    # Seasonal aggregation per district
    seasonal = valid_streaks.groupby(["COUNTRY", "ADM_NAME", "crop_year"]).agg(
        triggered=("streak_len", lambda x: 1 if len(x) > 0 else 0),
        max_duration=("streak_len", "max"),
        total_flood_days=("streak_len", "sum")
    ).reset_index()
    
    return seasonal

def main():
    print("1. Loading and preparing dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year
    
    # Adjust crop year for cross-year growing seasons
    plant_doy = pd.to_numeric(df["planting"], errors='coerce')
    harvest_doy = pd.to_numeric(df["harvest"], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1
    
    # Restrict to complete crop years & filter out Morocco
    df = df[~df["crop_year"].isin([2007, 2025])]
    df = df[df["COUNTRY"] != "Morocco"]
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    
    print("2. Extracting seasonal flood triggers & duration metrics...", flush=True)
    # Option 2 Logic: SWI >= 85 AND SWI >= 95th Percentile
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)
    
    # Continuous streak calculation
    df["block"] = (df["flag_opt2"] != df.groupby(["COUNTRY", "ADM_NAME"])["flag_opt2"].shift()).cumsum()
    block_info = df[df["flag_opt2"]].groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year", "block"]).size().reset_index(name="streak_days")
    valid_info = block_info[block_info["streak_days"] >= 7]
    
    seasonal_agg = valid_info.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        triggered=("streak_days", lambda x: 1 if len(x) > 0 else 0),
        max_streak=("streak_days", "max"),
        sum_streak_days=("streak_days", "sum")
    ).reset_index()

    # Get master list of all districts and years
    all_districts = df[["ISO3", "COUNTRY", "ADM_NAME"]].drop_duplicates()
    all_years = pd.DataFrame({"crop_year": df["crop_year"].unique()})
    master_grid = all_districts.merge(all_years, how="cross")
    
    full_seasonal = master_grid.merge(seasonal_agg, on=["ISO3", "COUNTRY", "ADM_NAME", "crop_year"], how="left").fillna(0)
    full_seasonal["ADM_NAME"] = full_seasonal["ADM_NAME"].astype(str).str.strip().str.upper()

    # ---------------------------------------------------------
    # 3. BUILD BINARY CO-FAILURE MATRIX & DURATION PROFILE
    # ---------------------------------------------------------
    print("3. Constructing Co-Failure Trigger Matrix & Duration Profiles...", flush=True)
    
    # Binary Matrix B: (Districts x Years)
    binary_pivot = full_seasonal.pivot_table(index="ADM_NAME", columns="crop_year", values="triggered").fillna(0)
    
    # Duration Matrix D: (Districts x Years) - Max Streak per Season
    duration_pivot = full_seasonal.pivot_table(index="ADM_NAME", columns="crop_year", values="max_streak").fillna(0)
    
    # District Level Long-term Flood Profile
    district_profile = full_seasonal.groupby("ADM_NAME").agg(
        trigger_freq=("triggered", "mean"),                # Failure Probability P(Fail)
        overall_max_duration=("max_streak", "max"),        # Worst flood duration observed
        p90_duration=("max_streak", lambda x: np.percentile(x, 90)) # 90th percentile duration
    )

    print("4. Aligning with Spatial Boundaries...", flush=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["ADM_NAME"] = gdf["ADM_NAME"].astype(str).str.strip().str.upper()
    gdf = gdf.drop_duplicates(subset="ADM_NAME").set_index("ADM_NAME").to_crs(epsg=3857)
    
    common = sorted(list(set(binary_pivot.index) & set(gdf.index)))
    binary_pivot = binary_pivot.loc[common]
    duration_pivot = duration_pivot.loc[common]
    district_profile = district_profile.loc[common]
    gdf_c = gdf.loc[common]

    # ---------------------------------------------------------
    # 5. CO-FAILURE DISTANCE MATRIX (JACCARD + DURATION)
    # ---------------------------------------------------------
    print("5. Calculating Jaccard Co-Failure Distance Matrix...", flush=True)
    
    # Jaccard distance on binary co-triggering history
    jaccard_dist_matrix = squareform(pdist(binary_pivot.values, metric="jaccard"))
    
    # Duration profile similarity (Standardized)
    dur_std = StandardScaler().fit_transform(district_profile.values)
    duration_dist_matrix = squareform(pdist(dur_std, metric="euclidean"))
    duration_dist_matrix /= duration_dist_matrix.max() # Normalize to [0, 1]
    
    # Combined Co-Failure & Duration Distance Matrix
    # 70% Weight on Exact Co-Failure History, 30% on Duration Magnitude Profile
    COMBINED_DIST = (0.70 * jaccard_dist_matrix) + (0.30 * duration_dist_matrix)

    # ---------------------------------------------------------
    # 6. K-MEANS & SPATIALLY CONSTRAINED CLUSTERING EVALUATION (K=2, 3, 4, 5)
    # ---------------------------------------------------------
    print("\n6. Evaluating Clustering Performance & Silhouette Scores for K = 2, 3, 4, 5...", flush=True)
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    
    # Combined feature matrix for KMeans (Binary co-trigger history + standardized duration)
    feat_matrix = np.hstack([binary_pivot.values, dur_std])
    
    centroids = gdf_c.centroid
    coords = np.column_stack([centroids.x, centroids.y])
    spatial_graph = kneighbors_graph(coords, n_neighbors=12, mode="connectivity")
    
    results = []
    best_score = -1.0
    best_k = 4
    best_labels = None
    
    print("\n================ SILHOUETTE SCORE EVALUATION SUMMARY ================", flush=True)
    print(f"{'K Clusters':<12} | {'K-Means Silhouette':<22} | {'Spatial Agglomerative Silhouette':<32}", flush=True)
    print("-" * 72, flush=True)
    
    for k in [2, 3, 4, 5]:
        # K-Means Clustering
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(feat_matrix)
        km_labels = km.labels_
        km_sil = silhouette_score(feat_matrix, km_labels)
        
        # Spatial Agglomerative Clustering (precomputed distance)
        agg = AgglomerativeClustering(
            n_clusters=k, 
            metric="precomputed", 
            connectivity=spatial_graph, 
            linkage="average"
        )
        agg_labels = agg.fit_predict(COMBINED_DIST)
        agg_sil = silhouette_score(COMBINED_DIST, agg_labels, metric="precomputed")
        
        print(f"K = {k:<9} | {km_sil:<22.4f} | {agg_sil:<32.4f}", flush=True)
        results.append({"K": k, "KMeans_Silhouette": km_sil, "Spatial_Agglomerative_Silhouette": agg_sil})
        
        if agg_sil > best_score:
            best_score = agg_sil
            best_k = k
            best_labels = agg_labels
            
    print("=" * 72, flush=True)
    print(f"\nOptimal K identified: K = {best_k} (Silhouette Score = {best_score:.4f})", flush=True)
    
    label_dict = dict(zip(common, best_labels.tolist()))

    # Assign labels based on Trigger Frequency and Max Duration
    gdf_c["cid"] = [label_dict[x] for x in gdf_c.index]
    gdf_c["trigger_freq"] = district_profile["trigger_freq"]
    gdf_c["max_dur"] = district_profile["overall_max_duration"]
    
    risk_ranks = gdf_c.groupby("cid")["trigger_freq"].mean().sort_values(ascending=False).index
    risk_labels = {cid: f"Co-Failure Pool {i+1} (P_fail={gdf_c[gdf_c['cid']==cid]['trigger_freq'].mean():.2f})" 
                   for i, cid in enumerate(risk_ranks)}
    
    gdf_c["cluster_label"] = gdf_c["cid"].map(risk_labels)

    # Export output map
    gdf_map = gdf_c.to_crs(epsg=4326).reset_index()
    fig = px.choropleth_mapbox(
        gdf_map,
        geojson=json.loads(gdf_map.to_json()),
        locations="ADM_NAME",
        featureidkey="properties.ADM_NAME",
        color="cluster_label",
        mapbox_style="open-street-map",
        center={"lat": 2.0, "lon": 18.0},
        zoom=2.2,
        opacity=0.6,
        title="<b>Africa Agricultural Flood Co-Failure Regionalization (2008-2024)</b><br><sup>Districts grouped by Jaccard Co-Occurrence of Parametric Flood Triggers</sup>"
    )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0}, height=750)
    out_file = os.path.join(OUT_DIR, "CoFailure_Flood_Pools_Map.html")
    fig.write_html(out_file)
    print(f"Complete! Output saved to {out_file}", flush=True)

if __name__ == "__main__":
    main()
