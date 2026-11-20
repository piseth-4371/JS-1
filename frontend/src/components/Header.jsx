import { useState } from "react";
import { nyTime, postJSON } from "../api.js";

// Small status item for the second header row: coloured dot + text, tooltip explains it.
function Status({ tone = "muted", title, children }) {
  const dot = { ok: "bg-emerald-400", info: "bg-sky-400", warn: "bg-amber-400", bad: "bg-red-500", muted: "bg-slate-500" }[tone];
  const text = { ok: "text-slate-200", info: "text-slate-200", warn: "text-amber-200", bad: "font-semibold text-red-200", muted: "text-slate-400" }[tone];
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 ${text}`} title={title}>
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {children}
    </span>
  );
}

const MARKET_NAME = { nas100: "NAS100", btc: "BTC", gold: "Gold" };

export default function Header({ ov, market, preview, marketError, previewError, refresh, setError, view, bookInfo }) {
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

  // KILL is never delayed: one dialog, the reason is optional (Cancel = do nothing).
  const kill = () => {
    const reason = window.prompt(
      "KILL SWITCH: cancel all orders, close all positions and turn auto-trading OFF.\n\n"
      + "Why? (optional, saved in the log; leave empty and press OK to stop now)", "");
    if (reason !== null) act(() => postJSON("/api/controls/kill", { reason }));
  };

  // Reset needs a written reason and, after the first 2 minutes, waits for the next New York day (cooling-off).
  const resetKill = () => {
    const reason = window.prompt("Why are you resetting the kill switch? (at least 5 characters, saved in the log)", "");
    if (reason !== null) act(() => postJSON("/api/controls/reset-kill", { reason }));
  };
  const resetAfter = ov?.kill_reset_after ?? null;

  const shownMarket = market?.view === view ? market : null;
  const loadingMarket = !shownMarket && !marketError;
  const stale = !shownMarket?.available || shownMarket?.stale || !!marketError;
  const quoteStatus = previewError ? "offline"
    : preview?.view === view && preview?.available ? (preview.stale ? "stale" : "live (display only)") : "unavailable";
  const news = ov?.news;

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
      {/* Row 1: identity, what is watched, and the emergency stop */}
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-2 px-4 pt-3">
        <h1 className="text-lg font-semibold tracking-tight">LITTLE</h1>
        <span className="rounded-md bg-emerald-600/20 px-2 py-0.5 text-xs font-bold text-emerald-300 ring-1 ring-emerald-500/40"
          title="Simulated orders and fills only. Live trading does not exist in this version.">
          PAPER ONLY · live off
        </span>

        <span className="text-xs text-slate-400" title="The scanner checks NAS100, BTC and gold with every strategy by itself. Nothing to choose.">
          Auto: watching NAS100, BTC and gold · chart: <b className="text-slate-200">{MARKET_NAME[view] ?? view}</b>
        </span>

        <div className="ml-auto flex items-center gap-2">
          {ov?.kill_switch ? (
            resetAfter ? (
              <span className="rounded-md bg-slate-800 px-2 py-1 text-xs text-amber-200 ring-1 ring-amber-500/40"
                title="Cooling-off: a reset waits for the next New York day, so the decision is not made in the heat of the moment.">
                Kill switch ON · reset from {nyTime(resetAfter)} NY
              </span>
            ) : (
              <button className="btn bg-amber-600 text-white" disabled={busy} onClick={resetKill}
                title="Asks why. Allowed in the first 2 minutes (misclick) or from the next New York day.">
                Reset kill switch
              </button>
            )
          ) : (
            <button className="btn bg-red-600 font-bold text-white hover:bg-red-500" disabled={busy || !ov} onClick={kill}>
              ■ KILL
            </button>
          )}
        </div>
      </div>

      {/* Row 2: one compact status line (scrolls sideways on a phone instead of filling the screen) */}
      <div className="mx-auto flex max-w-[1600px] gap-4 overflow-x-auto whitespace-nowrap px-4 py-2 text-xs">
        <Status
          tone={loadingMarket ? "muted" : stale ? "warn" : "ok"}
          title="Where the prices come from and the last completed 1-minute bar"
        >
          {bookInfo ? `${bookInfo.source} ${bookInfo.symbol}` : MARKET_NAME[view] ?? view} ·{" "}
          {loadingMarket ? "loading…" : `last bar ${nyTime(shownMarket?.last_bar_ts)} NY${stale ? " · STALE / closed" : ""}`}
        </Status>

        <Status tone={!ov ? "muted" : ov.engine_enabled ? "ok" : "warn"} title="The engine checks every closed 5-minute bar">
          Engine {!ov ? "connecting…" : ov.engine_enabled ? "running" : "off (ENGINE_ENABLED=true)"}
        </Status>

        <Status tone={ov?.trading_now ? "ok" : "muted"}
          title="NAS100 holds positions weekdays 03:00-15:55 NY; BTC weekends Fri 17:00 - Sun 17:00 NY">
          Window: {!ov ? "…" : ov.trading_now === "btc" ? "BTC open" : ov.trading_now === "nas100" ? "NAS100 open" : "both closed"}
        </Status>

        {news && (
          <Status
            tone={news.blackout_now || !news.calendar_covers_now ? "bad" : news.upcoming.length ? "warn" : "muted"}
            title={`High-impact US news (${news.events_included.join(", ")}): no new entries ±30 min. Sources: BLS, Federal Reserve, BEA. Calendar valid until ${news.calendar_until}.`}
          >
            {!news.calendar_covers_now
              ? "NEWS CALENDAR MISSING: no trading"
              : news.blackout_now
                ? `NEWS BLACKOUT: ${news.blackout_now}`
                : news.upcoming.length
                  ? `Next news: ${news.upcoming[0].label}`
                  : "No high-impact news in 7 days"}
          </Status>
        )}

        <Status tone={quoteStatus.startsWith("live") ? "info" : "muted"}
          title="The live quote only updates the chart. Trading signals use completed candles.">
          Quote: {quoteStatus}
        </Status>
      </div>
    </header>
  );
}
