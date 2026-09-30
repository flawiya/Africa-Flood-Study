# Walkthrough — 70-District Dashboard & EM-DAT Flood Trigger Validation

This walkthrough summarizes the implementation of the 70-district saturation trigger dashboard and the correlation analysis comparing our daily parametric agricultural flood triggers against the EM-DAT (International Disaster Database) historical disaster logs.

---

## 1. Standalone 70-District Interactive Dashboard
The dashboard provides a self-contained, offline-capable interface to visualize spatial flood anomalies and daily district-level timeseries across **all 70 agricultural districts in Zambia** for **all 25 crop years (2000–2025)**.

👉 **[Zambia_70_Agri_Trigger_Dashboard.html](output/visualizations/Zambia_70_Agri_Trigger_Dashboard.html)**

### Key Features:
* **Horizontal Year Slider:** Slide to cycle crop calendar years and instantly update spatial mapping and charts.
* **Locked Severe Map View:** The spatial map displays and colors districts exclusively by the number of **Severe Trigger Days** ($SSI \ge 1.5$ AND $Q \ge 20\text{ mm}$, color-coded in Dark Red).
* **Detailed Timeseries Subplots:** Clicking a district on the map displays its three dedicated daily subplots (SSI vs Climatology baseline, Curve Number Runoff $Q$ vs baseline, and dual-severity Trigger status bars) without overlap.

---

## 2. EM-DAT Historical Flood Validation & Visualization
We built an evaluation pipeline and visualization timeline to correlate our daily trigger catalog against historical EM-DAT flood disaster records for Zambia.

👉 **[EMDAT_Validation_Comparison.html](output/visualizations/EMDAT_Validation_Comparison.html)**  
📄 **[emdat_validation_report.md](output/emdat_validation_report.md)**

### Validation Results Summary:
* **Event-Level Capture (Recall):**
  * **Moderate Trigger:** **82.6%** capture rate (19 out of 23 historical events captured).
  * **Severe Trigger:** **65.2%** capture rate (15 out of 23 historical events captured).
* **Daily-Level Classification Accuracy:**
  * **Moderate Trigger:** **74.8%** overall daily accuracy.
  * **Severe Trigger:** **87.1%** overall daily accuracy.
* **Timeline Visualization:**
  * Overlays daily count of active trigger districts in Zambia (2000–2025) as a timeline curve with **semi-transparent vertical bands** representing the documented EM-DAT disasters.
  * Spikes in the curves match the position of the shaded bands, indicating strong historical correlation. Hovering over a band displays full disaster details (e.g. location, total affected).
* **Pearson Correlation Matrix Heatmap:**
  * Calculates daily-level correlation coefficients ($r$) between the core physical variables: Soil Moisture SSI, SCS Runoff $Q$, and EM-DAT Event Active.
  * Renders an interactive **$3 \times 3$ Heatmap Plot** in the dashboard, showing positive and statistically significant correlation values ($r = 0.165$ for SSI vs. EM-DAT, $r = 0.112$ for Runoff vs. EM-DAT).

---

## 3. Alternative Validation: Relaxed Runoff Trigger Analysis (Q > 0)
As a parametric sensitivity study, we compiled a separate validation comparing a relaxed runoff threshold ($Q > 0\text{ mm}$) with the standard trigger thresholds ($Q \ge 10\text{ / }20\text{ mm}$).

📄 **[emdat_relaxed_validation_report.md](output/emdat_relaxed_validation_report.md)**

### Sensitivity Findings:
* **Capture Rates Unchanged:** Relaxing runoff to $Q > 0$ resulted in **exactly the same capture rates** (Moderate remains **82.6%**; Severe remains **65.2%**). Real disasters already feature heavy runoff that exceeds $10\text{ mm}$ or $20\text{ mm}$.
* **Increase in False Positives:** Setting the threshold to $Q > 0$ increases daily False Positives by **4,028 days** for the Severe trigger and **2,131 days** for the Moderate trigger, showing that the standard runoff thresholds are vital for filtering out false alarms.

---

## 4. Added Files

### [NEW] [validate_emdat_correlation.py](script/visualisations/validate_emdat_correlation.py)
* Python script that reads the EM-DAT custom request sheet, maps GADM level-2 and level-1 admin locations, filters timeseries dates, and computes classification statistics.

### [NEW] [test_relaxed_trigger_validation.py](script/visualisations/test_relaxed_trigger_validation.py)
* Python script that calculates trigger validation under relaxed runoff conditions ($Q > 0$) and writes the comparison report.

### [NEW] [plot_emdat_validation.py](script/visualisations/plot_emdat_validation.py)
* Python script that builds the interactive validation timeline HTML chart comparing trigger spikes and EM-DAT windows.

### [NEW] [emdat_validation_report.md](output/emdat_validation_report.md)
* Markdown report displaying the event-level match table, daily classification counts, sensitivity/precision metrics, and correlation coefficients.

### [NEW] [emdat_relaxed_validation_report.md](output/emdat_relaxed_validation_report.md)
* Markdown report comparing standard triggers vs. relaxed triggers.
