"""
Script 1: SWI Consecutive Flood Days - Full Season Analysis
============================================================
Uses the downloaded Copernicus SWI (T=40) daily data for all Africa maize
districts to:
  1. Compute the climatological 95th percentile (P95) of SWI per district.
  2. Flag each day where SWI > P95 as a "flood day".
  3. Count consecutive flood-day streaks within each crop year
     (planting_doy → harvest_doy).
  4. Classify streaks by severity:
       ≥4 days → Waterlogging risk
       ≥6 days → High yield-loss risk
       ≥7 days → Severe yield-loss risk
  5. Output an event-level CSV and an annual summary CSV.
"""

import os
import time
import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────
BASE = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study"
SWI_CSV = os.path.join(BASE, "data", "SWI_T_10_T_40", "Africa_SWI_Maize_2007_2025.csv")
OUT_DIR = os.path.join(BASE, "output", "agricultural")
os.makedirs(OUT_DIR, exist_ok=True)

EVENT_OUT = os.path.join(OUT_DIR, "SWI_Consecutive_Flood_Days_AllDistricts.csv")
SUMMARY_OUT = os.path.join(OUT_DIR, "SWI_Flood_Summary_AllDistricts.csv")


def assign_crop_year(row_date, planting_doy, harvest_doy):
    """
    Return the crop-year integer for a given date.
    A crop year is defined by the planting DOY.
    If planting_doy > harvest_doy the season wraps across the calendar year
    boundary (e.g. plant Oct → harvest Apr).
    """
    doy = row_date.dayofyear
    year = row_date.year

    if planting_doy <= harvest_doy:
        # Season within one calendar year
        if planting_doy <= doy <= harvest_doy:
            return year
        else:
            return np.nan
    else:
        # Season wraps across year boundary (e.g. plant Oct, harvest Apr)
        if doy >= planting_doy:
            return year          # e.g. Oct 2010 → crop_year 2010
        elif doy <= harvest_doy:
            return year - 1      # e.g. Mar 2011 → crop_year 2010
        else:
            return np.nan        # out of season


def find_consecutive_streaks(flood_flags):
    """
    Given a boolean Series (True = flood day), return a list of
    (start_idx, end_idx, length) for every consecutive True run.
    """
    streaks = []
    in_streak = False
    start = 0
    for i, v in enumerate(flood_flags):
        if v and not in_streak:
            in_streak = True
            start = i
        elif not v and in_streak:
            in_streak = False
            streaks.append((start, i - 1, i - start))
    if in_streak:
        streaks.append((start, len(flood_flags) - 1, len(flood_flags) - start))
    return streaks


def classify_severity(n_days):
    if n_days >= 14:
        return "Severe yield-loss risk"
    elif n_days >= 10:
        return "High yield-loss risk"
    elif n_days >= 7:
        return "Severe waterlogging risk"
    return None  # should not happen if we filter >= 7


def main():
    t0 = time.time()
    print("=" * 60)
    print("Script 1: SWI Consecutive Flood Days - Full Season")
    print("=" * 60)

    # ── 1. Load data ──────────────────────────────────────────
    print("\n[1/5] Loading Copernicus SWI data ...", flush=True)
    df = pd.read_csv(SWI_CSV, low_memory=False)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['swi_040', 'planting_doy', 'harvest_doy'])
    df['planting_doy'] = df['planting_doy'].astype(int)
    df['harvest_doy'] = df['harvest_doy'].astype(int)
    print(f"    Loaded {len(df):,} rows, "
          f"{df['ADM_NAME'].nunique()} districts, "
          f"{df['COUNTRY'].nunique()} countries.")

    # ── 2. Climatological P95 per district ────────────────────
    print("\n[2/5] Computing climatological P95 per district ...", flush=True)
    district_key = ['ISO3', 'COUNTRY', 'ADM_NAME']
    p95 = (df.groupby(district_key)['swi_040']
             .quantile(0.95)
             .reset_index()
             .rename(columns={'swi_040': 'p95_swi'}))
    df = df.merge(p95, on=district_key, how='left')
    df['is_flood_day'] = df['swi_040'] > df['p95_swi']
    print(f"    P95 range: {p95['p95_swi'].min():.1f} – {p95['p95_swi'].max():.1f}")
    print(f"    Total flood days flagged: {df['is_flood_day'].sum():,}")

    # ── 3. Assign crop years ──────────────────────────────────
    print("\n[3/5] Assigning crop years (planting -> harvest) ...", flush=True)
    df['crop_year'] = df.apply(
        lambda r: assign_crop_year(r['date'], r['planting_doy'], r['harvest_doy']),
        axis=1
    )
    df = df.dropna(subset=['crop_year'])
    df['crop_year'] = df['crop_year'].astype(int)
    print(f"    Rows within a crop season: {len(df):,}")

    # ── 4. Count consecutive streaks ──────────────────────────
    print("\n[4/5] Counting consecutive flood-day streaks ...", flush=True)
    event_rows = []

    grouped = df.sort_values('date').groupby(district_key + ['crop_year'])
    total_groups = len(grouped)
    for i, ((iso3, country, adm, cy), grp) in enumerate(grouped):
        if (i + 1) % 5000 == 0:
            print(f"    Processing group {i+1:,}/{total_groups:,} ...", flush=True)

        flags = grp['is_flood_day'].values
        dates = grp['date'].values
        streaks = find_consecutive_streaks(flags)

        for s_start, s_end, s_len in streaks:
            if s_len >= 7:
                event_rows.append({
                    'ISO3': iso3,
                    'COUNTRY': country,
                    'ADM_NAME': adm,
                    'crop_year': cy,
                    'streak_start': pd.Timestamp(dates[s_start]).strftime('%Y-%m-%d'),
                    'streak_end': pd.Timestamp(dates[s_end]).strftime('%Y-%m-%d'),
                    'streak_days': s_len,
                    'severity': classify_severity(s_len),
                    'p95_threshold': grp['p95_swi'].iloc[0],
                })

    df_events = pd.DataFrame(event_rows)
    print(f"    Found {len(df_events):,} events with >=4 consecutive flood days.")

    # ── 5. Build summary ──────────────────────────────────────
    print("\n[5/5] Building annual summary per district ...", flush=True)
    if len(df_events) > 0:
        summary = (df_events.groupby(district_key + ['crop_year'])
                   .agg(
                       max_consecutive_flood_days=('streak_days', 'max'),
                       total_flood_streak_days=('streak_days', 'sum'),
                       num_waterlogging_events=('severity', lambda x: (x == 'Severe waterlogging risk').sum()),
                       num_high_risk_events=('severity', lambda x: (x == 'High yield-loss risk').sum()),
                       num_severe_events=('severity', lambda x: (x == 'Severe yield-loss risk').sum()),
                       p95_threshold=('p95_threshold', 'first'),
                   )
                   .reset_index())
    else:
        summary = pd.DataFrame()

    # ── Save outputs ──────────────────────────────────────────
    df_events.to_csv(EVENT_OUT, index=False)
    summary.to_csv(SUMMARY_OUT, index=False)
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"DONE in {elapsed:.1f}s")
    print(f"  Events CSV : {EVENT_OUT}")
    print(f"  Summary CSV: {SUMMARY_OUT}")
    if len(summary) > 0:
        print(f"\n  Summary stats:")
        print(f"    Districts with >=1 event: {summary['ADM_NAME'].nunique()}")
        print(f"    Countries represented  : {summary['COUNTRY'].nunique()}")
        print(f"    Total waterlogging     : {summary['num_waterlogging_events'].sum()}")
        print(f"    Total high-risk        : {summary['num_high_risk_events'].sum()}")
        print(f"    Total severe           : {summary['num_severe_events'].sum()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
