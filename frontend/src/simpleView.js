import { whyWait } from "./whyWait.js";

// Pure logic for the Simple view: what to show on the four cards.
// It never creates a signal. A trade to enter is shown only when whyWait() says SIGNAL,
// which needs a fresh signal from a strategy that passed its pre-registered test.

// The one signal card: SIGNAL (qualified, fresh) or WAIT/UNKNOWN with the main reason,
// plus any practice-only setups from strategies that failed their test.
export function signalCard({ scan, ov, signals = [], now }) {
  const w = whyWait({ scan, ov, signals, now });
  const practice = [];
  for (const m of scan?.markets ?? []) {
    for (const s of m.setups ?? []) {
      if (s.qualified || s.expired || (s.expiry_ts != null && s.expiry_ts <= now)) continue;
      practice.push({ ...s, marketLabel: m.label ?? m.key });
    }
  }
  return {
    state: w.state,
    signal: w.state === "SIGNAL" ? scan.signal : null,
    mainReason: w.reasons[0] ?? null,
    headline: w.headline,
    practice: w.state === "SIGNAL" ? [] : practice,
  };
}

// Which market the Simple view's chart shows, chosen automatically (no picker):
// the signal's market, else the first practice setup's, else the market trading now, else the first open one.
export const CHART_MARKETS = ["nas100", "btc", "gold"];
export function autoMarket(card, scan, ov) {
  const pick = [card?.signal?.market, card?.practice?.[0]?.market, ov?.trading_now,
    ...(scan?.markets ?? []).filter((m) => m.state === "open").map((m) => m.key)];
  return pick.find((k) => CHART_MARKETS.includes(k)) ?? "nas100";
}

// News: is entry blocked now, does the calendar cover today, and the next events.
export function newsCard(ov, now, limit = 5) {
  const n = ov?.news;
  if (!n) return { known: false, blackout: null, covered: false, until: null, upcoming: [] };
  const upcoming = (n.upcoming ?? [])
    .filter((e) => e.ts != null && e.ts >= now - 3600)
    .sort((a, b) => a.ts - b.ts)
    .slice(0, limit);
  return { known: true, blackout: n.blackout_now ?? null, covered: !!n.calendar_covers_now,
           until: n.calendar_until ?? null, upcoming };
}

// One results row from a track-record summary (backend api_scanner.summary).
export function resultRow(s) {
  if (!s) return null;
  const resolved = s.resolved ?? 0;
  const wins = s.wins ?? 0;
  return {
    signals: s.recorded ?? resolved,
    finished: resolved,
    wins,
    losses: resolved - wins,
    pending: s.pending ?? 0,
    expired: s.expired ?? 0,
    totalR: s.total_r ?? 0,
    avgR: resolved ? s.avg_r : null,
  };
}

// Results card: scanner signals from strategies that passed (shown) and practice ones, kept apart,
// plus the paper account's closed trades.
export function resultsCard(scan, metrics) {
  const tr = scan?.track_record;
  let paper = null;
  if (metrics) {
    const closed = metrics.closed_trades ?? 0;
    const wins = closed && metrics.win_rate != null ? Math.round((metrics.win_rate / 100) * closed) : 0;
    paper = { closed, wins, losses: closed - wins, totalR: metrics.total_r ?? 0,
              avgR: closed ? metrics.expectancy_r ?? null : null, pnlUsd: metrics.pnl_usd ?? 0 };
  }
  return { qualified: resultRow(tr?.shown), practice: resultRow(tr?.practice), paper, note: tr?.note ?? null,
           tom: tomRow(scan?.turn_of_month) };
}

// Volatility now (backend app/core/volatility.py): last hour's range vs the same New York hour on earlier days.
// Size only, never direction; no rule uses it.
const VOL_NAMES = { nas100: "NAS100", gold: "Gold", btc: "BTC" };
export const VOL_ORDER = ["nas100", "gold", "btc"];

export function volatilityCard(scan) {
  const v = scan?.volatility;
  if (!v || !Array.isArray(v.markets)) return { known: false, rows: [] };
  const byKey = Object.fromEntries(v.markets.map((m) => [m.market, m]));
  const rows = VOL_ORDER.map((k) => {
    const m = byKey[k];
    if (!m) return { key: k, name: VOL_NAMES[k], ok: false, text: "No data." };
    if (m.state !== "ok" || m.x == null) {
      const text = m.state === "not enough history" ? "Not enough history yet (needs 10 earlier days)."
        : "No recent prices (engine off, MT5 closed, or market closed).";
      return { key: k, name: VOL_NAMES[k], ok: false, text };
    }
    return { key: k, name: VOL_NAMES[k], ok: true, x: m.x, level: m.level, rangePct: m.range_pct,
             normalPct: m.normal_pct, asOf: m.as_of };
  });
  return { known: true, rows };
}

// Turn-of-month paper forward test (backend app/core/tom_forward.py). Never a verdict before 36 trades.
export function tomRow(t) {
  if (!t || !t.summary) return null;
  const done = (t.trades ?? []).filter((x) => x.counted && x.status === "done");
  return {
    trades: t.summary.trades, needed: t.summary.verdict_after, wins: t.summary.wins, losses: t.summary.losses,
    totalPct: t.summary.total_net_pct, verdict: t.summary.verdict, void: t.summary.void,
    last: done.length ? done[done.length - 1] : null, next: t.next ?? null,
  };
}
