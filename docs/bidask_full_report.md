# Bid/ask re-test 2019–2024 — results (INCOMPLETE DATA)

Made by `scripts/bidask_full_retest.py` on 2026-11-19 (`cd backend; .\.venv\Scripts\python scripts\bidask_full_retest.py`). Rules fixed in `docs/bidask_full_preregistration.md` (commit f69e58c) before this run. Measurement only: nothing can qualify; `scanner.QUALIFIED` stays empty; 2025+ is not loaded.

**Not fresh evidence:** all seven strategies were already tested on 2019–2024 (bid-only HistData) and 2023 was already re-tested with Dukascopy bid/ask; 36 strategy versions were tested in this project. A pass would only make a strategy eligible for a separately authorised final test on 2025+.

> **This run is INCOMPLETE.** At least one split has less than 90% of its weekdays with bid+ask data, so those strategies get no verdict. Indicators also bridge across long missing stretches, which makes the first days after a gap unreliable — in this partial run the 'development' trades are from December 2022 only, right after the first downloaded day, with no indicator warm-up. Re-run when the download finishes.

## How to read this (plain English)

- **R** = the amount risked on one trade. +1R = won what was risked; −1R = lost it.
- **Expectancy** = the average R per trade. Above 0 = made money on average *in this history*; it says nothing certain about the future.
- **Gross** = before any cost. **Net** = after spread, slippage and fees. Costs are always paid; profits are not.
- **Win rate** is how often trades won in this history. It is not a chance of the next trade winning.
- **95% week interval** = where the true average plausibly lies, found by re-drawing whole weeks of trades 5,000 times. **Family interval** is wider because seven strategies are tested at once (one of seven can look good by luck). If an interval contains 0, the data cannot tell a small edge from none.
- Assumptions of the week resampling: weeks are independent; longer regimes (a whole bull or bear year) are not captured, so the true uncertainty is larger than shown. With few trades the interval is unstable.

## Data and checks

- Dukascopy USATECHIDXUSD BID + ASK, minutes with both quotes: 452,551 (2022-12-01 .. 2024-03-28). December 2018 is warm-up only. No missing minute is filled in; no synthetic ask is used.
- Minutes where ask < bid: 0.
- Coverage needed for a verdict: ≥ 90% of weekdays. development 2019-2022: 2%; validation 2023-2024: 61%.

| year | weekdays | with bid+ask | valid sessions | missing months (weekdays missing) |
|---|---:|---:|---:|---|
| 2019 | 261 | 0 | 0 | 2019-01 (23), 2019-02 (20), 2019-03 (21), 2019-04 (22), 2019-05 (23), 2019-06 (20), 2019-07 (23), 2019-08 (22), 2019-09 (21), 2019-10 (23), 2019-11 (21), 2019-12 (22) |
| 2020 | 262 | 0 | 0 | 2020-01 (23), 2020-02 (20), 2020-03 (22), 2020-04 (22), 2020-05 (21), 2020-06 (22), 2020-07 (23), 2020-08 (21), 2020-09 (22), 2020-10 (22), 2020-11 (21), 2020-12 (23) |
| 2021 | 261 | 0 | 0 | 2021-01 (21), 2021-02 (20), 2021-03 (23), 2021-04 (22), 2021-05 (21), 2021-06 (22), 2021-07 (22), 2021-08 (22), 2021-09 (22), 2021-10 (21), 2021-11 (22), 2021-12 (23) |
| 2022 | 260 | 21 | 21 | 2022-01 (21), 2022-02 (20), 2022-03 (23), 2022-04 (21), 2022-05 (22), 2022-06 (22), 2022-07 (21), 2022-08 (23), 2022-09 (22), 2022-10 (21), 2022-11 (22) |
| 2023 | 260 | 257 | 247 | none (holidays only) |
| 2024 | 262 | 63 | 60 | 2024-04 (22), 2024-05 (23), 2024-06 (20), 2024-07 (23), 2024-08 (22), 2024-09 (21), 2024-10 (23), 2024-11 (21), 2024-12 (22) |

**Clock / daylight-saving check** (amendment 1 in the plan): the median 1-minute move must jump at 09:30 NY (≥ 1.5 × 09:29) and be larger than at 08:30 and 10:30, where a one-hour DST error would put it. Top minute shown for information.

| year | regime | ~days | 09:30 ÷ 09:29 | 08:30 | 09:30 | 10:30 | top minute | ok |
|---|---|---:|---:|---:|---:|---:|---|---|
| 2022 | US winter | 20 | 3.8× | 6.99 | 12.94 | 12.01 | 09:30 | yes |
| 2023 | US summer | 152 | 4.0× | 4.56 | 11.03 | 5.33 | 09:30 | yes |
| 2023 | US winter | 86 | 4.9× | 4.43 | 12.57 | 4.21 | 09:30 | yes |
| 2023 | US/UK mismatch | 15 | 2.6× | 4.55 | 9.15 | 5.08 | 09:56 | yes |
| 2024 | US winter | 48 | 2.9× | 4.50 | 9.28 | 5.72 | 09:30 | yes |
| 2024 | US/UK mismatch | 14 | 2.7× | 5.39 | 9.98 | 6.63 | 09:31 | yes |

**Second source** (Dukascopy bid close vs HistData close on shared minutes):

| year | shared minutes | median abs diff | p99 abs diff |
|---|---:|---:|---:|
| 2022 | 27,971 | 0.000 | 0.000 |
| 2023 | 299,229 | 0.000 | 0.000 |
| 2024 | 83,466 | 0.000 | 0.000 |

## Execution assumptions

| model | prices | spread | slippage | fees |
|---|---|---|---|---|
| G gross | bid only | 0 | 0 | 0 |
| B bid-only | bid only | 1.5 pts subtracted | 0.5 pt per market/stop leg | 0 |
| **R real bid/ask (primary)** | buys on ask, sells on bid | in prices | 0.5 pt per market/stop leg | 0 |
| S stress (fixed beforehand) | buys on ask, sells on bid | +0.5 pt extra | 1.0 pt per leg | 0 |

Fees are 0 (no commission on an Exness Standard CFD; no swap because every position is closed by 15:55 NY). Signals use bid 5-minute bars; the stop is checked before the target; positions close at 15:55 NY; orders only on valid sessions; rules, parameters, risk limits and news blackout unchanged.

## Pre-registered verdicts

| strategy | verdict |
|---|---|
| trend_fvg | **incomplete data — no verdict** |
| sweep_mss_fvg | **incomplete data — no verdict** |
| orb | **incomplete data — no verdict** |
| vwap_reversion | **incomplete data — no verdict** |
| silver_bullet | **incomplete data — no verdict** |
| london_trend_fvg | **incomplete data — no verdict** |
| london_sweep_mss_fvg | **incomplete data — no verdict** |

Rule: *passes* = in both dev and validation ≥ 30 trades, average R > 0, family-interval lower bound > 0 and stress average > 0. *Negative observed expectancy* = average ≤ 0 in dev or validation. Otherwise *inconclusive*. Passing only means eligible for a separately authorised 2025+ test, not live trading.

## 1. Results by split (model R, real bid/ask)

| strategy | split | trades | win rate | avg win | avg loss | gross (G) | net | profit factor | max DD | 95% week | family 95% (7 tests) | stress net |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| trend_fvg | development | 3 ⚠ < 30 trades: no conclusion | 67% | +2.000 | -1.025 | +1.000 | **+0.992** | 3.903 | 0.5% | +0.488 to +2.000 | +0.488 to +2.000 | +0.962 |
| trend_fvg | validation | 74 | 27% | +2.000 | -1.019 | -0.160 | **-0.203** | 0.727 | 14.3% | -0.497 to +0.118 | -0.588 to +0.227 | -0.235 |
| sweep_mss_fvg | development | 8 ⚠ < 30 trades: no conclusion | 25% | +1.121 | -1.021 | -0.469 | **-0.485** | 0.366 | 2.1% | -1.023 to +0.488 | -1.028 to +0.995 | -0.520 |
| sweep_mss_fvg | validation | 91 | 36% | +1.700 | -0.968 | +0.089 | **-0.001** | 0.999 | 7.9% | -0.255 to +0.254 | -0.351 to +0.355 | -0.031 |
| orb | development | 6 ⚠ < 30 trades: no conclusion | 50% | +1.235 | -1.019 | +0.298 | **+0.108** | 1.212 | 0.5% | -0.673 to +0.733 | -1.020 to +0.883 | +0.084 |
| orb | validation | 106 | 30% | +1.880 | -1.030 | -0.069 | **-0.151** | 0.790 | 12.0% | -0.407 to +0.110 | -0.495 to +0.233 | -0.191 |
| vwap_reversion | development | 28 ⚠ < 30 trades: no conclusion | 32% | +1.786 | -1.054 | -0.094 | **-0.141** | 0.803 | 3.6% | -0.727 to +0.192 | -1.056 to +0.229 | -0.215 |
| vwap_reversion | validation | 564 | 32% | +1.937 | -1.065 | +0.032 | **-0.101** | 0.860 | 27.5% | -0.205 to -0.004 | -0.242 to +0.043 | -0.191 |
| silver_bullet | development | 3 ⚠ < 30 trades: no conclusion | 33% | +2.000 | -1.015 | +0.000 | **-0.010** | 0.985 | 1.0% | -1.016 to +2.000 | -1.016 to +2.000 | -0.034 |
| silver_bullet | validation | 67 | 42% | +1.950 | -0.995 | +0.291 | **+0.236** | 1.407 | 3.0% | -0.122 to +0.588 | -0.250 to +0.721 | +0.210 |
| london_trend_fvg | development | 3 ⚠ < 30 trades: no conclusion | 33% | +2.000 | -1.040 | -0.250 | **-0.027** | 0.962 | 1.0% | -1.043 to +2.000 | -1.043 to +2.000 | -0.090 |
| london_trend_fvg | validation | 98 | 28% | +2.000 | -1.039 | +0.077 | **-0.202** | 0.732 | 13.7% | -0.449 to +0.064 | -0.540 to +0.159 | -0.270 |
| london_sweep_mss_fvg | development | 2 ⚠ < 30 trades: no conclusion | 0% | – | -1.041 | -1.000 | **-1.041** | 0.000 | 1.0% | -1.058 to -1.024 | -1.058 to -1.024 | -1.123 |
| london_sweep_mss_fvg | validation | 50 | 16% | +2.000 | -1.048 | -0.365 | **-0.560** | 0.364 | 15.7% | -0.907 to -0.175 | -0.987 to -0.031 | -0.646 |

## 2. Where the costs go — identical trades (model B)

Same fills with and without costs, per trade in R: gross − spread − slippage − fees = net. The last column is the largest per-trade reconciliation error.

| strategy | split | trades | gross | spread | slippage | fees | net | max error |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 3 | +1.000 | -0.063 | -0.008 | -0.000 | **+0.928** | 0.0e+00 |
| trend_fvg | validation | 75 | -0.160 | -0.056 | -0.013 | -0.000 | **-0.230** | 2.2e-16 |
| sweep_mss_fvg | development | 8 | -0.469 | -0.054 | -0.016 | -0.000 | **-0.540** | 2.2e-16 |
| sweep_mss_fvg | validation | 93 | +0.089 | -0.054 | -0.013 | -0.000 | **+0.023** | 2.2e-16 |
| orb | development | 6 | +0.298 | -0.025 | -0.014 | -0.000 | **+0.258** | 2.2e-16 |
| orb | validation | 106 | -0.069 | -0.045 | -0.025 | -0.000 | **-0.139** | 2.2e-16 |
| vwap_reversion | development | 28 | -0.094 | -0.089 | -0.049 | -0.000 | **-0.232** | 2.2e-16 |
| vwap_reversion | validation | 567 | +0.032 | -0.103 | -0.057 | -0.000 | **-0.127** | 2.2e-16 |
| silver_bullet | development | 3 | +0.000 | -0.039 | -0.010 | -0.000 | **-0.049** | 2.2e-16 |
| silver_bullet | validation | 67 | +0.291 | -0.049 | -0.009 | -0.000 | **+0.233** | 2.2e-16 |
| london_trend_fvg | development | 4 | -0.250 | -0.116 | -0.031 | -0.000 | **-0.397** | 2.2e-16 |
| london_trend_fvg | validation | 117 | +0.077 | -0.123 | -0.025 | -0.000 | **-0.072** | 2.2e-16 |
| london_sweep_mss_fvg | development | 2 | -1.000 | -0.123 | -0.041 | -0.000 | **-1.164** | 0.0e+00 |
| london_sweep_mss_fvg | validation | 52 | -0.365 | -0.138 | -0.036 | -0.000 | **-0.540** | 2.2e-16 |

## 3. Fill model: bid-only (B) → real bid/ask (R)

Total R changes for two reasons: the same trades get a different result (real spread instead of 1.5, stops and targets touched on the ask), and some trades fill only in one model. `total R − total B = matched change + R-only − B-only` (residual must be 0). The last column is the average real quoted spread at the buy leg (estimate, R per trade).

| strategy | split | matched | B-only | R-only | total B | total R | matched change | + R-only | − B-only | residual | real spread |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 3 | 0 | 0 | +2.8 | +3.0 | +0.2 | +0.0 | -0.0 | 0.0e+00 | -0.052 |
| trend_fvg | validation | 62 | 13 | 12 | -17.2 | -15.0 | +3.5 | -3.2 | +1.9 | 1.8e-15 | -0.050 |
| sweep_mss_fvg | development | 4 | 4 | 4 | -4.3 | -3.9 | +0.2 | -1.1 | +1.3 | 1.1e-16 | -0.042 |
| sweep_mss_fvg | validation | 85 | 8 | 6 | +2.1 | -0.1 | +1.5 | +4.7 | -8.3 | -2.2e-15 | -0.046 |
| orb | development | 6 | 0 | 0 | +1.5 | +0.6 | -0.9 | +0.0 | -0.0 | 2.2e-16 | -0.022 |
| orb | validation | 106 | 0 | 0 | -14.8 | -16.0 | -1.3 | +0.0 | -0.0 | 3.8e-15 | -0.038 |
| vwap_reversion | development | 28 | 0 | 0 | -6.5 | -3.9 | +2.6 | +0.0 | -0.0 | 4.4e-16 | -0.067 |
| vwap_reversion | validation | 559 | 8 | 5 | -72.2 | -57.1 | +25.9 | -5.5 | -5.2 | -9.6e-14 | -0.088 |
| silver_bullet | development | 2 | 1 | 1 | -0.1 | -0.0 | +0.1 | -1.0 | +1.1 | 0.0e+00 | -0.022 |
| silver_bullet | validation | 59 | 8 | 8 | +15.6 | +15.8 | -0.1 | +7.0 | -6.6 | -2.7e-15 | -0.043 |
| london_trend_fvg | development | 2 | 2 | 1 | -1.6 | -0.1 | +0.2 | +2.0 | -0.7 | 0.0e+00 | -0.250 |
| london_trend_fvg | validation | 58 | 59 | 40 | -8.4 | -19.8 | -2.8 | -11.3 | +2.7 | -1.8e-15 | -0.263 |
| london_sweep_mss_fvg | development | 2 | 0 | 0 | -2.3 | -2.1 | +0.2 | +0.0 | -0.0 | 2.2e-16 | -0.254 |
| london_sweep_mss_fvg | validation | 37 | 15 | 13 | -28.1 | -28.0 | -1.1 | -4.5 | +5.6 | 0.0e+00 | -0.308 |

## 4. By year (model R; gross from model G)

| strategy | year | trades | win rate | gross | net | profit factor | max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| trend_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2022 (data 21/260 days) | 3 | 67% | +1.000 | +0.992 | 3.903 | 0.5% |
| trend_fvg | 2023 | 63 | 27% | -0.156 | -0.204 | 0.726 | 13.4% |
| trend_fvg | 2024 (data 63/262 days) | 11 | 27% | -0.182 | -0.196 | 0.736 | 2.5% |
| sweep_mss_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2022 (data 21/260 days) | 8 | 25% | -0.469 | -0.485 | 0.366 | 2.1% |
| sweep_mss_fvg | 2023 | 76 | 36% | +0.038 | -0.028 | 0.955 | 7.9% |
| sweep_mss_fvg | 2024 (data 63/262 days) | 15 | 40% | +0.352 | +0.139 | 1.245 | 1.0% |
| orb | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| orb | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| orb | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| orb | 2022 (data 21/260 days) | 6 | 50% | +0.298 | +0.108 | 1.212 | 0.5% |
| orb | 2023 | 83 | 28% | -0.151 | -0.213 | 0.714 | 10.5% |
| orb | 2024 (data 63/262 days) | 23 | 39% | +0.224 | +0.070 | 1.112 | 3.1% |
| vwap_reversion | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2022 (data 21/260 days) | 28 | 32% | -0.094 | -0.141 | 0.803 | 3.6% |
| vwap_reversion | 2023 | 454 | 32% | +0.029 | -0.104 | 0.857 | 23.9% |
| vwap_reversion | 2024 (data 63/262 days) | 110 | 32% | +0.045 | -0.091 | 0.873 | 5.7% |
| silver_bullet | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2022 (data 21/260 days) | 3 | 33% | +0.000 | -0.010 | 0.985 | 1.0% |
| silver_bullet | 2023 | 55 | 44% | +0.379 | +0.315 | 1.564 | 3.0% |
| silver_bullet | 2024 (data 63/262 days) | 12 | 33% | -0.111 | -0.125 | 0.815 | 1.6% |
| london_trend_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2022 (data 21/260 days) | 3 | 33% | -0.250 | -0.027 | 0.962 | 1.0% |
| london_trend_fvg | 2023 | 87 | 28% | +0.096 | -0.201 | 0.733 | 13.7% |
| london_trend_fvg | 2024 (data 63/262 days) | 11 | 27% | -0.077 | -0.211 | 0.721 | 4.1% |
| london_sweep_mss_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2022 (data 21/260 days) | 2 | 0% | -1.000 | -1.041 | 0.000 | 1.0% |
| london_sweep_mss_fvg | 2023 | 41 | 15% | -0.488 | -0.600 | 0.328 | 13.4% |
| london_sweep_mss_fvg | 2024 (data 63/262 days) | 9 | 22% | +0.091 | -0.378 | 0.540 | 3.6% |

Trades of all models: `backend/data/reports/bidask_full_trades.csv`.

