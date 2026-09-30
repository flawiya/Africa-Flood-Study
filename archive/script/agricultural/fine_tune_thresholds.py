import os
import pandas as pd
import numpy as np

BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
IN_CSV = os.path.join(BASE, "output", "agricultural", "Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
OUT_DIR = os.path.join(BASE, "output", "agricultural", "meeting_17th_july_output")

print("Loading massive 2.5M row dataset...")
df = pd.read_csv(IN_CSV, parse_dates=['date'])
df['crop_year'] = df['date'].dt.year
df = df.sort_values(['ADM_NAME', 'date'])

def calculate_consecutive_days(series):
    return series.groupby((~series).cumsum()).sum()

print("Calculating district percentiles...")
percentiles = df.groupby('ADM_NAME')['swi_t10_mean'].quantile([0.96, 0.97]).unstack()
percentiles.columns = ['P96', 'P97']
df = df.merge(percentiles, on='ADM_NAME', how='left')

results_p96 = []
results_p97 = []

print("Evaluating streaks...")
for (adm, yr), group in df.groupby(['ADM_NAME', 'crop_year']):
    group = group.sort_values('date')
    country = group['COUNTRY'].iloc[0]
    
    # Option P96 + 85%
    cond_p96 = (group['swi_t10_mean'] >= group['P96']) & (group['swi_t10_mean'] >= 85.0)
    streaks_p96 = calculate_consecutive_days(cond_p96)
    valid_p96 = streaks_p96[streaks_p96 >= 7]
    
    results_p96.append({
        'COUNTRY': country, 'ADM_NAME': adm, 'crop_year': yr,
        'flood_days_7plus': valid_p96.sum(),
        'num_flood_events': len(valid_p96),
        'max_consec_days': streaks_p96.max() if not streaks_p96.empty else 0
    })
    
    # Option P97 + 85%
    cond_p97 = (group['swi_t10_mean'] >= group['P97']) & (group['swi_t10_mean'] >= 85.0)
    streaks_p97 = calculate_consecutive_days(cond_p97)
    valid_p97 = streaks_p97[streaks_p97 >= 7]
    
    results_p97.append({
        'COUNTRY': country, 'ADM_NAME': adm, 'crop_year': yr,
        'flood_days_7plus': valid_p97.sum(),
        'num_flood_events': len(valid_p97),
        'max_consec_days': streaks_p97.max() if not streaks_p97.empty else 0
    })

pd.DataFrame(results_p96).to_csv(os.path.join(OUT_DIR, 'option_p96_plus_absolute_summary.csv'), index=False)
pd.DataFrame(results_p97).to_csv(os.path.join(OUT_DIR, 'option_p97_plus_absolute_summary.csv'), index=False)

print("Saved P96 and P97 summaries!")
