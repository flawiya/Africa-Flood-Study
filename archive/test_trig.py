import pandas as pd
import numpy as np

def identify_sci_trigger(df):
    lag_status = np.zeros(len(df))
    sustained_status = np.zeros(len(df))
    in_lag = False
    is_fully_saturated = False
    
    dist_max = df['swi_value'].quantile(0.99)
    sat_threshold = dist_max * 0.95
    print('Sat Threshold:', sat_threshold)

    for i in range(len(df)):
        surface_trigger = (df.iloc[i]['Runoff_7d'] >= 20) and (df.iloc[i]['SSI_7d'] >= 1.5)
        saturated = df.iloc[i]['swi_value'] >= sat_threshold
        
        if surface_trigger and not is_fully_saturated:
            in_lag = True
        
        if in_lag and saturated:
            in_lag = False
            is_fully_saturated = True
            
        if not saturated:
            is_fully_saturated = False

        lag_status[i] = 1 if in_lag else 0
        sustained_status[i] = 1 if is_fully_saturated else 0
        
        if df.iloc[i]['Date'] >= pd.to_datetime('2011-01-25') and df.iloc[i]['Date'] <= pd.to_datetime('2011-01-30'):
            print(f"{df.iloc[i]['Date'].strftime('%Y-%m-%d')} | Rain:{df.iloc[i]['Rain_7d']:.1f} RO:{df.iloc[i]['Runoff_7d']:.1f} SSI:{df.iloc[i]['SSI_7d']:.2f} SWI:{df.iloc[i]['swi_value']:.1f} | SrfTrig:{surface_trigger} Sat:{saturated} | Lag:{in_lag} Full:{is_fully_saturated}")
        
    return lag_status, sustained_status

OUT_DIR = 'output/agricultural'
df_sm = pd.read_csv(f'{OUT_DIR}/Zambia_ERA5_Daily_Soil_Moisture_2000_2025.csv')
df_ro = pd.read_csv(f'{OUT_DIR}/Zambia_ERA5_Daily_Runoff_2000_2025.csv')
df_rf = pd.read_csv(f'{OUT_DIR}/CHIRPS_Standardized_Master.csv')
df_cop = pd.read_csv(f'{OUT_DIR}/Zambia_ERA5_Computed_SWI_T10_2000_2025.csv')

for d in [df_sm, df_ro, df_rf, df_cop]:
    d.columns = [c.replace('date', 'Date') for c in d.columns]
    d['Date'] = pd.to_datetime(d['Date'])
    if 'District_Name' in d.columns:
        d['Dist'] = d['District_Name'].str.upper().str.strip()

df = df_sm.merge(df_ro, on=['Dist', 'Date'], how='inner')
df = df.merge(df_rf, on=['Dist', 'Date'], how='inner')
df = df.merge(df_cop, on=['Dist', 'Date'], how='inner')

dist = 'CHIBOMBO'
d = df[df['Dist'] == dist].sort_values('Date').copy()
d['Rain_7d'] = d['precipitation'].rolling(7, min_periods=1).sum()
d['Runoff_7d'] = d['total_runoff_mm'].rolling(7, min_periods=1).sum()
mean_rain = df_rf[df_rf['Dist'] == dist]['precipitation'].mean()
std_rain = df_rf[df_rf['Dist'] == dist]['precipitation'].std()
d['SSI_7d'] = (d['Rain_7d'] - (mean_rain * 7)) / (std_rain * np.sqrt(7))

identify_sci_trigger(d)
