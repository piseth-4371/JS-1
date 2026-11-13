# Robustness report (NAS100 (weekdays)) — generated 2026-11-13 07:01 UTC

- Data: dukascopy USATECHIDXUSD up to 2019-12-31; out-of-sample (2025+) locked
- Base costs: Costs(spread=1.5, slippage=0.5, fee_pct=0.0, slip_pct=0.0); 'costs x2' doubles every cost; targets 2.5R/3.0R use the same entries
- Bootstrap: 5,000 resamples; Monte Carlo: 2,000 shuffles at 0.5% risk per trade

| strategy | split | trades | base avg R | costs x2 | 2.5R | 3.0R | avg R 90% range | P(no edge) | max DD p95 % | losing streak p95 | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| orb | development | 72 | 0.09 | -0.10 | 0.22 | 0.31 | -0.20 … 0.38 | 31% | 8.1 | 10 | NOT robust |
| sweep_mss_fvg | development | 60 | 0.05 | -0.12 | 0.01 | 0.13 | -0.25 … 0.35 | 40% | 7.4 | 10 | NOT robust |
| trend_fvg | development | 63 | -0.07 | -0.24 | -0.13 | -0.31 | -0.36 … 0.22 | 65% | 9.2 | 11 | NOT robust |

**Reading this:** 'robust in this split' needs avg R > 0 at base, with double costs, at 2.5R and 3.0R, and less than a 10% bootstrap chance that the true edge is ≤ 0, with ≥ 30 trades. A strategy must be robust in BOTH development and validation. Max DD p95 = 1 in 20 trade orders would be worse. Past results do not guarantee future results.
