import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Setup paths
BASE_DIR = r"C:\\Users\\FlawiyaShirishMore\\OneDrive - Africa Specialty Risks Ltd\\ASR-Parametric_Research_Study\\Africa-Flood-Study"
DATA_CSV = os.path.join(BASE_DIR, r"output\\agricultural\\district_cluster_assignments_k3.csv")
MAP_IMG = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_maps\\kmeans_map_k3.png")
HTML_OUT_DIR = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_html")
os.makedirs(HTML_OUT_DIR, exist_ok=True)

# Load assignments
assign_df = pd.read_csv(DATA_CSV)

# Create a simple trajectory/cluster distribution plot (histogram)
hist_path = os.path.join(BASE_DIR, r"output\\agricultural\\cluster_maps\\k3_hist.png")
assign_df['cluster_k3'].value_counts().sort_index().plot(kind='bar')
plt.title('Cluster Distribution (k=3)')
plt.xlabel('Cluster')
plt.ylabel('Number of Districts')
plt.tight_layout()
plt.savefig(hist_path, dpi=300)
plt.close()

# Helper to write HTML
def write_html(filename, title, body_html):
    with open(os.path.join(HTML_OUT_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(f"<html><head><title>{title}</title></head><body>{body_html}</body></html>")

# Use absolute file URLs for images
map_path = MAP_IMG.replace('\\', '/')
map_url = f"file:///{map_path}"

hist_path_url = hist_path.replace('\\', '/')
hist_url = f"file:///{hist_path_url}"
hist_url = f"file:///{hist_path.replace('\\', '/')}"

# 1. Map HTML
map_body = f"<h1>K=3 Cluster Map</h1><img src='{map_url}' alt='K=3 Map' style='max-width:100%;height:auto;'>"
write_html('k3_map.html', 'K=3 Cluster Map', map_body)

# 2. Assignments HTML (show first 20 rows)
assign_table = assign_df.head(20).to_html(index=False)
assign_body = f"<h1>K=3 Cluster Assignments (first 20 rows)</h1>{assign_table}"
write_html('k3_assignments.html', 'K=3 Assignments', assign_body)

# 3. Trajectory/Histogram HTML
traj_body = f"<h1>K=3 Cluster Distribution (Trajectory Placeholder)</h1><img src='{hist_url}' alt='Cluster Histogram' style='max-width:100%;height:auto;'>"
write_html('k3_trajectory.html', 'K=3 Trajectory', traj_body)

print('HTML reports generated in', HTML_OUT_DIR)
