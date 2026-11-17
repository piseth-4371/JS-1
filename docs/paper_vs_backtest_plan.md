# Paper-versus-backtest comparison — rules (written 2026-11-17, before the first comparison run)

**Purpose:** check that the same market data produces the same signal, entry, exit and cost in the paper engine
(`core/engine.py` + `core/paper_broker.py`) and in the backtester (`backtest/engine.py`). This tests the
*execution code*, not whether a strategy makes money. No rule, parameter, risk limit or `scanner.QUALIFIED` changes.

## Two modes
- **replay** (usable now): stored MT5 demo minutes are fed minute by minute through the REAL paper engine into a
  throwaway database (`data/replay_compare_<strategy>.db`; the real paper account is never touched), and the
  backtester runs on exactly the same minutes. The paper engine has placed no live orders yet, so this is the way
  to test it today.
- **journal** (for later): the real paper journal (`data/app.db` signals and positions) is compared with a
  backtest over the same stored minutes.

## Setup (same on both sides)
Source `mt5:MetaQuotes-Demo` `USTEC`; balance $1,000; `RiskSettings()` defaults; NAS100 costs (spread 1.5,
slippage 0.5); news calendar on. Replay days need ≥ 30 days of stored history before them (the engine's
`HISTORY_DAYS`). Each minute is replayed 5 s after it closes, as the live loop would see it. NY strategies replay
08:30–16:10 NY, London strategies 02:30–16:10; minutes outside those windows are stored without a cycle.

## Matching (fixed now)
- **Signals:** same strategy, same 5-minute bar close time and same side. Compared: kind, entry, stop, target.
- **Trades:** same fill minute and same side. Compared: entry price, stop, target, exit minute, exit price,
  exit reason, R (after costs).
- Prices must agree within 1e-6 points and R within 1e-9. Anything else is a **difference** and is listed.
- Unmatched items are listed as **paper only** or **backtest only**. For a paper signal the recorded risk/rejection
  reasons are shown, so a difference can be traced (e.g. minimum lot, pending order, news, stale data).

## Differences expected from the design (reported, not hidden or "fixed" here)
1. The paper engine checks the real USTEC minimum lot (0.1 lot); the backtester uses fractional lots, so it never
   rejects for that reason → trades only in the backtest.
2. The paper engine builds indicators from the last 30 days; the backtester from all loaded history → occasional
   different signals.
3. The paper engine skips stale or failed-validation data; the backtester has no such check.
Any other difference is treated as a possible execution bug and investigated.

## Output
`docs/paper_vs_backtest_report.md` (per strategy: counts of identical / different / one-side-only signals and
trades, the first differences in detail) and `backend/data/reports/paper_compare/*.json`.
