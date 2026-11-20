# Bid/ask re-test 2019–2024 — results (INCOMPLETE DATA)

Made by `scripts/bidask_full_retest.py` on 2026-11-20 (`cd backend; .\.venv\Scripts\python scripts\bidask_full_retest.py`). Rules fixed in `docs/bidask_full_preregistration.md` (commit f69e58c) before this run. Measurement only: nothing can qualify; `scanner.QUALIFIED` stays empty; 2025+ is not loaded.

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

- Dukascopy USATECHIDXUSD BID + ASK, minutes with both quotes: 732,044 (2018-12-02 .. 2024-12-31). December 2018 is warm-up only. No missing minute is filled in; no synthetic ask is used.
- Minutes where ask < bid: 0.
- Coverage needed for a verdict: ≥ 90% of weekdays. development 2019-2022: 2%; validation 2023-2024: 99%.

| year | weekdays | with bid+ask | valid sessions | missing months (weekdays missing) |
|---|---:|---:|---:|---|
| 2019 | 261 | 0 | 0 | 2019-01 (23), 2019-02 (20), 2019-03 (21), 2019-04 (22), 2019-05 (23), 2019-06 (20), 2019-07 (23), 2019-08 (22), 2019-09 (21), 2019-10 (23), 2019-11 (21), 2019-12 (22) |
| 2020 | 262 | 0 | 0 | 2020-01 (23), 2020-02 (20), 2020-03 (22), 2020-04 (22), 2020-05 (21), 2020-06 (22), 2020-07 (23), 2020-08 (21), 2020-09 (22), 2020-10 (22), 2020-11 (21), 2020-12 (23) |
| 2021 | 261 | 0 | 0 | 2021-01 (21), 2021-02 (20), 2021-03 (23), 2021-04 (22), 2021-05 (21), 2021-06 (22), 2021-07 (22), 2021-08 (22), 2021-09 (22), 2021-10 (21), 2021-11 (22), 2021-12 (23) |
| 2022 | 260 | 21 | 21 | 2022-01 (21), 2022-02 (20), 2022-03 (23), 2022-04 (21), 2022-05 (22), 2022-06 (22), 2022-07 (21), 2022-08 (23), 2022-09 (22), 2022-10 (21), 2022-11 (22) |
| 2023 | 260 | 257 | 247 | none (holidays only) |
| 2024 | 262 | 259 | 245 | none (holidays only) |

**Clock / daylight-saving check** (amendment 1 in the plan): the median 1-minute move must jump at 09:30 NY (≥ 1.5 × 09:29) and be larger than at 08:30 and 10:30, where a one-hour DST error would put it. Top minute shown for information.

| year | regime | ~days | 09:30 ÷ 09:29 | 08:30 | 09:30 | 10:30 | top minute | ok |
|---|---|---:|---:|---:|---:|---:|---|---|
| 2022 | US winter | 20 | 3.8× | 6.99 | 12.94 | 12.01 | 09:30 | yes |
| 2023 | US summer | 152 | 4.0× | 4.56 | 11.03 | 5.33 | 09:30 | yes |
| 2023 | US winter | 86 | 4.9× | 4.43 | 12.57 | 4.21 | 09:30 | yes |
| 2023 | US/UK mismatch | 15 | 2.6× | 4.55 | 9.15 | 5.08 | 09:56 | yes |
| 2024 | US summer | 148 | 3.4× | 5.22 | 10.30 | 6.13 | 09:30 | yes |
| 2024 | US winter | 88 | 4.6× | 4.47 | 11.86 | 6.06 | 09:30 | yes |
| 2024 | US/UK mismatch | 19 | 2.8× | 4.83 | 11.29 | 6.78 | 09:31 | yes |

**Second source** (Dukascopy bid close vs HistData close on shared minutes):

| year | shared minutes | median abs diff | p99 abs diff |
|---|---:|---:|---:|
| 2022 | 27,971 | 0.000 | 0.000 |
| 2023 | 299,229 | 0.000 | 0.000 |
| 2024 | 340,865 | 0.000 | 0.000 |

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
| trend_fvg | development | 4 ⚠ < 30 trades: no conclusion | 50% | +2.000 | -1.019 | +0.500 | **+0.491** | 1.963 | 0.5% | -1.013 to +2.000 | -1.013 to +2.000 | +0.462 |
| trend_fvg | validation | 114 | 30% | +1.963 | -1.017 | -0.011 | **-0.128** | 0.820 | 15.2% | -0.366 to +0.118 | -0.459 to +0.201 | -0.158 |
| sweep_mss_fvg | development | 8 ⚠ < 30 trades: no conclusion | 25% | +1.121 | -1.021 | -0.469 | **-0.485** | 0.366 | 2.1% | -1.023 to +0.488 | -1.028 to +0.995 | -0.520 |
| sweep_mss_fvg | validation | 138 | 38% | +1.772 | -0.980 | +0.138 | **+0.077** | 1.127 | 7.9% | -0.151 to +0.301 | -0.239 to +0.366 | +0.048 |
| orb | development | 6 ⚠ < 30 trades: no conclusion | 50% | +1.235 | -1.019 | +0.298 | **+0.108** | 1.212 | 0.5% | -0.673 to +0.733 | -1.020 to +0.883 | +0.084 |
| orb | validation | 176 | 35% | +1.890 | -1.024 | +0.061 | **-0.014** | 0.979 | 12.0% | -0.227 to +0.206 | -0.300 to +0.295 | -0.052 |
| vwap_reversion | development | 28 ⚠ < 30 trades: no conclusion | 32% | +1.786 | -1.054 | -0.094 | **-0.141** | 0.803 | 3.6% | -0.727 to +0.192 | -1.056 to +0.229 | -0.215 |
| vwap_reversion | validation | 875 | 31% | +1.918 | -1.058 | +0.005 | **-0.133** | 0.818 | 48.0% | -0.215 to -0.052 | -0.251 to -0.024 | -0.216 |
| silver_bullet | development | 3 ⚠ < 30 trades: no conclusion | 33% | +2.000 | -1.015 | +0.000 | **-0.010** | 0.985 | 1.0% | -1.016 to +2.000 | -1.016 to +2.000 | -0.034 |
| silver_bullet | validation | 98 | 36% | +1.960 | -0.997 | +0.101 | **+0.059** | 1.092 | 8.2% | -0.226 to +0.358 | -0.327 to +0.450 | +0.033 |
| london_trend_fvg | development | 5 ⚠ < 30 trades: no conclusion | 20% | +2.000 | -1.036 | -0.500 | **-0.429** | 0.483 | 1.1% | -1.040 to +1.239 | -1.043 to +1.241 | -0.492 |
| london_trend_fvg | validation | 149 | 26% | +2.000 | -1.037 | +0.011 | **-0.262** | 0.660 | 19.5% | -0.472 to -0.049 | -0.541 to +0.021 | -0.327 |
| london_sweep_mss_fvg | development | 2 ⚠ < 30 trades: no conclusion | 0% | – | -1.041 | -1.000 | **-1.041** | 0.000 | 1.0% | -1.058 to -1.024 | -1.058 to -1.024 | -1.123 |
| london_sweep_mss_fvg | validation | 71 | 18% | +2.000 | -1.047 | -0.232 | **-0.489** | 0.428 | 20.1% | -0.775 to -0.174 | -0.867 to -0.060 | -0.571 |

## 2. Where the costs go — identical trades (model B)

Same fills with and without costs, per trade in R: gross − spread − slippage − fees = net. The last column is the largest per-trade reconciliation error.

| strategy | split | trades | gross | spread | slippage | fees | net | max error |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 4 | +0.500 | -0.057 | -0.009 | -0.000 | **+0.434** | 0.0e+00 |
| trend_fvg | validation | 117 | -0.011 | -0.051 | -0.011 | -0.000 | **-0.074** | 2.2e-16 |
| sweep_mss_fvg | development | 8 | -0.469 | -0.054 | -0.016 | -0.000 | **-0.540** | 2.2e-16 |
| sweep_mss_fvg | validation | 140 | +0.138 | -0.051 | -0.011 | -0.000 | **+0.076** | 2.2e-16 |
| orb | development | 6 | +0.298 | -0.025 | -0.014 | -0.000 | **+0.258** | 2.2e-16 |
| orb | validation | 176 | +0.061 | -0.043 | -0.024 | -0.000 | **-0.005** | 2.2e-16 |
| vwap_reversion | development | 28 | -0.094 | -0.089 | -0.049 | -0.000 | **-0.232** | 2.2e-16 |
| vwap_reversion | validation | 882 | +0.005 | -0.095 | -0.053 | -0.000 | **-0.143** | 2.2e-16 |
| silver_bullet | development | 3 | +0.000 | -0.039 | -0.010 | -0.000 | **-0.049** | 2.2e-16 |
| silver_bullet | validation | 98 | +0.101 | -0.047 | -0.010 | -0.000 | **+0.044** | 2.2e-16 |
| london_trend_fvg | development | 6 | -0.500 | -0.109 | -0.031 | -0.000 | **-0.641** | 2.2e-16 |
| london_trend_fvg | validation | 175 | +0.011 | -0.116 | -0.025 | -0.000 | **-0.130** | 2.2e-16 |
| london_sweep_mss_fvg | development | 2 | -1.000 | -0.123 | -0.041 | -0.000 | **-1.164** | 0.0e+00 |
| london_sweep_mss_fvg | validation | 73 | -0.232 | -0.132 | -0.033 | -0.000 | **-0.397** | 2.2e-16 |

## 3. Fill model: bid-only (B) → real bid/ask (R)

Total R changes for two reasons: the same trades get a different result (real spread instead of 1.5, stops and targets touched on the ask), and some trades fill only in one model. `total R − total B = matched change + R-only − B-only` (residual must be 0). The last column is the average real quoted spread at the buy leg (estimate, R per trade).

| strategy | split | matched | B-only | R-only | total B | total R | matched change | + R-only | − B-only | residual | real spread |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 4 | 0 | 0 | +1.7 | +2.0 | +0.2 | +0.0 | -0.0 | 0.0e+00 | -0.046 |
| trend_fvg | validation | 99 | 18 | 15 | -8.6 | -14.6 | -1.0 | -0.2 | -4.8 | -1.8e-15 | -0.046 |
| sweep_mss_fvg | development | 4 | 4 | 4 | -4.3 | -3.9 | +0.2 | -1.1 | +1.3 | -2.2e-16 | -0.042 |
| sweep_mss_fvg | validation | 125 | 15 | 13 | +10.6 | +10.6 | +3.3 | +5.7 | -9.0 | 0.0e+00 | -0.044 |
| orb | development | 6 | 0 | 0 | +1.5 | +0.6 | -0.9 | +0.0 | -0.0 | 2.2e-16 | -0.022 |
| orb | validation | 176 | 0 | 0 | -0.9 | -2.5 | -1.6 | +0.0 | -0.0 | -1.1e-15 | -0.037 |
| vwap_reversion | development | 28 | 0 | 0 | -6.5 | -3.9 | +2.6 | +0.0 | -0.0 | 4.4e-16 | -0.067 |
| vwap_reversion | validation | 869 | 13 | 6 | -126.2 | -116.4 | +15.9 | -6.6 | +0.5 | -9.8e-14 | -0.082 |
| silver_bullet | development | 2 | 1 | 1 | -0.1 | -0.0 | +0.1 | -1.0 | +1.1 | 0.0e+00 | -0.022 |
| silver_bullet | validation | 87 | 11 | 11 | +4.3 | +5.8 | +1.0 | +6.9 | -6.5 | -1.8e-15 | -0.041 |
| london_trend_fvg | development | 4 | 2 | 1 | -3.8 | -2.1 | +0.4 | +2.0 | -0.7 | 0.0e+00 | -0.243 |
| london_trend_fvg | validation | 89 | 86 | 60 | -22.7 | -39.1 | -3.4 | -20.0 | +6.9 | 3.6e-15 | -0.249 |
| london_sweep_mss_fvg | development | 2 | 0 | 0 | -2.3 | -2.1 | +0.2 | +0.0 | -0.0 | 2.2e-16 | -0.254 |
| london_sweep_mss_fvg | validation | 53 | 20 | 18 | -29.0 | -34.7 | -5.2 | -3.6 | +3.2 | -8.9e-16 | -0.299 |

## 4. By year (model R; gross from model G)

| strategy | year | trades | win rate | gross | net | profit factor | max DD |
|---|---|---:|---:|---:|---:|---:|---:|
| trend_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| trend_fvg | 2022 (data 21/260 days) | 4 | 50% | +0.500 | +0.491 | 1.963 | 0.5% |
| trend_fvg | 2023 | 63 | 27% | -0.156 | -0.204 | 0.726 | 13.4% |
| trend_fvg | 2024 | 51 | 33% | +0.165 | -0.035 | 0.948 | 3.5% |
| sweep_mss_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| sweep_mss_fvg | 2022 (data 21/260 days) | 8 | 25% | -0.469 | -0.485 | 0.366 | 2.1% |
| sweep_mss_fvg | 2023 | 76 | 36% | +0.038 | -0.028 | 0.955 | 7.9% |
| sweep_mss_fvg | 2024 | 62 | 42% | +0.265 | +0.206 | 1.358 | 4.4% |
| orb | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| orb | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| orb | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| orb | 2022 (data 21/260 days) | 6 | 50% | +0.298 | +0.108 | 1.212 | 0.5% |
| orb | 2023 | 83 | 28% | -0.151 | -0.213 | 0.714 | 10.5% |
| orb | 2024 | 93 | 41% | +0.250 | +0.163 | 1.270 | 3.8% |
| vwap_reversion | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| vwap_reversion | 2022 (data 21/260 days) | 28 | 32% | -0.094 | -0.141 | 0.803 | 3.6% |
| vwap_reversion | 2023 | 454 | 32% | +0.029 | -0.104 | 0.857 | 23.9% |
| vwap_reversion | 2024 | 421 | 30% | -0.022 | -0.165 | 0.776 | 32.4% |
| silver_bullet | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| silver_bullet | 2022 (data 21/260 days) | 3 | 33% | +0.000 | -0.010 | 0.985 | 1.0% |
| silver_bullet | 2023 | 55 | 44% | +0.379 | +0.315 | 1.564 | 3.0% |
| silver_bullet | 2024 | 43 | 26% | -0.256 | -0.268 | 0.641 | 8.2% |
| london_trend_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_trend_fvg | 2022 (data 21/260 days) | 5 | 20% | -0.500 | -0.429 | 0.483 | 1.1% |
| london_trend_fvg | 2023 | 87 | 28% | +0.096 | -0.201 | 0.733 | 13.7% |
| london_trend_fvg | 2024 | 62 | 23% | -0.113 | -0.349 | 0.564 | 13.0% |
| london_sweep_mss_fvg | 2019 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2020 (data 0/262 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2021 (data 0/261 days) | 0 | – | – | – | – | 0.0% |
| london_sweep_mss_fvg | 2022 (data 21/260 days) | 2 | 0% | -1.000 | -1.041 | 0.000 | 1.0% |
| london_sweep_mss_fvg | 2023 | 41 | 15% | -0.488 | -0.600 | 0.328 | 13.4% |
| london_sweep_mss_fvg | 2024 | 30 | 23% | +0.095 | -0.337 | 0.581 | 8.7% |

Trades of all models: `backend/data/reports/bidask_full_trades.csv`.

