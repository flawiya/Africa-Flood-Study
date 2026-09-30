import ee
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

# 1. SET ENVIRONMENT AND PATHS
base_dir = Path(__file__).resolve().parents[1]
output_folder = base_dir / "output"
output_folder.mkdir(exist_ok=True)
shp_path = output_folder / "Zambia_Districts_GADM.shp"
csv_output_path = output_folder / "Zambia_SoilMoisture_7_28cm_CropSeasons.csv"

# 2. INITIALIZE GOOGLE EARTH ENGINE
PROJECT_ID = "vernal-parser-412016"
try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 3. LOAD DISTRICT BOUNDARIES AND BUILD NAME MAPPING
asset_path = 'projects/vernal-parser-412016/assets/Zambia_Administrative_Boundaries_Districts'
districts_fc = ee.FeatureCollection(asset_path)

# Extract centroids and map GEE names to GADM Admin_2
def add_coords(f):
    centroid = f.geometry().centroid()
    return f.set({'lon': centroid.coordinates().get(0), 'lat': centroid.coordinates().get(1)})

districts_with_coords = districts_fc.map(add_coords)
info_districts = districts_with_coords.select(['DISTRICT', 'lon', 'lat']).getInfo()
features_dist = info_districts['features']
rows_dist = [{'GEE_Name': f['properties']['DISTRICT'], 'Longitude': f['properties']['lon'], 'Latitude': f['properties']['lat']} for f in features_dist]
df_dist = pd.DataFrame(rows_dist)


def load_gadm_boundaries():
    candidates = [
        shp_path,
        output_folder / "Zambia_Districts_GADM.gpkg",
        base_dir / "data" / "gadm_410-levels" / "gadm_410-levels_AFRICA_ADM2.gpkg",
        base_dir / "data" / "gadm_410-levels" / "gadm_410-levels.gpkg",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue

        try:
            gdf = gpd.read_file(candidate)

            if 'NAME_0' in gdf.columns:
                zambia_mask = gdf['NAME_0'].astype(str).str.strip().eq('Zambia')
                if zambia_mask.any():
                    gdf = gdf.loc[zambia_mask].copy()

            if gdf.empty:
                print(f"[WARN] No usable features found in {candidate}.")
                continue

            if 'Admin_2' not in gdf.columns:
                if 'NAME_2' in gdf.columns:
                    gdf = gdf.rename(columns={'NAME_2': 'Admin_2'})
                elif 'ADM2_EN' in gdf.columns:
                    gdf = gdf.rename(columns={'ADM2_EN': 'Admin_2'})
                elif 'District_N' in gdf.columns:
                    gdf = gdf.rename(columns={'District_N': 'Admin_2'})

            if not shp_path.exists() and candidate != shp_path:
                print(f"[INFO] Exporting fallback GADM boundaries to {shp_path}")
                gdf.to_file(shp_path)

            return gdf
        except Exception as exc:
            print(f"[WARN] Could not read {candidate}: {exc}")

    raise FileNotFoundError(
        "No GADM boundary file found. Checked the expected shapefile and bundled geopackage files."
    )


gdf_gadm = load_gadm_boundaries()
shp_dist_col = 'Admin_2' if 'Admin_2' in gdf_gadm.columns else ('NAME_2' if 'NAME_2' in gdf_gadm.columns else 'District_N')
geometry = [Point(xy) for xy in zip(df_dist.Longitude, df_dist.Latitude)]
points_gdf = gpd.GeoDataFrame(df_dist, geometry=geometry, crs="EPSG:4326")
joined = gpd.sjoin(points_gdf, gdf_gadm[[shp_dist_col, 'geometry']], how="left", predicate="within")
name_map = {row['GEE_Name']: (row[shp_dist_col] if pd.notnull(row[shp_dist_col]) else row['GEE_Name']).strip() for _, row in joined.iterrows()}

# 4. DEFINE WORKER FOR SEASONAL RETRIEVAL

def iter_month_ranges(start_date_str, end_date_str):
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    current = start.replace(day=1)

    while current < end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        period_end = min(end, next_month - timedelta(days=1))
        month_end_str = (period_end + timedelta(days=1)).strftime("%Y-%m-%d")
        yield current.strftime("%Y-%m-%d"), month_end_str
        current = next_month


def fetch_period_data(start_date_str, end_date_str, district_batches):
    """Fetches daily 7-28cm soil moisture for a specific date range in smaller chunks."""
    all_records = []
    try:
        district_names = [str(name) for name in df_dist['GEE_Name'].tolist()]
        print(f"   Districts to process: {len(district_names)}")

        for month_start_str, month_end_str in iter_month_ranges(start_date_str, end_date_str):
            print(f"   Processing month {month_start_str} to {month_end_str}...")
            for batch_idx, district_batch in enumerate(district_batches, start=1):
                batch_fc = districts_fc.filter(ee.Filter.inList('DISTRICT', district_batch))
                era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
                    .filterDate(month_start_str, month_end_str) \
                    .select(['volumetric_soil_water_layer_2'])

                if era5.size().getInfo() == 0:
                    continue

                def extract_daily(image, batch_collection=batch_fc):
                    date_str = image.date().format('YYYY-MM-dd')
                    stats = image.reduceRegions(
                        collection=batch_collection,
                        reducer=ee.Reducer.mean().setOutputs(['soil_7_28cm']),
                        scale=9000
                    )
                    return stats.map(lambda f: ee.Feature(None, {
                        'GEE_District_Name': f.get('DISTRICT'),
                        'Date': date_str,
                        'soil_7_28cm': f.get('soil_7_28cm')
                    }))

                daily_stats = era5.map(extract_daily).flatten()
                info = daily_stats.getInfo()
                features = info.get('features', [])
                if features:
                    all_records.extend([f['properties'] for f in features])
                    print(f"    Retrieved {len(features)} records for batch {batch_idx}/{len(district_batches)}")

        return all_records
    except Exception as e:
        print(f"Error fetching {start_date_str} to {end_date_str}: {e}")
        return []

# 5. DEFINE CROP SEASONS (NOV - APRIL)
# Season 1: Nov 2007 - April 2008
# Season 2: Nov 2011 - April 2012
seasons = [
    ("2007-11-01", "2008-05-01"),
    ("2011-11-01", "2012-05-01")
]

# 6. EXECUTE AND SAVE
print(f"Starting focused extraction for 7-28cm layer...")
all_records = []

batch_size = 10
district_names = [str(name) for name in df_dist['GEE_Name'].tolist()]
district_batches = [district_names[i:i + batch_size] for i in range(0, len(district_names), batch_size)]

for start, end in seasons:
    print(f" Processing Season: {start} to {end}...")
    records = fetch_period_data(start, end, district_batches)
    if records:
        all_records.extend(records)
        print(f"  Successfully retrieved {len(records)} records.")

if all_records:
    df = pd.DataFrame(all_records)
    df['District_Name'] = df['GEE_District_Name'].map(name_map)
    df = df[['District_Name', 'GEE_District_Name', 'Date', 'soil_7_28cm']]
    df = df.sort_values(['District_Name', 'Date'])
    
    df.to_csv(csv_output_path, index=False)
    print(f"\nSUCCESS: Data saved to {csv_output_path}")
else:
    print("\nFAILED: No data retrieved.")