# Step-by-Step Derivation: EM-DAT Validation Comparison Dashboard

This document provides a detailed, step-by-step explanation of how the data for the **EM-DAT Validation Comparison Dashboard** (`EMDAT_Validation_Comparison.html`) was derived, calculated, and plotted.

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

## 2. EM-DAT Disaster Mapping

To validate these indices, historical disasters from the EM-DAT database are mapped to the daily grid:

### Step 1: Date Crossover Correction
If an EM-DAT record is missing a start month, it defaults to November (the start of the Zambian crop season). If the event ends in the early months of the next calendar year (e.g., February), the start year is adjusted to $Year - 1$ to align with the correct crop calendar window.

### Step 2: District Association
The affected regions listed in the EM-DAT database are mapped to our 70 districts using:
1. **GADM Admin JSON Parsing:** Matches standard level-2 name attributes.
2. **Province Aggregation:** If a whole province is listed, all districts belonging to that province are mapped as affected.
3. **Regex Text Searching:** Searches the raw free-text location description in EM-DAT for matches against the names of our 70 districts.

---

## 3. Daily Grid Matching & Classification

Once both datasets are compiled, they are aligned on a daily district-level grid of **329,761 rows** (70 districts $\times$ 25 years $\times$ 181 crop days/year).

For each day, the active trigger status is compared against EM-DAT:
* **In_EMDAT_Event (Target):** `True` if the date is within an EM-DAT event window and the district is listed as affected.
* **Trigger_Moderate (Prediction):** `True` if $SSI \ge 1.0$ AND $Q \ge 10\text{ mm}$.
* **Trigger_Severe (Prediction):** `True` if $SSI \ge 1.5$ AND $Q \ge 20\text{ mm}$.

From this grid, the classification metrics are computed:
* **True Positive (TP):** Trigger is active on a day when EM-DAT records a disaster.
* **False Positive (FP):** Trigger is active on a day when EM-DAT records no disaster.
* **False Negative (FN):** Trigger is inactive on a day when EM-DAT records a disaster.
* **True Negative (TN):** Trigger is inactive on a day when EM-DAT records no disaster.

### Underwriting Calculations:
* **Sensitivity (Recall):** $\frac{TP}{TP + FN}$ (ability of the policy to pay out during documented disasters).
* **Precision (PPV):** $\frac{TP}{TP + FP}$ (proportion of triggered days that correspond to documented national disasters).
* **Daily-Level Accuracy:** $\frac{TP + TN}{TP + TN + FP + FN}$ (overall correctness of the daily trigger states).

---

## 4. Plotting Logic

The timeline plot aggregates these daily district-level rows:
1. **X-Axis:** Continuous daily timeline from 2000-11-01 to 2025-04-30 (Nov–Apr segments).
2. **Y-Axis:** Number of active triggered districts (0 to 70).
3. **Lines:**
   * **Orange line:** Daily count of districts where the Moderate trigger is active.
   * **Red line:** Daily count of districts where the Severe trigger is active.
4. **Shaded Grey Bands:** Represent the EM-DAT disaster active windows. Hovering over a band displays the event number, location, and total affected population.
