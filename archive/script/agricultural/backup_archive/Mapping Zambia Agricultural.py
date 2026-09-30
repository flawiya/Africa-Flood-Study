import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects  # Explicitly import for the text stroke
import os

# =============================================================================
# RESEARCH STRATEGY & JUSTIFICATION (FULL METHODOLOGY)
# =============================================================================
# 1. TIER 1: MAJOR PRODUCTION AREAS (95% Cumulative Ranking)
#    Reference: Becker-Reshef, I., et al. (2020). "The GEOGLAM Crop Monitor for 
#    Early Warning: Assessing regional crop conditions with a focus on 
#    food-insecure regions." Applied Geography.
#    Justification: Isolates the "National Breadbasket" responsible for the 
#    majority of food production while excluding marginal agricultural land.
#
# 2. TIER 2: AGRICULTURAL INTENSITY (15% Density Threshold)
#    Reference: Rembold, F., et al. (2019). "The Anomaly Hotspots of Agricultural 
#    Production (ASAP): A new early warning system for low food production." 
#    Justification: High density (>15%) ensures that the climate signal (ERA5)
#    reflects farmland behavior rather than urban or forest noise.
#
# 3. DATA SOURCE: GLOBAL CROPLAND (GLAD)
#    Reference: Potapov, P., et al. (2021). "Global maps of cropland extent and 
#    change in the 21st century." Nature Food.
# =============================================================================

# 1. SET PATHS
base_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\agricultural"
shp_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Drought-Study\data\africa_agricultural_domain_2019.shp"
map_output_path = os.path.join(base_path, "Zambia_Agricultural_Study_Districts_Map.png")

# 2. LOAD AND PREPARE DATA
print("[INFO] Preparing map data for Zambia...")
gdf = gpd.read_file(shp_path)

# Filter for Zambia
country_col = 'COUNTRY' if 'COUNTRY' in gdf.columns else 'NAME_0'
zambia_all = gdf[gdf[country_col] == 'Zambia'].copy()

# Re-apply the Research Filter Logic to identify the 23 districts for mapping
zambia_all['crop_density'] = zambia_all['crop_km2'] / zambia_all['total_km2']
zambia_all = zambia_all.sort_values(by='crop_km2', ascending=False)
total_national_cropland = zambia_all['crop_km2'].sum()
zambia_all['cum_pct'] = zambia_all['crop_km2'].cumsum() / total_national_cropland

# Separate the 23 study districts from the rest
study_districts = zambia_all[(zambia_all['cum_pct'] <= 0.95) & (zambia_all['crop_density'] >= 0.15)].copy()

# 3. CREATE THE PLOT
fig, ax = plt.subplots(figsize=(12, 10), dpi=300)

# Layer 1: All Zambia Districts (Light gray background)
zambia_all.plot(ax=ax, color='#f2f2f2', edgecolor='#bfbfbf', linewidth=0.5)

# Layer 2: The 23 Agricultural Study Districts
study_districts.plot(
    ax=ax, 
    column='crop_density', 
    cmap='YlGn', 
    edgecolor='#1a5c37', 
    linewidth=0.8,
    legend=True,
    legend_kwds={'label': "Cropland Density (Fraction)", 'orientation': "horizontal", 'pad': 0.02, 'shrink': 0.6}
)

# 4. ADD ANNOTATIONS (District Names for the 23 selected)
for idx, row in study_districts.iterrows():
    # Find the centroid for label placement
    centroid = row.geometry.representative_point().coords[0]
    ax.annotate(
        text=row['ADM_NAME'], 
        xy=centroid, 
        ha='center', 
        fontsize=7, 
        fontweight='bold',
        color='black',
        # FIX: path_effects now uses the explicitly imported module
        path_effects=[path_effects.withStroke(linewidth=2, foreground='white')]
    )

# 5. TITLES AND CITATIONS
plt.title("Zambia Agricultural Study Districts (n=23)", fontsize=16, fontweight='bold', pad=20)
plt.text(0.5, 0.94, 
         "Strategy: Top 95% National Ranking (Becker-Reshef et al. 2020)\n"
         "& >15% Ag Density (Rembold et al. 2019)", 
         transform=ax.transAxes, ha="center", fontsize=9, style='italic')

# Remove axes for a clean map appearance
ax.set_axis_off()

# 6. SAVE AND SHOW
plt.savefig(map_output_path, bbox_inches='tight', dpi=300, facecolor='white')
print(f"✅ Map created successfully.")
print(f"✅ Selected Districts Mapped: {len(study_districts)}")
print(f"✅ File saved to: {map_output_path}")
plt.show()