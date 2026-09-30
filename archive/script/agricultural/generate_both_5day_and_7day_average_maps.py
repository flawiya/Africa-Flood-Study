"""
generate_both_5day_and_7day_average_maps.py
============================================
Generates MATCHING Pan-African Average Annual Flood Days Choropleth Maps for both:
  1. 5-Day Continuous Streak Rule (`Average_Flood_Days_Map_5Day.html`)
  2. 7-Day Continuous Streak Rule (`Average_Flood_Days_Map.html` in meeting_24th_july_output & meeting_30th_july_output)

Formula:
  Average Annual Flood Days per District = (Sum of flood days across 17 crop years 2008–2024) / 17.0

Colorbar & Layout Settings:
- Each option has its own tailored zmax (Option 1, Option 2, Option 3) with tickformat='.1f' displaying decimal numbers.
- Identical map center (lat=2.5, lon=17.5) & zoom level.
- Identical Blues colorscale.
- Identical compact dropdown menus at top-left.
- Identical multi-line title wrapping to prevent text cutoff on narrow/split screens.
- Smooth scroll zoom (scrollZoom=True) and full responsiveness enabled.

Outputs to:
  `output/agricultural/meeting_30th_july_output/Average_Flood_Days_Map_5Day.html`
  `output/agricultural/meeting_30th_july_output/Option2_5Day_Average_Flood_Days_Map.html`
  `output/agricultural/meeting_30th_july_output/Average_Flood_Days_Map_7Day.html`
  `output/agricultural/meeting_24th_july_output/Average_Flood_Days_Map.html`
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

DIR_JULY30 = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output")
DIR_JULY24 = os.path.join(BASE_DIR, r"output\agricultural\meeting_24th_july_output")

os.makedirs(DIR_JULY30, exist_ok=True)
os.makedirs(DIR_JULY24, exist_ok=True)


def compute_streak_summary(df_in, flag_col, min_streak):
    """Compute continuous flood day streaks per district per crop year."""
    df_calc = df_in.copy()
    df_calc["block"] = (df_calc[flag_col] != df_calc.groupby(["COUNTRY", "ADM_NAME"])[flag_col].shift()).cumsum()
    df_calc["is_true"] = df_calc[flag_col]
    block_len = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])["is_true"].transform("sum")
    df_calc["valid_streak_day"] = df_calc["is_true"] & (block_len >= min_streak)

    summary = df_calc.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        flood_days=("valid_streak_day", "sum")
    ).reset_index()
    return summary


def build_average_map(df_map, geojson_dict, streak_days, out_paths, zmax_dict):
    """Build choropleth map with tailored option-specific zmax and decimal colorbar ticks."""
    num_streak_label = f"{streak_days}-Day"
    title_streak = f"≥{streak_days}-Day Continuous Streak"

    def create_choropleth(z_col, title, zmax_val):
        return go.Choroplethmap(
            geojson=geojson_dict,
            locations=df_map["ADM_NAME"],
            z=df_map[z_col],
            colorscale="Blues",
            zmin=0,
            zmax=zmax_val,
            marker_line_width=0.3,
            marker_line_color="rgba(0,0,0,0.25)",
            marker_opacity=0.85,
            customdata=np.stack([df_map["COUNTRY"], df_map[z_col].round(2)], axis=-1),
            hovertemplate=(
                "<b>%{location}</b> (%{customdata[0]})<br>"
                f"Average Flood Days/Year ({num_streak_label}): <b>%{{customdata[1]:.2f}} days/yr</b><br>"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Avg Days/Yr"),
                len=0.65,
                x=0.98,
                tickformat=".1f",  # SHOW DECIMAL NUMBERS ON SCALE
                tickfont=dict(size=10, color="#334155")
            ),
            name=title
        )

    fig = go.Figure()

    trace_opt2 = create_choropleth("avg_days_opt2", f"Option 2: P95 + SWI≥85% ({num_streak_label} Basis)", zmax_dict["opt2"])
    trace_opt1 = create_choropleth("avg_days_opt1", f"Option 1: P99 Relative ({num_streak_label} Basis)", zmax_dict["opt1"])
    trace_opt3 = create_choropleth("avg_days_opt3", f"Option 3: Pure SWI≥85% ({num_streak_label} Basis)", zmax_dict["opt3"])

    trace_opt2.visible = True
    trace_opt1.visible = False
    trace_opt3.visible = False

    fig.add_trace(trace_opt2)
    fig.add_trace(trace_opt1)
    fig.add_trace(trace_opt3)

    fig.update_layout(
        map=dict(
            style="carto-positron",
            center=dict(lat=2.5, lon=17.5),
            zoom=2.1
        ),
        title=dict(
            text=(f"<b>Average Annual Flood Days per District (2008–2024 Baseline) — {num_streak_label} Basis</b><br>"
                  f"<sup>Option 2 (95th Percentile + 85% SWI Floor) — {title_streak} Rule</sup>"),
            font=dict(size=14, color="#0f172a"),
            x=0.5,
            y=0.98
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
                        label=f"Option 2: P95 + 85% SWI ({num_streak_label} Basis - Recommended)",
                        method="update",
                        args=[{"visible": [True, False, False]},
                              {"title.text": f"<b>Option 2: 95th Percentile + 85% Absolute SWI Floor ({title_streak})</b>"}]
                    ),
                    dict(
                        label=f"Option 1: 99th Percentile Relative ({num_streak_label} Basis)",
                        method="update",
                        args=[{"visible": [False, True, False]},
                              {"title.text": f"<b>Option 1: 99th Percentile Relative Threshold ({title_streak})</b>"}]
                    ),
                    dict(
                        label=f"Option 3: Pure Absolute 85% SWI ({num_streak_label} Basis)",
                        method="update",
                        args=[{"visible": [False, False, True]},
                              {"title.text": f"<b>Option 3: Pure Absolute 85% SWI Floor ({title_streak})</b>"}]
                    )
                ],
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#cbd5e1",
                borderwidth=1,
                font=dict(size=11, color="#1e293b")
            )
        ],
        height=820,
        margin=dict(l=5, r=5, t=65, b=5),
        font=dict(family="Inter, sans-serif", color="#334155")
    )

    for path in out_paths:
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
        print(f"   [OK] Saved map to: {path}", flush=True)


def main():
    print("1. Loading raw SWI dataset...", flush=True)
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

    print("2. Keeping 2008–2024 (17 crop years)...", flush=True)
    df = df[~df["crop_year"].isin([2007, 2025])]

    print("3. Computing Option 1, 2, and 3 flags...", flush=True)
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    p99 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.99))

    df["flag_opt1"] = df["swi_t10_mean"] >= p99
    df["flag_opt2"] = (df["swi_t10_mean"] >= p95) & (df["swi_t10_mean"] >= 85.0)
    df["flag_opt3"] = df["swi_t10_mean"] >= 85.0

    print("4. Loading GADM agricultural district shapefile...", flush=True)
    gdf = gpd.read_file(SHP_PATH)[["ADM_NAME", "COUNTRY", "geometry"]]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["geometry"] = gdf["geometry"].simplify(0.05, preserve_topology=True)

    num_years = 17.0

    # ── BUILD 5-DAY MAP ──────────────────────────────────────────────────────
    print("\n5. Computing 5-Day Average Map...", flush=True)
    s5_opt1 = compute_streak_summary(df, "flag_opt1", min_streak=5)
    s5_opt2 = compute_streak_summary(df, "flag_opt2", min_streak=5)
    s5_opt3 = compute_streak_summary(df, "flag_opt3", min_streak=5)

    a5_opt1 = s5_opt1.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    a5_opt2 = s5_opt2.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    a5_opt3 = s5_opt3.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()

    a5_opt1["avg_days_opt1"] = (a5_opt1["flood_days"] / num_years).round(2)
    a5_opt2["avg_days_opt2"] = (a5_opt2["flood_days"] / num_years).round(2)
    a5_opt3["avg_days_opt3"] = (a5_opt3["flood_days"] / num_years).round(2)

    df_map5 = a5_opt2[["ISO3", "COUNTRY", "ADM_NAME", "avg_days_opt2"]].merge(
        a5_opt1[["ADM_NAME", "avg_days_opt1"]], on="ADM_NAME"
    ).merge(
        a5_opt3[["ADM_NAME", "avg_days_opt3"]], on="ADM_NAME"
    )

    gdf_f5 = gdf[gdf["ADM_NAME"].isin(df_map5["ADM_NAME"])].copy()
    geo5 = json.loads(gdf_f5.set_index("ADM_NAME").to_json())

    paths_5day = [
        os.path.join(DIR_JULY30, "Average_Flood_Days_Map_5Day.html"),
        os.path.join(DIR_JULY30, "Option2_5Day_Average_Flood_Days_Map.html")
    ]
    # Option-specific zmax for 5-day
    zmax_5day = {"opt1": 4.0, "opt2": 10.0, "opt3": 25.0}
    build_average_map(df_map5, geo5, streak_days=5, out_paths=paths_5day, zmax_dict=zmax_5day)

    # ── BUILD 7-DAY MAP ──────────────────────────────────────────────────────
    print("\n6. Computing 7-Day Average Map...", flush=True)
    s7_opt1 = compute_streak_summary(df, "flag_opt1", min_streak=7)
    s7_opt2 = compute_streak_summary(df, "flag_opt2", min_streak=7)
    s7_opt3 = compute_streak_summary(df, "flag_opt3", min_streak=7)

    a7_opt1 = s7_opt1.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    a7_opt2 = s7_opt2.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()
    a7_opt3 = s7_opt3.groupby(["ISO3", "COUNTRY", "ADM_NAME"])["flood_days"].sum().reset_index()

    a7_opt1["avg_days_opt1"] = (a7_opt1["flood_days"] / num_years).round(2)
    a7_opt2["avg_days_opt2"] = (a7_opt2["flood_days"] / num_years).round(2)
    a7_opt3["avg_days_opt3"] = (a7_opt3["flood_days"] / num_years).round(2)

    df_map7 = a7_opt2[["ISO3", "COUNTRY", "ADM_NAME", "avg_days_opt2"]].merge(
        a7_opt1[["ADM_NAME", "avg_days_opt1"]], on="ADM_NAME"
    ).merge(
        a7_opt3[["ADM_NAME", "avg_days_opt3"]], on="ADM_NAME"
    )

    gdf_f7 = gdf[gdf["ADM_NAME"].isin(df_map7["ADM_NAME"])].copy()
    geo7 = json.loads(gdf_f7.set_index("ADM_NAME").to_json())

    paths_7day = [
        os.path.join(DIR_JULY30, "Average_Flood_Days_Map_7Day.html"),
        os.path.join(DIR_JULY24, "Average_Flood_Days_Map.html")
    ]
    # Tailored zmax for 7-day matching original
    zmax_7day = {"opt1": 1.5, "opt2": 4.0, "opt3": 15.0}
    build_average_map(df_map7, geo7, streak_days=7, out_paths=paths_7day, zmax_dict=zmax_7day)

    print("\n======================================================================")
    print("DONE - Generated maps with decimal colorbar scales & tailored zmax.")
    print("======================================================================")


if __name__ == "__main__":
    main()
