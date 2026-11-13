# NAS100 AI Trading Control Center (paper trading only)

See `CLAUDE.md` for the project manual and `docs/decisions.md` for the decision log.

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
