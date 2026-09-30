import pandas as pd
df = pd.read_csv('output/agricultural/Africa_SWI_Maize_AreaWeighted_2007_2025.csv')
d2024 = df[df.date.str.startswith('2024')]
d2025 = df[df.date.str.startswith('2025')]
print(f'2024 Unique Days in CSV: {d2024.date.nunique()}')
print(f'2025 Unique Days in CSV: {d2025.date.nunique()}')

print('\n2024 Months present:')
print(pd.to_datetime(d2024.date).dt.month.value_counts().sort_index())

print('\n2025 Months present:')
print(pd.to_datetime(d2025.date).dt.month.value_counts().sort_index())

zambia = df[df.COUNTRY == 'Zambia']
print(f'\nZambia data rows: {len(zambia)}')
if not zambia.empty:
    print(f'Zambia unique districts: {zambia.ADM_NAME.nunique()}')
    print(f'Zambia total dates: {zambia.date.nunique()}')
