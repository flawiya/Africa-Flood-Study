"""
generate_option2_5day_average_flood_map.py
===========================================
Generates the Pan-African Average Annual Flood Days Choropleth Map for Option 2
(95th Percentile + 85% Absolute SWI Floor on a 5-Day Continuous Basis across 2008–2024).

Mirroring the format and interactive features of Average_Flood_Days_Map.html:
- Smooth scroll zoom enabled (scrollZoom=True)
- CARTO Positron basemap
- Dropdown menu allowing seamless switching between:
    1. Option 2: 95th Percentile + 85% Absolute SWI (5-Day Basis - Recommended)
    2. Option 1: 99th Percentile Relative (5-Day Basis)
    3. Option 3: Pure Absolute 85% SWI (5-Day Basis)
- Detailed hovercards with District, Country, and Average Flood Days/Year (5-Day Basis).
- Saved without colleague names or corporate branding.

Outputs to:
  `output/agricultural/meeting_30th_july_output/Option2_5Day_Average_Flood_Days_Map.html`
  `output/agricultural/meeting_30th_july_output/Average_Flood_Days_Map_5Day.html`
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_PATH1 = os.path.join(OUT_DIR, "Option2_5Day_Average_Flood_Days_Map.html")
OUT_PATH2 = os.path.join(OUT_DIR, "Average_Flood_Days_Map_5Day.html")


def compute_streak_summary(df_in, flag_col, min_streak=5):
    """Compute 5-day continuous flood day streaks per district per crop year."""
    df_calc = df_in.copy()
    df_calc["block"] = (df_calc[flag_col] != df_calc.groupby(["COUNTRY", "ADM_NAME"])[flag_col].shift()).cumsum()
    df_calc["is_true"] = df_calc[flag_col]
    block_len = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])["is_true"].transform("sum")
    df_calc["valid_streak_day"] = df_calc["is_true"] & (block_len >= min_streak)
    
    summary = df_calc.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        flood_days=("valid_streak_day", "sum")
    ).reset_index()
    return summary


def main():
    print("1. Loading daily SWI dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["doy"] = df["date"].dt.dayofyear
    df["crop_year"] = df["date"].dt.year

    plant_doy = pd.to_numeric(df["planting"], errors="coerce")
    harvest_doy = pd.to_numeric(df["harvest"], errors="coerce")
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df["doy"] >= (plant_doy - 15))
    df.loc[shift_mask, "crop_year"] += 1

    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    df = df[df["COUNTRY"] != "Morocco"]

    print("2. Excluding edge years (keeping 2008–2024: 17 crop years)...", flush=True)
    df = df[~df["crop_year"].isin([2007, 2025])]

    print("3. Computing Option 1, 2, and 3 flags (5-day basis)...", flush=True)
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    p99 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.99))
    
    df["flag_opt1"] = df["swi_t10_mean"] >= p99
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)
    df["flag_opt3"] = df["swi_t10_mean"] >= 85.0

    print("4. Calculating 5-day continuous streak summaries...", flush=True)
    sum_opt1 = compute_streak_summary(df, "flag_opt1", min_streak=5)
    sum_opt2 = compute_streak_summary(df, "flag_opt2", min_streak=5)
    sum_opt3 = compute_streak_summary(df, "flag_opt3", min_streak=5)

    num_years = 17.0
    
    avg_opt1 = sum_opt1.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    avg_opt2 = sum_opt2.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    avg_opt3 = sum_opt3.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()

    avg_opt1["avg_days_opt1"] = (avg_opt1["flood_days"] / num_years).round(2)
    avg_opt2["avg_days_opt2"] = (avg_opt2["flood_days"] / num_years).round(2)
    avg_opt3["avg_days_opt3"] = (avg_opt3["flood_days"] / num_years).round(2)

    df_map = avg_opt2[["ISO3", "COUNTRY", "ADM_NAME", "avg_days_opt2"]].merge(
        avg_opt1[["ADM_NAME", "avg_days_opt1"]], on="ADM_NAME"
    ).merge(
        avg_opt3[["ADM_NAME", "avg_days_opt3"]], on="ADM_NAME"
    )

    print("5. Loading GADM agricultural district shapefile...", flush=True)
    gdf = gpd.read_file(SHP_PATH)[["ADM_NAME", "COUNTRY", "geometry"]]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["geometry"] = gdf["geometry"].simplify(0.05, preserve_topology=True)
    gdf_filtered = gdf[gdf["ADM_NAME"].isin(df_map["ADM_NAME"])].copy()
    geojson_dict = json.loads(gdf_filtered.set_index("ADM_NAME").to_json())

    print("6. Generating interactive Choropleth Map with smooth scroll zoom...", flush=True)

    def create_choropleth(z_col, title, zmax):
        return go.Choroplethmap(
            geojson=geojson_dict,
            locations=df_map["ADM_NAME"],
            z=df_map[z_col],
            colorscale="Blues",
            zmin=0,
            zmax=zmax,
            marker_line_width=0.4,
            marker_line_color="rgba(0,0,0,0.3)",
            marker_opacity=0.85,
            customdata=np.stack([df_map["COUNTRY"], df_map[z_col].round(2)], axis=-1),
            hovertemplate=(
                "<b>%{location}</b> (%{customdata[0]})<br>"
                "Average Flood Days/Year (≥5d streak): <b>%{customdata[1]:.2f} days/yr</b><br>"
                "<extra></extra>"
            ),
            colorbar=dict(title=dict(text="Avg Days/Yr"), len=0.7, x=0.98),
            name=title
        )

    fig = go.Figure()
    
    trace_opt2 = create_choropleth("avg_days_opt2", "Option 2: P95 + SWI≥85% (Recommended)", zmax=15)
    trace_opt1 = create_choropleth("avg_days_opt1", "Option 1: P99 Relative", zmax=15)
    trace_opt3 = create_choropleth("avg_days_opt3", "Option 3: Pure SWI≥85%", zmax=25)

    # Option 2 visible by default
    trace_opt2.visible = True
    trace_opt1.visible = False
    trace_opt3.visible = False

    fig.add_trace(trace_opt2)
    fig.add_trace(trace_opt1)
    fig.add_trace(trace_opt3)

    fig.update_layout(
        map=dict(
            style="carto-positron",
            center=dict(lat=2.0, lon=18.0),
            zoom=2.3
        ),
        title=dict(
            text="<b>Average Annual Flood Days per District (2008–2024 Baseline) — 5-Day Continuous Basis</b><br><sup>Option 2 (95th Percentile + 85% SWI Floor) — Recommended Parametric Threshold</sup>",
            font=dict(size=15, color="#0f172a"),
            x=0.5
        ),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                active=0,
                x=0.01,
                y=0.98,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="Option 2: P95 + 85% Absolute SWI (Recommended - 5-Day Basis)",
                        method="update",
                        args=[{"visible": [True, False, False]}, {"title.text": "<b>Option 2: 95th Percentile + 85% Absolute SWI Floor (5-Day Continuous Basis)</b>"}]
                    ),
                    dict(
                        label="Option 1: 99th Percentile Relative (5-Day Basis)",
                        method="update",
                        args=[{"visible": [False, True, False]}, {"title.text": "<b>Option 1: 99th Percentile Relative Threshold (5-Day Continuous Basis)</b>"}]
                    ),
                    dict(
                        label="Option 3: Pure Absolute 85% SWI (5-Day Basis)",
                        method="update",
                        args=[{"visible": [False, False, True]}, {"title.text": "<b>Option 3: Pure Absolute 85% SWI Floor (5-Day Continuous Basis)</b>"}]
                    )
                ],
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#cbd5e1",
                borderwidth=1
            )
        ],
        height=850,
        margin=dict(l=10, r=10, t=70, b=10)
    )

    # Save HTML output with full smooth scroll zoom configuration
    for path in [OUT_PATH1, OUT_PATH2]:
        fig.write_html(
            path,
            full_html=True,
            include_plotlyjs="cdn",
            config={
                "scrollZoom": True,
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToAdd": ["hoverClosestCartesian", "hoverCompareCartesian"],
                "responsive": True
            }
        )
        print(f"   [OK] Saved zoom-enabled map to: {path}", flush=True)

if __name__ == "__main__":
    main()
