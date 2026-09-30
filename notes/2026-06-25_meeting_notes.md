# Meeting Notes – 25 June

**Participants:** Speaker 1, Speaker 2

## Objectives
- Define visualisations for agricultural flood analysis.
- Agree on data sources and index calculations.
- Outline next steps for implementation.

## Key Discussion Points & Decisions
1. **Precipitation Visualisation**
   - Create a **7‑day cumulative precipitation** bar plot.
   - Bars **red** when precipitation > **mean + 2 σ** for that 7‑day window.
2. **Runoff Visualisation**
   - Keep the existing runoff plot unchanged.
3. **Agriculture Drought Index**
   - Apply the agreed formula to compute an **agriculture drought index**.
   - Show days classified as *agriculture drought* on a separate graph.
4. **SSI Comparison**
   - Retain the current **3‑day mean SSI** plot for comparison.
5. **Scope**
   - All visualisations should be generated **only for years/locations that experienced a flood**.

## Action Items / Tasks
- **Task 1:** Update `visualisations/plot_agri_daily_dashboard.py` to implement the 7‑day cumulative precipitation bar plot with the red‑over‑threshold colouring.
- **Task 2:** Verify that the runoff plot in `visualisations/plot_agri_daily_dashboard.py` (or related script) remains unchanged.
- **Task 3:** Implement the agriculture drought index calculation in `script/Zambia_Agri_Runoff_SCS.py` (or appropriate pipeline) and generate the third graph displaying days classified as drought.
- **Task 4:** Ensure `visualisations/plot_daily_ssi.py` continues to display the 3‑day mean SSI for the comparison graph.
- **Task 5:** Filter all visualisations to include **only flood‑affected years/locations**.

## Data Sources Referenced
- FAO dataset: <https://data.apps.fao.org/catalog/dataset/cc0ebca9-0df9-4061-a338-6ffec9e9acb4>
- World Bank Climate Knowledge Portal (Zambia natural disasters): <https://climateknowledgeportal.worldbank.org/country/zambia/natural-disasters-historical>

## Next Steps
- Complete the script updates and regenerate the four graphs.
- Review the generated visualisations with the team.
- Share the updated outputs by **Monday**.

*Prepared on 25 June 2026.*
