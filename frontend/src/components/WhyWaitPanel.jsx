import { CATEGORIES, whyWait } from "../whyWait.js";

// "Why WAIT?" — one plain-English list of everything that is stopping a signal or a paper trade right now.
// It explains the backend's decisions; it never creates a signal.
const STYLE = {
  data: "bg-red-500/15 text-red-200 ring-red-500/30",
  closed: "bg-slate-700/40 text-slate-300 ring-slate-600/40",
  unproven: "bg-amber-500/15 text-amber-200 ring-amber-500/30",
  news: "bg-fuchsia-500/15 text-fuchsia-200 ring-fuchsia-500/30",
  cost: "bg-orange-500/15 text-orange-200 ring-orange-500/30",
  risk: "bg-sky-500/15 text-sky-200 ring-sky-500/30",
  setup: "bg-slate-700/40 text-slate-300 ring-slate-600/40",
};
const STATE_TEXT = { WAIT: "WAIT", SIGNAL: "SIGNAL", UNKNOWN: "UNKNOWN" };

export default function WhyWaitPanel({ scan, ov, signals, backendDown }) {
  const r = whyWait({ scan: backendDown ? null : scan, ov: backendDown ? null : ov, signals, now: Date.now() / 1000 });
  return (
    <div className="card">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <div className="label">Why WAIT? · everything blocking a signal or a paper trade right now</div>
          <div className="mt-1 flex flex-wrap items-baseline gap-3">
            <span className={`text-2xl font-bold ${r.state === "SIGNAL" ? "text-sky-200" : "text-slate-200"}`}>{STATE_TEXT[r.state]}</span>
            <span className="text-sm text-slate-300">{r.headline}</span>
          </div>
        </div>
        <div className="text-xs text-slate-400">{r.reasons.length} reason(s)</div>
      </div>
      {r.reasons.length > 0 && (
        <ul className="mt-3 grid gap-2 md:grid-cols-2">
          {r.reasons.map((x, i) => (
            <li key={`${x.category}-${i}`} className="rounded-md bg-slate-800/50 p-2 text-sm ring-1 ring-slate-700/60">
              <span className={`mr-2 inline-block rounded px-1.5 py-0.5 text-[11px] font-semibold ring-1 ${STYLE[x.category]}`}>
                {CATEGORIES[x.category].label}
              </span>
              <span className="font-medium text-slate-100">{x.title}</span>
              {x.detail && <div className="mt-1 text-xs text-slate-400">{x.detail}</div>}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-500">
        WAIT is the normal, safe answer. A signal would only appear from a strategy that passed its pre-registered test,
        and even then it is not a chance of winning.
      </p>
    </div>
  );
}
