import { num, nyTime } from "../api.js";

const ACTION_STYLE = {
  LONG: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40",
  SHORT: "bg-red-500/15 text-red-300 ring-red-500/40",
  WAIT: "bg-slate-700/40 text-slate-300 ring-slate-600",
};

function Row({ k, v }) {
  return (
    <div className="flex justify-between border-b border-slate-800 py-1 text-sm">
      <span className="text-slate-400">{k}</span>
      <span className="font-mono">{v}</span>
    </div>
  );
}

export default function SignalPanel({ signal, market, ov, strategy }) {
  const action = signal?.action ?? "WAIT";
  const rr = signal?.entry != null && signal?.stop != null && signal?.target != null
    ? Math.abs(signal.target - signal.entry) / Math.abs(signal.entry - signal.stop) : null;

  return (
    <div className="flex flex-col gap-3">
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="label">Latest signal · {strategy ?? ov?.active_strategy}</div>
          <span className={`rounded-md px-3 py-1 text-sm font-bold ring-1 ${ACTION_STYLE[action]}`}>{action}</span>
        </div>
        {signal ? (
          <div className="mt-3">
            <Row k="5m bar closed" v={`${nyTime(signal.bar_close_ts)} NY`} />
            {action !== "WAIT" && (
              <>
                <Row k={`Entry (${signal.kind})`} v={num(signal.entry)} />
                <Row k="Stop-loss" v={num(signal.stop)} />
                <Row k="Take-profit" v={num(signal.target)} />
                <Row k="Reward : risk" v={rr ? `${rr.toFixed(2)} : 1` : "-"} />
                <Row k="Expires" v={`${nyTime(signal.expiry_ts)} NY`} />
              </>
            )}
            <p className="mt-2 text-sm text-slate-300">{signal.reason}</p>
            {signal.risk_approved != null && (
              <div className={`mt-3 rounded-lg p-2 text-sm ${signal.risk_approved ? "bg-emerald-500/10 text-emerald-200" : "bg-red-500/10 text-red-200"}`}>
                <div className="font-semibold">Risk Manager: {signal.risk_approved ? "APPROVED" : "REJECTED"}</div>
                <ul className="mt-1 list-disc pl-5">
                  {signal.risk_reasons.map((r) => <li key={r}>{r}</li>)}
                </ul>
              </div>
            )}
            <div className="mt-2 text-xs text-slate-500">
              Source {signal.data_source} · data up to {nyTime(signal.data_ts)} NY
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-400">
            {!ov?.engine_enabled
              ? "No signals recorded yet. Start the engine with ENGINE_ENABLED=true."
              : strategy?.startsWith("btc_")
                ? "No BTC signals yet: the BTC book only trades on weekends (Fri 17:00 - Sun 17:00 NY)."
                : "No signals yet for this strategy: NAS100 trades weekdays (entries in the strategy's session window)."}
          </p>
        )}
      </div>

      <div className="card">
        <div className="label mb-2">Market analysis</div>
        {market?.available ? (
          <>
            <Row k="Last price" v={num(market.last_price)} />
            <Row k="15m trend bias" v={market.bias_15m} />
            <Row k="ATR (5m)" v={`${num(market.atr_5m, 1)} pts`} />
            {Object.entries(market.levels).map(([k, v]) => <Row key={k} k={k} v={num(v)} />)}
            <div className="label mb-1 mt-3">Recent Fair Value Gaps</div>
            <div className="max-h-36 overflow-y-auto text-xs">
              {market.fvgs.length === 0 && <div className="text-slate-500">none in view</div>}
              {[...market.fvgs].reverse().map((g) => (
                <div key={`${g.time}-${g.side}`} className={g.side === "bullish" ? "text-emerald-300" : "text-red-300"}>
                  {nyTime(g.end_time)} {g.side} {num(g.low)} – {num(g.high)}
                </div>
              ))}
            </div>
            <div className="mt-2 text-xs text-slate-500">PDH/PDL = prior day high/low · ONH/ONL = overnight high/low</div>
          </>
        ) : (
          <p className="text-sm text-slate-400">No data.</p>
        )}
      </div>
    </div>
  );
}
