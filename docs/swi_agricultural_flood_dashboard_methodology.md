This document provides a detailed, step-by-step explanation of the methodology and plotting mechanics behind `SWI_Ultimate_Flood_Dashboard.html`. This interactive dashboard is designed to visualize severe agricultural flooding (specifically long-term waterlogging) across maize-growing districts in Africa. 

**What Data Are We Using?**
We use two primary data sources:
* **Satellite Soil Moisture:** Daily Copernicus Soil Water Index (SWI at 0-10cm depth) covering 2007 to 2025. This tells us exactly how physically saturated the soil is on any given day.
* **Africa Maize Crop Calendar:** A shapefile dataset that provides the specific, localized Planting Day and Harvest Day for every individual district in Africa.

**How Do We Compute a "Flood Event"? (The Core Rules)**
To ensure we only capture flooding that actually destroys maize crops (via root hypoxia/rot), the script applies three strict filtering rules to the raw satellite data:

**Rule 1: The Crop Calendar Rule**
Flooding during the dry season or fallow period does not impact maize yields. Therefore, the script extracts the exact Planting Day and Harvest Day for each district. It throws away all satellite data outside of this window. We strictly monitor soil moisture *only* during the active growing season.

**Rule 2: The 95th Percentile Rule (The Threshold)**
Because soil types and baseline rainfall vary drastically across Africa, we cannot use a single flat threshold for the whole continent. Instead, the script calculates a historical 95th Percentile (P95) baseline independently for every single district. A day is only flagged as "flooded" if the soil moisture exceeds that specific district's local P95 threshold. 

**Rule 3: The 7-Day Duration Rule (The Streak)**
A brief 1-or-2 day puddle does not kill maize; roots need to be starved of oxygen for an extended period to suffer irreversible damage. The script groups consecutive "flooded" days into unbroken streaks. If a streak lasts for fewer than 7 consecutive days, the script throws it out entirely. 

**How is the Data Aggregated for Plotting?**
Once the rules above are applied, the script calculates the final math for each district per year. 

*Practical Example:* Imagine a district in the 2008 growing season. The soil moisture spikes above the P95 threshold three times:
* Streak A: Lasts 10 days
* Streak B: Lasts 4 days
* Streak C: Lasts 8 days

The script applies the 7-Day Rule and deletes Streak B. It then aggregates the surviving streaks (A and C) to compute three final metrics for that district in 2008:
* **Total Flood Days:** 18 days (10 + 8)
* **Number of Distinct Flood Events:** 2 events
* **Maximum Consecutive Flood Duration:** 10 days (Streak A was the longest uninterrupted flood)

**How is the Dashboard Plotted?**
The script takes those final aggregated metrics and uses them to render the two interactive plots on the dashboard:

**1. The Animated Choropleth Map (Panel A)**
This map visually plots the **Total Flood Days** metric. Every district is assigned a colour based on a fixed 0 to 30+ day scale (e.g., 0 days is clear, 30 days is dark blue). Because the scale is fixed, you can use the play button to animate the map through time (2007 to 2025) and watch the exact spatial footprint and severity of agricultural flooding expand and contract across the continent year by year.

**2. The District Spaghetti Plot (Panel B)**
This graph plots the historical trajectory of **Total Flood Days** over time for all districts simultaneously. 
* To keep the plot clean, any district that had 0 flood days in a given year is completely hidden from the graph for that year. 
* Any district that experienced a severe flood (at least one 7-day streak) is plotted and highlighted with a blue line. 
* By hovering over a specific spike on a blue line, you can instantly read exactly which district it is, how many total days it was flooded that year, and the length of its single longest streak.

By combining precise crop calendars with a rigorous >=7-day soil saturation threshold, this framework ensures that the dashboard plots only the true, yield-destroying instances of severe agricultural waterlogging.
