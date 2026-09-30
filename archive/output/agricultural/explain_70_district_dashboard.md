# Step-by-Step Derivation: Zambia 70 Agri District Dashboard

This document provides a detailed, step-by-step explanation of how the data for the **Zambia 70 Agricultural District Dashboard** (`Zambia_70_Agri_Trigger_Dashboard.html`) was derived, calculated, and plotted.

---

## 1. Underlying Physical Calculations

For each day in the crop growing season (November 1 to April 30) across all 70 agricultural districts over 25 years (2000–2025), the following indices are calculated:

### A. Root-Zone Soil Moisture ($SM_{\text{root}}$)
* **Input Data:** ERA5-Land daily volumetric soil water layers:
  * Layer 1 ($SM_{0-7\text{cm}}$)
  * Layer 2 ($SM_{7-28\text{cm}}$)
  * Layer 3 ($SM_{28-100\text{cm}}$)
* **Equation:**
  $$SM_{\text{root}} = 0.07 \cdot SM_{0-7\text{cm}} + 0.21 \cdot SM_{7-28\text{cm}} + 0.72 \cdot SM_{28-100\text{cm}}$$
* **Justification:** Weights are proportional to the physical depth of each soil layer to represent the root-zone reservoir of maize crops (1 meter).

### B. Non-parametric Standardized Soil Moisture Index (SSI)
* **Equation:**
  For each district and Day of Year (DOY) across all 25 years:
  1. Rank the historical values of $SM_{\text{root}}$ for that specific day of the year: $R$
  2. Compute empirical probability using the Gringorten plotting position:
     $$p = \frac{R - 0.44}{N + 0.12}$$
  3. Transform to standard normal anomalies:
     $$SSI = \Phi^{-1}(p)$$
* **Justification & Reference:** Gringorten (1963) plotting position provides the most unbiased probability distribution estimates for hydrological extremes.

### C. 7-Day Rolling Precipitation ($P_{7\text{d}}$)
* **Input Data:** Daily CHIRPS rainfall.
* **Equation:**
  $$P_{7\text{d}, t} = \sum_{i=0}^{6} \text{precipitation}_{t-i}$$

### D. Soil Conservation Service (SCS) Runoff ($Q$)
* **Parameters:** Curve Number $CN = 85$ (representing average agricultural soils and crop covers in Zambia).
* **Equations:**
  1. Max Soil Water Retention ($S$):
     $$S = \frac{25400}{CN} - 254 = 45.41\text{ mm}$$
  2. Initial Abstraction ($I_a$, moisture threshold before surface runoff begins):
     $$I_a = 0.2 \cdot S = 9.08\text{ mm}$$
  3. Runoff ($Q$):
     $$Q = \begin{cases} \frac{(P_{7\text{d}} - I_a)^2}{P_{7\text{d}} - I_a + S} & \text{if } P_{7\text{d}} > I_a \\ 0 & \text{if } P_{7\text{d}} \le I_a \end{cases}$$
* **Justification & Reference:** USDA Soil Conservation Service National Engineering Handbook, Section 4. Represents rain-induced surface runoff accumulation over a rolling 7-day period.

---

## 2. Trigger Rule Classification

The daily data is classified into three trigger states:
* **Trigger_Severe (Red):** $SSI \ge 1.5$ AND $Q \ge 20\text{ mm}$.
* **Trigger_Moderate (Orange):** $SSI \ge 1.0$ AND $Q \ge 10\text{ mm}$ (and not Severe).
* **Normal (Grey):** Any other condition.

---

## 3. Dashboard Structure & Interactive Plotting

The dashboard is structured into three main interactive sections:

### A. Step-by-Step Spatial Choropleth Map (Left Panel)
1. **Shapefile Processing:**
   * Loads the district shapefile `Zambia_agri_districts.shp` containing the spatial boundaries of the 70 agricultural zones.
   * Simplifies the geometries using a tolerance factor ($0.005$ degrees) to compress the output GeoJSON size.
2. **Frequency Aggregation:**
   * Groups the daily timeseries by `District_Upper` and counts the total number of days each trigger rule was active.
3. **Map Rendering:**
   * Plots the district shapes using `choropleth_mapbox` in Plotly.js.
   * Shading intensity corresponds to the historical trigger frequency of the selected trigger method.

### B. Daily Crop-Season Timeseries Plot (Right Panel)
1. **District & Crop-Year Selection:**
   * Dropdowns allow the user to select any of the 70 districts and any crop year (e.g., 2007).
2. **Subplots:**
   * **Top Subplot (Soil Moisture SSI):** Plots the daily SSI anomaly (blue line) against the historical daily climatological mean (dashed line).
   * **Bottom Subplot (Runoff Q):** Plots the daily Runoff $Q$ in mm (purple line) against the historical daily climatological mean (dashed line).
3. **Trigger Band Overlays:**
   * Semi-transparent vertical background bands are drawn:
     * **Orange bands:** Days when the Moderate trigger condition is met.
     * **Red bands:** Days when the Severe trigger condition is met.

### C. Annual Peak Trigger Stats (Bottom Panel)
Renders a summary table listing the crop years sorted by the maximum daily runoff and peak soil moisture index reached during that season.
