# Backtest report — generated 2026-11-13 07:36 UTC

- Market: BTC (weekends). Data: Binance BTCUSDT 1-minute bars (trade prices), 2019-01-01 → 2024-12-31 (3,152,369 bars)
- Costs: spread 0.0 pts + fee 0.1% of price per round trip; slippage 0.0 pts + 0.02% of price on market/stop fills and stop exits
- Risk: 0.5% per trade, min RR 2.0, max 3 trades/day, 1 position, daily −2.0%, weekly −5.0%, stop after 2 losses
- Fills: stop assumed first if a minute touches stop and target; no profit on the fill minute; flat at the end of the book's window (NAS100 15:55 NY, BTC Sunday 17:00 NY)
- Out-of-sample (2025+) included: no (locked)

| strategy | split | trades | win % | avg R | PF | total R | return % | max DD % | trades/month | $ needed* | note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| btc_weekend_trend_fvg | development | 765 | 32.4 | -0.50 | 0.50 | -379.1 | -85.3 | 85.4 | 15.9 | 0 |  |
| btc_weekend_trend_fvg | validation | 428 | 25.2 | -1.26 | 0.19 | -539.2 | -93.4 | 93.4 | 17.8 | 0 |  |

\* median account size at which BTCUSDT's minimum lot fits the stop at 0.5% risk. The paper balance is $1,000; at $10 every trade would be rejected.

**Reading this table:** avg R = average result per trade in units of risk (the edge). Above 0 after costs on BOTH development and validation is the minimum bar. Past results do not guarantee future results.
