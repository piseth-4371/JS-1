# Turn of the month — rules written before any result

Written 2026-11-19, before any turn-of-month return was computed. Owner request: "do it now" (our own strategy with
a real reason, holding days not minutes so the spread matters less).

## Question
Does holding the Nasdaq over the turn of each month earn more than holding it on random days, after Exness-like
costs, both in older data and in the 25 years after the effect became well known?

## Why it might work (the reason, not a chart pattern)
Pension contributions, salaries and fund rebalancing put new money into stocks around month ends. Published studies
(Ariel 1987; Lakonishok & Smidt 1988) found most of the US stock return came on the last trading day and the first
three trading days of the month. Because it is published and famous, it may have disappeared — that is what the
validation period tests.

## Disclosure
This is evaluation **53** in this project (52 so far, 0 passes, `docs/experiment_journal.md`). The same FRED file
was used before only for monthly returns (E17), never by day of month. No turn-of-month number has been looked at.

## Data
- FRED `NASDAQCOM` (Nasdaq Composite, daily close), already in `backend/data/external/fred/` (downloaded for E17),
  1971-02-05 to 2024-12-31, read with `multimarket_trend.read_fred` (blank or "." days dropped, never filled;
  2025+ refused). A **trading day** is a date with a value.
- It is the Nasdaq **Composite**, not the Nasdaq-100 you would trade (the Nasdaq-100 only starts in 1986 and is not
  downloaded). They move closely together, but the result is about the Composite. Price index only: no dividends.
- **Development: 1971-1999. Validation: 2000-2024.** A trade belongs to the period of its entry date.
- 2025 and later stay locked.

## The rule (fixed; no other day count or month will be tried)
- **Buy** at the close of the **second-to-last** trading day of the month, **sell** at the close of the **third**
  trading day of the next month. So the trade earns the daily returns of the last day and the first three days
  (4 trading days), the standard window.
- One trade per month, always long. The first month (Feb 1971) is skipped if its window is incomplete, and so is
  any trade whose exit would be after 2024-12-31.

## Costs (Exness-like, charged on every trade)
- **Spread:** 0.02% of price per round trip (Exness median 2.94 points ≈ 0.015% at today's ~20,000 level, rounded up).
- **Overnight financing:** 7% a year on the position for each **calendar night** held (Exness charges a swap on
  CFDs held overnight; the exact rate changes, so 7% is an assumption).
- **Stress:** both costs doubled (0.04% and 14% a year).
- Net return per trade = price return − spread − 7% × nights / 365.

## Benchmarks
1. **Random timing (the main control):** 5,000 runs (seed 11). Each run takes, in the same period, the same number of
   trades, each a 4-trading-day hold starting on a random trading day, with the same cost formula. The rule beats
   random timing if its average net return is above the 95th percentile of the random runs' averages.
2. **Always invested (information only):** average daily return of all days vs the 4 turn-of-month days.

## Statistics
- 95% interval for the average net return per trade: **12-month block bootstrap** (calendar years resampled with
  replacement, 5,000 runs, seed 11). One test, so no family widening.

## Verdict (fixed now)
**Passes the research criteria** only if, in BOTH development and validation:
- at least 30 trades,
- average net return per trade > 0,
- bootstrap lower bound > 0,
- above the 95th percentile of random timing,
- stress average net return > 0.

**Negative observed result** = average net return ≤ 0 in either period. **Inconclusive** = anything else.
A pass would be a reason for a paper-only forward test, not for real money, and would still need a check on the
traded Nasdaq-100 CFD and its real swap rate. Nothing here changes `scanner.QUALIFIED`, a strategy or a risk limit.

## Limits
- Composite, not Nasdaq-100; close prices, no slippage at the close; dividends ignored.
- The 7% swap and 0.02% spread are assumptions for today's account; costs in the 1970s-90s were much higher, so
  the old period is easier than reality would have been.
- About 12 trades a year: individual years are noisy.
