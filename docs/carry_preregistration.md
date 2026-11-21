# FX carry — rules written before any result

Written 2026-11-21, before any interest rate or carry return was read or computed. Owner request: "Option B",
"HIGHT RISK HIGHT REWARD", "yes carry, download the data" (the ONE forex idea, `CLAUDE.md` section 2a).

## Question
Does holding, each month, the 2 currencies with the highest short-term interest rate against the 2 with the lowest
(among USD, EUR, GBP, JPY, CHF, CAD, AUD) earn more than picking currencies at random, after an assumed broker swap
markup and spreads, in both 1980-2004 and 2005-2024?

## Why it might work (the reason, not a chart pattern)
In theory a high interest rate should be cancelled by the currency falling (uncovered interest parity). In decades
of data it mostly was not: high-rate currencies paid more than they lost (Fama 1984; Lustig & Verdelhan 2007;
Burnside et al. 2011). The usual explanation is a **crash-risk premium**: carry earns slowly and then loses fast when
markets panic (1998, 2008) and everyone sells high-rate currencies at once. Investors who cannot take that risk pay
those who can. Since 2008 interest rates were near zero in many countries for years, so the premium may be smaller.

## Disclosure
This is evaluation **55** in this project (54 so far, 0 passes, `docs/experiment_journal.md`). The same 6 FRED
exchange-rate files were used in E17 (12-month price trend, failed in 2011-2024); that test ignored interest rates
completely. No interest-rate file has been opened in this project before. At the time of writing the rate files
are not yet downloaded.

## Pre-mortem (required, written before any result)
1. **Crashes:** 2008 (and 2020) losses wipe out years of carry income, so 2005-2024 is negative.
2. **Near-zero rates:** from about 2009 to 2021 the rate gaps were small, so there was little to earn while the
   swap markup kept costing, and 2005-2024 is at or below zero.
3. **It does not beat random picks:** the result is mainly the US dollar's long moves, not the interest gap, and it
   stays below the 95th percentile of random currency choices.

## Data
- **Exchange rates (already in the project, unmodified):** FRED daily `DEXUSEU`, `DEXUSUK`, `DEXUSAL` (USD per
  unit) and `DEXJPUS`, `DEXSZUS`, `DEXCAUS` (units per USD, inverted), in `backend/data/external/fred/`, read with
  `multimarket_trend.read_fred`. The **month-end rate** = the last daily value in the month.
- **Interest rates (to be downloaded, unmodified):** FRED monthly OECD 3-month interbank rates, % a year:
  `IR3TIB01USM156N`, `IR3TIB01EZM156N`, `IR3TIB01GBM156N`, `IR3TIB01JPM156N`, `IR3TIB01CHM156N`,
  `IR3TIB01CAM156N`, `IR3TIB01AUM156N`, to `backend/data/external/fred_rates/`, requested up to 2024-12-31.
- **No look-ahead:** a monthly average rate is only known after its month ends, so the ranking at the end of month
  t uses each currency's rate for month **t−1**. The interest earned during month t+1 uses that same rate.
- A currency takes part in a month only if it has both a rate and month-end exchange rates for that month and the
  next. Gaps are never filled. A month is used only if at least **5** of the 7 currencies take part (the euro
  starts in 1999, so before that there are at most 6).
- **Development: 1980-2004. Validation: 2005-2024.** A month belongs to the period of its holding month.
  2025 and later stay locked.

## The rule (fixed; no other setting will be tried)
- At each month end, rank the taking-part currencies by their rate (t−1). **Long the 2 highest, short the 2
  lowest**, each leg with weight 0.5, so 1 unit long and 1 unit short. Ties are broken alphabetically by currency
  code. Hold for the next month, then re-rank.
- **Gross return for the month** = average over the long legs of (spot change in USD + its rate / 12) minus the
  average over the short legs of (spot change in USD + its rate / 12). The USD leg, if picked, has spot change 0.
- Free settings = **1** (currencies per side = 2).

## Costs (charged every month)
- **Swap markup:** a broker pays less than the full interest gap and charges more. Assumed **2% a year** on the
  gross position (1 unit long + 1 unit short = 2 units), so 2 × 2% / 12 per month.
- **Spread:** **0.03%** per unit of position changed at each rebalance (major-pair spreads are about 0.01-0.02%;
  rounded up), so a month with no change pays only the swap markup.
- **Stress:** both costs doubled (4% a year and 0.06%).

## Benchmarks
1. **Random picks (the main control):** 5,000 runs (seed 11). Each run, in the same months, picks 2 random long
   and 2 different random short currencies from the ones taking part, with the same return formula. Costs for
   random: the same swap markup, and a spread equal to the rule's own average monthly spread cost in that period
   (so random is not punished for re-picking every month). The rule beats random if its average net monthly
   return is above the 95th percentile of the random runs' averages.
2. **Information only:** the same rule without the interest income (spot changes only), and without costs.

## Statistics
- 95% interval for the average net monthly return: **calendar-year block bootstrap** (5,000 runs, seed 11).
  One test, so no family widening.
- Also shown (information only): annualised return and volatility, Sharpe ratio, worst month, worst year, and the
  largest fall from a peak.

## Year-by-year check (required in every test)
Code: `app/backtest/yearly.py`, unit % per month, each month = one "trade". A year counts with at least 10 months.
In EACH period: more than half of the counting years have an average above 0, and the total without the single
best year stays above 0. Fewer than 2 counting years = cannot pass. Failing it alone = **inconclusive**.

## Nearby-settings check (required in every test)
Code: `app/backtest/nearby.py`. One setting, neighbours fixed now: **currencies per side 1 and 3** (chosen 2).
In EACH period at least 2/3 of the 2 neighbours (so both) average above 0, and the chosen average is at most 2× the
median neighbour average. A neighbour can never replace the chosen setting. Failing it alone = **inconclusive**.

## Verdict (fixed now)
**Passes the research criteria** only if, in BOTH development and validation:
- at least 30 months,
- average net monthly return > 0, and > 0 under stress costs,
- bootstrap lower bound > 0,
- above the 95th percentile of random picks,
- the year-by-year check passes,
- the nearby-settings check passes.

**Negative observed result** = average net monthly return ≤ 0 in either period. **Inconclusive** = anything else.
A pass is a reason for a paper-only forward test with Exness's real published swaps on these pairs, not for real
money. Nothing here changes `scanner.QUALIFIED`, a strategy, a risk limit, or the dashboard. Under `CLAUDE.md` 2a,
a fail or inconclusive result freezes the project again.

## Limits
- Interbank rates, not the swaps a broker pays; the 2% markup is an assumption (Exness swaps are not checked yet).
- Monthly average rates, month-end spot prices from FRED noon New York rates, not tradable CFD prices.
- Seven currencies only; one bad year (2008) can decide the validation period.
- Leverage is not part of the test: returns are per unit of position, before choosing any size.

## After the result
- Report: `docs/carry_report.md` with every number above, the year-by-year and nearby tables, failures included,
  and a "Pre-mortem check" line per reason.
- Journal entry E23, `scripts/experiment_journal.py` and `--check`, a row in `docs/decisions.md`, a line in
  CLAUDE.md section 11. No re-run with other settings.
