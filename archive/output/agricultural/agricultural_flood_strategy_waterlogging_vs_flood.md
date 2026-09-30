# Strategic Proposal: Waterlogging vs. Flood in Parametric Insurance

This proposal outlines the scientific justification for our runoff calculations and presents a dual-regime underwriting strategy that formally distinguishes between **Waterlogging (Soil Saturation)** and **Flooding (Crop Submersion/Washout)** for agricultural parametric insurance in Zambia.

---

## 1. Why Calculate SCS Runoff ($Q$) instead of using Raw Model Runoff?

When reviewing this methodology, underwriting partners may ask: **Why calculate runoff dynamically when global model runoff (e.g., from ERA5-Land or GLDAS) is already available?**

Here is the scientific and underwriting justification:

### A. Spatial Scale & Grid Resolution Mismatch
* **Global Models (ERA5-Land/GLDAS):** Compute physical runoff at coarse spatial scales ($9\text{ km}$ to $25\text{ km}$ grids). The model runoff is a grid-averaged pixel value that blends together diverse land-cover types (forests, grasslands, built-up areas, hills, and crop fields).
* **Our Method (SCS CN):** Customizes the runoff response strictly to **cultivated croplands** (Curve Number $CN=85$) and the specific **Hydrologic Soil Group** of the district. It represents field-level agricultural hydrology, which is the scale at which crop damage actually occurs.

### B. Transparency and Auditability in Underwriting
* For a parametric contract to be insurable, the payout trigger must be **transparent, reproducible, and verifiable** by insurers, reinsurers, and the insured.
* **ERA5-Land runoff** is calculated using complex, proprietary land surface model equations (the HTESSEL scheme) which are subject to update revisions, version changes, and retroactive calibration. 
* **Our SCS CN runoff** is computed directly from **CHIRPS daily precipitation** (a highly respected, open satellite rainfall product) using simple, transparent algebra. This ensures that the contract triggers are easily auditable.

### C. Capturing Antecedent Moisture Dynamics
* The SCS model translates daily rainfall into runoff by looking at **7-day cumulative rainfall** (Antecedent Moisture Condition). This represents how recent storms saturate the upper soil layers before runoff pooling begins, which physical land surface models often under-represent in coarse clay soils.

---

## 2. Underwriting Strategy: Waterlogging vs. Surface Flood

We propose dividing our agricultural parametric products into two distinct contracts based on crop growth stages and physical damage mechanisms:

### Type I: Waterlogging (Sustained Soil Saturation)
* **Damage Mechanism:** Root zone oxygen depletion (anoxia). Saturated soil prevents soil aeration, halting nitrogen uptake, stunting crop development, and resulting in slow crop yellowing (chlorosis) and gradual yield decay.
* **Target Growth Window:** Active vegetative and reproductive phases (January to March) when the crop has high transpiration demands.
* **Parametric Proxy Indicator:** **Standardized Soil Moisture Index (SSI) alone**.
  * *Trigger Condition:* $SSI \ge 1.2$ or $1.5$ sustained for **$\ge 7$ or $10$ consecutive days**.
  * *Underwriting Benefit:* Captures slow-onset, prolonged wet spells that stunt maize fields without creating visible standing water pooling.

### Type II: Surface Flood (Crop Submersion or Physical Washout)
* **Damage Mechanism:** Complete crop canopy submersion (stopping photosynthesis completely) or high-velocity flow washing away plants or flattening stalks (lodging).
* **Target Growth Window & Trigger Conditions:**
  1. **Early Stage (November–December):** Emergence and seedling stage. Young maize plants are short ($<30\text{ cm}$) and easily submerged.
     * *Trigger Condition:* Moderate Runoff (**$Q \ge 10\text{ mm}$**) or extreme daily rainfall anomaly (**$P \ge \text{Mean} + 2\sigma$**).
  2. **Late Stage (January–April):** Flowering and grain-filling. Plants are tall but vulnerable to lodging or physical washout.
     * *Trigger Condition:* Severe Runoff (**$Q \ge 25\text{ mm}$**) representing extreme surface pooling or flash flooding.
* **Parametric Proxy Indicator:** **SCS Runoff Depth ($Q$) or Daily Precipitation ($P$)**.
  * *Underwriting Benefit:* Captures rapid-onset, high-intensity storm events that cause immediate, visible flood destruction.

---

## 3. Strategic Recommendations for Tomorrow's Discussion

To align with underwriting partners and prepare possible solutions, we suggest structuring tomorrow's discussion around these three options:

1. **Standard Dual-Regime (Current):** SSI and Q must trigger on the same day. This is simple, has very low false positives, but may miss pure waterlogging events (where soil is wet but no single runoff spike occurs).
2. **Multi-Peril Basket (Recommended):** Separate waterlogging (SSI-based) and flash flood (Q-based) triggers. This provides complete coverage of both hazard mechanisms and is agronomically precise, though it may have higher premium costs.
3. **Phase-Gate Trigger:** Early stage utilizes pure rainfall/runoff trigger (for seedling drowning), while mid-to-late stage utilizes soil saturation + runoff trigger. This protects seedlings when they are small and mature plants when soil is saturated.
