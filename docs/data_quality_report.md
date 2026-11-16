# Data quality report (HistData NSXUSD M1, 2019-2024)

Made by `scripts/audit_measurements.py` on 2026-11-16. Rule: `docs/data_quality_rule.md` (03:00-15:55 New York, at least 765/775 bars, no hole longer than 5 min). Missing prices are never filled in.

| year | weekdays with data | valid | invalid | invalid: low coverage | invalid: hole > 5 min only | median bars | zero-volume bars |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 258 | 247 | 11 | 11 | 0 | 775 | 100% |
| 2020 | 258 | 242 | 16 | 16 | 0 | 775 | 100% |
| 2021 | 258 | 251 | 7 | 7 | 0 | 775 | 100% |
| 2022 | 258 | 250 | 8 | 8 | 0 | 775 | 100% |
| 2023 | 256 | 137 | 119 | 119 | 0 | 774 | 100% |
| 2024 | 259 | 242 | 17 | 15 | 2 | 775 | 100% |

**Volume:** HistData bars carry no volume (0 on every bar). `session_vwap` then falls back to the plain average of 5-minute typical prices (a time-weighted average), while the live MT5 feed has tick volume, so the backtest 'VWAP' and the live VWAP are different lines. VWAP-based rules (trend_fvg filter, vwap_reversion, london variants) were backtested on the time-weighted version.

## Invalid dates

| date | bars | longest hole (min) | reason |
|---|---:|---:|---|
| 2019-01-21 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2019-01-25 | 751 | 16 | only 751/775 bars; gap of 16 min |
| 2019-02-18 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2019-05-27 | 420 | 180 | only 420/775 bars; gap of 180 min |
| 2019-07-03 | 616 | 159 | only 616/775 bars; gap of 159 min |
| 2019-07-04 | 601 | 174 | only 601/775 bars; gap of 174 min |
| 2019-09-02 | 601 | 174 | only 601/775 bars; gap of 174 min |
| 2019-10-22 | 749 | 26 | only 749/775 bars; gap of 26 min |
| 2019-11-28 | 599 | 174 | only 599/775 bars; gap of 174 min |
| 2019-11-29 | 616 | 159 | only 616/775 bars; gap of 159 min |
| 2019-12-24 | 611 | 160 | only 611/775 bars; gap of 160 min |
| 2020-01-20 | 597 | 175 | only 597/775 bars; gap of 175 min |
| 2020-02-17 | 599 | 175 | only 599/775 bars; gap of 175 min |
| 2020-03-09 | 371 | 304 | only 371/775 bars; gap of 304 min |
| 2020-03-12 | 666 | 94 | only 666/775 bars; gap of 94 min |
| 2020-03-13 | 638 | 133 | only 638/775 bars; gap of 133 min |
| 2020-03-16 | 369 | 406 | only 369/775 bars; gap of 406 min |
| 2020-03-17 | 674 | 89 | only 674/775 bars; gap of 89 min |
| 2020-03-18 | 372 | 390 | only 372/775 bars; gap of 390 min |
| 2020-03-20 | 638 | 111 | only 638/775 bars; gap of 111 min |
| 2020-03-24 | 683 | 79 | only 683/775 bars; gap of 79 min |
| 2020-05-25 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2020-07-03 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2020-09-07 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2020-11-26 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2020-11-27 | 615 | 160 | only 615/775 bars; gap of 160 min |
| 2020-12-24 | 615 | 160 | only 615/775 bars; gap of 160 min |
| 2021-01-18 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2021-02-15 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2021-04-02 | 375 | 400 | only 375/775 bars; gap of 400 min |
| 2021-07-05 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2021-09-06 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2021-11-25 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2021-11-26 | 614 | 161 | only 614/775 bars; gap of 161 min |
| 2022-01-17 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-02-21 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-05-30 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-06-20 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-07-04 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-09-05 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-11-24 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2022-11-25 | 614 | 161 | only 614/775 bars; gap of 161 min |
| 2023-01-16 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2023-01-19 | 715 | 60 | only 715/775 bars; gap of 60 min |
| 2023-02-20 | 361 | 174 | only 361/775 bars; gap of 174 min |
| 2023-02-21 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-02-22 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-02-23 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-02-24 | 417 | 120 | only 417/775 bars; gap of 120 min |
| 2023-02-27 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-02-28 | 420 | 180 | only 420/775 bars; gap of 180 min |
| 2023-03-01 | 420 | 120 | only 420/775 bars; gap of 120 min |
| 2023-03-02 | 420 | 120 | only 420/775 bars; gap of 120 min |
| 2023-03-03 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-06 | 420 | 180 | only 420/775 bars; gap of 180 min |
| 2023-03-07 | 415 | 60 | only 415/775 bars; gap of 60 min |
| 2023-03-08 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-03-09 | 413 | 67 | only 413/775 bars; gap of 67 min |
| 2023-03-10 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-13 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-03-14 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-15 | 475 | 300 | only 475/775 bars; gap of 300 min |
| 2023-03-16 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-03-17 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-03-20 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-03-21 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-22 | 535 | 60 | only 535/775 bars; gap of 60 min |
| 2023-03-23 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-03-24 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-03-27 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-28 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-03-29 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-03-30 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-03-31 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-03 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-04 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-05 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-10 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-04-11 | 535 | 120 | only 535/775 bars; gap of 120 min |
| 2023-04-12 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-04-13 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-14 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-17 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-18 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-19 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-20 | 535 | 120 | only 535/775 bars; gap of 120 min |
| 2023-04-21 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-04-24 | 475 | 180 | only 475/775 bars; gap of 180 min |
| 2023-04-25 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-26 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-04-27 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-04-28 | 480 | 180 | only 480/775 bars; gap of 180 min |
| 2023-05-01 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-05-02 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-05-03 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-04 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-05 | 420 | 60 | only 420/775 bars; gap of 60 min |
| 2023-05-08 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-09 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-05-10 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-11 | 535 | 60 | only 535/775 bars; gap of 60 min |
| 2023-05-12 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-05-15 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-16 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-17 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-05-18 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-05-19 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-22 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-05-23 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-24 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-25 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-05-26 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-05-29 | 419 | 176 | only 419/775 bars; gap of 176 min |
| 2023-05-30 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-05-31 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-01 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-02 | 535 | 120 | only 535/775 bars; gap of 120 min |
| 2023-06-05 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-06 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-07 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-08 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-06-09 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-06-12 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-06-13 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-06-14 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-15 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-06-16 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-19 | 360 | 235 | only 360/775 bars; gap of 235 min |
| 2023-06-20 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-21 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-22 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-06-23 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-26 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-06-27 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-06-28 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-29 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-06-30 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-07-03 | 374 | 161 | only 374/775 bars; gap of 161 min |
| 2023-07-05 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-07-06 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-07-07 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-07-10 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-11 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-12 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-13 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-14 | 475 | 60 | only 475/775 bars; gap of 60 min |
| 2023-07-17 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-07-18 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-07-19 | 535 | 60 | only 535/775 bars; gap of 60 min |
| 2023-07-20 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-21 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-07-24 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-07-25 | 475 | 120 | only 475/775 bars; gap of 120 min |
| 2023-07-26 | 480 | 60 | only 480/775 bars; gap of 60 min |
| 2023-07-27 | 477 | 120 | only 477/775 bars; gap of 120 min |
| 2023-07-28 | 480 | 120 | only 480/775 bars; gap of 120 min |
| 2023-09-04 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2023-09-14 | 764 | 10 | only 764/775 bars; gap of 10 min |
| 2023-09-25 | 721 | 54 | only 721/775 bars; gap of 54 min |
| 2023-11-23 | 539 | 236 | only 539/775 bars; gap of 236 min |
| 2023-11-24 | 554 | 221 | only 554/775 bars; gap of 221 min |
| 2024-01-15 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2024-02-19 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2024-03-07 | 767 | 8 | gap of 8 min |
| 2024-05-27 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2024-06-19 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2024-07-03 | 615 | 160 | only 615/775 bars; gap of 160 min |
| 2024-07-04 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2024-07-19 | 619 | 91 | only 619/775 bars; gap of 91 min |
| 2024-08-12 | 746 | 29 | only 746/775 bars; gap of 29 min |
| 2024-08-26 | 769 | 6 | gap of 6 min |
| 2024-09-02 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2024-10-24 | 540 | 235 | only 540/775 bars; gap of 235 min |
| 2024-10-28 | 600 | 175 | only 600/775 bars; gap of 175 min |
| 2024-11-14 | 540 | 180 | only 540/775 bars; gap of 180 min |
| 2024-11-28 | 599 | 176 | only 599/775 bars; gap of 176 min |
| 2024-11-29 | 614 | 161 | only 614/775 bars; gap of 161 min |
| 2024-12-24 | 606 | 161 | only 606/775 bars; gap of 161 min |
