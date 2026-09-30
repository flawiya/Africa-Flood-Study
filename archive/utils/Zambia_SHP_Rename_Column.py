import geopandas as gpd
import os

# 1. SET PATH
shp_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\Zambia_Districts_GADM.shp"

print(f"🔄 Opening shapefile: {os.path.basename(shp_path)}")

# 2. LOAD DATA
gdf = gpd.read_file(shp_path)

# 3. IDENTIFY AND RENAME COLUMN
# GADM Level 2 standard column for district names is 'NAME_2'
# We check if it exists before renaming
if 'NAME_2' in gdf.columns:
    gdf = gdf.rename(columns={'NAME_2': 'Admin_2'})
    print("✅ Successfully renamed 'NAME_2' to 'Admin_2'.")
elif 'District_N' in gdf.columns: # Sometimes shapefiles truncate names
    gdf = gdf.rename(columns={'District_N': 'Admin_2'})
    print("✅ Successfully renamed 'District_N' to 'Admin_2'.")
else:
    print(f"⚠️ Warning: Expected column not found. Available columns: {gdf.columns.tolist()}")

# 4. SAVE PERMANENTLY
# Note: This will overwrite the original file. Ensure QGIS/ArcGIS is closed!
try:
    gdf.to_file(shp_path)
    print(f"🚀 Success! Changes saved permanently to: {shp_path}")
except PermissionError:
    print("❌ ERROR: Permission Denied. Please CLOSE the shapefile in QGIS or ArcGIS and run again.")

# 5. VERIFY
print("\n--- 📋 UPDATED SHP COLUMNS ---")
print(gdf.columns.tolist())