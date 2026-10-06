# Africa Parametric Flood Risk Study

> **Module**: `Africa-Flood-Study`  
> **Project**: Multi-Peril Parametric Insurance Research Study  
> **Target Region**: All 54 African Countries (1,671 Administrative Districts)  
> **Primary Peril**: Dual-Regime Pluvial Flash Flood & Agricultural Waterlogging Saturation  
> **Status**: Production & Handover Ready  

---

## 📌 1. Overview & Objective

The **Africa Parametric Flood Risk Study** establishes a continental-scale parametric flood insurance trigger engine designed to automate rapid post-disaster payouts for reinsurers and agricultural policyholders.

### Key Methodological Pillars:
1. **Copernicus Global Land Service SWI V3 (1 km Daily Resolution)**: Advanced ASCAT C-band active scatterometer radar measuring surface topsoil ($T=10$) and root-zone moisture ($T=40$).
2. **Dual-Regime Architecture**: Distinguishes between Urban Pluvial Flash Floods ($P_{24h} \ge P_{95}$ on $>10\%$ Impervious Surface Area) and Agricultural Saturation Floods.
3. **Calibrated 5-Day Continuous Streak Rule**: Resolves semi-arid flash flood under-reporting ($SWI \ge 85\% + P_{95}$ sustained for 5 consecutive days), capturing $+8.27\%$ additional verified flood days and $+25.87\%$ discrete catastrophe events without false positives.
4. **Machine Learning Spatial Risk Regionalization**: Agglomerative clustering with $60\%$ Geography / $40\%$ Weather weighting into 15–16 homogeneous risk pools.

---

## 📂 2. Repository Directory Structure

```
Africa-Flood-Study/
├── core_analysis/                                # Production Python analysis engines
│   ├── run_option2_5day_flood_analysis.py        # Production 5-day continuous SWI engine
│   ├── run_option2_7day_flood_analysis.py        # Legacy 7-day comparative engine
│   ├── run_clustering_60geo_40wx.py              # ML risk regionalization engine
│   ├── run_correlation_map_dashboards.py         # Inter-district correlation dashboards
│   └── run_cluster_trajectories.py               # Annual cluster trajectory generator
├── data/                                         # District shapefiles & crop calendars
│   └── africa_agricultural_domain_maize_calendar.shp # Domain boundaries & planting/harvest dates
├── docs/                                         # Technical documentation & guides
│   ├── FLOOD_PARAMETRIC_METHODOLOGY_GUIDE.md     # Formal Technical Guide
│   ├── METHODOLOGY_AND_PRESENTATION_NOTES.md     # Presentation slides & derivation notes
│   └── Pan_African_Option2_5Day_Flood_Validation_Registry.md # EM-DAT & PDNA event registry
├── outputs/                                      # Dashboards & analysis CSVs
│   ├── Average_Flood_Days_Map_5Day.html          # Pan-African 5-day interactive map
│   ├── Africa_Flood_Correlation_Map_60geo_40wx.html # Leaflet click-to-correlate dashboard
│   ├── Option2_5Day_vs_7Day_Comparison.csv       # Country-level statistical comparison
│   └── Option2_5Day_vs_7Day_District_Comparison.csv # District-level comparison table
└── README.md                                     # This Execution & Handover Guide
```

---

## 🚀 3. Pipeline Execution Sequence

```bash
# 1. Run Production Option 2 (5-Day Continuous SWI) Flood Analysis across all 1,671 districts
python core_analysis/run_option2_5day_flood_analysis.py

# 2. Run Spatial Risk Regionalization (60% Geography / 40% Weather Clustering at K=14, 15, 16)
python core_analysis/run_clustering_60geo_40wx.py

# 3. Generate Inter-District Correlation Dashboards & Leaflet Interactive Maps
python core_analysis/run_correlation_map_dashboards.py

# 4. Generate Risk Cluster Annual Trajectory Plots (2008–2024)
python core_analysis/run_cluster_trajectories.py
```

---

## 📖 4. Reference Documentation

- 📘 [FLOOD_PARAMETRIC_METHODOLOGY_GUIDE.md](docs/FLOOD_PARAMETRIC_METHODOLOGY_GUIDE.md)
- 📋 [METHODOLOGY_AND_PRESENTATION_NOTES.md](docs/METHODOLOGY_AND_PRESENTATION_NOTES.md)
