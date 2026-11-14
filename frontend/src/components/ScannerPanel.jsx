import { useEffect, useState } from "react";
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
  const [now, setNow] = useState(() => Date.now() / 1000);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(timer);
  }, []);
  if (!scan) return <div className="card text-sm text-slate-400">Scanner: loading…</div>;
  const freshSignal = scan.signal && now < scan.signal.expiry_ts
    && now - (scan.scanned_ts ?? 0) <= 60;
  const practice = (scan.markets ?? []).flatMap((m) => m.setups.filter((s) => !s.eligible));
  const tr = scan.track_record ?? {};
  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="label">3-market scanner · signals only (no orders)</div>
          {freshSignal ? (
            <div className="mt-1 text-lg font-semibold text-sky-200">
              {MARKET_NAME[scan.signal.market]} · {strategyLabel(scan.signal.strategy)} · <Levels s={scan.signal} />
            </div>
          ) : (
            <div className="mt-1 text-2xl font-bold text-slate-200">WAIT</div>
          )}
          <div className="mt-1 max-w-3xl text-sm text-slate-300">{scan.signal && !freshSignal ? "WAIT: signal expired or scanner updates stopped." : scan.note}</div>
          {freshSignal && (
            <div className="mt-1 text-xs text-slate-400">
              Expires {nyTime(scan.signal.expiry_ts)} NY · cost {(scan.signal.cost_share * 100).toFixed(0)}% of risk ·
              {scan.signal.cost_basis} · ranking uses past validation results and is NOT a chance of winning.
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
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <caption className="pb-2 text-left text-slate-300">Forward simulation · completed trades only</caption>
          <thead className="text-slate-400"><tr>
            <th className="p-2">Market / group</th><th className="p-2">Completed</th>
            <th className="p-2">Win rate / 95% range</th><th className="p-2">Avg net R / 95% range</th>
            <th className="p-2">Pending / expired / invalid</th>
          </tr></thead>
          <tbody>{(tr.by_market ?? []).flatMap((m) => ["shown", "practice"].map((group) => {
            const stats = m[group];
            const range = (value, unit = "") => value ? `${value[0]}–${value[1]}${unit}` : "—";
            return <tr key={`${m.market}-${group}`} className="border-t border-slate-700/50">
              <td className="p-2">{MARKET_NAME[m.market]} · {group === "shown" ? "qualified signals" : "practice only"}</td>
              <td className="p-2">{stats.resolved}</td>
              <td className="p-2">{stats.win_rate == null ? "—" : `${stats.win_rate}%`} / {range(stats.win_rate_95_range, "%")}</td>
              <td className="p-2">{stats.avg_r == null ? "—" : `${stats.avg_r}R`} / {range(stats.avg_r_95_range, "R")}</td>
              <td className="p-2">{stats.pending} / {stats.expired} / {stats.invalid}</td>
            </tr>;
          }))}</tbody>
        </table>
      </div>
      {tr.legacy_excluded > 0 && <p className="mt-2 text-xs text-amber-200">
        {tr.legacy_excluded} older records excluded: they used a different fill model.
      </p>}
      <details className="mt-3 text-xs text-slate-400">
        <summary className="cursor-pointer">Cost assumptions and observed spreads</summary>
        <div className="mt-2 grid gap-2 sm:grid-cols-3">{(scan.costs ?? []).map((c) => (
          <div key={c.market} className="rounded bg-slate-800/60 p-2">
            <div className="font-semibold text-slate-200">{MARKET_NAME[c.market]}</div>
            <div>Assumed spread: {c.assumptions.spread} points; round-trip fees: {c.assumptions.fee_pct}%.</div>
            <div>Assumed slippage per applicable leg: {c.assumptions.slippage} points + {c.assumptions.slip_pct}%.</div>
            {c.observation ? <>
              <div className="mt-1">Observed spread: {num(c.observation.median_spread, 4)} {c.observation.unit}
                {c.observation.p90_spread != null && ` · p90 ${num(c.observation.p90_spread, 4)}`}.</div>
              <div>{c.observation.sample_count} samples · {c.observation.kind}</div>
              <div>{c.observation.source} · collected {new Date(c.observation.observed_ts * 1000).toLocaleString()}</div>
              {c.observation.last_quote_ts && <div>Last bar {new Date(c.observation.last_quote_ts * 1000).toLocaleString()}</div>}
            </> : <div className="mt-1 text-amber-200">No spread observations collected.</div>}
            <div className="mt-1">{c.note}</div>
          </div>
        ))}</div>
      </details>
      {showPractice && (
        <ul className="mt-2 space-y-1 text-xs text-amber-200/90">
          {practice.map((s) => (
            <li key={`${s.market}-${s.strategy}-${s.bar_close_ts}`}>
              PRACTICE ONLY ({s.qualified ? "blocked by eligibility checks" : "this strategy failed its backtest"}):{" "}
              {MARKET_NAME[s.market]} · {strategyLabel(s.strategy)} · <Levels s={s} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
