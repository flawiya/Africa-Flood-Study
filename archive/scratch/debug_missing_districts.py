import pandas as pd, geopandas as gpd, xarray as xr, numpy as np, os, zipfile
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
import exactextract
import warnings
warnings.filterwarnings('ignore')

# Load GDF
gdf = gpd.read_file('data/africa_agricultural_domain_2019.shp')
cal = gpd.read_file('data/GEOGLAM_CM4EW_Calendars_V1.4/GEOGLAM_CM4EW_Calendars_V1.4.shp').to_crs(gdf.crs)
gdf['district_uid'] = range(len(gdf))
maize = cal[cal['crop'].isin(['Maize 1', 'Maize 2'])].copy()
centroids = gdf.copy()
centroids['geometry'] = centroids.geometry.centroid
joined = gpd.sjoin(centroids, maize[['crop', 'planting', 'harvest', 'geometry']], how='left', predicate='within')
joined = joined.drop_duplicates(subset=['district_uid'])
final_gdf = gdf.merge(joined[['district_uid', 'planting', 'harvest']], on='district_uid', how='left')
final_gdf = final_gdf.dropna(subset=['planting', 'harvest']).copy()
final_gdf['extract_geom'] = final_gdf.geometry

gdf_extract = final_gdf.copy()
gdf_extract['geometry'] = gdf_extract['extract_geom']

# Find a zip
LOCAL_DIR = r'C:\Users\FlawiyaShirishMore\swi_temp_processing'
zips = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.zip')]
if not zips:
    print('No zip found.')
    exit(1)
zip_path = os.path.join(LOCAL_DIR, zips[0])

# Extract and read
with zipfile.ZipFile(zip_path, 'r') as zf:
    nc_name = [n for n in zf.namelist() if n.endswith('.nc')][0]
    zf.extract(nc_name, LOCAL_DIR)
    nc_path = os.path.join(LOCAL_DIR, nc_name)

with xr.open_dataset(nc_path, engine='netcdf4') as ds:
    lon = ds.lon.values
    lat = ds.lat.values
    res_x = float(lon[1] - lon[0]) if len(lon) > 1 else 0.1
    res_y = float(lat[0] - lat[1]) if len(lat) > 1 else 0.1
    transform = from_origin(lon[0], lat[0], res_x, res_y)
    print(f'Lat bounds: {lat.min()} to {lat.max()}, Lon bounds: {lon.min()} to {lon.max()}')
    print(f'res_x: {res_x}, res_y: {res_y}')
    print(f'Transform: {transform}')
    
    da = ds['SWI_010'][0, :, :]
    data_array = da.values.astype('float32')
    data_array[data_array > 200] = np.nan
    
    with MemoryFile() as memfile:
        with memfile.open(driver='GTiff', height=data_array.shape[0], width=data_array.shape[1], count=1, dtype=data_array.dtype, transform=transform) as dataset:
            dataset.write(data_array, 1)
        with memfile.open() as dataset:
            stats = exactextract.exact_extract(
                dataset, 
                gdf_extract, 
                ['mean'], 
                include_cols=['ADM_NAME'],
                output='pandas'
            )

print(f'Null means: {stats["mean"].isnull().sum()}')
null_districts = stats[stats["mean"].isnull()]['properties:ADM_NAME'].tolist()
print(f'Sample null districts: {null_districts[:10]}')
