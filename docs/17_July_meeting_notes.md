# Meeting Notes: SWI Flood Index Calibration

**Date:** July 18, 2026

## Key Discussion Points

* **Current Threshold Sensitivity:** The team noted that the current P95 threshold is too sensitive. P95 inherently flags 5% of all days as flooded (approx. 1 in 20 days), which accumulates to unrealistic numbers (e.g., 100 flood days in a 6-month season).
* **Defining a "Bad Year":** A realistically severe "bad year" for crop damage should only register roughly **10 to 20 days of flooding** over the season. Anything significantly higher than this is physically impossible/resilient.
* **Scaling Exercise:** The current goal is a scaling exercise rather than completely rewriting the science. We need to tighten the threshold (e.g., moving from 95th to 99th percentile, or applying absolute thresholds) to scale the outputs down to realistic limits.
* **Morocco Use-Case:** Morocco was discussed as a good visual sanity-check because it did not experience floods in the last 5 years, but had a notable event around Dec 2025 / Jan 2026. *(Note: Morocco is currently excluded from the dashboard because it is not in the underlying Maize Crop Calendar shapefile).*

## Action Items / Next Steps
Based on post-meeting feedback, the following steps will be executed to tune the index:
1. **Modify Thresholds:** Play with combinations of percentiles, consecutive days, and absolute values. Specifically test:
   * 99th Percentile
   * 95th Percentile + Absolute Threshold
   * Only Absolute Threshold
2. **Target Outcome:** Calibrate the thresholds to ensure floods do not happen every year, aiming for a maximum of ~15 days per year during a bad year.
3. **Expand Crop Calendar:** Manually supplement the missing crop calendar data for other key districts (e.g., Morocco) based on publicly available agricultural data so they can be included in the analysis.
