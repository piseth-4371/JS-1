import { money, num, nyTime } from "../api.js";
import { newsCard, resultsCard, signalCard } from "../simpleView.js";
import { strategyLabel } from "../strategies.js";
import Chart from "./Chart.jsx";

// The Simple view: four cards answering "should I enter?", "is there news?", "why?" and "how has it gone?".
// It only shows what the backend decided. A trade to enter appears only for a strategy that passed its test.
const STATE_STYLE = {
  SIGNAL: "bg-sky-500/15 text-sky-200 ring-sky-500/40",
  WAIT: "bg-slate-700/40 text-slate-200 ring-slate-600",
  UNKNOWN: "bg-red-500/15 text-red-200 ring-red-500/40",
};
const SIDE_STYLE = { LONG: "text-emerald-300", SHORT: "text-red-300" };

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-3 border-b border-slate-800 py-1 text-sm">
      <span className="text-slate-400">{k}</span>
      <span className="font-mono text-right">{v}</span>
    </div>
  );
}

const fmtR = (x) => (x == null ? "—" : `${x >= 0 ? "+" : ""}${Number(x).toFixed(2)}R`);

function SignalCard({ c }) {
  const s = c.signal;
  const label = s ? s.side : c.state;
  return (
    <div className="card">
      <div className="label">1 · Signal</div>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <span className={`rounded-lg px-4 py-2 text-3xl font-bold ring-1 ${s ? STATE_STYLE.SIGNAL : STATE_STYLE[c.state]}`}>
          <span className={s ? SIDE_STYLE[s.side] : ""}>{label}</span>
        </span>
        {s && <span className="text-sm text-slate-300">{s.market.toUpperCase()} · {strategyLabel(s.strategy)}</span>}
      </div>
      {s ? (
        <div className="mt-3">
          <Row k={`Entry (${s.kind})`} v={num(s.entry)} />
          <Row k="Stop-loss" v={num(s.stop)} />
          <Row k="Take-profit" v={num(s.target)} />
          <Row k="Reward : risk" v={s.rr_target ? `${num(s.rr_target, 1)} : 1` : "-"} />
          <Row k="Expires" v={`${nyTime(s.expiry_ts)} NY`} />
          <p className="mt-2 text-xs text-slate-400">Paper trading only. Not a chance of winning; past tests can fail in the future.</p>
        </div>
      ) : (
        <div className="mt-3 text-sm">
          <div className="font-medium text-slate-100">{c.mainReason?.title ?? c.headline}</div>
          {c.mainReason?.detail && <div className="mt-1 text-xs text-slate-400">{c.mainReason.detail}</div>}
          <p className="mt-2 text-xs text-slate-500">Do not enter a trade. WAIT is the normal, safe answer.</p>
        </div>
      )}
      {c.practice.length > 0 && (
        <div className="mt-3 rounded-md bg-amber-500/10 p-2 ring-1 ring-amber-500/30">
          <div className="text-xs font-semibold text-amber-200">
            Practice only — this strategy failed its test. Not a trade to enter.
          </div>
          <ul className="mt-1 space-y-1 text-xs text-amber-100/80">
            {c.practice.map((p, i) => (
              <li key={`${p.market}-${p.strategy}-${i}`}>
                {p.marketLabel} · {strategyLabel(p.strategy)} · {p.side} at {num(p.entry)} (stop {num(p.stop)}, target {num(p.target)})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function NewsCard({ n }) {
  return (
    <div className="card">
      <div className="label">2 · News</div>
      {!n.known ? (
        <p className="mt-2 text-sm text-slate-400">News status unknown (no data from the backend).</p>
      ) : (
        <>
          <div className={`mt-2 rounded-md p-2 text-sm ring-1 ${n.blackout
            ? "bg-fuchsia-500/15 text-fuchsia-200 ring-fuchsia-500/30"
            : n.covered ? "bg-slate-800/50 text-slate-200 ring-slate-700" : "bg-red-500/15 text-red-200 ring-red-500/30"}`}>
            {n.blackout ? `News blackout now: ${n.blackout}. No new entries.`
              : n.covered ? "No news blackout right now."
                : "The news calendar does not cover today, so entries are blocked."}
          </div>
          <div className="label mb-1 mt-3">Next high-impact events</div>
          {n.upcoming.length === 0 ? (
            <div className="text-sm text-slate-500">None listed.</div>
          ) : (
            n.upcoming.map((e) => (
              <Row key={`${e.label}-${e.ts}`} k={e.label} v={`${nyTime(e.ts)} NY`} />
            ))
          )}
          {n.until && <div className="mt-2 text-xs text-slate-500">Calendar loaded up to {n.until}.</div>}
        </>
      )}
    </div>
  );
}

function AnalysisCard({ c, market, preview, previewError, marketError, view }) {
  const why = c.signal?.reason ?? (c.practice[0] ? `Practice setup: ${c.practice[0].reason}` : c.headline);
  const levels = market?.available ? Object.entries(market.levels ?? {}) : [];
  const fvgs = market?.available ? [...(market.fvgs ?? [])].reverse().slice(0, 3) : [];
  return (
    <div className="card">
      <div className="label mb-2">3 · Market analysis — why this signal</div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Chart market={market} preview={preview} previewError={previewError} marketError={marketError} view={view} />
        </div>
        <div>
          <p className="rounded-md bg-slate-800/50 p-2 text-sm text-slate-200 ring-1 ring-slate-700">{why}</p>
          {market?.available ? (
            <div className="mt-3">
              <Row k="Last price" v={num(market.last_price)} />
              <Row k="15m trend" v={market.bias_15m} />
              <Row k="Typical 5m move (ATR)" v={market.unit === "$" ? `$${num(market.atr_5m, 1)}` : `${num(market.atr_5m, 1)} pts`} />
              {levels.map(([k, v]) => <Row key={k} k={k} v={num(v)} />)}
              <div className="label mb-1 mt-3">Latest fair value gaps</div>
              {fvgs.length === 0 && <div className="text-xs text-slate-500">none in view</div>}
              {fvgs.map((g) => (
                <div key={`${g.time}-${g.side}`} className={`text-xs ${g.side === "bullish" ? "text-emerald-300" : "text-red-300"}`}>
                  {nyTime(g.end_time)} {g.side} {num(g.low)} – {num(g.high)}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-400">{market ? market.message ?? "No data." : "Loading…"}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultLine({ title, r, tone }) {
  return (
    <div className={`rounded-md p-2 ring-1 ${tone}`}>
      <div className="text-xs font-semibold">{title}</div>
      {r ? (
        <div className="mt-1 grid grid-cols-2 gap-x-3 text-sm sm:grid-cols-5">
          <span>Signals <b className="font-mono">{r.signals}</b></span>
          <span>Wins <b className="font-mono text-emerald-300">{r.wins}</b></span>
          <span>Losses <b className="font-mono text-red-300">{r.losses}</b></span>
          <span>Total <b className="font-mono">{fmtR(r.totalR)}</b></span>
          <span>Average <b className="font-mono">{fmtR(r.avgR)}</b></span>
        </div>
      ) : <div className="mt-1 text-sm text-slate-400">No data.</div>}
    </div>
  );
}

function ResultsCard({ r }) {
  return (
    <div className="card">
      <div className="label mb-2">4 · Results summary</div>
      <div className="flex flex-col gap-2">
        <ResultLine title="Signals from strategies that passed their test" r={r.qualified}
          tone="bg-sky-500/10 text-sky-100 ring-sky-500/30" />
        <ResultLine title="Practice setups (strategies that failed their test)" r={r.practice}
          tone="bg-amber-500/10 text-amber-100 ring-amber-500/30" />
        <div className="rounded-md bg-slate-800/50 p-2 ring-1 ring-slate-700">
          <div className="text-xs font-semibold text-slate-200">Paper account (closed trades)</div>
          {r.paper ? (
            <div className="mt-1 grid grid-cols-2 gap-x-3 text-sm text-slate-200 sm:grid-cols-5">
              <span>Trades <b className="font-mono">{r.paper.closed}</b></span>
              <span>Wins <b className="font-mono text-emerald-300">{r.paper.wins}</b></span>
              <span>Losses <b className="font-mono text-red-300">{r.paper.losses}</b></span>
              <span>Total <b className="font-mono">{fmtR(r.paper.totalR)}</b></span>
              <span>P/L <b className="font-mono">{money(r.paper.pnlUsd)}</b></span>
            </div>
          ) : <div className="mt-1 text-sm text-slate-400">No data.</div>}
        </div>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        R = result in units of the risk taken (+1R won what was risked, −1R lost it). Simulated with assumed costs; history, not a promise.
      </p>
    </div>
  );
}

export default function SimpleView({ scan, ov, signals, metrics, backendDown, market, preview, previewError, marketError, view }) {
  const now = Date.now() / 1000;
  const live = backendDown ? null : scan;
  const c = signalCard({ scan: live, ov: backendDown ? null : ov, signals, now });
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <SignalCard c={c} />
        <NewsCard n={newsCard(backendDown ? null : ov, now)} />
      </div>
      <AnalysisCard c={c} market={market} preview={preview} previewError={previewError} marketError={marketError} view={view} />
      <ResultsCard r={resultsCard(live, metrics)} />
    </div>
  );
}
