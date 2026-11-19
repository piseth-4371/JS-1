# Exness cost gate — results

Made by `scripts/exness_cost_gate.py` on 2026-11-19 from `backtest_trades.csv` (4,774 NAS100 trades). Rules were committed first: `docs/exness_cost_gate_preregistration.md`.
Measurement only: no strategy, risk limit or `scanner.QUALIFIED` changed.

Input check: largest difference from the backtest cost model = 4.44e-16 (PASS).

**Backtest** = average R per trade with the 1.5-point spread. **Exness** = with 2.94 points (highest 2021-23 median). **Stress** = with the highest p90 (3.29 pre-US, 3.65 US). **Family range** = 95% range of the Exness average, widened for 7 strategies.

| strategy | split | trades | backtest | Exness | family range | stress | verdict |
|---|---|---:|---:|---:|---|---:|---|
| london_sweep_mss_fvg | 2019-22 | 124 | -0.328 | -0.485 | -0.808 to -0.136 | -0.523 | not eligible — failed its main test |
| london_sweep_mss_fvg | 2023-24 | 74 | -0.369 | -0.498 | -0.899 to -0.036 | -0.529 |  |
| london_trend_fvg | 2019-22 | 306 | -0.354 | -0.507 | -0.722 to -0.277 | -0.544 | not eligible — failed its main test |
| london_trend_fvg | 2023-24 | 174 | -0.237 | -0.350 | -0.711 to -0.052 | -0.377 |  |
| orb | 2019-22 | 259 | -0.007 | -0.070 | -0.290 to +0.160 | -0.102 | not eligible — failed its main test |
| orb | 2023-24 | 160 | -0.066 | -0.109 | -0.423 to +0.219 | -0.131 |  |
| silver_bullet | 2019-22 | 212 | -0.070 | -0.144 | -0.404 to +0.123 | -0.180 | not eligible — failed its main test |
| silver_bullet | 2023-24 | 80 | -0.108 | -0.156 | -0.545 to +0.273 | -0.180 |  |
| sweep_mss_fvg | 2019-22 | 270 | -0.169 | -0.238 | -0.448 to -0.007 | -0.272 | not eligible — failed its main test |
| sweep_mss_fvg | 2023-24 | 127 | +0.150 | +0.100 | -0.214 to +0.416 | +0.075 |  |
| trend_fvg | 2019-22 | 244 | -0.064 | -0.139 | -0.377 to +0.083 | -0.176 | not eligible — failed its main test |
| trend_fvg | 2023-24 | 100 | -0.185 | -0.238 | -0.587 to +0.107 | -0.265 |  |
| vwap_reversion | 2019-22 | 1823 | -0.310 | -0.451 | -0.540 to -0.362 | -0.521 | not eligible — failed its main test |
| vwap_reversion | 2023-24 | 821 | -0.211 | -0.302 | -0.435 to -0.179 | -0.347 |  |

On average the wider Exness spread costs **0.109R more per trade** than the backtest assumed (median risk 18.3 points).

## Limits
- Quoted spread only (last tick per minute); commission and account type not included.
- One flat value per window; news spikes and the open are only covered by the p90 stress.
- 2019, 2020 and 2024 trades use 2021-2023 Exness levels.
