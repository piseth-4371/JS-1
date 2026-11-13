# Robustness report (BTC (weekends)) — generated 2026-11-13 07:38 UTC

- Data: binance BTCUSDT up to 2024-12-31; out-of-sample (2025+) locked
- Base costs: Costs(spread=0.0, slippage=0.0, fee_pct=0.1, slip_pct=0.02); 'costs x2' doubles every cost; targets 2.5R/3.0R use the same entries
- Bootstrap: 5,000 resamples; Monte Carlo: 2,000 shuffles at 0.5% risk per trade

| strategy | split | trades | base avg R | costs x2 | 2.5R | 3.0R | avg R 90% range | P(no edge) | max DD p95 % | losing streak p95 | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| btc_weekend_trend_fvg | development | 765 | -0.50 | -0.96 | -0.50 | -0.49 | -0.58 to -0.41 | 100% | 85.9 | 21 | NOT robust |
| btc_weekend_trend_fvg | validation | 428 | -1.26 | -2.22 | -1.27 | -1.32 | -1.38 to -1.13 | 100% | 93.5 | 25 | NOT robust |

**Reading this:** 'robust in this split' needs avg R > 0 at base, with double costs, at 2.5R and 3.0R, and less than a 10% bootstrap chance that the true edge is ≤ 0, with ≥ 30 trades. A strategy must be robust in BOTH development and validation. Max DD p95 = 1 in 20 trade orders would be worse. Past results do not guarantee future results.
