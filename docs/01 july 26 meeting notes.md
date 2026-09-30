# Meeting Notes: July 1st, 2026
**Topic:** Parametric Agricultural Flood Models & Thesis Review  
**Participants:** Speaker 1 (Lead Researcher), Speaker 2 (Co-Researcher), Speaker 3 (Data Analyst / Researcher)

---

## 1. Meeting Objectives
* Evaluate the current daily trigger baseline comparison dashboard.
* Distinguish the physical mechanisms and impacts of **Water Logging** vs. **Flooding** on crops.
* Discuss validation triggers and anomalies in Soil Moisture (SSI), Runoff, and Precipitation.
* Review and align the scientific scope of the researcher's academic thesis on drought trajectories.

---

## 2. Key Discussion Points

### A. Soil Moisture Capping & Water Logging Physics
* **Physical Cap:** Speaker 1 emphasized that soil moisture is a physical index that should hit a local saturation "cap" (determined by soil composition, e.g., sand vs. clay). Once moisture exceeds this cap, waterlogging occurs, removing oxygen from the root zone and killing the plant within 72 hours in early growth stages.
* **SSI vs. Physical Moisture:** Speaker 2 noted that the Standardized Soil Moisture Index (SSI) is statistical (an anomaly index) rather than a physical index, which is why it doesn't show a physical cap and rarely exceeds a value of 2.0.
* **Action:** Compare precipitation and its moving sums (e.g., 5-day rolling sum) directly against raw physical soil moisture to locate and define these local saturation caps.

### B. Copernicus Soil Water Index (SWI) Integration
* **SWI Reference:** Speaker 1 suggested comparing the current model against the **Copernicus Soil Water Index (SWI)** (specifically the [Daily Soil Water Index Global 12.5km V4](https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-global-12-5km-v4)), which is the reference standard in Europe. It is radar-based, and though resolution in Africa varies, it provides a direct physical measure of soil water content.
* **Action:** Add a daily Soil Water Index (SWI) trace to the existing comparison graphs to observe physical correlations.

### C. Critique of Climatological Mean Thresholds (DOY)
* **DOY Fluctuations:** Speaker 1 questioned why small daily rainfall bars were triggering in red during the initial weeks of the season. Speaker 3 explained that the threshold was comparing each daily precipitation value to the historical 25-year mean for that exact day of the year. The team agreed that comparing daily values is not physically sound and that 7-day cumulative precipitation should be plotted and compared instead.
* **Physical Impact:** Speaker 1 pointed out that a 40mm rainfall event has the same physical water-logging impact whether it occurs in winter or summer; comparing it to a daily mean introduces seasonal artifact triggers.
* **Action:** 
  1. **[Completed]** Update the daily baseline comparison dashboards (`ERA5_Daily_Agri_Trigger_Baseline_Comparison.html` and the Optimized version) to plot the 7-day rolling cumulative precipitation and calculate the `Mean + 2 Std Dev` threshold based on this 7-day rolling sum instead of daily rainfall.
  2. Smooth the historical mean threshold using a moving window (e.g., 30 days before and after the day of interest) to remove high daily fluctuations, or focus on absolute physical limits.

### D. Crop Growth Stage Integration
* **Stage Vulnerability:** Speaker 3 highlighted that crop vulnerability changes over the crop calendar. A 5cm water level will drown a seedling in 72 hours but will not harm a fully grown crop later in the production stage.
* **Action:** Restrict trigger evaluations or adjust thresholds based on crop calendar months (e.g., focusing on early vegetative stages in the first 1-2 months).

### E. Thesis Scope Alignment
* **Critique of Thesis Scope:** Speaker 1 felt the title *"Understanding the Temporal Trajectories in Drought Incidents"* sounded fancy but was scientifically vague.
* **Mitigation Recommendation Pitfalls:** Speaker 1 cautioned against focusing too much on policy/recommendations for drought mitigation (noting it has been done thousands of times without success). 
* **Focus:** Recommended aligning the thesis strictly around core technical strengths—**data wrangling, statistics, and visualization**—which will yield a more rigorous scientific thesis.

---

## 3. Action Items & Changes

| Task / Change Description | Responsible | Priority | Status |
| :--- | :---: | :---: | :---: |
| **Direct Soil Moisture Analysis:** Plot raw soil moisture against precipitation sums to identify physical saturation caps across districts. | Data Analyst | High | Pending |
| **Copernicus SWI Comparison:** Obtain Copernicus SWI daily data for validation zones and plot it alongside the existing triggers. | Data Analyst | Medium | Pending |
| **Threshold Smoothing:** Update the daily baseline scripts to use a smoothed 30-day moving window for climatology thresholds. | Data Analyst | High | Pending |
| **Thesis Title & Scope Update:** Reframe the thesis objectives to focus on spatial-temporal data clustering and validation, narrowing down policy chapters. | Data Analyst | Medium | Pending |
