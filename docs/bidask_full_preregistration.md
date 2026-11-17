# Bid/ask re-test of the 7 NAS100 strategies, 2019–2024 (pre-registered 2026-11-17)

Written and committed BEFORE any 2019–2022 or 2024 bid/ask result was computed.
**Measurement re-test, not new strategy research.** The research pause stays in force.

## Honest disclosure (read first)
- These are **not fresh out-of-sample results.** All 7 strategies were already backtested on 2019–2024
  (HistData, bid-only; `docs/report_card.md`) and all failed. 2023 was already re-tested on Dukascopy bid/ask
  (`docs/bidask_retest_report.md`; silver_bullet +0.32R, range crossing 0). 36 strategy versions/filters were
  tested in this project in total (`docs/lessons.md`, `docs/decisions.md`).
- Because the data has been seen, **passing this re-test can only make a strategy eligible for a separately
  authorised final evaluation on the locked 2025+ data.** It does not add it to `scanner.QUALIFIED` and does not
  qualify anything for live trading. 2025+ is not loaded or touched by this work.
- Silver Bullet's positive 2023 result is treated as **unproven** and gets no special treatment.

## Data
- Dukascopy `USATECHIDXUSD` 1-minute **BID and ASK**, 2018-12-01 .. 2024-12-31 (December 2018 = warm-up only).
  Only minutes with BOTH quotes are used; nothing is filled in; no synthetic ask is substituted for a missing real ask.
- Splits unchanged: **development 2019–2022, validation 2023–2024** (trade's New York date).
- Session rule unchanged (`docs/data_quality_rule.md`): 03:00–15:55 NY needs ≥ 765/775 joined minutes and no hole
  > 5 min; new orders only on valid sessions.
- Strategy rules, parameters, risk settings, news blackout, 15:55 flat rule: unchanged. Volume set to 0 (same
  plain-average "VWAP" as all earlier NAS100 backtests).
- **Coverage requirement:** a split gets a verdict only if ≥ 90% of its New York weekdays have joined bid+ask
  data. Otherwise that strategy is reported **"incomplete data — no verdict"** and the missing period is listed.
  An incomplete run is never called complete.

## Data checks (reported, not used to choose anything)
1. Minutes with ask < bid (expected 0).
2. Clock / daylight saving: for each year, in US-summer and US-winter weeks separately (and the US/UK mismatch
   weeks), the New York minute with the largest median |1-minute move| must be 09:30. Any other answer = the
   clock is wrong and the run stops.
3. Second source: Dukascopy bid close vs HistData close on shared minutes, median |difference| per year.
4. Coverage per year: weekdays with data, valid sessions, missing days listed by month.

## Models (each run on valid sessions)
| id | prices | spread | slippage | fees | use |
|---|---|---|---|---|---|
| G gross | BID only | 0 | 0 | 0 | gross expectancy |
| B bid-only | BID only | 1.5 subtracted | 0.5 | 0 | cost effect on identical trades |
| **R real** | buys on ASK, sells on BID | 0 (in prices) | 0.5 | 0 | **primary result** |
| S stress | buys on ASK, sells on BID | +0.5 extra | 1.0 | 0 | cost stress, fixed now |

Fees: 0 (Exness Standard CFD has no commission; no swap because every position is closed the same day by 15:55 NY).
Slippage: 0.5 pt on market/stop entries and stop/forced exits, as in every earlier test.

## Reported per strategy × year and per split (model R unless stated)
Trades, win rate (historical share, not a probability), average winner and loser (R), gross expectancy (G),
spread cost and slippage cost and fees (R per trade), net expectancy (B and R), profit factor, max drawdown at
0.5% risk.

**Reconciliation:**
- Identical trades (B vs G): per trade, `net = gross − spread/risk − slippage/risk − fees`; must reconcile to
  < 1e-9 R. G and B can take different trades (losses trigger the 2-loss / daily-loss stops), so this is done on
  trades matched by entry time and side; unmatched trades are counted separately.
- Fill model (R vs B): total R of R minus total R of B = (sum of differences on matched trades) + (R-only trades)
  − (B-only trades); must reconcile exactly. Matched-trade difference = real quoted spread vs 1.5 + trigger
  timing on the ask; the other two = trades that fill (or not) because of the ask.

## Statistics
- 95% interval for the average R: **whole-week block bootstrap** (ISO weeks resampled with replacement, 5,000
  resamples, seed 11). Assumes weeks are independent of each other; ignores longer regimes (e.g. a whole bull
  year); few trades per week → wide, unstable intervals.
- **Family adjustment for 7 strategies:** Bonferroni two-sided α = 0.05/7 → percentiles 0.357 and 99.643 of the
  same bootstrap ("family 95% interval"). The 36 earlier tests are disclosed above but not in this correction,
  which makes the bar *lower* than a full correction would — another reason a pass is only "eligible".

## Verdicts (fixed now; model R, each split separately)
- **Passes the research criteria** = in BOTH dev and validation: ≥ 30 trades, average R > 0, family-interval lower
  bound > 0, and stress model S average R > 0.
- **Negative observed expectancy** = average R ≤ 0 in dev or in validation.
- **Inconclusive** = neither of the above.
- **Incomplete data — no verdict** = coverage requirement not met.
No setting, year, filter or session is chosen after seeing results. Nothing here changes `scanner.QUALIFIED`.

## Amendment 1 (2026-11-17, before any strategy result was computed)
Data check 2 as written stopped the first run: in the 15 US/UK-mismatch weekdays of 2023 the minute with the
largest median move was 09:56, not 09:30. Inspection (no strategy run had happened): the median 1-minute move jumps
from 3.58 at 09:29 to 9.15 at 09:30, while 08:30 = 4.55 and 10:30 = 5.08. A one-hour clock error would put the jump
at 08:30 or 10:30, so the clock is right; March 2023 (US banking stress) made the whole first half hour volatile and
one later minute won by chance. The single-top-minute rule is too fragile for ~15-day samples. **Replacement rule,
which tests the real failure (a DST hour shift):** per year and regime, median move at 09:30 ≥ 1.5 × the median at
09:29, and greater than the medians at 08:30 and 10:30. The top minute is still reported for information.
