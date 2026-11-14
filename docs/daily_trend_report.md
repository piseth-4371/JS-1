# Daily trend research (NAS100) — generated 2026-11-14 12:44 UTC

- Rules fixed before testing: docs/daily_trend_preregistration.md (commit 923b5a6)
- Data: HistData NSXUSD 1-minute → 1549 daily bars 2019-01-02 to 2024-12-31; 2025+ locked
- Costs: 2.0 points per trade + overnight financing 5%/year of position value [assumptions]
- Control: same side, same holding length, same stop, random entry day (500 runs)

| strategy | split | trades | long/short | win% | avg R (fin 5%) | avg R fin 0% | avg R fin 10% | avg R costs x2 | control avg R | beats control in | avg days held | PASS? |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sma100_long | development | 27 | 27/0 | 19% | -0.07 | +0.04 | -0.17 | -0.17 | +0.14 | 21% | 34 | FAIL |
| sma100_long | validation | 12 | 12/0 | 33% | +0.67 | +0.85 | +0.48 | +0.48 | +0.23 | 83% | 54 | FAIL |
| donchian_55_20 | development | 15 | 10/5 | 40% | +0.08 | +0.29 | -0.12 | -0.13 | +0.03 | 57% | 57 | FAIL |
| donchian_55_20 | validation | 8 | 5/3 | 50% | +0.44 | +0.68 | +0.20 | +0.20 | +0.17 | 69% | 59 | FAIL |

## Verdict

- **sma100_long: FAILS** (needs avg R > 0, beat the random-timing control in ≥90% of runs, and ≥20 trades, in BOTH splits)
- **donchian_55_20: FAILS** (needs avg R > 0, beat the random-timing control in ≥90% of runs, and ≥20 trades, in BOTH splits)

'costs x2' = 4 points per trade and 10% financing. Few trades per split means wide uncertainty. Past results do not guarantee future results. Research only: not connected to the live engine.
