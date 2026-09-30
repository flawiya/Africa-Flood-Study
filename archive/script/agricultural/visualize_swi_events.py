import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
OUT_DIR = os.path.join(BASE, "output", "agricultural", "visualizations")
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Load Summary Data
full_summary_csv = os.path.join(BASE, "output", "agricultural", "SWI_Flood_Summary_AllDistricts.csv")
pv_summary_csv = os.path.join(BASE, "output", "agricultural", "SWI_PlantingVeg_Flood_Summary_AllDistricts.csv")

df_full = pd.read_csv(full_summary_csv)
df_pv = pd.read_csv(pv_summary_csv)

# ── Visualization 1: Events per Country (Full Season) ──────────────────────────
country_summary = df_full.groupby('COUNTRY').agg(
    total_waterlogging=('num_waterlogging_events', 'sum'),
    total_high_risk=('num_high_risk_events', 'sum'),
    total_severe=('num_severe_events', 'sum')
).reset_index()

country_melt = pd.melt(country_summary, id_vars=['COUNTRY'], 
                       value_vars=['total_waterlogging', 'total_high_risk', 'total_severe'],
                       var_name='Severity', value_name='Count')

country_melt['Severity'] = country_melt['Severity'].map({
    'total_waterlogging': 'Severe Waterlogging Risk (≥7 days)',
    'total_high_risk': 'High Yield-Loss Risk (≥10 days)',
    'total_severe': 'Severe Yield-Loss Risk (≥14 days)'
})

fig1 = px.bar(country_melt, x='COUNTRY', y='Count', color='Severity',
              title="Full Season: Flood Events by Severity and Country (2007-2025)",
              labels={'Count': 'Number of Flood Events', 'COUNTRY': 'Country'},
              color_discrete_map={
                  'Severe Waterlogging Risk (≥7 days)': '#F4D03F', 
                  'High Yield-Loss Risk (≥10 days)': '#E67E22', 
                  'Severe Yield-Loss Risk (≥14 days)': '#E74C3C'
              })
fig1.update_layout(xaxis_tickangle=-45, barmode='stack', template="plotly_white")

# ── Visualization 2: Planting→Vegetative Focus Breakdown by Country ──────────
pv_country = df_pv.groupby('COUNTRY').agg(
    moderate=('num_moderate_events', 'sum'),
    severe=('num_severe_events', 'sum')
).reset_index()

pv_melt = pd.melt(pv_country, id_vars=['COUNTRY'], 
                  value_vars=['moderate', 'severe'],
                  var_name='Risk', value_name='Count')

pv_melt['Risk'] = pv_melt['Risk'].map({
    'moderate': 'Moderate Damage (7-9 days)',
    'severe': 'Severe Damage (≥10 days)'
})

fig2 = px.bar(pv_melt, x='COUNTRY', y='Count', color='Risk',
              title="Planting→Vegetative Stage: Flood Risk Events by Country (2007-2025)",
              labels={'Count': 'Number of Events', 'COUNTRY': 'Country'},
              color_discrete_map={
                  'Moderate Damage (7-9 days)': '#5DADE2', 
                  'Severe Damage (≥10 days)': '#1A5276'
              })
fig2.update_layout(xaxis_tickangle=-45, barmode='group', template="plotly_white")


# ── Combine into an HTML Dashboard ───────────────────────────────────────────
html_path = os.path.join(OUT_DIR, "SWI_Flood_Events_Dashboard.html")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write("<html><head><title>SWI Flood Events</title></head><body>")
    f.write("<h1 style='font-family: sans-serif; text-align: center;'>Africa SWI Agricultural Flood Index (2007-2025)</h1>")
    f.write(fig1.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write("<hr>")
    f.write(fig2.to_html(full_html=False, include_plotlyjs=False))
    f.write("</body></html>")

print(f"Visuals generated and saved to: {html_path}")
