# Robustness report (BTC (weekends)) — generated 2026-11-13 07:51 UTC

- Data: binance BTCUSDT up to 2024-12-31; out-of-sample (2025+) locked
- Base costs: Costs(spread=0.0, slippage=0.0, fee_pct=0.1, slip_pct=0.02); 'costs x2' doubles every cost; targets 2.5R/3.0R use the same entries
- Bootstrap: 5,000 resamples; Monte Carlo: 2,000 shuffles at 0.5% risk per trade

| strategy | split | trades | base avg R | costs x2 | 2.5R | 3.0R | avg R 90% range | P(no edge) | max DD p95 % | losing streak p95 | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| btc_weekend_trend_fvg | development | 765 | -0.50 | -0.96 | -0.50 | -0.49 | -0.58 to -0.41 | 100% | 85.9 | 21 | NOT robust |
| btc_weekend_trend_fvg | validation | 428 | -1.26 | -2.22 | -1.27 | -1.32 | -1.38 to -1.13 | 100% | 93.5 | 25 | NOT robust |
| btc_weekend_sweep_mss_fvg | development | 114 | -0.58 | -1.06 | -0.59 | -0.49 | -0.82 to -0.36 | 100% | 31.1 | 16 | NOT robust |
| btc_weekend_sweep_mss_fvg | validation | 57 | -0.62 | -1.50 | -0.56 | -0.63 | -1.14 to -0.17 | 99% | 20.3 | 10 | NOT robust |
| btc_weekend_orb | development | 335 | -0.47 | -1.02 | -0.47 | -0.43 | -0.60 to -0.33 | 100% | 56.9 | 16 | NOT robust |
| btc_weekend_orb | validation | 188 | -1.31 | -2.52 | -1.36 | -1.44 | -1.54 to -1.10 | 100% | 71.8 | 20 | NOT robust |
| btc_weekend_vwap_reversion | development | 1485 | -0.80 | -1.54 | -0.81 | -0.83 | -0.87 to -0.73 | 100% | 99.8 | 22 | NOT robust |
| btc_weekend_vwap_reversion | validation | 641 | -1.59 | -3.95 | -1.59 | -1.62 | -1.74 to -1.44 | 100% | 99.4 | 23 | NOT robust |
| btc_weekend_silver_bullet | development | 39 | -0.67 | -1.26 | -0.70 | -0.64 | -1.05 to -0.28 | 100% | 14.7 | 12 | NOT robust |
| btc_weekend_silver_bullet | validation | 34 | -2.09 | -3.88 | -2.08 | -2.26 | -2.85 to -1.39 | 100% | 30.9 | 17 | NOT robust |

**Reading this:** 'robust in this split' needs avg R > 0 at base, with double costs, at 2.5R and 3.0R, and less than a 10% bootstrap chance that the true edge is ≤ 0, with ≥ 30 trades. A strategy must be robust in BOTH development and validation. Max DD p95 = 1 in 20 trade orders would be worse. Past results do not guarantee future results.
