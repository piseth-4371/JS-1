# LITTLE â€” Project Manual

## 1. Purpose
Learning project: a **paper-trading** control center for the Nasdaq-100 (Exness symbol `USTEC`).
Owner is a beginner learning Python/full-stack. Explain choices simply; give Windows PowerShell commands.
Success = rules followed, zero risk violations, reproducible backtest, working kill switch. **Not P&L.**

## 2. Stack
- Backend: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2, (Alembic later), pytest
- Database: SQLite in week 1 (`backend/data/app.db`), PostgreSQL later via `DATABASE_URL`
- Market data: Exness **MT5 demo** (Standard account) via the `MetaTrader5` Python package (Windows only, terminal must be running)
- Weekend book: BTCUSDT from **Binance public market data** (no account, no key). Paper only; never send orders to Binance.
- Frontend (Day 5): React + Vite + Tailwind + lightweight-charts

## 3. Strategy â€” "NY Trend-FVG v1" (frozen until backtest review)
Times America/New_York. Closed bars only.
- Bias 15m: close > EMA50 and EMA20 > EMA50 â†’ long (mirror short); else WAIT.
- Entries 09:45â€“11:30 only; flat by 15:55.
- 5m FVG: c3.low > c1.high (bull), c2 body â‰¥ 1.0Ã—ATR14, gap â‰¥ 0.15Ã—ATR14, close on bias side of session VWAP.
- Entry limit at FVG midpoint, expires after 6 bars. SL = c1.low âˆ’ 0.10Ã—ATR; stop distance must be 0.5â€“2.0Ã—ATR.
- TP fixed 2.0R. Avoid Â±30 min of high-impact US news (implemented in `core/news.py` for CPI/NFP/FOMC/GDP/PCE; calendar `app/calendar/us_high_impact_events.csv`, valid to 2026-12-31 â€” extend it from BLS/Fed/BEA sources before 2027), extreme ATR, stale/gappy data.

## 4. Risk restrictions (NEVER raise without explicit owner approval)
- Virtual balance: **$1,000 paper** (owner approved 2026-11-13, was $10). Virtual money only; risk % limits unchanged.
- Risk/trade 0.5% default, 1% hard ceiling in code. Daily loss âˆ’2%, weekly âˆ’5% â†’ lock.
- Max 3 trades/day, 1 open position, stop after 2 consecutive losses that day.
- Mandatory stop-loss. No martingale, grid, averaging down, or leverage beyond equity/price cap.
- If broker minimum lot Ã— stop distance > allowed risk â†’ **REJECT** (at $10 this rejected every USTEC trade; at $1,000 most fit).
- Risk Manager is deterministic Python with absolute veto. No LLM in the trading loop.
- **Live trading does not exist in this codebase.** Do not add a live order path.

## 5. Architecture
One FastAPI process. Engine loop: MarketData â†’ Strategy (pure) â†’ RiskManager (pure, veto) â†’ PaperBroker (internal simulator) â†’ DB journal. Kill switch is a persisted backend flag checked before every action.

## 6. Folder structure
```
nas100-control-center/
  CLAUDE.md  README.md  .gitignore  docs/decisions.md
  backend/
    requirements.txt  .env.example
    app/  main.py config.py db.py  api/  core/  models/
    scripts/  check_mt5.py
    tests/
  frontend/ (Day 5)
```

## 7. Coding conventions
- Type hints everywhere; Pydantic models for API I/O.
- Store timestamps in UTC; display in New York time.
- Every market-data record carries `source` and `ts`. Never fabricate prices.
- Pure functions for strategy and risk (no DB / network inside).

## 8. API contracts (planned)
`GET /api/health` (done) Â· overview Â· market/bars Â· signals Â· risk/decisions Â· positions Â· orders Â· journal Â· settings/risk Â· controls/auto-trading Â· controls/kill.

## 9. Testing
`cd backend; .\.venv\Scripts\python -m pytest -q` must pass before finishing any task. Risk rules need tests before engine code.

## 10. Security
- Secrets only in `backend/.env` (gitignored). Never print or commit them. Never put credentials in code.
- Server binds to 127.0.0.1 only.

## 11. Current progress
- [x] Day 0: research & plan approved (2026-11-13), revision 2: Exness MT5 demo, $10 kept, SQLite.
- [x] Day 1: setup, health endpoint, MT5 USTEC check (MetaQuotes-Demo: min lot 0.1 = $0.10/pt; ~30 days M1 history)
- Owner decision: keep $10 â†’ Risk Manager will reject all USTEC trades; system logs signals + rejections only. Do not raise limits.
- Owner decision 2026-11-13: paper balance raised to $1,000 (STARTING_BALANCE) so trades fit the 0.1 min lot. Risk % limits unchanged. Real account is still 1000 USC = $10: this is NOT a reason to trade it live.
- [x] Day 2: market data. `app/core/market_data.py` (Bar, validate, coverage, stale, resample), MT5 + Dukascopy sources, `bars` table, `scripts/backfill.py`, `scripts/compare_sources.py`, `GET /api/market/bars`. 25 tests pass. Stored: MT5 60 days, Dukascopy 2026-10-19..11-12.
- [x] Day 3 (+ backtester pulled forward from Day 6): `core/indicators.py`, `core/features.py` (causal 5m table), `core/risk.py` (hard limits, full reason list), 5 strategies in `core/strategies/` (trend_fvg, sweep_mss_fvg, orb, vwap_reversion, silver_bullet), `backtest/engine.py` + `metrics.py`, `scripts/run_backtest.py`. 64 tests pass.
- Backtest splits fixed in advance: dev 2019â€“2022, validation 2023â€“2024, OOS 2025+ (run ONCE with --oos). Do not tune on OOS.
- [x] Day 4: paper execution. `core/fills.py` (shared fill rules), `core/paper_broker.py`, `core/engine.py` (cycle), `core/live_loop.py` (MT5 every 20 s when ENGINE_ENABLED=true), `core/state.py` (persisted kill_switch / auto_trading / active_strategy), `api_trading.py` (overview, signals, orders, positions, events, controls). 76 tests pass. Live check on MT5 demo OK.
- [x] Day 5: React + Vite + Tailwind + lightweight-charts dashboard in `frontend/` (header with PAPER badge, data source + stale flag, strategy select, auto-trading, kill switch; overview tiles; NY-time chart with EMA20/50 (15m), VWAP, PDH/PDL/ONH/ONL, FVG markers; signal + risk panel; journal tabs). `GET /api/market/analysis`. 80 backend tests pass; checked in browser with live MT5 demo data.
- [x] Day 6 (partial): paper metrics `/api/journal/metrics` + Metrics tab, Markdown backtest report, prior-day-level fix. FULL BACKTEST STILL PENDING (download).
- [x] Day 7: `scripts/replay_day.py` (full-day replay through the real engine), failure-injection tests (`tests/test_reliability.py`), NumPy-bytes bug fix, engine performance fix, `.claude/` skills (risk-audit, backtest-review, teach-step) + protect_files hook, `docs/review_day7.md`. 89 tests pass.
- [x] London variants (owner approved 2026-11-13): `london_trend_fvg`, `london_sweep_mss_fvg`; features `lmod` (London clock), `lvwap`, Asia range `ash`/`asl`; positions may be held 03:00-15:55 NY. 95 tests pass. 2019 smoke run: both London variants negative so far (not conclusive).
- [x] Weekend BTC book (owner approved 2026-11-13, Binance public data): `core/markets.py` (NAS100 + BTCUSD books, holding windows, costs), `sources/binance_source.py`, `backfill.py binance`, BTC loop in `live_loop.py`, broker scoped per book (shared account), `btc_weekend_trend_fvg`, `run_backtest.py --market btc`, dashboard NAS100/BTC toggle + 'Trading now'. 105 tests pass.
- [x] Auto-switch research: `app/backtest/selector.py` + `scripts/run_selector.py` (weekly walk-forward, no look-ahead, 5 tests). 2019 result: worse than fixed strategies; not enabled. 110 tests pass.
- [x] News blackout (2026-11-13): 255 sourced events 2019-2026, enforced in backtester + engine + broker, dashboard badge. 118 tests pass.
- [x] Robustness tool (`scripts/robustness.py`), daily paper report (`scripts/daily_report.py`), DB backup (`scripts/backup_db.py`), `start.ps1`, BEA GDP + PCE in the news calendar (444 events). 127 tests pass.
- [x] BTC backtests (2019-2024): all 5 weekend strategies fail (fees 0.4-1.1R per trade, ~0R before costs). Overview speed fix. 131 tests pass.
- [x] Cost research: real demo spread ~1 pt (keep 2.0 assumption); cost filter research wrapper (skip if cost > 20% of risk), partial dev data: mixed, not validated. 134 tests pass.
- [ ] Next: finish download â†’ run backtest â†’ review â†’ choose strategy (see docs/review_day7.md Â§5â€“6)
- Data facts: MT5 times = server time (Europe/Athens for MetaQuotes-Demo). Dukascopy month in URL is 0-based, price Ã·1000.

## 12. Pending decisions
- Confirm USTEC contract size / min lot / spread from `scripts/check_mt5.py`.
- How much M1 history MT5 provides (fallback: Dukascopy).
- Full Dukascopy backfill 2019â†’2026 (~1 hour download) before Day 6.
