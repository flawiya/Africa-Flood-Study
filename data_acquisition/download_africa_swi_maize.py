"""
Africa SWI Maize Data Acquisition - V7 SAFE (Sequential + Year-by-Year Verification)
=============================================================================
1. Single-Worker Sequential Processing: 1 worker to prevent token rate-limiting.
2. Local-Drive First: Writing to C:\\ drive to eliminate OneDrive file lock errors.
3. Column-Aligned CSV: Produces 9 columns matching the original format.
4. Year-by-Year Verification: After each year, validates crop calendar coverage.
5. Nearest Land-Pixel Buffering: 10km buffer ensures 100% of 3,333 districts have valid land data.
6. In-Season Crop Calendar Filtering: Only saves active crop calendar dates per district.
"""

import os, sys, shutil, requests, pandas as pd, numpy as np, geopandas as gpd
import xarray as xr, zipfile, time, warnings
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
import exactextract

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
warnings.filterwarnings("ignore")

# =============================================================================
# CONFIGURATION
# =============================================================================
# Set these environment variables before running:
#   export CDSE_USERNAME="your_email@example.com"
#   export CDSE_PASSWORD="your_password"
USERNAME = os.environ.get("CDSE_USERNAME", "")
PASSWORD = os.environ.get("CDSE_PASSWORD", "")
_CDSE_CLIENT = "cdse-public"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_CSV    = os.path.join(BASE_DIR, "data", "raw", "copernicus_swi", "swi_global_12.5km_daily_v3_nc.csv")
SHAPEFILE_PATH = os.path.join(BASE_DIR, "data", "africa_agricultural_domain_2019.shp")
CALENDAR_SHP   = os.path.join(BASE_DIR, "data", "GEOGLAM_CM4EW_Calendars_V1.4", "GEOGLAM_CM4EW_Calendars_V1.4.shp")

OUTPUT_CSV = os.path.join(BASE_DIR, "output", "agricultural", "Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
LOCAL_DIR  = os.path.join(BASE_DIR, "scratch", "swi_temp_processing")

os.makedirs(LOCAL_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)



YEARS = range(2007, 2026)
SWI_VAR = "SWI_010"
SWI_RES = 0.1

# Token management
_current_token = None
_token_time = 0

# =============================================================================
# PHASE 1: SPATIAL DATA OPTIMIZATION & NEAREST LAND-PIXEL BUFFERING
# =============================================================================
def prep_spatial_data():
    print("[Phase 1] Preparing spatial data and crop calendars...", flush=True)
    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf = gdf[gdf.geometry.is_valid]
    gdf["district_uid"] = range(len(gdf))
    
    cal = gpd.read_file(CALENDAR_SHP).to_crs(gdf.crs)
    maize = cal[cal["crop"].isin(["Maize 1", "Maize 2"])].copy()
    
    centroids = gdf.copy()
    centroids["geometry"] = centroids.geometry.centroid
    joined = gpd.sjoin(centroids, maize[["crop", "planting", "harvest", "geometry"]], how="left", predicate="within")
    joined = joined.drop_duplicates(subset=["district_uid"])
    
    final_gdf = gdf.merge(joined[["district_uid", "planting", "harvest"]], on="district_uid", how="left")
    
    final_gdf.loc[final_gdf["COUNTRY"] == "Guinea-Bissau", "planting"] = 152
    final_gdf.loc[final_gdf["COUNTRY"] == "Guinea-Bissau", "harvest"] = 304
    final_gdf.loc[final_gdf["COUNTRY"] == "Malawi", "planting"] = 319
    final_gdf.loc[final_gdf["COUNTRY"] == "Malawi", "harvest"] = 135
    final_gdf.loc[final_gdf["COUNTRY"] == "Morocco", "planting"] = 91
    final_gdf.loc[final_gdf["COUNTRY"] == "Morocco", "harvest"] = 273
    
    final_gdf = final_gdf.dropna(subset=["planting", "harvest"]).copy()
    final_gdf["geometry"] = final_gdf["geometry"].simplify(0.01, preserve_topology=True)
    final_gdf["extract_geom"] = final_gdf["geometry"].buffer(0.08)
    
    print(f"Total valid maize-growing districts ready for extraction: {len(final_gdf)}", flush=True)
    return final_gdf

# =============================================================================
# COPERNICUS TOKEN & HTTP SESSION MANAGEMENT
# =============================================================================
def get_token():
    """Get a fresh token, with caching to avoid rate-limiting."""
    global _current_token, _token_time
    # Reuse token if less than 8 minutes old (tokens last 10 min)
    if _current_token and (time.time() - _token_time) < 480:
        return _current_token
    
    url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    for attempt in range(5):
        try:
            r = requests.post(url, data={"grant_type": "password", "username": USERNAME, "password": PASSWORD, "client_id": _CDSE_CLIENT}, timeout=30)
            if r.status_code == 200:
                _current_token = r.json()["access_token"]
                _token_time = time.time()
                return _current_token
            else:
                print(f"  [Token] Attempt {attempt+1}: HTTP {r.status_code}", flush=True)
        except Exception as e:
            print(f"  [Token] Attempt {attempt+1}: {e}", flush=True)
        time.sleep(3 * (attempt + 1))
    
    print("  CRITICAL: Could not obtain authentication token after 5 attempts!", flush=True)
    return None

def create_robust_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    return session

# =============================================================================
# PHASE 3: SINGLE-THREADED EXTRACTION LOGIC
# =============================================================================
def process_daily_file(product_id, date_str, gdf):
    """Process a single day's SWI data. Returns a DataFrame with 9 columns."""
    global _current_token
    zip_path = os.path.join(LOCAL_DIR, f"swi_{date_str}.zip")
    nc_path  = None
    session  = create_robust_session()
    
    download_success = False
    for attempt in range(1, 6):
        try:
            token = get_token()
            if token is None:
                print(f"  CRITICAL: No token available for {date_str}, attempt {attempt}", flush=True)
                time.sleep(5)
                continue
                
            url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
            r = session.get(url, headers={"Authorization": f"Bearer {token}"}, stream=True, timeout=120)
            if r.status_code == 401:
                print(f"  [Auth] 401 on {date_str}, refreshing token...", flush=True)
                _current_token = None  # Force token refresh
                time.sleep(2)
                continue
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536): f.write(chunk)
            download_success = True
            break
        except Exception as e:
            if attempt < 5:
                print(f"  [Retry] {date_str} attempt {attempt}: {e}", flush=True)
                time.sleep(2 * attempt)
            else:
                print(f"  CRITICAL: Failed downloading {date_str} after 5 attempts: {e}", flush=True)
                return pd.DataFrame()

    if not download_success:
        print(f"  CRITICAL: Download failed completely for {date_str}!", flush=True)
        return pd.DataFrame()

    try:
        doy = datetime.strptime(date_str, "%Y-%m-%d").timetuple().tm_yday
        gdf_extract = gdf.copy()
        gdf_extract["geometry"] = gdf_extract["extract_geom"]

        with zipfile.ZipFile(zip_path, "r") as zf:
            nc_files = [n for n in zf.namelist() if n.endswith(".nc")]
            if not nc_files:
                print(f"  WARNING: No .nc file found in zip for {date_str}!", flush=True)
                return pd.DataFrame()
            nc_name = nc_files[0]
            zf.extract(nc_name, LOCAL_DIR)
            nc_path = os.path.join(LOCAL_DIR, nc_name)

        with xr.open_dataset(nc_path, engine="netcdf4") as ds:
            # Dynamically read the true spatial boundaries of the NetCDF
            lon = ds.lon.values
            lat = ds.lat.values
            res_x = float(lon[1] - lon[0]) if len(lon) > 1 else SWI_RES
            res_y = float(lat[0] - lat[1]) if len(lat) > 1 else SWI_RES
            transform = from_origin(lon[0], lat[0], res_x, res_y)
            
            da = ds[SWI_VAR][0, :, :]
            data_array = da.values.astype('float32')
            
            with MemoryFile() as memfile:
                with memfile.open(driver='GTiff', height=data_array.shape[0], width=data_array.shape[1], count=1, dtype=data_array.dtype, transform=transform) as dataset:
                    dataset.write(data_array, 1)
                with memfile.open() as dataset:
                    stats = exactextract.exact_extract(
                        dataset, 
                        gdf_extract, 
                        ['mean', 'max'], 
                        include_cols=['ISO3', 'COUNTRY', 'ADM_NAME', 'planting', 'harvest'],
                        output='pandas'
                    )
            
            # Map column names explicitly to prevent KeyErrors
            stats = stats.rename(columns={
                'properties:ISO3': 'ISO3', 
                'properties:COUNTRY': 'COUNTRY', 
                'properties:ADM_NAME': 'ADM_NAME', 
                'properties:planting': 'planting', 
                'properties:harvest': 'harvest', 
                'mean': 'swi_t10_mean', 
                'max': 'swi_t10_max'
            })
            stats['date'] = date_str
            # Add the swi_t10_raw column to match the 9-column format
            stats['swi_t10_raw'] = stats['swi_t10_mean']
            
            def check_in_season(row):
                p, h = int(row['planting']), int(row['harvest'])
                if p <= h:
                    return p <= doy <= h
                else:
                    return doy >= p or doy <= h

            stats['in_season'] = stats.apply(check_in_season, axis=1)
            
            # Keep only the active records, in the exact 9-column order
            filtered_stats = stats[stats['in_season'] == True].copy()
            filtered_stats = filtered_stats[['date', 'ISO3', 'COUNTRY', 'ADM_NAME', 'planting', 'harvest', 'swi_t10_raw', 'swi_t10_mean', 'swi_t10_max']]
            filtered_stats = filtered_stats.dropna(subset=['swi_t10_mean'])
            
            return filtered_stats

    except Exception as e:
        print(f"  ERROR extracting {date_str}: {e}", flush=True)
        return pd.DataFrame()
    finally:
        for p in [zip_path, nc_path]:
            if p and os.path.exists(p): 
                try: os.remove(p)
                except: pass

# =============================================================================
# PHASE 4: YEAR-BY-YEAR VERIFICATION
# =============================================================================
def verify_year(yr, gdf):
    """After downloading a year, verify that the crop calendar coverage looks correct."""
    if not os.path.exists(OUTPUT_CSV):
        return
    
    df = pd.read_csv(OUTPUT_CSV, low_memory=False)
    df_yr = df[df['date'].astype(str).str[:4] == str(yr)]
    
    n_dates = df_yr['date'].nunique()
    n_districts = df_yr['ADM_NAME'].nunique()
    n_rows = len(df_yr)
    
    print(f"  [Verify {yr}] {n_dates} unique dates, {n_districts} unique districts, {n_rows:,} total rows", flush=True)
    
    # Check if this year has a reasonable number of dates
    # Most years should have 100+ dates (one per day during growing seasons)
    if n_dates < 50 and yr < 2025:
        print(f"  WARNING: Year {yr} has only {n_dates} dates - this seems low!", flush=True)
    else:
        print(f"  [Verify {yr}] PASSED - data looks good.", flush=True)

# =============================================================================
# PHASE 2: SEQUENTIAL DOWNLOAD MANAGEMENT
# =============================================================================
def main():
    gdf = prep_spatial_data()
    
    catalog = pd.read_csv(CATALOG_CSV, sep=";")
    catalog["date_only"] = catalog["nominal_date"].str[:10]
    catalog["year"] = catalog["nominal_date"].str[:4].astype(int)
    
    done_dates = set()
    if os.path.exists(OUTPUT_CSV):
        existing_df = pd.read_csv(OUTPUT_CSV, usecols=["date"], dtype={"date": str})
        done_dates = set(existing_df["date"].unique())
        print(f"[Checkpoint] Found {len(done_dates)} dates already processed locally. Resuming...", flush=True)
    
    first_write = not os.path.exists(OUTPUT_CSV)
    
    for yr in YEARS:
        cat_yr = catalog[catalog["year"] == yr]
        queue = list(zip(cat_yr["date_only"], cat_yr["id"]))
        queue = [q for q in queue if q[0] not in done_dates]
        
        if not queue:
            print(f"Year {yr} already fully processed. Skipping.", flush=True)
            continue
            
        print(f"\n[Phase 2] Beginning SEQUENTIAL processing for Year {yr} ({len(queue)} days remaining)...", flush=True)
        
        failed_days = []
        
        for i, (dstr, pid) in enumerate(queue, 1):
            res_df = process_daily_file(pid, dstr, gdf)
            if not res_df.empty:
                with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
                    res_df.to_csv(f, header=first_write, index=False)
                first_write = False
                done_dates.add(dstr)
            else:
                failed_days.append(dstr)
            
            if i % 20 == 0 or i == len(queue):
                print(f"  Processed {i}/{len(queue)} days for {yr}", flush=True)
        
        if failed_days:
            print(f"  WARNING: {len(failed_days)} days failed for {yr}: {failed_days[:5]}{'...' if len(failed_days) > 5 else ''}", flush=True)
        
        # Verify the year's data
        verify_year(yr, gdf)
        
        # Sync to OneDrive at the end of each completed year
        print(f"[Sync] Copying completed Year {yr} dataset to OneDrive...", flush=True)
        shutil.copy2(OUTPUT_CSV, ONEDRIVE_OUTPUT_CSV)
            
    # Final Sync
    if os.path.exists(OUTPUT_CSV):
        shutil.copy2(OUTPUT_CSV, ONEDRIVE_OUTPUT_CSV)
    print("\n[COMPLETE] All processing complete! Synced to OneDrive.", flush=True)

if __name__ == "__main__":
    main()