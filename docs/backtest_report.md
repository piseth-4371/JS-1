# Backtest report — generated 2026-11-13 06:41 UTC

- Market: NAS100 (weekdays). Data: Dukascopy USATECHIDXUSD 1-minute BID bars, 2019-01-01 → 2019-12-23 (335,818 bars)
- Costs: spread 1.5 pts + fee 0.0% of price per round trip; slippage 0.5 pts + 0.0% of price on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat at the end of the book's window (NAS100 15:55 NY, BTC Sunday 17:00 NY)
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trend_fvg | all | 63 | 38.1 | -0.07 | 0.90 | -4.5 | -2.4 | 5.0 | 5.4 | 221 |  |
| sweep_mss_fvg | all | 59 | 44.1 | 0.07 | 1.11 | 4.3 | 2.0 | 7.3 | 5.0 | 266 |  |
| orb | all | 72 | 43.1 | 0.09 | 1.13 | 6.4 | 3.0 | 5.2 | 6.1 | 327 |  |
| vwap_reversion | all | 459 | 32.0 | -0.45 | 0.53 | -205.7 | -64.7 | 65.2 | 39.1 | 133 |  |
| silver_bullet | all | 55 | 38.2 | -0.12 | 0.84 | -6.4 | -3.3 | 6.5 | 4.7 | 227 |  |
| london_trend_fvg | all | 82 | 32.9 | -0.37 | 0.60 | -30.7 | -14.5 | 15.8 | 7.0 | 111 |  |
| london_sweep_mss_fvg | all | 27 | 37.0 | -0.28 | 0.68 | -7.5 | -3.8 | 6.7 | 2.3 | 112 | too few trades to conclude |

\* median account size at which USTEC's minimum lot fits the stop at 0.5% risk. The paper balance is $1,000; at $10 every trade would be rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
