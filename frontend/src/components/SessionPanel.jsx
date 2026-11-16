import { useEffect, useMemo, useState } from "react";
import { isScanFresh, nextWindow, sessionState } from "../sessions.js";

const sessions = [
  { key: "asia", name: "Asia", schedule: "18:00 New York → 08:00 London", detail: "Reference range only. Highs and lows inform London sweep setups; no Asian entry strategy." },
  { key: "london", name: "London", schedule: "08:05–10:00 London", detail: "Liquidity sweep from 08:05; trend + FVG from 08:15. Both stop taking entries at 10:00." },
  { key: "ny", name: "New York", schedule: "09:35–15:00 New York", detail: "Sweep 09:35–11:30 · trend 09:45–11:30 · breakout 09:50–11:30 · Silver Bullet 10:05–11:00 · VWAP 10:00–15:00." },
];
const localDate = new Intl.DateTimeFormat(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit", timeZoneName: "short" });

export default function SessionPanel({ scan, backendDown, view }) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);
  const state = sessionState(now);
  const next = useMemo(() => Object.fromEntries(sessions.map(s => [s.key,
    state[s.key] ? null : nextWindow(now, s.key)])), [now]);
  const fresh = !backendDown && isScanFresh(scan?.scanned_ts, Date.now() / 1000);
  return <section className="card" aria-label="Trading session schedule">
    <div className="flex flex-wrap justify-between gap-2">
      <div><h2 className="font-semibold text-slate-100">Trading sessions</h2>
        <p className="mt-1 text-xs text-slate-400">NAS100 & gold strategy schedule · daylight saving adjusts automatically · holidays and feed availability may affect scanning</p></div>
      <div className="text-xs text-slate-400">London {state.londonClock} · New York {state.nyClock}</div>
    </div>
    <div className="mt-3 grid gap-3 md:grid-cols-3">
      {sessions.map(s => <article key={s.key} className="rounded-lg border border-slate-700 bg-slate-900/40 p-3">
        <div className="flex items-center justify-between gap-2"><h3 className="font-semibold">{s.name}</h3>
          <span className={`rounded px-2 py-1 text-xs ${state[s.key] ? "bg-sky-500/15 text-sky-200" : "bg-slate-800 text-slate-400"}`}>
            {state[s.key] ? s.key === "asia" ? "Range window" : "Entry window" : "Outside window"}
          </span></div>
        <p className="mt-2 text-sm text-slate-200">{s.schedule}</p>
        <p className="mt-2 text-xs leading-relaxed text-slate-400">{s.detail}</p>
        {next[s.key] && <p className="mt-3 text-xs text-sky-200">Next: {localDate.format(next[s.key])} (your time)</p>}
      </article>)}
    </div>
    <p className="mt-3 text-xs text-slate-400">
      {fresh ? "Scanner updates are current." : "Scanner freshness unconfirmed; schedule is based on your device clock."}
      {" "}A scheduled window does not mean a signal is available. See the scanner below for eligibility and feed status.
      {view === "btc" && " BTC uses separate weekend strategies; these session windows do not control BTC entries."}
    </p>
  </section>;
}
