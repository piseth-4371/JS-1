import test from "node:test";
import assert from "node:assert/strict";
import { autoMarket, newsCard, resultRow, resultsCard, signalCard, tomRow } from "./simpleView.js";

const NOW = 1_800_000_000;
const setup = (over = {}) => ({ market: "nas100", strategy: "silver_bullet", side: "LONG", entry: 100, stop: 95,
  target: 110, qualified: false, expired: false, expiry_ts: NOW + 600, cost_share: 0.1, news_blackout: false, ...over });
const scan = (setups = [], over = {}) => ({
  scanned_ts: NOW - 10, signal: null, qualified_strategies: [],
  markets: [{ key: "nas100", label: "NAS100", state: "open", setups }], ...over,
});
const ov = { kill_switch: false, auto_trading: true, engine_enabled: true, trades_today: 0, consecutive_losses_today: 0,
  day_pnl_pct: 0, week_pnl_pct: 0, markets: [],
  risk_settings: { max_trades_per_day: 3, max_consecutive_losses: 2, daily_loss_pct: 2, weekly_loss_pct: 5 },
  news: { blackout_now: null, calendar_covers_now: true, calendar_until: "2026-12-31",
          upcoming: [{ label: "CPI", ts: NOW + 7200 }, { label: "FOMC", ts: NOW + 3600 }, { label: "old", ts: NOW - 90000 }] } };

test("a failed strategy's setup is practice only, never a signal", () => {
  const c = signalCard({ scan: scan([setup()]), ov, now: NOW });
  assert.equal(c.state, "WAIT");
  assert.equal(c.signal, null);
  assert.equal(c.practice.length, 1);
  assert.equal(c.practice[0].marketLabel, "NAS100");
  assert.match(c.mainReason.title, /passed|test|qualif/i);
});

test("expired practice setups are dropped", () => {
  const c = signalCard({ scan: scan([setup({ expired: true }), setup({ expiry_ts: NOW - 1 })]), ov, now: NOW });
  assert.equal(c.practice.length, 0);
});

test("a fresh qualified signal is shown as the signal", () => {
  const sig = setup({ qualified: true, strategy: "orb" });
  const s = scan([sig], { signal: sig, qualified_strategies: [{ market: "nas100", strategy: "orb" }] });
  const c = signalCard({ scan: s, ov, now: NOW });
  assert.equal(c.state, "SIGNAL");
  assert.equal(c.signal, sig);
  assert.deepEqual(c.practice, []);
});

test("no backend data means UNKNOWN with no signal", () => {
  const c = signalCard({ scan: null, ov: null, now: NOW });
  assert.equal(c.state, "UNKNOWN");
  assert.equal(c.signal, null);
});

test("news lists upcoming events in time order and drops old ones", () => {
  const n = newsCard(ov, NOW);
  assert.deepEqual(n.upcoming.map((e) => e.label), ["FOMC", "CPI"]);
  assert.equal(n.covered, true);
  assert.equal(newsCard(null, NOW).known, false);
});

test("results keep qualified and practice apart and count losses", () => {
  const tr = { shown: { resolved: 0, wins: 0, total_r: 0, avg_r: null, recorded: 0, pending: 0, expired: 0 },
               practice: { resolved: 10, wins: 3, total_r: -2.5, avg_r: -0.25, recorded: 14, pending: 1, expired: 3 } };
  const r = resultsCard({ track_record: tr }, { closed_trades: 4, win_rate: 50, total_r: 1.2, expectancy_r: 0.3, pnl_usd: 6 });
  assert.equal(r.qualified.signals, 0);
  assert.equal(r.qualified.avgR, null);
  assert.deepEqual([r.practice.wins, r.practice.losses, r.practice.totalR], [3, 7, -2.5]);
  assert.deepEqual([r.paper.wins, r.paper.losses], [2, 2]);
  assert.equal(resultRow(null), null);
});

test("turn-of-month row shows the last finished trade and the next one", () => {
  const t = { summary: { trades: 2, verdict_after: 36, wins: 1, losses: 1, total_net_pct: -1.13, verdict: "collecting — no verdict", void: 0 },
              trades: [{ counted: true, status: "done", net_pct: 2.3, entry_date: "2026-09-29" },
                       { counted: true, status: "done", net_pct: -3.4, entry_date: "2026-10-29" },
                       { counted: true, status: "scheduled", entry_date: "2026-11-27" }],
              next: { status: "scheduled", entry_date: "2026-11-27", exit_date: "2026-12-03" } };
  const r = tomRow(t);
  assert.equal(r.last.net_pct, -3.4);
  assert.equal(r.next.entry_date, "2026-11-27");
  assert.equal(r.verdict, "collecting — no verdict");
  assert.equal(tomRow(null), null);
  assert.equal(resultsCard({ turn_of_month: t }, null).tom.trades, 2);
});

test("the chart market is picked automatically", () => {
  const gold = { market: "gold" };
  assert.equal(autoMarket({ signal: { market: "btc" }, practice: [gold] }, null, { trading_now: "nas100" }), "btc");
  assert.equal(autoMarket({ signal: null, practice: [gold] }, null, { trading_now: "nas100" }), "gold");
  assert.equal(autoMarket({ signal: null, practice: [] }, null, { trading_now: "btc" }), "btc");
  const s = { markets: [{ key: "nas100", state: "closed" }, { key: "gold", state: "open" }] };
  assert.equal(autoMarket({ signal: null, practice: [] }, s, { trading_now: null }), "gold");
  assert.equal(autoMarket(null, null, null), "nas100");
});
