import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg') # Force headless rendering to prevent backend crashes
import matplotlib.pyplot as plt
import os
import glob
from shapely.geometry import Point
import ee

# 1. SET PATHS
output_folder = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output"
shp_path = os.path.join(output_folder, "Zambia_Districts_GADM.shp")
strat_csv_path = os.path.join(output_folder, "Zambia_Flood_Stratification_Data.csv")

# 2. CHECK OR DYNAMICALLY GENERATE STRATIFICATION DATA
if not os.path.exists(strat_csv_path):
    print(f"[INFO] '{os.path.basename(strat_csv_path)}' not found. Fetching from GEE...")
    # Initialize Earth Engine
    ee.Initialize(project='vernal-parser-412016')

    # Load GEE collections
    asset_path = 'projects/vernal-parser-412016/assets/Zambia_Administrative_Boundaries_Districts'
    districts = ee.FeatureCollection(asset_path)
    worldcover = ee.Image("ESA/WorldCover/v200/2021").select('Map')

    # Create masks
    builtup_mask = worldcover.eq(50).rename('builtup_fraction')
    cropland_mask = worldcover.eq(40).rename('cropland_fraction')

    # GHSL SMOD 2020
    smod_collection = ee.ImageCollection("JRC/GHSL/P2023A/GHS_SMOD_V2-0")
    smod2020 = smod_collection.filterDate('2020-01-01', '2020-12-31').first().select('smod_code')
    smod_urban_centre = smod2020.eq(30).rename('urban_centre_fraction')

    # Combine bands
    combined_masks = builtup_mask.addBands(cropland_mask).addBands(smod_urban_centre)

    # Add centroids in GEE
    def add_coords(f):
        centroid = f.geometry().centroid()
        return f.set({
            'longitude': centroid.coordinates().get(0),
            'latitude': centroid.coordinates().get(1)
        })
    districts_with_coords = districts.map(add_coords)

    # Zonal stats
    stats = combined_masks.reduceRegions(
        collection=districts_with_coords,
        reducer=ee.Reducer.mean(),
        scale=100
    )

    # Format features
    def format_output(f):
        return ee.Feature(None, {
            'ADM2_EN': f.get('ADM2_EN'),
            'Latitude': f.get('latitude'),
            'Longitude': f.get('longitude'),
            'Builtup_Percentage': ee.Number(f.get('builtup_fraction')).multiply(100),
            'Cropland_Percentage': ee.Number(f.get('cropland_fraction')).multiply(100),
            'Urban_Centre_Percentage': ee.Number(f.get('urban_centre_fraction')).multiply(100)
        })
    final_collection = stats.map(format_output)

    # Fetch synchronously
    print("[INFO] Querying Earth Engine...")
    info = final_collection.getInfo()
    features = info['features']
    rows = [f['properties'] for f in features]
    df_raw = pd.DataFrame(rows)

    # Convert coordinates to Points for Spatial Join name healing
    print("[INFO] Healing district names via spatial join in-memory...")
    geometry = [Point(xy) for xy in zip(df_raw.Longitude, df_raw.Latitude)]
    csv_points = gpd.GeoDataFrame(df_raw, geometry=geometry, crs="EPSG:4326")

    gdf_districts = gpd.read_file(shp_path)
    shp_dist_col = 'Admin_2' if 'Admin_2' in gdf_districts.columns else ('NAME_2' if 'NAME_2' in gdf_districts.columns else 'District_N')

    # Join GEE points with GADM shapefile to get standard names
    joined = gpd.sjoin(csv_points, gdf_districts[[shp_dist_col, 'geometry']], how="left", predicate="within")
    joined = joined.rename(columns={shp_dist_col: 'District_Name'})

    # Fallback to ADM2_EN if point fell slightly outside GADM polygons
    joined['District_Name'] = joined['District_Name'].fillna(joined['ADM2_EN'])

    # Drop geometry and indexing columns to save a clean pandas DataFrame
    df = pd.DataFrame(joined.drop(columns=['geometry', 'index_right']))
    df['District_Name'] = df['District_Name'].astype(str).str.strip()
    df.to_csv(strat_csv_path, index=False)
    print(f"[SUCCESS] Recreated and saved stratification data to: {strat_csv_path}")
else:
    print(f"[INFO] Loading existing data source: {os.path.basename(strat_csv_path)}")
    df = pd.read_csv(strat_csv_path)

# 3. LOAD GADM GEOMETRY
gdf = gpd.read_file(shp_path)
shp_dist_col = 'Admin_2' if 'Admin_2' in gdf.columns else ('NAME_2' if 'NAME_2' in gdf.columns else 'District_N')
gdf['NAME_2_clean'] = gdf[shp_dist_col].astype(str).str.strip()
df['District_Name'] = df['District_Name'].astype(str).str.strip()

# 4. APPLY REGIME RULES (Dynamic GHSL DEGURBA Rules)
# Rule 1: Urban Tipping Point (Builtup_Percentage >= 10.0% OR contains a DEGURBA Urban Centre)
# Rule 2: Agri Bread Basket (Cropland_Percentage >= 3.29% and Builtup < 10.0% and no Urban Centre)
def classify_district(row):
    if row['Builtup_Percentage'] >= 10.0 or row['Urban_Centre_Percentage'] > 0.0:
        return 'URBAN_STUDY'
    elif row['Cropland_Percentage'] >= 3.29:
        return 'AGRI_STUDY'
    else:
        return 'NATURAL_LAND'

df['Flood_Regime'] = df.apply(classify_district, axis=1)

# 5. SAVE CSV DATASETS
urban_df = df[df['Flood_Regime'] == 'URBAN_STUDY']
agri_df = df[df['Flood_Regime'] == 'AGRI_STUDY']

urban_df.to_csv(os.path.join(output_folder, "Final_Urban_Study_Area.csv"), index=False)
agri_df.to_csv(os.path.join(output_folder, "Final_Agri_Study_Area.csv"), index=False)

# 6. MERGE WITH SPATIAL DATA
merged = gdf.merge(df[['District_Name', 'Flood_Regime', 'Builtup_Percentage', 'Cropland_Percentage', 'Urban_Centre_Percentage']], left_on='NAME_2_clean', right_on='District_Name')

# 7. EXPORT SHAPEFILES
urban_shp = merged[merged['Flood_Regime'] == 'URBAN_STUDY'].copy()
agri_shp = merged[merged['Flood_Regime'] == 'AGRI_STUDY'].copy()

# Drop temporary join column before export to avoid shapefile warning
if 'NAME_2_clean' in urban_shp.columns:
    urban_shp = urban_shp.drop(columns=['NAME_2_clean'])
if 'NAME_2_clean' in agri_shp.columns:
    agri_shp = agri_shp.drop(columns=['NAME_2_clean'])

if not urban_shp.empty:
    urban_shp.to_file(os.path.join(output_folder, "Final_Urban_Study_Area.shp"))
    urban_shp.to_file(os.path.join(output_folder, "Study_Area_Urban_Final.shp"))

if not agri_shp.empty:
    agri_shp.to_file(os.path.join(output_folder, "Final_Agri_Saturation_Study_Area.shp"))
    agri_shp.to_file(os.path.join(output_folder, "Study_Area_Agri_Final.shp"))

print("[SUCCESS] Stratification Complete:")
print(f"   - Urban Districts: {len(urban_df)}")
print(f"   - Agri Districts: {len(agri_df)}")
print("[INFO] Study Areas saved as SHP and CSV in output folder.")

# 8. GENERATE SIDE-BY-SIDE VISUALIZATION
print("[INFO] Generating side-by-side plot...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 12), dpi=100)

def plot_bg(ax):
    gdf.plot(ax=ax, color='#f0f0f0', edgecolor='#d9d9d9', linewidth=0.5)

# --- MAP 1: URBAN STUDY AREA (LEFT) ---
plot_bg(ax1)
if not urban_shp.empty:
    urban_shp.plot(ax=ax1, color='#de2d26', edgecolor='#a50f15', linewidth=1.2)
    
    # Label Urban Districts
    for idx, row in urban_shp.iterrows():
        lbl_name = row[shp_dist_col]
        centroid = row.geometry.centroid
        ax1.annotate(text=f"{lbl_name}\n{row['Builtup_Percentage']:.1f}%", 
                     xy=(centroid.x, centroid.y),
                     ha='center', fontsize=9, fontweight='bold', 
                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

ax1.set_title("1. Urban Flood Study Area\n(Regime: Intensity-Excess | Built-up >= 10% or DEGURBA)", fontsize=18, fontweight='bold')
ax1.axis('off')

# --- MAP 2: AGRICULTURAL STUDY AREA (RIGHT) ---
plot_bg(ax2)
if not agri_shp.empty:
    agri_shp.plot(ax=ax2, color='#31a354', edgecolor='#00441b', linewidth=0.8)
    
    # Label top Agri districts for reference
    top_agri = agri_shp.sort_values('Cropland_Percentage', ascending=False).head(5)
    for idx, row in top_agri.iterrows():
        lbl_name = row[shp_dist_col]
        centroid = row.geometry.centroid
        ax2.annotate(text=lbl_name, xy=(centroid.x, centroid.y),
                     ha='center', color='darkgreen', fontsize=9, fontweight='bold')

ax2.set_title("2. Agricultural Flood Study Area\n(Regime: Saturation-Excess | Cropland >= 3.29%)", fontsize=18, fontweight='bold')
ax2.axis('off')

plt.suptitle("Zambia: Flood Study Area Identification - Dual Regime Stratification", 
             fontsize=26, fontweight='bold', y=0.98)

# Add Methodology Note
plt.figtext(0.5, 0.05, 
            "Urban: Built-up >= 10.0% or DEGURBA Urban Centre | Agricultural: Cropland >= 3.29% (and not Urban)", 
            ha="center", fontsize=14, bbox={"facecolor":"#f9f9f9", "alpha":0.5, "pad":10})

output_map = os.path.join(output_folder, "Zambia_Stratification_SideBySide.png")
plt.savefig(output_map, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Side-by-Side maps saved to: {output_map}")
print(f"   - Final Urban Shapefile: {len(urban_shp)} districts")
print(f"   - Final Agri Shapefile: {len(agri_shp)} districts")