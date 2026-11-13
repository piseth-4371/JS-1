---
name: risk-audit
description: Audit any change that touches risk, execution or the engine (backend/app/core/risk.py, paper_broker.py, engine.py, fills.py, api_trading.py). Use before finishing such a change or when the owner asks "is this safe?".
---

# Risk audit

Run this checklist on the changed code. Report each item as PASS / FAIL with the file and line.

1. **Hard limits unchanged**: `HARD_LIMITS` in `backend/app/core/risk.py` still has risk_pct 1.0, daily 2.0, weekly 5.0, 3 trades/day, 1 position, 2 consecutive losses, leverage 20. Any increase needs the owner's explicit approval in chat.
2. **No bypass**: every path that creates an `OrderRow` goes through `risk.evaluate()` first (search for `broker.place(` and `OrderRow(`).
3. **Stop-loss mandatory**: no order can exist without a finite stop on the correct side.
4. **Kill switch**: `engine._cycle` checks `kill_switch` before the strategy runs; `/api/controls/kill` cancels orders and closes positions immediately.
5. **Paper only**: no MT5 `order_send`, no broker order API, no "live" mode. `trading_mode` is `Literal["paper"]`.
6. **No martingale / grid / averaging**: position size never depends on previous losses except to reduce or stop.
7. **Tests**: run `cd backend; .\.venv\Scripts\python -m pytest -q tests/test_risk.py tests/test_paper_trading.py tests/test_reliability.py` and paste the summary line.

Finish with: overall PASS/FAIL and what must be fixed.
