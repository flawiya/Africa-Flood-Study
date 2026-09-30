import geopandas as gpd
import matplotlib.pyplot as plt
import os

BASE_PATH = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"

# Shapefile paths
zambia_shp = os.path.join(BASE_PATH, "output", "Zambia_Districts_GADM.shp")
agri_shp = os.path.join(BASE_PATH, "output", "agricultural", "Zambia_agri_districts.shp")
urban_shp = os.path.join(BASE_PATH, "output", "urban", "Final_Urban_Study_Area.shp")

print("Loading shapefiles...")
gdf_all = gpd.read_file(zambia_shp)
gdf_all = gdf_all[gdf_all['COUNTRY'] == 'Zambia']
gdf_agri = gpd.read_file(agri_shp)
gdf_urban = gpd.read_file(urban_shp)

print(f"Total Zambia districts: {len(gdf_all)}")
print(f"Agricultural districts: {len(gdf_agri)}")
print(f"Urban districts: {len(gdf_urban)}")

fig, ax = plt.subplots(1, 1, figsize=(14, 14))

# Plot all of Zambia as background
gdf_all.plot(ax=ax, color='#e0e0e0', edgecolor='white', linewidth=0.5)

# Plot Agricultural districts
gdf_agri.plot(ax=ax, color='#2ca02c', edgecolor='black', linewidth=0.8, alpha=0.7)

# Plot Urban districts
gdf_urban.plot(ax=ax, color='#d62728', edgecolor='black', linewidth=0.8, alpha=0.8)

# Custom legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#e0e0e0', edgecolor='white', label='Other Districts'),
    Patch(facecolor='#2ca02c', edgecolor='black', alpha=0.7, label=f'Agricultural Districts (n={len(gdf_agri)})'),
    Patch(facecolor='#d62728', edgecolor='black', alpha=0.8, label=f'Urban Districts (n={len(gdf_urban)})')
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=14, frameon=True, shadow=True)

ax.set_title("Zambia Flood Parametric Study Areas\nUrban vs Agricultural Stratification", fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Save
out_dir = os.path.join(BASE_PATH, "output", "visualizations")
os.makedirs(out_dir, exist_ok=True)
out_img = os.path.join(out_dir, "Study_Areas_Map.png")
plt.tight_layout()
plt.savefig(out_img, dpi=300, bbox_inches='tight')
print(f"Map saved successfully to {out_img}")
