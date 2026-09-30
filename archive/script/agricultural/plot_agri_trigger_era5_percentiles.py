import os
import sys
import traceback

# Define the error log file path
log_file_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\plot_era5_percentiles_theory_error.txt"

try:
    print("Trace: Initializing imports...", flush=True)
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    print("Trace: Imports complete.", flush=True)

    # Configure UTF-8 encoding for standard outputs
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    print("Trace: Encoding configured.", flush=True)

    # =============================================================================
    # CONFIGURATION & PATHS
    # =============================================================================
    base_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
    output_folder = os.path.join(base_path, "output", "agricultural")
    ssi_csv = os.path.join(output_folder, "Zambia_Agricultural_Districts_Final_Study_SSI_Gringorten_Full_Season.csv")
    chirps_csv = os.path.join(output_folder, "CHIRPS_Standardized_Master.csv")
    era5_runoff_csv = os.path.join(output_folder, "Zambia_ERA5_Daily_Runoff_2000_2025.csv")
    viz_folder = os.path.join(output_folder, "visualizations")
    os.makedirs(viz_folder, exist_ok=True)

    # List of targets to plot (District: Year)
    requested_targets = {
        'KAPIRI MPOSHI': 2007,
        'CHIBOMBO': 2011,
        'MONZE': 2007
    }

    def normalize_name(name):
        return str(name).replace('-', ' ').replace('_', ' ').strip().upper()

    print("Trace: Configuration set.", flush=True)

    # ──────────────────────────────────────────────────────────
    # LOAD & MERGE DATASETS
    # ──────────────────────────────────────────────────────────
    print("Trace: Loading Gringorten SSI dataset...", flush=True)
    if not os.path.exists(ssi_csv):
        raise FileNotFoundError(f"SSI dataset not found at: {ssi_csv}")

    df_ssi = pd.read_csv(ssi_csv)
    df_ssi['Date'] = pd.to_datetime(df_ssi['Date'])
    df_ssi['District_Upper'] = df_ssi['District_Name'].apply(normalize_name)

    print("Trace: Loading CHIRPS master rainfall dataset...", flush=True)
    if not os.path.exists(chirps_csv):
        raise FileNotFoundError(f"CHIRPS master rainfall not found at: {chirps_csv}")

    df_chirps = pd.read_csv(chirps_csv, low_memory=False)
    df_chirps['date'] = pd.to_datetime(df_chirps['date'])
    df_chirps['District_Upper'] = df_chirps['District_Name'].apply(normalize_name)

    print("Trace: Loading GEE ERA5-Land daily runoff...", flush=True)
    if not os.path.exists(era5_runoff_csv):
        raise FileNotFoundError(f"GEE ERA5-Land runoff dataset not found at: {era5_runoff_csv}")
    df_era5 = pd.read_csv(era5_runoff_csv)
    df_era5['Date'] = pd.to_datetime(df_era5['Date'])
    df_era5['District_Upper'] = df_era5['District_Name'].apply(normalize_name)
    df_era5 = df_era5.sort_values(['District_Upper', 'Date'])

    print("Trace: Calculating 7-day rolling sum of GEE downloaded total_runoff_mm...", flush=True)
    df_era5['Runoff_Q_mm'] = df_era5.groupby('District_Upper')['total_runoff_mm'].transform(
        lambda x: x.rolling(7, min_periods=1).sum()
    )

    # Calculate percentiles (Nov-Apr growing season only)
    print("Trace: Calculating district-level 75th and 85th percentiles...", flush=True)
    df_era5['Month'] = df_era5['Date'].dt.month
    df_era5['doy'] = df_era5['Date'].apply(
        lambda d: d.dayofyear if not d.is_leap_year or d.dayofyear < 60 else d.dayofyear - 1
    )
    growing_season_months = [11, 12, 1, 2, 3, 4]
    df_gs = df_era5[df_era5['Month'].isin(growing_season_months)]

    district_thresholds = {}
    for dist, group in df_gs.groupby('District_Upper'):
        q_vals = group['Runoff_Q_mm'].dropna()
        if len(q_vals) > 0:
            q_low = max(np.percentile(q_vals, 75.0), 1.0)
            q_high = max(np.percentile(q_vals, 85.0), 2.0)
        else:
            q_low = 5.0
            q_high = 10.0
        district_thresholds[dist] = (q_low, q_high)

    df_chirps = df_chirps.sort_values(['District_Upper', 'date'])
    df_chirps['P_7d'] = df_chirps.groupby('District_Upper')['precipitation'].transform(
        lambda x: x.rolling(7, min_periods=7).sum()
    )
    df_chirps['doy'] = df_chirps['date'].apply(
        lambda d: d.dayofyear if not d.is_leap_year or d.dayofyear < 60 else d.dayofyear - 1
    )

    # Merge datasets
    print("Trace: Merging SSI, rainfall, and GEE runoff data...", flush=True)
    df_merged = df_ssi.merge(
        df_chirps[['District_Upper', 'date', 'precipitation', 'P_7d']],
        left_on=['District_Upper', 'Date'],
        right_on=['District_Upper', 'date'],
        how='inner'
    ).drop(columns=['date'])

    df_merged = df_merged.merge(
        df_era5[['District_Upper', 'Date', 'Runoff_Q_mm']],
        on=['District_Upper', 'Date'],
        how='inner'
    )
    print("Trace: Datasets merged.", flush=True)

    # Calculate climatology of daily variables on merged dataset
    print("Trace: Computing daily climatological means for GEE Runoff, SSI, and precipitation...", flush=True)
    merged_climatology = df_merged.groupby(['District_Upper', 'doy']).agg(
        mean_Runoff_Q_mm=('Runoff_Q_mm', 'mean'),
        mean_SSI=('SSI', 'mean'),
        mean_precipitation=('P_7d', 'mean'),
        std_precipitation=('P_7d', 'std')
    ).reset_index()

    df_plot = df_merged.merge(merged_climatology, on=['District_Upper', 'doy'], how='left')
    df_plot['precip_threshold'] = df_plot['mean_precipitation'] + 2 * df_plot['std_precipitation']
    df_plot['precip_above_threshold'] = df_plot['P_7d'] > df_plot['precip_threshold']
    print("Trace: Climatological means and standard deviations computed.", flush=True)

    # ──────────────────────────────────────────────────────────
    # DEFINE DYNAMIC TRIGGER OUTCOMES (75th / 85th Percentiles)
    # ──────────────────────────────────────────────────────────
    print("Trace: Computing dynamic triggers per district...", flush=True)
    df_plot['Trigger_Severe'] = False
    df_plot['Trigger_Moderate'] = False

    for dist, (q_low, q_high) in district_thresholds.items():
        mask = (df_plot['District_Upper'] == dist)
        df_plot.loc[mask, 'Trigger_Severe'] = (df_plot.loc[mask, 'SSI'] >= 1.5) & (df_plot.loc[mask, 'Runoff_Q_mm'] >= q_high)
        df_plot.loc[mask, 'Trigger_Moderate'] = (df_plot.loc[mask, 'SSI'] >= 1.0) & (df_plot.loc[mask, 'Runoff_Q_mm'] >= q_low) & (~df_plot.loc[mask, 'Trigger_Severe'])

    # Filter targets
    available_districts = df_plot['District_Upper'].unique()
    targets_to_plot = []
    for dist_name, yr in requested_targets.items():
        norm_dist = normalize_name(dist_name)
        if norm_dist in available_districts:
            targets_to_plot.append((norm_dist, yr))

    # Sort targets
    targets_to_plot.sort(key=lambda x: x[0])
    print("Trace: Triggers computed. Targets filtered.", flush=True)

    # ──────────────────────────────────────────────────────────
    # INTERACTIVE PLOT: 4 PANELS PER DISTRICT (Plotly HTML)
    # ──────────────────────────────────────────────────────────
    n_plots = len(targets_to_plot)
    if n_plots > 0:
        print("Trace: Creating interactive comparison subplots (Plotly HTML)...", flush=True)
        
        subplot_titles = []
        for dist, yr in targets_to_plot:
            dist_title = dist.title()
            yr_label = f"{yr}-{yr+1}"
            subplot_titles.extend([
                f"{dist_title} - 7-Day Cumulative Precipitation ({yr_label})",
                f"{dist_title} - SSI (Daily) ({yr_label})",
                f"{dist_title} - ERA5 Runoff (7-Day Cumulative) ({yr_label})",
                f"{dist_title} - Agricultural Trigger (Moderate & Severe Outcomes) ({yr_label})"
            ])

        fig_plotly = make_subplots(
            rows=n_plots * 4, cols=1,
            shared_xaxes=False,
            vertical_spacing=0.025,
            subplot_titles=subplot_titles
        )
        
        for idx, (dist, yr) in enumerate(targets_to_plot, 1):
            d_df = df_plot[(df_plot['District_Upper'] == dist) & (df_plot['Crop_Year'] == yr)].sort_values('Date')
            
            row_rain = (idx - 1) * 4 + 1
            row_ssi  = (idx - 1) * 4 + 2
            row_q    = (idx - 1) * 4 + 3
            row_trig = (idx - 1) * 4 + 4
            
            # Fetch district thresholds
            q_low, q_high = district_thresholds.get(dist, (1.0, 2.0))
            
            # Convert Date to string lists to prevent any datetime serialization anomalies
            date_str_list = d_df['Date'].dt.strftime('%Y-%m-%d').tolist()

            # ── PANEL 1: 7-Day Cumulative Precipitation ──
            bar_colors = ['#ef4444' if above else '#2563eb' for above in d_df['precip_above_threshold'].fillna(False)]
            fig_plotly.add_trace(
                go.Bar(x=date_str_list, y=d_df['P_7d'].tolist(), marker_color=bar_colors, name=f"7-Day Precip ({yr})", hovertemplate='%{x|%Y-%m-%d}<br>7-Day Cumulative Precip: %{y:.1f} mm<extra></extra>'),
                row=row_rain, col=1
            )
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['precip_threshold'].tolist(), mode='lines', name="Mean + 2 Std Dev (7-Day)", line=dict(color='#ef4444', width=1.5, dash='dash'), hovertemplate='Threshold (Mean+2σ): %{y:.1f} mm<extra></extra>'),
                row=row_rain, col=1
            )
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['mean_precipitation'].tolist(), mode='lines', name="25-Year Mean (7-Day)", line=dict(color='#64748b', width=1.2, dash='dot'), hovertemplate='Mean: %{y:.1f} mm<extra></extra>'),
                row=row_rain, col=1
            )
            fig_plotly.update_yaxes(title_text="Rainfall (mm)", range=[0, max(150.0, d_df['P_7d'].max() * 1.2)], row=row_rain, col=1)

            # ── PANEL 2: SSI ──
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['SSI'].tolist(), mode='lines', name=f"SSI ({yr})", line=dict(color='#10b981', width=2)),
                row=row_ssi, col=1
            )
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['mean_SSI'].tolist(), mode='lines', name="25-Year Mean SSI", line=dict(color='#64748b', width=1, dash='dot')),
                row=row_ssi, col=1
            )
            # Threshold lines
            fig_plotly.add_trace(go.Scatter(x=date_str_list, y=[1.5]*len(d_df), mode='lines', name="Severe Threshold (1.5)", line=dict(color='#dc2626', width=1.2, dash='dash'), showlegend=False), row=row_ssi, col=1)
            fig_plotly.add_trace(go.Scatter(x=date_str_list, y=[1.0]*len(d_df), mode='lines', name="Moderate Threshold (1.0)", line=dict(color='#ea580c', width=1.2, dash='dash'), showlegend=False), row=row_ssi, col=1)
            fig_plotly.update_yaxes(title_text="SSI Anomaly", range=[-3.0, 3.0], row=row_ssi, col=1)

            # ── PANEL 3: ERA5 Runoff ──
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['Runoff_Q_mm'].tolist(), mode='lines', name=f"ERA5 Runoff ({yr})", line=dict(color='#f59e0b', width=2)),
                row=row_q, col=1
            )
            fig_plotly.add_trace(
                go.Scatter(x=date_str_list, y=d_df['mean_Runoff_Q_mm'].tolist(), mode='lines', name="25-Year Mean Runoff", line=dict(color='#64748b', width=1, dash='dot')),
                row=row_q, col=1
            )
            # Threshold lines (Dynamic percentiles for this district)
            fig_plotly.add_trace(go.Scatter(x=date_str_list, y=[q_high]*len(d_df), mode='lines', name=f"Severe Q ({q_high:.1f}mm)", line=dict(color='#dc2626', width=1.2, dash='dash'), showlegend=False), row=row_q, col=1)
            fig_plotly.add_trace(go.Scatter(x=date_str_list, y=[q_low]*len(d_df), mode='lines', name=f"Moderate Q ({q_low:.1f}mm)", line=dict(color='#ea580c', width=1.2, dash='dash'), showlegend=False), row=row_q, col=1)
            fig_plotly.update_yaxes(title_text="Runoff (mm)", range=[0, max(10.0, d_df['Runoff_Q_mm'].max() * 1.2)], row=row_q, col=1)

            # ── PANEL 4: Trigger Bars ──
            # Map trigger status to discrete numeric values for clean height plotting (2 for severe, 1 for moderate)
            status_vals = np.zeros(len(d_df))
            status_vals[d_df['Trigger_Moderate']] = 1
            status_vals[d_df['Trigger_Severe']] = 2
            
            # Map bar colors
            trig_colors = ['#f1f5f9' if v==0 else ('#ffedd5' if v==1 else '#fee2e2') for v in status_vals]
            fig_plotly.add_trace(
                go.Bar(x=date_str_list, y=status_vals.tolist(), marker_color=trig_colors, name=f"Triggers ({yr})", hovertemplate='%{x|%Y-%m-%d}<br>Status: %{text}<extra></extra>', text=['No Trigger' if v==0 else ('Moderate Trigger' if v==1 else 'Severe Trigger') for v in status_vals]),
                row=row_trig, col=1
            )
            fig_plotly.update_yaxes(
                title_text="Trigger Level",
                tickvals=[0, 1, 2],
                ticktext=["No Trigger", "Moderate", "Severe"],
                range=[0, 2.5],
                row=row_trig, col=1
            )
            fig_plotly.update_xaxes(title_text="Date", row=row_trig, col=1)

        # Update global layout
        fig_plotly.update_layout(
            height=n_plots * 1100,
            width=1400,
            title_text="Zambia Agricultural Saturation Flood Risk Model (Optimized ERA5 Percentiles)",
            showlegend=False,
            template="plotly_white"
        )
        
        # Write to interactive HTML template
        plotly_div = fig_plotly.to_html(full_html=False, include_plotlyjs='cdn')
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Zambia Agricultural Saturation Flood Risk Model (Optimized ERA5 Percentiles)</title>
    <style>
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: #0f172a;
            background-color: #ffffff;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1450px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 24px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 16px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 700;
            margin: 0;
            color: #0f172a;
        }}
        .subtitle {{
            font-size: 14px;
            color: #64748b;
            margin-top: 4px;
            margin-bottom: 0;
        }}
        .methodology-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 32px;
        }}
        .card {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
        }}
        .card h3 {{
            margin-top: 0;
            font-size: 15px;
            font-weight: 600;
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .card p {{
            font-size: 13px;
            line-height: 1.6;
            color: #334155;
            margin: 0 0 8px 0;
        }}
        .formula {{
            font-family: monospace;
            background-color: #f1f5f9;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            display: inline-block;
            margin: 4px 0;
        }}
        .highlight-moderate {{
            color: #ea580c;
            font-weight: 700;
            background-color: #fffaf0;
            border: 1px solid #ffedd5;
        }}
        .highlight-severe {{
            color: #dc2626;
            font-weight: 700;
            background-color: #fef2f2;
            border: 1px solid #fee2e2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Zambia Agricultural Saturation Flood Risk Model (Optimized ERA5 Percentiles)</h1>
            <p class="subtitle">Parametric Insurance Event Analysis (Regime B - Rural) with District-Specific 75th & 85th Percentile Runoff Thresholds</p>
        </header>
        
        <div class="methodology-grid">
            <div class="card">
                <h3>1. Soil Moisture Index (SSI)</h3>
                <p>Calculated using the non-parametric <b>Gringorten plotting position</b> method applied to daily root-zone soil moisture (0-100cm) across the 25-year record.</p>
                <p>Identifies the "full sponge" condition where soil is waterlogged and plant roots are in the suffocation zone.</p>
                <span class="formula">Moderate Threshold: SSI &ge; 1.0</span><br>
                <span class="formula">Severe Threshold: SSI &ge; 1.5</span>
            </div>
            <div class="card">
                <h3>2. Optimized ERA5 Runoff (Q)</h3>
                <p>Acquired from <b>ERA5-Land daily total runoff</b> aggregated over a <b>7-day rolling cumulative window</b>. Thresholds are optimized dynamically to represent localized anomalies:</p>
                <span class="formula">Moderate: 75th Percentile (Min 1.0mm)</span><br>
                <span class="formula">Severe: 85th Percentile (Min 2.0mm)</span>
            </div>
            <div class="card">
                <h3>3. Dual-Regime Saturation Triggers</h3>
                <p>A flood payout event is defined by the daily intersection of soil saturation (SSI) and active runoff (Q), with thresholds tailored per district:</p>
                <span class="formula highlight-moderate">Moderate: (SSI &ge; 1.0) AND (Q &ge; 75th Percentile)</span><br>
                <span class="formula highlight-severe">Severe: (SSI &ge; 1.5) AND (Q &ge; 85th Percentile)</span>
            </div>
        </div>
        
        {plotly_div}
    </div>
</body>
</html>
"""
        
        interactive_plot_path = os.path.join(viz_folder, "ERA5_Optimized_Daily_Agri_Trigger_Baseline_Comparison.html")
        with open(interactive_plot_path, "w", encoding="utf-8") as f_html:
            f_html.write(html_content)
        print(f"Trace: Interactive comparison plot saved to {interactive_plot_path}", flush=True)

    print("Trace: Plot generation complete. Script finished successfully.", flush=True)

except Exception as e:
    with open(log_file_path, "w") as f_err:
        f_err.write(f"Exception Type: {type(e).__name__}\n")
        f_err.write(f"Exception Message: {str(e)}\n\n")
        traceback.print_exc(file=f_err)
    print(f"CRITICAL RUNTIME ERROR: {str(e)}", file=sys.stderr, flush=True)
    sys.exit(1)
