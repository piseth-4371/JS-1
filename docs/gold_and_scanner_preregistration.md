# Gold test + 3-market scanner — rules fixed BEFORE testing (2026-11-14)

Owner request (2026-11-14): a **signals-only** scanner over NAS100, BTC and gold (XAUUSD) that shows ONE
qualifying signal or WAIT, plus a tracker. No bot, no orders, no real money. The words "strongest" or a rank
are never shown as a chance of winning.

## 1. Gold data
HistData.com XAUUSD 1-minute bars 2019–2024 (same provider and clock as NSXUSD: UTC−4 during UK summer time,
else UTC−5; checked on the 2019 file: weekly open at 18:00 NY, same October repeated hour, which is dropped).
2025+ never imported (locked).

## 2. Gold strategy test
- Strategies: the 7 NAS100 intraday strategies (`trend_fvg`, `sweep_mss_fvg`, `orb`, `vwap_reversion`,
  `silver_bullet`, `london_trend_fvg`, `london_sweep_mss_fvg`) with their rules **unchanged** (New York clock,
  ATR-based, so they do not depend on the price scale). No gold-specific tuning.
- Holding window: same as NAS100 (03:00–15:55 NY weekdays). News blackout: same calendar (USD events move gold).
- Costs [assumption]: spread $0.30 + slippage $0.10 = **$0.40 per ounce per trade**, also shown doubled.
  Not yet measured on the MT5 demo.
- Splits: development 2019–2022, validation 2023–2024.
- **Pass rule (per strategy, BOTH splits):** avg R > 0; avg R still > 0 with doubled costs; bootstrap
  P(no edge) ≤ 10%; at least 50 trades.

## 3. What "qualifies" for the scanner
A strategy may produce a scanner signal only if it **passed development AND validation on that market**
(NAS100 results: docs/backtest_report.md; BTC: docs/backtest_report_btc.md; gold: this test).
As of this file, **no NAS100 or BTC strategy qualifies.** Gold is unknown until the test above runs.

## 4. Scanner behaviour
1. Every closed 5-minute bar, look at each market that is open now (NAS100 weekdays 03:00–15:55 NY; BTC weekends;
   gold weekdays 03:00–15:55 NY).
2. Per market, check: data fresh (last bar ≤ 2 min old), inside the trading window, no news blackout, and a setup
   from a **qualified** strategy with entry, stop, target, expiry.
3. Cost check: skip a setup when cost > 20% of its risk.
4. If several qualify: show the one whose strategy had the highest **validation** avg R; ties → lowest cost share.
5. Nothing qualifies → **WAIT**, with the reason per market. Unqualified setups may be listed underneath as
   "practice only — this strategy failed its backtest", never as the signal.
6. Tracker: every signal the scanner shows (qualified or practice) is stored, and its outcome
   (target / stop / expired) is filled in later from real prices, so the scanner's own record can be checked.
