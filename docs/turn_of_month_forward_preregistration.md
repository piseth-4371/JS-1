# Turn of the month — paper forward test, rules written before it starts

Written 2026-11-19. Follows E19 (`docs/turn_of_month_report.md`: inconclusive — positive in 1971-1999 and
2000-2024, but the 2000-2024 range crossed zero). Owner approved: "the turn-of-the-month paper test running
automatically". The rule below is **exactly** the E19 rule; nothing is tuned.

## Rule (unchanged from E19)
- **Buy** at the close of the **second-to-last** trading day of each month, **sell** at the close of the **3rd**
  trading day of the next month. Always long, one paper trade per month. **No order is ever sent anywhere.**

## Instrument, prices and days (the traded CFD, not the index)
- Prices: the MT5 `USTEC` 1-minute bars the engine stores (`ENGINE_SOURCE`, NAS100 symbol).
- **Close of a day** = close of the 15:59 New York bar; if that bar is missing, the latest bar from 15:55 to 15:59.
  If none of them exists, that day has **no close**.
- **Trading days** = weekdays that are not NYSE holidays, computed by fixed rules: New Year's Day, Martin Luther King
  Day, Presidents' Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, Christmas
  (Saturday holidays observed Friday, Sunday holidays observed Monday; New Year's Day on a Saturday is not moved
  back into December, as on the NYSE). So the schedule is known in advance, never chosen from the data.
- If the entry day or the exit day has no close (e.g. the PC or MT5 was off), that month's trade is **void
  (no data)**. It is reported and never filled in or guessed.

## Costs (same as E19)
Spread 0.02% of price per round trip + 7% a year financing per calendar night held.
Net return = price return − 0.02% − 7% × nights / 365. Points are reported as well.

## Start and evaluation
- Counts every month turn whose **entry day is on or after 2025-12-01**, i.e. data E19 never saw. Earlier month
  turns that happen to be in the database are shown separately as "before the forward test", not counted.
- **No verdict before 36 completed trades** (about 3 years). Then: **passes** if the average net return is > 0
  AND the 95% interval of the average (bootstrap by trade, 5,000 runs, seed 11) is above 0; **negative** if the
  average is ≤ 0; otherwise **inconclusive**. Void months do not count as trades.
- Until then the dashboard and Telegram show it as **"paper forward test — collecting, no verdict"**.

Nothing here changes `scanner.QUALIFIED`, the paper account, a strategy or a risk limit.
