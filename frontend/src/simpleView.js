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
  return { qualified: resultRow(tr?.shown), practice: resultRow(tr?.practice), paper, note: tr?.note ?? null };
}
