# Walkthrough — 70-District Daily Saturation Trigger Dashboard

This walkthrough summarizes the implementation and features of the compiled 70-district spatial mapping and timeseries dashboard, including final UI adjustments.

## Dashboard Summary
The generated dashboard provides a self-contained, interactive web interface to explore daily Gringorten Soil Moisture SSI, SCS Curve Number surface runoff depth ($Q$), and dual-severity parametric flood triggers across **all 70 agricultural districts in Zambia** for **all 25 years (2000–2025)** of crop seasons.

👉 **[Zambia_70_Agri_Trigger_Dashboard.html](output/visualizations/Zambia_70_Agri_Trigger_Dashboard.html)**

---

## Technical Details & UI Features

### 1. Spatial Map Locked to Severe Trigger Days
* The Map Metric selection dropdown has been removed from the control panel.
* The interactive choropleth map **only displays and colors districts based on Severe Trigger Days** (SSI $\ge 1.5$ AND $Q \ge 20\text{ mm}$, color-coded in Dark Red).
* Timeseries charts for the selected district still show both Moderate and Severe information.

### 2. Horizontal Year Slider Control
* Moving the range slider dynamically updates the active Crop Calendar Year text (e.g. `2011 - 2012`) and dynamically refreshes the map and plots in real time.

### 3. Detailed Subplots Spacing & Alignment
* Margins and standoff offsets are set to prevent overlapping:
  * **Panel 1 (SSI):** mapped to `xaxis` / `yaxis`.
  * **Panel 2 (Runoff Q):** mapped to `xaxis2` / `yaxis2`.
  * **Panel 3 (Trigger bars):** mapped to `xaxis3` / `yaxis3` (Moderate is orange, Severe is dark red).
  * Axis title standoffs are configured to push titles away from tick labels.
  * Date labels are rotated $-30^\circ$ and thinned to ensure they are fully readable.

---

## File Deliverables

### [NEW] [plot_agri_70_districts_dashboard.py](visualisations/plot_agri_70_districts_dashboard.py)
* Python script that reads shapefiles, simplifies boundaries, processes daily datasets, and compiles the standalone HTML dashboard.

### [NEW] [Zambia_70_Agri_Trigger_Dashboard.html](output/visualizations/Zambia_70_Agri_Trigger_Dashboard.html)
* Standalone dashboard containing the methodology header card, control selectors, year slider, choropleth map, and 3-panel dynamic timeline subplots.
