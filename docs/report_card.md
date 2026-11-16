# Strategy report card (2026-11-16)

Quant-finance numbers for every saved backtest trade, after costs. Made by `scripts/report_card.py`
from `data/backtest_trades*.csv`; ideas from the book *Quantitative Finance From Scratch* (chapter numbers below).
Growth and Monte Carlo use **0.5% risk per trade**. Gold trades were never saved to a file, so gold is not here
(its results are in `gold_report.md`). These numbers MEASURE an edge; they cannot create one.

## How to read it

- **Avg R** (ch 3, expected value): what one trade makes on average. Below 0 = loses money over time.
- **95% range** (ch 15, standard error): where the true average probably lies. If the whole range is below 0, the loss is real, not bad luck.
- **Luck chance** (ch 4): how often reshuffled trades average 0R or worse. Near 100% = no edge.
- **Sharpe/yr** (ch 8): return per unit of swing per year. Good funds are around +0.5 to +1. Negative = paid nothing for the risk.
- **Growth/yr** (ch 9, volatility drag): what the account really keeps per year at 0.5% risk.
- **Kelly %** (ch 14): best % of the account to risk per trade. **0 means: do not trade it.**
- **Worst 5%** (ch 16-17, expected shortfall): average R of the worst 5% of trades.
- **MC** (ch 15, Monte Carlo): 10,000 reshuffled years of trades. Loss chance = share of years that end below the start; DD = largest fall from a peak.

## NAS100 — development 2019-2022

| strategy | trades | avg R | 95% range | luck chance | Sharpe/yr | growth/yr | Kelly % | worst 5% | MC loss chance | MC median | MC bad DD (95th) | verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| london_sweep_mss_fvg | 124 | -0.328 | -0.57 to -0.08 | 100% | -1.32 | -5.0% | 0.00 | -1.77 | 91% | -5.0% | 11.3% | LOSES ON AVERAGE (do not trade) |
| london_trend_fvg | 306 | -0.354 | -0.51 to -0.20 | 100% | -2.24 | -12.8% | 0.00 | -1.63 | 99% | -12.9% | 21.6% | LOSES ON AVERAGE (do not trade) |
| orb | 259 | -0.007 | -0.18 to +0.17 | 54% | -0.04 | -0.4% | 0.00 | -1.44 | 53% | -0.5% | 11.6% | NO PROVEN EDGE (could be luck either way) |
| silver_bullet | 212 | -0.070 | -0.26 to +0.12 | 77% | -0.36 | -2.0% | 0.00 | -1.28 | 65% | -2.0% | 11.4% | NO PROVEN EDGE (could be luck either way) |
| sweep_mss_fvg | 270 | -0.169 | -0.33 to -0.01 | 98% | -1.02 | -5.7% | 0.00 | -1.33 | 86% | -5.8% | 15.2% | LOSES ON AVERAGE (do not trade) |
| trend_fvg | 244 | -0.064 | -0.24 to +0.11 | 76% | -0.36 | -2.1% | 0.00 | -1.25 | 66% | -2.3% | 12.3% | NO PROVEN EDGE (could be luck either way) |
| vwap_reversion | 1823 | -0.310 | -0.37 to -0.25 | 100% | -4.73 | -51.2% | 0.00 | -1.83 | 100% | -51.4% | 62.5% | LOSES ON AVERAGE (do not trade) |

## NAS100 — validation 2023-2024

| strategy | trades | avg R | 95% range | luck chance | Sharpe/yr | growth/yr | Kelly % | worst 5% | MC loss chance | MC median | MC bad DD (95th) | verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| london_sweep_mss_fvg | 74 | -0.369 | -0.68 to -0.06 | 99% | -1.66 | -6.7% | 0.00 | -1.35 | 95% | -6.8% | 13.2% | LOSES ON AVERAGE (do not trade) |
| london_trend_fvg | 174 | -0.237 | -0.48 to +0.01 | 97% | -1.33 | -10.1% | 0.00 | -2.43 | 92% | -10.2% | 22.6% | NO PROVEN EDGE (could be luck either way) |
| orb | 160 | -0.066 | -0.29 to +0.16 | 72% | -0.41 | -2.8% | 0.00 | -1.56 | 67% | -2.8% | 14.4% | NO PROVEN EDGE (could be luck either way) |
| silver_bullet | 80 | -0.108 | -0.42 to +0.20 | 76% | -0.48 | -2.2% | 0.00 | -1.38 | 71% | -2.3% | 10.3% | NO PROVEN EDGE (could be luck either way) |
| sweep_mss_fvg | 127 | +0.150 | -0.10 to +0.40 | 13% | +0.82 | +4.7% | 7.35 | -1.54 | 22% | +4.8% | 8.7% | NO PROVEN EDGE (could be luck either way) |
| trend_fvg | 100 | -0.185 | -0.46 to +0.09 | 91% | -0.94 | -4.6% | 0.00 | -1.26 | 83% | -4.7% | 12.9% | NO PROVEN EDGE (could be luck either way) |
| vwap_reversion | 821 | -0.211 | -0.31 to -0.11 | 100% | -2.95 | -35.9% | 0.00 | -1.81 | 100% | -36.0% | 50.7% | LOSES ON AVERAGE (do not trade) |

## BTC weekends — development 2019-2022

| strategy | trades | avg R | 95% range | luck chance | Sharpe/yr | growth/yr | Kelly % | worst 5% | MC loss chance | MC median | MC bad DD (95th) | verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| btc_weekend_orb | 335 | -0.468 | -0.63 to -0.31 | 100% | -2.86 | -18.0% | 0.00 | -2.53 | 100% | -18.1% | 27.4% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_silver_bullet | 39 | -0.669 | -1.14 to -0.20 | 100% | -1.39 | -3.2% | 0.00 | -2.58 | 92% | -3.4% | 7.0% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_sweep_mss_fvg | 114 | -0.585 | -0.86 to -0.31 | 100% | -2.09 | -8.1% | 0.00 | -2.72 | 98% | -8.0% | 14.0% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_trend_fvg | 765 | -0.496 | -0.60 to -0.39 | 100% | -4.74 | -38.1% | 0.00 | -2.16 | 100% | -38.1% | 47.9% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_vwap_reversion | 1485 | -0.801 | -0.88 to -0.72 | 100% | -9.62 | -77.7% | 0.00 | -3.63 | 100% | -77.7% | 82.9% | LOSES ON AVERAGE (do not trade) |

## BTC weekends — validation 2023-2024

| strategy | trades | avg R | 95% range | luck chance | Sharpe/yr | growth/yr | Kelly % | worst 5% | MC loss chance | MC median | MC bad DD (95th) | verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| btc_weekend_orb | 188 | -1.314 | -1.57 to -1.05 | 100% | -7.03 | -46.4% | 0.00 | -5.34 | 100% | -46.3% | 53.9% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_silver_bullet | 34 | -2.088 | -2.95 to -1.23 | 100% | -3.35 | -16.5% | 0.00 | -8.99 | 100% | -16.1% | 24.2% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_sweep_mss_fvg | 57 | -0.623 | -1.21 to -0.03 | 99% | -1.46 | -8.7% | 0.00 | -6.16 | 95% | -8.0% | 18.6% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_trend_fvg | 428 | -1.260 | -1.41 to -1.11 | 100% | -11.71 | -74.3% | 0.00 | -4.16 | 100% | -74.3% | 78.8% | LOSES ON AVERAGE (do not trade) |
| btc_weekend_vwap_reversion | 641 | -1.590 | -1.76 to -1.42 | 100% | -12.70 | -92.4% | 0.00 | -7.30 | 100% | -92.4% | 94.6% | LOSES ON AVERAGE (do not trade) |

## What it means

- A strategy is only worth watching if its **95% range is above 0 in BOTH periods** and Kelly is above 0 in both.
- Kelly 0% everywhere is the maths saying what the backtests already said: these rules have no edge after costs.
- A bigger risk % never fixes a negative average; it only makes the losses and drawdowns larger (try `--risk 1.0`).
- This report is a measuring tool. A new signal still needs its own pre-registered test before it may enter `scanner.QUALIFIED`.
