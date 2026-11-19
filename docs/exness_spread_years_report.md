# Exness USTEC spread by year — results

Made by `scripts/exness_spread_years.py` on 2026-11-19. Rules were committed before these prices were read (`docs/exness_spread_years_preregistration.md`). Measurement only: no strategy was run and no cost, backtest or qualification setting changed. 2023 is a control run; the official 2023 result is `docs/exness_spread_check_report.md`.

**Spread** is ask minus bid in index points. **Median** is the middle minute. **p90** means 90% of minutes were at or below that value.

## File checks

| year | usable | valid weekdays | clock | median price gap to HistData | bad ticks |
|---|---|---:|---|---:|---:|
| 2019 (Aug 5 on) | NO | 33/107 = 30.8% FAIL | PASS | 1.17 PASS | 0 of 5,043,952 PASS |
| 2020 | NO | 235/262 = 89.7% FAIL | PASS | 1.91 PASS | 0 of 14,421,267 PASS |
| 2021 | YES | 242/261 = 92.7% PASS | PASS | 3.65 PASS | 0 of 11,700,710 PASS |
| 2022 | YES | 246/260 = 94.6% PASS | PASS | 3.83 PASS | 0 of 16,483,469 PASS |
| 2023 (control) | YES | 245/260 = 94.2% PASS | PASS | 7.90 PASS | 0 of 12,701,245 PASS |
| 2024 | NO | 241/262 = 92.0% PASS | PASS | 17.29 FAIL | 0 of 19,214,331 PASS |

## Spread

| year | window | minutes | days | Exness median | Exness p90 | vs 1.5 | Dukascopy median |
|---|---|---:|---:|---:|---:|---|---|
| 2019 (Aug 5 on) | pre-US 03:00-09:29 | 40,543 | 104 | 2.16 | 2.35 | no verdict (file not usable) | Dukascopy not available |
| 2019 (Aug 5 on) | US 09:30-15:54 | 38,328 | 104 | 2.17 | 2.39 | no verdict (file not usable) | Dukascopy not available |
| 2020 | pre-US 03:00-09:29 | 98,503 | 255 | 2.69 | 3.28 | no verdict (file not usable) | Dukascopy not available |
| 2020 | US 09:30-15:54 | 97,405 | 257 | 2.72 | 3.39 | no verdict (file not usable) | Dukascopy not available |
| 2021 | pre-US 03:00-09:29 | 99,959 | 257 | 2.86 | 3.22 | 1.5 assumption understated | Dukascopy not available |
| 2021 | US 09:30-15:54 | 96,850 | 255 | 2.94 | 3.41 | 1.5 assumption understated | Dukascopy not available |
| 2022 | pre-US 03:00-09:29 | 100,521 | 258 | 2.75 | 3.29 | 1.5 assumption understated | Dukascopy not available |
| 2022 | US 09:30-15:54 | 97,885 | 258 | 2.87 | 3.65 | 1.5 assumption understated | Dukascopy not available |
| 2023 (control) | pre-US 03:00-09:29 | 100,551 | 258 | 2.94 | 3.22 | 1.5 assumption understated | 3.45 (ratio 0.85): similar |
| 2023 (control) | US 09:30-15:54 | 97,357 | 257 | 2.93 | 3.39 | 1.5 assumption understated | 1.45 (ratio 2.02): Exness more expensive |
| 2024 | pre-US 03:00-09:29 | 97,868 | 251 | 3.41 | 3.77 | no verdict (file not usable) | Dukascopy not available |
| 2024 | US 09:30-15:54 | 95,376 | 251 | 3.31 | 3.64 | no verdict (file not usable) | Dukascopy not available |

## Clock check details

| year | period | correlation at lag 0 | best lag (minutes) |
|---|---|---:|---:|
| 2019 (Aug 5 on) | US DST | 0.992 | +0 |
| 2019 (Aug 5 on) | after US DST | 0.988 | +0 |
| 2020 | before US DST | 0.996 | +0 |
| 2020 | US DST | 0.997 | +0 |
| 2020 | after US DST | 0.994 | +0 |
| 2021 | before US DST | 0.997 | +0 |
| 2021 | US DST | 0.971 | +0 |
| 2021 | after US DST | 0.996 | +0 |
| 2022 | before US DST | 0.997 | +0 |
| 2022 | US DST | 0.991 | +0 |
| 2022 | after US DST | 0.912 | +0 |
| 2023 (control) | before US DST | 0.995 | +0 |
| 2023 (control) | US DST | 0.994 | +0 |
| 2023 (control) | after US DST | 0.992 | +0 |
| 2024 | before US DST | 0.993 | +0 |
| 2024 | US DST | 0.995 | +0 |
| 2024 | after US DST | 0.997 | +0 |

## Limits

- This is the archive's `USTEC` instrument. Account types such as `USTECm` or `USTECc` can differ, and any commission is not in the spread.
- It shows the spread at the last tick of each minute, not the price of any actual order.
- It says nothing about whether a strategy makes money.
