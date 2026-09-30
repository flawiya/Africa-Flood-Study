import pandas as pd
ed = pd.read_excel('output/agricultural/public_emdat_custom_request_2026-06-29_abbb1136-4dd7-4354-9d72-25ddda669f01.xlsx')
ed = ed[(ed['Country'] == 'Zambia') & (ed['Disaster Type'] == 'Flood')]
for _, row in ed.iterrows():
    print(f"{row['Start Year']}-{row['Start Month']}: {row['Location']}")
