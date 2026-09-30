
1. Strategic Objective

"To develop a dual-regime parametric flood risk model for Zambia that
distinguishes between Urban Flash Flooding (Intensity-driven) and Agricultural
Saturation Flooding (Accumulation-driven) using high-resolution satellite data
and 30-year historical baselines."

2. Supervisory Tasks & Requirements

  - Core Requirements:
    1.  Simplicity vs. Complexity: Compare a "Simple" approach (Rainfall
        Percentiles) with a "Complex" approach (SCS Curve Number/Physics).
    2.  Value at Risk: Don't just map concrete; identify Economic/Industrial
        Hubs (Mining, Tourism, Trade).
    3.  Ground Truth: Validate identified triggers against historical news and
        disaster records (EM-DAT).
  - Core Requirements:
    1.  Pilot Study: Prove the pipeline in Zambia before scaling to the African
        continent.
    2.  Visual Proof: Provide clear, step-by-step visualizations of the data
        stratification.
    3.  Crop Calendars: Ensure agricultural floods are only triggered during
        growing seasons.

3. Scientific Formulas

Regime A: Urban Flood (Pluvial)

  - Trigger Logic: Rainfall Intensity over Impervious Surfaces.
  - Simple Formula: P_{24h} > P_{95} (24-hour rain exceeds the historical 95th
    percentile).
  - Complex Formula:
    Flood_{Urban} = \{1 \text{ if } P_{24h} > P_{95} \text{ AND } ISA > 10\%\}
      - ISA: Impervious Surface Area (ESA Class 50).

Regime B: Agricultural Flood (Rural)

  - Trigger Logic: Accumulation and Saturation (The "Full Sponge").
  - Runoff Depth (Q): Q = \frac{(P - I_a)^2}{(P - I_a + S)}
      - P: 7-day cumulative rainfall.
      - S: Max Soil Retention (25400 / CN - 254).
      - I_a: Initial Abstraction (0.2 \times S).
  - Agri Trigger: \sum P_{7d} > (2 \times \sigma) + \mu (7-day rain > 200% of
    mean) AND Q > 0 (Soil is saturated).

4. Study Mind Map (Cascade Diagram)

This diagram flows from the inputs required to the results expected by ASR.

[INPUTS] │ ├── Satellite Data: CHIRPS (Rain), ESA WorldCover (Land use), GLDAS
(Soil Moisture). ├── Admin Data: GADM Level 2 (District boundaries). └──
Economic Data: Mining Hubs, Border Trade Posts, Tourism Centers (Livingstone). │
[REQUIREMENTS / STRATIFICATION] │ ├── Urban Mask: Built-up > 10% OR
Economic/Industrial Hub designation. └── Agri Mask: Built-up < 10% AND Cropland
> 3.29% (Zambia's Top 70 Agri Districts). │ [PROCESSING / ANALYSIS] │ ├──
Baseline (Urban): Calculate 30-year P_{95} daily thresholds. ├── Baseline
(Agri): Calculate weekly means and Soil Retention (S) capacity. └── Event Scan:
Identify dates where Inflow (P) > Loss (I_a + S). │ [OUTPUTS / RESULTS] │ ├──
Stratification Map: Visual proof of where each model applies. ├── Trigger
Catalog: List of historical dates/districts where flood criteria were met. └──
Validation Report: Correlation between model triggers and "Ground Truth"
disaster records. │ [EXPECTED OUTCOME] │ └── Parametric Index: A scientifically
defensible tool for ASR to automate flood insurance payouts in Zambia.

5. Summary of Progress (For your Meeting)

  - Objective 1 (Identification): COMPLETE.
      - You have stratified Zambia into 12 Urban/Economic Districts and 70
        Agricultural Districts.
      - You have separate Shapefiles and a Dual-Regime Map.
  - Objective 2 (Baselines): IN PROGRESS.
      - You have standardized the 25-year CHIRPS dataset.
      - You have calculated the P_{95} Intensity Triggers for the 12 Urban Hubs.
  - Objective 3 (The "Next Step"): UPCOMING.
      - Run the Saturation/SCS Runoff analysis for the Agricultural group.
      - Cross-reference dates with EM-DAT historical flood records.

- Add visualization for each step to understand the steps.
- output shoudl be in light theme no dark therem shoudl be used. 
- **CRITICAL RULE (Crop Calendar):** Always strictly adhere to the Crop Calendar (Harvest Year) for temporal aggregations, NEVER the standard Gregorian Calendar Year. Floods and streaks that span across New Year's Eve (e.g., Nov to Mar seasons) must never be mathematically or visually split. The `crop_year` logic must dynamically shift late-year dates (>= planting) forward to align with the upcoming Harvest Year, ensuring valid cross-year streaks remain unified in all dataset aggregations and visualizations.