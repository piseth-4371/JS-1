# Broker spread by time of day — results

Made by `scripts/spread_by_hour.py` on 2026-11-17. Rules fixed in `docs/spread_by_hour_preregistration.md` before the analysis. Measurement only: no cost, backtest or qualification change.

## Data

- MetaQuotes-Demo `USTEC` 1-minute bar `spread` field, New York dates 2026-08-07 .. 2026-11-17 (weekdays, 03:00-15:55 NY): 55,783 minutes on 73 days.
- MetaQuotes demo feed, **not Exness**. The bar spread may be the minimum within the minute, so it can understate cost.
- Distribution check: max spread 1.00; 97% of minutes are exactly 0.90 or 1.00. A feed that never widens (not even at the open or news) looks fixed/capped or minimum-per-minute, so it cannot show the spread actually paid at busy moments.

## Pre-registered decisions (assumption 1.5 pts)

| window | minutes | days | median | p90 | verdict |
|---|---:|---:|---:|---:|---|
| pre-US 03:00-09:29 | 28,252 | 73 | 1.00 | 1.00 | 1.5 assumption holds on this feed |
| US 09:30-15:54 | 27,531 | 72 | 0.90 | 0.90 | 1.5 assumption holds on this feed |

**Same pattern as Dukascopy (pre-US much wider):** NO (pre-US median 1.00 < 1.5 x US median 0.90)

For comparison, Dukascopy 2023: pre-US ~3.0, US ~1.45 points (`docs/bidask_retest_report.md`).

## By New York hour

| hour | minutes | median | p90 |
|---:|---:|---:|---:|
| 03:00 | 4,379 | 1.00 | 1.00 |
| 04:00 | 4,380 | 1.00 | 1.00 |
| 05:00 | 4,380 | 1.00 | 1.00 |
| 06:00 | 4,320 | 1.00 | 1.00 |
| 07:00 | 4,320 | 1.00 | 1.00 |
| 08:00 | 4,313 | 1.00 | 1.00 |
| 09:00 | 4,317 | 0.90 | 1.00 |
| 10:00 | 4,317 | 0.90 | 0.90 |
| 11:00 | 4,319 | 0.90 | 0.90 |
| 12:00 | 4,319 | 0.90 | 0.90 |
| 13:00 | 4,260 | 0.90 | 0.90 |
| 14:00 | 4,257 | 0.90 | 0.90 |
| 15:00 | 3,902 | 0.90 | 0.90 |
