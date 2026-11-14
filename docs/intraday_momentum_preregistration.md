# Intraday momentum research — rules fixed BEFORE testing (2026-11-14)

## Why this idea
Different kind from everything tested so far: no chart pattern, no stop-hunting levels. It is a
**time-of-day effect** from published research:
- Gao, Han, Li, Zhou, "Market intraday momentum", Journal of Financial Economics 2018: on the S&P 500 ETF
  (1993–2013) the first half-hour return (including the overnight move) predicted the last half-hour return.
  Explained by late portfolio rebalancing / hedging near the close. Weaker for QQQ (Nasdaq-100) per a summary
  of 1999–2012 data.
- Against it: Rosa (Journal of Futures Markets, 2022) reports the predictability disappears out of sample.
- Baltussen et al. report it across 60+ futures 1974–2020.
So the evidence is mixed. Prior expectation: probably fails after costs. We test it once, honestly.

Research only: not connected to the live engine. Nothing in the core rules changes.

## Data
HistData NSXUSD 1-minute bars (2019–2024), New York time. Development 2019–2022, validation 2023–2024
(by trade date). 2025+ stays locked.

## Rule — `intraday_momentum_nas100`
1. Signal: `r1 = close at 10:00 / previous trading day's close at 16:00 − 1`
   (10:00 = close of the 09:59 bar; 16:00 = close of the 15:59 bar). Includes the overnight move, as in the paper.
2. At 15:30 (close of the 15:29 bar) go **long if r1 > 0, short if r1 < 0** (r1 = 0 → no trade).
3. Exit at 15:55 (close of the 15:54 bar) — the project's "flat by 15:55" rule.
   (The paper's 15:30–16:00 window is shown for information only; it does not count for the verdict.)
4. Mandatory stop: 2 × ATR14 of 5-minute bars (the 14 bars ending 15:30) from entry. Checked on every
   1-minute bar 15:30–15:54; if a bar opens beyond the stop, fill at that open (pessimistic).
5. Skip: US early-close days (July 3, the day after Thanksgiving, December 24, when they are weekdays) and
   days with any of the needed bars missing (previous 15:59, today 09:59, 15:29, 15:54).
6. Cost: 2.0 points per trade (same assumption as all NAS100 tests). 1 trade per day at most.

## Pass rule (all must hold in BOTH development and validation)
1. Average R per trade > 0 after costs.
2. At least 100 trades.
3. Beats a **random-direction control** (same days, same window, same stop, direction by coin flip; 500 runs)
   in ≥ 90% of runs — i.e. the signal must predict direction, not just catch volatility.
4. Beats **always-long** in the same window (average R), so it is not just the 2019–2024 bull market.
If it fails, it fails — no parameter changes afterwards.
