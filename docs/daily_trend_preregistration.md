# Daily trend research — rules fixed BEFORE testing (2026-11-14)

Why: every intraday strategy failed because costs (2 points) are large compared with small intraday stops.
Multi-day trend trades have stops of hundreds of points, so the same cost is tiny in R.
This is **research only**: it is not wired into the live engine (it holds positions overnight,
which the current NAS100 book does not allow). Nothing here changes the core rules.

## Data
HistData NSXUSD 1-minute bars → daily bars. A trading day runs 18:00 → 17:00 New York time
(the futures/CFD day); the daily close is the last bar before 17:00 NY.
Splits: development 2019–2022, validation 2023–2024 (by entry date). 2025+ stays locked.
The first 100 trading days of 2019 are warm-up only (indicators need history).

## Strategy A — `sma100_long` (long only)
- Signal: daily close > 100-day simple moving average → be long; close < SMA100 → exit.
- Entry/exit at the NEXT day's open (no same-bar look-ahead).
- Stop-loss (mandatory): entry − 2 × ATR(20) at entry, fixed.

## Strategy B — `donchian_55_20` (long and short)
- Long when the close is above the highest high of the previous 55 days; short when below the lowest low.
- Exit long when the close is below the lowest low of the previous 20 days (short: mirror).
- Entry/exit at the next day's open. Stop-loss: 2 × ATR(20) from entry, fixed.

## Costs [assumptions]
- 2.0 points per round trip (same as the intraday tests).
- Overnight financing (swap): 5% per year of the position's value, charged for every calendar day held,
  on longs AND shorts. Exness' real USTEC swap was not checked; the test is also shown at 0% and 10%.

## Pass rule (all must hold, in BOTH development and validation)
1. Average R per trade > 0 after costs and financing.
2. Better than the **random-timing control**: same side, same holding length and same stop, but random entry days
   (500 runs). The strategy must beat the control's average in ≥ 90% of the runs. This matters because the Nasdaq
   rose strongly in 2019–2024: almost any long trade made money, so beating "being long at random" is the real test.
3. At least 20 trades per split.
If a strategy fails, it fails — no parameter changes afterwards.
