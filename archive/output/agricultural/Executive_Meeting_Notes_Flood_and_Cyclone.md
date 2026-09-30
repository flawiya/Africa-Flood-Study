# Executive Meeting Summary & Technical Action Items

---

## 📌 Executive Overview

This document summarizes key decisions, scientific justifications, methodology calibrations, and next technical deliverables discussed during the research review meeting. 

All content has been fully anonymized (removing all individual personal names and corporate entity references) for project documentation and archival.

---

## 🎯 Key Objectives

1. **Flood Model Threshold Calibration**:
   - Finalize the parametric flood trigger definition using the combined **Option 2** methodology: **95th Percentile ($P_{95}$) Soil Water Index + 85% Absolute Physical SWI Floor** on a **5-day continuous streak basis**.
   - Validate the reduction of the continuous streak requirement from 7 days down to 5 days across all 1,638 agricultural districts.

2. **Spatial Risk Regionalization**:
   - Establish regional risk clusters using a **60% Geographic Contiguity / 40% Weather Co-occurrence** weighting scheme.
   - Evaluate cluster stability across $K = 14, 15, 16$ zones using spatial Silhouette validation scores.

3. **Inter-District Correlation Pipeline**:
   - Compute intra-cluster (within-zone) and inter-cluster (cross-zone) correlation matrices for annual flood days to quantify portfolio risk diversification.

4. **Cyclone & Wind Speed Feasibility Study**:
   - Initiate technical pipeline development for wind speed and atmospheric pressure parameters using ERA5 hourly and historical cyclone best-track datasets.

---

## 💡 Key Results & Methodological Findings

### 1. 5-Day vs. 7-Day Continuous Streak Calibration
* **Metric Shift**: Reducing the minimum continuous streak parameter from 7 consecutive days to 5 consecutive days resulted in an **+8.27% increase in detected flood days** (+4,849 additional flood days across 3.2M observation records).
* **Ground-Truth Validation**:
  * 7-day continuous rules missed critical 3–5 day severe inundation events in semi-arid and tropical coastal jurisdictions (e.g., flash flood events and cyclone landfalls in South Africa, Senegal, Niger, Kenya, and Malawi).
  * 5-day continuous rules successfully captured these verified disaster events without introducing false positive triggers in humid zones (a 3-day rule was evaluated but discarded due to high false positive rates in rainforest/coastal zones).
* **Agronomic Validation**: Soil saturation ($SWI \ge 85\%$) sustained for 5 consecutive days induces root hypoxia/anoxia during vegetative and flowering maize stages, leading to irreversible 30–50% crop loss.

### 2. Spatial Risk Regionalization (Clustering)
* **Weighting Scheme**: Re-calibrated from a weather-dominated weighting to **60% Geographic Contiguity / 40% Weather Co-Movement** to align risk pools with physical river basins, topography (Digital Elevation Model), and agro-ecological zones.
* **Cluster Resolution**: While macro drought modeling utilizes 4 broad continental pools, flood regionalization requires higher spatial resolution ($K = 14–16$ clusters) due to localized hydrology, elevation gradients, and coastal dynamics.

### 3. Parametric Model Benchmark Evaluation
* **Option 1 (99th Percentile Relative)**: Over-triggers in dry/normal years; captures relative anomalies but fails to guarantee physical soil saturation.
* **Option 2 (95th Percentile + 85% Absolute SWI Floor - Selected Winner)**: Combines local historical rarity ($P_{95}$) with physical waterlogging floor ($\ge 85\%$ SWI), eliminating false triggers in semi-arid zones while capturing severe 5-day events.
* **Option 3 (Pure 85% Absolute SWI)**: Over-triggers in naturally wet coastal/swamp regions where soil moisture is permanently elevated.

---

## 📋 Outstanding Technical Action Items

### Task 1: Flood Pipeline Finalization
* [x] Re-run continuous streak algorithm under **Option 2 (P95 + 85% SWI) for 5-day streaks** across 2008–2024 (excluding edge years 2007 and 2025).
* [x] Generate matching side-by-side country spaghetti validation dashboards (Kenya, Malawi, Nigeria) highlighting verified disaster years with star markers.
* [x] Produce Pan-African 5-Day Average Annual Flood Days Map (`Average_Flood_Days_Map_5Day.html`).
* [ ] Complete intra-cluster vs. inter-cluster Spearman/Pearson correlation analysis for flood days across assigned risk zones.
* [ ] Export finalized master dataset and metadata to the shared parametric research repository.

### Task 2: Cyclone & Wind Parameter Research Pipeline
* [ ] **Data Extraction**: Process ERA5 Hourly dataset for 10-meter $u$-component of wind, $v$-component of wind, and mean sea-level pressure (`mean_sea_level_pressure`).
* [ ] **Wind Vector Computation**: Compute hourly wind speed magnitude:
  $$W = \sqrt{u^2 + v^2}$$
* [ ] **Track Integration**: Cross-reference wind speed time series with IBTrACS (International Best Track Archive for Climate Stewardship) cyclone track coordinates during historical landfall events (e.g., Cyclone Idai, Cyclone Freddy, Cyclone Ana).
* [ ] **Threshold Calibration**: Evaluate operational wind speed thresholds ($\ge 64 \text{ km/h}$ for tropical storm onset; $\ge 110–120 \text{ km/h}$ for severe agricultural structural/crop destruction).
* [ ] **Study Domain Definition**: Determine district selection strategy (coastal & cyclone-prone agricultural districts vs. full continental domain).

---

## 📁 Related Output Artifacts

* 🗺️ **[Average_Flood_Days_Map_5Day.html](output/agricultural/meeting_30th_july_output/Average_Flood_Days_Map_5Day.html)**
* 📈 **[Africa_Flood_InterDistrict_Correlation_Dashboard.html](output/agricultural/meeting_30th_july_output/Africa_Flood_InterDistrict_Correlation_Dashboard.html)**
* 🇲🇼 **[Malawi_5Day_Spaghetti_Validation_Dashboard.html](output/agricultural/meeting_30th_july_output/Malawi_5Day_Spaghetti_Validation_Dashboard.html)**
* 🇰🇪 **[Kenya_5Day_Spaghetti_Validation_Dashboard.html](output/agricultural/meeting_30th_july_output/Kenya_5Day_Spaghetti_Validation_Dashboard.html)**
* 🇳🇬 **[Nigeria_5Day_Spaghetti_Validation_Dashboard.html](output/agricultural/meeting_30th_july_output/Nigeria_5Day_Spaghetti_Validation_Dashboard.html)**
