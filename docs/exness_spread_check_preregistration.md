# Exness vs Dukascopy spread check, 2023 (pre-registered 2026-11-19)

Written and committed BEFORE any Exness tick file was downloaded or opened.
**Measurement only.** No strategy is run on this data. It changes no strategy, cost setting, backtest, risk limit
or `scanner.QUALIFIED` (stays empty). It does not replace Dukascopy in `docs/bidask_full_preregistration.md`.

## Why
Every bid/ask result so far uses Dukascopy quotes, and the MT5 spread we measured came from MetaQuotes' demo feed.
The real Exness USTEC spread has never been checked. Exness publishes free bid/ask ticks. Two questions:
1. Is the 2023 Exness file complete and correctly timed, so it can be trusted?
2. How does its spread compare with Dukascopy's and with the 1.5-point backtest assumption?

## Data
- Exness: `https://ticks.ex2archive.com/ticks/USTEC/2023/Exness_USTEC_2023.zip`, instrument `USTEC`, from
  https://www.exness.com/tick-history/. Kept unmodified in `backend/data/external/exness_2023/` (not in git, not in
  `app.db`). 2025 and later are not downloaded.
- Expected content: one CSV of ticks with a UTC timestamp, bid and ask. If the columns or units differ, the check
  stops and reports that. Nothing is guessed.
- Dukascopy: stored `USATECHIDXUSD` (bid) and `USATECHIDXUSD:ASK` minute bars for 2023.
- Limitation stated now: this describes the `USTEC` instrument in Exness's archive. It may differ from a given
  account type (`USTECm`, `USTECc`, Raw Spread, Zero), and a published spread leaves out any commission.

## Method (fixed now)
- Weekdays only, New York time 03:00-15:55 (the strategies' holding window).
- **Minute spread** = ask - bid at the last tick of the minute for Exness; ask close - bid close for Dukascopy.
- Ticks with bid <= 0, ask <= 0 or ask < bid are excluded and counted. Missing minutes are never filled.
- Spreads are compared only on minutes present in both sources.
- Windows: **pre-US 03:00-09:29** and **US 09:30-15:54**. Reported per window and per New York hour: minutes, days,
  median and 90th percentile of each source.

## File checks (all must pass, otherwise "file not usable", no spread verdict)
1. **Coverage:** at least 90% of 2023 weekdays are valid sessions under the project rule (03:00-15:55 NY has at least
   765 of 775 minutes and no hole over 5 minutes). Every month is listed.
2. **Clock:** correlation of 1-minute mid-price changes with Dukascopy is highest at lag 0, among lags -2..+2 minutes,
   checked separately for each of the three 2023 clock periods (before US DST, US DST, after US DST).
3. **Price level:** median absolute difference between Exness and Dukascopy minute mid prices is at most 10 points.
4. **Bad ticks:** at most 0.1% of ticks are excluded.

## Decisions (fixed now, per window, on the median)
- Against the assumption: Exness median <= 1.5 → "1.5 assumption holds"; > 1.5 → "1.5 assumption understated".
- Against Dukascopy, ratio = Exness / Dukascopy: below 0.80 → "Exness cheaper"; 0.80-1.25 → "similar";
  above 1.25 → "Exness more expensive".
- Fewer than 200 shared days in a window → "not enough data", no verdict.
- **Other years:** fetching 2019-2022 and 2024 is worthwhile only if all file checks pass. The spread level does not
  decide this. Exness starts in August 2019, so it cannot meet the 90% coverage rule for 2019-2022 alone.
- Whatever the result: no automatic change to costs or backtests. A strategy test on Exness data would need its own
  pre-registration and owner decision, recorded in `docs/decisions.md`.

Output: `docs/exness_spread_check_report.md`, made by `backend/scripts/exness_spread_check.py`.
