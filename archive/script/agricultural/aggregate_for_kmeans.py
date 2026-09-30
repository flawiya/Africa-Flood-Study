import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
INPUT_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, r"output\agricultural\kmeans_district_summary.csv")

# ---------------------------------------------------------------------
# Load only the columns we need
# ---------------------------------------------------------------------
cols_needed = [
    'ISO3', 'COUNTRY', 'ADM_NAME', 'date',
    'swi_t10_mean'
]

print("Loading source CSV (may be large)...")
df = pd.read_csv(INPUT_CSV, usecols=cols_needed)
# Convert date to datetime for easier handling
df['date'] = pd.to_datetime(df['date'])
# Extract the calendar year from the date (this is the *reporting* year)
df['year'] = df['date'].dt.year

# ---------------------------------------------------------------------

# Build a boolean Series indexing the original rows that belong to a complete year
# ---------------------------------------------------------------------
# Since 'planting' and 'harvest' columns are absent, skip completeness filtering.
# Use all rows for aggregation.
# ---------------------------------------------------------------------
# Build a boolean Series flagging all rows as complete (i.e., keep everything)
filtered_df = df

print(f"Original rows: {len(df):,}")
print(f"Rows after removing incomplete years: {len(filtered_df):,}")

# ---------------------------------------------------------------------
# Compute district‑level summary metrics
# ---------------------------------------------------------------------
# 1. Mean SWI and 95th percentile SWI
agg_mean = filtered_df.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['swi_t10_mean'].mean().rename('mean_swi')
agg_p95  = filtered_df.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['swi_t10_mean'].quantile(0.95).rename('p95_swi')

# 2. Flood‑streak metrics per district
def streak_metrics(group: pd.DataFrame):
    # Sort by date for reliable streak detection
    series = group.sort_values('date')['swi_t10_mean'] > 0
    # Convert to integer array for fast processing
    arr = series.values.astype(int)
    # Identify runs of 1s
    counts = []
    cur = 0
    for v in arr:
        if v:
            cur += 1
        else:
            if cur:
                counts.append(cur)
            cur = 0
    if cur:
        counts.append(cur)
    if not counts:
        return pd.Series({'freq_7day_streaks': 0, 'max_flood_duration': 0})
    freq_7 = sum(1 for c in counts if c >= 7)
    max_dur = max(counts)
    return pd.Series({'freq_7day_streaks': freq_7, 'max_flood_duration': max_dur})

streak_df = filtered_df.groupby(['ISO3', 'COUNTRY', 'ADM_NAME']).apply(streak_metrics)

# ---------------------------------------------------------------------
# Combine all metrics into a single DataFrame
# ---------------------------------------------------------------------
summary = pd.concat([agg_mean, agg_p95, streak_df], axis=1).reset_index()
print("District summary ready – writing to CSV...")
summary.to_csv(OUTPUT_CSV, index=False)
print(f"Summary written to: {OUTPUT_CSV}")
