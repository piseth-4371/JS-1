# Exness vs Dukascopy spread, 2023 — results

Made by `scripts/exness_spread_check.py` on 2026-11-19. Rules were committed before the file was downloaded (`docs/exness_spread_check_preregistration.md`). Measurement only: no strategy was run and no cost, backtest or qualification setting changed.

**File usable under the rules: YES.**

## What the words mean

- **Spread:** ask minus bid, in index points. You pay it when you enter and exit a trade.
- **Median:** the middle value. Half of the minutes were lower and half were higher.
- **p90:** 90% of the minutes were at or below this value, so it shows the expensive moments.

## File checks

| check | result | value |
|---|---|---|
| Coverage: valid weekdays >= 90% | PASS | 94.2% |
| Clock: correlation peaks at lag 0 in all 3 periods | PASS | see table |
| Price level: median gap <= 10 points | PASS | 7.98 points |
| Bad ticks <= 0.1% | PASS | 0 of 12,701,245 (0.0000%) |

### Clock check (correlation of 1-minute price changes; lag in minutes)

| period | -2 | -1 | +0 | +1 | +2 | best |
|---|---:|---:|---:|---:|---:|---:|
| before US DST | -0.009 | 0.011 | 0.995 | 0.010 | -0.012 | +0 |
| US DST | -0.000 | -0.006 | 0.994 | -0.008 | 0.001 | +0 |
| after US DST | -0.009 | 0.006 | 0.993 | 0.003 | -0.007 | +0 |

### Valid sessions by month

| month | weekdays | valid |
|---:|---:|---:|
| 1 | 22 | 20 |
| 2 | 20 | 18 |
| 3 | 23 | 23 |
| 4 | 20 | 18 |
| 5 | 23 | 22 |
| 6 | 22 | 21 |
| 7 | 21 | 19 |
| 8 | 23 | 23 |
| 9 | 21 | 20 |
| 10 | 22 | 22 |
| 11 | 22 | 19 |
| 12 | 21 | 20 |

## Spread (minutes present in both sources)

| window | minutes | days | Exness median | Exness p90 | Dukascopy median | Dukascopy p90 | ratio | vs 1.5 | vs Dukascopy |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| pre-US 03:00-09:29 | 100,158 | 257 | 2.95 | 3.22 | 3.45 | 3.53 | 0.85 | 1.5 assumption understated | similar |
| US 09:30-15:54 | 96,994 | 256 | 2.93 | 3.39 | 1.45 | 1.52 | 2.02 | 1.5 assumption understated | Exness more expensive |

## By New York hour

| hour | minutes | Exness median | Exness p90 | Dukascopy median | Dukascopy p90 |
|---:|---:|---:|---:|---:|---:|
| 03:00 | 15,399 | 3.01 | 3.23 | 3.45 | 3.52 |
| 04:00 | 15,420 | 2.73 | 3.22 | 3.46 | 3.53 |
| 05:00 | 15,418 | 2.72 | 3.18 | 3.46 | 3.53 |
| 06:00 | 15,419 | 2.76 | 3.20 | 3.45 | 3.53 |
| 07:00 | 15,420 | 2.79 | 3.21 | 3.45 | 3.52 |
| 08:00 | 15,394 | 2.98 | 3.30 | 3.45 | 3.53 |
| 09:00 | 15,367 | 3.00 | 3.56 | 1.95 | 3.50 |
| 10:00 | 15,352 | 2.98 | 3.50 | 1.45 | 1.52 |
| 11:00 | 15,307 | 2.89 | 3.34 | 1.45 | 1.52 |
| 12:00 | 15,246 | 2.82 | 3.26 | 1.45 | 1.52 |
| 13:00 | 14,894 | 2.88 | 3.27 | 1.45 | 1.52 |
| 14:00 | 14,879 | 2.93 | 3.32 | 1.45 | 1.52 |
| 15:00 | 13,637 | 2.92 | 3.32 | 1.45 | 1.52 |

## Limits

- This is the archive's `USTEC` instrument. Other account types (`USTECm`, `USTECc`, Raw Spread, Zero) can differ, and any commission is not in the spread.
- It shows the spread at the last tick of each minute, not the price of any actual order.
- Exness history starts in August 2019, so it cannot meet the 90% coverage rule for 2019-2022 by itself.
- It says nothing about whether a strategy makes money.
