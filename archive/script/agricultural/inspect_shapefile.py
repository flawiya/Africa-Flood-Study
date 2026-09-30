import os
import geopandas as gpd
BASE_DIR = r"C:\\Users\\FlawiyaShirishMore\\OneDrive - Africa Specialty Risks Ltd\\ASR-Parametric_Research_Study\\Africa-Flood-Study"
SHAPEFILE = os.path.join(BASE_DIR, r"data\\africa_agricultural_domain_2019.shp")
print('Loading shapefile:', SHAPEFILE)
geo_df = gpd.read_file(SHAPEFILE)
print('Columns:', geo_df.columns.tolist())
print('First rows:', geo_df.head())
