import ee
import geemap
import os

# 1. INITIALIZE EARTH ENGINE
# Using your specific project ID
PROJECT_ID = 'vernal-parser-412016'

try:
    ee.Initialize(project=PROJECT_ID)
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 2. DEFINE GEOGRAPHY (Zambia Districts)
# Using GAUL (Global Administrative Unit Layers)
countries = ee.FeatureCollection("FAO/GAUL/2015/level0")
zambia = countries.filter(ee.Filter.eq('ADM0_NAME', 'Zambia'))
districts = ee.FeatureCollection("FAO/GAUL/2015/level2").filterBounds(zambia)

# 3. EXPOSURE: ESA WORLDCOVER (CROPLAND)
# Class 40 = Cropland. We mask everything else.
worldcover = ee.Image("ESA/WorldCover/v200/2021").clip(zambia)
cropland = worldcover.eq(40)
cropland_masked = cropland.updateMask(cropland)

# 4. HAZARD: CHIRPS RAINFALL (ANNUAL SUM 2023)
# Creating a spatial intensity map
rainfall_2023 = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \
    .filterDate('2023-01-01', '2023-12-31') \
    .select('precipitation') \
    .sum() \
    .clip(zambia)

# 5. VISUALIZATION PARAMETERS
# Professional palette: Light Blue to Deep Navy for rainfall
rain_vis = {
    'min': 600,
    'max': 1400,
    'palette': ['#f7fbff', '#deebf7', '#9ecae1', '#4292c6', '#084594']
}

# High-visibility Green for Agriculture
agri_vis = {'palette': ['#238b45']}

# 6. CREATE LINKED MAPS
print("🔄 Generating side-by-side interactive maps...")

# Left Map: Exposure
m1 = geemap.Map(center=[-13.13, 27.84], zoom=6, basemap='CartoDB.Positron')
m1.add_layer(cropland_masked, agri_vis, 'Agricultural Land (ESA)')
m1.add_layer(districts.style(color='grey', fillColor='00000000', width=1), {}, 'Districts')
m1.add_text("1. Agricultural Exposure (ESA Class 40)", position='topleft')

# Right Map: Hazard
m2 = geemap.Map(center=[-13.13, 27.84], zoom=6, basemap='CartoDB.Positron')
m2.add_layer(rainfall_2023, rain_vis, 'Total Rainfall (mm)')
m2.add_layer(districts.style(color='grey', fillColor='00000000', width=1), {}, 'Districts')
m2.add_text("2. Rainfall Hazard (CHIRPS 2023)", position='topright')

# Combine into one linked layout
linked_map = geemap.linked_maps(rows=1, cols=2, maps=[m1, m2])

# 7. SAVE OUTPUT
# Since you are running a .py script, we save the result as HTML to open in your browser
output_folder = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output"
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "Zambia_Agri_Flood_Comparison.html")

# Note: geemap.linked_maps creates a widget. To save to HTML, we save the individual maps or the container
# For a .py run, the best way to see the result is:
m1.save(os.path.join(output_folder, "Map_Agri_Exposure.html"))
m2.save(os.path.join(output_folder, "Map_Rainfall_Hazard.html"))

print(f"✅ Success! Interactive maps saved to: {output_folder}")
print("📂 Please open 'Map_Agri_Exposure.html' and 'Map_Rainfall_Hazard.html' in your browser.")