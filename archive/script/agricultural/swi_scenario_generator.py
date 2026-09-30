import pandas as pd
import numpy as np
import geopandas as gpd
import os

print("Starting SWI Threshold Scenario Generator...")

# ── 1. Setup Paths ────────────────────────────────────────────────────────
BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
SHP_PATH = os.path.join(BASE, "data", "africa_agricultural_domain_maize_calendar.shp")
SWI_CSV_PATH = os.path.join(BASE, "output", "agricultural", "Africa_SWI_Maize_Full_2007_2025.csv")
SUPP_CAL_PATH = os.path.join(BASE, "data", "supplemental_crop_calendar.csv")
OUT_DIR = os.path.join(BASE, "output", "agricultural", "scenarios")
os.makedirs(OUT_DIR, exist_ok=True)

# ── 2. Load Shapefile and Supplement ──────────────────────────────────────
print("Loading crop calendars...")
gdf = gpd.read_file(SHP_PATH)
df_cal = gdf[['ISO3', 'COUNTRY_x', 'ADM_NAME', 'planting_d', 'harvest_do']].copy()
df_cal.rename(columns={'COUNTRY_x': 'COUNTRY'}, inplace=True)
df_cal['Plant_DOY'] = df_cal['planting_d']
df_cal['Harvest_DOY'] = df_cal['harvest_do']

supp_cal = pd.read_csv(SUPP_CAL_PATH)

# ── 3. Load SWI Data ──────────────────────────────────────────────────────
print("Loading SWI data (this may take a moment)...")
df_swi = pd.read_csv(SWI_CSV_PATH)
df_swi = df_swi[df_swi['swi_band'] == 'swi_010'].copy()
df_swi.rename(columns={'swi_value': 'swi_010'}, inplace=True)
df_swi['swi_010'] = pd.to_numeric(df_swi['swi_010'], errors='coerce')
df_swi['date'] = pd.to_datetime(df_swi['date'])
df_swi['crop_year'] = df_swi['date'].dt.year
df_swi['doy'] = df_swi['date'].dt.dayofyear

# Merge main shapefile calendar
df_swi_main = df_swi.merge(df_cal[['COUNTRY', 'ADM_NAME', 'Plant_DOY', 'Harvest_DOY']], on=['COUNTRY', 'ADM_NAME'], how='inner')

# Identify missing countries in SWI raw data that are in supplement but missing from shapefile
missing_countries = supp_cal['COUNTRY'].unique()
df_swi_supp = df_swi[df_swi['COUNTRY'].isin(missing_countries)].copy()
if not df_swi_supp.empty:
    print(f"Adding supplemental calendar data for: {missing_countries}")
    df_swi_supp = df_swi_supp.merge(supp_cal[['COUNTRY', 'Plant_DOY', 'Harvest_DOY']], on='COUNTRY', how='inner')
    # Combine
    df_pv_raw = pd.concat([df_swi_main, df_swi_supp], ignore_index=True)
else:
    df_pv_raw = df_swi_main

# ── 4. Filter to Crop Calendar ────────────────────────────────────────────
def is_in_crop_calendar(row):
    start = row['Plant_DOY']
    end = row['Harvest_DOY']
    doy = row['doy']
    if pd.isna(start) or pd.isna(end) or start == 0 or end == 0:
        return False
    start, end = int(start), int(end)
    if start <= end:
        return start <= doy <= end
    else:  # Crosses year boundary
        return doy >= start or doy <= end

print("Filtering to active growing season...")
df_pv_raw['in_crop_calendar'] = df_pv_raw.apply(is_in_crop_calendar, axis=1)
df_pv = df_pv_raw[df_pv_raw['in_crop_calendar']].copy()

# ── 5. Calculate Climatologies ────────────────────────────────────────────
print("Calculating percentiles...")
thresholds = df_pv.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['swi_010'].agg(
    P95=lambda x: x.quantile(0.95),
    P99=lambda x: x.quantile(0.99)
).reset_index()

df_pv = df_pv.merge(thresholds, on=['ISO3', 'COUNTRY', 'ADM_NAME'], how='left')
df_pv = df_pv.sort_values(by=['ISO3', 'COUNTRY', 'ADM_NAME', 'date'])

# ── 6. Define Scenarios ───────────────────────────────────────────────────
scenarios = [
    {"name": "Scenario_1_P99", "condition": df_pv['swi_010'] > df_pv['P99']},
    {"name": "Scenario_2_P95_Abs80", "condition": (df_pv['swi_010'] > df_pv['P95']) & (df_pv['swi_010'] > 80.0)},
    {"name": "Scenario_3_Abs85", "condition": df_pv['swi_010'] > 85.0}
]

print("\n" + "="*50)
print("RUNNING SCENARIOS AND CALIBRATION CHECKS")
print("="*50)

for sc in scenarios:
    s_name = sc["name"]
    print(f"\nProcessing {s_name}...")
    
    df_pv['is_flood'] = sc["condition"]
    df_pv['streak_id'] = (df_pv['is_flood'] != df_pv['is_flood'].shift()).cumsum()
    df_flood = df_pv[df_pv['is_flood']].copy()
    
    if df_flood.empty:
        print(f"  [!] No floods detected at all for {s_name}")
        continue
        
    streak_lengths = df_flood.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year', 'streak_id']).size().reset_index(name='consec_days')
    streak_lengths['is_flood_event'] = streak_lengths['consec_days'] >= 7
    streak_lengths['flood_days'] = np.where(streak_lengths['is_flood_event'], streak_lengths['consec_days'], 0)
    
    summary = streak_lengths.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year']).agg(
        flood_days_7plus=('flood_days', 'sum'),
        num_flood_events_7plus=('is_flood_event', 'sum'),
        max_consec_days=('consec_days', 'max')
    ).reset_index()
    
    # Calculate zero-flood years (districts that didn't appear in df_flood have 0 automatically if we reindex, but we just check the max)
    # The true 'global' max flood days in any district in any year
    max_days = summary['flood_days_7plus'].max()
    avg_days_when_flooded = summary[summary['flood_days_7plus'] > 0]['flood_days_7plus'].mean()
    
    out_csv = os.path.join(OUT_DIR, f"SWI_Summary_{s_name}.csv")
    summary.to_csv(out_csv, index=False)
    
    print(f"  -> File saved: SWI_Summary_{s_name}.csv")
    print(f"  -> Calibration Result: Max flood days in a single year across all districts = {max_days}")
    print(f"  -> Average flood days (when a flood happens) = {avg_days_when_flooded:.1f} days")

print("\nDone!")
