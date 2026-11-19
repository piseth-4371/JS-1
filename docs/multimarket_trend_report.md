# Slow multi-market trend vs simple benchmarks — results

Made by `scripts/multimarket_trend_test.py` on 2026-11-19. Rules committed before any price was read (`docs/multimarket_trend_preregistration.md`, commit 3d5fd49). Research only: nothing is traded and no strategy, risk limit or scanner setting changed. 2025+ was never downloaded.

## Verdict: **negative observed result**

## Words used here

- **Sharpe ratio:** average monthly return divided by how much it moves, scaled to a year. Above 0 means it gained on average; the higher, the steadier. Around 0.5 is what published trend studies report over a century.
- **95% range:** the Sharpe values we would plausibly see if the same kind of history were dealt again (12-month blocks re-drawn 5,000 times). If the range includes 0, a real edge cannot be told apart from luck.
- **Random direction:** the same markets, sizes and costs, but long or short by coin flip. A real trend rule should beat at least 95% of those 5,000 coin-flip portfolios.
- **Net** = after the assumed trading costs and financing. **Stress** = with both doubled.

## Pass rule check (all must be yes in both periods)

| period | net Sharpe > 0 | 95% range low > 0 | above random 95th pct | stress > 0 | months, avg markets |
|---|---|---|---|---|---|
| development 1988-2010 | +0.32 yes | -0.07 **no** | +0.32 vs -0.27 yes | -0.10 **no** | 276, 8.5 yes |
| validation 2011-2024 | -0.30 **no** | -0.72 **no** | -0.30 vs -0.28 **no** | -0.73 **no** | 168, 10.0 yes |

## Returns

| period | portfolio | yearly return | volatility | Sharpe | max drawdown |
|---|---|---:|---:|---:|---:|
| development 1988-2010 | trend, gross | +3.6% | 4.9% | +0.73 | -12.8% |
| development 1988-2010 | **trend, net** | +1.6% | 4.9% | +0.32 | -14.3% |
| development 1988-2010 | trend, stress | -0.5% | 4.9% | -0.10 | -20.4% |
| development 1988-2010 | always long, gross | +2.5% | 5.6% | +0.44 | -19.1% |
| development 1988-2010 | always long, net | +0.5% | 5.6% | +0.09 | -27.0% |
| development 1988-2010 | always long, stress | -1.5% | 5.6% | -0.26 | -44.1% |
| validation 2011-2024 | trend, gross | +0.7% | 4.9% | +0.13 | -14.4% |
| validation 2011-2024 | **trend, net** | -1.5% | 4.9% | -0.30 | -25.4% |
| validation 2011-2024 | trend, stress | -3.6% | 4.9% | -0.73 | -42.9% |
| validation 2011-2024 | always long, gross | -0.5% | 6.4% | -0.08 | -22.9% |
| validation 2011-2024 | always long, net | -2.5% | 6.4% | -0.39 | -36.1% |
| validation 2011-2024 | always long, stress | -4.5% | 6.4% | -0.69 | -50.2% |

## Uncertainty and comparisons (net)

| period | months | avg markets | Sharpe 95% range | random 95th pct | random runs beaten | correlation with always long | worst 10% always-long months: trend vs always long |
|---|---:|---:|---|---:|---:|---:|---|
| development 1988-2010 | 276 | 8.5 | -0.07 to +0.71 | -0.27 | 100% | +0.15 | -0.2% vs -2.9% |
| validation 2011-2024 | 168 | 10.0 | -0.72 to +0.21 | -0.28 | 94% | -0.08 | +0.1% vs -3.8% |

## By asset class (trend, net; reported only, not part of the pass rule)

| period | class | markets | months | Sharpe | yearly return |
|---|---|---:|---:|---:|---:|
| development 1988-2010 | equity | 2 | 276 | +0.46 | +4.0% |
| development 1988-2010 | energy | 2 | 256 | +0.06 | +0.5% |
| development 1988-2010 | currency | 6 | 276 | +0.12 | +0.8% |
| validation 2011-2024 | equity | 2 | 168 | +0.34 | +2.6% |
| validation 2011-2024 | energy | 2 | 168 | +0.12 | +0.8% |
| validation 2011-2024 | currency | 6 | 168 | -0.54 | -3.6% |

## Data checks

| market | FRED id | first | last | daily values | valid months | months with < 10 values | longest gap (days) | values <= 0 excluded (Amendment 1) |
|---|---|---|---|---:|---:|---:|---:|---|
| Nasdaq Composite | `NASDAQCOM` | 1971-02-05 | 2024-12-31 | 13,594 | 647 | 0 | 7 | 0 |
| Nikkei 225 | `NIKKEI225` | 1960-01-04 | 2024-12-30 | 16,120 | 648 | 0 | 11 | 0 |
| WTI crude oil | `DCOILWTICO` | 1986-01-02 | 2024-12-31 | 9,077 | 459 | 9 | 14 | 2020-04-20 |
| Henry Hub natural gas | `DHHNGSP` | 1997-01-07 | 2024-12-31 | 5,264 | 235 | 101 | 41 | 0 |
| Japanese yen | `DEXJPUS` (inverted) | 1971-01-04 | 2024-12-31 | 13,535 | 648 | 0 | 18 | 0 |
| British pound | `DEXUSUK` | 1971-01-04 | 2024-12-31 | 13,541 | 648 | 0 | 10 | 0 |
| Canadian dollar | `DEXCAUS` (inverted) | 1971-01-04 | 2024-12-31 | 13,547 | 648 | 0 | 5 | 0 |
| Swiss franc | `DEXSZUS` (inverted) | 1971-01-04 | 2024-12-31 | 13,541 | 648 | 0 | 10 | 0 |
| Australian dollar | `DEXUSAL` | 1971-01-04 | 2024-12-31 | 13,534 | 648 | 0 | 10 | 0 |
| Euro | `DEXUSEU` | 1999-01-04 | 2024-12-31 | 6,520 | 312 | 0 | 5 | 0 |

## Limits

- Spot prices and index levels, not tradable CFDs or futures: no dividends, futures roll or currency interest differences. Profit levels are therefore not what a trading account would have earned.
- Costs and financing are fixed assumptions, not broker quotes.
- When a market sits out a month because of missing data, the cost of closing its position is not charged (an implementation detail the rules did not specify; it affects only months with fewer than 10 values).
- Trend following was widely reported to be weak in parts of 2011-2024 before this test was written.
- Six of the ten markets are currencies, so currencies carry most of the portfolio's risk.
- Past results do not predict the future, and no strategy here is approved for trading.
