import { useState } from "react";
import { nyTime, postJSON } from "../api.js";

const STRATEGIES = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet",
  "london_trend_fvg", "london_sweep_mss_fvg", "btc_weekend_trend_fvg"];

export default function Header({ ov, market, refresh, setError, view, book, setBook, bookInfo }) {
  const [busy, setBusy] = useState(false);

  const act = async (fn) => {
    setBusy(true);
    try {
      await fn();
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      refresh();
    }
  };

  const kill = () => {
    if (window.confirm("KILL SWITCH: cancel all orders, close all positions and turn auto-trading OFF?")) {
      act(() => postJSON("/api/controls/kill"));
    }
  };

  const stale = !market?.available || market?.stale;

  return (
    <header className="flex flex-wrap items-center gap-3 border-b border-slate-800 bg-slate-900/80 px-4 py-3">
      <h1 className="mr-2 text-lg font-semibold">LITTLE</h1>

      <span className="rounded-md bg-emerald-600/20 px-2 py-1 text-xs font-bold text-emerald-300 ring-1 ring-emerald-500/40">
        PAPER TRADING
      </span>
      <span
        title="Live trading does not exist in this version"
        className="cursor-not-allowed rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-500 ring-1 ring-slate-700"
      >
        🔒 LIVE: not available in V1
      </span>

      <span
        className={`rounded-md px-2 py-1 text-xs ring-1 ${
          stale ? "bg-amber-500/15 text-amber-300 ring-amber-500/40" : "bg-sky-500/15 text-sky-300 ring-sky-500/40"
        }`}
        title="Where the prices come from"
      >
        Data: {bookInfo?.source ?? ov?.data_source ?? "-"} {bookInfo?.symbol ?? ""} · last bar {nyTime(market?.last_bar_ts)} NY
        {stale ? " · STALE / market closed" : " · live"}
      </span>

      <span className={`text-xs ${ov?.engine_enabled ? "text-sky-300" : "text-slate-500"}`}>
        Engine: {ov?.engine_enabled ? "running" : "off (set ENGINE_ENABLED=true)"}
      </span>

      <span
        className={`rounded-md px-2 py-1 text-xs font-semibold ring-1 ${
          ov?.trading_now ? "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40" : "bg-slate-800 text-slate-400 ring-slate-700"
        }`}
        title="NAS100 trades weekdays 03:00-15:55 NY; BTC trades weekends Fri 17:00 - Sun 17:00 NY"
      >
        Trading now: {ov?.trading_now === "btc" ? "BTC (weekend)" : ov?.trading_now === "nas100" ? "NAS100" : "nothing (both closed)"}
      </span>

      {ov?.news && (
        <span
          className={`rounded-md px-2 py-1 text-xs ring-1 ${
            ov.news.blackout_now || !ov.news.calendar_covers_now
              ? "bg-red-600/20 font-semibold text-red-200 ring-red-500/50"
              : "bg-slate-800 text-slate-300 ring-slate-700"
          }`}
          title={`High-impact US news (${ov.news.events_included.join(", ")}): no new entries ±30 min. Official sources: BLS, Federal Reserve. Calendar valid until ${ov.news.calendar_until}.`}
        >
          {!ov.news.calendar_covers_now
            ? "NEWS CALENDAR MISSING: no trading"
            : ov.news.blackout_now
              ? `NEWS BLACKOUT: ${ov.news.blackout_now}`
              : ov.news.upcoming.length
                ? `Next news: ${ov.news.upcoming[0].label}`
                : "No high-impact news in the next 7 days"}
        </span>
      )}

      <div className="flex overflow-hidden rounded-md ring-1 ring-slate-700" role="group" aria-label="Which market to show">
        {(ov?.markets ?? [{ key: "nas100", label: "NAS100" }, { key: "btc", label: "BTC" }]).map((m) => (
          <button
            key={m.key}
            className={`px-2 py-1 text-xs ${view === m.key ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-300"}`}
            onClick={() => setBook(book === m.key ? null : m.key)}
            title={m.open_now ? "trading window open now" : "outside its trading window"}
          >
            {m.key === "btc" ? "BTC" : "NAS100"}{m.open_now ? " ●" : ""}
          </button>
        ))}
      </div>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1 text-sm">
          <span className="label">Strategy</span>
          <select
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-sm"
            value={bookInfo?.active_strategy ?? ov?.active_strategy ?? ""}
            disabled={busy || !ov}
            onChange={(e) => act(() => postJSON("/api/controls/strategy", { name: e.target.value }))}
          >
            {STRATEGIES.filter((s) => s.startsWith("btc_") === (view === "btc")).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <button
          className={`btn ${ov?.auto_trading ? "bg-sky-600 text-white" : "bg-slate-700 text-slate-200"}`}
          disabled={busy || !ov || ov.kill_switch}
          onClick={() => act(() => postJSON("/api/controls/auto-trading", { enabled: !ov.auto_trading }))}
          title={ov?.kill_switch ? "Reset the kill switch first" : "Auto-trading can never bypass the Risk Manager"}
        >
          Auto-trading: {ov?.auto_trading ? "ON" : "OFF"}
        </button>

        {ov?.kill_switch ? (
          <button className="btn bg-amber-600 text-white" disabled={busy}
            onClick={() => act(() => postJSON("/api/controls/reset-kill"))}>
            Reset kill switch
          </button>
        ) : (
          <button className="btn bg-red-600 font-bold text-white hover:bg-red-500" disabled={busy || !ov} onClick={kill}>
            ■ KILL SWITCH
          </button>
        )}
      </div>
    </header>
  );
}
