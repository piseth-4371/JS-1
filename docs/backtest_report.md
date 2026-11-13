# Backtest report — generated 2026-11-13 05:56 UTC

- Data: Dukascopy USATECHIDXUSD 1-minute BID bars, 2019-01-01 → 2019-11-29 (314,421 bars)
- Costs: spread 1.5 pts + slippage 0.5 pts on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat 15:55 NY
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trend_fvg | all | 60 | 38.3 | -0.05 | 0.93 | -2.9 | -1.6 | 5.0 | 5.5 | 224 |  |
| sweep_mss_fvg | all | 57 | 42.1 | 0.02 | 1.03 | 1.0 | 0.4 | 7.3 | 5.2 | 266 |  |
| orb | all | 67 | 44.8 | 0.14 | 1.21 | 9.3 | 4.6 | 5.2 | 6.1 | 328 |  |
| vwap_reversion | all | 437 | 31.8 | -0.44 | 0.54 | -191.3 | -62.0 | 62.5 | 39.9 | 140 |  |
| silver_bullet | all | 52 | 34.6 | -0.20 | 0.74 | -10.4 | -5.2 | 6.5 | 4.8 | 228 |  |
| london_trend_fvg | all | 78 | 34.6 | -0.32 | 0.65 | -24.9 | -11.9 | 13.2 | 7.1 | 114 |  |
| london_sweep_mss_fvg | all | 27 | 37.0 | -0.28 | 0.68 | -7.5 | -3.8 | 6.7 | 2.5 | 112 | too few trades to conclude |

\* median account size at which USTEC's 0.1 minimum lot fits the stop at 0.5% risk. The paper balance is $1,000; at $10 every trade would be rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
