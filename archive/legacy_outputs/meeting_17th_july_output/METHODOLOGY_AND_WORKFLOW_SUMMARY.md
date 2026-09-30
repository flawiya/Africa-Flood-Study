# 📖 SWI Parametric Flood Study: End-to-End Methodological & Scientific Blueprint

This document provides a comprehensive, step-by-step scientific and technical explanation of the entire SWI Parametric Agricultural Flood workflow. It covers **what** data was acquired, **why** specific spatial and satellite choices were made, **how** metrics were computed, **why** threshold calibration strategies were evaluated, and **how** visual dashboards were constructed.

---

## 1. Direct Raw Satellite Values vs. Area-Weighted Values

### How `swi_t10_raw` is computed:
When `rasterstats.zonal_stats(district_polygon, raster, stats=['mean'])` runs, it identifies **ALL** satellite grid pixels whose area intersects or touches the district polygon boundary, and calculates their simple unweighted mathematical average:
$$\text{swi\_t10\_raw} = \frac{\text{Pixel}_1 + \text{Pixel}_2 + \dots + \text{Pixel}_N}{N}$$

### Difference between raw and mean (area-weighted):
* **`swi_t10_raw`:** Every intersecting pixel is given an equal weight of $1.0$, even if a boundary pixel only has 5% of its area inside the polygon.
* **`swi_t10_mean` (`exactextract`):** Every pixel is weighted by its exact polygon-pixel overlap fraction (e.g., $0.05$ weight for 5% overlap vs. $1.0$ weight for 100% overlap).

---

## 2. Scientific Insight: The 2013 P99 Trigger Paradox Explained

### Why Option 1 (P99) Triggers in 2013, while Option 2 & Option 3 Do Not
* **Option 1 (99th Percentile) evaluates RELATIVE local extremes:**
  * Option 1 compares daily SWI to each district's historical 99th percentile (P99) with no absolute floor.
  * In semi-arid or naturally dry districts (such as **Sidi Kacem** in Morocco or **Shiselweni** in Eswatini), soil moisture is naturally low. Sidi Kacem's P99 threshold is only **51.62%**!
  * During a 2013 rainstorm, Sidi Kacem reached **56.90%** SWI for $>7$ consecutive days. Because $56.90\% \ge P99\ (51.62\%)$, **Option 1 (P99) TRIGGERS!**
* **Option 2 & Option 3 require AN ABSOLUTE CAP OF SWI $\ge 85\%$:**
  * Option 2 and 3 demand that the soil reach actual physical waterlogging ($\ge 85\%$).
  * Since Sidi Kacem reached only **56.90%** (which is $<85\%$), **Option 2 and Option 3 DO NOT TRIGGER!**

### Empirical Case Study Table (2013 Flood Events):

| District Name | Region Type | P95 Percentile | P99 Percentile | 2013 Max SWI | Option 1 (P99) Trigger? | Option 2 & 3 (SWI $\ge 85\%$) Trigger? | Scientific Cause |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sidi Kacem (Morocco)** | Dry / Semi-Arid | 40.47% | **51.62%** | **56.90%** | **YES** | ❌ **NO** | 56.9% exceeds P99 (51.6%), but is far below absolute waterlogging (85%). |
| **Shiselweni (Eswatini)** | Sub-Humid | 72.76% | **77.17%** | **82.26%** | **YES** | ❌ **NO** | 82.2% exceeds P99 (77.1%), but fails the 85% absolute cap. |

---

## 3. Scientific Rationale: Absolute Threshold Selection (Fixed at 85%)

### Why 85% is the Constant Absolute Threshold for Parametric Triggers
* **Physical Soil Saturation:** At 85% Soil Water Index (SWI), soil macro-pores collapse, soil oxygen is depleted (anoxia/hypoxia), and crop roots begin suffocating, causing severe root rot and crop failure.
* **District Spatial Averaging:**
  * A district polygon (e.g., 5,000 $\text{km}^2$) contains both low-lying agricultural valleys/river basins and higher-elevation hills/slopes.
  * During a major cyclonic flood, agricultural lowlands become **100% submerged under standing water**, while higher slopes maintain lower moisture. The **district-wide average** SWI evaluates to **~85%**.
* **Conclusion:** Keeping the absolute threshold constant at **85%** ensures cyclonic floods and severe lowland submergence are cleanly captured without being muted by terrain.

---

## 4. Data Acquisition & 18-Year Daily Completeness (Morocco & All Africa)

### 100% Daily Coverage Across All 18 Years (2007–2025)
* For **all 33 Moroccan districts** and **all other 1,638 maize-growing districts across Africa** (1,671 total active districts), we extracted Copernicus satellite data for **every single day of all 18 years (2007 to 2025)** during their in-season growing calendars.
* Total master dataset size: **2,562,919 clean daily rows** with 0 missing values.
* From this complete 2.56M daily dataset, we evaluated the 7-consecutive-day streaks and generated all HTML dashboards and CSV summaries.

### A. The Satellite Source: Copernicus Global Land SWI (V3 12.5km)
* **What it is:** The Soil Water Index (SWI 0–100%) produced by Copernicus / EUMETSAT, derived from ASCAT radar scatterometers on MetOp satellites.
* **Why SWI over Rainfall (CHIRPS/ERA5):** Radar scatterometers directly measure root-zone soil moisture ($0–100\%$) and penetrate cloud cover during heavy rain/monsoon events.

### B. Engineering Architecture: Local-Drive First & TURBO Downloader
* Writes to `C:\Users\FlawiyaShirishMore\swi_temp_processing\` to bypass Windows/OneDrive file locking (`OSError Errno 22`) and syncs to OneDrive automatically.

---

## 5. July 17th Meeting Requirements: The 3 Exact Options Tested

### Calibration Results for the 3 Meeting Options ($\ge 7$ Consecutive Days)

| Meeting Option | Exact Rule & Threshold Definition | Mean Days / Year | Median Days / Year | 90th %ile (1-in-10 Yr Bad Season) | 95th %ile (1-in-20 Yr Severe Season) | 99th %ile (1-in-100 Yr Catastrophe) | Absolute Max Days |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Option 1: 99th Percentile** | `swi_t10_mean >= P99` (Pure relative percentile, no absolute floor) for $\ge 7$ consec days | **0.41** | 0.0 | 0.0 | 0.0 | **12.0 days** | **22 days** |
| **Option 2: 95th %ile + Absolute 85%** | `swi_t10_mean >= P95` **AND** `swi_t10_mean >= 85%` for $\ge 7$ consec days | **1.32** | 0.0 | 0.0 | **11.0 days** | **28.0 days** | **65 days** |
| **Option 3: Pure Absolute 85%** | `swi_t10_mean >= 85%` (Pure absolute soil waterlogging) for $\ge 7$ consec days | **4.43** | 0.0 | **18.0 days** | **30.0 days** | **58.0 days** | **113 days** |

### Column Definitions Explained:
* **Mean Days / Year:** The average number of flood days triggered per district per crop year across all 18 years (2007–2025).
  * *Option 1 (0.41 days/year):* Average of ~0.4 days per district each year (~4 flood days per decade).
  * *Option 2 (1.32 days/year):* Average of ~1.3 days per district each year (~13 flood days per decade).
  * *Option 3 (4.43 days/year):* Average of ~4.4 days per district each year (~44 flood days per decade).
* **Median Days / Year (0.0):** In 50% or more of normal years, a district experiences 0 flood days.
* **90th Percentile (1-in-10 Year Bad Season):** The flood days triggered during a 1-in-10 year bad flood season.
* **95th Percentile (1-in-20 Year Severe Season):** The flood days triggered during a 1-in-20 year severe flood season.
* **99th Percentile (1-in-100 Year Catastrophe):** The flood days triggered during a 1-in-100 year extreme catastrophe.
* **Absolute Max Days:** The single highest number of flood days recorded in any single district in any single year across all 18 years.

---

## 6. Visual Dashboard Architecture: Dual-Panel (Map + Spaghetti Plot)

* **Panel A — Animated Mapbox Map:** Interactive time-series map with a fixed 0–25 day color scale across all 18 years.
* **Panel B — District Spaghetti Plot:** Plots all district historical time series simultaneously, highlighting affected districts and showing regional average trendlines.

---

## 7. Directory File Index (`meeting_17th_july_output`)

📁 `OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\meeting_17th_july_output\`

### CSV Data Summaries:
* **Calibration Master Table:** `output/agricultural/meeting_17th_july_output/meeting_17th_july_calibration_summary.csv`
* **Option 1 Summary CSV:** `output/agricultural/meeting_17th_july_output/option1_99th_percentile_summary.csv`
* **Option 2 Summary CSV:** `output/agricultural/meeting_17th_july_output/option2_95th_plus_absolute_summary.csv`
* **Option 3 Summary CSV:** `output/agricultural/meeting_17th_july_output/option3_pure_absolute_summary.csv`

### Interactive Dual-Panel HTML Dashboards (Map + Spaghetti Plot):
* **Option 1 Dashboard:** `output/agricultural/meeting_17th_july_output/Option1_99th_Percentile_Dashboard.html`
* **Option 2 Dashboard:** `Option2_95th_plus_Absolute_Dashboard.html`
* **Option 3 Dashboard:** `Option3_Pure_Absolute_Dashboard.html`
