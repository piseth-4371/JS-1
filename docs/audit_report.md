# Measurement audit (2026-11-16)

Scope: data quality, backtest correctness, costs and statistics of the NAS100 research. No strategy, parameter,
entry/exit rule or risk limit was changed. 2025+ data was not loaded. `scanner.QUALIFIED` stays empty.
Paper-only operation, risk limits and the kill switch are untouched.

**Bottom line:** the backtest engine is mostly sound and reproducible (the re-run matches the saved
2019–2024 trades exactly). The audit found real measurement problems: missing data in 2023, a scanner rule
that differed from the engine, a bid-only fill model and misleading statistics labels. None of the corrected
numbers changes the conclusion. **No strategy has a demonstrated edge after costs.** Gross of all costs, every
strategy averages roughly −0.17R to +0.25R per trade, and no strategy is positive in both development and validation.

Numbers: `docs/audit_measurements.md` and `docs/data_quality_report.md` (both made by `scripts/audit_measurements.py`).
Rule fixed before the re-run: `docs/data_quality_rule.md` (commit 6664851).

## Findings, most severe first

| # | severity | finding | where | status |
|---|---|---|---|---|
| 1 | High | **2023 data is badly incomplete.** 119 of 256 weekdays fail the coverage rule; other years have 7–17 failures, mostly holidays. 2023 is half of the validation period, so earlier validation results rested on many partial days. 74 trades in 2019–2024 were held through a data hole longer than 5 minutes. Two london_trend_fvg trades lost an average of −6.4R because the stop was only checked after the hole. | data; `app/core/data_quality.py` | Made visible and excludable with a rule fixed in advance. No prices filled in. |
| 2 | High (for the planned paper-vs-backtest comparison) | **Scanner outcome tracking ignored `cancel_level`.** The engine (`app/backtest/engine.py:155`) and paper broker (`app/core/paper_broker.py:139`) cancel an unfilled order when a 5m bar closes beyond the FVG level. The scanner's `resolve` did not, so it recorded fills the other two would never take. | `app/core/scanner.py:196` (`resolve`) | **Fixed.** Old rows have `cancel_level` NULL and keep their recorded outcomes. |
| 3 | Medium–High | **Bid-only fill model.** HistData and MT5 bars are BID prices. A buy needs the ASK (bid + spread). Limit fills on touch (`app/core/fills.py:26`) and short stops/targets (`fills.py:55,57`) trigger on the bid. Short target exits where the bid reached the target but stayed within one spread of it: trend_fvg 6, sweep_mss_fvg 18, orb 17, vwap_reversion 183, silver_bullet 16, london_trend_fvg 26, london_sweep_mss_fvg 16. Each one that a real ask would have missed is an overstated win. Long limit fills that depended on such a touch were **not** systematically better than other long limit fills (mixed signs). | `app/core/fills.py` | Measured, not changed. A bid/ask model is a separate change (see "Next step"). |
| 4 | Medium | **Statistics labels overstated what the bootstrap means.** "Luck chance" and "chance the true edge is ≤ 0" are really the share of resampled averages ≤ 0 under an iid resample. That is not a probability that the strategy has, or lacks, an edge. | `app/backtest/report_card.py:109`, `app/backtest/robustness.py:102`, `scripts/report_card.py`, `scripts/robustness.py`, `scripts/vol_filter_test.py` | **Relabelled.** Pass/fail gates are unchanged. Every earlier verdict was FAIL and stays FAIL. |
| 5 | Medium | **Dependence and multiple testing were not accounted for.** CIs and the bootstrap treat trades as independent. Sharpe is annualised as per-trade Sharpe × √(trades/yr) (`report_card.py:134`). 36 strategy versions were tried with no family-wise adjustment. | `report_card.py:123`, `robustness.py:58,102` | **Added** a week-clustered bootstrap, a Bonferroni (36-test) lower bound, and documented caveats on Sharpe, Kelly (in-sample) and Monte Carlo (assumes exchangeable trades). The week-clustered ranges came out close to the iid ones, so within-week dependence is small here. |
| 6 | Medium | **Zero volume breaks VWAP.** All HistData bars have volume 0, so `session_vwap` falls back to a plain average of typical prices (`app/core/indicators.py:31`). Live MT5 uses tick volume, so the backtest "VWAP" and the live VWAP are different lines. This was partly known: decisions.md 2026-11-14 found vwap_reversion differs on Dukascopy volume. | `indicators.py:22-32` | Made visible in `docs/data_quality_report.md`. Behaviour not changed, because changing it would change the strategies. |
| 7 | Medium | **No holiday / early-close calendar.** `can_hold` is time-of-day only (`app/core/features.py:135-137`). On early-close days the data stops before 15:55, so 20 positions were closed at the next available bar, on a later day or after 15:55. Those exits ignore the closed market and charge no overnight financing. | `features.py:135` | Excluded by the valid-session rule (those days fail coverage). No calendar was added. |
| 8 | Low | **R uses the risk at the fill; the order was sized on the planned risk.** The engine and paper broker divide by fill risk (`engine.py:85,121`; `paper_broker.py:131,169`), while the scanner uses planned risk (`scanner.py:205`). Measured effect on average R is ≤ 0.002R (market orders only). | engine | `Trade.planned_risk_pts` now recorded; convention documented. |
| 9 | Low | **Remaining scanner/engine differences.** If a limit fills beyond its fixed target, the scanner marks the row `invalid`; the engine fills it and exits at the next bar. The scanner also keeps the target shown at publication even for market orders. | `scanner.py:240-247` | Documented, not changed. These are rare edge cases. |
| 10 | Low | **Costs: assumptions vs measurements.** The 1.5-pt spread and 0.5-pt slippage are assumptions. The only measured spread comes from the MetaQuotes-Demo USTEC feed (median 0.9, p90 1.0 pts; not Exness). Slippage and Exness spread/swap were never measured. No commission is modelled (Exness Standard assumption). The daily-trend financing `entry × rate × days / 365` (`app/backtest/daily_trend.py:32`) has consistent units and is charged once. No double counting was found: `net_points` charges the spread once per round trip and slippage once per market/stop leg. | `app/core/fills.py`, `daily_trend.py:32` | Stress test added (below). |

### Checked and found correct
- No duplicate timestamps and no impossible candles (high < low, open/close outside the range).
- HistData clock is UTC−4 during UK summer time, else UTC−5. Checked independently against 08:30 New York data-release spikes for 2019–2024, including the US/UK DST-mismatch weeks. No hour shifts.
- 5m bars are built only from complete 1-minute buckets (`features.py` `resample_complete`).
- 15m bias joins on the 15m bar close (`merge_asof` on `close_ts`, backward). Prior-day levels use `shift(1)`. Overnight levels are from the closed session. Strategies only see closed bars.
- Fills happen on later 1-minute bars. The stop is checked before the target. On the fill minute only the stop counts. Gaps fill at the worse open for stops and the better open for limits. Orders expire at `expiry_ts`. A gap through the stop before a fill is cancelled. The news blackout is applied. Backtest, paper broker and scanner share `app/core/fills.py`.
- Reproducibility: re-running the engine gives the same 4,774 trades and the same R to 1e−9.

## Fixes made, and why they matter
1. `app/core/data_quality.py`: per-date coverage, longest gap, zero-volume share, and the session-validity rule fixed in advance. `max_gap_between` flags trades held through holes. Incomplete data is now visible and excluded by rule, never filled in.
2. `app/backtest/engine.py`: `run(..., valid_dates=...)` rejects new orders on invalid dates and counts them as "Invalid data session". The default `None` gives the original behaviour, so earlier results reproduce exactly. `Trade.planned_risk_pts` is now recorded.
3. `app/core/scanner.py`: `resolve` applies `cancel_level` on complete 5m closes, the same rule as the engine and paper broker, with a new status `cancelled`. `Setup.cancel_level` and the `scanner_signals.cancel_level` column were added. `app/repository.py` `init_db` adds new nullable columns to existing tables. It only adds, never drops or rewrites. The scanner API counts `cancelled`.
4. `app/backtest/robustness.py`: `cluster_bootstrap` (resampling whole weeks) and `bonferroni_z`. `report_card.report(groups=..., tests=...)` adds week-clustered ranges and a family-wise lower bound. Labels now say what the bootstrap number is. The verdict rule is unchanged.
5. `scripts/audit_measurements.py`: reproducibility check, data report, all-sessions vs valid-only results, gross vs net, cost/risk, drawdown, cost stress, and the bid-only and data-hole checks. It loads 2019–2024 only and asserts that.

## Tests
- New tests: 3 in `tests/test_backtest_engine.py` (valid dates, default unchanged, planned vs fill risk), 3 in `tests/test_scanner.py` (cancel, ignored once filled or on old rows, incomplete 5m bucket), 6 in `tests/test_data_quality.py` (rule thresholds, edges, weekends, hole detection, column migration on an old table), 3 in `tests/test_robustness.py` (clustered vs iid width, Bonferroni z), and 1 in `tests/test_report_card.py`.
- The scanner cancel test **fails on the old code** (checked by temporarily restoring the old `scanner.py`) and passes with the fix.
- Full suite: **212 passed** (196 before the audit plus 16 new).

## Corrected numbers (new; earlier reports are left unchanged)
Base costs (spread 1.5 + slippage 0.5 pts). Average R per trade. "Valid" means valid sessions only, from a fresh engine run.

| strategy | dev gross | dev net (all → valid) | val gross (valid) | val net (all → valid) | cost/risk (median) |
|---|---:|---:|---:|---:|---:|
| trend_fvg | +0.03 | −0.064 → −0.059 | −0.10 | −0.185 → −0.158 | 0.06–0.07 |
| sweep_mss_fvg | −0.08 | −0.169 → −0.164 | +0.25 | +0.150 → +0.186 | 0.05–0.06 |
| orb | +0.07 | −0.007 → −0.012 | +0.10 | −0.066 → +0.032 | 0.06–0.07 |
| vwap_reversion | −0.08 | −0.310 → −0.310 | −0.00 | −0.211 → −0.149 | 0.13–0.16 |
| silver_bullet | +0.02 | −0.070 → −0.076 | +0.04 | −0.108 → −0.014 | 0.05–0.07 |
| london_trend_fvg | −0.17 | −0.354 → −0.362 | +0.02 | −0.237 → −0.112 | 0.13–0.15 |
| london_sweep_mss_fvg | −0.13 | −0.328 → −0.322 | −0.14 | −0.369 → −0.307 | 0.15 |

- **No strategy is positive net in both splits, with or without the valid-session rule.** The two closest:
  - sweep_mss_fvg: validation +0.19R (95% range −0.08 to +0.45; −0.25 after the 36-test adjustment), but development −0.16R with a range entirely below 0.
  - orb: −0.01 / +0.03, both ranges spanning 0. It turns negative in validation at spread ×2.
- Excluding invalid sessions mostly removes partial 2023 days, which lifts several validation averages. This is the expected direction when broken days are dropped. It is reported, not used to qualify anything: `scanner.QUALIFIED` stays empty.
- **Cost stress** (valid sessions, same trades re-priced): at spread 3.0 + slippage 1.5, every strategy except sweep_mss_fvg validation is negative in both splits. At the lower "measured-like" cost (spread 1.0, the MetaQuotes-Demo level, + slippage 0.5), orb is marginally positive in both splits (+0.006 / +0.045R). Both ranges span 0, it is negative in development at base cost, and it fails the existing robustness rule (positive at double costs). That is not evidence of an edge, and a cost assumption must not be lowered because it helps one strategy.
- Only one earlier number changes: "75 trades held through gaps" becomes **74** under the module's exact definition. The earlier scratch count used a slightly different gap test.

## Remaining limitations
- The bid/ask fill bias is measured, not corrected: the data has no ask prices.
- 2023 cannot be repaired from HistData. Valid-only validation now has fewer trades, so it is less certain.
- There is no holiday calendar in the engine or the live loop. Live early-close days rely on stale-data detection.
- Exness spread, swap and slippage are not measured. The only measured spread is the MetaQuotes-Demo feed.
- Cost stress re-prices fixed trades. It ignores the effect of costs on later risk-limit decisions.
- The Bonferroni adjustment is conservative. "36 versions" counts NAS100, BTC, gold, daily and intraday tests together.
- The backtest VWAP is a time-weighted average, not volume-weighted.
- Folder rename to `makeithappen` is still pending (unrelated to this audit).

## One recommended next research step
**Re-measure the existing 7 strategies, unchanged, on bid AND ask data for 2023 from a second source.** Dukascopy
serves ASK as well as BID candles; the URL pattern is the same as in `dukascopy_source.py`, to be confirmed before
downloading. Pre-register it like the other tests, with no rule changes and 2025+ still locked. This tests the two
largest open measurement doubts together: the half-missing validation year and the bid-only fills. If the strategies
still fail, the "no edge" conclusion becomes much firmer.
