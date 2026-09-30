# Step-by-Step Derivation: Daily Agri Trigger Baseline Comparison Dashboard

This document provides a detailed, step-by-step explanation of how the data for the **Daily Agri Trigger Baseline Comparison Dashboard** (`Daily_Agri_Trigger_Baseline_Comparison.html`) was derived, calculated, and plotted.

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

### B. Non-parametric Standardized Soil Moisture Index (SSI)
* **Equation:**
  For each district and Day of Year (DOY) across all 25 years:
  1. Rank the historical values of $SM_{\text{root}}$ for that specific day of the year: $R$
  2. Compute empirical probability using the Gringorten plotting position:
     $$p = \frac{R - 0.44}{N + 0.12}$$
  3. Transform to standard normal anomalies:
     $$SSI = \Phi^{-1}(p)$$

### C. 7-Day Rolling Precipitation ($P_{7\text{d}}$)
* **Input Data:** Daily CHIRPS rainfall.
* **Equation:**
  $$P_{7\text{d}, t} = \sum_{i=0}^{6} \text{precipitation}_{t-i}$$

### D. Soil Conservation Service (SCS) Runoff ($Q$)
* **Parameters:** Curve Number $CN = 85$.
* **Equations:**
  1. Max Soil Water Retention ($S$):
     $$S = \frac{25400}{CN} - 254 = 45.41\text{ mm}$$
  2. Initial Abstraction ($I_a$):
     $$I_a = 0.2 \cdot S = 9.08\text{ mm}$$
  3. Runoff ($Q$):
     $$Q = \begin{cases} \frac{(P_{7\text{d}} - I_a)^2}{P_{7\text{d}} - I_a + S} & \text{if } P_{7\text{d}} > I_a \\ 0 & \text{if } P_{7\text{d}} \le I_a \end{cases}$$

---

## 2. Trigger Methodologies (Comparison Targets)

This dashboard evaluates and compares two distinct parametric trigger methodologies:

### Method A: Implemented Dual-Trigger (Physical Index)
* **Moderate trigger:** $SSI \ge 1.0$ AND $Runoff\_Q \ge 10\text{ mm}$.
* **Severe trigger:** $SSI \ge 1.5$ AND $Runoff\_Q \ge 20\text{ mm}$.
* **Physical Justification:** Ensures that both **saturation-excess** (wet soil, high SSI) and **precipitation inflow** (surface runoff, high $Q$) occur simultaneously to verify an agricultural flood disaster.

### Method B: Baseline GEE Statistical Trigger (PDF Method)
* **Trigger condition:**
  $$P_{7\text{d}} > 2 \cdot \sigma_{P_{7\text{d}}} \quad \text{AND} \quad Runoff\_Q > 0\text{ mm}$$
  Where $\sigma_{P_{7\text{d}}}$ is the historical standard deviation of the 7-day rolling precipitation for that day of the year.
* **Statistical Justification:** Focuses on statistical rainfall anomalies (deviations exceeding 2 standard deviations) to trigger payouts.

---

## 3. Selected Underwriter Case Studies

The dashboard focuses on three historical events to demonstrate how the policies behave in practice:
1. **Kapiri Mposhi (2007–2008 Crop Year):** A major wet year in central Zambia.
2. **Chibombo (2010–2011 Crop Year):** An intense, high-runoff season.
3. **Monze (2007–2008 Crop Year):** A southern province district showing prolonged soil saturation.

---

## 4. Plotting & Subplot Logic

For each of the three case studies, the dashboard renders an interactive dual-axis chart:
1. **X-Axis:** Crop calendar dates (November 1 to April 30).
2. **Left Y-Axis (Precipitation & Runoff):**
   * **Blue bars:** Daily precipitation in mm.
   * **Purple line:** Daily Runoff $Q$ in mm.
3. **Right Y-Axis (Soil Moisture SSI):**
   * **Green line:** Daily Gringorten SSI anomalies.
4. **Horizontal Reference Lines:**
   * **Dashed purple line:** Runoff thresholds (10 mm and 20 mm).
   * **Dashed green line:** SSI thresholds (1.0 and 1.5).
5. **Background Shaded Bands:**
   * **Orange/Red vertical bands:** Active days under the Implemented Dual-Trigger.
   * **Grey vertical bands:** Active days under the Baseline GEE Statistical Trigger.
   * **Overlapping bands:** Allow underwriters to see exactly when and where the two methods agree or disagree.
