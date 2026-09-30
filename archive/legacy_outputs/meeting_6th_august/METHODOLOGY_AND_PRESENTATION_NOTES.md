# Pan-African Agricultural Flood Risk Regionalization & Correlation Study
## Comprehensive Methodology, Diagnostic Insights & Presentation Reference Guide

* **Study Scope**: 1,638 Agricultural Districts across Africa (2008–2024 Crop Years, 17 Historical Seasons)
* **Underlying Hazard Model**: 95th Percentile + 85% Absolute SWI Floor Threshold (5-Day Continuous Streak Basis)
* **Isolated Project Folder**: `output/agricultural/meeting_6th_august/` & `script/agricultural/meeting_6th_august/`

---

## 📌 Section 1: Spatial Regionalization & Clustering Methodology

### 1.1 Combined Distance Matrix ($D_{\text{combined}}$)
Spatial regionalization groups contiguous, hydrologically similar agricultural districts into homogenous risk zones. The dissimilarity matrix combines physical geography and historical flood occurrence dissimilarity:

$$D_{\text{combined}} = w_{\text{geo}} \cdot \tilde{D}_{\text{geo}} + w_{\text{weather}} \cdot \tilde{D}_{\text{weather}}$$

Where:
* $\tilde{D}_{\text{geo}}$: Normalized Euclidean distance between district metric centroids projected in EPSG:3857 (Web Mercator), scaled to $[0, 1]$.
* $\tilde{D}_{\text{weather}}$: Normalized Jaccard dissimilarity of annual 5-day continuous flood occurrence vectors over 2008–2024.
* $w_{\text{geo}}, w_{\text{weather}}$: Model weighting parameters (e.g., $0.60 / 0.40$, $0.70 / 0.30$, $0.50 / 0.50$).

---

### 1.2 Agglomerative Hierarchical Clustering (Ward Linkage)
Ward’s minimum-variance agglomerative hierarchical clustering method is applied to $D_{\text{combined}}$. At each step, Ward’s criterion merges the pair of clusters that minimizes the increase in total within-cluster variance:

$$\Delta E = \frac{n_A \cdot n_B}{n_A + n_B} \|\vec{m}_A - \vec{m}_B\|^2$$

This guarantees spatial contiguity and compact risk zones across the African continent.

---

### 1.3 Centroid Choice Rationale: Standard Centroid (`.centroid`) vs. Representative Point
* **Methodology Rationale**: Standard metric polygon `.centroid` (in EPSG:3857) is retained as the spatial location feature.
* **Comparative Finding**: Comparative evaluation against `.representative_point()` demonstrated that at the Pan-African macro scale (0 to 4,000 km dissimilarity range across 1,638 districts), the minor 2–5 km shift for concave/horseshoe geometries has **zero impact on spatial regionalization boundaries**.
* **Empirical Verification**: Ward agglomerative clustering yields 100% identical optimal cluster counts ($K=6$ for 60-40, $K=10$ for 70-30, $K=2$ for 50-50) and identical Silhouette validation scores (`0.4731` for 60-40). Retaining standard `.centroid` ensures computational efficiency, code simplicity, and direct consistency with established spatial econometrics literature (Ward 1963, Murtagh & Legendre 2014).

---

### 1.4 Natural Cluster Count Optimization ($K = 2 \dots 15$)
Cluster counts were evaluated across $K = 2 \dots 15$ using the Mean Silhouette Score to determine natural cluster boundaries without artificial constraints:

$$S(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$

#### Active Model Benchmarks:
1. **60% Geography / 40% Weather** $\rightarrow$ **Optimal Natural $K = 6$** (Silhouette Score: `0.4731`)
   * *Output*: `MultiMethod_Clustering_60geo_40wx.html`
2. **70% Geography / 30% Weather** $\rightarrow$ **Optimal Natural $K = 10$** (Silhouette Score: `0.4886`)
   * *Output*: `MultiMethod_Clustering_70geo_30wx.html`
3. **50% Geography / 50% Weather** $\rightarrow$ **Optimal Natural $K = 2$** (Silhouette Score: `0.4913`)
   * *Output*: `MultiMethod_Clustering_50geo_50wx.html`
5. **30% Geography / 70% Weather** $\rightarrow$ **Optimal Natural $K = 2$** (Silhouette Score: `0.5563`)
   * *Output*: `MultiMethod_Clustering_30geo_70wx.html` & `Africa_Flood_Correlation_Map_30geo_70wx.html`

---

## 🔬 Section 2: Inter-District Correlation & Zero-Variance Scientific Diagnostics

### 2.1 Pearson Correlation Matrix Formula
The inter-district co-movement of annual 95th Percentile + 85% SWI Floor flood days is calculated using Pearson’s product-moment correlation coefficient $r(X, Y)$ across 17 crop years (2008–2024):

$$r(X, Y) = \frac{\sum_{t=2008}^{2024} (X_t - \bar{X})(Y_t - \bar{Y})}{\sqrt{\sum_{t=2008}^{2024} (X_t - \bar{X})^2 \sum_{t=2008}^{2024} (Y_t - \bar{Y})^2}} = \frac{\text{Cov}(X, Y)}{\sigma_X \cdot \sigma_Y}$$

---

### 2.2 The Zero-Trigger Variance Phenomenon ($\sigma = 0$) & Short-Duration Flood Events (< 5 Days)
#### Empirical Audit Finding:
* **786 out of 1,643 agricultural districts (47.8% across Africa)** recorded **0 flood days in ALL 17 crop years** (2008–2024) under the 5-day continuous streak model.

#### Hydrological Rationale:
1. **5-Day Continuous Persistence Rule**: The model requires $SWI \ge P_{95}$ AND $SWI \ge 85\%$ absolute Soil Water Index floor held continuously for **at least 5 consecutive days**.
2. **Flash Floods & Cyclonic Deluge (< 5 Days)**: Intense short-duration events (such as 1-to-4 day flash floods or rapid tropical cyclonic storm surges) dump extreme rainfall but do not persist for 5 unbroken days. These short events trigger 1–4 days of inundation, which are filtered out under the 5-day continuous streak rule.
3. **Hyper-Arid Baselines**: In hyper-arid or high-altitude regions (Sahel, Sahara fringes, Karoo), soil moisture never reaches the 85% absolute SWI floor.

#### Mathematical Explanation of $0.000$ Correlation:
* For these 786 zero-trigger districts, the 17-year annual time-series is a constant zero vector:
  $$\vec{X} = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]$$
* The standard deviation of a constant vector is **$\sigma_X = 0$**.
* When calculating Pearson correlation, division by zero occurs:
  $$r(X, Y) = \frac{0}{0 \cdot \sigma_Y} \quad \rightarrow \text{Mathematically Undefined / Assigned } 0.000$$
* **Key Presentation Note**: Clicking any of these 786 districts renders a white map ($r = 0.000$). This reflects **zero historical 5-day continuous flood variance ($\sigma = 0$)**, though short-duration flash floods (<5 days) may still occur.

---

### 2.3 Distinction: Geographic Weighting vs. Pearson Correlation
* **70% Geo / 30% Weather Weighting**: Used **strictly for Spatial Risk Regionalization Clustering** (grouping contiguous districts into Risk Zones $K=10$).
* **Pearson Correlation Matrix ($r$)**: Measures **pure annual time-series co-movement** of flood days over 2008–2024. It measures whether two districts experience floods in the exact same years, independent of geographic distance weighting.

---

## 🎨 Section 3: User Interface & Dashboard Architecture

1. **Light-Theme Design**: CartoDB Positron Light basemap (`light_all`), `#ffffff` panels, `#0f172a` slate typography, and `#e2e8f0` borders.
2. **Hidden Side Panel on Load (100% Full-Width Map)**: Map takes 100% width initially. Clicking any district polygon slides open the right panel; clicking `✕` collapses it back to full-width.
3. **Discrete Categorical Class Legend**:
   * 🟦 **Strong Positive** ($r \ge +0.70$)
   * 🩵 **Moderate Positive** ($+0.30 \le r < +0.70$)
   * ⬜ **Weak / Neutral** ($-0.30 < r < +0.30$)
   * 🟧 **Moderate Negative** ($-0.70 < r \le -0.30$)
   * 🟥 **Strong Negative** ($r \le -0.70$)
4. **Clean Side Panel Tables**: Clean `District | Country | Zone | Pearson r` columns (Disaster Context column removed for maximum readability).

---

## 📊 Section 4: Recommended Slide Structure for Executive Presentation

### Slide 1: Introduction & Underlying Threshold Hazard Model
* **Objective**: Regionalize Pan-African agricultural flood risk for parametric underwriting.
* **Dataset**: 1,638 districts, 17 crop seasons (2008–2024), 95th Percentile + 85% SWI Floor Threshold (5-day continuous streak basis).

### Slide 2: Spatial Regionalization & Clustering Results
* **Method**: Agglomerative Ward Hierarchical Clustering with $w_{\text{geo}} \cdot \tilde{D}_{\text{geo}} + w_{\text{weather}} \cdot \tilde{D}_{\text{weather}}$.
* **Results**:
  * 60% Geo / 40% Weather $\rightarrow$ Natural $K = 6$ (Silhouette: `0.4731`)
  * 70% Geo / 30% Weather $\rightarrow$ Natural $K = 10$ (Silhouette: `0.4886`)
  * Executive Forced Baseline $\rightarrow$ Forced $K = 14$ (Silhouette: `0.4421`)

### Slide 3: Inter-District Correlation & Short-Duration Flood Diagnostic
* **Co-movement Analysis**: Inter-district Pearson correlation $r$ across 1,638 districts.
* **Key Finding**: 47.8% of African districts (786 districts) recorded zero 5-day continuous flood triggers ($\sigma = 0$).
* **Hydrological Proof**: Short-duration flash floods & cyclonic deluge (<5 days) or hyper-arid baselines result in constant zero vectors ($\sigma=0$), yielding mathematically $0.000$ Pearson correlation.

### Slide 4: Interactive Web Dashboards Walkthrough
* Live demonstration of standalone clustering maps (`MultiMethod_Clustering_60geo_40wx.html`, `MultiMethod_Clustering_70geo_30wx.html`) and continuous correlation map dashboards (`Africa_Flood_Correlation_Map_60geo_40wx.html`, `Africa_Flood_Correlation_Map_70geo_30wx.html`).
