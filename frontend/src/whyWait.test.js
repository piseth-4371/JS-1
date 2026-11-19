import test from "node:test";
import assert from "node:assert/strict";
import { whyWait } from "./whyWait.js";

const NOW = 1_800_000_000;
const setup = (over = {}) => ({ market: "nas100", strategy: "orb", qualified: false, cost_share: 0.1, news_blackout: false, ...over });
const scan = (over = {}) => ({
  scanned_ts: NOW - 10, signal: null, qualified_strategies: [],
  markets: [{ key: "nas100", label: "NAS100", state: "open", detail: "", setups: [] },
            { key: "btc", label: "BTC", state: "closed", detail: "", setups: [] },
            { key: "gold", label: "Gold", state: "open", detail: "", setups: [] }],
  ...over,
});
const ov = (over = {}) => ({
  kill_switch: false, auto_trading: true, engine_enabled: true, trades_today: 0, consecutive_losses_today: 0,
  day_pnl_pct: 0, week_pnl_pct: 0, markets: [],
  risk_settings: { max_trades_per_day: 3, max_consecutive_losses: 2, daily_loss_pct: 2, weekly_loss_pct: 5 },
  news: { blackout_now: null, calendar_covers_now: true, calendar_until: "2026-12-31" }, ...over,
});
const cats = (r) => r.reasons.map((x) => x.category);

test("no backend means UNKNOWN, not a guess", () => {
  const r = whyWait({ scan: null, ov: null, now: NOW });
  assert.equal(r.state, "UNKNOWN");
  assert.deepEqual(cats(r), ["data"]);
});

test("nothing qualified is the main reason, and quiet open markets say no setup", () => {
  const r = whyWait({ scan: scan(), ov: ov(), now: NOW });
  assert.equal(r.state, "WAIT");
  assert.deepEqual(cats(r), ["unproven", "setup"]);
  assert.match(r.headline, /no strategy has passed its test/);
  assert.match(r.reasons[1].title, /NAS100, Gold/);
});

test("expensive setups and practice-only setups are explained", () => {
  const s = scan();
  s.markets[0].setups = [setup({ cost_share: 0.35 }), setup({ cost_share: 0.12, strategy: "silver_bullet" })];
  const r = whyWait({ scan: s, ov: ov(), now: NOW });
  const cost = r.reasons.find((x) => x.category === "cost");
  assert.match(cost.title, /^1 setup/);
  assert.match(cost.detail, /35%/);
  assert.match(r.reasons.find((x) => x.category === "unproven").detail, /2 setup\(s\)/);
  assert.equal(r.reasons.some((x) => x.title.includes("No setup on the latest bar: NAS100")), false);
});

test("stale scanner and stale or missing feeds are data problems", () => {
  const s = scan({ scanned_ts: NOW - 600 });
  s.markets[2] = { key: "gold", label: "Gold", state: "stale", detail: "newest bar closed 9 min ago", setups: [] };
  const r = whyWait({ scan: s, ov: ov({ news: { calendar_covers_now: false, calendar_until: "2026-12-31" } }), now: NOW });
  const titles = r.reasons.filter((x) => x.category === "data").map((x) => x.title);
  assert.ok(titles.includes("The scanner has stopped updating"));
  assert.ok(titles.includes("Gold: price feed is stale"));
  assert.ok(titles.includes("The news calendar does not cover today"));
  assert.equal(r.reasons[0].category, "data");
  assert.equal(r.reasons.some((x) => x.category === "setup"), false);   // a stale scan cannot claim "no setup"
});

test("all markets closed", () => {
  const s = scan();
  s.markets.forEach((m) => { m.state = "closed"; });
  assert.ok(cats(whyWait({ scan: s, ov: ov(), now: NOW })).includes("closed"));
});

test("paper-engine risk limits and a rejected signal are listed", () => {
  const signals = [{ action: "LONG", strategy: "orb", bar_close_ts: NOW - 120, risk_approved: false,
    risk_reasons: ["Minimum lot 0.1 would risk $8.59 (0.9% of equity) > allowed $5.00 (0.5%)"] }];
  const r = whyWait({ scan: scan(), ov: ov({ auto_trading: false, trades_today: 3, consecutive_losses_today: 2,
    day_pnl_pct: -2.1, news: { blackout_now: "CPI", calendar_covers_now: true } }), signals, now: NOW });
  const risk = r.reasons.filter((x) => x.category === "risk").map((x) => x.title);
  assert.equal(risk.length, 5);
  assert.ok(risk.some((t) => t.startsWith("The last paper signal was rejected")));
  assert.ok(cats(r).includes("news"));
});

test("an old rejected signal is not shown as a current reason", () => {
  const signals = [{ action: "LONG", strategy: "orb", bar_close_ts: NOW - 3600, risk_approved: false, risk_reasons: ["x"] }];
  assert.equal(whyWait({ scan: scan(), ov: ov(), signals, now: NOW }).reasons.some((x) => x.title.includes("rejected")), false);
});

test("a fresh signal from a qualified strategy is SIGNAL", () => {
  const s = scan({ qualified_strategies: [{ market: "nas100", strategy: "orb" }], signal: { expiry_ts: NOW + 300 } });
  assert.equal(whyWait({ scan: s, ov: ov(), now: NOW }).state, "SIGNAL");
  assert.equal(whyWait({ scan: { ...s, signal: { expiry_ts: NOW - 1 } }, ov: ov(), now: NOW }).state, "WAIT");
});
