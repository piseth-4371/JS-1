# LITTLE (paper trading only)

See `CLAUDE.md` for the project manual and `docs/decisions.md` for the decision log.

## Results (project frozen 2026-11-21)

**What it is:** a paper-trading control center for the Nasdaq-100 (Exness `USTEC`), with gold and BTC
on the side. FastAPI + SQLite backend, React dashboard, MT5 demo price feed, Telegram alerts.
Paper money only: there is no live order path in the code.

**What was built**
- A backtester and a paper engine that agree exactly (126 of 126 signals identical in a replay check).
- A deterministic risk manager with veto: 0.5% risk per trade, daily and weekly loss locks, kill switch.
- A news blackout (±30 min around CPI, NFP, FOMC, GDP, PCE; calendar to the end of 2027).
- A 3-market scanner that shows a signal only from a strategy that passed its tests, otherwise **WAIT**.
- An experiment journal in which every test is written down before it runs, failures included.

**What was tested:** 21 experiments with 53 strategy evaluations: 7 intraday NAS100 strategies (ICT-style
FVG, liquidity sweep, opening range, VWAP, silver bullet), the same rules on gold and BTC, daily trend,
intraday momentum, cost and volatility filters, slow multi-market trend, and turn of the month.
Data: 1-minute bars 2019-2024 (development 2019-2022, validation 2023-2024). The 2025+ data stays locked.

**Result: 0 passes.** No strategy made money after costs in both periods. The best, turn of the month,
was inconclusive and now runs as a paper forward test (no verdict before 36 trades, about 2029).
Full list: `docs/experiment_journal.md`.

**What was learned** (`docs/lessons.md`)
1. Costs decide most intraday results. Exness `USTEC` spread is about 2.9 points, double the first assumption.
2. Small samples lie: early "winners" turned negative on the full data.
3. A result must hold in both periods, not just one.
4. A filter cannot create an edge that is not there.
5. "No edge found" is a useful answer: it kept real money safe.

**Status:** frozen, then unfrozen the same day for ONE new pre-registered idea plus a weekly
health check (rules in `CLAUDE.md` section 2a). No weekly strategy tweaks.

## Backend quick start (PowerShell)

```powershell
cd backend
py -3.14 -m venv .venv                       # once
.\.venv\Scripts\python -m pip install -r requirements.txt   # once
Copy-Item .env.example .env                  # once, then edit if needed
.\.venv\Scripts\python -m pytest -q          # run tests
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/api/health and http://127.0.0.1:8000/docs

## MT5 check (read-only)
Log in to an Exness **demo** account in MetaTrader 5, then:
```powershell
.\.venv\Scripts\python scripts\check_mt5.py
```

## Dashboard (React) — PowerShell, second terminal

```powershell
cd frontend
npm install          # once
npm run dev          # opens on http://127.0.0.1:5173 (forwards /api to the backend on port 8000)
```

To see live prices, start the backend with the engine on (MT5 demo must be open):
```powershell
cd backend
$env:ENGINE_ENABLED = "true"
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Weekend BTC book (paper)

NAS100 trades on weekdays; on weekends (Fri 17:00 - Sun 17:00 New York) the engine trades BTCUSDT on paper, using free Binance public data (no account needed). Same $1,000 paper account, same risk rules, same kill switch.

```powershell
cd backend
.\.venv\Scripts\python scripts\backfill.py binance --start 2019-01-01   # BTC history for backtests
.\.venv\Scripts\python scripts\run_backtest.py --market btc            # BTC backtest (dev + validation)
```

> **Start here:** [docs/lessons.md](docs/lessons.md) explains, in plain English, what every backtest in this project found (short version: no strategy has an edge after costs).

## Daily routine (PowerShell)
One click: from this folder run `.\start.ps1` (backs up the database, then opens the backend and the dashboard).
Paper trading only; the MT5 terminal must be open for NAS100 prices.

In `backend\`:
- `.\.venv\Scripts\python scripts\daily_report.py` - yesterday's report (New York date): news, signals, risk decisions, orders, trades. Saved in `data\reports\`.
- `.\.venv\Scripts\python scripts\backup_db.py` - copy of the database into `data\backups\` (newest 7 kept). Restore: stop the server, copy a backup over `data\app.db`.
- `.\.venv\Scripts\python scripts\robustness.py --market nas100` (or `btc`) - stress test (double costs, other targets, bootstrap, Monte Carlo) on development + validation data only.
