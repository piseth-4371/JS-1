# Slow multi-market trend vs simple benchmarks (pre-registered 2026-11-19)

Written and committed BEFORE any price in the FRED files was read. Only file headers, line counts and first/last
dates were looked at, to confirm the downloads. Research only: no order path, no change to strategies, risk limits,
paper account or `scanner.QUALIFIED` (the scanner is for intraday signals and stays empty).

## Question
Does a slow trend rule, spread across unrelated markets, earn a positive return after costs, and is it better than
simply holding the same markets or picking random directions?

## Why this is a different kind of idea
Holds for months, uses 10 markets in three asset classes, and needs no chart pattern. Published evidence covers
1880-2016 across 67 markets (Hurst, Ooi and Pedersen, "A Century of Evidence on Trend-Following Investing"). It is
related to E05 (daily trend on NAS100 alone, failed); the differences are many markets, long and short positions,
and equal risk per market. Things already known before this test, stated so they are not hidden: trend funds were
widely reported to have done poorly in parts of 2011-2024, which is the validation period.

## Data (FRED, downloaded 2026-11-19, requested up to 2024-12-31; 2025+ never downloaded)
Files in `backend/data/external/fred/`, unmodified. Daily closing values; "." or empty = no value (holiday), never filled.

| market | FRED id | class | used as |
|---|---|---|---|
| Nasdaq Composite | NASDAQCOM | equity | index level |
| Nikkei 225 | NIKKEI225 | equity | index level |
| WTI crude oil | DCOILWTICO | energy | spot price |
| Henry Hub natural gas | DHHNGSP | energy | spot price |
| Japanese yen | DEXJPUS | currency | 1 / value (USD per yen) |
| British pound | DEXUSUK | currency | value (USD per pound) |
| Canadian dollar | DEXCAUS | currency | 1 / value (USD per CAD) |
| Swiss franc | DEXSZUS | currency | 1 / value (USD per CHF) |
| Australian dollar | DEXUSAL | currency | value (USD per AUD) |
| Euro | DEXUSEU | currency | value (USD per euro) |

Limits fixed now: these are spot prices and index levels, not tradable CFDs or futures. They leave out dividends,
futures roll and currency interest differences. Brent (moves with WTI) and the 10-year yield (a yield, not a price)
are not used.

## Rules
- **Month end** = the last day in a calendar month with a value. A market-month needs at least 10 daily values,
  otherwise that market sits out that month (no filling).
- **Signal** at month end t: sign of the 12-month price change, P(t) / P(t-12 months) - 1. Above 0 = long, below 0 =
  short, exactly 0 = flat.
- **Size:** each market targets 10% annual volatility: weight = 0.10 / sigma, where sigma = standard deviation of the
  last 63 daily log returns x sqrt(252), capped at weight 4. A market needs 13 month ends and 63 daily returns of
  history before it can trade.
- **Return** of month t+1 for a market = weight x signal x (P(t+1) / P(t) - 1). Portfolio return = the average over
  markets that trade that month (equal risk per market).
- **Costs** per month, per market, as a fraction of notional: trading cost = |new weight x signal - old weight x
  signal| x one-way cost (equity 0.05%, currency 0.03%, oil 0.10%, natural gas 0.20%), plus financing 2% per year x
  |weight| / 12. These are assumptions, not broker quotes. **Stress:** both doubled.

## Benchmarks (same markets, same weights, same costs)
- **Always long:** signal = +1 every month.
- **Random direction:** each market-month long or short with equal chance; 5,000 runs, seed 11.

## Periods
- **Development:** returns of January 1988 to December 2010 (WTI starts 1986, so it can trade from 1988).
  Data from 1971 is used only for history before the first month.
- **Validation:** January 2011 to December 2024.
- 2025+ stays locked and was not downloaded.

## Reported per period
Months, average number of markets, annualised return, volatility, Sharpe ratio (mean / standard deviation x
sqrt(12), no risk-free rate), maximum drawdown, gross vs net, stress, and the same for always long. Sharpe 95% range
from a 12-month block bootstrap (5,000 runs, seed 11). The strategy's percentile among the random-direction runs.
Correlation with always long. Average return in the worst 10% of always-long months. Results by asset class.

## Pass rule (all must hold in BOTH development and validation)
1. Net Sharpe > 0, and the lower end of its 95% block-bootstrap range > 0.
2. Net Sharpe above the 95th percentile of the random-direction runs.
3. Stress net Sharpe > 0.
4. At least 120 months, with an average of at least 4 markets trading.

**Verdicts:** *passes the research criteria* (all of the above); *negative observed result* (net Sharpe <= 0 in
either period); otherwise *inconclusive*. Beating always long is reported but is not required, because the reason
for trend is diversification, not higher return in a rising market.

## If it passes
Nothing is traded, and nothing is added to the scanner or paper engine. A pass would only justify a separate,
owner-approved plan using tradable instruments and real costs, and a one-time test on locked 2025+ data.
No setting in this file is changed after the results are seen.

Output: `docs/multimarket_trend_report.md`, made by `backend/scripts/multimarket_trend_test.py`.
