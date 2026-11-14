# Backtest report — generated 2026-11-14 12:33 UTC

- Market: NAS100 (weekdays). Data: HistData.com NSXUSD 1-minute BID bars, 2019-01-01 → 2024-12-31 (2,006,809 bars)
- Costs: spread 1.5 pts + fee 0.0% of price per round trip; slippage 0.5 pts + 0.0% of price on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat at the end of the book's window (NAS100 15:55 NY, BTC Sunday 17:00 NY)
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trend_fvg | development | 244 | 35.2 | -0.06 | 0.91 | -15.7 | -8.1 | 11.5 | 5.1 | 484 |  |
| trend_fvg | validation | 100 | 30.0 | -0.18 | 0.76 | -18.5 | -9.0 | 15.2 | 4.2 | 658 |  |
| sweep_mss_fvg | development | 270 | 32.6 | -0.17 | 0.77 | -45.5 | -20.8 | 23.6 | 5.6 | 566 |  |
| sweep_mss_fvg | validation | 127 | 43.3 | 0.15 | 1.24 | 19.0 | 9.6 | 4.6 | 5.3 | 712 |  |
| orb | development | 259 | 38.6 | -0.01 | 0.99 | -1.9 | -1.6 | 16.1 | 5.4 | 689 |  |
| orb | validation | 160 | 35.0 | -0.07 | 0.91 | -10.5 | -5.5 | 15.8 | 6.7 | 779 |  |
| vwap_reversion | development | 1823 | 31.2 | -0.31 | 0.64 | -564.7 | -94.3 | 94.3 | 38.0 | 287 |  |
| vwap_reversion | validation | 821 | 32.4 | -0.21 | 0.74 | -173.3 | -58.9 | 60.5 | 34.2 | 348 |  |
| silver_bullet | development | 212 | 35.8 | -0.07 | 0.90 | -14.8 | -7.6 | 12.7 | 4.4 | 541 |  |
| silver_bullet | validation | 80 | 32.5 | -0.11 | 0.85 | -8.6 | -4.4 | 10.4 | 3.3 | 716 |  |
| london_trend_fvg | development | 306 | 28.1 | -0.35 | 0.59 | -108.3 | -42.3 | 43.1 | 6.4 | 256 |  |
| london_trend_fvg | validation | 174 | 32.2 | -0.24 | 0.72 | -41.3 | -19.2 | 21.3 | 7.2 | 261 |  |
| london_sweep_mss_fvg | development | 124 | 29.0 | -0.33 | 0.62 | -40.7 | -18.7 | 19.6 | 2.6 | 261 |  |
| london_sweep_mss_fvg | validation | 74 | 27.0 | -0.37 | 0.57 | -27.3 | -12.9 | 16.4 | 3.1 | 267 |  |

\* median account size at which USTEC's minimum lot fits the stop at 0.5% risk. The paper balance is $1,000; at $10 every trade would be rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
