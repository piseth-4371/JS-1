# Buy the drop (daily mean reversion) — rules written before any result

Written 2026-11-21, before any result of this idea was computed. Owner request: "1: Buy the drop" (the ONE new
idea allowed by the unfreeze, `CLAUDE.md` section 2a).

## Question
Does buying the Nasdaq at the close of a day that ends at its **lowest close of the last 10 trading days**, and
selling **5 trading days later**, earn more than buying on random days, after Exness-like costs, in both
1971-1999 and 2000-2024?

## Why it might work (the reason, not a chart pattern)
After a fast fall some sellers are forced, not choosing: margin calls, funds that must cut risk when volatility
jumps, and nervous people selling at any price. Buyers who can wait are paid to take the other side, so part of the
fall tends to bounce back within days. Short-term reversal in stock indexes is widely documented (for example
Lehmann 1990; Lo & MacKinlay 1990; Connors & Alvarez 2009 popularised "buy a 10-day low" style rules). Because it is
well known and fast traders now do it, the effect may be smaller or gone since 2000; the validation period tests
that. It can also fail badly in crashes, when a fall keeps going.

## Disclosure
This is evaluation **54** in this project (53 so far, 0 passes, `docs/experiment_journal.md`). The same FRED file
was used before for monthly returns (E17) and for the turn-of-month window and its random-timing control (E19).
Daily returns were therefore seen in aggregate, but no number about returns after a 10-day low, or after any drop,
has been computed in this project. The rule below is the textbook form, chosen before looking.

## Pre-mortem (required, written before any result)
1. **Crashes:** in 2000-2002 and 2008 the rule keeps buying new lows while prices keep falling, and those losses
   make the validation period negative.
2. **It does not beat random timing:** the market rose most of the time, so any 5-day long trade looks good; the
   "bounce" is just normal drift and the rule stays below the 95th percentile of random holds.
3. **Costs and fading:** the bounce is smaller since 2000, and about 7 nights of 7%/yr financing (~0.13% per trade)
   plus the spread eat what is left.

## Data
- FRED `NASDAQCOM` (Nasdaq Composite, daily close), `backend/data/external/fred/NASDAQCOM.csv`,
  1971-02-05 to 2024-12-31, read with `multimarket_trend.read_fred` (blank or "." days dropped, never filled;
  2025+ refused). A **trading day** is a date with a value.
- Nasdaq **Composite**, not the Nasdaq-100 you would trade. Price index only, no dividends.
- **Development: 1971-1999. Validation: 2000-2024.** A trade belongs to the period (and year) of its entry date.
  A trade whose exit would fall in the next period, or after 2024-12-31, is dropped.
- 2025 and later stay locked (the out-of-sample test is run ONCE, only after a pass, with separate approval).

## The rule (fixed; no other setting will be tried)
- **Signal:** today's close is the lowest close of the last **10** trading days (today included; strictly lower
  than each of the previous 9 closes). The first 9 trading days of the file cannot signal.
- **Entry:** buy at that same close. **Exit:** sell at the close **5** trading days later. Always long.
- **One position at a time:** signals while a trade is open are ignored. A new trade can start on the exit day's
  close only if that day is itself a signal.
- No stop, no target, no other filter. (A paper version would need a stop for the engine's risk rules; that is a
  separate decision after a pass, not part of this test.)
- Free settings = **2** (lookback 10, holding 5 days).

## Costs (charged on every trade)
- Same as E19, so results are comparable: **spread 0.02%** of price per round trip (Exness `USTEC` median 2.94
  points, about 0.015% at today's level, rounded up) and **financing 7% a year** for each **calendar night** held.
- Net return per trade = price return − 0.02% − 7% × nights / 365.
- **Stress:** both costs doubled (0.04% and 14% a year).

## Benchmarks
1. **Random timing (the main control):** 5,000 runs (seed 11). Each run takes, in the same period, the same number
   of trades, each a 5-trading-day hold starting on a random trading day, with the same cost formula. The rule
   beats random timing if its average net return is above the 95th percentile of the random runs' averages.
2. **Always invested (information only):** average 5-day net return over all start days in the period.

## Statistics
- 95% interval for the average net return per trade: **calendar-year block bootstrap** (years resampled with
  replacement, 5,000 runs, seed 11). One test, so no family widening.
- Also shown (information only): win rate, worst trade, and the worst calendar year.

## Year-by-year check (required in every test)
Code: `app/backtest/yearly.py` (`by_year`, `year_check`), unit % per trade. Fixed rules:
- A year **counts** only if it has at least **10** trades; fewer = "too few trades", ignored below.
- **Most years positive:** in EACH period, the average net return per trade is above 0 in MORE THAN HALF of the
  counting years.
- **Not one lucky year:** in EACH period, the total net return with its single best year removed stays above 0.
- Fewer than **2** counting years in a period = the check cannot pass.
- Failing this check alone makes the result **inconclusive**, never a pass.

## Nearby-settings check (required in every test)
Code: `app/backtest/nearby.py` (`nearby_check`, `table`). Neighbours, fixed now:
- **Lookback:** chosen 10, neighbours **7** and **13**.
- **Holding days:** chosen 5, neighbours **4** and **6**.
- One setting changed at a time, other at its chosen value, same period, normal costs: 4 extra runs per period.
- **Plateau:** in EACH period at least 2/3 of the 4 neighbours (3 of 4) average above 0.
- **Not a spike:** in EACH period the chosen average is at most 2× the median neighbour average (median above 0).
- A neighbour can **never** replace the chosen setting. Failing this check alone = **inconclusive**.

## Verdict (fixed now)
**Passes the research criteria** only if, in BOTH development and validation:
- at least 30 trades,
- average net return per trade > 0, and > 0 under stress costs,
- bootstrap lower bound > 0,
- above the 95th percentile of random timing,
- the year-by-year check passes,
- the nearby-settings check passes.

**Negative observed result** = average net return ≤ 0 in either period. **Inconclusive** = anything else.
A pass is a reason for a paper-only forward test on MT5 `USTEC` (with the Exness cost gate and a real swap check),
not for real money. Nothing here changes `scanner.QUALIFIED`, a strategy or a risk limit.
Under `CLAUDE.md` 2a, a fail or inconclusive result re-freezes the project.

## Limits
- Composite, not Nasdaq-100; dividends ignored.
- Signal and entry use the same close: in real trading you would have to act a few minutes before the close, at a
  slightly different price. No slippage at the close is charged.
- The 7% financing and 0.02% spread are today's assumptions; costs in the 1970s-90s were much higher, so the old
  period is easier than reality would have been.
- No stop: single trades can lose a lot in a crash (the worst trade is reported).

## After the result
- Report: `docs/buy_the_drop_report.md` with every number above, the year-by-year and nearby-settings tables,
  failures included, and a "Pre-mortem check" line per reason: happened / did not happen / cannot tell.
- Update the journal entry, run `scripts/experiment_journal.py` and `--check`, add a row to `docs/decisions.md`
  and a line to CLAUDE.md section 11.
- Do not re-run with other settings after seeing the result (that is curve fitting).
