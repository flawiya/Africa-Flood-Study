import ee

ee.Initialize(project='vernal-parser-412016')

# 1. LOAD DISTRICTS
asset_path = 'projects/vernal-parser-412016/assets/Zambia_Administrative_Boundaries_Districts'
districts = ee.FeatureCollection(asset_path)

# 2. DEFINE TIME RANGE
years = list(range(2000, 2026)) # Add years as needed

def download_chirps(year):
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = start_date.advance(1, 'year')
    
    # Load CHIRPS Daily Rainfall
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \
        .filterDate(start_date, end_date) \
        .select('precipitation')

    def get_daily_stats(image):
        date = image.date().format('YYYY-MM-dd')
        # Calculate 95th percentile of rainfall per district
        stats = image.reduceRegions(
            collection=districts,
            reducer=ee.Reducer.percentile([95]).setOutputs(['mean']),
            scale=5000 # CHIRPS is approx 5km resolution
        )
        return stats.map(lambda f: f.set('date', date))

    daily_collection = chirps.map(get_daily_stats).flatten()
    
    # Export to Google Drive
    task = ee.batch.Export.table.toDrive(
        collection=daily_collection,
        description=f'Zambia_Rainfall_Only_{year}',
        folder='CHIRPS_Zambia_Data',
        fileFormat='CSV',
        selectors=['ADM2_EN', 'date', 'mean'] # 'mean' is the average rainfall
    )
    task.start()
    print(f"✅ Started download for CHIRPS {year}")

# Run the loop
for y in years:
    download_chirps(y)