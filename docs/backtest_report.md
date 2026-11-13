# Backtest report — generated 2026-11-13 05:06 UTC

- Data: Dukascopy USATECHIDXUSD 1-minute BID bars, 2026-10-19 → 2026-11-12 (25,303 bars)
- Costs: spread 1.5 pts + slippage 0.5 pts on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat 15:55 NY
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| trend_fvg | all | 1 | 0.0 | -1.03 | 0.00 | -1.0 | -0.5 | 0.5 | 1.2 | 1437 | too few trades to conclude |
| sweep_mss_fvg | all | 5 | 0.0 | -1.04 | 0.00 | -5.2 | -2.6 | 2.6 | 6.1 | 1025 | too few trades to conclude |
| orb | all | 4 | 0.0 | -1.04 | 0.00 | -4.2 | -2.1 | 2.1 | 4.9 | 1269 | too few trades to conclude |
| vwap_reversion | all | 33 | 30.3 | -0.12 | 0.83 | -4.0 | -2.1 | 4.3 | 40.2 | 783 |  |
| silver_bullet | all | 2 | 0.0 | -1.04 | 0.00 | -2.1 | -1.0 | 1.0 | 2.4 | 1193 | too few trades to conclude |

\* median account size at which USTEC's 0.1 minimum lot fits the stop at 0.5% risk. At $10 every trade is rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
