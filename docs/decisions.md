# Decision Log

| Date | Decision | Why |
|---|---|---|
| 2026-11-13 | Paper trading only; live trading not implemented | Capital preservation; beginner |
| 2026-11-13 | Strategy: NY Trend-FVG v1 (Trend + Pullback + FVG) | More mechanical and testable than Sweep+MSS |
| 2026-11-13 | Broker/data: Exness MT5 demo (Standard), symbol USTEC | Owner uses Exness; Cent accounts reportedly MT4-only without indices |
| 2026-11-13 | Execution: internal paper simulator first; MT5 demo orders = Day 7 stretch | Testable, replayable, no credentials needed |
| 2026-11-13 | Virtual balance $10 (owner's choice) | Mirrors 1000 USC cent account. Consequence: Risk Manager will reject most trades (0.01 lot × 20–40 pt stop ≈ 2–4% risk > 0.5%) |
| 2026-11-13 | SQLite for week 1 | Zero install; switch to PostgreSQL via DATABASE_URL later |
| 2026-11-13 | Correction: owner's cent account runs on **MT5** (server Exness-MT5Real25, currency USC), so the "Cent = MT4 only" claim from reviews was wrong for this account. Whether USTEC exists on cent is still unverified | Seen by `check_mt5.py`. The script stopped because the account is real, not demo |
| 2026-11-13 | MT5 check on **MetaQuotes-Demo** (not Exness): USTEC exists; contract_size 1, min lot 0.1, step 0.1, tick 0.01 → **$0.10 per index point at min lot**. At $10 / 0.5% the largest allowed stop is 0.5 points → **every realistic trade is rejected**. M1 history available: ~30 days only (30,173 bars from 2026-10-14) | `scripts/check_mt5.py` output. Exness values still to confirm on an Exness demo. Backtests need another history source (Dukascopy) |
| 2026-11-13 | **Owner keeps $10 and accepts that no trades will be taken.** Risk limits stay unchanged. The system will log signals and risk rejections only | Owner's decision after seeing the min-lot math. The rejection log is still useful for checking strategy and risk logic |
| 2026-11-13 | **MT5 bar times are server time, not UTC.** MetaQuotes-Demo = Europe/Athens (UTC+2 winter, +3 summer). Converted with `MT5_SERVER_TZ`; the live tick is checked against it | Live tick 06:18 vs real UTC 04:18 |
| 2026-11-13 | Backtest history from Dukascopy `USATECHIDXUSD` (free, 1-min, price ÷ 1000). HTTPS timed out, so it falls back to HTTP; the server rate-limits (503), so we download day by day with back-off | Cross-check vs MT5 over 25,270 minutes: mean abs close diff 3.3 pts, best time shift 0h (incl. across DST changes) |
| 2026-11-13 | MT5 history limited by the terminal's "Max bars in chart" (100,000): ~60–70 days of M1 | `copy_rates_range` fails for 90 days |
| 2026-11-13 | Alembic deferred; tables created with `create_all` for now | Keep week 1 simple |
| 2026-11-13 | Owner asked to "test all" strategies: Trend-FVG, Sweep+MSS+FVG, Opening Range Breakout, VWAP reversion, Silver Bullet. All share one backtester, one cost model (spread 1.5 + slippage 0.5 pts [assumption]) and the real Risk Manager. Ranked by expectancy in R on dev, confirmed on validation | Let data choose, not opinion |
| 2026-11-13 | Backtest fill rules: stop-first when one minute touches both; no profit on the fill minute; flat at 15:55 NY | Pessimistic on purpose |
| 2026-11-13 | Paper broker shares fill rules with the backtester (`core/fills.py`). Auto-trading is OFF by default; kill switch persisted in DB, closes positions at last price and forces auto-trading OFF; reset does not re-enable it | Paper = backtest behaviour; safest defaults |
| 2026-11-13 | Engine re-runs the strategy over today's bars each cycle (no in-memory strategy state) | Restart-safe and deterministic |
| 2026-11-13 | $300 target is not a success criterion | Mathematically unreachable within risk rules (best case ≈ +16% in 15 winning trades) |
| 2026-11-13 | Bug fix: prior-day high/low were missing before 09:30 and on days without a session yet; now taken from the most recent earlier session | Seen on the dashboard after midnight NY; test added |
| 2026-11-13 | Paper-trade metrics (`/api/journal/metrics`) always state the sample size; under 30 trades = "do not conclude / do not change rules" | Avoid optimising on noise |
| 2026-11-13 | Bug fix: NumPy int64 timestamps from strategies were stored as bytes by SQLite (broker crash). Order now converts to plain Python numbers | Found by full-day replay |
| 2026-11-13 | Engine only processes new minutes and skips the feature rebuild when the newest 5m bar was already evaluated | ~40k DB queries per cycle before; replay >10 min → ~2.5 min |
| 2026-11-13 | Claude Code: CLAUDE.md + skills risk-audit, backtest-review, teach-step + PreToolUse hook blocking .env edits and `order_send(` | Enforced by the harness, not memory |
| 2026-11-13 | Live-trading gates written in docs/review_day7.md §5 | Profit over 7 days is never enough |
