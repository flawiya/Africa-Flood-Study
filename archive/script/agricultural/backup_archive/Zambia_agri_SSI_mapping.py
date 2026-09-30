import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# =============================================================================
# RESEARCH METHODOLOGY & CITATIONS
# =============================================================================
# 1. FULL-CYCLE VULNERABILITY MONITORING (November–April)
#    References: Rosenzweig et al. (2002). "Increased crop damage from excess 
#    precipitation"; Bremond et al. (2023). "Agricultural flood risk assessment."
#    Justification: Excess moisture impacts maize at the emergence stage 
#    (Nov-Dec washout), the vegetative stage (Jan-Feb anoxia), and the 
#    maturity stage (Mar-Apr grain rot). Monitoring the full window is 
#    essential for agricultural flood risk assessment.
#
# 2. FLOOD THRESHOLD (SSI > +1.5)
#    Reference: WMO (2012). "Standardized Precipitation Index User Guide."
#    Justification: An SSI value of +1.5 represents a "Very Wet" anomaly, 
#    statistically occurring in the top ~6.7% of historical observations. 
#
# 3. NON-PARAMETRIC SSI (Gringorten)
#    Reference: Farahmand & AghaKouchak (2015).
#    Justification: Gringorten SSI respects the physical ceiling of soil 
#    saturation, allowing for unbiased cross-district comparisons.
# =============================================================================

# 1. LOAD DATA
# Update path to the Full-Season SSI file
file_path = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\Zambia_Agricultural_Districts_Final_Study_SSI_Gringorten_Full_Season.csv"

if not os.path.exists(file_path):
    print(f"❌ Error: File not found at {file_path}")
else:
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])

    # 2. CALCULATE SEASONAL FLOOD FREQUENCY (Heatmap)
    # Note: We now group by 'Crop_Year' (e.g., Nov 2020-Apr 2021 is one unit)
    flood_counts = df[df['SSI'] >= 1.5].groupby(['District_Name', 'Crop_Year']).size().unstack(fill_value=0)

    # -----------------------------------------------------------------------------
    # VISUALIZATION 1: SEASONAL FLOOD HEATMAP
    # -----------------------------------------------------------------------------
    plt.figure(figsize=(16, 10))
    sns.heatmap(flood_counts, cmap="YlOrRd", annot=False, 
                cbar_kws={'label': 'Days per Crop Season (Nov-Apr) with SSI > 1.5'})

    plt.title("Zambia Agricultural Districts: Annual Flood Risk Frequency (Nov-Apr Season)", 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Crop Year (Starting November)", fontsize=12)
    plt.ylabel("District Name", fontsize=12)
    plt.tight_layout()

    heatmap_path = file_path.replace(".csv", "_Seasonal_Heatmap.png")
    plt.savefig(heatmap_path, dpi=300)
    print(f"[SUCCESS] Seasonal Heatmap saved: {heatmap_path}")

    # -----------------------------------------------------------------------------
    # VISUALIZATION 2: FACETED SSI TIME-SERIES (The Gallery)
    # -----------------------------------------------------------------------------
    districts = sorted(df['District_Name'].unique())
    n_districts = len(districts)
    cols = 3
    rows = (n_districts // cols) + (1 if n_districts % cols > 0 else 0)

    fig, axes = plt.subplots(rows, cols, figsize=(22, rows * 4), sharex=False)
    axes = axes.flatten()

    print(f"[INFO] Generating time-series plots for {n_districts} districts...")

    for i, dist in enumerate(districts):
        ax = axes[i]
        dist_data = df[df['District_Name'] == dist].sort_values('Date')
        
        # Plot SSI (Matplotlib will automatically leave gaps for the missing dry months)
        ax.plot(dist_data['Date'], dist_data['SSI'], color='#2980b9', linewidth=0.7, alpha=0.9)
        
        # Highlight Flood Threshold (+1.5)
        ax.axhline(y=1.5, color='#c0392b', linestyle='--', linewidth=1, label='Threshold (+1.5)')
        
        # Fill areas above threshold
        ax.fill_between(dist_data['Date'], dist_data['SSI'], 1.5, 
                        where=(dist_data['SSI'] >= 1.5), color='#e74c3c', alpha=0.4)

        ax.set_title(f"District: {dist}", fontsize=13, fontweight='bold')
        ax.set_ylim(-3.5, 3.5)
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        
        if i % cols == 0:
            ax.set_ylabel("SSI (Gringorten)")

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.suptitle("Zambia Root Zone (0-100cm) Soil Moisture SSI: Full-Season Analysis (Nov-Apr)\n"
                 "References: Rosenzweig et al. (2002) | WMO (2012) | Farahmand & AghaKouchak (2015)", 
                 fontsize=22, fontweight='bold', y=1.03)
    
    plt.tight_layout()
    gallery_path = file_path.replace(".csv", "_Full_Season_Check.png")
    plt.savefig(gallery_path, dpi=300, bbox_inches='tight')
    print(f"[SUCCESS] Full-Season Gallery saved: {gallery_path}")

    plt.show()