# Volatility regime filter — results (2026-11-16 04:28 UTC)

Rules fixed and committed BEFORE this run: `volatility_filter_preregistration.md` (commit 67434a7).
Run note: the first attempt crashed while printing (Windows console encoding) before any strategy result was shown; it was re-run unchanged.
Data: HistData NSXUSD 2019-2024 (2025+ locked). Costs 1.5 spread + 0.5 slippage.
Day regimes 2019-2024: normal 790, calm 533, wild 380, not enough history 163 (start of 2019).

## Verdict: FAIL — no strategy passes in both periods

Checks (all needed, both periods): 1 filtered avg R > 0 · 2 enough trades (100 dev / 50 val) · 3 luck chance ≤ 10% · 4 better than unfiltered · 5 beats ≥ 90% of random-skip controls.

| strategy | split | trades base | avg R base | trades filtered | avg R filtered | luck chance | beats random skip | checks 1-5 | result |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| trend_fvg | development | 244 | -0.064 | 109 | +0.028 | 42% | 83% | ✓✓✗✓✗ | fail |
| trend_fvg | validation | 100 | -0.185 | 38 | -0.358 | 95% | 19% | ✗✗✗✗✗ | fail |
| sweep_mss_fvg | development | 270 | -0.169 | 123 | -0.141 | 87% | 62% | ✗✓✗✓✗ | fail |
| sweep_mss_fvg | validation | 127 | +0.150 | 44 | -0.097 | 68% | 8% | ✗✗✗✗✗ | fail |
| orb | development | 259 | -0.007 | 121 | -0.136 | 87% | 7% | ✗✓✗✗✗ | fail |
| orb | validation | 160 | -0.066 | 68 | -0.050 | 62% | 57% | ✗✓✗✓✗ | fail |
| vwap_reversion | development | 1823 | -0.310 | 841 | -0.298 | 100% | 64% | ✗✓✗✓✗ | fail |
| vwap_reversion | validation | 821 | -0.211 | 328 | -0.163 | 98% | 76% | ✗✓✗✓✗ | fail |
| silver_bullet | development | 212 | -0.070 | 96 | -0.070 | 69% | 49% | ✗✗✗✗✗ | fail |
| silver_bullet | validation | 80 | -0.108 | 37 | -0.199 | 81% | 27% | ✗✗✗✗✗ | fail |
| london_trend_fvg | development | 306 | -0.354 | 125 | -0.323 | 100% | 61% | ✗✓✗✓✗ | fail |
| london_trend_fvg | validation | 174 | -0.237 | 63 | -0.327 | 96% | 27% | ✗✓✗✗✗ | fail |
| london_sweep_mss_fvg | development | 124 | -0.328 | 56 | -0.349 | 97% | 42% | ✗✗✗✗✗ | fail |
| london_sweep_mss_fvg | validation | 74 | -0.369 | 27 | -0.487 | 97% | 29% | ✗✗✗✗✗ | fail |

## Information only (not part of the verdict): trades on skipped days, unfiltered

| strategy | split | calm trades | calm avg R | wild trades | wild avg R |
|---|---|---:|---:|---:|---:|
| trend_fvg | development | 38 | +0.006 | 62 | -0.301 |
| trend_fvg | validation | 45 | -0.148 | 17 | +0.106 |
| sweep_mss_fvg | development | 43 | -0.235 | 67 | -0.206 |
| sweep_mss_fvg | validation | 57 | +0.416 | 26 | -0.014 |
| orb | development | 33 | -0.001 | 65 | +0.124 |
| orb | validation | 68 | -0.279 | 24 | +0.495 |
| vwap_reversion | development | 302 | -0.314 | 451 | -0.251 |
| vwap_reversion | validation | 369 | -0.302 | 124 | -0.068 |
| silver_bullet | development | 36 | +0.103 | 52 | -0.216 |
| silver_bullet | validation | 36 | +0.076 | 7 | -0.572 |
| london_trend_fvg | development | 54 | -0.651 | 78 | -0.212 |
| london_trend_fvg | validation | 93 | -0.167 | 18 | -0.286 |
| london_sweep_mss_fvg | development | 25 | -0.169 | 26 | -0.294 |
| london_sweep_mss_fvg | validation | 34 | -0.382 | 13 | -0.088 |

No rule may be changed after this run (20/80 percentile, 20-day volatility, 250-day ranking). Past results do not guarantee future results.

## What it means
- **The filter does not fix anything.** In validation it made 5 of 7 strategies WORSE (check 4), and none beat random skipping 90% of the time (check 5).
- trend_fvg looked positive in development (+0.028R) but became -0.358R in validation: the same "one good period" trap as before.
- The skipped calm/wild days were not consistently the bad ones (table above): sometimes calm trades were the best, sometimes wild ones. Volatility regime does not explain the losses.
- Same lesson as the cost filter: removing trades cannot create an edge the entry rule does not have.
