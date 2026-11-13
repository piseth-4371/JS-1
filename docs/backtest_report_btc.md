# Backtest report — generated 2026-11-13 07:51 UTC

- Market: BTC (weekends). Data: Binance BTCUSDT 1-minute bars (trade prices), 2019-01-01 → 2024-12-31 (3,152,369 bars)
- Costs: spread 0.0 pts + fee 0.1% of price per round trip; slippage 0.0 pts + 0.02% of price on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat at the end of the book's window (NAS100 15:55 NY, BTC Sunday 17:00 NY)
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| btc_weekend_trend_fvg | development | 765 | 32.4 | -0.50 | 0.50 | -379.1 | -85.3 | 85.4 | 15.9 | 0 |  |
| btc_weekend_trend_fvg | validation | 428 | 25.2 | -1.26 | 0.19 | -539.2 | -93.4 | 93.4 | 17.8 | 0 |  |
| btc_weekend_sweep_mss_fvg | development | 114 | 30.7 | -0.58 | 0.45 | -66.7 | -28.6 | 28.6 | 2.4 | 0 |  |
| btc_weekend_sweep_mss_fvg | validation | 57 | 42.1 | -0.62 | 0.48 | -35.5 | -16.6 | 20.0 | 2.4 | 0 |  |
| btc_weekend_orb | development | 335 | 35.8 | -0.47 | 0.53 | -156.6 | -54.8 | 54.8 | 7.0 | 0 |  |
| btc_weekend_orb | validation | 188 | 27.1 | -1.31 | 0.19 | -247.0 | -71.3 | 71.4 | 7.8 | 0 |  |
| btc_weekend_vwap_reversion | development | 1485 | 33.1 | -0.80 | 0.35 | -1190.1 | -99.8 | 99.8 | 30.9 | 0 |  |
| btc_weekend_vwap_reversion | validation | 641 | 28.9 | -1.59 | 0.16 | -1019.2 | -99.4 | 99.4 | 26.7 | 0 |  |
| btc_weekend_silver_bullet | development | 39 | 30.8 | -0.67 | 0.41 | -26.1 | -12.3 | 14.6 | 0.8 | 0 |  |
| btc_weekend_silver_bullet | validation | 34 | 17.6 | -2.09 | 0.08 | -71.0 | -30.2 | 30.2 | 1.4 | 0 |  |

\* median account size at which BTCUSDT's minimum lot fits the stop at 0.5% risk. The paper balance is $1,000; at $10 every trade would be rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
