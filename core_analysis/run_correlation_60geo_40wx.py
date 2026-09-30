"""
run_correlation_60geo_40wx.py
==============================
Generates the Inter-District Flood Correlation Dashboard for the
60% Geography / 40% Weather weighting.

Output:
  - output/agricultural/outputs/Africa_Flood_Correlation_Map_60geo_40wx.html
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "outputs", "Africa_Maize_Flood_Annual_Option2_5Day.csv")
SHP_PATH = os.path.join(BASE_DIR, "data", "africa_agricultural_domain_2019.shp")
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

WEIGHT_KEY   = "60geo_40wx"
WEIGHT_LABEL = "60% Geography / 40% Weather"


def classify_risk_tier(rank, total_clusters, avg_days):
    if total_clusters == 2:
        return "High Risk Cluster" if rank == 1 else "Low Risk Cluster"
    elif total_clusters <= 4:
        if rank == 1:
            return "High Risk Cluster"
        elif rank == total_clusters:
            return "Low Risk Cluster"
        else:
            return "Moderate Risk Cluster"
    else:
        third = total_clusters / 3.0
        if rank <= third:
            return "High Risk Cluster"
        elif rank > (total_clusters - third):
            return "Low Risk Cluster"
        else:
            return "Moderate Risk Cluster"


def main():
    print("=" * 70)
    print(f"Inter-District Flood Correlation Dashboard — {WEIGHT_LABEL}")
    print("=" * 70)

    df = pd.read_csv(DATA_CSV)
    df["DISTRICT_KEY"] = df["COUNTRY"].astype(str).str.strip() + "||" + df["ADM_NAME"].astype(str).str.strip()
    years = [int(y) for y in sorted(df["crop_year"].unique())]

    pivot_df = df.pivot_table(index="DISTRICT_KEY", columns="crop_year", values="flood_days_5plus", aggfunc="first").fillna(0)
    district_keys = pivot_df.index.tolist()

    print(f"   Districts: {len(district_keys):,}, Crop Years: {len(years)} ({min(years)}–{max(years)})")

    print("\nComputing 1,638 x 1,638 Inter-District Pearson Correlation Matrix...")
    corr_matrix = pivot_df.T.corr(method="pearson").fillna(0).values

    print("\nLoading GADM agricultural district shapefile...")
    gdf = gpd.read_file(SHP_PATH)[["ADM_NAME", "COUNTRY", "geometry"]]
    gdf = gdf[gdf["COUNTRY"] != "Morocco"]
    gdf["ADM_NAME"] = gdf["ADM_NAME"].astype(str).str.strip()
    gdf["COUNTRY"]  = gdf["COUNTRY"].astype(str).str.strip()
    gdf["DISTRICT_KEY"] = gdf["COUNTRY"] + "||" + gdf["ADM_NAME"]

    gdf_sub = gdf[gdf["DISTRICT_KEY"].isin(district_keys)].drop_duplicates(subset=["DISTRICT_KEY"]).copy()
    gdf_sub = gdf_sub.set_index("DISTRICT_KEY").loc[district_keys].reset_index()
    gdf_sub["DISTRICT_KEY_PROP"] = gdf_sub["DISTRICT_KEY"]
    gdf_sub["geometry"] = gdf_sub["geometry"].simplify(0.04, preserve_topology=True)

    json_meta_path = os.path.join(OUT_DIR, f"cluster_labels_{WEIGHT_KEY}.json")
    out_map_html   = os.path.join(OUT_DIR, f"Africa_Flood_Correlation_Map_{WEIGHT_KEY}.html")

    print(f"\nBuilding correlation dashboard for {WEIGHT_LABEL}...")
    with open(json_meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    best_k = int(meta["best_k"])
    best_k_str = str(best_k)
    best_clusters = meta["clusters_by_k"][best_k_str]
    key_to_cluster = dict(zip(meta["district_keys"], best_clusters))

    cluster_tot_days = {}
    cluster_counts   = {}
    for key, c_id in key_to_cluster.items():
        days_sum = float(pivot_df.loc[key].sum()) / len(years)
        cluster_tot_days[c_id] = cluster_tot_days.get(c_id, 0.0) + days_sum
        cluster_counts[c_id]   = cluster_counts.get(c_id, 0) + 1

    cluster_avg_days = {c: round(cluster_tot_days[c] / cluster_counts[c], 2) for c in cluster_tot_days}
    sorted_clusters  = sorted(cluster_avg_days.keys(), key=lambda c: cluster_avg_days[c], reverse=True)

    cluster_risk_label = {}
    for rank_idx, c_id in enumerate(sorted_clusters):
        tier = classify_risk_tier(rank_idx + 1, best_k, cluster_avg_days[c_id])
        cluster_risk_label[c_id] = f"{tier} (Zone {c_id} - Avg {cluster_avg_days[c_id]} d/yr)"

    district_data = {}
    for idx, key in enumerate(district_keys):
        adm_name = gdf_sub.loc[idx, "ADM_NAME"]
        country  = gdf_sub.loc[idx, "COUNTRY"]
        c_id     = int(key_to_cluster.get(key, 1))
        c_risk   = cluster_risk_label.get(c_id, f"Zone {c_id}")

        ts_values = [float(v) for v in pivot_df.loc[key].tolist()]
        tot_days  = int(sum(ts_values))
        avg_days  = round(tot_days / len(years), 2)

        corrs_row = [round(float(r), 3) for r in corr_matrix[idx]]

        sorted_indices = np.argsort(corr_matrix[idx])
        pos_indices = [int(i) for i in sorted_indices[::-1] if i != idx][:10]
        neg_indices = [int(i) for i in sorted_indices if i != idx][:10]

        pos_list = []
        for pi in pos_indices:
            other_key  = district_keys[pi]
            other_adm  = gdf_sub.loc[pi, "ADM_NAME"]
            other_c    = gdf_sub.loc[pi, "COUNTRY"]
            other_zone = int(key_to_cluster.get(other_key, 1))
            r_val      = round(float(corr_matrix[idx][pi]), 3)
            pos_list.append({
                "name": other_adm, "country": other_c, "zone": other_zone, "r": r_val
            })

        neg_list = []
        for ni in neg_indices:
            other_key  = district_keys[ni]
            other_adm  = gdf_sub.loc[ni, "ADM_NAME"]
            other_c    = gdf_sub.loc[ni, "COUNTRY"]
            other_zone = int(key_to_cluster.get(other_key, 1))
            r_val      = round(float(corr_matrix[idx][ni]), 3)
            neg_list.append({
                "name": other_adm, "country": other_c, "zone": other_zone, "r": r_val
            })

        district_data[key] = {
            "name": adm_name,
            "country": country,
            "zone": c_id,
            "risk_desc": c_risk,
            "tot_days": tot_days,
            "avg_days": avg_days,
            "corrs": corrs_row,
            "pos": pos_list,
            "neg": neg_list
        }

    gdf_sub["cluster"] = [int(key_to_cluster.get(k, 1)) for k in district_keys]
    gdf_sub["risk_desc"] = [cluster_risk_label.get(int(key_to_cluster.get(k, 1)), "") for k in district_keys]
    geojson_dict = json.loads(gdf_sub.set_index("DISTRICT_KEY").to_json())

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inter-District Flood Correlation Dashboard (__WEIGHT_LABEL__)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        *, *::before, *::after { box-sizing: border-box; }
        body {
            margin: 0; padding: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: #f8fafc; color: #0f172a;
            display: flex; height: 100vh; overflow: hidden;
        }

        .app-header {
            position: absolute; top: 0; left: 0; right: 0; height: 52px;
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0; z-index: 1000;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .app-header h1 { margin: 0; font-size: 1.05rem; font-weight: 800; color: #0f172a; }
        .app-header .subtitle { font-size: 0.775rem; color: #64748b; font-weight: 500; margin-top: 1px; }

        .app-container {
            display: flex; width: 100%; height: calc(100vh - 52px); margin-top: 52px; position: relative;
        }

        #map { flex: 1; height: 100%; background: #f8fafc; transition: all 0.3s ease; }

        .side-panel {
            width: 0; opacity: 0; pointer-events: none;
            background: #ffffff; border-left: 1px solid #e2e8f0;
            display: flex; flex-direction: column; overflow-y: auto;
            padding: 0; box-shadow: -4px 0 20px rgba(0,0,0,0.06);
            transition: all 0.3s ease; position: relative; z-index: 900;
        }
        .side-panel.open {
            width: 440px; opacity: 1; pointer-events: auto; padding: 22px;
        }
        .side-panel::-webkit-scrollbar { width: 6px; }
        .side-panel::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

        .close-btn {
            position: absolute; top: 14px; right: 16px;
            width: 28px; height: 28px; border-radius: 50%;
            background: #f1f5f9; border: 1px solid #cbd5e1;
            color: #475569; font-size: 14px; font-weight: 700;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.2s ease;
        }
        .close-btn:hover { background: #e2e8f0; color: #0f172a; }

        .district-header {
            border-bottom: 1px solid #e2e8f0; padding-bottom: 14px; margin-bottom: 16px; padding-right: 30px;
        }
        .district-header h2 { margin: 0; font-size: 1.3rem; font-weight: 800; color: #0f172a; }
        .district-header .country-badge {
            display: inline-block; background: #e0f2fe;
            color: #0369a1; border: 1px solid #bae6fd;
            padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-top: 6px;
        }

        .risk-badge {
            display: block; background: #fef3c7; color: #92400e;
            border: 1px solid #fde68a; padding: 4px 10px;
            border-radius: 6px; font-size: 0.75rem; font-weight: 700; margin-top: 8px;
        }

        .zero-notice {
            display: none; background: #eff6ff; border: 1px solid #bfdbfe;
            color: #1e40af; padding: 10px 12px; border-radius: 6px;
            font-size: 0.75rem; line-height: 1.45; margin-top: 10px; font-weight: 500;
        }

        .stats-grid {
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; margin-top: 14px;
        }
        .stat-card {
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px;
        }
        .stat-card .label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
        .stat-card .val { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-top: 2px; }

        .section-title {
            font-size: 0.85rem; font-weight: 700; color: #0284c7;
            margin: 16px 0 10px; border-left: 3px solid #0284c7; padding-left: 8px;
        }

        .corr-list { width: 100%; border-collapse: collapse; font-size: 0.775rem; margin-bottom: 14px; }
        .corr-list th { text-align: left; color: #475569; padding: 6px 8px; border-bottom: 1px solid #cbd5e1; font-size: 0.7rem; font-weight: 700; }
        .corr-list td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        .corr-list tr:hover td { background: #f1f5f9; }
        .r-pos { color: #0284c7; font-weight: 700; }
        .r-neg { color: #dc2626; font-weight: 700; }

        .legend-box {
            background: #ffffff; border: 1px solid #cbd5e1;
            padding: 12px 16px; border-radius: 8px; color: #0f172a; font-size: 0.75rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); line-height: 1.4;
        }
        .legend-title { font-weight: 800; margin-bottom: 8px; color: #0f172a; font-size: 0.8rem; }
        .legend-item { display: flex; align-items: center; margin-bottom: 5px; font-weight: 500; font-size: 0.725rem; }
        .legend-swatch { width: 16px; height: 16px; border-radius: 3px; margin-right: 8px; border: 1px solid rgba(0,0,0,0.15); }
    </style>
</head>
<body>

    <div class="app-header">
        <div>
            <h1>📊 Inter-District Flood Correlation Dashboard</h1>
            <div class="subtitle">__WEIGHT_LABEL__ — 95th Percentile + 85% SWI Floor Threshold (5-Day Basis) Spatial Risk Regionalization</div>
        </div>
    </div>

    <div class="app-container">
        <div id="map"></div>

        <div class="side-panel" id="side-panel">
            <button class="close-btn" onclick="closePanel()">✕</button>
            <div id="panel-content">
                <div class="district-header">
                    <h2 id="p-adm">District Name</h2>
                    <span class="country-badge" id="p-country">Country</span>
                    <div class="risk-badge" id="p-risk">Risk Category</div>
                    <div class="zero-notice" id="p-zero-notice">
                        ℹ️ <b>Zero 5-Continuous Day Flood Triggers (2008–2024)</b><br>
                        This district recorded 0 flood days under the 5-day continuous streak rule (95th %ile + 85% SWI floor). Short-duration inundation events (&lt; 5 days, such as intense flash floods or rapid cyclonic deluge) or hyper-arid baselines result in a constant zero series (&sigma;=0), yielding a mathematical 0.000 Pearson correlation.
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="label">Total Flood Days (08-24)</div>
                        <div class="val" id="p-tot">0 days</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Avg Flood Days/Year</div>
                        <div class="val" id="p-avg">0.00 d/yr</div>
                    </div>
                </div>

                <div class="section-title">🔥 Top 10 Positively Correlated Districts (10+)</div>
                <table class="corr-list">
                    <thead>
                        <tr><th>District</th><th>Country</th><th>Zone</th><th>Pearson r</th></tr>
                    </thead>
                    <tbody id="p-pos-body"></tbody>
                </table>

                <div class="section-title">❄️ Top 10 Negatively / Lowest Correlated Districts (10-)</div>
                <table class="corr-list">
                    <thead>
                        <tr><th>District</th><th>Country</th><th>Zone</th><th>Pearson r</th></tr>
                    </thead>
                    <tbody id="p-neg-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const geojsonData = __GEOJSON_DATA__;
        const districtData = __DISTRICT_DATA__;

        const map = L.map('map', {
            center: [2.5, 17.5],
            zoom: 4,
            zoomControl: true
        });

        const lightBasemap = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);

        const legend = L.control({ position: 'bottomleft' });
        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'legend-box');
            div.innerHTML = `
                <div class="legend-title">Pearson Correlation (r)</div>
                <div class="legend-item"><span class="legend-swatch" style="background:#0284c7;"></span> Strong Positive (r &ge; +0.70)</div>
                <div class="legend-item"><span class="legend-swatch" style="background:#7dd3fc;"></span> Moderate Positive (+0.30 &le; r &lt; +0.70)</div>
                <div class="legend-item"><span class="legend-swatch" style="background:#e2e8f0;"></span> Weak / Neutral (-0.30 &lt; r &lt; +0.30)</div>
                <div class="legend-item"><span class="legend-swatch" style="background:#f87171;"></span> Moderate Negative (-0.70 &lt; r &le; -0.30)</div>
                <div class="legend-item"><span class="legend-swatch" style="background:#dc2626;"></span> Strong Negative (r &le; -0.70)</div>
            `;
            return div;
        };
        legend.addTo(map);

        function getCorrColor(r) {
            if (r === null || r === undefined) return '#cbd5e1';
            if (r >= 0) {
                let t = Math.min(1, Math.max(0, r));
                let red = Math.round(241 + (2 - 241) * t);
                let green = Math.round(245 + (132 - 245) * t);
                let blue = Math.round(249 + (199 - 249) * t);
                return `rgb(${red}, ${green}, ${blue})`;
            } else {
                let t = Math.min(1, Math.max(0, -r));
                let red = Math.round(241 + (220 - 241) * t);
                let green = Math.round(245 + (38 - 245) * t);
                let blue = Math.round(249 + (38 - 249) * t);
                return `rgb(${red}, ${green}, ${blue})`;
            }
        }

        function initialStyle(feature) {
            return {
                fillColor: '#e2e8f0',
                weight: 0.5,
                opacity: 0.8,
                color: '#94a3b8',
                fillOpacity: 0.65
            };
        }

        let selectedKey = null;

        function onEachFeature(feature, layer) {
            const key = feature.id || (feature.properties && feature.properties.DISTRICT_KEY_PROP) || (feature.properties && feature.properties.DISTRICT_KEY);
            const adm = (feature.properties && feature.properties.ADM_NAME) || "";
            const country = (feature.properties && feature.properties.COUNTRY) || "";
            const riskDesc = (feature.properties && feature.properties.risk_desc) || "";

            layer.bindTooltip(`<b>${adm}</b> (${country})<br>${riskDesc}`, {sticky: true});

            layer.on({
                click: function(e) {
                    selectedKey = key;
                    updateMapAndSidePanel(key);
                }
            });
        }

        const geojsonLayer = L.geoJSON(geojsonData, {
            style: initialStyle,
            onEachFeature: onEachFeature
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds());

        function closePanel() {
            const panel = document.getElementById('side-panel');
            panel.classList.remove('open');
            selectedKey = null;
            setTimeout(() => { map.invalidateSize(); }, 300);
        }

        function updateMapAndSidePanel(key) {
            const data = districtData[key];
            if (!data) return;

            const corrs = data.corrs;

            let featureIdx = 0;
            geojsonLayer.eachLayer(function(layer) {
                const rVal = corrs[featureIdx];
                const isSelected = (layer.feature.id === key) ||
                                   (layer.feature.properties && layer.feature.properties.DISTRICT_KEY_PROP === key);

                if (isSelected) {
                    layer.setStyle({
                        fillColor: '#0284c7',
                        fillOpacity: 1.0,
                        weight: 3,
                        color: '#d97706'
                    });
                    layer.bringToFront();
                } else {
                    layer.setStyle({
                        fillColor: getCorrColor(rVal),
                        fillOpacity: 0.85,
                        weight: 0.4,
                        color: 'rgba(0,0,0,0.15)'
                    });
                }
                featureIdx++;
            });

            const panel = document.getElementById('side-panel');
            panel.classList.add('open');
            setTimeout(() => { map.invalidateSize(); }, 300);

            document.getElementById('p-adm').innerText = data.name;
            document.getElementById('p-country').innerText = data.country;
            document.getElementById('p-risk').innerText = '🏷️ ' + data.risk_desc;
            document.getElementById('p-tot').innerText = data.tot_days + ' days';
            document.getElementById('p-avg').innerText = data.avg_days.toFixed(2) + ' d/yr';

            const zeroNotice = document.getElementById('p-zero-notice');
            if (data.tot_days === 0) {
                zeroNotice.style.display = 'block';
            } else {
                zeroNotice.style.display = 'none';
            }

            const posBody = document.getElementById('p-pos-body');
            posBody.innerHTML = '';
            data.pos.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><b>${item.name}</b></td>
                                <td>${item.country}</td>
                                <td>Z${item.zone}</td>
                                <td class="r-pos">+${item.r.toFixed(3)}</td>`;
                posBody.appendChild(tr);
            });

            const negBody = document.getElementById('p-neg-body');
            negBody.innerHTML = '';
            data.neg.forEach(item => {
                const tr = document.createElement('tr');
                const rClass = item.r >= 0 ? 'r-pos' : 'r-neg';
                const rSign = item.r >= 0 ? '+' : '';
                tr.innerHTML = `<td><b>${item.name}</b></td>
                                <td>${item.country}</td>
                                <td>Z${item.zone}</td>
                                <td class="${rClass}">${rSign}${item.r.toFixed(3)}</td>`;
                negBody.appendChild(tr);
            });
        }
    </script>
</body>
</html>"""

    filled_html = html_template \
        .replace("__WEIGHT_LABEL__", WEIGHT_LABEL) \
        .replace("__GEOJSON_DATA__", json.dumps(geojson_dict)) \
        .replace("__DISTRICT_DATA__", json.dumps(district_data))

    with open(out_map_html, "w", encoding="utf-8") as f:
        f.write(filled_html)
    print(f"   [OK] Saved: {out_map_html}")


if __name__ == "__main__":
    main()
