# Volatility regime filter — rules fixed BEFORE testing (2026-11-16)

## Why this idea
From the report card (`report_card.md`) and the book *Quantitative Finance From Scratch* (ch 7 volatility,
ch 16 fat tails): two plausible reasons the intraday strategies lose are
- **calm days**: small stops, so the fixed 2-point cost is a large share of risk (Lesson 1), and
- **wild days**: fat-tail jumps hit or gap through stops.
If that is true, trading only on "normal" volatility days should raise the average R.

Prior expectation: **probably fails.** The similar cost filter helped on early data and failed on the full
period (`cost_filter_report.md`, Lesson 2). A filter only removes trades; it cannot create an edge that the
rule does not have. We test it once, honestly.

Different from what exists: `trend_fvg` already skips 5-minute ATR outside its 10th–95th percentile of the last
~20 days (intraday noise). This filter uses **day-level** volatility over a one-year window (market regime).

Research only: not connected to the live engine or the scanner. No core rule changes.

## Data
HistData NSXUSD 1-minute bars 2019–2024, New York time. Development 2019–2022, validation 2023–2024
(by trade date). 2025+ stays locked. Same engine, costs (1.5 spread + 0.5 slippage) and risk settings as
`run_backtest.py`.

## Measure (causal: only days BEFORE the trade date)
1. **Daily close** = close of the last 1-minute bar before 16:00 New York on each weekday that has bars.
2. **Daily log return** = ln(close / previous daily close).
3. **Realized volatility** for trade date D = standard deviation of the last 20 daily log returns before D
   (needs at least 15 of them).
4. **Percentile** = rank of that volatility among the realized-volatility readings of the previous
   250 trading days (needs at least 120 readings).

## Filter — `volatility_regime`
- Keep a trade only if the trade date's volatility percentile is **between 20 and 80** (inclusive).
- Below 20 = "calm", above 80 = "wild": the order is skipped (counted and reported).
- Not enough history (start of 2019) = skipped and reported.
- Applied as a wrapper around each of the 7 NAS100 strategies: trend_fvg, sweep_mss_fvg, orb, vwap_reversion,
  silver_bullet, london_trend_fvg, london_sweep_mss_fvg. Their own rules stay unchanged.

## Pass rule (a strategy passes only if ALL hold in BOTH development and validation)
1. Filtered average R per trade **> 0** after costs.
2. Enough trades: **≥ 100** filtered trades in development, **≥ 50** in validation.
3. Luck check: bootstrap chance of no edge (`p_no_edge`, as in `robustness.py`) **≤ 10%**.
4. The filter itself helps: filtered average R **> unfiltered** average R.
5. Not just fewer trades: beats a **random-skip control** (remove the same number of trades at random,
   500 runs, seed 7) in **≥ 90%** of runs.

Multiple testing: 7 strategies are tested, so one could pass rule 1 by luck. That is why rules 3–5 must hold
in both periods. If no strategy passes, the answer is "no" — **no changes to 20/80, 20 days or 250 days
afterwards.** Reported for information only (not part of the verdict): average R of the skipped calm and wild
trades.

## If something passes
It is still NOT added to `scanner.QUALIFIED` automatically. Next step would be a written decision by the owner,
then the locked 2025+ test, run once.
