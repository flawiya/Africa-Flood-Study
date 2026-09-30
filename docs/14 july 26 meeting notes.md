# Meeting Notes – July 14, 2026: Agricultural Flood Index Finalization

## Meeting Overview
- **Date:** July 14, 2026
- **Participants:** Speaker 1 (Risk Modeling & Pricing Specialist), Speaker 2 (Lead Research Scientist), Speaker 3 (Parametric Risk Analyst), Speaker 4 (Senior Reinsurance Underwriter)
- **Primary Objective:** Finalize the methodology for an agricultural flood index to assess crop damage and risk curves, comparable to existing drought and fire indices.

---

## Key Technical Discussions

### 1. Index Selection: SSI vs. SWI
* **SSI (Standardised Saturation Index):** The Risk Analyst noted that SSI shows fluctuations and captures water stagnation on the surface. She argued that crop damage starts earlier (at root suffocation) before surface stagnation is visible.
* **SWI (Soil Water Index):** The team compared the custom-calculated index (using ERA5 data) against the Copernicus (European Commission) standard.
* **Decision:** The team decided to proceed with the **SWI** (the "purple" index).
  * **Reasoning:** Both indices show similar dynamics, but the SWI is simpler to calculate, standardized globally, and updated regularly by Copernicus. It reduces the need for "ad-hoc" science in favor of engineering efficiency.

### 2. Methodology & Calculation
* **Root Zone Focus:** The analysis focuses on the top **0–28 cm** of soil.
* **Exponential Filtering:** The Risk Analyst explained the use of a recursive exponential filter with a **"10-day memory"** to smooth the data and simulate how moisture infiltrates the soil over time.
* **Thresholds:** The team discussed using a saturation threshold (e.g., **95% or 99% quantile**) to trigger a "flood day."

### 3. Defining Impact (Loss Curves)
* **Non-Binary Loss:** The Reinsurance Underwriter emphasized that crop loss is not binary (i.e., the plant doesn't just die on day 3). It is a gradient:
  * Example: 1–3 days = 10% loss; 11+ days = maximum loss.
* **Metric Consistency:** To ensure the flood index is comparable to the drought index ("Days of Drought"), the outcome will be measured as **"Consecutive Days of Flood."**
* **Aggregation:** The team needs to determine how to handle multiple events in a single year (e.g., a 3-day flood followed by a 10-day flood) and whether to sum them or treat them as separate intensity markers.

---

## Action Items

| Action Item | Responsible | Timeline |
| :--- | :---: | :---: |
| **Calculate Consecutive Days:** Use Copernicus SWI data to calculate consecutive flood days per year/district. | Risk Analyst | Before next meeting |
| **Develop Loss Formula:** Propose a curve/formula to convert "number of days" into "percentage of crop loss." | Risk Analyst / Underwriter | By Friday |
| **Schedule Follow-up:** Set a call for Thursday/Friday to agree on the final loss formula. | Lead Research Scientist | Immediate |
| **Risk Curve Generation:** Begin drawing risk curves for territories once the formula is finalized. | Risk Analyst | Post-Friday meeting |

---

## Notes on Data Constraints
* **Historical Data:** Copernicus SWI data is available from **2007 onwards**. While the project originally sought data back to 2000, the team agreed to proceed with 2007 for the sake of standardization and speed.
* **Crop Specificity:** The Pricing Specialist noted that percentage of loss is highly crop-specific; the team will use **corn as a proxy** for the general model for now.
