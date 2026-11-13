# Cost filter research (NAS100) — generated 2026-11-13 08:51 UTC

- Data: Dukascopy USATECHIDXUSD 2019-01-01 to 2020-06-19 (2025+ locked)
- Costs 1.5 spread + 0.5 slippage = 2.0 points per trade [assumption; MetaQuotes-Demo measured ~0.9-1.0 point spread on 2026-11-13]
- Filter (fixed in advance): skip the trade if cost > 20% of its risk

| strategy | split | trades base | avg R base | trades filtered | avg R filtered | total R base | total R filtered | P(no edge) filtered |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| trend_fvg | development (partial) | 90 | -0.11 | 65 | -0.19 | -10.1 | -12.4 | 88% |
| trend_fvg | validation | not downloaded yet | | | | | | |
| sweep_mss_fvg | development (partial) | 92 | +0.05 | 76 | +0.15 | +5.0 | +11.5 | 18% |
| sweep_mss_fvg | validation | not downloaded yet | | | | | | |
| orb | development (partial) | 100 | -0.04 | 85 | +0.04 | -4.5 | +3.1 | 42% |
| orb | validation | not downloaded yet | | | | | | |
| vwap_reversion | development (partial) | 701 | -0.45 | 320 | -0.23 | -317.7 | -72.6 | 100% |
| vwap_reversion | validation | not downloaded yet | | | | | | |
| silver_bullet | development (partial) | 81 | -0.17 | 58 | -0.09 | -13.8 | -5.0 | 68% |
| silver_bullet | validation | not downloaded yet | | | | | | |
| london_trend_fvg | development (partial) | 120 | -0.43 | 35 | -0.43 | -51.0 | -15.0 | 97% |
| london_trend_fvg | validation | not downloaded yet | | | | | | |
| london_sweep_mss_fvg | development (partial) | 39 | -0.17 | 13 | -0.41 | -6.7 | -5.4 | 84% |
| london_sweep_mss_fvg | validation | not downloaded yet | | | | | | |

**Reading this:** the filter only counts as an improvement if avg R improves in BOTH development and validation with enough trades (30+). Fewer trades also means more luck in the result. Past results do not guarantee future results.
