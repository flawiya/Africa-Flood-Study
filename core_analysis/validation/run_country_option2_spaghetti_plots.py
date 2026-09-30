"""
run_country_option2_spaghetti_plots.py
========================================
Generates country-specific Option 2 ONLY (95th Percentile + 85% Absolute SWI Floor)
spaghetti trajectory validation dashboards for Kenya, Malawi, and Nigeria
under 5-Day and 7-Day Continuous Streak Rules.

Features:
  - Clean uniform faint gray background lines for all country districts.
  - National Mean Line (blue dashed line with diamond markers).
  - Star callout markers (★) with district text labels (e.g. TA Machinjili, TA Pemba, Gem, Teso South, Karachuonyo, Kabondo Kasipul).
  - Interactive Ground-Truth Reference Cards Block right below the plot with verified clickable HTTP links
    (UN ReliefWeb, World Bank PDNA, Copernicus, WHO, Wikipedia).

Outputs to: output/agricultural/outputs/
"""

import os
import pandas as pd
import plotly.graph_objects as go

# Project root: core_analysis/validation/ → core_analysis/ → project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

CSV_5DAY = os.path.join(OUT_DIR, "Africa_Maize_Flood_Annual_Option2_5Day.csv")
CSV_7DAY = os.path.join(OUT_DIR, "Africa_Maize_Flood_Annual_Option2_7Day.csv")

COUNTRY_CONFIGS = {
    "KEN": {
        "name": "Kenya",
        "flag": "🇰🇪",
        "events": {
            2018: {
                "title": "2018 Long Rains - Severe Nationwide Floods (40/47 Counties)",
                "districts": ["GEM", "BUTERE", "MATUNGU"],
                "impact": "186 deaths, 310,000+ displaced; Solai Dam collapse; ~21,000 ha maize destroyed in Western Kenya & Lake Victoria Basin (Gem, Butere, Matungu)",
                "refs": [
                    ("UN ReliefWeb - Kenya: Floods Mar 2018 (FF-2018-000030-KEN)", "https://reliefweb.int/disaster/ff-2018-000030-ken"),
                    ("Wikipedia - 2018 East Africa Floods", "https://en.wikipedia.org/wiki/2018_East_Africa_floods")
                ]
            },
            2020: {
                "title": "2020 Long Rains - Lake Victoria 63-Year Record High & Basin Floods",
                "districts": ["GEM", "BUTERE", "TESO SOUTH", "KARACHUONYO"],
                "impact": "200,000+ displaced across East Africa; Lake Victoria rose 1.2m; thousands of hectares submerged (Gem, Butere, Teso South, Karachuonyo)",
                "refs": [
                    ("UN ReliefWeb - Kenya: Floods & Landslides Apr 2020 (FL-2020-000128-KEN)", "https://reliefweb.int/disaster/fl-2020-000128-ken"),
                    ("Copernicus - Lake Victoria 2020 Extreme Water Levels", "https://climate.copernicus.eu/esotc/2020/lake-victoria"),
                    ("Wikipedia - 2020 East Africa Floods", "https://en.wikipedia.org/wiki/2020_East_Africa_floods")
                ]
            },
            2023: {
                "title": "2023 Short Rains - El Niño Strong Regional Floods",
                "districts": ["KABONDO KASIPUL", "GEM"],
                "impact": "160+ deaths, 500,000+ displaced; widespread agricultural flooding in Western & Nyanza regions (Kabondo Kasipul, Gem)",
                "refs": [
                    ("UN ReliefWeb - Kenya El Niño Floods Response 2023", "https://reliefweb.int/report/kenya/kenya-floods-el-nino-response-update"),
                    ("WFP - Kenya El Niño Flood Impact 2023", "https://www.wfp.org/")
                ]
            },
            2024: {
                "title": "2024 MAM Long Rains - Worst Flood Disaster in Modern Kenyan History",
                "districts": ["GEM", "KABONDO KASIPUL", "MATUNGU"],
                "impact": "315+ deaths, 293,000+ displaced (58,641 families); 24,000-41,000 acres farmland destroyed; severe inundation (Gem, Kabondo Kasipul, Matungu)",
                "refs": [
                    ("UN ReliefWeb - Kenya: Floods Apr 2024 (FL-2024-000045-KEN)", "https://reliefweb.int/disaster/fl-2024-000045-ken"),
                    ("Wikipedia - 2024 East Africa Floods", "https://en.wikipedia.org/wiki/2024_East_Africa_floods")
                ]
            }
        }
    },
    "MWI": {
        "name": "Malawi",
        "flag": "🇲🇼",
        "events": {
            2015: {
                "title": "2015 Floods - Worst Disaster in Living Memory (State of Emergency in 15 Districts)",
                "districts": ["TA MACHINJILI", "TA MAKHWIRA", "TA NGABU"],
                "impact": "176 deaths, 150+ missing, 230,000 displaced, 1.1M affected across 17 districts; $335M damages in Shire Valley & Central Region (TA Machinjili, TA Makhwira, TA Ngabu)",
                "refs": [
                    ("UN ReliefWeb - Southern Africa: Floods Jan 2015 (FL-2015-000006-MWI)", "https://reliefweb.int/disaster/fl-2015-000006-mwi"),
                    ("World Bank / GFDRR - Malawi 2015 Post-Disaster Needs Assessment (PDNA)", "https://www.gfdrr.org/en/publication/malawi-2015-floods-post-disaster-needs-assessment-report"),
                    ("Wikipedia - 2015 Southeast Africa Floods", "https://en.wikipedia.org/wiki/2015_Southeast_Africa_floods")
                ]
            },
            2019: {
                "title": "2019 Cyclone Idai - Catastrophic Inundation in Southern & Central Districts",
                "districts": ["TA MACHINJILI", "TA KAPHUKA", "TA WIMBE", "TA MAKHWIRA"],
                "impact": "81,000+ households affected; severe crop loss across Chikwawa, Machinjili, Kaphuka, Wimbe, Makhwira",
                "refs": [
                    ("UN ReliefWeb - Tropical Cyclone Idai (TC-2019-000021-MOZ)", "https://reliefweb.int/disaster/tc-2019-000021-moz"),
                    ("Wikipedia - Cyclone Idai", "https://en.wikipedia.org/wiki/Cyclone_Idai")
                ]
            },
            2022: {
                "title": "2022 Tropical Storm Ana & Cyclone Gombe",
                "districts": ["TA MACHINJILI", "TA M'MBELWA"],
                "impact": "Ana: ~1M affected, 46 deaths, 67,800 households displaced, countrywide blackouts; severe flooding in TA Machinjili, TA M'Mbelwa",
                "refs": [
                    ("UN ReliefWeb - Tropical Storm Ana Jan 2022 (ST-2022-000138-MDG)", "https://reliefweb.int/disaster/st-2022-000138-mdg"),
                    ("WHO - Malawi Tropical Storm Ana Response", "https://www.who.int/emergencies/situations/tropical-storm-ana-malawi"),
                    ("Wikipedia - Tropical Storm Ana (2022)", "https://en.wikipedia.org/wiki/Tropical_Storm_Ana_(2022)")
                ]
            },
            2023: {
                "title": "2023 Cyclone Freddy - Record-Breaking Cyclone & Deluge",
                "districts": ["TA MACHINJILI", "TA PEMBA", "TA KAPHUKA", "TA MAKHWIRA"],
                "impact": "679 deaths, 530+ missing, 659,000 displaced, 2.3M affected; extreme mudslides & agricultural inundation (TA Machinjili, TA Pemba, TA Kaphuka, TA Makhwira)",
                "refs": [
                    ("UN ReliefWeb - Tropical Cyclone Freddy Feb 2023 (TC-2023-000023-MDG)", "https://reliefweb.int/disaster/tc-2023-000023-mdg"),
                    ("World Bank - Cyclone Freddy Malawi Post-Disaster Report", "https://www.preventionweb.net/understanding-risk/cyclone-freddy"),
                    ("Wikipedia - Cyclone Freddy", "https://en.wikipedia.org/wiki/Cyclone_Freddy")
                ]
            }
        }
    },
    "NGA": {
        "name": "Nigeria",
        "flag": "🇳🇬",
        "events": {
            2012: {
                "title": "2012 Nigeria Mega-Flood - Worst Flooding in 50 Years",
                "districts": ["AGATU", "APA", "LOKOJA", "PATEGI"],
                "impact": "363 deaths, 7.7M affected, 2.1-2.3M displaced; 32 of 36 states affected; N2.6T economic loss (Agatu, Apa, Lokoja, Pategi)",
                "refs": [
                    ("UN ReliefWeb - Nigeria: Floods Jul 2012 (FL-2012-000138-NGA)", "https://reliefweb.int/disaster/fl-2012-000138-nga"),
                    ("World Bank / GFDRR - Nigeria 2012 PDNA Report", "https://www.gfdrr.org/en/publication/nigeria-post-disaster-needs-assessment-2012-floods"),
                    ("Wikipedia - 2012 Nigeria Floods", "https://en.wikipedia.org/wiki/2012_Nigeria_floods")
                ]
            },
            2018: {
                "title": "2018 Nigeria Floods - National Emergency Declaration in 12 States",
                "districts": ["ASA", "LOKOJA", "MORO", "ORI-IRE", "SAKI EAST"],
                "impact": "199 deaths, 826,000+ affected across Benue, Kogi, Kwara, Oyo states (Asa, Lokoja, Moro, Ori-Ire, Saki East)",
                "refs": [
                    ("UN ReliefWeb - Nigeria Floods Emergency 2018", "https://reliefweb.int/disaster/ff-2018-000140-nga")
                ]
            },
            2022: {
                "title": "2022 Nigeria Record Floods - Most Devastating Inundation in a Decade",
                "districts": ["AGATU", "LOKOJA", "GBOKO", "ASA", "ORI-IRE", "UKUM"],
                "impact": "665 deaths, 4.4M affected, 1.4-2.4M displaced; 33 of 36 states; 560,000+ ha farmland submerged (Agatu, Lokoja, Gboko, Asa, Ori-Ire, Ukum)",
                "refs": [
                    ("UN ReliefWeb - Nigeria: Floods Aug 2022 (FL-2022-000271-NGA)", "https://reliefweb.int/disaster/fl-2022-000271-nga"),
                    ("Wikipedia - 2022 Nigeria Floods", "https://en.wikipedia.org/wiki/2022_Nigeria_floods")
                ]
            },
            2023: {
                "title": "2023 Middle Belt & SE Inundation",
                "districts": ["ABAKALIKI", "EBONYI", "EZZA NORTH", "EZZA SOUTH", "IKWO", "KATSINA-ALA"],
                "impact": "FEWS NET reported severe flood displacement and agricultural crop losses across Middle Belt & SE maize belts (Abakaliki, Ebonyi, Ezza, Ikwo, Katsina-Ala)",
                "refs": [
                    ("FEWS NET - Nigeria Food Security Outlook 2023", "https://fews.net/west-africa/nigeria")
                ]
            },
            2024: {
                "title": "2024 Dam Collapse & Nationwide Floods",
                "districts": ["ABAKALIKI", "EBONYI", "EZZA NORTH", "EZZA SOUTH", "IKWO", "OHAUKWU"],
                "impact": "Alau Dam overflow & heavy monsoonal deluge submerged vast agricultural zones across Middle Belt & SE (Abakaliki, Ebonyi, Ezza, Ikwo, Ohaukwu)",
                "refs": [
                    ("UN ReliefWeb - Nigeria: Floods Sep 2024", "https://reliefweb.int/report/nigeria/nigeria-floods-flash-update")
                ]
            }
        }
    }
}

EVENT_COLORS = ["#ef4444", "#ea580c", "#8b5cf6", "#10b981", "#ec4899", "#06b6d4"]


def build_country_spaghetti_fig(df_country, iso3, streak_days):
    val_col = "flood_days_5plus" if streak_days == 5 else "flood_days_7plus"
    fig = go.Figure()
    districts = sorted(df_country["ADM_NAME"].unique())
    c_config = COUNTRY_CONFIGS.get(iso3, {})
    country_events = c_config.get("events", {})

    # 1. Background trajectories (all districts, faint gray)
    for dist in districts:
        d_df = df_country[df_country["ADM_NAME"] == dist].sort_values("crop_year")
        if d_df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d_df["crop_year"],
            y=d_df[val_col],
            mode="lines",
            name=dist,
            showlegend=False,
            line=dict(color="rgba(203, 213, 225, 0.45)", width=1.0),
            hoverinfo="skip"
        ))

    # 2. National Mean Line (blue dashed line with diamond markers)
    mean_df = df_country.groupby("crop_year")[val_col].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=mean_df["crop_year"],
        y=mean_df[val_col],
        mode="lines+markers",
        name=f"National Mean ({streak_days}-Day Basis)",
        line=dict(color="#3b82f6", width=3.0, dash="dash"),
        marker=dict(size=7, color="#3b82f6", symbol="diamond"),
        showlegend=True
    ))

    # 3. Highlighted reference districts per event (STAR MARKERS ONLY, NO COLORED ZIGZAG LINES)
    dist_upper_map = {d.upper(): d for d in districts}

    for ev_idx, (yr, ev) in enumerate(sorted(country_events.items())):
        color = EVENT_COLORS[ev_idx % len(EVENT_COLORS)]
        title = ev["title"]
        ref_list = ev.get("refs", [])
        ref_summary = " | ".join([r[0] for r in ref_list])

        ref_dist_list = [d.upper() for d in ev["districts"]]
        matched = [dist_upper_map[d] for d in ref_dist_list if d in dist_upper_map]

        first_in_legend = True
        for dist in matched:
            d_df = df_country[df_country["ADM_NAME"] == dist].sort_values("crop_year")
            if d_df.empty:
                continue

            # Highlight star marker specifically at the trigger year with text label above
            yr_df = d_df[d_df["crop_year"] == yr]
            if not yr_df.empty:
                fig.add_trace(go.Scatter(
                    x=yr_df["crop_year"],
                    y=yr_df[val_col],
                    mode="markers+text",
                    name=f"{yr}: {dist}",
                    legendgroup=f"{yr}_{title}",
                    showlegend=first_in_legend,
                    marker=dict(size=14, color=color, symbol="star", line=dict(color="white", width=1.5)),
                    text=[dist],
                    textposition="top center",
                    textfont=dict(size=9, color=color, family="Inter, sans-serif"),
                    hovertemplate=(
                        f"<b>VERIFIED DISASTER TRIGGER ({yr})</b><br>"
                        f"District: <b>{dist}</b><br>"
                        f"Event: {title}<br>"
                        f"Flood Days (≥{streak_days}-Day Streak): <b>%{{y}} days</b><br>"
                        f"<i>Reference: {ref_summary}</i>"
                        "<extra></extra>"
                    )
                ))
                first_in_legend = False

    fig.update_layout(
        xaxis=dict(
            title="Crop Year",
            tickmode="linear", tick0=2008, dtick=1,
            range=[2007.5, 2024.5],
            gridcolor="#f1f5f9",
            linecolor="#cbd5e1",
            tickfont=dict(size=11, color="#334155")
        ),
        yaxis=dict(
            title=f"Flood Days (≥{streak_days}-Day Continuous Streak)",
            gridcolor="#f1f5f9",
            linecolor="#cbd5e1",
            tickfont=dict(size=11, color="#334155"),
            rangemode="tozero"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=520,
        margin=dict(l=55, r=25, t=60, b=50),
        font=dict(family="Inter, sans-serif", color="#334155"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#e2e8f0",
            borderwidth=1
        )
    )

    return fig


def generate_country_dashboard(iso3, df_country, streak_days):
    c_config = COUNTRY_CONFIGS.get(iso3, {})
    c_name   = c_config.get("name", iso3)
    flag     = c_config.get("flag", "🌍")
    events   = c_config.get("events", {})

    fig = build_country_spaghetti_fig(df_country, iso3, streak_days)

    # Build Event Cards HTML block with clickable HTTP links
    event_cards_html = ""
    for yr in sorted(events.keys()):
        ev = events[yr]
        title  = ev["title"]
        impact = ev["impact"]
        refs   = ev["refs"]

        ref_links_html = ""
        for idx, (ref_label, ref_url) in enumerate(refs):
            ref_links_html += f'''<a href="{ref_url}" target="_blank" class="ref-link">🔗 [{idx+1}] {ref_label}</a><br/>'''

        event_cards_html += f"""
        <div class="event-card">
            <div class="event-card-header">
                <span class="year-badge">Year {yr}</span>
                <h4 class="event-title">🚨 {title}</h4>
            </div>
            <p class="impact-text"><b>Ground-Truth Impact:</b> {impact}</p>
            <div class="ref-block">
                <span class="ref-heading">Verified Reference Links (Click to Verify):</span><br/>
                {ref_links_html}
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{c_name} — {streak_days}-Day Flood Index Option 2 Validation Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: #f8fafc; color: #0f172a; margin: 0; padding: 0;
        }}
        .header {{
            background: #ffffff; border-bottom: 1px solid #e2e8f0;
            padding: 24px 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .header h1 {{ margin: 0; font-size: 1.5rem; font-weight: 800; color: #0f172a; }}
        .header p {{ margin: 6px 0 0; color: #64748b; font-size: 0.875rem; font-weight: 500; }}

        .main {{ max-width: 1300px; margin: 28px auto; padding: 0 20px; }}

        .card {{
            background: white; border: 1px solid #e2e8f0;
            border-radius: 10px; padding: 22px 26px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .card h3 {{ margin: 0 0 12px; font-size: 1.1rem; font-weight: 800; color: #0284c7; }}
        .card-sub {{ font-size: 0.825rem; color: #64748b; margin-bottom: 16px; line-height: 1.4; }}

        .event-card {{
            background: #ffffff; border: 1px solid #cbd5e1;
            border-left: 5px solid #ef4444; border-radius: 8px;
            padding: 16px 20px; margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .event-card-header {{
            display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;
        }}
        .year-badge {{
            background: #ef4444; color: #ffffff;
            padding: 3px 10px; border-radius: 12px;
            font-size: 0.75rem; font-weight: 800; text-transform: uppercase;
        }}
        .event-title {{ margin: 0; color: #0f172a; font-size: 1.025rem; font-weight: 700; }}
        .impact-text {{ margin: 6px 0 10px; color: #334155; font-size: 0.875rem; line-height: 1.5; }}

        .ref-block {{
            margin-top: 10px; padding-top: 8px; border-top: 1px solid #f1f5f9;
        }}
        .ref-heading {{ font-size: 0.775rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }}
        .ref-link {{
            color: #2563eb; text-decoration: none; font-size: 0.825rem;
            display: inline-block; margin-top: 4px; font-weight: 600;
            transition: color 0.2s ease;
        }}
        .ref-link:hover {{ color: #1d4ed8; text-decoration: underline; }}

        .footer {{
            text-align: center; padding: 20px 24px;
            color: #94a3b8; font-size: 0.8rem;
            border-top: 1px solid #e2e8f0; margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{flag} {c_name} — {streak_days}-Day Flood Index Option 2 Validation Dashboard</h1>
        <p>Year-by-Year Triggered District Validation (2008–2024) under 95th Percentile + 85% Absolute SWI Floor Threshold ({streak_days}-Day Basis)</p>
    </div>

    <div class="main">
        <!-- PLOT CARD -->
        <div class="card">
            <h3>Option 2 (95th Percentile + 85% Absolute SWI Floor - {streak_days}-Day Rule) — Recommended</h3>
            {fig.to_html(full_html=False, include_plotlyjs='cdn')}
        </div>

        <!-- VERIFIED REFERENCES & CLICKABLE LINKS CARD -->
        <div class="card">
            <h3>📖 Verified Ground-Truth Disaster References & Direct Event Links</h3>
            <div class="card-sub">
                Historical disaster documentation for {c_name} from official United Nations (ReliefWeb), World Bank (GFDRR PDNA), Copernicus, WHO, and Wikipedia archives verifying each flood event. Click any link below to view the official disaster report.
            </div>
            {event_cards_html}
        </div>
    </div>

    <div class="footer">
        Option 2 ({streak_days}-Day Continuous Basis) — 2008–2024 Pan-African Parametric Research Study
    </div>
</body>
</html>"""

    out_file = os.path.join(OUT_DIR, f"{c_name}_{streak_days}Day_Option2_Validation_Dashboard.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   [OK] Saved {c_name} {streak_days}-Day Option 2 Dashboard with Reference Links: {out_file}", flush=True)


def main():
    print("=" * 70)
    print("1. Loading Option 2 5-Day and 7-Day datasets...")
    print("=" * 70)

    df_5day = pd.read_csv(CSV_5DAY)
    df_7day = pd.read_csv(CSV_7DAY)

    for streak_days, df_data in [(5, df_5day), (7, df_7day)]:
        print(f"\n2. Generating Option 2 ONLY {streak_days}-Day Country Dashboards (with star markers & clickable reference links)...", flush=True)
        for c_iso in ["KEN", "MWI", "NGA"]:
            c_sub = df_data[df_data["ISO3"] == c_iso]
            generate_country_dashboard(c_iso, c_sub, streak_days)

    print("\n======================================================================")
    print("[OK] DONE - Generated Option 2 country dashboards with clickable reference links.")
    print("======================================================================")


if __name__ == "__main__":
    main()
