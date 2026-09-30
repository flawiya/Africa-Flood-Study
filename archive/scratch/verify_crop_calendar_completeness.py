import pandas as pd
import numpy as np

print("Loading dataset...")
df = pd.read_csv('output/agricultural/Africa_SWI_Maize_AreaWeighted_2007_2025.csv')

# Extract year from date
df['year'] = df['date'].str[:4].astype(int)

# Group by district and year to count available days
district_yearly_counts = df.groupby(['ADM_NAME', 'year', 'planting', 'harvest']).size().reset_index(name='actual_days')

# Calculate expected days in season
def calc_expected_days(row):
    p = int(row['planting'])
    h = int(row['harvest'])
    if p <= h:
        return h - p + 1
    else:
        # Crosses year boundary
        return (365 - p + 1) + h

district_yearly_counts['expected_days'] = district_yearly_counts.apply(calc_expected_days, axis=1)

# Allow a small buffer (e.g., 5 days) for leap years or minor Copernicus server gaps
district_yearly_counts['gap'] = district_yearly_counts['expected_days'] - district_yearly_counts['actual_days']

# Filter out 2025 because it's incomplete (ends in July)
full_years = district_yearly_counts[district_yearly_counts['year'] < 2025]

# Find severe gaps (missing more than 10 days of their season in a given year)
severe_gaps = full_years[full_years['gap'] > 10]

print(f"Total District-Year combinations checked (2007-2024): {len(full_years)}")
print(f"Combinations with perfect/near-perfect data: {len(full_years) - len(severe_gaps)}")
print(f"Combinations missing >10 days of their season: {len(severe_gaps)}")

if len(severe_gaps) > 0:
    print("\nSample of severe gaps found:")
    print(severe_gaps.sort_values('gap', ascending=False).head(10))
else:
    print("\nSUCCESS: All districts have their complete crop calendar data for every year!")
