# Triple Lock EM-DAT Validation for 3 Zambia Maize Districts

This validation compares the T=20 Triple Lock trigger against EM-DAT event windows for Kapiri Mposhi, Chibombo, and Monze.

## Target districts and seasons
- KAPIRI MPOSHI: 2007/2008
- CHIBOMBO: 2011/2012
- MONZE: 2007/2008

## Trigger rules
- Severe: SSI_14d > 1.5, Runoff_7d > 20.0, SWI_T20 > 30.0
- Moderate: SSI_14d > 1.0, Runoff_7d > 10.0, SWI_T20 > 25.0

## District-level results
| District | Season | Events | Event Hits | Event Misses | Severe Trigger Days | Severe Days In Event | Severe Days Outside Event | Day Precision | Event Sensitivity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| KAPIRI MPOSHI | 2007/2008 | 0 | 0 | 0 | 30 | 0 | 30 | 0.000 | nan |
| CHIBOMBO | 2011/2012 | 0 | 0 | 0 | 0 | 0 | 0 | nan | nan |
| MONZE | 2007/2008 | 1 | 1 | 0 | 43 | 43 | 0 | 1.000 | 1.000 |

## Notes
- This script uses EM-DAT event windows mapped to the target districts by district name and province text matching.
- A hit is counted when a severe trigger day appears inside an EM-DAT event window.
- False alarms are counted as severe trigger days outside any EM-DAT event window in the season.
