# Buy the drop — results

Made by `scripts/buy_the_drop_test.py` on 2026-11-21. Rules were committed before any result: `docs/buy_the_drop_preregistration.md` (commit 6943a95). Run once. Measurement only: no strategy, risk limit or `scanner.QUALIFIED` changed.

## Verdict: **negative observed result**

Rule: buy the Nasdaq Composite at a close that is the lowest of the last 10 trading days, sell at the close 5 trading days later, one trade at a time. Costs: 0.02% spread + 7%/year financing per night (stress: doubled). Returns are per trade.

| period | trades | before costs | after costs | 95% range (years resampled) | stress | random timing 95th pct | trades won | worst trade | all checks |
|---|---:|---:|---:|---|---:|---|---:|---:|---|
| Development 1971-1999 | 446 | -0.184% | **-0.342%** | -0.626% to -0.030% | -0.499% | +0.312% (0.0% beaten) | 48% | -20.6% | no |
| Validation 2000-2024 | 400 | +0.362% | **+0.203%** | -0.122% to +0.526% | +0.045% | +0.283% (87.0% beaten) | 54% | -13.3% | no |

**Random timing** = the same number of 5-day holds started on random days, same costs, 5,000 runs. The rule must beat 95% of them.

Information only — average 5-day hold after costs over every start day: development +0.124%, validation +0.023%.

## Year-by-year and nearby settings

### Development 1971-1999

Year-by-year: **fails** (7 of 29 counting years positive; total without the best year -178.42%) — most years positive: only 7 of 29 years above 0; one lucky year: total without the best year (1999) is -178.422

| year | trades | average per trade (%) | total (%) |
|---:|---:|---:|---:|
| 1971 | 15 | -0.200 | -2.99 |
| 1972 | 16 | -0.007 | -0.12 |
| 1973 | 26 | -0.962 | -25.01 |
| 1974 | 22 | -1.850 | -40.70 |
| 1975 | 14 | -0.332 | -4.64 |
| 1976 | 12 | -0.265 | -3.18 |
| 1977 | 15 | -0.137 | -2.06 |
| 1978 | 13 | -0.909 | -11.81 |
| 1979 | 10 | -0.377 | -3.77 |
| 1980 | 12 | -1.035 | -12.42 |
| 1981 | 19 | -0.651 | -12.38 |
| 1982 | 16 | -1.162 | -18.59 |
| 1983 | 15 | -0.097 | -1.46 |
| 1984 | 24 | -0.980 | -23.51 |
| 1985 | 15 | -0.270 | -4.05 |
| 1986 | 15 | -0.382 | -5.73 |
| 1987 | 12 | -1.429 | -17.15 |
| 1988 | 16 | -0.076 | -1.21 |
| 1989 | 13 | +0.281 | +3.65 |
| 1990 | 20 | -1.416 | -28.31 |
| 1991 | 14 | +0.967 | +13.53 |
| 1992 | 17 | -0.073 | -1.23 |
| 1993 | 15 | +0.483 | +7.24 |
| 1994 | 18 | -0.001 | -0.02 |
| 1995 | 11 | +1.325 | +14.58 |
| 1996 | 14 | +0.092 | +1.28 |
| 1997 | 12 | -0.230 | -2.76 |
| 1998 | 13 | +0.339 | +4.41 |
| 1999 | 12 | +2.171 | +26.06 |

Nearby settings: **fails** — plateau: only 0 of 4 nearby settings above 0 (need 3); not above 0: lookback 7 (chosen 10), lookback 13 (chosen 10), hold 4 days (chosen 5), hold 6 days (chosen 5)

| setting | average per trade (%) |
|---|---:|
| **lookback 10, hold 5 (chosen)** | -0.342 |
| lookback 7 (chosen 10) | -0.283 |
| lookback 13 (chosen 10) | -0.491 |
| hold 4 days (chosen 5) | -0.387 |
| hold 6 days (chosen 5) | -0.356 |

### Validation 2000-2024

Year-by-year: **passes** (17 of 23 counting years positive; total without the best year +62.62%)

| year | trades | average per trade (%) | total (%) |
|---:|---:|---:|---:|
| 2000 | 17 | -1.254 | -21.31 |
| 2001 | 19 | -1.090 | -20.71 |
| 2002 | 24 | -0.088 | -2.11 |
| 2003 | 16 | +1.448 | +23.17 |
| 2004 | 17 | +0.268 | +4.56 |
| 2005 | 18 | +0.020 | +0.37 |
| 2006 | 15 | +0.788 | +11.82 |
| 2007 | 11 | +0.870 | +9.57 |
| 2008 | 22 | -0.370 | -8.13 |
| 2009 | 14 | +1.140 | +15.96 |
| 2010 | 13 | +0.053 | +0.68 |
| 2011 | 21 | +0.455 | +9.55 |
| 2012 | 17 | +0.904 | +15.36 |
| 2013 | 12 | +1.563 | +18.76 |
| 2014 | 16 | +0.247 | +3.95 |
| 2015 | 16 | +0.151 | +2.41 |
| 2016 | 19 | +0.102 | +1.94 |
| 2017 | 14 | +1.262 | +17.66 |
| 2018 | 16 | -0.294 | -4.70 |
| 2019 (too few trades) | 8 | -0.004 | -0.03 |
| 2020 (too few trades) | 9 | -0.486 | -4.37 |
| 2021 | 14 | +0.900 | +12.60 |
| 2022 | 26 | -1.117 | -29.04 |
| 2023 | 14 | +0.708 | +9.91 |
| 2024 | 12 | +1.126 | +13.52 |

Nearby settings: **passes**

| setting | average per trade (%) |
|---|---:|
| **lookback 10, hold 5 (chosen)** | +0.203 |
| lookback 7 (chosen 10) | +0.166 |
| lookback 13 (chosen 10) | +0.225 |
| hold 4 days (chosen 5) | +0.132 |
| hold 6 days (chosen 5) | +0.170 |

## Pre-mortem check

1. **Crashes** (2000-2002, 2008 make validation negative): **did not happen.** Validation was positive
   (+0.203% per trade) despite both crashes. The loss came from the development period instead.
2. **Does not beat random timing:** **happened, in both periods.** Development beat 0.0% of random runs,
   validation 87.0% (95% needed).
3. **Costs and fading since 2000:** **did not happen as written.** The opposite: before costs, development was
   already negative (−0.184%), and validation was better (+0.362% before costs, still +0.045% under stress).

**Not foreseen** (information only, not part of the verdict): before 2000 the Nasdaq Composite's daily returns
tended to continue the next day (lag-1 autocorrelation +0.205 in 1971-1999, −0.064 in 2000-2024; a known effect of
small, rarely traded stocks in old index data). So in the old period a drop tended to keep going instead of
bouncing. The 2000-2024 result looks better, but its 95% range crosses zero and it does not beat random timing,
so it is not evidence of an edge. Choosing only the later period now would be picking the result after seeing it.

## Limits
- Nasdaq Composite, not the Nasdaq-100 CFD; signal and entry on the same close, no slippage; dividends ignored.
- 0.02% spread and 7% financing are assumptions for today's Exness account; real older costs were higher.
- No stop: single trades can lose a lot in a crash. This is evaluation 54 in this project.
- A pass would only justify a paper forward test, never real money.
