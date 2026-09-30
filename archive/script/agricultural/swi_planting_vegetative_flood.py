import pandas as pd
import numpy as np
import geopandas as gpd
import os

print("Starting SWI Full Crop Calendar Flood Analysis (Admin 2 Level)...")

# ── 1. Setup Paths ────────────────────────────────────────────────────────
BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
SHP_PATH = os.path.join(BASE, "data", "africa_agricultural_domain_maize_calendar.shp")
SWI_CSV_PATH = os.path.join(BASE, "output", "agricultural", "Africa_SWI_Maize_Full_2007_2025.csv")
OUT_DIR = os.path.join(BASE, "output", "agricultural")
os.makedirs(OUT_DIR, exist_ok=True)

# ── 2. Load Shapefile (for Planting/Vegetative dates) ─────────────────────
print("Loading shapefile...")
gdf = gpd.read_file(SHP_PATH)
df_cal = gdf[['ISO3', 'COUNTRY_x', 'ADM_NAME', 'planting_d', 'harvest_do']].copy()
df_cal.rename(columns={'COUNTRY_x': 'COUNTRY'}, inplace=True)

# The columns are already in DOY format — use full planting -> harvest calendar
df_cal['Plant_DOY'] = df_cal['planting_d']
df_cal['Harvest_DOY'] = df_cal['harvest_do']

# ── 3. Load SWI Data ──────────────────────────────────────────────────────
print("Loading SWI data...")
df_swi = pd.read_csv(SWI_CSV_PATH)
df_swi = df_swi[df_swi['swi_band'] == 'swi_010']
df_swi.rename(columns={'swi_value': 'swi_010'}, inplace=True)
df_swi['date'] = pd.to_datetime(df_swi['date'])
df_swi['crop_year'] = df_swi['date'].dt.year
df_swi['doy'] = df_swi['date'].dt.dayofyear

# Only keep districts that are in the maize calendar
df_swi = df_swi.merge(df_cal, on=['ISO3', 'COUNTRY', 'ADM_NAME'], how='inner')

# ── 4. Filter to Full Crop Calendar (Planting -> Harvest) ────────────────
def is_in_crop_calendar(row):
    start = row['Plant_DOY']
    end = row['Harvest_DOY']
    doy = row['doy']

    if pd.isna(start) or pd.isna(end):
        return False

    start, end = int(start), int(end)
    if start <= end:
        return start <= doy <= end
    else:  # Crosses year boundary (e.g. plant Oct -> harvest Apr)
        return doy >= start or doy <= end

print("Filtering to full crop calendar (Planting->Harvest)...")
df_swi['in_crop_calendar'] = df_swi.apply(is_in_crop_calendar, axis=1)
df_pv = df_swi[df_swi['in_crop_calendar']].copy()

# ── 5. Calculate District-Level 95th Percentile Thresholds ────────────────
print("Calculating P95 thresholds...")
thresholds = df_pv.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['swi_010'].quantile(0.95).reset_index()
thresholds.rename(columns={'swi_010': 'P95'}, inplace=True)

df_pv = df_pv.merge(thresholds, on=['ISO3', 'COUNTRY', 'ADM_NAME'], how='left')

# ── 6. Identify Flood Streaks (SWI > P95) ─────────────────────────────────
print("Identifying flood streaks...")
df_pv = df_pv.sort_values(by=['ISO3', 'COUNTRY', 'ADM_NAME', 'date'])
df_pv['is_flood'] = df_pv['swi_010'] > df_pv['P95']

df_pv['streak_id'] = (df_pv['is_flood'] != df_pv['is_flood'].shift()).cumsum()
df_flood = df_pv[df_pv['is_flood']].copy()

streak_lengths = df_flood.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year', 'streak_id']).size().reset_index(name='consec_days')

# ── Severity: ONLY >=7 consecutive days above P95 counts as a flood event ──
# A streak of 6 days or fewer is NOT counted at all.
streak_lengths['is_flood_event'] = streak_lengths['consec_days'] >= 7
streak_lengths['flood_days']     = np.where(streak_lengths['is_flood_event'], streak_lengths['consec_days'], 0)

# ── 7. Aggregate by District and Crop Year ────────────────────────────────
print("Aggregating...")
summary = streak_lengths.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year']).agg(
    # Total days in the season that belonged to >=7 consecutive flood streaks
    flood_days_7plus=('flood_days', 'sum'),
    # Number of distinct >=7 day streak events in the season
    num_flood_events_7plus=('is_flood_event', 'sum'),
    # Longest single unbroken flood streak in the season
    max_consec_days=('consec_days', 'max'),
).reset_index()

summary = summary.merge(thresholds, on=['ISO3', 'COUNTRY', 'ADM_NAME'], how='left')

out_csv = os.path.join(OUT_DIR, "SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")  # kept same filename for downstream compatibility
summary.to_csv(out_csv, index=False)

print(f"Processed summary saved to: {out_csv}")
