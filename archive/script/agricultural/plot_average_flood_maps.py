import os
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\meeting_24th_july_output")

def compute_streak_summary(df_in, flag_col):
    df_calc = df_in.copy()
    df_calc["block"] = (df_calc[flag_col] != df_calc.groupby(["COUNTRY", "ADM_NAME"])[flag_col].shift()).cumsum()
    block_len = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])[flag_col].transform(lambda s: s.sum() if s.iloc[0] else 0)
    
    df_calc["valid_streak_day"] = df_calc[flag_col] & (block_len >= 7)
    
    summary = df_calc.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        flood_days_7plus=("valid_streak_day", "sum")
    ).reset_index()
    
    return summary

def main():
    print("Loading master dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year
    
    # Harvest Year logic
    plant_doy = pd.to_numeric(df["planting"], errors='coerce')
    harvest_doy = pd.to_numeric(df["harvest"], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1
    
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    
    print("Excluding truncated boundaries (2007 and 2025)...", flush=True)
    df = df[~df["crop_year"].isin([2007, 2025])]

    print("Computing thresholds...", flush=True)
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    p99 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.99))
    df["p95"] = p95
    df["p99"] = p99

    df["flag_opt1"] = df["swi_t10_mean"] >= df["p99"]
    df["flag_opt2"] = (df["swi_t10_mean"] >= df["p95"]) & (df["swi_t10_mean"] >= 85.0)
    df["flag_opt3"] = df["swi_t10_mean"] >= 85.0

    print("Calculating streaks for Option 1...", flush=True)
    sum_opt1 = compute_streak_summary(df, "flag_opt1")
    print("Calculating streaks for Option 2...", flush=True)
    sum_opt2 = compute_streak_summary(df, "flag_opt2")
    print("Calculating streaks for Option 3...", flush=True)
    sum_opt3 = compute_streak_summary(df, "flag_opt3")
    
    # Calculate historical average (sum over the years per district divided by 18)
    avg_opt1 = sum_opt1.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()
    avg_opt2 = sum_opt2.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()
    avg_opt3 = sum_opt3.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()
    
    avg_opt1['flood_days_7plus'] = avg_opt1['flood_days_7plus'] / 18.0
    avg_opt2['flood_days_7plus'] = avg_opt2['flood_days_7plus'] / 18.0
    avg_opt3['flood_days_7plus'] = avg_opt3['flood_days_7plus'] / 18.0
    
    avg_opt1.rename(columns={'flood_days_7plus': 'avg_days_opt1'}, inplace=True)
    avg_opt2.rename(columns={'flood_days_7plus': 'avg_days_opt2'}, inplace=True)
    avg_opt3.rename(columns={'flood_days_7plus': 'avg_days_opt3'}, inplace=True)
    
    df_map = avg_opt1.merge(avg_opt2[['ADM_NAME', 'avg_days_opt2']], on='ADM_NAME')
    df_map = df_map.merge(avg_opt3[['ADM_NAME', 'avg_days_opt3']], on='ADM_NAME')
    
    print("Loading shapefile...", flush=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'geometry']]
    gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)
    gdf_filtered = gdf[gdf['ADM_NAME'].isin(df_map['ADM_NAME'])].copy()
    geojson_dict = json.loads(gdf_filtered.set_index('ADM_NAME').to_json())
    
    print("Generating Maps...", flush=True)
    
    def create_choropleth(z_col, title, zmax):
        return go.Choroplethmap(
            geojson=geojson_dict,
            locations=df_map['ADM_NAME'],
            z=df_map[z_col],
            colorscale="Blues",
            zmin=0,
            zmax=zmax,
            marker_line_width=0.4,
            marker_line_color='rgba(0,0,0,0.3)',
            marker_opacity=0.8,
            hovertemplate=(
                "<b>%{location}</b><br>"
                "Avg Flood Days / Year: <b>%{z:.2f}</b><extra></extra>"
            ),
            colorbar=dict(title=dict(text="Avg Days"), len=0.7),
        )

    fig = go.Figure()
    
    trace_opt1 = create_choropleth('avg_days_opt1', 'Option 1', zmax=1.0)
    trace_opt2 = create_choropleth('avg_days_opt2', 'Option 2', zmax=4.0)
    trace_opt3 = create_choropleth('avg_days_opt3', 'Option 3', zmax=15.0)
    
    trace_opt1.visible = True
    trace_opt2.visible = False
    trace_opt3.visible = False

    fig.add_trace(trace_opt1)
    fig.add_trace(trace_opt2)
    fig.add_trace(trace_opt3)
    
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=2.0, lon=18.0), zoom=2.3),
        title_text="Average Historical Flood Days per Year (2008-2024)",
        title_x=0.5,
        margin=dict(l=10, r=10, t=60, b=10),
        height=800,
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            active=0,
            x=0.01,
            y=0.99,
            buttons=list([
                dict(label="Option 1 (99th %ile)",
                     method="update",
                     args=[{"visible": [True, False, False]}]),
                dict(label="Option 2 (95th %ile + 85%)",
                     method="update",
                     args=[{"visible": [False, True, False]}]),
                dict(label="Option 3 (Absolute > 85%)",
                     method="update",
                     args=[{"visible": [False, False, True]}]),
            ]),
        )]
    )
    
    out_path = os.path.join(OUT_DIR, "Historical_Average_Flood_Maps.html")
    fig.write_html(out_path)
    print(f"Maps saved to {out_path}", flush=True)

if __name__ == "__main__":
    main()
