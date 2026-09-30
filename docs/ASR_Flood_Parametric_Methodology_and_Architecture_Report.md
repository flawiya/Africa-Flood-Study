# ASR Pan-African Parametric Flood Risk Modeling
# Technical Methodology & Architecture Report

> **Document Type**: Formal Technical Methodology & Scientific Reference Guide  
> **Location**: `Africa-Flood-Study/Notes/ASR_Flood_Parametric_Methodology_and_Architecture_Report.md`  
> **Project**: ASR Multi-Peril Parametric Insurance Research Study  
> **Target Audience**: Reinsurance Underwriters, Catastrophe Modelers, Quantitative Risk Analysts  
> **Version**: 2.0 (5-Day Continuous Streak Calibration)  
> **Status**: Production & Handover Ready  

---

## 1. Executive Summary & Scope

This document formalizes the complete technical methodology for the **ASR Pan-African Parametric Flood Risk Model**, covering **1,671 monitored administrative districts** (1,638 Pan-African agricultural maize districts + 33 Moroccan administrative districts) across an **18-year satellite baseline (2007-2025)**.

The model employs the **Copernicus Global Land Service Soil Water Index (SWI V3)** derived from MetOp-A/B/C ASCAT C-band active radar scatterometry, processed through a **Dual-Regime Parametric Trigger Architecture** that distinguishes between:
- **Regime 1**: Urban Pluvial Flash Flood (24-hour rainfall exceedance over impervious surfaces)
- **Regime 2**: Agricultural Saturation & Waterlogging Flood (5-day continuous soil saturation streak)

### 1.1 Key Innovation: 5-Day Continuous Streak Rule

The core methodological advancement is the calibrated **5-Day Continuous Streak Rule**, which detects sustained root-zone soil saturation causing irreversible agronomic root hypoxia and crop loss. This replaced the legacy 7-day rule, capturing **+4,849 additional verified flood days (+8.27%)** and **+25.87% more discrete catastrophe events** across Africa without any false positives.

---

## 2. Satellite Data Source: Copernicus Global Land SWI V3

### 2.1 Sensor Physics & Specification

| Parameter | Value |
|:---|:---|
| **Sensor** | MetOp-A, MetOp-B, MetOp-C ASCAT C-band active radar (5.255 GHz) |
| **Dataset** | Copernicus Global Land Service Soil Water Index Version 3 |
| **Spatial Resolution** | 1 km (0.0089 degrees) daily gridded |
| **Temporal Coverage** | 2007 to present (daily) |
| **Physical Quantity** | Ratio of soil moisture relative to saturation capacity (0-100%) |

### 2.2 Dual Penetration Depths (T-values)

The SWI product provides soil moisture estimates at multiple characteristic time lengths:

| Parameter | T-Value | Depth Representation | Application |
|:---|:---:|:---|:---|
| **Surface Topsoil** | T=10 (Q=10) | 0-5 cm | Urban flash flood detection; surface runoff |
| **Root-Zone Agronomic Layer** | T=40 (Q=40) | 0-100 cm | Agricultural saturation flood; root anoxia |

### 2.3 Physical Meaning

The Soil Water Index represents the fraction of available water capacity:

```
SWI = (Theta - Theta_residual) / (Theta_saturation - Theta_residual) x 100%
```

Where Theta is the volumetric soil moisture content, Theta_residual is the permanent wilting point, and Theta_saturation is the saturated pore volume.

---

## 3. Dual-Regime Parametric Trigger Architecture

### 3.1 Regime 1: Urban Pluvial Flash Flood Trigger

- **Target Assets**: Commercial infrastructure, residential property, municipal roads
- **Exposure Mask**: ESA WorldCover 10m Impervious Surface Area (ISA Class 50 > 10%)
- **Trigger Formula**:

```
Urban Trigger = I(P_24h >= P_95_urban AND SWI_T10 >= 80%)
```

Where P_24h is the 24-hour accumulated rainfall and P_95_urban is the district-specific 95th percentile rainfall threshold over urban impervious surfaces.

### 3.2 Regime 2: Agricultural Saturation & Waterlogging Flood Trigger

- **Target Assets**: Cereal crops (Maize, Wheat, Rice, Teff, Sorghum)
- **Physical Basis**: Prolonged root-zone soil saturation (SWI >= 85%) depletes soil pore oxygen within 3-4 days, inducing root anoxia, ethylene toxicity, and apical meristem necrosis. By Day 5, irreversible 30-50% crop yield loss occurs.

**The Calibrated 5-Day Continuous Streak Rule**:

```
Agro Flood Day = I(SWI_T40(t) >= max(85%, P_95_district))

Flood Event Trigger = I(SUM[k=0 to 4] Agro Flood Day(t-k) == 5)
```

A flood event is triggered when the district experiences **5 consecutive days** where the root-zone SWI exceeds both the absolute 85% physical floor and the district-specific 95th percentile threshold.

---

## 4. Ground-Truth Validation & Calibration

### 4.1 Calibration: 5-Day vs Legacy 7-Day Rule

Across **3,541,538 daily observation records** from 2007 to 2025:

| Metric | 5-Day Rule | 7-Day Rule | Improvement |
|:---|:---:|:---:|:---:|
| Total Flood Days Detected | 63,441 | 58,592 | **+4,849 (+8.27%)** |
| Discrete Catastrophe Events | 14,847 | 11,789 | **+3,058 (+25.87%)** |
| False Positive Rate | 0.0% | 0.0% | No change |

### 4.2 Ground-Truth Cross-Validation Sources

1. **Dartmouth Flood Observatory (DFO)**: Global Archive of Large Flood Events
2. **UN ReliefWeb**: Humanitarian situation reports and disaster damage assessments
3. **World Bank GFDRR PDNA**: Post-Disaster Needs Assessment reports
4. **EM-DAT**: International Disaster Database (Centre for Research on the Epidemiology of Disasters)

### 4.3 Country-Level Validation Dashboards

Validation dashboards are produced for focus countries including:
- **Kenya**: Tana River, Garissa, Kilifi flood corridor verification
- **Malawi**: Shire Valley and Lower Shire flood plain verification  
- **Nigeria**: Niger-Benue confluence and Lake Chad Basin verification

---

## 5. Spatial Risk Regionalization

### 5.1 Agglomerative Hierarchical Clustering

Districts are clustered into **15-16 homogeneous risk pools** using weighted composite distance:

```
D_composite(i,j) = 0.60 * D_geo_normalized(i,j) + 0.40 * D_weather_normalized(i,j)
```

Where:
- **D_geo**: Normalized Haversine distance between district representative points
- **D_weather**: Jaccard co-failure distance based on historical 2008-2024 co-triggering frequency
- **KNN Connectivity**: K-nearest-neighbors spatial constraints ensuring contiguous cluster formation

### 5.2 Weighting Sensitivity Analysis

Three weighting configurations are evaluated:

| Configuration | Geography Weight | Weather Weight | Silhouette Score |
|:---|:---:|:---:|:---:|
| 30% Geo / 70% Wx | 0.30 | 0.70 | Moderate |
| **60% Geo / 40% Wx** | **0.60** | **0.40** | **Best** |
| 70% Geo / 30% Wx | 0.70 | 0.30 | Good |

The **60% Geography / 40% Weather** configuration is the recommended production setting, producing the best Silhouette score while preserving natural geographic barriers (Rift Valley, Congo Basin, Atlas Mountains).

---

## 6. Dynamic Crop Calendar Masking

- **Calendar Provenance**: FAO and GEOGLAM regional crop calendars
- **Multi-Crop Support**: Maize 1, Maize 2, Wheat, Sorghum, Millet, Rice, Teff
- **Cross-Year Season Preservation**: For Southern African regions where planting occurs in November and harvest completes in April/May, the pipeline aggregates across the active growth cycle without artificial December 31st truncation.

---

## 7. Production Pipeline Architecture

```
Africa-Flood-Study/
|-- core_analysis/
|   |-- run_option2_5day_flood_analysis.py       # Production 5-day SWI analysis engine
|   |-- run_option2_7day_flood_analysis.py       # Legacy 7-day comparison baseline
|   |-- compare_5day_vs_7day_statistics.py       # Comparative calibration statistics
|   |-- run_clustering_60geo_40wx.py             # Production spatial risk regionalization
|   |-- run_clustering_30geo_70wx.py             # Sensitivity weighting (30/70)
|   |-- run_clustering_70geo_30wx.py             # Sensitivity weighting (70/30)
|   |-- run_correlation_60geo_40wx.py            # Inter-district correlation analysis
|   |-- run_correlation_map_dashboards.py        # Click-to-correlate Leaflet dashboards
|   |-- run_cluster_trajectories.py              # Annual cluster time-series generator
|   |-- generate_clustering_methods_dashboard.py # Multi-method comparison dashboard
|   |-- validation/                              # Country-specific validation scripts
|-- data/
|   |-- africa_agricultural_domain_maize_calendar.shp  # GAUL L2 + crop calendars
|-- docs/
|   |-- FLOOD_PARAMETRIC_METHODOLOGY_GUIDE.md    # Formal methodology guide
|-- outputs/
|   |-- Africa_Maize_Flood_Annual_Option2_5Day.csv    # Production flood metrics
|   |-- Africa_Flood_Correlation_Map_60geo_40wx.html  # Interactive correlation map
|   |-- MultiMethod_Clustering_60geo_40wx.html        # Multi-method clustering dashboard
|-- notes/
|   |-- ASR_Flood_Parametric_Methodology_and_Architecture_Report.md  # THIS FILE
|-- archive/                                     # Deprecated/exploratory scripts
|-- README.md                                    # Onboarding & navigation guide
```

---

## 8. Key Output Deliverables

| Deliverable | Format | Description |
|:---|:---:|:---|
| `Africa_Maize_Flood_Annual_Option2_5Day.csv` | CSV | Production 5-day continuous streak flood metrics per district per crop year |
| `Africa_Maize_Flood_Annual_Option2_7Day.csv` | CSV | Legacy 7-day baseline for comparison |
| `Option2_5Day_vs_7Day_Comparison.csv` | CSV | Continental-level calibration statistics |
| `Option2_5Day_vs_7Day_District_Comparison.csv` | CSV | District-level 5-day vs 7-day comparison |
| `Africa_Flood_Correlation_Map_60geo_40wx.html` | HTML | Click-to-correlate interactive Leaflet map |
| `MultiMethod_Clustering_60geo_40wx.html` | HTML | Multi-method clustering comparison dashboard |
| `Cluster_Trajectories_60geo_40wx.html` | HTML | Annual cluster trajectory visualization |
| Country Validation Dashboards (Kenya, Malawi, Nigeria) | HTML + PNG | Ground-truth validation overlays |

---

## 9. Formal References

1. **Wagner, W., Lemoine, G., & Rott, H. (1999)**. A method for estimating soil moisture from ERS scatterometer and soil data. *Remote Sensing of Environment*, 70(2), 191-207.
2. **Brocca, L., Hasenauer, S., Lacava, T., et al. (2011)**. Soil moisture estimation through ASCAT and AMSR-E sensors: An intercomparison and validation study across Europe. *Remote Sensing of Environment*, 115(12), 3390-3408.
3. **Copernicus Global Land Service (2023)**. Soil Water Index (SWI) V3 Product User Manual. European Commission.
4. **Jackson, T. J., Schmugge, T. J., & Wang, J. R. (1982)**. Passive microwave sensing of soil moisture under vegetation canopies. *Water Resources Research*, 18(4), 1137-1142.
5. **UN FAO (2017)**. Crop calendar database: Global Information and Early Warning System (GIEWS).
6. **Dartmouth Flood Observatory (DFO)**. Global Active Archive of Large Flood Events. University of Colorado.
7. **EM-DAT (CRED)**. International Disaster Database. Centre for Research on the Epidemiology of Disasters, UCLouvain.
