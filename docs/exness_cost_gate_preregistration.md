# Exness cost gate — rules written before any result

Written 2026-11-19, before the check below was run on any trade. Owner request: "do 5" (re-check any strategy that
passes with Exness' real costs before it is ever used).

## Why
Every NAS100 backtest charges a **1.5-point spread** per round trip (`app/core/fills.Costs.spread`) plus 0.5 points
of slippage on each market/stop leg. The Exness `USTEC` archive (`docs/exness_spread_years_report.md`) measured a
much wider spread in every usable year:

| window (New York time) | 2021 median | 2022 median | 2023 median | highest median | highest p90 |
|---|---:|---:|---:|---:|---:|
| pre-US 03:00–09:29 | 2.86 | 2.75 | 2.94 | **2.94** | **3.29** |
| US 09:30–15:54 | 2.94 | 2.87 | 2.93 | **2.94** | **3.65** |

2019, 2020 and 2024 Exness files failed their data checks and are not used.

## The gate (a new, permanent rule)
A strategy that **passes** its main pre-registered test (for NAS100 now: `docs/bidask_full_preregistration.md`)
may be added to `scanner.QUALIFIED` only if it **also passes this gate**. Failing the gate means "not eligible for
an Exness account", whatever the main result was. Passing the gate is not proof of an edge either.

## How each trade is re-priced
- Window = the trade's **entry** minute in New York time: before 09:30 → pre-US, otherwise US.
- **Exness model:** `r_exness = r + (1.5 − 2.94) / risk_pts` (spread replaced by the highest usable-year median
  for that window; both windows are 2.94). Slippage is unchanged.
- **Exness stress:** the same with the highest p90: 3.29 pre-US, 3.65 US.
- Trades whose cost model is not the NAS100 one (BTC) are out of scope.
- One check of the input first: `r` must equal `gross − (1.5 + 0.5 × legs) / risk_pts` for every trade
  (difference < 1e-9). If not, stop: "input does not use the expected cost model — no verdict".

## Pass rule (same shape as the main test)
For **both** development (2019–2022) and validation (2023–2024), separately:
- at least 30 trades,
- Exness-model average R > 0,
- family 95% interval lower bound > 0 (whole-week block bootstrap, 5,000 resamples, seed 11, Bonferroni for 7
  strategies — `app/backtest/decompose.week_interval(tests=7)`),
- Exness-stress average R > 0.

Verdict words: **"passes the Exness gate"**, **"fails the Exness gate"** (any split with average R ≤ 0, or any
other condition missed), or **"not eligible — failed its main test"** when the main test already failed. In that
case the Exness numbers are still printed, for information only.

## First run (information only)
Input: `backend/data/backtest_trades.csv` (the bid-only HistData backtest, 7 NAS100 strategies, 2019–2024). All 7
already failed their main tests (`docs/experiment_journal.md`), so no strategy can become eligible from this run.
When the bid/ask re-test finishes, the gate is run on its trades too (`--trades`).

## Limits
- Spread is the median/p90 of last-tick-per-minute quotes, not real order fills; commission and the account type
  (`USTECm`, `USTECc`) are not included.
- One flat value per window ignores news spikes and the open; the p90 stress is the only allowance for that.
- 2019, 2020 and 2024 trades use 2021–2023 Exness levels.

Nothing in this file changes a strategy, a risk limit or `scanner.QUALIFIED`.
