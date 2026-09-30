import pandas as pd
import numpy as np
from scipy.stats import norm
import os
import sys

# Configure UTF-8 encoding for standard outputs to prevent UnicodeEncodeError on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


# =============================================================================
# RESEARCH METHODOLOGY & CITATIONS
# =============================================================================
# 1. FULL-CYCLE VULNERABILITY MONITORING (November–April)
#    References: Rosenzweig et al. (2002). "Increased crop damage from excess 
#    precipitation"; Bremond et al. (2023). "Agricultural flood risk assessment."
#    Justification: Unlike drought (critical in the reproductive stage), 
#    flooding impacts crops across the full cycle: 
#    - Nov–Dec: Seedling Washout stage.
#    - Jan–Feb: Root Anoxia (Vegetative/Flowering stage).
#    - Mar–Apr: Grain Rot/Harvest interference.
#
# 2. DEPTH-WEIGHTED ROOT ZONE SOIL MOISTURE (0-100cm)
#    Reference: Muñoz-Sabater, J. (2019). "ERA5-Land hourly data from 1981 to present."
#    Justification: Root zone moisture is calculated using depth-weights based 
#    on ERA5 layer thickness: L1 (7cm), L2 (21cm), and L3 (72cm).
#
# 3. NON-PARAMETRIC SSI (Gringorten Approach)
#    Reference: Farahmand & AghaKouchak (2015); Wang et al. (2019).
#    Justification: Gringorten SSI is distribution-free. It is superior for 
#    floods because it respects the "physical ceiling" of soil saturation 
#    (porosity), whereas Gamma distributions can over-extrapolate the upper tail.
# =============================================================================

# 1. LOAD DATA
input_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\Zambia_Agricultural_Districts_Final_Study.csv"
df = pd.read_csv(input_path)
df = df.drop_duplicates(subset=['District_Name', 'Date'])

# 2. TEMPORAL FILTERING & CROP YEAR ASSIGNMENT
df['Date'] = pd.to_datetime(df['Date'])
df['Month'] = df['Date'].dt.month
# Create a leap-year-safe day-of-year (1 to 365) to prevent calendar shifts
df['doy'] = df['Date'].apply(lambda d: d.dayofyear if not d.is_leap_year or d.dayofyear < 60 else d.dayofyear - 1)

print("[INFO] Applying Full-Season Filter (November to April)...")
# Filter for Zambia Maize Season (Nov, Dec, Jan, Feb, Mar, Apr)
df = df[(df['Month'] >= 11) | (df['Month'] <= 4)].copy()

# Assign Crop Year (e.g., Nov 2020 and Jan 2021 both belong to Crop Year 2020)
# This is standard for Parametric Insurance / Agricultural studies (ARC, 2024)
df['Crop_Year'] = np.where(df['Month'] >= 11, df['Date'].dt.year, df['Date'].dt.year - 1)

# -----------------------------------------------------------------------------
# STEP 1: CALCULATE DEPTH-WEIGHTED AVERAGE (0-100cm)
# -----------------------------------------------------------------------------
print("[INFO] Calculating depth-weighted root zone moisture (0-100cm)...")
df['sm_root_zone'] = (df['soil_0_7cm'] * 0.07) + \
                     (df['soil_7_28cm'] * 0.21) + \
                     (df['soil_28_100cm'] * 0.72)

# -----------------------------------------------------------------------------
# STEP 2: CALCULATE NON-PARAMETRIC SSI (GRINGORTEN)
# -----------------------------------------------------------------------------
def calculate_gringorten_ssi(series):
    valid_series = series.dropna()
    n = len(valid_series)
    if n < 10:
        return pd.Series([np.nan] * len(series), index=series.index)
    
    # Rank data (1 to n)
    ranks = series.rank(method='average')
    # Gringorten Plotting Position
    prob = (ranks - 0.44) / (n + 0.12)
    # Transform to Z-score
    return norm.ppf(np.clip(prob, 0.0001, 0.9999))

print("[INFO] Computing SSI anomalies (Gringorten method per DOY)...")
# Group by District and Day-of-Year to isolate anomalies from the seasonal norm
df['SSI'] = df.groupby(['District_Name', 'doy'])['sm_root_zone'].transform(calculate_gringorten_ssi)

# -----------------------------------------------------------------------------
# STEP 3: DEFINE FLOOD PHASES & THRESHOLDS
# -----------------------------------------------------------------------------
# Tier 1: Statistical Wetness Anomaly
df['Flood_Indicator'] = np.where(df['SSI'] >= 1.5, 'Flood Risk', 'Normal')

# Tier 2: Lifecycle Impact Phase (for research categorization)
conditions = [
    (df['Month'] >= 11),                          # Early: Washout
    (df['Month'] >= 1) & (df['Month'] <= 2),      # Mid: Anoxia
    (df['Month'] >= 3) & (df['Month'] <= 4)       # Late: Rot
]
choices = ['Early (Washout Phase)', 'Mid (Anoxia Phase)', 'Late (Rot/Harvest Phase)']
df['Crop_Stage'] = np.select(conditions, choices, default='Unknown')

# 4. SAVE OUTPUT
output_path = input_path.replace(".csv", "_SSI_Gringorten_Full_Season.csv")
df.to_csv(output_path, index=False)

print("\n" + "="*70)
print("🚀 FULL-SEASON SSI EXTRACTION SUCCESSFUL")
print("="*70)
print(f"Monitoring Window: November to April")
print(f"Total Study Rows:  {len(df):,}")
print(f"Output Saved:      {output_path}")
print("="*70)