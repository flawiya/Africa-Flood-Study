Recommended Execution Order
Run these scripts in this exact sequence to complete all Readme objectives:


# ── STEP 1: Data Foundations (already done) ──
python "Extracting Admin 2_GADM _Zambia.py"
python "ESA_World_Cover_Zambia_Extraction.py"       # → GEE export
python "CHIRP_data acquition_Zambia.py"              # → GEE export
python "Spatial Join & Mapping_Zambia.py"            # → Heal GEE names
# ── STEP 2: Stratification (already done) ──
python "Zambia_Agri_Threshold_Audit.py"
python "Study_Area_Extraction_SHP.py"
python "Zambia_Dual_regime.py"
# ── STEP 3: Baselines ──
python "Zambia_Urban_P95_Triggers.py"                # Urban P₉₅
python "Zambia_Agri_Runoff_SCS.py"                   # ← NEW: Agri SCS
# ── STEP 4: Visualization ──
python "visualization_pipeline.py"                    # ← NEW: All 6 maps
# ── STEP 5: Validation ──
# First: download EM-DAT CSV → output/emdat_zambia_floods.csv
python "emdat_integration.py"          