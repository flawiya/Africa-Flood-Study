import ee
import pandas as pd

# Initialize Earth Engine
ee.Initialize()

# 1. Load Data
# GADM contains the district boundaries (Level 2) for all of Africa
districts = ee.FeatureCollection("wmgeolab/geoBoundaries/6_0/ZMB/ADM2") # Example for Zambia
# Or for all Africa: ee.FeatureCollection("FAO/GAUL/2015/level2")

# Load GLAD Cropland 2019 (High quality agricultural mask)
glad_cropland = ee.Image("users/potapovpeter/Global_cropland_2019")

# 2. Strategy: Create a Binary Mask (1 = Cropland, 0 = Other)
cropland_mask = glad_cropland.gt(0) 

# 3. Calculate Area
# Add a pixel area layer (m2) and mask it by cropland
pixel_area = ee.Image.pixelArea().updateMask(cropland_mask)

def calculate_ag_area(feature):
    # Sum the area of cropland pixels within each district
    stats = pixel_area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=feature.geometry(),
        scale=30, # GLAD resolution is 30m
        maxPixels=1e13
    )
    
    # Calculate Total District Area
    total_area = feature.geometry().area()
    
    return feature.set({
        'crop_area_m2': stats.get('area'),
        'total_area_m2': total_area,
        'crop_pct': ee.Number(stats.get('area')).divide(total_area).multiply(100)
    })

# Apply the calculation to all districts
processed_districts = districts.map(calculate_ag_area)

# 4. Convert to Pandas for Ranking
# Export only the properties we need to keep it fast
df = pd.DataFrame([f['properties'] for f in processed_districts.getInfo()['features']])

# 5. The Ranking Strategy (95% Rule)
df = df.sort_values(by='crop_area_m2', ascending=False)
df['cum_sum'] = df['crop_area_m2'].cumsum()
total_national_crop = df['crop_area_m2'].sum()
df['cum_pct'] = df['cum_sum'] / total_national_crop

# Filter: Top 95% of national cropland OR any district with >20% density
final_ag_districts = df[(df['cum_pct'] <= 0.95) | (df['crop_pct'] >= 20)]

# Save to CSV
final_ag_districts.to_csv("africa_agricultural_districts_ranked.csv", index=False)
print("Ranking complete. CSV saved.")