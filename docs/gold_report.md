# Gold (XAUUSD) strategy test — generated 2026-11-14 13:26 UTC

- Rules fixed before testing: docs/gold_and_scanner_preregistration.md (commit 6315eb8)
- Data: HistData XAUUSD 1-minute bars, 2,078,857 bars 2019-2024 (2025+ locked)
- Costs [assumption]: $0.3 spread + $0.1 slippage per ounce; also doubled
- Pass (BOTH splits): avg R > 0, avg R > 0 with double costs, P(no edge) ≤ 10%, ≥ 50 trades

| strategy | split | trades | win% | avg R | avg R costs x2 | avg R 90% range | P(no edge) | result |
|---|---|---:|---:|---:|---:|---|---:|---|
| trend_fvg | development | 200 | 34% | -0.21 | -0.39 | -0.37 to -0.04 | 98% | FAIL |
| trend_fvg | validation | 96 | 44% | +0.05 | -0.09 | -0.18 to +0.29 | 35% | FAIL |
| sweep_mss_fvg | development | 138 | 30% | -0.35 | -0.52 | -0.52 to -0.18 | 100% | FAIL |
| sweep_mss_fvg | validation | 61 | 41% | +0.07 | -0.07 | -0.23 to +0.38 | 36% | FAIL |
| orb | development | 862 | 39% | -0.11 | -0.31 | -0.19 to -0.03 | 99% | FAIL |
| orb | validation | 352 | 35% | -0.14 | -0.30 | -0.27 to -0.02 | 97% | FAIL |
| vwap_reversion | development | 1474 | 34% | -0.47 | -0.91 | -0.53 to -0.41 | 100% | FAIL |
| vwap_reversion | validation | 709 | 34% | -0.36 | -0.71 | -0.44 to -0.27 | 100% | FAIL |
| silver_bullet | development | 126 | 29% | -0.40 | -0.58 | -0.58 to -0.22 | 100% | FAIL |
| silver_bullet | validation | 53 | 30% | -0.26 | -0.39 | -0.55 to +0.06 | 91% | FAIL |
| london_trend_fvg | development | 317 | 38% | -0.15 | -0.44 | -0.28 to -0.01 | 96% | FAIL |
| london_trend_fvg | validation | 150 | 29% | -0.44 | -0.68 | -0.64 to -0.23 | 100% | FAIL |
| london_sweep_mss_fvg | development | 132 | 26% | -0.51 | -0.79 | -0.71 to -0.31 | 100% | FAIL |
| london_sweep_mss_fvg | validation | 74 | 39% | -0.09 | -0.36 | -0.38 to +0.20 | 71% | FAIL |

## Verdict: **no gold strategy qualifies**

Past results do not guarantee future results. Research only.
