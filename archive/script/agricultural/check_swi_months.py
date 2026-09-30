import pandas as pd
import os

base_dir = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
merged_path = os.path.join(base_dir, "output", "agricultural", "Africa_and_Zambia_SWI_Maize_Merged_Long.csv")

print("Loading merged data...")
df = pd.read_csv(merged_path, usecols=['COUNTRY', 'ADM_NAME', 'date', 'swi_band', 'swi_value'])
df_zmb = df[df['COUNTRY'] == 'Zambia'].copy()

df_zmb['date'] = pd.to_datetime(df_zmb['date'])
df_zmb['month'] = df_zmb['date'].dt.month

print("Counting records per month by district (Zambia)...")
monthly_counts = df_zmb.groupby(['ADM_NAME', 'month']).size().unstack(fill_value=0)
print(monthly_counts.sum())

months_after_march = [m for m in range(4, 13) if m in monthly_counts.columns]
if months_after_march and monthly_counts[months_after_march].sum().sum() > 0:
    print("\nData DOES exist for months after March in Zambia:")
    print(monthly_counts[months_after_march].sum())
else:
    print("\nNO DATA exists for months after March in the Zambia dataset!")

print("\nSummary of records by month across all Zambia districts:")
print(df_zmb['month'].value_counts().sort_index())
