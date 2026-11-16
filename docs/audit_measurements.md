# Audit measurements (2019-2024 only; 2025+ untouched)

Made by `scripts/audit_measurements.py` on 2026-11-16. HistData NSXUSD 1-minute BID bars. Risk 0.5% per trade. R = net points / risk at the fill (engine convention). Every number below is after the audit fixes; earlier reports are kept unchanged for history.

## 1. Reproducibility of the saved backtest

| strategy | saved trades | re-run trades | saved total R | re-run total R | identical |
|---|---:|---:|---:|---:|---|
| trend_fvg | 344 | 344 | -34.20 | -34.20 | yes |
| sweep_mss_fvg | 397 | 397 | -26.47 | -26.47 | yes |
| orb | 419 | 419 | -12.46 | -12.46 | yes |
| vwap_reversion | 2644 | 2644 | -737.95 | -737.95 | yes |
| silver_bullet | 292 | 292 | -23.46 | -23.46 | yes |
| london_trend_fvg | 480 | 480 | -149.63 | -149.63 | yes |
| london_sweep_mss_fvg | 198 | 198 | -68.03 | -68.03 | yes |

## 2. Gross vs net, all sessions vs valid sessions (base costs: spread 1.5 + slippage 0.5 pts)

Cost/risk = cost of the trade in R (share of the initial risk). DD = max drawdown of the compounded 0.5% risk curve. 95% iid = avg ± 1.96·SE. Week 95% = bootstrap over ISO weeks. Family low = avg − z·SE with Bonferroni z for 36 versions. Share ≤ 0 = share of bootstrap resamples whose average is ≤ 0 (a frequency, not a probability of no edge).

| strategy | split | sessions | trades | gross avg R | net avg R | cost/risk mean | cost/risk median | max DD | 95% iid | 95% week | family low | share ≤ 0 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| trend_fvg | development | all sessions | 244 | +0.030 | -0.064 | 0.095 | 0.074 | 11.5% | -0.241 to +0.112 | -0.237 to +0.113 | -0.352 | 76% |
| trend_fvg | validation | all sessions | 100 | -0.115 | -0.185 | 0.069 | 0.057 | 15.2% | -0.455 to +0.086 | -0.432 to +0.081 | -0.626 | 91% |
| trend_fvg | development | valid sessions | 241 | +0.035 | -0.059 | 0.094 | 0.074 | 11.2% | -0.237 to +0.118 | -0.235 to +0.130 | -0.349 | 75% |
| trend_fvg | validation | valid sessions | 85 | -0.097 | -0.158 | 0.061 | 0.055 | 13.2% | -0.452 to +0.136 | -0.416 to +0.126 | -0.638 | 85% |
| sweep_mss_fvg | development | all sessions | 270 | -0.080 | -0.169 | 0.089 | 0.064 | 23.6% | -0.330 to -0.007 | -0.321 to -0.011 | -0.432 | 98% |
| sweep_mss_fvg | validation | all sessions | 127 | +0.213 | +0.150 | 0.063 | 0.048 | 4.6% | -0.105 to +0.404 | -0.084 to +0.384 | -0.265 | 13% |
| sweep_mss_fvg | development | valid sessions | 266 | -0.077 | -0.164 | 0.086 | 0.063 | 23.6% | -0.326 to -0.001 | -0.321 to +0.001 | -0.428 | 97% |
| sweep_mss_fvg | validation | valid sessions | 112 | +0.246 | +0.186 | 0.060 | 0.048 | 4.6% | -0.080 to +0.452 | -0.057 to +0.428 | -0.248 | 8% |
| orb | development | all sessions | 259 | +0.095 | -0.007 | 0.103 | 0.070 | 16.1% | -0.181 to +0.166 | -0.172 to +0.157 | -0.291 | 54% |
| orb | validation | all sessions | 160 | +0.006 | -0.066 | 0.071 | 0.061 | 15.8% | -0.290 to +0.158 | -0.305 to +0.183 | -0.431 | 72% |
| orb | development | valid sessions | 241 | +0.072 | -0.012 | 0.084 | 0.065 | 14.7% | -0.190 to +0.166 | -0.181 to +0.157 | -0.303 | 56% |
| orb | validation | valid sessions | 135 | +0.095 | +0.032 | 0.063 | 0.059 | 10.4% | -0.210 to +0.274 | -0.217 to +0.288 | -0.363 | 40% |
| vwap_reversion | development | all sessions | 1823 | -0.079 | -0.310 | 0.230 | 0.164 | 94.3% | -0.374 to -0.246 | -0.371 to -0.250 | -0.414 | 100% |
| vwap_reversion | validation | all sessions | 821 | -0.063 | -0.211 | 0.148 | 0.135 | 60.5% | -0.310 to -0.112 | -0.305 to -0.124 | -0.373 | 100% |
| vwap_reversion | development | valid sessions | 1778 | -0.084 | -0.310 | 0.226 | 0.163 | 93.9% | -0.375 to -0.245 | -0.373 to -0.250 | -0.416 | 100% |
| vwap_reversion | validation | valid sessions | 677 | -0.004 | -0.149 | 0.144 | 0.130 | 42.9% | -0.256 to -0.042 | -0.240 to -0.055 | -0.323 | 100% |
| silver_bullet | development | all sessions | 212 | +0.023 | -0.070 | 0.093 | 0.065 | 12.7% | -0.259 to +0.119 | -0.260 to +0.121 | -0.378 | 77% |
| silver_bullet | validation | all sessions | 80 | -0.045 | -0.108 | 0.062 | 0.051 | 10.4% | -0.418 to +0.202 | -0.408 to +0.191 | -0.613 | 76% |
| silver_bullet | development | valid sessions | 205 | +0.015 | -0.076 | 0.090 | 0.065 | 10.6% | -0.268 to +0.116 | -0.270 to +0.114 | -0.389 | 78% |
| silver_bullet | validation | valid sessions | 74 | +0.041 | -0.014 | 0.055 | 0.049 | 8.8% | -0.340 to +0.311 | -0.330 to +0.305 | -0.545 | 54% |
| london_trend_fvg | development | all sessions | 306 | -0.157 | -0.354 | 0.197 | 0.145 | 43.1% | -0.509 to -0.199 | -0.502 to -0.201 | -0.607 | 100% |
| london_trend_fvg | validation | all sessions | 174 | -0.094 | -0.237 | 0.143 | 0.139 | 21.3% | -0.484 to +0.009 | -0.488 to -0.004 | -0.640 | 97% |
| london_trend_fvg | development | valid sessions | 302 | -0.166 | -0.362 | 0.197 | 0.145 | 42.9% | -0.518 to -0.207 | -0.515 to -0.207 | -0.616 | 100% |
| london_trend_fvg | validation | valid sessions | 129 | +0.023 | -0.112 | 0.135 | 0.132 | 11.0% | -0.361 to +0.137 | -0.331 to +0.111 | -0.518 | 80% |
| london_sweep_mss_fvg | development | all sessions | 124 | -0.129 | -0.328 | 0.199 | 0.148 | 19.6% | -0.573 to -0.084 | -0.564 to -0.079 | -0.728 | 100% |
| london_sweep_mss_fvg | validation | all sessions | 74 | -0.202 | -0.369 | 0.167 | 0.148 | 16.4% | -0.676 to -0.062 | -0.675 to -0.049 | -0.870 | 99% |
| london_sweep_mss_fvg | development | valid sessions | 120 | -0.125 | -0.322 | 0.197 | 0.148 | 18.7% | -0.571 to -0.073 | -0.557 to -0.073 | -0.729 | 99% |
| london_sweep_mss_fvg | validation | valid sessions | 62 | -0.144 | -0.307 | 0.163 | 0.145 | 13.6% | -0.650 to +0.035 | -0.651 to +0.043 | -0.866 | 96% |

## 3. Cost stress (valid sessions; same trades re-priced; avg R per trade)

Scenarios fixed before running. 'measured-like' uses the MetaQuotes-Demo median spread (~0.9-1.0 pts; not Exness, slippage not measured). Re-pricing keeps the same entries and exits, so it ignores that higher costs would also change which later trades the daily-loss rules allow.

| strategy | split | trades | gross (no cost) | measured-like (1.0 / 0.5) | base (1.5 / 0.5) | spread x2 (3.0 / 0.5) | slippage x3 (1.5 / 1.5) | both (3.0 / 1.5) | DD at worst case |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 241 | +0.035 | -0.034 | -0.059 | -0.137 | -0.093 | -0.170 | 21.3% |
| trend_fvg | validation | 85 | -0.097 | -0.142 | -0.158 | -0.208 | -0.182 | -0.231 | 14.8% |
| sweep_mss_fvg | development | 266 | -0.077 | -0.140 | -0.164 | -0.234 | -0.196 | -0.266 | 32.0% |
| sweep_mss_fvg | validation | 112 | +0.246 | +0.202 | +0.186 | +0.136 | +0.165 | +0.115 | 5.0% |
| orb | development | 241 | +0.072 | +0.006 | -0.012 | -0.066 | -0.073 | -0.127 | 22.0% |
| orb | validation | 135 | +0.095 | +0.045 | +0.032 | -0.009 | -0.013 | -0.054 | 12.4% |
| vwap_reversion | development | 1778 | -0.084 | -0.262 | -0.310 | -0.455 | -0.473 | -0.618 | 99.6% |
| vwap_reversion | validation | 677 | -0.004 | -0.118 | -0.149 | -0.241 | -0.252 | -0.345 | 70.2% |
| silver_bullet | development | 205 | +0.015 | -0.051 | -0.076 | -0.150 | -0.109 | -0.183 | 18.5% |
| silver_bullet | validation | 74 | +0.041 | +0.001 | -0.014 | -0.059 | -0.034 | -0.079 | 10.5% |
| london_trend_fvg | development | 302 | -0.166 | -0.309 | -0.362 | -0.521 | -0.439 | -0.597 | 59.8% |
| london_trend_fvg | validation | 129 | +0.023 | -0.075 | -0.112 | -0.223 | -0.159 | -0.271 | 16.9% |
| london_sweep_mss_fvg | development | 120 | -0.125 | -0.269 | -0.322 | -0.484 | -0.394 | -0.556 | 29.1% |
| london_sweep_mss_fvg | validation | 62 | -0.144 | -0.263 | -0.307 | -0.439 | -0.370 | -0.502 | 18.3% |

## 4. Data and fill-model checks (all sessions, 2019-2024)

| strategy | trades | held through hole > 5 min | avg R of those | exit after 15:55 NY or next day | long limit fills where the bid stayed within 1 spread* | avg R of those | other long limit fills | avg R of those | short target exits where the bid stayed within 1 spread* | fill risk ≠ planned risk | avg R on planned risk | avg R on fill risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | 344 | 6 | +0.22 | 1 | 83 | -0.031 | 119 | +0.094 | 6 | 0 | -0.099 | -0.099 |
| sweep_mss_fvg | 397 | 7 | +0.60 | 0 | 50 | +0.073 | 118 | -0.128 | 18 | 0 | -0.067 | -0.067 |
| orb | 419 | 17 | +0.07 | 7 | 0 | +nan | 0 | +nan | 17 | 369 | -0.028 | -0.030 |
| vwap_reversion | 2644 | 39 | -0.50 | 12 | 0 | +nan | 0 | +nan | 183 | 2368 | -0.277 | -0.279 |
| silver_bullet | 292 | 1 | -1.74 | 0 | 49 | -0.118 | 90 | -0.217 | 16 | 0 | -0.080 | -0.080 |
| london_trend_fvg | 480 | 2 | -6.39 | 0 | 171 | -0.198 | 91 | -0.260 | 26 | 2 | -0.312 | -0.312 |
| london_sweep_mss_fvg | 198 | 2 | +0.40 | 0 | 37 | -0.014 | 38 | -0.124 | 16 | 2 | -0.343 | -0.344 |

\* The bars are BID prices. A buy (long entry, short exit) needs the ASK (about bid + spread) at the level. These fills/exits happened because the bid reached the level while staying within one spread of it, so with real quotes some would not have happened. Long limit fills are compared with the other long limit fills (a fair comparison: both groups are entries). Short target exits are only counted, because they are winners by construction; each one that would not have happened is an overstated result.

