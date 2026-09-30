# Flood Index Methodology Update

## Dual-Metric SWI Extraction Logic

**Justification for Methodology:**
The 12.5km spatial resolution of the Metop ASCAT sensor can lead to 'signal dilution' when averaging across large agricultural districts. To mitigate this, our pipeline extracts the District Max in addition to the Area-Weighted Mean. 

Following the 'Variable Contributing Area' theory (Beven & Kirkby, 1979), we define flood potential based on the saturation of these localized peak areas reaching the 80% physical threshold (Brocca et al., 2010), rather than the regional average.

## Pipeline Architecture
1. **Area-Weighted Mean:** Calculates the exact fraction of each 12.5km pixel falling inside the district to prevent small districts from being overshadowed by surrounding non-agricultural land.
2. **District Max (>10% Overlap):** Identifies the maximum saturation value among all pixels overlapping the district, successfully capturing the localized "flood signal" that would otherwise be hidden by the regional mean.
3. **Simple Unweighted Average:** Retained for backward compatibility with previous analysis outputs.
