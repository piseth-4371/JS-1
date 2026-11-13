# Auto-switch (strategy selector) test — generated 2026-11-13 06:15 UTC

- Market: NAS100 (weekdays); data dukascopy USATECHIDXUSD 2019-01-01 → 2019-12-23; out-of-sample (2025+) locked
- Each Monday the selector looks only at trades that closed BEFORE that Monday and picks one strategy for the week (min 10 past trades). `avg_r` stays out if the best average R is ≤ 0; `win_rate` always picks the highest win rate.
- 6 versions were fixed before running (1, 3, 6 month lookback × 2 criteria). All are shown.

| version | split | trades | win % | avg R | PF | total R | max DD % | note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| trend_fvg | all | 62 | 38.7 | -0.05 | 0.93 | -3.1 | 5.0 |  |
| sweep_mss_fvg | all | 59 | 44.1 | 0.07 | 1.11 | 4.3 | 7.3 |  |
| orb | all | 72 | 43.1 | 0.09 | 1.13 | 6.4 | 5.2 |  |
| vwap_reversion | all | 465 | 31.8 | -0.45 | 0.53 | -209.0 | 65.6 |  |
| silver_bullet | all | 55 | 38.2 | -0.12 | 0.84 | -6.4 | 6.5 |  |
| london_trend_fvg | all | 82 | 32.9 | -0.37 | 0.60 | -30.7 | 15.8 |  |
| london_sweep_mss_fvg | all | 27 | 37.0 | -0.28 | 0.68 | -7.5 | 6.7 | too few trades to conclude |
| auto-switch avg_r 1m | all | 7 | 28.6 | -0.48 | 0.50 | -3.3 | 2.4 | too few trades to conclude idle 98% of weeks; picked: vwap_reversion 1 |
| auto-switch avg_r 3m | all | 50 | 38.0 | -0.08 | 0.90 | -3.8 | 4.0 | idle 12% of weeks; picked: sweep_mss_fvg 20, orb 18 |
| auto-switch avg_r 6m | all | 53 | 37.7 | -0.07 | 0.91 | -3.6 | 4.9 | idle 20% of weeks; picked: orb 25, sweep_mss_fvg 13 |
| auto-switch win_rate 1m | all | 425 | 32.2 | -0.44 | 0.54 | -186.6 | 62.0 | idle 2% of weeks; picked: vwap_reversion 46, london_trend_fvg 3 |
| auto-switch win_rate 3m | all | 87 | 36.8 | -0.19 | 0.76 | -16.3 | 12.4 | idle 2% of weeks; picked: sweep_mss_fvg 22, orb 16, vwap_reversion 4 |
| auto-switch win_rate 6m | all | 96 | 37.5 | -0.14 | 0.82 | -13.7 | 11.2 | idle 2% of weeks; picked: orb 24, sweep_mss_fvg 16, vwap_reversion 4 |

**Pass rule:** the auto-switch is only worth using if a version beats the best FIXED strategy on average R in BOTH development and validation, with ≥ 100 trades each. Past results do not guarantee future results.
