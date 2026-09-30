Trigger Formulas and Data Processing
====================================

This document describes the formulas, thresholds, and processing steps used
by the Triple Lock trigger implementation (SSI + Runoff + SWI), and explains
how the key variables are computed and plotted.

1) Trigger definitions
----------------------
- Moderate trigger:
  - SSI > 1.0
  - Runoff_Q_mm > 10.0 (7-day cumulative ERA5 total_runoff_mm)
  - swi_040 > 25.0 (Copernicus SWI T=40, percent or SWI units as provided)

- Severe trigger:
  - SSI > 1.5
  - Runoff_Q_mm > 20.0 (7-day cumulative)
  - swi_040 > 33.0

- Trigger encoding:
  - `Trigger_Moderate` and `Trigger_Severe` are boolean columns.
  - `Trigger_Int` is an integer encoding: 2 = Severe, 1 = Moderate, 0 = None.

2) SSI (Standardised Soil-moisture Index)
-----------------------------------------
- Source variable: `soil_7_28cm` (ERA5 volumetric soil moisture for the 7–28 cm layer).
- Method:
  1. For each district, rank `soil_7_28cm` values using average ranks.
  2. Compute Gringorten plotting position: `pp = (rank - 0.44) / (count + 0.12)`.
  3. Clip `pp` into (1e-6, 1-1e-6) to avoid infinite values.
  4. Convert to standard normal quantile: `SSI = norm.ppf(pp)` using `scipy.stats.norm`.
- Notes: This produces an SSI that is approximately N(0,1) per-district distribution.

3) SWI (Soil Water Index)
-------------------------
- Source: Copernicus SWI T=40 product (CSV: `Zambia_SWI_Maize_200708_201112.csv`).
- Variable used: `swi_040` (T=40 layer) representing soil water index values per district-date.
- Processing: loaded and merged by district/date; in some scripts a district-level saturation percentage
  is computed relative to the local maximum SWI for the period (for saturation-based triggers).
- Thresholds above use the SWI values directly (`swi_040 > 25`, `swi_040 > 33`).

4) Precipitation (CHIRPS)
--------------------------
- Source: CHIRPS daily precipitation master (`precipitation`).
- Derived variable used: `P_7d` — 7-day rolling sum of daily precipitation.
  - Implementation notes: in dashboards typically calculated with `groupby('District')` and
    `.transform(lambda x: x.rolling(7, min_periods=7).sum())` (requires full 7-day window for climatology)
    or `min_periods=1` where partial windows are acceptable for continuity.

5) Runoff (ERA5 total_runoff_mm)
--------------------------------
- Source: ERA5-Land per-district `total_runoff_mm` (daily values from GEE export).
- Derived variable: `Runoff_Q_mm` — 7-day rolling sum of `total_runoff_mm` grouped by district.
  - Implementation: `df.groupby('District')['total_runoff_mm'].transform(lambda x: x.rolling(7, min_periods=1).sum())`.
  - The scripts generally use `min_periods=1` for continuity; some climatology contexts set `min_periods=7`.

6) Correlation and plotting
---------------------------
- Correlation matrices:
  - Variables: precipitation, `SSI`, `Runoff_Q_mm`, `swi_040`, `Trigger_Int`, `In_EMDAT_Event_Int`.
  - Method: select complete rows (`.dropna()` on selected columns) and compute Pearson correlation with `df.corr()`.
  - Outputs: CSV, PNG heatmap, and markdown report.

- EM-DAT validation dashboards:
  - Process: map EM-DAT events to district lists and date ranges, create `In_EMDAT_Event` boolean per district-day,
    compute trigger flags, then produce an HTML dashboard (Plotly) with:
    - Time series of daily active district counts for Moderate/Severe triggers (lines),
    - EM-DAT event bands rendered as semi-transparent rectangles (`shapes` overlay),
    - Correlation table and confusion matrices.

7) Notes and caveats
--------------------
- The SWI product covers 2007–2011 in the maize-specific CSV; validation scripts merge SWI as a left join
  and may contain NaNs outside that period. Trigger logic that depends on SWI must account for missing SWI data.
- Thresholds are strict `>` comparisons to match your requested semantics (e.g., `SSI > 1.0`).
- Where historic thresholds (percentile-based runoff thresholds) are used in other scripts, those are left unchanged unless explicitly requested.

8) Where to find the code
-------------------------
- Primary scripts that implement these variables and triggers:
  - `script/agricultural/Zambia_SSI_7_28cm_Trigger_Model_SSI1_5_Runoff20_SWI30.py` (SSI computation + model CSV output)
  - `script/agricultural/plot_emdat_validation_era5_ssi7_28cm_triple_lock.py` (EM-DAT validation HTML dashboard)
  - `script/agricultural/correlation_precip_ssi_runoff_swi_emdat_trigger_triple_lock.py` (correlation and reports)

If you want, I can also insert this documentation text as docstrings at the top of each script (recommended) and run the three scripts to produce updated reports. Let me know if you want `min_periods` adjusted to `7` for `P_7d`/`Runoff_Q_mm` calculations for stricter windows.