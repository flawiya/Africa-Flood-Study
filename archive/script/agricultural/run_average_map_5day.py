"""
run_average_map_5day.py
=======================
Computes district-level average flood days per year under the 5-consecutive-day threshold
for Option 1 (P99), Option 2 (P95 + SWI>=85%), and Option 3 (Pure SWI>=85%).

Excludes 2007 and 2025 (17 crop years: 2008 to 2024).
Generates an interactive Choropleth Map:
`output/agricultural/meeting_30th_july_output/Average_Flood_Days_Map_5Day.html`
"""

import os, json, numpy as np, pandas as pd, geopandas as gpd
import plotly.graph_objects as go

BASE_DIR = r'C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study'
DATA_CSV = os.path.join(BASE_DIR, r'output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv')
SHP_PATH = os.path.join(BASE_DIR, r'data\africa_agricultural_domain_2019.shp')
OUT_DIR  = os.path.join(BASE_DIR, r'output\agricultural\meeting_30th_july_output')
os.makedirs(OUT_DIR, exist_ok=True)

OUT_PATH = os.path.join(OUT_DIR, 'Average_Flood_Days_Map_5Day.html')

def compute_streak_summary(df_in, flag_col, min_streak=5):
    df_calc = df_in.copy()
    df_calc['block'] = (df_calc[flag_col] != df_calc.groupby(['COUNTRY', 'ADM_NAME'])[flag_col].shift()).cumsum()
    df_calc['is_true'] = df_calc[flag_col]
    block_len = df_calc.groupby(['COUNTRY', 'ADM_NAME', 'block'])['is_true'].transform('sum')
    df_calc['valid_streak_day'] = df_calc['is_true'] & (block_len >= min_streak)
    summary = df_calc.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year']).agg(
        flood_days=('valid_streak_day', 'sum')
    ).reset_index()
    return summary

def main():
    print('Loading master dataset for 5-day average map...', flush=True)
    df = pd.read_csv(DATA_CSV)
    df['date'] = pd.to_datetime(df['date'])
    df['doy'] = df['date'].dt.dayofyear
    df['crop_year'] = df['date'].dt.year

    plant_doy = pd.to_numeric(df['planting'], errors='coerce')
    harvest_doy = pd.to_numeric(df['harvest'], errors='coerce')
    cross_year_mask = plant_doy > harvest_doy
    shift_mask = cross_year_mask & (df['doy'] >= (plant_doy - 15))
    df.loc[shift_mask, 'crop_year'] += 1

    df = df.sort_values(['COUNTRY', 'ADM_NAME', 'date'])
    df = df[df['COUNTRY'] != 'Morocco']

    print('Excluding 2007 and 2025...', flush=True)
    df = df[~df['crop_year'].isin([2007, 2025])]

    print('Computing thresholds...', flush=True)
    p95 = df.groupby(['COUNTRY', 'ADM_NAME'])['swi_t10_mean'].transform(lambda x: x.quantile(0.95))
    p99 = df.groupby(['COUNTRY', 'ADM_NAME'])['swi_t10_mean'].transform(lambda x: x.quantile(0.99))
    df['p95'] = p95
    df['p99'] = p99

    df['flag_opt1'] = df['swi_t10_mean'] >= df['p99']
    df['flag_opt2'] = (df['swi_t10_mean'] >= df['p95']) & (df['swi_t10_mean'] >= 85.0)
    df['flag_opt3'] = df['swi_t10_mean'] >= 85.0

    print('Calculating 5-day streaks...', flush=True)
    sum_opt1 = compute_streak_summary(df, 'flag_opt1', min_streak=5)
    sum_opt2 = compute_streak_summary(df, 'flag_opt2', min_streak=5)
    sum_opt3 = compute_streak_summary(df, 'flag_opt3', min_streak=5)

    num_years = 17.0
    
    avg_opt1 = sum_opt1.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days'].sum().reset_index()
    avg_opt2 = sum_opt2.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days'].sum().reset_index()
    avg_opt3 = sum_opt3.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days'].sum().reset_index()

    avg_opt1['avg_days_opt1'] = (avg_opt1['flood_days'] / num_years).round(2)
    avg_opt2['avg_days_opt2'] = (avg_opt2['flood_days'] / num_years).round(2)
    avg_opt3['avg_days_opt3'] = (avg_opt3['flood_days'] / num_years).round(2)

    df_map = avg_opt1[['ISO3', 'COUNTRY', 'ADM_NAME', 'avg_days_opt1']].merge(
        avg_opt2[['ADM_NAME', 'avg_days_opt2']], on='ADM_NAME'
    ).merge(
        avg_opt3[['ADM_NAME', 'avg_days_opt3']], on='ADM_NAME'
    )

    print('Loading shapefile...', flush=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
    gdf = gdf[gdf['COUNTRY'] != 'Morocco']
    gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)
    gdf_filtered = gdf[gdf['ADM_NAME'].isin(df_map['ADM_NAME'])].copy()
    geojson_dict = json.loads(gdf_filtered.set_index('ADM_NAME').to_json())

    fig = go.Figure()

    def create_choropleth(z_col, title, zmax):
        return go.Choroplethmap(
            geojson=geojson_dict,
            locations=df_map['ADM_NAME'],
            z=df_map[z_col],
            colorscale='Blues',
            zmin=0,
            zmax=zmax,
            marker_line_width=0.4,
            marker_line_color='rgba(0,0,0,0.3)',
            marker_opacity=0.8,
            customdata=np.stack([df_map['COUNTRY'], df_map[z_col]], axis=-1),
            hovertemplate=(
                '<b>%{location}</b> (%{customdata[0]})<br>'
                'Average Flood Days/Year (>=5d): <b>%{customdata[1]:.2f}</b><br>'
                '<extra></extra>'
            ),
            name=title
        )

    fig.add_trace(create_choropleth('avg_days_opt2', 'Option 2: P95 + SWI>=85% (Winner)', zmax=15))
    fig.add_trace(create_choropleth('avg_days_opt1', 'Option 1: P99 Percentile', zmax=15))
    fig.add_trace(create_choropleth('avg_days_opt3', 'Option 3: Pure SWI>=85%', zmax=25))

    # Make Option 2 visible by default
    fig.data[0].visible = True
    fig.data[1].visible = False
    fig.data[2].visible = False

    fig.update_layout(
        map=dict(
            style='carto-positron',
            center=dict(lat=2.0, lon=18.0),
            zoom=2.3
        ),
        title=dict(
            text='<b>Average Annual Flood Days per District (2008–2024 Baseline) — 5-Day Continuous Rule</b><br><sup>Option 2 (P95 + SWI>=85%) vs Option 1 (P99) vs Option 3 (Pure ABS 85%)</sup>',
            font=dict(size=16)
        ),
        updatemenus=[
            dict(
                type='buttons',
                direction='down',
                active=0,
                x=0.01,
                y=0.98,
                xanchor='left',
                yanchor='top',
                buttons=[
                    dict(
                        label='Option 2 (P95 + SWI>=85% - Recommended)',
                        method='update',
                        args=[{'visible': [True, False, False]}, {'title.text': '<b>Option 2: P95 Percentile + Absolute SWI >= 85% (>=5-Day Streaks)</b>'}]
                    ),
                    dict(
                        label='Option 1 (P99 Percentile)',
                        method='update',
                        args=[{'visible': [False, True, False]}, {'title.text': '<b>Option 1: Relative P99 Percentile (>=5-Day Streaks)</b>'}]
                    ),
                    dict(
                        label='Option 3 (Pure Absolute SWI >= 85%)',
                        method='update',
                        args=[{'visible': [False, False, True]}, {'title.text': '<b>Option 3: Pure Absolute SWI >= 85% (>=5-Day Streaks)</b>'}]
                    )
                ],
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#cbd5e1',
                borderwidth=1
            )
        ],
        height=750,
        margin=dict(l=0, r=0, t=60, b=0)
    )

    fig.write_html(OUT_PATH)
    print(f'Successfully generated 5-day average flood map: {OUT_PATH}', flush=True)

if __name__ == '__main__':
    main()
