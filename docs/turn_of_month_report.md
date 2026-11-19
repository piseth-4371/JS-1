# Turn of the month — results

Made by `scripts/turn_of_month_test.py` on 2026-11-19. Rules were committed before any result: `docs/turn_of_month_preregistration.md`. Measurement only: no strategy, risk limit or `scanner.QUALIFIED` changed.

## Verdict: **inconclusive**

Rule: buy the Nasdaq Composite at the close of the second-to-last trading day of each month, sell at the close of the 3rd trading day of the next month. Costs: 0.02% spread + 7%/year financing per night (stress: doubled). Returns are per trade.

| period | trades | before costs | after costs | 95% range (years resampled) | stress | random timing 95th pct | trades won | all checks |
|---|---:|---:|---:|---|---:|---|---:|---|
| Development 1971-1999 | 347 | +0.632% | **+0.496%** | +0.230% to +0.736% | +0.360% | +0.278% (100.0% beaten) | 64% | yes |
| Validation 2000-2024 | 299 | +0.329% | **+0.193%** | -0.125% to +0.520% | +0.056% | +0.288% (85.9% beaten) | 54% | no |

**Random timing** = the same number of 4-day holds started on random days, same costs, 5,000 runs. The rule must beat 95% of them.

## Average daily price move (information only)

| period | on the 4 turn-of-month days | on all days |
|---|---:|---:|
| Development 1971-1999 | +0.159% | +0.055% |
| Validation 2000-2024 | +0.084% | +0.037% |

## By decade (information only, not part of the verdict)

| decade | trades | after costs |
|---|---:|---:|
| 1970s | 107 | +0.233% |
| 1980s | 120 | +0.584% |
| 1990s | 120 | +0.643% |
| 2000s | 120 | +0.223% |
| 2010s | 120 | +0.165% |
| 2020s | 59 | +0.186% |

## Limits
- Nasdaq Composite, not the Nasdaq-100 CFD; close prices with no slippage; dividends ignored.
- 0.02% spread and 7% financing are assumptions for today's Exness account; real older costs were higher.
- About 12 trades a year, so single years are noisy. This is evaluation 53 in this project.
- A pass would only justify a paper forward test, never real money.
