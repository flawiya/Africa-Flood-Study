# Comparative Analysis: Daily Confusion Matrices (Zambia Parametric Flood triggers vs. EM-DAT)

This report evaluates the daily district-day classification performance of five different parametric flood trigger configurations against historical EM-DAT flood disaster records across **33,515 daily district-day observations** (2000–2025).

---

## 1. Summary Comparison Table

Evaluating models at a daily level represents a strict validation (with no date buffers). It tells us how accurately the triggers capture the precise days and locations where disasters occurred.

### Moderate Trigger Levels

| Model Configuration | True Positive (TP) | False Positive (FP) | False Negative (FN) | True Negative (TN) | Accuracy | Precision | Daily Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Precipitation Only (CHIRPS)** | 92 | 2,708 | 1,104 | 29,611 | **88.63%** | 3.29% | 7.69% | 4.60% |
| **SSI Only (Soil Moisture)** | 646 | 8,860 | 550 | 23,459 | 71.92% | 6.80% | **54.01%** | 12.07% |
| **SCS CN Runoff + SSI** | 644 | 8,237 | 552 | 24,082 | 73.78% | 7.25% | 53.85% | 12.78% |
| **Base GEE ERA5 + SSI (10mm)** | 545 | 5,063 | 651 | 27,256 | 82.95% | **9.72%** | 45.57% | **16.02%** |
| **Optimized GEE ERA5 (75%ile)** | 625 | 6,056 | 571 | 26,263 | 80.23% | 9.35% | 52.26% | 15.87% |

### Severe Trigger Levels

| Model Configuration | True Positive (TP) | False Positive (FP) | False Negative (FN) | True Negative (TN) | Accuracy | Precision | Daily Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Precipitation Only (CHIRPS)** | 33 | 1,094 | 1,163 | 31,225 | **93.27%** | 2.93% | 2.76% | 2.84% |
| **SSI Only (Soil Moisture)** | 426 | 4,921 | 770 | 27,398 | 83.02% | 7.97% | **35.62%** | 13.02% |
| **SCS CN Runoff + SSI** | 399 | 3,802 | 797 | 28,517 | 86.28% | 9.50% | 33.36% | 14.79% |
| **Base GEE ERA5 + SSI (20mm)** | 228 | 1,611 | 968 | 30,708 | 92.30% | **12.40%** | 19.06% | 15.02% |
| **Optimized GEE ERA5 (85%ile)** | 403 | 3,002 | 793 | 29,317 | 88.68% | 11.84% | 33.70% | **17.52%** |

---

## 2. Key Physical & Analytical Insights

1. **Failure of Precipitation-Only Triggers:**
   Precipitation alone has near-zero daily recall (**2.76% – 7.69%**). This highlights why parametric flood insurance programs must avoid simple rainfall triggers: heavy rainfall falling on dry soil infiltrates rapidly and does not cause flood disasters.
2. **SSI (Soil Moisture) Over-Triggering:**
   Soil moisture alone has high recall (up to **54.01%**) but suffers from high false alarms (**8,860 False Positive days**), dragging precision down to **6.80%**. This is because soil can remain fully saturated for weeks without active drainage water overflowing fields.
3. **The SCS Curve Number Base Model:**
   The original Curve Number model translates rainfall directly into runoff. It captures events decently but has high false alarms (**8,237 Moderate False Positive days**), leading to lower daily accuracy (73.78%).
4. **Base GEE ERA5 vs. Optimized Percentiles (The Core Value):**
   * *The Base ERA5 model* uses static 10mm / 20mm thresholds. Because ERA5 runoff is physically smoother, these static thresholds severely suppress event capture, dropping daily recall to **19.06%** for severe floods.
   * *The Optimized ERA5 model* adjusts thresholds per district using percentiles. This restores daily recall to **33.70%** (almost doubling base recall) and yields the highest overall **F1-Score (17.52%)** for severe triggers, representing the best balance of precision and recall.
