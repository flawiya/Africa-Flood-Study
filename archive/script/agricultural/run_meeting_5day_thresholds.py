"""
SWI Flood Index - 30th July Meeting Threshold Analysis (5-Day Continuous Flood Rule)
=====================================================================================
Generates 3 HTML dashboards with:
- Panel A — Animated Map
- Panel B — District Spaghetti Plot with Marked Historical Case Study Points
- Panel C — Annual Flood Days Distribution (Violin Plot per Year, 2008–2024)

Outputs saved to: `output/agricultural/meeting_30th_july_output/`
"""

import os, sys, json, numpy as np, pandas as pd, geopandas as gpd
import plotly.graph_objects as go

BASE_DIR = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv")
SHP_PATH = os.path.join(BASE_DIR, r"data\africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, r"output\agricultural\meeting_30th_july_output")
os.makedirs(OUT_DIR, exist_ok=True)

# Marked Case Study Benchmark Events (Highlighting Major Baseline + NEW 5-Day Triggers Across Africa)
MARKED_EVENTS = [
    # Baseline 17th July Major Benchmark Events
    {"country": "Tanzania", "district": "Kasulu", "year": 2024, "label": "Kasulu (2024)", "color": "#ef4444"},
    {"country": "Malawi", "district": "Lilongwe City", "year": 2019, "label": "Lilongwe (2019)", "color": "#f97316"},
    {"country": "Malawi", "district": "Chikwawa", "year": 2019, "label": "Chikwawa (2019)", "color": "#f97316"},
    {"country": "Nigeria", "district": "Lokoja", "year": 2012, "label": "Lokoja (2012)", "color": "#eab308"},
    
    # NEW 5-Day Triggers Across Africa (0 days under 7-day baseline!)
    {"country": "Nigeria", "district": "Oyo West", "year": 2022, "label": "⭐ Nigeria: Oyo West (2022 - NEW 5d)", "color": "#10b981"},
    {"country": "Kenya", "district": "Ndhiwa", "year": 2024, "label": "⭐ Kenya: Ndhiwa (2024 - NEW 5d)", "color": "#06b6d4"},
    {"country": "Guinea-Bissau", "district": "Bula", "year": 2022, "label": "⭐ Guinea-Bissau: Bula (2022 - NEW 5d)", "color": "#3b82f6"},
    {"country": "Democratic Republic of the Congo", "district": "Pweto", "year": 2018, "label": "⭐ DR Congo: Pweto (2018 - NEW 5d)", "color": "#8b5cf6"},
    {"country": "Angola", "district": "Ukuma", "year": 2024, "label": "⭐ Angola: Ukuma (2024 - NEW 5d)", "color": "#ec4899"},
    {"country": "Chad", "district": "Mont Illi", "year": 2022, "label": "⭐ Chad: Mont Illi (2022 - NEW 5d)", "color": "#f43f5e"},
    {"country": "Namibia", "district": "Ondangwa", "year": 2012, "label": "⭐ Namibia: Ondangwa (2012 - NEW 5d)", "color": "#14b8a6"},
    {"country": "Guinea", "district": "Forécariah", "year": 2024, "label": "⭐ Guinea: Forécariah (2024 - NEW 5d)", "color": "#a855f7"},
    {"country": "Tanzania", "district": "Mbinga", "year": 2023, "label": "⭐ Tanzania: Mbinga (2023 - NEW 5d)", "color": "#84cc16"},
    
    # Additional Expanded Pan-African NEW 5-Day Triggers
    {"country": "Benin", "district": "Kalalé", "year": 2019, "label": "⭐ Benin: Kalalé (2019 - NEW 5d)", "color": "#f59e0b"},
    {"country": "Ghana", "district": "Akatsi North", "year": 2019, "label": "⭐ Ghana: Akatsi North (2019 - NEW 5d)", "color": "#10b981"},
    {"country": "Uganda", "district": "Bamunanika", "year": 2008, "label": "⭐ Uganda: Bamunanika (2008 - NEW 5d)", "color": "#6366f1"},
    {"country": "Burundi", "district": "Nyanrusange", "year": 2020, "label": "⭐ Burundi: Nyanrusange (2020 - NEW 5d)", "color": "#d946ef"},
    {"country": "Mozambique", "district": "Metarica", "year": 2023, "label": "⭐ Mozambique: Metarica (2023 - NEW 5d)", "color": "#0284c7"},
    {"country": "Zambia", "district": "Mkushi", "year": 2022, "label": "⭐ Zambia: Mkushi (2022 - NEW 5d)", "color": "#059669"},
    {"country": "Ethiopia", "district": "Hadiya", "year": 2022, "label": "⭐ Ethiopia: Hadiya (2022 - NEW 5d)", "color": "#b45309"},
]

def compute_streak_summary(df_in, flag_col, combo_name):
    print(f"  Calculating streaks for {combo_name}...", flush=True)
    df_calc = df_in.copy()
    df_calc["block"] = (df_calc[flag_col] != df_calc.groupby(["COUNTRY", "ADM_NAME"])[flag_col].shift()).cumsum()
    block_len = df_calc.groupby(["COUNTRY", "ADM_NAME", "block"])[flag_col].transform(lambda s: s.sum() if s.iloc[0] else 0)
    
    df_calc["valid_streak_day_5"] = df_calc[flag_col] & (block_len >= 5)
    df_calc["valid_streak_day_7"] = df_calc[flag_col] & (block_len >= 7)
    df_calc["max_streak_len"]     = block_len
    
    summary = df_calc.groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"]).agg(
        planting=("planting", "first"),
        harvest=("harvest", "first"),
        mean_swi=("swi_t10_mean", "mean"),
        max_swi=("swi_t10_mean", "max"),
        flood_days_5plus=("valid_streak_day_5", "sum"),
        flood_days_7plus=("valid_streak_day_7", "sum"),
        max_consec_days=("max_streak_len", "max")
    ).reset_index()

    summary["mean_swi"] = summary["mean_swi"].round(2)
    summary["max_swi"]  = summary["max_swi"].round(2)
    
    events = df_calc[df_calc["valid_streak_day_5"]].groupby(["ISO3", "COUNTRY", "ADM_NAME", "crop_year"])["block"].nunique().reset_index()
    events.rename(columns={"block": "num_flood_events"}, inplace=True)
    
    summary = summary.merge(events, on=["ISO3", "COUNTRY", "ADM_NAME", "crop_year"], how="left").fillna({"num_flood_events": 0})
    summary["num_flood_events"] = summary["num_flood_events"].astype(int)
    
    return summary

def main():
    print("[30th July Meeting Script] Loading master dataset...", flush=True)
    df = pd.read_csv(DATA_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["crop_year"] = df["date"].dt.year
    df = df.sort_values(["COUNTRY", "ADM_NAME", "date"])
    df = df[df["COUNTRY"] != "Morocco"]
    print(f"Total rows loaded: {len(df):,}", flush=True)

    # 1. Compute per-district historical P95 and P99 percentiles
    print("Computing per-district P95 and P99 thresholds...", flush=True)
    p95 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.95))
    p99 = df.groupby(["COUNTRY", "ADM_NAME"])["swi_t10_mean"].transform(lambda x: x.quantile(0.99))
    df["p95"] = p95
    df["p99"] = p99

    # 2. Daily Flags for the 3 Exact Meeting Options
    df["flag_opt1"] = df["swi_t10_mean"] >= df["p99"]
    df["flag_opt2"] = (df["swi_t10_mean"] >= df["p95"]) & (df["swi_t10_mean"] >= 85.0)
    df["flag_opt3"] = df["swi_t10_mean"] >= 85.0

    df_opt1 = compute_streak_summary(df, "flag_opt1", "Option 1 (99th Percentile)")
    df_opt2 = compute_streak_summary(df, "flag_opt2", "Option 2 (95th %ile + Absolute SWI >= 85%)")
    df_opt3 = compute_streak_summary(df, "flag_opt3", "Option 3 (Pure Absolute SWI >= 85%)")

    # Save summary CSV files to destination folder
    path_opt1 = os.path.join(OUT_DIR, "option1_99th_percentile_5day_summary.csv")
    path_opt2 = os.path.join(OUT_DIR, "option2_95th_plus_absolute_5day_summary.csv")
    path_opt3 = os.path.join(OUT_DIR, "option3_pure_absolute_5day_summary.csv")

    df_opt1.to_csv(path_opt1, index=False)
    df_opt2.to_csv(path_opt2, index=False)
    df_opt3.to_csv(path_opt3, index=False)

    # 3. Save Calibration Summary Table CSV
    def get_stats(df_sub, name):
        arr = df_sub["flood_days_5plus"]
        return {
            "Meeting Option": name,
            "Mean_Days_Per_Year": round(arr.mean(), 2),
            "Median_Days_Per_Year": round(arr.median(), 2),
            "90th_Percentile_Bad_Year": round(np.percentile(arr, 90), 1),
            "95th_Percentile_Severe_Year": round(np.percentile(arr, 95), 1),
            "99th_Percentile_Worst_Disaster": round(np.percentile(arr, 99), 1),
            "Absolute_Max_Days": int(arr.max())
        }

    calib_list = [
        get_stats(df_opt1, "Option 1: 99th Percentile (>=5 Consec Days)"),
        get_stats(df_opt2, "Option 2: 95th %ile + SWI>=85% (>=5 Consec Days) [WINNER]"),
        get_stats(df_opt3, "Option 3: Pure Absolute SWI>=85% (>=5 Consec Days)")
    ]

    df_calib = pd.DataFrame(calib_list)
    calib_csv_path = os.path.join(OUT_DIR, "meeting_30th_july_calibration_summary.csv")
    df_calib.to_csv(calib_csv_path, index=False)

    print("\n================ MEETING 30TH JULY CALIBRATION SUMMARY (5-DAY RULE) ================", flush=True)
    print(df_calib.to_string(index=False), flush=True)

    # 4. Generate Full 3-Panel HTML Dashboards (Map + Marked Spaghetti Plot + Violin Plot)
    build_full_dashboards(df_opt1, df_opt2, df_opt3)

def build_full_dashboards(df_opt1, df_opt2, df_opt3):
    print("\nBuilding 3-panel HTML dashboards (Map + Marked Spaghetti Plot + Violin Plot) for each option...", flush=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
    gdf = gdf[gdf['COUNTRY'] != 'Morocco']
    gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)

    combos = [
        (df_opt1, "Option1_99th_Percentile_5Day_Dashboard.html", "Option 1: 99th Percentile (>=5 Consecutive Days)", "99th Percentile per district"),
        (df_opt2, "Option2_95th_plus_Absolute_5Day_Dashboard.html", "Option 2: 95th %ile + Absolute SWI>=85% (>=5 Consecutive Days)", "95th Percentile AND SWI >= 85%"),
        (df_opt3, "Option3_Pure_Absolute_5Day_Dashboard.html", "Option 3: Pure Absolute SWI>=85% (>=5 Consecutive Days)", "Pure Absolute SWI >= 85%")
    ]

    for df_sub, filename, title_text, desc_text in combos:
        df_sub['crop_year'] = df_sub['crop_year'].astype(int)
        districts = df_sub[['COUNTRY', 'ADM_NAME']].drop_duplicates()
        years = sorted(df_sub['crop_year'].unique())
        
        grid = pd.MultiIndex.from_product([districts['ADM_NAME'], years], names=['ADM_NAME', 'crop_year']).to_frame(index=False)
        grid = grid.merge(districts, on='ADM_NAME', how='left')
        df_plot = grid.merge(df_sub[['ADM_NAME', 'crop_year', 'flood_days_5plus', 'flood_days_7plus', 'max_consec_days']], on=['ADM_NAME', 'crop_year'], how='left').fillna(0)
        
        gdf_filtered = gdf[gdf['ADM_NAME'].isin(districts['ADM_NAME'])].copy()
        geojson_dict = json.loads(gdf_filtered.set_index('ADM_NAME').to_json())

        COLOR_MAX = 25

        # --- PANEL A: Map ---
        def make_choropleth(year_df):
            return go.Choroplethmapbox(
                geojson=geojson_dict,
                locations=year_df['ADM_NAME'].tolist(),
                z=year_df['flood_days_5plus'].tolist(),
                colorscale="Blues",
                zmin=0,
                zmax=COLOR_MAX,
                colorbar=dict(
                    title=dict(text="Flood Days<br>(>=5 Consec Days)", font=dict(size=11)),
                    tickvals=[0, 5, 10, 15, 25],
                    ticktext=["0", "5", "10", "15", "25+"],
                    len=0.55, x=1.0
                ),
                marker_line_width=0.4,
                marker_line_color='rgba(0,0,0,0.3)',
                marker_opacity=0.8,
                customdata=np.stack([
                    year_df['COUNTRY'].tolist(),
                    year_df['flood_days_5plus'].tolist(),
                    year_df['max_consec_days'].tolist(),
                ], axis=-1),
                hovertemplate=(
                    "<b>%{location}</b> (%{customdata[0]})<br>"
                    "Days in >=5-day streaks: <b>%{customdata[1]:.0f}</b><br>"
                    "Longest streak this year: <b>%{customdata[2]:.0f} days</b>"
                    "<extra></extra>"
                ),
                name=""
            )

        base_trace = make_choropleth(df_plot[df_plot['crop_year'] == years[0]])
        frames = [
            go.Frame(
                data=[make_choropleth(df_plot[df_plot['crop_year'] == yr])],
                name=str(yr),
                layout=go.Layout(annotations=[dict(text=f"Year: <b>{yr}</b>", xref="paper", yref="paper", x=0.5, y=0.98, xanchor='center', font=dict(size=22, color='#0f172a'), showarrow=False, bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1, borderpad=4)])
            ) for yr in years
        ]

        fig_map = go.Figure(
            data=[base_trace], frames=frames,
            layout=go.Layout(
                mapbox=dict(style="carto-positron", center=dict(lat=2.0, lon=18.0), zoom=2.3),
                updatemenus=[dict(
                    type='buttons', showactive=False, y=-0.05, x=0.0, xanchor='left', yanchor='top', direction='right', pad={"r": 10, "t": 20},
                    buttons=[
                        dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=700, redraw=True), fromcurrent=True, mode='immediate', transition=dict(duration=300))]),
                        dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate', transition=dict(duration=0))])
                    ]
                )],
                sliders=[dict(active=0, steps=[dict(args=[[str(yr)], dict(frame=dict(duration=600, redraw=True), mode='immediate', transition=dict(duration=300))], label=str(yr), method='animate') for yr in years], x=0.1, y=-0.05, len=0.9, pad=dict(b=10, t=20))],
                height=650, margin=dict(l=0, r=0, t=30, b=80), paper_bgcolor='white'
            )
        )

        # --- PANEL B: Marked Spaghetti Plot ---
        fig_spag = go.Figure()
        # Highlight all districts that triggered under the 5-day streak rule (flood_days_5plus >= 5)
        affected_districts = df_plot[df_plot['flood_days_5plus'] >= 5]['ADM_NAME'].unique()

        for dist in sorted(df_plot['ADM_NAME'].unique()):
            d_df = df_plot[df_plot['ADM_NAME'] == dist].sort_values('crop_year')
            cntry = d_df['COUNTRY'].iloc[0] if len(d_df) > 0 else ''
            is_aff = dist in affected_districts
            
            y_jit = d_df['flood_days_5plus'] + np.random.uniform(-0.3, 0.3)
            l_col = 'rgba(56,189,248,0.25)' if is_aff else 'rgba(148,163,184,0.06)'
            l_wid = 1
            m_mark = dict(size=5, opacity=0.7, color='rgba(56,189,248,0.8)') if is_aff else dict(size=4, opacity=0.2, color='rgba(148,163,184,0.2)')
            
            fig_spag.add_trace(go.Scatter(
                x=d_df['crop_year'], y=y_jit, mode='lines+markers', name=f"{dist} ({cntry})", showlegend=False,
                marker=m_mark, line=dict(color=l_col, width=l_wid),
                customdata=np.stack([[cntry] * len(d_df), d_df['flood_days_5plus'].tolist(), d_df['max_consec_days'].tolist()], axis=-1),
                hovertemplate=f"<b>{dist}</b> ({cntry})<br>Year: <b>%{{x}}</b><br>Flood Days (>=5d): <b>%{{customdata[1]:.0f}}</b><br>Longest streak: <b>%{{customdata[2]:.0f}}d</b><extra></extra>"
            ))

        # Add Marked Case Study Points on Spaghetti Plot (uniform Royal Circle with white border)
        for ev in MARKED_EVENTS:
            sub = df_plot[(df_plot['COUNTRY'] == ev['country']) & (df_plot['ADM_NAME'] == ev['district']) & (df_plot['crop_year'] == ev['year'])]
            val = sub['flood_days_5plus'].iloc[0] if len(sub) > 0 else 0
            consec = sub['max_consec_days'].iloc[0] if len(sub) > 0 else 0
            
            fig_spag.add_trace(go.Scatter(
                x=[ev['year']], y=[val],
                mode='markers',
                marker=dict(size=11, color='#1e3a8a', symbol='circle', line=dict(color='white', width=2)),
                name=ev['label'],
                showlegend=False,
                hovertemplate=f"<b>{ev['label']}</b><br>Country: <b>{ev['country']}</b><br>District: <b>{ev['district']}</b><br>Year: <b>{ev['year']}</b><br>Flood Days (>=5d): <b>{val:.0f}</b><br>Longest Streak: <b>{consec:.0f}d</b><extra></extra>"
            ))

        df_aff = df_plot[df_plot['flood_days_5plus'] >= 5]
        avg_aff = df_aff.groupby('crop_year')['flood_days_5plus'].mean().reset_index()
        avg_aff_full = pd.DataFrame({'crop_year': years}).merge(avg_aff, on='crop_year', how='left').fillna(0)

        fig_spag.add_trace(go.Scatter(
            x=avg_aff_full['crop_year'], y=avg_aff_full['flood_days_5plus'],
            mode='lines+markers', name='Avg of Affected', line=dict(color='#f97316', width=4),
            marker=dict(size=8, color='#f97316', line=dict(color='white', width=1.5)),
            hovertemplate="<b>Avg of Affected Districts</b><br>Year: <b>%{x}</b><br>Avg Days: <b>%{y:.1f}</b><extra></extra>"
        ))

        fig_spag.update_layout(
            title=dict(text=f"Historical Flood Day Trends per District & Marked Benchmark Events ({title_text})", font=dict(size=14, family='Inter, sans-serif')),
            xaxis=dict(tickmode='array', tickvals=years, tickangle=45, title='Crop Year', gridcolor='#f1f5f9'),
            yaxis=dict(title='Total Days in >=5-Day Consecutive Flood Streaks', gridcolor='#f1f5f9'),
            hovermode='closest', height=500, template='plotly_white', legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.85)'),
            margin=dict(l=70, r=20, t=60, b=80)
        )

        # --- PANEL C: Annual Violin Plot per Year (2008–2024) ---
        fig_violin = go.Figure()
        df_v = df_plot[(df_plot['crop_year'] >= 2008) & (df_plot['crop_year'] <= 2024)]
        v_years = sorted(df_v['crop_year'].unique())

        for yr in v_years:
            y_vals = df_v[df_v['crop_year'] == yr]['flood_days_5plus']
            fig_violin.add_trace(go.Violin(
                x=[yr] * len(y_vals),
                y=y_vals,
                name=str(yr),
                box_visible=False,
                meanline_visible=True,
                points=False,
                fillcolor='rgba(2, 132, 199, 0.35)',
                line=dict(color='#0284c7', width=1.5),
                showlegend=False,
                hovertemplate=f"<b>Year {yr}</b><br>District Flood Days (>=5d): <b>%{{y:.0f}}</b><extra></extra>"
            ))

        fig_violin.update_layout(
            title=dict(text=f"Annual Flood Days Distribution Across All Districts (Violin Plot per Year, 2008–2024)", font=dict(size=14, family='Inter, sans-serif')),
            xaxis=dict(title="Crop Year", tickmode='array', tickvals=v_years, tickangle=45, gridcolor='#f1f5f9'),
            yaxis=dict(title="Total Days in >=5-Day Continuous Streaks", gridcolor='#f1f5f9'),
            height=450, template='plotly_white', margin=dict(l=70, r=20, t=60, b=80)
        )

        html_map    = fig_map.to_html(full_html=False, include_plotlyjs='cdn', config={'scrollZoom': True, 'displayModeBar': True})
        html_spag   = fig_spag.to_html(full_html=False, include_plotlyjs=False, config={'scrollZoom': True, 'displayModeBar': True})
        html_violin = fig_violin.to_html(full_html=False, include_plotlyjs=False, config={'scrollZoom': True, 'displayModeBar': True})

        out_html_path = os.path.join(OUT_DIR, filename)
        with open(out_html_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_text} - SWI Flood Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: #f1f5f9; color: #0f172a; }}
    .header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
      color: white; padding: 24px 36px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    .header h1 {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 4px; }}
    .header p  {{ font-size: 0.85rem; opacity: 0.75; margin-top: 4px; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 16px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
      background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3);
      margin-top: 10px;
    }}
    .container {{ max-width: 1500px; margin: 0 auto; padding: 24px; }}
    .panel {{
      background: white; border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.07);
      padding: 20px 20px 10px; margin-bottom: 24px;
    }}
    .panel-title   {{ font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 3px; }}
    .panel-sub     {{ font-size: 0.78rem; color: #64748b; margin-bottom: 10px; line-height: 1.5; }}
    .def-box {{
      background: #f0f9ff; border-left: 4px solid #0284c7;
      padding: 10px 16px; border-radius: 4px;
      font-size: 0.78rem; color: #0369a1; margin-bottom: 12px; line-height: 1.6;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>30th July Meeting Output &mdash; {title_text}</h1>
    <p>Full Crop Calendar (Planting to Harvest) &nbsp;|&nbsp; {df_plot['ADM_NAME'].nunique()} Active Districts &nbsp;|&nbsp; 2007&ndash;2025</p>
    <div class="badge">Threshold Rule: {desc_text} (Must persist &ge; 5 Consecutive Days)</div>
  </div>

  <div class="container">
    <div class="panel">
      <p class="panel-title">Panel A &mdash; Animated Time-Series Map</p>
      <p class="panel-sub">
        Colour = total days in the crop year belonging to unbroken &gt;=5-day flood streaks under this strategy.
        Fixed scale (0&ndash;25 days) across all years for direct comparison.
      </p>
      <div class="def-box">
        <b>Strategy Definition:</b> Count all days that belong to a continuous streak of &ge; 5 consecutive days where {desc_text}.
      </div>
      {html_map}
    </div>

    <div class="panel">
      <p class="panel-title">Panel B &mdash; District Spaghetti Plot with Marked Case Study Events (2007&ndash;2025)</p>
      <p class="panel-sub">
        Light blue lines highlight all districts affected under this threshold. Marked points show specific historical disaster events in benchmark districts. The orange line shows the <b>Average of Affected Districts</b>.
      </p>
      {html_spag}
    </div>
  </div>
</body>
</html>""")
        print(f"  Saved full 2-panel dashboard: {filename}", flush=True)

if __name__ == "__main__":
    main()
