import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Configure UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Paths
base_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
output_folder = os.path.join(base_path, "output", "agricultural")
profile_csv = os.path.join(output_folder, "Agri_Flood_Annual_Stress_Profile.csv")
viz_folder = os.path.join(output_folder, "visualizations")
os.makedirs(viz_folder, exist_ok=True)

print("🔄 Loading Annual Hydrological Stress Profile dataset...")
if not os.path.exists(profile_csv):
    print(f"❌ ERROR: Profile CSV not found at: {profile_csv}")
    sys.exit(1)

df = pd.read_csv(profile_csv)
df = df.dropna().sort_values(['District_Name', 'Crop_Year'])

# Clean up Crop_Year bounds to only include complete study years (2000 to 2024)
df = df[(df['Crop_Year'] >= 2000) & (df['Crop_Year'] <= 2024)].copy()

print(f"Extracted {len(df)} annual district profile records.")

# ──────────────────────────────────────────────────────────
# PART A: INTERACTIVE PARALLEL COORDINATES PLOT (PLOTLY)
# ──────────────────────────────────────────────────────────
print("📊 Generating Plotly Parallel Coordinates Fingerprint Plot...")

fig = go.Figure(data=
    go.Parcoords(
        line=dict(
            color=df['Annual_Waterlogged_Days'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title='Waterlogged Days (D)',
                titleside='right',
                thickness=15
            )
        ),
        dimensions=list([
            dict(range=[2000, 2024],
                 label='Crop Year', values=df['Crop_Year']),
            dict(range=[0, float(df['P_3d_sum'].max() * 1.05)],
                 label='Coincident 3-Day Rain (mm)', values=df['P_3d_sum']),
            dict(range=[float(df['SSI_3d_mean'].min() * 1.1), float(df['SSI_3d_mean'].max() * 1.1)],
                 label='Peak 3-Day SSI', values=df['SSI_3d_mean']),
            dict(range=[0, float(df['Runoff_Q_3d_sum'].max() * 1.05)],
                 label='Peak 3-Day Runoff Q (mm)', values=df['Runoff_Q_3d_sum']),
            dict(range=[0, int(df['Annual_Waterlogged_Days'].max() + 2)],
                 label='Waterlogged Days', values=df['Annual_Waterlogged_Days'])
        ]),
        unselected=dict(line=dict(color='rgba(148, 163, 184, 0.05)'))
    )
)

# Apply premium styles
fig.update_layout(
    template="plotly_white",
    title={
        'text': "Zambia Agricultural Flood Study — 25-Year Hydrological Event Fingerprint<br>"
                "<span style='font-size:12px; color:#64748b;'>Parallel Coordinates Profile (Nov-Apr Season Peak Stress Dates)</span>",
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {'size': 18, 'family': 'Inter, sans-serif', 'color': '#0f172a'}
    },
    paper_bgcolor='#ffffff',
    font_family="Inter, sans-serif",
    height=600,
    margin=dict(l=80, r=80, t=100, b=50)
)

plotly_html_path = os.path.join(viz_folder, "Agri_Flood_Parallel_Coordinates_Fingerprint.html")
fig.write_html(plotly_html_path, include_plotlyjs='cdn')
print(f"  ✅ Interactive Plotly plot saved: {plotly_html_path}")


# ──────────────────────────────────────────────────────────
# PART B: STATIC PARALLEL COORDINATES PLOT (MATPLOTLIB)
# ──────────────────────────────────────────────────────────
print("📊 Generating Matplotlib Parallel Coordinates Fingerprint Plot...")

# Standardize values to [0, 1] range for visual alignment on Matplotlib axes
cols = ['Crop_Year', 'P_3d_sum', 'SSI_3d_mean', 'Runoff_Q_3d_sum', 'Annual_Waterlogged_Days']
labels = ['Crop Year', '3-Day Rain (mm)', 'Peak 3-Day SSI', 'Peak 3-Day Runoff Q (mm)', 'Waterlogged Days (D)']

df_norm = df.copy()
min_max = {}
for col in cols:
    c_min = df[col].min()
    c_max = df[col].max()
    if c_max == c_min:
        df_norm[col] = 0.5
    else:
        df_norm[col] = (df[col] - c_min) / (c_max - c_min)
    min_max[col] = (c_min, c_max)

fig, ax = plt.subplots(figsize=(12, 6.5))

# Plot each row as a line
import matplotlib.cm as cm
colormap = cm.viridis
max_d = max(1, df['Annual_Waterlogged_Days'].max())

for idx, row in df_norm.iterrows():
    # Retrieve raw waterlogged days for coloring
    d_raw = df.loc[idx, 'Annual_Waterlogged_Days']
    color = colormap(d_raw / max_d)
    alpha = 0.15 + 0.65 * (d_raw / max_d)  # Highlight flood years (darker/more opaque)
    lw = 0.6 + 1.2 * (d_raw / max_d)
    ax.plot(range(len(cols)), [row[c] for c in cols], color=color, alpha=alpha, linewidth=lw)

# Draw vertical axes
for i in range(len(cols)):
    ax.axvline(i, color='#cbd5e1', linestyle='-', linewidth=1.2, zorder=1)

# Set axes properties
ax.set_xticks(range(len(cols)))
ax.set_xticklabels(labels, fontsize=10, fontweight='bold', color='#1e293b')
ax.set_xlim(-0.2, len(cols) - 0.8)
ax.set_ylim(-0.05, 1.05)

# Add min/max text labels to vertical axes
for i, col in enumerate(cols):
    c_min, c_max = min_max[col]
    if col == 'Crop_Year':
        ax.text(i, -0.04, f"{int(c_min)}", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#475569')
        ax.text(i, 1.04, f"{int(c_max)}", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#475569')
    elif col == 'Annual_Waterlogged_Days':
        ax.text(i, -0.04, f"{int(c_min)} days", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#475569')
        ax.text(i, 1.04, f"{int(c_max)} days", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#475569')
    else:
        ax.text(i, -0.04, f"{c_min:.1f}", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#475569')
        ax.text(i, 1.04, f"{c_max:.1f}", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#475569')

# Add Colorbar for Waterlogged Days
sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=0, vmax=max_d))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.03, aspect=25)
cbar.set_label('Seasonal Waterlogged Days (D)', fontsize=9.5, fontweight='bold', color='#1e293b', labelpad=10)
cbar.ax.tick_params(labelsize=8.5)

ax.set_title("Zambia Agricultural Flood Study — 25-Year Hydrological Event Fingerprint\n"
             "Parallel Coordinates Profile (Nov–Apr Season Peak Stress Dates)", 
             fontsize=13, fontweight='bold', color='#0f172a', pad=25)

# Clean up plot borders
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.get_yaxis().set_visible(False)

plt.tight_layout()
static_png_path = os.path.join(viz_folder, "Agri_Flood_Parallel_Coordinates_Fingerprint.png")
plt.savefig(static_png_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  ✅ Static Matplotlib plot saved: {static_png_path}")
print("\n🎉 Parallel coordinates visualization generation completed successfully!")
