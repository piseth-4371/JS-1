# Experiment journal

Made by `backend/scripts/experiment_journal.py` on 2026-11-21 from `docs/experiments.json`. Every experiment is listed, including every failure. Edit the JSON file, never this page.

## How to read it

- **Pre-registered** means the rules and pass mark were committed to git *before* the result existed. The script checks this against git history. "no" means the rules were not written down first, so treat that result with extra caution.
- **Evaluations** counts how many times a strategy was judged against a pass mark. Each one is another chance for luck to look like skill, which is why the pass mark has to be strict.
- A pass would only make a strategy eligible for one final test on the locked 2025+ data, and only with the owner's separate approval.

## Summary

- Experiments: **23** (14 strategy tests or filters, 9 measurements or checks).
- Strategy evaluations so far: **54**. Passed: **0**.
- Outcomes: Failed 10, Measured (no pass/fail) 9, In progress (no verdict) 3, Inconclusive 1.
- Journal check: **OK**.

| id | date | experiment | kind | pre-registered | evaluations | outcome |
|---|---|---|---|---|---:|---|
| E01 | 2026-11-13 | Auto-switch between strategies (weekly walk-forward) | strategy test | no | 1 | Failed |
| E02 | 2026-11-13 | BTC weekend intraday, 5 strategies | strategy test | no | 5 | Failed |
| E03 | 2026-11-13 | Cost filter: skip trades where cost is more than 20% of risk | filter | no | 7 | Failed |
| E04 | 2026-11-14 | NAS100 intraday, 7 strategies (NY and London), full 2019-2024 | strategy test | no | 7 | Failed |
| E05 | 2026-11-14 | Daily trend: SMA100 long and Donchian 55/20 | strategy test | yes, before results | 2 | Failed |
| E06 | 2026-11-14 | Intraday momentum (published time-of-day effect) | strategy test | yes, before results | 1 | Failed |
| E07 | 2026-11-14 | Gold intraday, the same 7 rules unchanged | strategy test | yes, before results | 7 | Failed |
| E08 | 2026-11-16 | Strategy report card | measurement | no | 0 | Measured (no pass/fail) |
| E09 | 2026-11-16 | Volatility regime filter (20th-80th percentile) | filter | yes, before results | 7 | Failed |
| E10 | 2026-11-16 | Measurement audit and session-validity rule | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E11 | 2026-11-16 | Real bid/ask prices, 2023 | measurement | yes, before results | 7 | Measured (no pass/fail) |
| E12 | 2026-11-17 | MT5 demo spread by time of day | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E13 | 2026-11-17 | Real bid/ask re-test, 7 strategies, 2019-2024 | strategy test | yes, before results | 7 | In progress (no verdict) |
| E14 | 2026-11-17 | Paper engine vs backtester replay | execution check | yes, before results | 0 | Measured (no pass/fail) |
| E15 | 2026-11-19 | Exness vs Dukascopy spread, 2023 | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E16 | 2026-11-19 | Exness spread by year, 2019-2024 | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E17 | 2026-11-19 | Slow multi-market trend (10 markets, monthly) vs benchmarks | strategy test | yes, before results | 1 | Failed |
| E18 | 2026-11-19 | Exness cost gate: NAS100 backtest trades re-priced with Exness spread | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E19 | 2026-11-19 | Turn of the month: hold the Nasdaq over each month end (own idea) | strategy test | yes, before results | 1 | Inconclusive |
| E20 | 2026-11-19 | News effect: how much NAS100, gold and BTC move in the 30 minutes after each US high-impact release | measurement | yes, before results | 0 | Measured (no pass/fail) |
| E21 | 2026-11-19 | Turn of the month: paper forward test on MT5 USTEC (collecting) | strategy test | yes, before results | 0 | In progress (no verdict) |
| E22 | 2026-11-21 | Buy the drop: Nasdaq at a 10-day-low close, hold 5 days (the one unfreeze idea) | strategy test | yes, before results | 1 | Failed |
| E23 | 2026-11-21 | FX carry: long the 2 highest-rate, short the 2 lowest-rate of 7 currencies (cancelled) | strategy test | yes, before results | 0 | In progress (no verdict) |

## Details

### E01 — Auto-switch between strategies (weekly walk-forward)

- **Question:** Does picking last week's best strategy each week beat sticking with one strategy?
- **Rules:** not written down before the test
- **Data:** NAS100 1-minute bars, 2019 only
- **Outcome:** Failed. Worse than the fixed strategies on 2019. Not enabled.
- **Report:** `docs/selector_report.md`

### E02 — BTC weekend intraday, 5 strategies

- **Question:** Do the intraday setups make money on Bitcoin at weekends after exchange fees?
- **Rules:** not written down before the test
- **Data:** Binance BTCUSDT 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** Failed. All 5 fail. About 0R before costs; fees cost 0.4-1.1R per trade.
- **Report:** `docs/backtest_report_btc.md`, `docs/robustness_report_btc.md`

### E03 — Cost filter: skip trades where cost is more than 20% of risk

- **Question:** Does skipping small-stop trades, where costs eat the most, turn the NAS100 strategies positive?
- **Rules:** not written down before the test
- **Data:** NAS100 1-minute bars; first a partial period, then full 2019-2022
- **Outcome:** Failed. Fewer losses, still no winner. sweep_mss_fvg looked like +0.15R on the first 18 months but was -0.14R on full 2019-2022 (Lesson 2: small samples lie).
- **Report:** `docs/cost_filter_report.md`

### E04 — NAS100 intraday, 7 strategies (NY and London), full 2019-2024

- **Question:** Do the 7 written-down intraday strategies make money after costs in both periods?
- **Rules:** not written down before the test
- **Data:** HistData NSXUSD 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024 (splits fixed in CLAUDE.md before the run)
- **Outcome:** Failed. No strategy is positive in both periods; averages -0.01R to -0.37R per trade; none robust.
- **Report:** `docs/backtest_report.md`, `docs/robustness_report.md`

### E05 — Daily trend: SMA100 long and Donchian 55/20

- **Question:** Do slow daily trend rules beat a random-timing control with the same stop and holding time?
- **Rules:** `docs/daily_trend_preregistration.md` (commit 923b5a6)
- **Data:** HistData NSXUSD daily bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** Failed. Both fail: they do not beat random timing, and only 8-27 trades per period. A rising market made random entries look good (Lesson 4).
- **Report:** `docs/daily_trend_report.md`

### E06 — Intraday momentum (published time-of-day effect)

- **Question:** Does the first-half-hour move predict the last-half-hour move on NAS100, as published research reports for other markets?
- **Rules:** `docs/intraday_momentum_preregistration.md` (commit 406b7fb)
- **Data:** HistData NSXUSD 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** Failed. About 0R per trade even before costs (1,338 trades).
- **Report:** `docs/intraday_momentum_report.md`

### E07 — Gold intraday, the same 7 rules unchanged

- **Question:** Do the 7 NAS100 rules work on gold without any change?
- **Rules:** `docs/gold_and_scanner_preregistration.md` (commit 6315eb8)
- **Data:** HistData XAUUSD 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** Failed. All 7 fail on gold.
- **Report:** `docs/gold_report.md`

### E08 — Strategy report card

- **Question:** How large and how certain is each strategy's edge (expected value, range, luck check, Kelly)?
- **Rules:** not written down before the test
- **Data:** Existing backtest trades, 2019-2024
- **Outcome:** Measured (no pass/fail). Kelly fraction is 0% for every strategy except sweep_mss_fvg in validation only. Measures edge; creates no signals.
- **Report:** `docs/report_card.md`

### E09 — Volatility regime filter (20th-80th percentile)

- **Question:** Do the strategies work if they only trade on days with normal, not calm or wild, volatility?
- **Rules:** `docs/volatility_filter_preregistration.md` (commit 67434a7)
- **Data:** HistData NSXUSD 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** Failed. All 7 fail; the filter made validation worse for 5 of 7.
- **Report:** `docs/volatility_filter_report.md`

### E10 — Measurement audit and session-validity rule

- **Question:** Are the backtest measurements sound (data holes, costs, clustered uncertainty, multiple testing)?
- **Rules:** `docs/data_quality_rule.md` (commit 6664851)
- **Data:** HistData NSXUSD 2019-2024
- **Outcome:** Measured (no pass/fail). 2023 fails the session-validity rule on 119 of 256 weekdays. Conclusion unchanged: no edge after costs.
- **Report:** `docs/audit_report.md`, `docs/data_quality_report.md`

### E11 — Real bid/ask prices, 2023

- **Question:** Does the bid-only fill model flatter the results, and what is the real spread by time of day?
- **Rules:** `docs/bidask_retest_preregistration.md` (commit 8a9c21d)
- **Data:** Dukascopy USATECHIDXUSD bid and ask 1-minute bars, 2023
- **Outcome:** Measured (no pass/fail). The bid-only model is not material. Spread about 1.45 pts in US hours, about 3 pts before 09:30 NY. 6 of 7 strategies at or below 0; silver_bullet +0.32R but its range crosses 0 (unproven).
- **Report:** `docs/bidask_retest_report.md`

### E12 — MT5 demo spread by time of day

- **Question:** Does the broker demo feed show the same wider spread before the US open as Dukascopy?
- **Rules:** `docs/spread_by_hour_preregistration.md` (commit 1572f18)
- **Data:** MetaQuotes-Demo USTEC 1-minute bar spread, 73 days
- **Outcome:** Measured (no pass/fail). 1.0 pts before the US open, 0.9 in US hours, never above 1.0. The feed looks fixed or capped, so this is weak evidence. Not Exness.
- **Report:** `docs/spread_by_hour_report.md`

### E13 — Real bid/ask re-test, 7 strategies, 2019-2024

- **Question:** Does any of the 7 strategies have a reliable advantage with real bid/ask prices, in both periods?
- **Rules:** `docs/bidask_full_preregistration.md` (commit f69e58c)
- **Data:** Dukascopy USATECHIDXUSD bid and ask 1-minute bars 2019-2024; dev 2019-2022, validation 2023-2024
- **Outcome:** In progress (no verdict). Waiting for data. On 2026-11-19 dev coverage was 2% and validation 61%, so there is no verdict. Amendment 1 (commit 390efc1, DST clock check) was made before any strategy result.
- **Report:** `docs/bidask_full_report.md`

### E14 — Paper engine vs backtester replay

- **Question:** Does the same market data give the same signal, fill, exit and cost in the paper engine and the backtester?
- **Rules:** `docs/paper_vs_backtest_plan.md` (commit a1408ee)
- **Data:** MetaQuotes-Demo USTEC 1-minute bars, 23 weekdays 2026-10-14 to 2026-11-13
- **Outcome:** Measured (no pass/fail). Signals 126/126 identical; shared trades 28/28 identical. All 34 one-sided trades trace to the 0.1 minimum lot and its knock-on through the risk rules. No execution bug found.
- **Report:** `docs/paper_vs_backtest_report.md`

### E15 — Exness vs Dukascopy spread, 2023

- **Question:** Is the Exness tick file trustworthy, and how does its spread compare with Dukascopy and the 1.5-point assumption?
- **Rules:** `docs/exness_spread_check_preregistration.md` (commit 7fba3c4)
- **Data:** Exness USTEC ticks 2023 and Dukascopy bid/ask 2023
- **Outcome:** Measured (no pass/fail). File passes all checks. Exness median 2.95 pts before the US open (similar to Dukascopy) and 2.93 in US hours (about double Dukascopy's 1.45). The 1.5 assumption is understated.
- **Report:** `docs/exness_spread_check_report.md`

### E16 — Exness spread by year, 2019-2024

- **Question:** Is the Exness spread similar in every year, and are the yearly files usable?
- **Rules:** `docs/exness_spread_years_preregistration.md` (commit 0d54a49)
- **Data:** Exness USTEC ticks 2019-2024, checked against HistData NSXUSD
- **Outcome:** Measured (no pass/fail). Usable: 2021, 2022, 2023 (median 2.75-2.94 pts). Not usable: 2019 and 2020 (too few complete days), 2024 (price gap to HistData 17.29 pts). Exness cannot cover both test periods.
- **Report:** `docs/exness_spread_years_report.md`

### E17 — Slow multi-market trend (10 markets, monthly) vs benchmarks

- **Question:** Does a 12-month trend rule across stocks, energy and currencies earn a positive return after costs, and beat holding the same markets or random directions?
- **Rules:** `docs/multimarket_trend_preregistration.md` (commit 3d5fd49)
- **Data:** FRED daily spot prices and index levels, 10 markets; dev 1988-2010, validation 2011-2024 (2025+ not downloaded)
- **Outcome:** Failed. Negative observed result. Net Sharpe +0.32 in 1988-2010 (range -0.07 to +0.71) but -0.30 in 2011-2024. Before costs +0.73 and +0.13: the assumed costs and 2% financing removed the small validation edge. Beat 100% and 94% of random-direction portfolios, and lost far less than always long in its worst months. Amendment 1 (commit 669cbe5) excluded one negative WTI price before any result.
- **Report:** `docs/multimarket_trend_report.md`

### E18 — Exness cost gate: NAS100 backtest trades re-priced with Exness spread

- **Question:** Would the 7 NAS100 strategies still look the same if the 1.5-point backtest spread were replaced by the 2.94-point spread measured on Exness USTEC (p90 stress 3.29/3.65)?
- **Rules:** `docs/exness_cost_gate_preregistration.md` (commit 5e8744a)
- **Data:** backend/data/backtest_trades.csv (bid-only HistData backtest, 4,774 trades 2019-2024); Exness USTEC 2021-2023 spread levels
- **Outcome:** Measured (no pass/fail). Every strategy got worse: on average 0.109R more cost per trade. All 7 had already failed their main tests, so none is eligible. The only positive split, sweep_mss_fvg 2023-24, fell from +0.150R to +0.100R (stress +0.075R) while its 2019-22 split is -0.238R. The gate is now a permanent extra rule before anything can be added to scanner.QUALIFIED.
- **Report:** `docs/exness_cost_gate_report.md`

### E19 — Turn of the month: hold the Nasdaq over each month end (own idea)

- **Question:** Does holding the Nasdaq Composite from the second-to-last trading day of a month to the 3rd trading day of the next earn more than random timing, after Exness-like spread and overnight financing?
- **Rules:** `docs/turn_of_month_preregistration.md` (commit bd2e15c)
- **Data:** FRED NASDAQCOM daily closes; dev 1971-1999, validation 2000-2024 (2025+ locked)
- **Outcome:** Inconclusive. Inconclusive, the best result so far but not a pass. 1971-1999 passed every check (+0.50% per trade after costs, range +0.23% to +0.74%, beat 100% of random timing). 2000-2024 stayed positive (+0.19% per trade, stress +0.06%) but the range crossed zero (-0.13% to +0.52%) and it beat only 86% of random timing (95% required). The effect looks smaller since it became famous.
- **Report:** `docs/turn_of_month_report.md`

### E20 — News effect: how much NAS100, gold and BTC move in the 30 minutes after each US high-impact release

- **Question:** How many times bigger is the 30-minute range after CPI, NFP, FOMC, GDP and PCE than at the same time on nearby days without news, per market?
- **Rules:** `docs/news_effect_preregistration.md` (commit 60c011d)
- **Data:** HistData NSXUSD and XAUUSD, Binance BTCUSDT M1, events 2019-2024 (2025+ locked)
- **Outcome:** Measured (no pass/fail). News makes the first 30 minutes much bigger than normal: NAS100 CPI 3.3x, NFP 3.5x, FOMC 2.9x; gold FOMC 6.1x, CPI 2.8x, NFP 2.9x; BTC 1.9-2.4x for CPI/NFP/FOMC; GDP and PCE 1.2-1.8x. Size only: the measure says nothing about direction. Shown on the dashboard News card and in the Telegram heads-up 30 minutes before each release; the +-30-minute blackout is unchanged.
- **Report:** `docs/news_effect_report.md`

### E21 — Turn of the month: paper forward test on MT5 USTEC (collecting)

- **Question:** Does the E19 turn-of-month rule, unchanged, make money after costs on new MT5 USTEC prices it has never seen?
- **Rules:** `docs/turn_of_month_forward_preregistration.md` (commit 60c011d)
- **Data:** MT5 USTEC M1 bars stored by the engine, month turns with entry on or after 2025-12-01
- **Outcome:** In progress (no verdict). Running automatically (app/core/tom_forward.py, dashboard Results card, Telegram). No verdict before 36 trades (about 3 years). First 2 trades: +2.33% and -3.46% after costs. Paper only; never ordered.
- **Report:** 

### E22 — Buy the drop: Nasdaq at a 10-day-low close, hold 5 days (the one unfreeze idea)

- **Question:** Does buying the Nasdaq Composite at a close that is the lowest of the last 10 trading days and selling 5 trading days later earn more than random timing, after Exness-like spread and overnight financing, in both 1971-1999 and 2000-2024?
- **Rules:** `docs/buy_the_drop_preregistration.md` (commit 6943a95)
- **Data:** FRED NASDAQCOM daily closes; dev 1971-1999, validation 2000-2024 (2025+ locked)
- **Outcome:** Failed. Negative observed result. 1971-1999: 446 trades, -0.342% per trade after costs (-0.184% before costs), range -0.626% to -0.030%, beat 0% of random timing, 7 of 29 years positive, 0 of 4 nearby settings positive. 2000-2024: 400 trades, +0.203% (stress +0.045%) but the range crosses zero (-0.122% to +0.526%) and it beat only 87% of random timing. Before 2000 Nasdaq daily moves tended to continue (autocorrelation +0.205), so drops kept going. Project re-frozen (CLAUDE.md 2a).
- **Report:** `docs/buy_the_drop_report.md`

### E23 — FX carry: long the 2 highest-rate, short the 2 lowest-rate of 7 currencies (cancelled)

- **Question:** Does monthly FX carry among USD, EUR, GBP, JPY, CHF, CAD, AUD beat random currency picks after a swap markup and spreads, in both 1980-2004 and 2005-2024?
- **Rules:** `docs/carry_preregistration.md` (commit 2e521ea)
- **Data:** Not run: only the USD rate file was downloaded (FRED refused automated downloads)
- **Outcome:** In progress (no verdict). Cancelled by the owner before any result: the project covers NAS100, gold and BTC only. No rate or carry return was computed. Code and data removed; rules kept as history.
- **Report:** 

## Adding a new experiment

1. Write the rules and pass mark in `docs/<name>_preregistration.md` and commit it *before* running anything.
2. Add an entry to `docs/experiments.json` with `"outcome": "incomplete"` and that commit as `rules_commit`.
3. Run the test, commit the report, then update `outcome` and `result`, including when it fails.
4. Run `.\.venv\Scripts\python scripts\experiment_journal.py` from `backend`.
