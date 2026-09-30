import pandas as pd
import geopandas as gpd
import os

# =============================================================================
# RESEARCH STRATEGY & JUSTIFICATION (FULL METHODOLOGY)
# =============================================================================
# 1. TIER 1: MAJOR PRODUCTION AREAS (95% Cumulative Ranking)
#    Reference: Becker-Reshef, I., et al. (2020). "The GEOGLAM Crop Monitor for 
#    Early Warning: Assessing regional crop conditions with a focus on 
#    food-insecure regions." Applied Geography.
#    Justification: To isolate the "National Breadbasket." This strategy sorts 
#    administrative units by absolute cropland area. Selecting the top 95% 
#    ensures the study captures the districts responsible for the vast majority 
#    of national food production, effectively filtering out marginal or 
#    non-productive land that does not impact national food security.
#
# 2. TIER 2: AGRICULTURAL INTENSITY (15% Density Threshold)
#    Reference: Rembold, F., et al. (2019). "The Anomaly Hotspots of Agricultural 
#    Production (ASAP): A new early warning system for low food production." 
#    Justification: Districts with low agricultural density (<15%) produce 
#    "noisy" biophysical signals because the soil moisture data (ERA5-Land) is 
#    dominated by non-crop land cover (forest, urban, or water). Filtering for 
#    >15% ensures the climate signal extracted reflects actual farmland conditions.
#
# 3. DATA SOURCE: GLOBAL CROPLAND (GLAD)
#    Reference: Potapov, P., et al. (2021). "Global maps of cropland extent and 
#    change in the 21st century." Nature Food.
#    Justification: Utilizing the 30m GLAD dataset allows for precise 
#    zonal aggregation of cropland area within GADM administrative boundaries, 
#    distinguishing between agricultural and non-agricultural land use.
# =============================================================================

# 1. SET PATHS
base_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output"
shp_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Drought-Study\data\africa_agricultural_domain_2019.shp"
climate_csv_path = os.path.join(base_path, "Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv")
output_path = os.path.join(base_path, "Zambia_Agricultural_Districts_Final_Study.csv")

# 2. LOAD AND FILTER SHAPEFILE FOR ZAMBIA
print("[INFO] Loading shapefile and isolating Zambia...")
gdf = gpd.read_file(shp_path)

# Ensure ranking is calculated at the national level for Zambia
country_col = 'COUNTRY' if 'COUNTRY' in gdf.columns else 'NAME_0'
gdf = gdf[gdf[country_col] == 'Zambia'].copy()

if gdf.empty:
    print("❌ ERROR: No Zambia data found in shapefile. Check the 'COUNTRY' column name.")
else:
    print(f"[INFO] Analyzing {len(gdf)} Zambian districts...")

    # Calculate Agricultural Density (Tier 2 Strategy: ASAP/Rembold)
    # Ensure 'crop_km2' and 'total_km2' exist in your shapefile
    gdf['crop_density'] = gdf['crop_km2'] / gdf['total_km2']

    # 3. APPLY RESEARCH FILTERS
    # Tier 1 Strategy: ranking (95% Cumulative Rule - Becker-Reshef)
    gdf = gdf.sort_values(by='crop_area_km' if 'crop_area_km' in gdf.columns else 'crop_km2', ascending=False)
    total_national_cropland = gdf['crop_km2'].sum()
    gdf['cum_pct'] = gdf['crop_km2'].cumsum() / total_national_cropland

    # Final selection based on the intersection of Importance (Ranking) and Intensity (Density)
    ag_districts_gdf = gdf[(gdf['cum_pct'] <= 0.95) & (gdf['crop_density'] >= 0.15)].copy()

    # Create a standardized list of district names (UPPERCASE) for error-free matching
    ag_district_list = ag_districts_gdf['ADM_NAME'].str.strip().str.upper().unique().tolist()

    print(f"✅ Strategy Application Complete:")
    print(f"   - Districts in Top 95% ranking: {len(gdf[gdf['cum_pct'] <= 0.95])}")
    print(f"   - Districts with >15% Density: {len(gdf[gdf['crop_density'] >= 0.15])}")
    print(f"   - FINAL STUDY DISTRICTS SELECTED: {len(ag_district_list)}")

    # 4. FILTER THE SOIL MOISTURE CSV
    if not os.path.exists(climate_csv_path):
        print(f"❌ Error: Could not find soil moisture CSV at {climate_csv_path}")
    else:
        print("[INFO] Loading climate data (Fixing ParserError by skipping bad lines)...")
        
        # on_bad_lines='skip' bypasses the "Expected 6 fields, saw 10" error
        df_climate = pd.read_csv(
            climate_csv_path, 
            on_bad_lines='skip', 
            low_memory=False
        )
        
        # Standardize CSV names for matching
        df_climate['District_Match'] = df_climate['District_Name'].astype(str).str.strip().str.upper()
        
        # Execute Filter
        df_final = df_climate[df_climate['District_Match'].isin(ag_district_list)].copy()
        
        # 5. MERGE RESEARCH METRICS FOR TRANSPARENCY
        stats_to_merge = ag_districts_gdf[['ADM_NAME', 'crop_km2', 'crop_density', 'cum_pct']]
        stats_to_merge['District_Match'] = stats_to_merge['ADM_NAME'].str.strip().str.upper()
        stats_to_merge = stats_to_merge.drop_duplicates(subset=['District_Match'])
        
        df_final = df_final.merge(
            stats_to_merge.drop(columns=['ADM_NAME']), 
            on='District_Match', 
            how='left'
        )
        
        # Drop the temporary matching column
        df_final = df_final.drop(columns=['District_Match'])

        # 6. SAVE OUTPUT
        df_final.to_csv(output_path, index=False)
        
        print("\n" + "="*75)
        print("🚀 RESEARCH EXTRACTION SUCCESSFUL")
        print("="*75)
        print(f"Total Ag Districts Included: {len(ag_district_list)}")
        print(f"Filtered Study Records:      {len(df_final):,}")
        print(f"Final Study Dataset:         {output_path}")
        print("="*75)