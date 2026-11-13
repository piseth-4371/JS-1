---
name: backtest-review
description: Review a backtest or a new/changed strategy for look-ahead bias, unrealistic fills, missing costs and overfitting before trusting its results. Use whenever backend/app/core/strategies/*, features.py, backtest/* change, or before reporting backtest numbers.
---

# Backtest review

Check and report PASS / FAIL for each:

1. **Closed bars only**: strategies read only `a[...][j]` with `j <= i`; features are causal (`tests/test_indicators.py` passes).
2. **Fill realism**: shared rules in `core/fills.py` (stop first when both hit, no profit on the fill minute, gaps fill at the worse price for stops).
3. **Costs included**: spread and slippage are non-zero in the run being reported (`--spread`, `--slippage`).
4. **Split discipline**: rules were frozen before looking at validation; the 2025+ out-of-sample run (`--oos`) is used ONCE. If someone tunes after seeing OOS, say the OOS result is no longer valid.
5. **Sample size**: flag any split with fewer than 30 trades as "no conclusion".
6. **Report**: quote `docs/backtest_report.md` numbers (trades, win %, avg R, PF, max DD) for development AND validation. A strategy is only a candidate if avg R > 0 after costs in BOTH.

Never describe a strategy as profitable or guaranteed. State what the data supports and what is uncertain.
