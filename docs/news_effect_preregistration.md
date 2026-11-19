# News effect on NAS100, gold and BTC — rules written before any result

Written 2026-11-19, before any number below was computed. Owner request: "get news work (need the news effect for
NAS, gold and BTC only)". **Measurement only:** it describes how much each market usually moves around each news
type. It is not a strategy and it does not change the ±30-minute news blackout, a risk limit or `scanner.QUALIFIED`.

## Data
- Events: `app/calendar/us_high_impact_events.csv` (CPI, NFP, FOMC, GDP, PCE; official sources), releases from
  2019-01-01 to 2024-12-31 only (2025+ stays locked).
- Prices (stored 1-minute bars, UTC): NAS100 = HistData `NSXUSD`, Gold = HistData `XAUUSD`, BTC = Binance `BTCUSDT`.
  The same files the backtests used.

## What is measured for each event and market
- **Before price** = close of the last 1-minute bar that starts before the release minute (within 10 minutes).
- **30-minute range** = (highest high − lowest low) of the 1-minute bars starting in [release, release + 30 min),
  as a **% of the before price**. Needs at least 20 of those 30 bars, otherwise the event is skipped for that market
  (counted and reported).
- **30-minute move** = |close of the last bar in the window − before price|, as a % of the before price.
- **Normal range (control)** = the same 30-minute range at the **same New York clock time** on the 20 nearest
  weekdays (10 before, 10 after) that have **no** calendar event that day; median of those that have enough bars.

## Summary per news type × market
- Number of events measured (and skipped).
- Median 30-minute range on news, median normal range, and **effect = news median ÷ normal median**
  ("× normal").
- Median 30-minute move on news.
- Share of events whose range was more than 2× that event's own normal range.

## Output
`backend/app/calendar/news_effect.json` (used by the dashboard and Telegram) and `docs/news_effect_report.md`.
Nothing is chosen after seeing results; no threshold here turns into a trading rule.

## Limits
- HistData gold/NAS100 are not Exness prices; BTC trades 24/7, so its "normal" includes US-morning activity too.
- 2019-2024 only; markets can react differently in the future. A median says nothing about the direction.
