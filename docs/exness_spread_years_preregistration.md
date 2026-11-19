# Exness spread by year, 2019-2024 (pre-registered 2026-11-19)

Written and committed BEFORE any price or spread in the 2019-2022 and 2024 Exness files was read. Only their
timestamps have been read, to list dates. The 2023 file was already analysed
(`docs/exness_spread_check_report.md`), and that report stays the official 2023 result.

**Measurement only.** No strategy is run on this data. It changes no strategy, cost setting, backtest, risk limit or
`scanner.QUALIFIED` (stays empty). It does not replace Dukascopy in `docs/bidask_full_preregistration.md`.

## Data
- Exness `USTEC` yearly zips in `backend/data/external/exness_<year>/`, unmodified. 2025 and later are never read.
- Reference for the file checks: stored HistData `NSXUSD` bid minutes, because it covers every year. Dukascopy bid+ask
  covers only part of these years today.
- Years: 2019 (scope 2019-08-05 to 2019-12-31, because the file starts in August), 2020, 2021, 2022, 2024.
  2023 is run again with the same code as a **control** for the new reference. It does not replace the 2023 report.

## Method
Same as `docs/exness_spread_check_preregistration.md`: weekdays, New York 03:00-15:55, last tick of each minute,
spread = ask - bid, the same bad-tick rule, no filled minutes, windows pre-US 03:00-09:29 and US 09:30-15:54.
Here the Exness spread uses every Exness minute in the window, because no spread reference covers all years.

## File checks, per year (all must pass, otherwise "file not usable", no verdict for that year)
1. **Coverage:** at least 90% of weekdays in scope are valid sessions (at least 765 of 775 minutes, no hole over
   5 minutes). 2024 is judged on the whole year, so its missing last days count against it.
2. **Clock:** correlation of 1-minute bid changes with HistData is highest at lag 0 among lags -2..+2, separately
   before US DST, during US DST and after US DST.
3. **Price level:** median absolute gap between Exness and HistData minute bids is at most 10 points.
4. **Bad ticks:** at most 0.1% of ticks are excluded.

Numbers are still shown for a failed year, labelled "no verdict".

## Decisions, per year and window, on the median
- Exness median <= 1.5 → "1.5 assumption holds"; > 1.5 → "1.5 assumption understated".
- Dukascopy comparison only where Dukascopy bid+ask share at least 200 days with Exness in that window (ratio below
  0.80 "Exness cheaper", 0.80-1.25 "similar", above 1.25 "Exness more expensive"). Otherwise "Dukascopy not available".
- A window needs at least 200 days (80 for 2019), otherwise "not enough data".
- Whatever the result: no automatic change to costs or backtests. Using Exness costs in a strategy test needs its own
  pre-registration and owner decision, recorded in `docs/decisions.md`.

Output: `docs/exness_spread_years_report.md`, made by `backend/scripts/exness_spread_years.py`.
