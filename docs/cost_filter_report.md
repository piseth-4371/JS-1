# Cost filter research (NAS100) — generated 2026-11-14 12:35 UTC

- Data: histdata NSXUSD 2019-01-01 to 2024-12-31 (2025+ locked)
- Costs 1.5 spread + 0.5 slippage = 2.0 points per trade [assumption; MetaQuotes-Demo measured ~0.9-1.0 point spread on 2026-11-13]
- Filter (fixed in advance): skip the trade if cost > 20% of its risk

| strategy | split | trades base | avg R base | trades filtered | avg R filtered | total R base | total R filtered | P(no edge) filtered |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development | 244 | -0.06 | 218 | -0.09 | -15.7 | -18.9 | 82% |
| trend_fvg | validation | 100 | -0.18 | 98 | -0.16 | -18.5 | -15.9 | 88% |
| sweep_mss_fvg | development | 270 | -0.17 | 252 | -0.14 | -45.5 | -36.5 | 95% |
| sweep_mss_fvg | validation | 127 | +0.15 | 124 | +0.19 | +19.0 | +23.0 | 8% |
| orb | development | 259 | -0.01 | 240 | +0.03 | -1.9 | +6.4 | 39% |
| orb | validation | 160 | -0.07 | 158 | -0.05 | -10.5 | -7.9 | 66% |
| vwap_reversion | development | 1823 | -0.31 | 1298 | -0.22 | -564.7 | -280.8 | 100% |
| vwap_reversion | validation | 821 | -0.21 | 746 | -0.19 | -173.3 | -141.2 | 100% |
| silver_bullet | development | 212 | -0.07 | 187 | -0.03 | -14.8 | -6.2 | 62% |
| silver_bullet | validation | 80 | -0.11 | 78 | -0.08 | -8.6 | -6.0 | 69% |
| london_trend_fvg | development | 306 | -0.35 | 197 | -0.29 | -108.3 | -56.6 | 100% |
| london_trend_fvg | validation | 174 | -0.24 | 150 | -0.28 | -41.3 | -41.4 | 98% |
| london_sweep_mss_fvg | development | 124 | -0.33 | 73 | -0.36 | -40.7 | -25.9 | 99% |
| london_sweep_mss_fvg | validation | 74 | -0.37 | 48 | -0.33 | -27.3 | -15.7 | 95% |

**Reading this:** the filter only counts as an improvement if avg R improves in BOTH development and validation with enough trades (30+). Fewer trades also means more luck in the result. Past results do not guarantee future results.
