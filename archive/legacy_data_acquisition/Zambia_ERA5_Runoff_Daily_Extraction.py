import ee
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. SET ENVIRONMENT AND PATHS
# Force headless matplotlib rendering
import matplotlib
matplotlib.use('Agg')

output_folder = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output"
shp_path = os.path.join(output_folder, "agricultural", "Zambia_Districts_GADM.shp")
csv_output_path = os.path.join(output_folder, "agricultural", "Zambia_ERA5_Daily_Runoff_2000_2025.csv")

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# 2. INITIALIZE GOOGLE EARTH ENGINE
PROJECT_ID = "vernal-parser-412016"
try:
    ee.Initialize(project=PROJECT_ID)
    print(" Earth Engine initialized successfully.")
except Exception:
    print(" Authenticating Earth Engine...")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 3. LOAD DISTRICT BOUNDARIES AND BUILD NAME MAPPING
print(" Building GADM name mapping using spatial centroids...")
asset_path = 'projects/vernal-parser-412016/assets/Zambia_Administrative_Boundaries_Districts'
districts_fc = ee.FeatureCollection(asset_path)

# Extract centroids in GEE
def add_coords(f):
    centroid = f.geometry().centroid()
    return f.set({
        'lon': centroid.coordinates().get(0),
        'lat': centroid.coordinates().get(1)
    })
districts_with_coords = districts_fc.map(add_coords)

# Fetch GEE names and coordinates
info_districts = districts_with_coords.select(['DISTRICT', 'lon', 'lat']).getInfo()
features_dist = info_districts['features']
rows_dist = []
for f in features_dist:
    props = f['properties']
    rows_dist.append({
        'GEE_Name': props['DISTRICT'],
        'Longitude': props['lon'],
        'Latitude': props['lat']
    })
df_dist = pd.DataFrame(rows_dist)

# Load GADM shapefile to match naming conventions ('Admin_2')
if not os.path.exists(shp_path):
    print(f"[ERROR] GADM shapefile not found at: {shp_path}")
    print("Please make sure the shapefile is in the output folder.")
    sys.exit(1)

gdf_gadm = gpd.read_file(shp_path)
shp_dist_col = 'Admin_2' if 'Admin_2' in gdf_gadm.columns else ('NAME_2' if 'NAME_2' in gdf_gadm.columns else 'District_N')

# Perform a spatial join on centroids to resolve the exact GADM Admin_2 names
geometry = [Point(xy) for xy in zip(df_dist.Longitude, df_dist.Latitude)]
points_gdf = gpd.GeoDataFrame(df_dist, geometry=geometry, crs="EPSG:4326")
joined = gpd.sjoin(points_gdf, gdf_gadm[[shp_dist_col, 'geometry']], how="left", predicate="within")

name_map = {}
for idx, row in joined.iterrows():
    gee_name = row['GEE_Name']
    gadm_name = row[shp_dist_col]
    if pd.isnull(gadm_name):
        gadm_name = gee_name  # Fallback to GEE name if slightly outside polygon
    name_map[gee_name] = gadm_name.strip()

print(f" Success: Built name mapping for {len(name_map)} districts.")

# 4. DEFINE WORKER FOR MONTHLY RETRIEVAL
def fetch_month_data(year, month, max_retries=3):
    """Fetches daily runoff records for a specific year and month."""
    for attempt in range(1, max_retries + 1):
        try:
            start_date = ee.Date.fromYMD(year, month, 1)
            end_date = start_date.advance(1, 'month')
            
            # Select the three runoff layers (surface runoff sum, sub-surface runoff sum, total runoff sum)
            era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
                .filterDate(start_date, end_date) \
                .select([
                    'surface_runoff_sum',
                    'sub_surface_runoff_sum',
                    'runoff_sum'
                ])
            
            def extract_daily(image):
                date_str = image.date().format('YYYY-MM-dd')
                stats = image.reduceRegions(
                    collection=districts_fc,
                    reducer=ee.Reducer.mean(), # Areal average runoff depth
                    scale=9000  # ERA5-Land native resolution is ~9km
                )
                return stats.map(lambda f: ee.Feature(None, {
                    'GEE_District_Name': f.get('DISTRICT'),
                    'Date': date_str,
                    'surface_runoff_m': f.get('surface_runoff_sum'),
                    'subsurface_runoff_m': f.get('sub_surface_runoff_sum'),
                    'total_runoff_m': f.get('runoff_sum')
                }))
            
            daily_stats = era5.map(extract_daily).flatten()
            info = daily_stats.getInfo()
            
            features = info['features']
            rows = [f['properties'] for f in features]
            
            # Convert values from meters to millimeters (mm)
            converted_rows = []
            for r in rows:
                surface_q = r.get('surface_runoff_m')
                subsurface_q = r.get('subsurface_runoff_m')
                total_q = r.get('total_runoff_m')
                
                converted_rows.append({
                    'GEE_District_Name': r.get('GEE_District_Name'),
                    'Date': r.get('Date'),
                    'surface_runoff_mm': surface_q * 1000.0 if surface_q is not None else 0.0,
                    'subsurface_runoff_mm': subsurface_q * 1000.0 if subsurface_q is not None else 0.0,
                    'total_runoff_mm': total_q * 1000.0 if total_q is not None else 0.0
                })
            
            return converted_rows
            
        except Exception as e:
            if attempt == max_retries:
                print(f"   [ERROR] Failed to fetch month {year}-{month:02d} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)  # Exponential backoff

# 5. LOOP OVER YEARS AND EXPORT INCREMENTALLY
years = list(range(2000, 2026))
print(f" Starting daily runoff extraction for {len(years)} years ({years[0]}-{years[-1]}) in parallel...")
print(f" Saving results directly to: {csv_output_path}")

t_start_global = time.time()

# Check if file already exists to avoid duplicate headers
write_header = not os.path.exists(csv_output_path)

for idx, year in enumerate(years):
    t_year_start = time.time()
    print(f"\n[{idx+1}/{len(years)}] Processing Year {year}...", flush=True)
    
    year_records = []
    
    # Fetch 12 months in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_month_data, year, m): m for m in range(1, 13)}
        
        for future in as_completed(futures):
            month = futures[future]
            res = future.result()
            if res:
                year_records.extend(res)
            else:
                print(f"   [WARNING] Month {year}-{month:02d} returned empty dataset.", flush=True)
                
    if year_records:
        # Create DataFrame
        df_year = pd.DataFrame(year_records)
        
        # Map names to GADM standard
        df_year['District_Name'] = df_year['GEE_District_Name'].map(name_map)
        
        # Reorder columns
        df_year = df_year[['District_Name', 'GEE_District_Name', 'Date', 'surface_runoff_mm', 'subsurface_runoff_mm', 'total_runoff_mm']]
        
        # Sort values chronologically and by district name
        df_year = df_year.sort_values(['District_Name', 'Date'])
        
        # Append to CSV
        df_year.to_csv(csv_output_path, mode='a', header=write_header, index=False)
        write_header = False  # Header written, don't write it again
        
        t_year_end = time.time()
        duration = t_year_end - t_year_start
        print(f"   [SUCCESS] Saved {len(df_year):,} rows for Year {year} in {duration:.1f} seconds.", flush=True)
    else:
        print(f"   [FAILED] No data retrieved for Year {year}.", flush=True)

t_end_global = time.time()
total_duration_mins = (t_end_global - t_start_global) / 60

print(f"\n{'='*65}")
print("EXTRACTION COMPLETE AND SAVED TO MASTER CSV")
print(f"{'='*65}")
print(f"Output File: {csv_output_path}")
print(f"Total Time Taken: {total_duration_mins:.2f} minutes")
if os.path.exists(csv_output_path):
    file_size_mb = os.path.getsize(csv_output_path) / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")
    print(f"Columns: District_Name, GEE_District_Name, Date, surface_runoff_mm, subsurface_runoff_mm, total_runoff_mm")
print(f"{'='*65}")
