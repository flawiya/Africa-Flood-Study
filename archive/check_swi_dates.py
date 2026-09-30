import pandas as pd
df = pd.read_csv('output/agricultural/Africa_and_Zambia_SWI_Maize_Merged_Long.csv')
df = df[(df['COUNTRY'] == 'Zambia') & (df['ADM_NAME'].str.upper().str.strip() == 'CHIBOMBO') & (df['swi_band'] == 'swi_010')]
df['date'] = pd.to_datetime(df['date'])
print("Min date:", df['date'].min())
print("Max date:", df['date'].max())
print("Rows between 2010-10-01 and 2011-05-31:", len(df[(df['date'] >= '2010-10-01') & (df['date'] <= '2011-05-31')]))
