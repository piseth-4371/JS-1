# Day 7 Review: LITTLE (paper)

Date: 2026-11-13 · Status: **Version 1 built. Paper only. No strategy is proven yet.**

## 1. What exists now

| Part | Where | Verified by |
|---|---|---|
| Market data (MT5 demo + Dukascopy), validation, UTC handling | `backend/app/core/market_data.py`, `sources/` | tests; MT5 vs Dukascopy cross-check over 25,270 minutes (mean diff 3.3 pts, 0 h time shift) |
| 5 strategies (Trend-FVG, Sweep+MSS+FVG, ORB, VWAP reversion, Silver Bullet) | `core/strategies/` | unit tests on hand-built candles; replay |
| Risk Manager with hard limits and full reason list | `core/risk.py` | 22 tests |
| Paper broker + engine + kill switch + reconciliation | `core/paper_broker.py`, `core/engine.py` | tests incl. restart, duplicates, kill switch |
| Backtester (shared fill rules, costs, splits) + report | `backtest/`, `scripts/run_backtest.py` | 9 fill-rule tests; 4-week smoke run |
| Dashboard | `frontend/` | checked in the browser with live MT5 demo data |
| Claude Code: `CLAUDE.md`, 3 skills, 1 safety hook | `.claude/` | hook blocks `.env` edits and `order_send(` (tested by piping JSON) |

**Automated tests: 89 passing.**

## 2. Day 7 reliability results

Full-day replay of **2026-11-12** through the real engine (`scripts/replay_day.py`, 460 one-minute cycles, separate `data/replay.db`):

| Strategy | Balance | Result |
|---|---|---|
| trend_fvg | $10 | no setup that day (93 WAIT signals), 0 errors |
| orb | $10 / $1,000 | skipped: opening range was 344 pts = 5.2 × ATR (> 3 × ATR rule). Correct |
| vwap_reversion | $10 | 2 signals, **both rejected**: min lot would risk $6.07 / $3.91 (61% / 39% of equity) |
| vwap_reversion | $1,000 | 1 rejected (min lot = 0.6% > 0.5%), 1 traded: SHORT → target, **+1.96 R after costs**, 0 errors |

One trade proves the **plumbing** works. It says nothing about whether the strategy is any good.

Failure-injection tests added (all pass): MT5 terminal closed, network error, an exception inside a cycle (loop keeps running); an impossible candle (WAIT + ERROR event); the feed stops mid-session (WAIT + WARN); the kill switch survives a restart; a position left open over a restart is closed at 15:55; an order without a stop is rejected.

## 3. Bugs found and fixed this week

1. MT5 bar times are **server time**, not UTC (forum claim was wrong). Fixed with `MT5_SERVER_TZ` + live check.
2. Prior-day high/low missing before 09:30 → fixed, test added.
3. **NumPy numbers saved as bytes in SQLite** → the broker crashed when an order existed. Found only by the full replay; fixed in `Order.__post_init__`, regression test added.
4. Engine performance: each cycle re-processed every stored minute (~40,000 DB queries every 20 s) → now only new minutes; replay time went from >10 min to ~2.5 min.

## 4. What we know vs. what is still unknown

**Known (supported by evidence)**
- With **$10**, USTEC's 0.1 minimum lot makes every realistic trade too large: the Risk Manager rejects them all. This is the rules working, not a bug.
- The pipeline is consistent: backtest and paper trading use the same fill rules and the same Risk Manager.
- The $300 target was never reachable within the risk rules (best case ≈ +16% for 15 straight wins).

**Unknown (not yet tested)**
- **Whether ANY of the 5 strategies has an edge after costs.** The 2019–2024 history download is still running (Dukascopy rate-limits us). Until development AND validation results exist, every strategy is unproven.
- The real Exness USTEC spread/commission and minimum lot (all numbers so far are from MetaQuotes-Demo; costs are an assumption: 1.5 + 0.5 pts).
- Behaviour around high-impact news: there is no economic-calendar filter yet.

## 5. Gates before anything goes live (recommended, not negotiable by the system)

1. Development (2019–2022) **and** validation (2023–2024): average R > 0 after costs, ≥ 100 trades each, max drawdown acceptable to you.
2. Out-of-sample (2025–2026) run **once** (`--oos`) with frozen rules: still positive.
3. ≥ 100 paper trades on the live engine that match the backtest's behaviour.
4. Costs re-checked against a real Exness account (spread, commission, min lot).
5. An account size where the minimum lot fits the stop at ≤ 1% risk (the backtest's "$ needed" column, around $800–1,400 at 0.5% in the 4-week sample).
6. A written decision by you, plus a separate code review, before any live order code is written. (The hook currently blocks `order_send(`.)

## 6. Next steps (in order)

1. Let the download finish → run `scripts/run_backtest.py` → review `docs/backtest_report.md` with the `backtest-review` skill.
2. Pick at most one or two strategies that pass development + validation. Drop the rest.
3. Run the engine in paper mode for weeks, not days; read the Metrics tab only after 30+ trades.
4. Optional: a high-impact news filter (CSV of CPI/FOMC/NFP dates), Exness demo comparison, Git + GitHub backup.
