import pandas as pd
import os
import sys

def main():
    base_dir = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
    out_dir = os.path.join(base_dir, "output", "agricultural")
    
    africa_t10_path = os.path.join(out_dir, "Africa_SWI_Maize_2007_2024.csv")
    africa_t40_path = os.path.join(out_dir, "Africa_SWI_Maize_2007_2025.csv")
    zambia_path = os.path.join(out_dir, "Zambia_SWI_Maize_MultiBand_2007_2024.csv")
    
    merged_output_path = os.path.join(out_dir, "Africa_and_Zambia_SWI_Maize_Merged_Long.csv")
    
    print("Loading Africa T10 data...")
    df_t10 = pd.read_csv(africa_t10_path)
    print("Loading Africa T40 data...")
    df_t40 = pd.read_csv(africa_t40_path)
    
    # Drop cal_country from T40 if it exists to match T10 columns
    if 'cal_country' in df_t40.columns:
        df_t40 = df_t40.drop(columns=['cal_country'])
        
    print("Merging Africa T10 and T40 data...")
    # The common columns are date, ISO3, COUNTRY, ADM_NAME, cal_region, crop, planting_doy, harvest_doy
    common_cols = ['date', 'ISO3', 'COUNTRY', 'ADM_NAME', 'cal_region', 'crop', 'planting_doy', 'harvest_doy']
    
    # We do an outer join on common columns
    df_africa = pd.merge(df_t10, df_t40, on=common_cols, how='outer')
    
    print("Loading Zambia data...")
    df_zambia = pd.read_csv(zambia_path)
    
    # Add missing metadata columns for Zambia
    df_zambia['ISO3'] = 'ZMB'
    df_zambia['COUNTRY'] = 'Zambia'
    df_zambia['cal_region'] = 'National' # Placeholder or based on actual data
    df_zambia['crop'] = 'Maize 1' # Assuming Maize 1
    df_zambia['planting_doy'] = pd.NA
    df_zambia['harvest_doy'] = pd.NA
    
    print("Concatenating Africa and Zambia data...")
    # Reorder Zambia columns to match Africa
    df_zambia = df_zambia[['date', 'ISO3', 'COUNTRY', 'ADM_NAME', 'cal_region', 'crop', 'planting_doy', 'harvest_doy', 'swi_010', 'swi_040']]
    
    df_final_wide = pd.concat([df_africa, df_zambia], ignore_index=True)
    
    print("Melting to long format...")
    # Melt swi_010 and swi_040 into a single column
    df_long = df_final_wide.melt(
        id_vars=common_cols,
        value_vars=['swi_010', 'swi_040'],
        var_name='swi_band',
        value_name='swi_value'
    )
    
    # Drop rows where swi_value is NaN (to save space)
    df_long = df_long.dropna(subset=['swi_value'])
    
    print(f"Saving merged long format data to {merged_output_path}...")
    df_long.to_csv(merged_output_path, index=False)
    
    print("Done!")

if __name__ == "__main__":
    main()
