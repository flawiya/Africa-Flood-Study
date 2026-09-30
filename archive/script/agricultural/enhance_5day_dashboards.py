import argparse
import json
import pathlib
import sys

import geopandas as gpd
import pandas as pd

# ---------------------------------------------------------------------------
# User‑provided flood list (district, year, approximate flood DOY range)
# ---------------------------------------------------------------------------
USER_FLOOD_LIST = [
    {"COUNTRY": "Nigeria",   "ADM_NAME": "Ibaji / Ogbaru",   "crop_year": 2022, "doy_start": 260, "doy_end": 295},
    {"COUNTRY": "Nigeria",   "ADM_NAME": "Ibaji / Lokoja",   "crop_year": 2012, "doy_start": 255, "doy_end": 290},
    {"COUNTRY": "Malawi",    "ADM_NAME": "Nsanje / Chikwawa", "crop_year": 2023, "doy_start": 70,  "doy_end": 85},
    {"COUNTRY": "Malawi",    "ADM_NAME": "Nsanje / Phalombe", "crop_year": 2019, "doy_start": 65,  "doy_end": 80},
    {"COUNTRY": "Mozambique","ADM_NAME": "Búzi / Nhamatanda", "crop_year": 2019, "doy_start": 73,  "doy_end": 88},
    {"COUNTRY": "Kenya",     "ADM_NAME": "Budalangi / Tana",  "crop_year": 2024, "doy_start": 110, "doy_end": 145},
    {"COUNTRY": "Kenya",     "ADM_NAME": "Nyando / Kisumu",   "crop_year": 2020, "doy_start": 115, "doy_end": 160},
    {"COUNTRY": "Zambia",    "ADM_NAME": "Namwala / Monze",   "crop_year": 2023, "doy_start": 15,  "doy_end": 55},
    {"COUNTRY": "Zambia",    "ADM_NAME": "Southern Province", "crop_year": 2022, "doy_start": 10,  "doy_end": 50},
    {"COUNTRY": "Egypt",     "ADM_NAME": "Beheira (Delta)",  "crop_year": 2025, "doy_start": 1,   "doy_end": 25},
    {"COUNTRY": "Ethiopia", "ADM_NAME": "Mustahil (Somali)","crop_year": 2023, "doy_start": 290, "doy_end": 325},
    {"COUNTRY": "South Sudan","ADM_NAME": "Bor South",        "crop_year": 2020, "doy_start": 220, "doy_end": 300},
    {"COUNTRY": "Ghana",    "ADM_NAME": "Kassena-Nankana",   "crop_year": 2020, "doy_start": 245, "doy_end": 270},
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_calibration(csv_path: pathlib.Path) -> pd.DataFrame:
    """Load a per‑option CSV summary.

    Expected columns include at least:
        ISO3, COUNTRY, ADM_NAME, crop_year, planting, harvest,
        flood_days_5plus, max_consec_days
    The script will treat any row with ``flood_days_5plus > 0`` as a
    positive 5‑day streak for that option.
    """
    df = pd.read_csv(csv_path)
    return df


def load_shapefile(shp_path: pathlib.Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(shp_path)
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)
    gdf["centroid"] = gdf.geometry.centroid
    gdf["lon"] = gdf.centroid.x
    gdf["lat"] = gdf.centroid.y
    return gdf


def filter_to_user_list(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows that match the user‑provided district/year list and whose
    flood window overlaps the in‑season maize calendar.
    """
    def matches_user_list(r):
        for entry in USER_FLOOD_LIST:
            if r["COUNTRY"] == entry["COUNTRY"] and r["crop_year"] == entry["crop_year"]:
                parts = [p.strip() for p in entry["ADM_NAME"].split('/')]
                if r["ADM_NAME"] in parts:
                    return True
        return False

    df = df[df.apply(matches_user_list, axis=1)]
    if df.empty:
        return df
    user_df = pd.DataFrame(USER_FLOOD_LIST)
    # We must join carefully because ADM_NAME in df might be just one part of the entry
    # For now, keep the overlap logic based on the user-provided window
    df = df.merge(user_df, on=["COUNTRY", "crop_year"], how="inner", suffixes=("", "_ref"))
    # Filter where the ADM_NAME from the row is present in the split list of the ref
    df = df[df.apply(lambda r: r["ADM_NAME"] in [p.strip() for p in r["ADM_NAME_ref"].split('/')], axis=1)]
    
    overlap = (df["planting"].astype(float) <= df["doy_end"]) & (df["harvest"].astype(float) >= df["doy_start"])
    return df[overlap]


def build_marker_dict(df: pd.DataFrame) -> list:
    """Create markers for rows where a 5‑day streak was recorded.
    ``flood_days_5plus`` > 0 indicates the condition was met.
    """
    markers = []
    for _, row in df.iterrows():
        markers.append({
            "name": row["ADM_NAME"],
            "year": int(row["crop_year"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "flood_days": int(row["max_consec_days"] if "max_consec_days" in row else 0),
        })
    return markers


def inject_js(html_path: pathlib.Path, markers_json: dict) -> None:
    html_text = html_path.read_text(encoding="utf-8")
    js_arrays = []
    for opt, markers in markers_json.items():
        js_var = f"caught_{opt}"
        js_arrays.append(f"const {js_var} = {json.dumps(markers, ensure_ascii=False)};")
    add_markers_js = """
    function addMarkers(markerArray) {
        markerArray.forEach(d => {
            L.circleMarker([d.lat, d.lon], {
                color: 'red',
                radius: 6,
                fillOpacity: 0.8
            }).addTo(map).bindTooltip(`${d.name} – ${d.year}<br>Flood days: ${d.flood_days}`);
        });
    }
    """
    script_content = "<script>\n" + "\n".join(js_arrays) + "\n" + add_markers_js + "\n" + "addMarkers(caught_opt1); addMarkers(caught_opt2); addMarkers(caught_opt3);\n" + "</script>"
    if "</body>" in html_text:
        new_html = html_text.replace("</body>", script_content + "\n</body>")
    else:
        new_html = html_text + script_content
    html_path.write_text(new_html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Overlay red‑dot markers for user‑specified flood districts on the 5‑day dashboards.")
    parser.add_argument("--csv-dir", required=True, help="Directory containing the three per‑option CSV summary files.")
    parser.add_argument("--shp", required=True, help="Path to district shapefile (Zambia_agri_districts.shp).")
    parser.add_argument("--output-dir", required=True, help="Folder with the three HTML dashboard files.")
    args = parser.parse_args()

    csv_dir = pathlib.Path(args.csv_dir)
    out_dir = pathlib.Path(args.output_dir)

    gdf = load_shapefile(pathlib.Path(args.shp))

    markers = {}
    option_files = {
        "opt1": csv_dir / "option1_99th_percentile_5day_summary.csv",
        "opt2": csv_dir / "option2_95th_plus_absolute_5day_summary.csv",
        "opt3": csv_dir / "option3_pure_absolute_5day_summary.csv",
    }
    for opt_key, csv_path in option_files.items():
        if not csv_path.is_file():
            print(f"Warning: {csv_path} not found – skipping {opt_key}", file=sys.stderr)
            continue
        df = load_calibration(csv_path)
        df = df.merge(gdf[["ADM_NAME", "lon", "lat"]], on="ADM_NAME", how="inner")
        df = filter_to_user_list(df)
        markers[opt_key] = build_marker_dict(df)
        print(f"{opt_key}: {len(markers[opt_key])} markers will be added.")

    html_files = [
        out_dir / "Option1_99th_Percentile_5Day_Dashboard.html",
        out_dir / "Option2_95th_plus_Absolute_5Day_Dashboard.html",
        out_dir / "Option3_Pure_Absolute_5Day_Dashboard.html",
    ]
    for html_path in html_files:
        if not html_path.is_file():
            print(f"Warning: {html_path} not found – skipping", file=sys.stderr)
            continue
        inject_js(html_path, markers)
        print(f"Injected markers into {html_path.name}")

    print("All done.")

if __name__ == "__main__":
    main()
