# What we learned (2026-11-13 → 11-14)

Plain-English summary of every test in this project. All numbers come from the reports in this folder
(`backtest_report.md`, `robustness_report.md`, `cost_filter_report.md`, `daily_trend_report.md`,
`backtest_report_btc.md`) and the log in `decisions.md`. Past results do not predict the future.

**Words used here**
- **R** = the amount you risk on one trade. +1R = you won what you risked; −1R = you lost it.
  "Average R" is the result of an average trade. Above 0 = it made money on average.
- **Development (dev) 2019–2022** = the years used to build and judge ideas.
- **Validation 2023–2024** = newer years used to check whether a dev result was real.
- **Out-of-sample 2025+** = a final exam that can be used once. It is still locked: no strategy earned it.

---

## Lesson 1 — Costs decide most intraday results

Every trade pays the spread plus slippage (we assume 2.0 points on NAS100; the MT5 demo showed a
~1 point spread, so 2.0 is on the safe side).

That cost is fixed, but the stop size is not. With a 10-point stop, 2 points of cost is **20% of your risk
on every trade** — before the market even moves. Small-stop strategies have to be very good just to break even.

- NAS100: the 7 intraday strategies averaged between **−0.01R and −0.37R** per trade.
- BTC weekends were worse: fees (0.12% per round trip, assumed) cost **0.4–1.1R per trade**, and before
  costs the 5 BTC strategies were about 0R — no edge to pay the fees with.

**Takeaway:** before trusting any setup, ask "how big is the cost compared with my stop?"

## Lesson 2 — Small samples lie

The cost filter (skip trades where cost > 20% of risk) looked good on the first 18 months of data:
sweep_mss_fvg went from **+0.05R to +0.15R**. On the full 2019–2022 period the same rule gave **−0.14R**.

The early result was luck. With fewer than ~100 trades, a strategy can look great or terrible by chance.

**Takeaway:** never judge a strategy on a few weeks or a few dozen trades — including your own live trades.

## Lesson 3 — A result must hold in BOTH periods

sweep_mss_fvg: **−0.17R** in 2019–2022, **+0.15R** in 2023–2024. Someone who only tested 2023–2024 would
think they found a winner. Someone who only tested 2019–2022 would throw it away. The honest answer: it is
not consistent, so it is not trusted.

**Takeaway:** if an idea only works in one period, it probably fits that period's noise, not a real pattern.

## Lesson 4 — A rising market makes everything look good

The Nasdaq-100 rose strongly from 2019 to 2024. The daily trend test showed this trap:

- "Long when price is above the 100-day average" made **+0.67R** per trade in 2023–2024.
- But buying on *random* days, with the same stop and holding time, made **+0.23R**, and in 2019–2022 random
  timing (**+0.14R**) beat the strategy (**−0.07R**).

So most of the profit came from the market going up, not from the rule. We only saw this because we compared
with a random-timing control.

**Takeaway:** always ask "would I have made this money by just being in the market?"

## Lesson 5 — Popular ideas are not proof

The intraday strategies use well-known ideas (fair value gaps, liquidity sweeps, opening range, Silver
Bullet, London session). Tested with fixed rules on 6 years of 1-minute data, none showed an edge after costs.
This does not prove the ideas can never work with a human's judgment — it shows these exact, written-down
versions do not.

**Takeaway:** a strategy that "everyone uses" still needs a test like the ones in this project.

## Lesson 6 — Check your data before you trust any result

- HistData's FAQ says its times are fixed EST. They are not: the files follow UK summer time. Trusting
  the FAQ would have shifted every summer trade by one hour. We found it by checking the weekly 18:00 New York
  open, and confirmed it against Dukascopy (identical prices on 565,552 shared minutes).
- 2023 has missing hours on 110 of 253 trading days. We tested with and without those days; the
  conclusions did not change.

**Takeaway:** a wrong clock or missing data can create fake results. Verify data with a second source.

## Lesson 7 — Write the rules down first

For the daily trend test the rules and the pass mark were committed to git **before** the test
(`daily_trend_preregistration.md`). That is what keeps a test honest: you cannot quietly change the
rules after seeing the result. Changing settings until the backtest looks good is called overfitting,
and it produces strategies that only work on the past.

---

## Scoreboard

| Group | Strategies | Result |
|---|---|---|
| NAS100 intraday (NY + London) | 7 | All fail (dev and validation) |
| NAS100 intraday + cost filter | 7 | Fewer losses, still no winner |
| BTC weekend intraday | 5 | All fail (fees) |
| NAS100 daily trend (pre-registered) | 2 | Both fail (do not beat random timing; too few trades) |
| NAS100 intraday momentum (published research, pre-registered) | 1 | Fails: about 0R even before costs (1,338 trades) |
| Gold intraday (same 7 rules, pre-registered) | 7 | All fail |
| NAS100 intraday + volatility regime filter (pre-registered 2026-11-16) | 7 | All fail; made validation worse for 5 of 7 |

## What this means for you

- The **system** works: risk rules never broken, kill switch works, backtests are reproducible.
- The **strategies** do not have an edge. Do not trade them with real money, including the cent account.
- Next: let the paper engine run 2–4 weeks and compare the daily reports with the backtest. That tests the
  system, and it is also good practice in reading results calmly.
