# Correlation Matrix: Precipitation, SSI, Runoff, SWI, EM-DAT Trigger

This analysis uses the established agricultural trigger formula:
- Moderate: `SSI >= 1.0` AND `Runoff_Q_mm >= 10.0`
- Severe: `SSI >= 1.5` AND `Runoff_Q_mm >= 20.0`

Rows used for correlation: **36,604**

| Variable | Precipitation (mm) | Soil Moisture SSI | ERA5 Runoff 7d (mm) | SWI T=40 | Trigger Strength | EM-DAT Event Active |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Precipitation (mm)** | 1.000 | 0.410 | 0.264 | 0.291 | 0.271 | 0.051 |
| **Soil Moisture SSI** | 0.410 | 1.000 | 0.543 | 0.760 | 0.518 | 0.196 |
| **ERA5 Runoff 7d (mm)** | 0.264 | 0.543 | 1.000 | 0.537 | 0.745 | 0.372 |
| **SWI T=40** | 0.291 | 0.760 | 0.537 | 1.000 | 0.378 | 0.267 |
| **Trigger Strength** | 0.271 | 0.518 | 0.745 | 0.378 | 1.000 | 0.285 |
| **EM-DAT Event Active** | 0.051 | 0.196 | 0.372 | 0.267 | 0.285 | 1.000 |