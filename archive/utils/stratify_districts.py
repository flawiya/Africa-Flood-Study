import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os
import pathlib

# Define paths
UTILS_DIR = pathlib.Path(__file__).parent.resolve()
BASE_DIR = UTILS_DIR.parent
OUTPUT_DIR = BASE_DIR / "output"

shp_path = OUTPUT_DIR / "Zambia_Districts_GADM.shp"
csv_path = OUTPUT_DIR / "Zambia_Flood_Stratification_Data.csv"

print("=" * 60)
print("[INFO] OBJECTIVE 1: DISTRICT STRATIFICATION & EXTRACTION")
print("=" * 60)

# 1. Load data
try:
    gdf = gpd.read_file(shp_path)
    df = pd.read_csv(csv_path)
except Exception as e:
    print(f"[ERROR] Loading files: {e}")
    exit(1)

# Clean names
df['District_Name'] = df['District_Name'].astype(str).str.strip()
gdf['NAME_2'] = gdf['NAME_2'].astype(str).str.strip()

# Merge data
merged = gdf.merge(df, left_on='NAME_2', right_on='District_Name')

# 2. Define Groups (GHSL SMOD DEGURBA Dynamic Rules)
URBAN_THRESHOLD = 10.0
AGRI_THRESHOLD = 3.29

# Classification Masks:
# Urban/Economic: Builtup > 10% OR contains a DEGURBA Urban Centre (smod_code 30, i.e., Urban_Centre_Percentage > 0)
urban_mask = (merged['Builtup_Percentage'] > URBAN_THRESHOLD) | (merged['Urban_Centre_Percentage'] > 0.0)

# Agricultural: Builtup <= 10% AND Cropland > 3.29% AND does not contain a DEGURBA Urban Centre
agri_mask = (merged['Builtup_Percentage'] <= URBAN_THRESHOLD) & (merged['Cropland_Percentage'] > AGRI_THRESHOLD) & (merged['Urban_Centre_Percentage'] == 0.0)

# Get GeoDataFrames
urban_gdf = merged[urban_mask].copy()
agri_gdf = merged[agri_mask].copy()

# Find Overlapping Districts (Districts meeting urban criteria but also having high cropland density)
overlapping_gdf = merged[urban_mask & (merged['Cropland_Percentage'] > AGRI_THRESHOLD)].copy()

# Print stats
print(f"Urban/Economic Districts identified      : {len(urban_gdf)}")
print(f"Agricultural Districts identified       : {len(agri_gdf)}")
print(f"Overlapping Districts identified        : {len(overlapping_gdf)}")
print(f"Overlapping District Names: {overlapping_gdf['District_Name'].tolist()}")
print(f"Urban District Names: {urban_gdf['District_Name'].tolist()}")

# 3. Save Shapefiles
print("\n[INFO] Saving shapefiles to output folder...")
try:
    urban_gdf.to_file(OUTPUT_DIR / "Final_Urban_Intensity_Study_Area.shp", driver='ESRI Shapefile')
    agri_gdf.to_file(OUTPUT_DIR / "Final_Agri_Saturation_Study_Area.shp", driver='ESRI Shapefile')
    overlapping_gdf.to_file(OUTPUT_DIR / "Final_Overlapping_Study_Area.shp", driver='ESRI Shapefile')
    print("   [OK] Final_Urban_Intensity_Study_Area.shp saved.")
    print("   [OK] Final_Agri_Saturation_Study_Area.shp saved.")
    print("   [OK] Final_Overlapping_Study_Area.shp saved.")
except Exception as e:
    print(f"[ERROR] Saving shapefiles: {e}")

# 4. Generate Plotting
print("\n[INFO] Plotting dual-regime and overlap map...")
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(30, 10), dpi=120)

# Base background map of Zambia
def plot_base(ax):
    gdf.plot(ax=ax, color='#f7f7f7', edgecolor='#d9d9d9', linewidth=0.5)

# Panel 1: Urban
plot_base(ax1)
urban_gdf.plot(ax=ax1, color='#de2d26', edgecolor='#a50f15', linewidth=0.8)
ax1.set_title("1. Urban & Economic Flood Risk Regime\n(Built-up > 10% OR DEGURBA Urban Centre)", fontsize=14, fontweight='bold')
ax1.axis('off')

# Panel 2: Agri
plot_base(ax2)
agri_gdf.plot(ax=ax2, column='Cropland_Percentage', cmap='YlGn', edgecolor='#00441b', linewidth=0.4, legend=True, 
              legend_kwds={'label': 'Cropland Density (%)', 'shrink': 0.6})
ax2.set_title("2. Agricultural Flood Risk Regime\n(Built-up <= 10% & Cropland > 3.29%)", fontsize=14, fontweight='bold')
ax2.axis('off')

# Panel 3: Overlapping
plot_base(ax3)
# Plot urban as light red, agri as light green
urban_gdf.plot(ax=ax3, color='#fee0d2', edgecolor='#fc9272', linewidth=0.3)
agri_gdf.plot(ax=ax3, color='#e5f5e0', edgecolor='#a1d99b', linewidth=0.3)
# Plot overlapping in bright orange
overlapping_gdf.plot(ax=ax3, color='#fe9929', edgecolor='#cc4c02', linewidth=1.2)
ax3.set_title("3. Dual-Regime Overlapping Districts\n(Urban Centres with High Agriculture)", fontsize=14, fontweight='bold')
ax3.axis('off')

# Add legend notes for Overlapping
plt.suptitle("Zambia: Parametric Flood Study Area Stratification & Overlap", fontsize=20, fontweight='bold', y=0.98)
plt.figtext(0.5, 0.05, 
            "Regime Stratification Overview: Urban/Economic group (red) is monitored via daily CHIRPS rainfall intensity triggers (P95).\n" +
            "Agricultural group (green) is monitored via daily SCS Curve Number runoff depth (Q) and Soil Moisture (GLDAS).\n" +
            "Overlapping group (orange) contains districts that are DEGURBA Urban Centres but also have significant cropland density.",
            ha="center", fontsize=11, bbox={"facecolor":"#f9f9f9", "alpha":0.8, "pad":8})

map_output = OUTPUT_DIR / "Zambia_Dual_Regime_Map.png"
plt.savefig(map_output, bbox_inches='tight')
plt.close()

print(f"   [OK] Stratification map saved to: {map_output}")
print("=" * 60)
