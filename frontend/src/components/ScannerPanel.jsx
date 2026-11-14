import { useState } from "react";
import { num, nyTime } from "../api.js";
import { strategyLabel } from "../strategies.js";

// Signals-only scanner over NAS100, BTC and gold. It never places orders.
// A signal is shown ONLY from a strategy that passed its backtest on that market; otherwise WAIT.
const STATE_STYLE = {
  open: "bg-emerald-500/15 text-emerald-200 ring-emerald-500/30",
  closed: "bg-slate-700/40 text-slate-400 ring-slate-600/40",
  stale: "bg-amber-500/15 text-amber-200 ring-amber-500/30",
  "no data": "bg-red-500/15 text-red-200 ring-red-500/30",
};
const MARKET_NAME = { nas100: "NAS100", btc: "BTC", gold: "Gold" };
const digits = (m) => (m === "nas100" ? 1 : 2);

function Levels({ s }) {
  const d = digits(s.market);
  return (
    <span className="font-mono">
      {s.side} {s.kind} @ {num(s.entry, d)} · SL {num(s.stop, d)} · TP {s.target == null ? `${s.rr_target}R` : num(s.target, d)}
    </span>
  );
}

export default function ScannerPanel({ scan }) {
  const [showPractice, setShowPractice] = useState(false);
  if (!scan) return <div className="card text-sm text-slate-400">Scanner: loading…</div>;
  const practice = (scan.markets ?? []).flatMap((m) => m.setups.filter((s) => !s.eligible));
  const tr = scan.track_record ?? {};
  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="label">3-market scanner · signals only (no orders)</div>
          {scan.signal ? (
            <div className="mt-1 text-lg font-semibold text-sky-200">
              {MARKET_NAME[scan.signal.market]} · {strategyLabel(scan.signal.strategy)} · <Levels s={scan.signal} />
            </div>
          ) : (
            <div className="mt-1 text-2xl font-bold text-slate-200">WAIT</div>
          )}
          <div className="mt-1 max-w-3xl text-sm text-slate-300">{scan.note}</div>
          {scan.signal && (
            <div className="mt-1 text-xs text-slate-400">
              Expires {nyTime(scan.signal.expiry_ts)} NY · cost {(scan.signal.cost_share * 100).toFixed(0)}% of risk ·
              ranking uses past validation results and is NOT a chance of winning.
            </div>
          )}
        </div>
        <div className="text-right text-xs text-slate-400">
          Scanned {scan.scanned_ts ? `${nyTime(scan.scanned_ts)} NY` : "—"}
          <div>Qualified strategies: {scan.qualified_strategies?.length ? scan.qualified_strategies.length : "none"}</div>
        </div>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {(scan.markets ?? []).map((m) => (
          <div key={m.key} className={`rounded-md px-2 py-1.5 text-xs ring-1 ${STATE_STYLE[m.state] ?? STATE_STYLE.closed}`}>
            <div className="font-semibold">{m.label} · {m.state}</div>
            <div>{m.detail}</div>
            {m.last_bar_ts && <div className="text-slate-400">last bar {nyTime(m.last_bar_ts)} NY</div>}
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
        <span>
          Track record (shown signals): {tr.shown?.resolved ?? 0} resolved
          {tr.shown?.avg_r != null && ` · avg ${tr.shown.avg_r}R`} · practice setups: {tr.practice?.resolved ?? 0} resolved
          {tr.practice?.avg_r != null && ` · avg ${tr.practice.avg_r}R`}. {tr.note}
        </span>
        {practice.length > 0 && (
          <button className="rounded bg-slate-800 px-2 py-1 text-slate-300 ring-1 ring-slate-700"
            onClick={() => setShowPractice((x) => !x)}>
            {showPractice ? "Hide" : "Show"} {practice.length} practice setup(s)
          </button>
        )}
      </div>
      {showPractice && (
        <ul className="mt-2 space-y-1 text-xs text-amber-200/90">
          {practice.map((s) => (
            <li key={`${s.market}-${s.strategy}-${s.bar_close_ts}`}>
              PRACTICE ONLY ({s.qualified ? "blocked by news/cost check" : "this strategy failed its backtest"}):{" "}
              {MARKET_NAME[s.market]} · {strategyLabel(s.strategy)} · <Levels s={s} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
