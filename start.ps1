# One-click start: backs up the database, then opens the backend and the dashboard in two windows.
# Run from PowerShell in this folder:   .\start.ps1
# Paper trading only. Auto-trading stays as you last set it on the dashboard; the kill switch is respected.
# The MT5 terminal must be open for NAS100 prices (BTC uses Binance public data).

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$py = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) { Write-Host "Python venv not found at $py - see README setup." -ForegroundColor Red; exit 1 }

Write-Host "1/3 Backing up database..."
Push-Location $backend
& $py scripts\backup_db.py
Pop-Location

Write-Host "2/3 Starting backend on http://127.0.0.1:8000 ..."
Start-Process powershell -WorkingDirectory $backend -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:ENGINE_ENABLED='true'; & '$py' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

Write-Host "3/3 Starting dashboard on http://localhost:5173 ..."
Start-Process powershell -WorkingDirectory $frontend -ArgumentList @("-NoExit", "-Command", "npm run dev")

Start-Sleep -Seconds 5
Start-Process "http://localhost:5173"
Write-Host "Done. Close the two PowerShell windows to stop everything."
