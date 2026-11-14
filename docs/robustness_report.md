# Robustness report (NAS100 (weekdays)) — generated 2026-11-14 12:34 UTC

- Data: histdata NSXUSD up to 2024-12-31; out-of-sample (2025+) locked
- Base costs: Costs(spread=1.5, slippage=0.5, fee_pct=0.0, slip_pct=0.0); 'costs x2' doubles every cost; targets 2.5R/3.0R use the same entries
- Bootstrap: 5,000 resamples; Monte Carlo: 2,000 shuffles at 0.5% risk per trade

| strategy | split | trades | base avg R | costs x2 | 2.5R | 3.0R | avg R 90% range | P(no edge) | max DD p95 % | losing streak p95 | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| trend_fvg | development | 244 | -0.06 | -0.16 | -0.09 | -0.13 | -0.21 to 0.09 | 76% | 19.6 | 16 | NOT robust |
| trend_fvg | validation | 100 | -0.18 | -0.25 | -0.11 | -0.07 | -0.41 to 0.04 | 91% | 15.1 | 16 | NOT robust |
| sweep_mss_fvg | development | 270 | -0.17 | -0.26 | -0.17 | -0.13 | -0.31 to -0.03 | 98% | 28.0 | 18 | NOT robust |
| sweep_mss_fvg | validation | 127 | 0.15 | 0.09 | 0.16 | 0.03 | -0.06 to 0.36 | 11% | 9.0 | 11 | NOT robust |
| orb | development | 259 | -0.01 | -0.11 | 0.03 | 0.09 | -0.15 to 0.14 | 54% | 17.4 | 15 | NOT robust |
| orb | validation | 160 | -0.07 | -0.14 | 0.02 | 0.05 | -0.26 to 0.12 | 72% | 15.6 | 14 | NOT robust |
| vwap_reversion | development | 1823 | -0.31 | -0.54 | -0.32 | -0.32 | -0.36 to -0.26 | 100% | 94.7 | 24 | NOT robust |
| vwap_reversion | validation | 821 | -0.21 | -0.36 | -0.22 | -0.20 | -0.30 to -0.13 | 100% | 62.8 | 21 | NOT robust |
| silver_bullet | development | 212 | -0.07 | -0.16 | -0.13 | -0.09 | -0.22 to 0.09 | 76% | 18.4 | 15 | NOT robust |
| silver_bullet | validation | 80 | -0.11 | -0.17 | -0.10 | -0.14 | -0.36 to 0.14 | 76% | 11.4 | 14 | NOT robust |
| london_trend_fvg | development | 306 | -0.35 | -0.55 | -0.38 | -0.35 | -0.48 to -0.22 | 100% | 45.4 | 21 | NOT robust |
| london_trend_fvg | validation | 174 | -0.24 | -0.38 | -0.14 | -0.08 | -0.45 to -0.04 | 97% | 25.6 | 17 | NOT robust |
| london_sweep_mss_fvg | development | 124 | -0.33 | -0.53 | -0.27 | -0.17 | -0.53 to -0.12 | 99% | 22.9 | 17 | NOT robust |
| london_sweep_mss_fvg | validation | 74 | -0.37 | -0.54 | -0.38 | -0.33 | -0.62 to -0.12 | 99% | 16.5 | 16 | NOT robust |

**Reading this:** 'robust in this split' needs avg R > 0 at base, with double costs, at 2.5R and 3.0R, and less than a 10% bootstrap chance that the true edge is ≤ 0, with ≥ 30 trades. A strategy must be robust in BOTH development and validation. Max DD p95 = 1 in 20 trade orders would be worse. Past results do not guarantee future results.
