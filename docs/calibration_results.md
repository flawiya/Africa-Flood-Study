# Flood Index Calibration Results

We ran three distinct threshold scenarios across the full historical dataset (2007–2025) using the 7-consecutive-day rule. 

Here are the results for each scenario:

### 1. Scenario: 99th Percentile (P99)
* **Threshold:** Soil Water Index (SWI) > 99th Percentile
* **Result:** **SUCCESS**
* **Global Maximum:** The absolute worst-case "bad year" across any district in Africa capped out at **39 days** of flooding.
* **Average Severe Flood:** When a severe flood does occur under this threshold, the average duration is exactly **11.7 days**.
* **Conclusion:** This threshold scales the outputs down perfectly. It aligns exactly with the team's target of a historically bad year causing 10–20 days of flooding on average.

### 2. Scenario: 95th Percentile + Absolute 80
* **Threshold:** SWI > 95th Percentile **AND** SWI > 80.0
* **Result:** **FAILED** (0 floods detected globally)
* **Conclusion:** This threshold is physically impossible for the dataset. The Copernicus SWI_010 satellite product does not output values close to 80 for maize-growing regions. The absolute maximum SWI value recorded in the entire 18-year dataset is **49.1**.

### 3. Scenario: Strict Absolute 85
* **Threshold:** SWI > 85.0
* **Result:** **FAILED** (0 floods detected globally)
* **Conclusion:** For the same reason as Scenario 2, an absolute threshold of 85 is physically impossible. If we wish to use an absolute threshold in the future, we must test values around **40 to 45**.

---
*Note: Morocco has been successfully mapped into the dataset and processed alongside the other districts.*
