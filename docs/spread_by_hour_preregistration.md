# Broker spread by time of day (pre-registered 2026-11-17)

Written and committed BEFORE any MT5 spread history was analysed by hour.
**Measurement only.** It changes no strategy, cost setting, backtest or `scanner.QUALIFIED` (stays empty).
The research pause stays in force.

## Why
The bid/ask re-test (`docs/bidask_retest_report.md`) found Dukascopy's quoted spread is ~1.45 pts during US
hours but ~3 pts before 09:30 New York. Backtests assume 1.5 pts all day. Does the broker feed we actually use
show the same pattern?

## Data
- MT5 terminal, account **MetaQuotes-Demo** (demo), symbol `USTEC`, 1-minute bars, the `spread` field × `point`.
  This is MetaQuotes' demo feed, **not Exness**; the Exness spread is still unknown.
- All history the terminal returns (up to 99,000 closed bars), weekdays only, New York time 03:00–15:55
  (the strategies' holding window). Bars converted from server time with `mt5_server_tz` as elsewhere.
- Each run adds its bars to `data/reports/mt5_spreads.csv` (one row per minute, duplicates dropped), so re-running
  later extends the sample. Nothing is filled in.
- Known limitation, stated now: MT5 does not document whether the bar `spread` is the minimum, last or average
  spread in that minute; many servers store the minimum. It may therefore **understate** the spread paid.

## Reported
Per New York hour (03..15): minutes, median, p90 spread. Per window: **pre-US 03:00–09:29** and **US 09:30–15:54**:
minutes, trading days, median, p90.

## Decision rules (fixed now)
For each window, against the backtest assumption of 1.5 pts:
- median ≤ 1.5 → "1.5 assumption holds on this feed" (weak evidence, because of the minimum-spread limitation);
- median > 1.5 → "1.5 assumption understated on this feed".
- Same pattern as Dukascopy if the pre-US median is ≥ 1.5 × the US median.
- Fewer than 10 trading days in a window → "not enough data", no verdict.
- Whatever the result: no automatic change to costs, backtests or qualification. A changed cost assumption would
  need its own owner decision and re-run, recorded in `docs/decisions.md`.
