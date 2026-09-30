"""
run_cluster_trajectories.py
============================
Generates interactive cluster trajectory dashboards for all 3 clustering weightings:
  1. 60% Geography / 40% Weather
  2. 70% Geography / 30% Weather
  3. 30% Geography / 70% Weather

Each dashboard shows the annual mean flood days per cluster over 2008–2024 as
colored trajectory lines, with a Pan-African national mean overlay.

Outputs:
  - output/agricultural/outputs/Cluster_Trajectories_60geo_40wx.html
  - output/agricultural/outputs/Cluster_Trajectories_70geo_30wx.html
  - output/agricultural/outputs/Cluster_Trajectories_30geo_70wx.html
"""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "outputs", "Africa_Maize_Flood_Annual_Option2_5Day.csv")
OUT_DIR  = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

CLUSTER_CONFIGS = [
    {"key": "60geo_40wx", "label": "60% Geography / 40% Weather"},
    {"key": "70geo_30wx", "label": "70% Geography / 30% Weather"},
    {"key": "30geo_70wx", "label": "30% Geography / 70% Weather"},
]

DISCRETE_PALETTE = [
    "#0284c7", "#f97316", "#16a34a", "#dc2626", "#8b5cf6",
    "#a16207", "#ec4899", "#6b7280", "#84cc16", "#06b6d4",
    "#6366f1", "#ea580c", "#22d3ee", "#e11d48", "#a3e635"
]


def classify_risk_tier(rank, total_clusters):
    if total_clusters == 2:
        return "High Risk" if rank == 1 else "Low Risk"
    elif total_clusters <= 4:
        if rank == 1:
            return "High Risk"
        elif rank == total_clusters:
            return "Low Risk"
        else:
            return "Moderate Risk"
    else:
        third = total_clusters / 3.0
        if rank <= third:
            return "High Risk"
        elif rank > (total_clusters - third):
            return "Low Risk"
        else:
            return "Moderate Risk"


def build_trajectory_dashboard(df, pivot_df, years, cfg):
    """Build a single trajectory dashboard for one clustering weighting."""
    weight_key   = cfg["key"]
    weight_label = cfg["label"]

    json_path = os.path.join(OUT_DIR, f"cluster_labels_{weight_key}.json")
    if not os.path.exists(json_path):
        print(f"   [SKIP] Cluster metadata not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    best_k = int(meta["best_k"])
    best_labels = meta["clusters_by_k"][str(best_k)]
    district_keys = meta["district_keys"]
    sil_score = meta["sil_scores"][str(best_k)]

    key_to_cluster = dict(zip(district_keys, best_labels))

    # Compute cluster-level annual mean flood days
    cluster_annual = {}  # {cluster_id: {year: [values]}}
    for key in district_keys:
        c_id = key_to_cluster[key]
        if c_id not in cluster_annual:
            cluster_annual[c_id] = {yr: [] for yr in years}
        for yr in years:
            val = float(pivot_df.loc[key, yr]) if yr in pivot_df.columns else 0.0
            cluster_annual[c_id][yr].append(val)

    # Compute means per cluster per year
    cluster_means = {}  # {cluster_id: {year: mean_val}}
    cluster_overall_avg = {}
    for c_id in cluster_annual:
        cluster_means[c_id] = {}
        total = 0.0
        for yr in years:
            vals = cluster_annual[c_id][yr]
            mean_val = np.mean(vals) if vals else 0.0
            cluster_means[c_id][yr] = round(mean_val, 3)
            total += mean_val
        cluster_overall_avg[c_id] = round(total / len(years), 3)

    # Sort clusters by overall average (descending = highest risk first)
    sorted_clusters = sorted(cluster_overall_avg.keys(), key=lambda c: cluster_overall_avg[c], reverse=True)

    # Compute Pan-African mean per year
    pan_african_annual = {}
    for yr in years:
        all_vals = []
        for c_id in cluster_annual:
            all_vals.extend(cluster_annual[c_id][yr])
        pan_african_annual[yr] = round(np.mean(all_vals), 3) if all_vals else 0.0

    # Build Plotly figure
    fig = go.Figure()

    # Add cluster trajectories
    for rank_idx, c_id in enumerate(sorted_clusters):
        tier = classify_risk_tier(rank_idx + 1, best_k)
        n_dists = len(cluster_annual[c_id][years[0]])
        color = DISCRETE_PALETTE[(c_id - 1) % len(DISCRETE_PALETTE)]
        label = f"Zone {c_id}: {tier} ({n_dists} dists, Avg {cluster_overall_avg[c_id]:.2f} d/yr)"

        y_vals = [cluster_means[c_id][yr] for yr in years]

        fig.add_trace(go.Scatter(
            x=years,
            y=y_vals,
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>Zone {c_id} ({tier})</b><br>"
                          f"Year: %{{x}}<br>"
                          f"Mean Flood Days: %{{y:.2f}}<extra></extra>"
        ))

    # Add Pan-African mean line
    pan_y = [pan_african_annual[yr] for yr in years]
    fig.add_trace(go.Scatter(
        x=years,
        y=pan_y,
        mode="lines+markers",
        name=f"Pan-African Mean ({np.mean(pan_y):.2f} d/yr)",
        line=dict(color="#0f172a", width=3, dash="dash"),
        marker=dict(size=7, symbol="diamond", color="#0f172a"),
        hovertemplate="<b>Pan-African Mean</b><br>"
                      "Year: %{x}<br>"
                      "Mean Flood Days: %{y:.2f}<extra></extra>"
    ))

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=(
                f"<b>Cluster Trajectory Dashboard — {weight_label}</b><br>"
                f"<sup>Option 2 (95th %ile + 85% SWI Floor, 5-Day Basis) | "
                f"Optimal K={best_k} (Silhouette: {sil_score}) | 2008–2024</sup>"
            ),
            font=dict(family="Inter, system-ui, sans-serif", size=15, color="#0f172a"),
            x=0.5
        ),
        xaxis=dict(
            title="Crop Year",
            dtick=1,
            tickangle=-45,
            gridcolor="#e2e8f0",
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="Mean Flood Days per District",
            gridcolor="#e2e8f0",
            zeroline=True,
            zerolinecolor="#cbd5e1",
            tickfont=dict(size=11)
        ),
        legend=dict(
            title=dict(text="<b>Risk Clusters (Ward Linkage)</b>", font=dict(size=11)),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#cbd5e1",
            borderwidth=1,
            font=dict(size=10),
            x=0.01, y=0.99,
            xanchor="left", yanchor="top"
        ),
        margin=dict(l=60, r=30, t=80, b=60),
        hovermode="x unified",
        height=600,
        font=dict(family="Inter, system-ui, sans-serif")
    )

    out_html = os.path.join(OUT_DIR, f"Cluster_Trajectories_{weight_key}.html")
    fig.write_html(out_html, include_plotlyjs="cdn")
    print(f"   [OK] Saved: {out_html}")


def main():
    print("=" * 70)
    print("Cluster Trajectory Dashboards — All 3 Weighting Types")
    print("=" * 70)

    df = pd.read_csv(DATA_CSV)
    df["DISTRICT_KEY"] = df["COUNTRY"].astype(str).str.strip() + "||" + df["ADM_NAME"].astype(str).str.strip()
    years = sorted(df["crop_year"].unique())

    pivot_df = df.pivot_table(
        index="DISTRICT_KEY", columns="crop_year",
        values="flood_days_5plus", aggfunc="first"
    ).fillna(0)

    print(f"   Districts: {len(pivot_df):,}, Crop Years: {len(years)} ({min(years)}–{max(years)})\n")

    for cfg in CLUSTER_CONFIGS:
        print(f"\n--- {cfg['label']} ---")
        build_trajectory_dashboard(df, pivot_df, years, cfg)

    print("\n" + "=" * 70)
    print("All 3 cluster trajectory dashboards generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
