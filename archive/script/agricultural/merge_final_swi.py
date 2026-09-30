import pandas as pd
import os

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE_DIR, "output", "agricultural")

file1 = os.path.join(OUT_DIR, "Africa_and_Zambia_SWI_Maize_Merged_Long.csv")
file2 = os.path.join(OUT_DIR, "Africa_SWI_Maize_Missing_2015_2025.csv")
out_file = os.path.join(OUT_DIR, "Africa_SWI_Maize_Full_2007_2025.csv")

print("Loading original dataset (2007-2014 Africa + 2007-2024 Zambia)...")
df1 = pd.read_csv(file1)

print("Loading new downloaded dataset (2015-2025 Africa missing)...")
df2 = pd.read_csv(file2)

print("Concatenating datasets...")
df_full = pd.concat([df1, df2], ignore_index=True)

print(f"Saving fully combined dataset ({len(df_full)} rows) to: {out_file}")
df_full.to_csv(out_file, index=False)
print("Merge complete!")
