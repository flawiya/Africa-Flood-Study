# Technical Plan: Copernicus Soil Water Index (SWI) Integration

This document outlines the specifications, resolutions, scaling solutions, and mathematical reconstruction required to integrate the **Copernicus Daily Soil Water Index (SWI)** into the Zambia parametric flood trigger model.

---

## 1. Dataset Specifications & Resolution

* **Product Identifier:** Daily Soil Water Index Global 12.5km V4 (CGLS SWI V4)
* **Spatial Resolution:** 0.1° grid cells (approximately 12.5 km x 12.5 km).
* **Temporal Resolution:** Daily (2007 – present).
* **Sensor Origin:** Derived from active radar backscatter (ASCAT on MetOp satellites).
* **Input Soil Depth:** It utilizes **Surface Soil Moisture (SSM)** as input, which represents the top **0–5 cm** of the soil profile. 
  * *ERA5 Mapping:* In our custom ERA5-Land model, we use the **`soil_0_7cm`** (first layer) as the corresponding daily surface input.
* **Vertical Resolution (T-Values):** 
  Rather than standard physical depths (e.g. 10cm), it uses **characteristic time lengths (T-values)**: `T = 1, 5, 10, 15, 20, 40, 60, 100` representing the infiltration time. For agricultural water logging, **`T=40`** or **`T=60`** are used.

---

## 2. Handling the 12.5 km Spatial Resolution for Small Districts

Since a 12.5 km pixel size (0.1°) is coarse, some small agricultural districts in Zambia might only intersect a few pixels. To resolve this:

1. **Area-Weighted Zonal Aggregation (Spatial Intersection):**
   When extracting the grid values using our district shapefile (`Zambia_agri_districts.shp`), we calculate the **area-weighted mean** of all intersecting pixels. If a district covers 30% of Pixel A and 70% of Pixel B, the daily value is computed as:
   $$\text{Value} = 0.3 \times \text{Pixel}_A + 0.7 \times \text{Pixel}_B$$
   This prevents edge artifacts and handles small districts smoothly.
2. **Copernicus SWI 1km Africa Product (Alternative):**
   Copernicus also provides a **1km Soil Water Index (SWI1km) for Africa** (combining Sentinel-1 SAR and ASCAT radar). While it provides excellent spatial resolution for small districts, Sentinel-1 data only begins in **2014**. For long-term historical comparisons (2000–present), the 12.5km version remains the baseline.

---

## 3. Reconstructing SWI for the 2000–2006 Data Gap (Same Scale & Method)

The Copernicus SWI product starts in **2007**. To compute it in the **same way** for the **2000–2006** gap, we run the recursive exponential filter on ERA5 daily surface soil moisture (`soil_0_7cm`). 

To match the actual Copernicus SWI scale, we must account for unit differences:
* **Copernicus SWI** is in **Relative Saturation (0% to 100%)** relative to wilting point and field capacity.
* **ERA5-Land `soil_0_7cm`** is in **Volumetric Water Content ($m^3/m^3$)**, typically ranging from ~0.10 to ~0.45.

### Normalization and Filter Pipeline:
1. **Locate District Extremes:** Find the minimum ($SSM_{min}$) and maximum ($SSM_{max}$) observed volumetric soil moisture (`soil_0_7cm`) for each district over the 26-year record.
2. **Normalize daily values (0 to 100%):**
   $$SSM_{rel}(t) = \frac{SSM(t) - SSM_{min}}{SSM_{max} - SSM_{min}} \times 100$$
3. **Apply the Wagner/Albergel Recursive Filter:**
   $$SWI_T(t) = SWI_T(t-1) + K(t) \cdot [SSM_{rel}(t) - SWI_T(t-1)]$$
   where the gain factor $K(t)$ is:
   $$K(t) = \frac{K(t-1)}{K(t-1) + e^{-1/T}}, \quad K(1) = 1.0, \quad SWI_T(1) = SSM_{rel}(1)$$

This output will range from **0% to 100%**, matching the physical scale and behavior of the post-2007 Copernicus SWI product.

---

## 4. Extraction & Validation Strategy (Three Target Focus)

We focus our daily baseline validation on the **3 target districts** where historical flood events occurred (noting that the target years differ by district):
* 📍 **Kapiri Mposhi** (2007–2008 Crop Year)
* 📍 **Chibombo** (2011–2012 Crop Year)
* 📍 **Monze** (2007–2008 Crop Year)

### Action Steps:
1. **Download Daily SWI (2007–2025):** Download the daily Copernicus SWI V4 (T=40) data for **all Zambia agricultural districts** (for long-term scalability) via Sentinel Hub or CDSE API.
2. **Run Custom normalized SWI (2000–2025):** Run our normalized exponential filter script to compute custom SWI values for the 3 target districts (and all others).
3. **Validate Overlap (2007–2025):** Plot the custom SWI alongside the actual Copernicus SWI for the 3 target districts during the overlapping years to verify the correlation and calibrate the parameter $T$ (e.g. testing $T=20$ vs. $T=40$).
4. **Compare against EMDAT:** Check if the custom normalized SWI captures the water-logging events during the 2000–2006 gap.
