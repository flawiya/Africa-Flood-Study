import os
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import json

BASE_DIR = r'C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study'
DATA_CSV = os.path.join(BASE_DIR, r'output\agricultural\Africa_SWI_Maize_AreaWeighted_2007_2025.csv')
SHP_PATH = os.path.join(BASE_DIR, r'data\africa_agricultural_domain_2019.shp')
OUT_DIR  = os.path.join(BASE_DIR, r'output\agricultural\meeting_24th_july_output')
os.makedirs(OUT_DIR, exist_ok=True)

OUT_PATH = os.path.join(OUT_DIR, 'Average_Flood_Days_Map.html')

def compute_streak_summary(df_in, flag_col):
    df_calc = df_in.copy()
    df_calc['block'] = (df_calc[flag_col] != df_calc.groupby(['COUNTRY', 'ADM_NAME'])[flag_col].shift()).cumsum()
    df_calc['is_true'] = df_calc[flag_col]
    block_len = df_calc.groupby(['COUNTRY', 'ADM_NAME', 'block'])['is_true'].transform('sum')
    df_calc['valid_streak_day'] = df_calc['is_true'] & (block_len >= 7)
    summary = df_calc.groupby(['ISO3', 'COUNTRY', 'ADM_NAME', 'crop_year']).agg(
        flood_days_7plus=('valid_streak_day', 'sum')
    ).reset_index()
    return summary

def main():
    print('Loading master dataset...', flush=True)
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

    print('Calculating streaks...', flush=True)
    sum_opt1 = compute_streak_summary(df, 'flag_opt1')
    sum_opt2 = compute_streak_summary(df, 'flag_opt2')
    sum_opt3 = compute_streak_summary(df, 'flag_opt3')

    num_years = 17.0
    
    avg_opt1 = sum_opt1.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()
    avg_opt2 = sum_opt2.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()
    avg_opt3 = sum_opt3.groupby(['ISO3', 'COUNTRY', 'ADM_NAME'])['flood_days_7plus'].sum().reset_index()

    avg_opt1['flood_days_7plus'] = avg_opt1['flood_days_7plus'] / num_years
    avg_opt2['flood_days_7plus'] = avg_opt2['flood_days_7plus'] / num_years
    avg_opt3['flood_days_7plus'] = avg_opt3['flood_days_7plus'] / num_years

    avg_opt1.rename(columns={'flood_days_7plus': 'avg_days_opt1'}, inplace=True)
    avg_opt2.rename(columns={'flood_days_7plus': 'avg_days_opt2'}, inplace=True)
    avg_opt3.rename(columns={'flood_days_7plus': 'avg_days_opt3'}, inplace=True)

    df_map = avg_opt1.merge(avg_opt2[['ADM_NAME', 'avg_days_opt2']], on='ADM_NAME')
    df_map = df_map.merge(avg_opt3[['ADM_NAME', 'avg_days_opt3']], on='ADM_NAME')

    print('Loading shapefile...', flush=True)
    gdf = gpd.read_file(SHP_PATH)[['ADM_NAME', 'COUNTRY', 'geometry']]
    gdf = gdf[gdf['COUNTRY'] != 'Morocco']
    gdf['geometry'] = gdf['geometry'].simplify(0.05, preserve_topology=True)
    gdf_filtered = gdf[gdf['ADM_NAME'].isin(df_map['ADM_NAME'])].copy()
    geojson_dict = json.loads(gdf_filtered.set_index('ADM_NAME').to_json())

    print('Generating Map with Smooth Scroll Zoom enabled...', flush=True)

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
            customdata=np.stack([df_map['COUNTRY'], df_map[z_col].round(2)], axis=-1),
            hovertemplate=(
                '<b>%{location}</b> (%{customdata[0]})<br>'
                'Average Annual Flood Days: <b>%{customdata[1]} days/yr</b><extra></extra>'
            ),
            colorbar=dict(title=dict(text='Avg Days/Yr'), len=0.7, x=1.0),
            name=title
        )

    fig = go.Figure()
    
    trace_opt1 = create_choropleth('avg_days_opt1', 'Option 1 (99th Percentile)', zmax=1.5)
    trace_opt2 = create_choropleth('avg_days_opt2', 'Option 2 (95th %ile + 85% Abs)', zmax=4.0)
    trace_opt3 = create_choropleth('avg_days_opt3', 'Option 3 (Pure 85% Abs)', zmax=15.0)

    trace_opt1.visible = True
    trace_opt2.visible = False
    trace_opt3.visible = False

    fig.add_trace(trace_opt1)
    fig.add_trace(trace_opt2)
    fig.add_trace(trace_opt3)

    fig.update_layout(
        map=dict(style='carto-positron', center=dict(lat=2.0, lon=18.0), zoom=2.3),
        title_text='Average Flood Days per Year Across African Agricultural Districts (2008-2024)',
        title_x=0.5,
        margin=dict(l=10, r=10, t=60, b=10),
        height=850,
        updatemenus=[dict(
            type='dropdown',
            direction='down',
            active=0,
            x=0.01,
            y=0.99,
            buttons=list([
                dict(label='Option 1: 99th Percentile (>=7 Consec Days)', method='update', args=[{'visible': [True, False, False]}]),
                dict(label='Option 2: 95th %ile + SWI>=85% (>=7 Consec Days)', method='update', args=[{'visible': [False, True, False]}]),
                dict(label='Option 3: Pure Absolute SWI>=85% (>=7 Consec Days)', method='update', args=[{'visible': [False, False, True]}]),
            ]),
        )]
    )

    # Enable full zoom config (scrollZoom=True, displayModeBar=True, etc.)
    fig.write_html(
        OUT_PATH,
        full_html=True,
        include_plotlyjs='cdn',
        config={
            'scrollZoom': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['hoverClosestCartesian', 'hoverCompareCartesian'],
            'responsive': True
        }
    )
    print(f'Done! Zoom-enabled Map saved to {OUT_PATH}', flush=True)

if __name__ == '__main__':
    main()
