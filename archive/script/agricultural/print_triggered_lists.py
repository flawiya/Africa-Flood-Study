import os
import pandas as pd

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
CSV_PATH = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output\Triggered_Districts_5Day_Kenya_Malawi_Nigeria.csv")

df = pd.read_csv(CSV_PATH)
df["triggered_years"] = df["triggered_years"].apply(eval)

for cntry in ["Kenya"]:
    sub = df[df["COUNTRY"] == cntry].sort_values("ADM_NAME")
    print(f"\n=================== {cntry.upper()} ({len(sub)} Districts) ===================")
    for _, row in sub.iterrows():
        years_str = ", ".join(map(str, row["triggered_years"]))
        print(f"- **{row['ADM_NAME']}**: [{years_str}] ({row['total_triggered_years']} yrs triggered)")
