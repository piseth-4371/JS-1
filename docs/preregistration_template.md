# <Name of the idea> — rules written before any result

<!--
TEMPLATE. Copy to docs/<idea>_preregistration.md, fill in every <...>, delete these comments, and COMMIT it before
running anything. Then add an "incomplete" entry to docs/experiments.json with the commit hash (CLAUDE.md, section 11:
experiment journal). After the run, update that entry, also when it fails. Never change this file after a result.
Wording: short sentences, plain English, numbers fixed in advance. If a rule cannot be fixed now, the test is not ready.
-->

Written <YYYY-MM-DD>, before any result of this idea was computed. Owner request: "<quote>".

## Question
<One sentence: does <rule> on <market> earn more than <control>, after <costs>, in both development and validation?>

## Why it might work (the reason, not a chart pattern)
<Who is on the other side of the trade and why they keep doing it. Cite sources if any. Say why it may have stopped.>

## Disclosure
This is evaluation **<N>** in this project (<N-1> so far, <P> passes, `docs/experiment_journal.md`).
<Has any of this data or a similar rule been looked at before? Say exactly what was seen.>

## Data
- <Source, symbol, timeframe, file or table, date range, how gaps are handled (never filled).>
- **Development: <2019-2022>. Validation: <2023-2024>.** A trade belongs to the period (and year) of its entry time
  in New York time.
- 2025 and later stay locked (the out-of-sample test is run ONCE, only after a pass).

## The rule (fixed; no other setting will be tried)
- <Entry, exit, stop, target, time limits, filters. Every number written here.>
- <Number of settings that could have been chosen differently = <k>. Keep it small.>

## Costs (charged on every trade)
- <Spread, slippage, commission, financing.> NAS100: use the Exness cost gate too
  (`docs/exness_cost_gate_preregistration.md`: 2.94-point spread, p90 stress 3.29 / 3.65).
- **Stress:** <costs doubled, or the p90 costs>.

## Benchmarks
1. **Random timing (the main control):** 5,000 runs (seed 11), same number of trades and same holding time on random
   start times in the same period, same costs. Beats random if its average net result is above the 95th percentile.
2. <Any information-only comparison.>

## Statistics
- 95% interval for the average net result per trade: <bootstrap type, runs, seed>.
- <Family widening if several variants are tested at once (Bonferroni), or "one test, no widening".>

## Year-by-year check (required in every test)
Code: `app/backtest/yearly.py` (`by_year`, `year_check`). Shown as a table per period: year, trades, average net
result per trade, total net result. Fixed rules:
- A year **counts** only if it has at least **10** trades. Years with fewer are shown as "too few trades" and are
  ignored by the two checks below.
- **Most years positive:** in EACH period, the average net result per trade must be above 0 in MORE THAN HALF of
  the counting years (development with 4 counting years: at least 3; validation with 2: both).
- **Not one lucky year:** in EACH period, the total net result with its single best year removed must still be
  above 0.
- If a period has fewer than **2** counting years, the check cannot be passed ("not enough years").
- Failing this check alone makes the result **inconclusive**, never a pass. It never turns a fail into anything better.

## Nearby-settings check (required in every test)
Code: `app/backtest/nearby.py` (`nearby_check`, `table`). A real effect should survive small changes to its numbers
(a plateau); a result that only exists at the exact chosen value (a spike) is probably luck.
- For EACH setting counted in "The rule" (the <k> numbers that could have been chosen differently), write here one
  **smaller** and one **larger** neighbour value, fixed now (the next natural step, or about 25% away):
  - <setting 1: chosen X, neighbours A and B>
  - <setting 2: chosen Y, neighbours C and D>
- Each neighbour is run with every other setting at its chosen value, in the same period, with the same normal
  costs. One setting at a time, so 2 × <k> extra runs per period.
- **Plateau:** in EACH period, at least **2/3** of the neighbour runs (rounded up) must have an average net result
  per trade above 0.
- **Not a spike:** in EACH period, the chosen setting's average may be at most **2×** the median neighbour average
  (and that median must be above 0).
- Neighbour runs are a robustness check only. A neighbour can **never** replace the chosen setting, even if it looks
  better (that would be curve fitting). They are shown in the report, not counted as new strategies.
- If the rule has no free settings (k = 0), write "not applicable" and the reason.
- Failing this check alone makes the result **inconclusive**, never a pass. It never turns a fail into anything better.

## Verdict (fixed now)
**Passes the research criteria** only if, in BOTH development and validation:
- at least <30> trades,
- average net result per trade > 0, and > 0 under stress costs,
- bootstrap lower bound > 0,
- above the 95th percentile of random timing,
- the year-by-year check passes,
- the nearby-settings check passes (or is not applicable).

**Negative observed result** = average net result ≤ 0 in either period. **Inconclusive** = anything else.
A pass is a reason for a paper-only forward test (and, for NAS100, the Exness cost gate), not for real money.
Nothing here changes `scanner.QUALIFIED`, a strategy or a risk limit until all of that has passed.

## Limits
- <Data source is not the broker's prices, clock issues, missing hours, assumptions about costs, small samples.>

## After the result
- Report: `docs/<idea>_report.md` with every number above, the year-by-year and nearby-settings tables
  included, failures included.
- Update the journal entry (`outcome`: pass / fail / inconclusive), run `scripts/experiment_journal.py` and
  `--check`, add a row to `docs/decisions.md` and a line to CLAUDE.md section 11.
- Do not re-run with other settings after seeing the result (that is curve fitting).
