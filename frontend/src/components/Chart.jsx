import { useEffect, useRef, useState } from "react";
import { createChart, LineStyle } from "lightweight-charts";

// Show chart times in New York time (the strategy's clock).
const nyTick = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false });
const nyFull = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false });
const nyQuote = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
const nyDay = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "short", day: "2-digit" });
const nyClock = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
// The viewer's own clock (Cambodia for the owner), so chart times can be matched to local time.
const localClock = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
const localShort = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
const localZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
// lightweight-charts tick types 0-2 = year / month / day boundary: show the date there, the time elsewhere.
const tickLabel = (t, type) => (type <= 2 ? nyDay : nyTick).format(new Date(t * 1000));
const MAX_PREVIEW_AGE_SECONDS = 15;

const LEVEL_COLORS = { PDH: "#f87171", PDL: "#34d399", ONH: "#fb923c", ONL: "#2dd4bf" };

export default function Chart({ market, preview, previewError, marketError, view }) {
  const box = useRef(null);
  const chart = useRef(null);
  const series = useRef({});
  const historyKey = useRef(null);
  const lastClosedTime = useRef(null);
  const lastPreviewKey = useRef(null);
  const [nowMs, setNowMs] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Create the chart once.
  useEffect(() => {
    const c = createChart(box.current, {
      autoSize: true,
      layout: { background: { color: "#0f172a" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
      timeScale: { timeVisible: true, tickMarkFormatter: tickLabel },
      localization: {
        timeFormatter: (t) => `${nyFull.format(new Date(t * 1000))} NY · ${localShort.format(new Date(t * 1000))} local`,
      },
    });
    series.current = {
      candles: c.addCandlestickSeries({ upColor: "#10b981", downColor: "#ef4444", borderVisible: false, wickUpColor: "#10b981", wickDownColor: "#ef4444" }),
      ema20: c.addLineSeries({ color: "#38bdf8", lineWidth: 1, title: "EMA20 (15m)", priceLineVisible: false }),
      ema50: c.addLineSeries({ color: "#a78bfa", lineWidth: 1, title: "EMA50 (15m)", priceLineVisible: false }),
      vwap: c.addLineSeries({ color: "#facc15", lineWidth: 1, lineStyle: LineStyle.Dotted, title: "VWAP", priceLineVisible: false }),
    };
    series.current.lines = [];
    chart.current = c;
    return () => { c.remove(); chart.current = null; series.current = {}; };
  }, []);

  // A market switch must never leave the previous market's candles on screen.
  useEffect(() => {
    const s = series.current;
    if (!s.candles) return;
    s.candles.setData([]);
    s.ema20.setData([]);
    s.ema50.setData([]);
    s.vwap.setData([]);
    s.lines.forEach((line) => s.candles.removePriceLine(line));
    s.lines = [];
    s.candles.setMarkers([]);
    historyKey.current = null;
    lastClosedTime.current = null;
    lastPreviewKey.current = null;
  }, [view]);

  // Replace history only when completed candles, indicators or levels actually change.
  useEffect(() => {
    if (!market?.available || market.view !== view || !chart.current) return;
    const key = JSON.stringify([view, market.candles, market.ema20_15, market.ema50_15,
      market.vwap, market.levels, market.fvgs]);
    if (key === historyKey.current) return;
    const s = series.current;
    s.candles.setData(market.candles);
    s.ema20.setData(market.ema20_15);
    s.ema50.setData(market.ema50_15);
    s.vwap.setData(market.vwap);

    s.lines.forEach((l) => s.candles.removePriceLine(l));
    s.lines = Object.entries(market.levels ?? {})
      .filter(([, v]) => v != null)
      .map(([k, v]) => s.candles.createPriceLine({ price: v, color: LEVEL_COLORS[k], lineWidth: 1, lineStyle: LineStyle.Dashed, title: k }));

    s.candles.setMarkers(
      (market.fvgs ?? []).map((g) => ({
        time: g.end_time,
        position: g.side === "bullish" ? "belowBar" : "aboveBar",
        color: g.side === "bullish" ? "#10b981" : "#ef4444",
        shape: g.side === "bullish" ? "arrowUp" : "arrowDown",
        text: "FVG",
      }))
    );
    historyKey.current = key;
    lastClosedTime.current = market.candles.at(-1)?.time ?? null;
    lastPreviewKey.current = null;
  }, [market, view]);

  // Display-only quote: the engine still trades from completed bars, never this candle.
  const previewAge = preview?.observed_ts == null ? null : Math.max(0, Math.floor(nowMs / 1000 - preview.observed_ts));
  const previewCurrent = preview?.view === view && preview?.available && !preview.stale && !previewError
    && previewAge != null && previewAge <= MAX_PREVIEW_AGE_SECONDS;
  useEffect(() => {
    if (!previewCurrent || !market?.available || market.view !== view || !series.current.candles) return;
    const candle = preview.candle;
    if (!candle || (lastClosedTime.current != null && candle.time < lastClosedTime.current)) return;
    const key = JSON.stringify([preview.observed_ts, candle]);
    if (key === lastPreviewKey.current) return;
    series.current.candles.update(candle);
    lastPreviewKey.current = key;
  }, [market, preview, previewCurrent, view]);

  const quoteStatus = previewError ? "QUOTE OFFLINE"
    : previewCurrent ? `LIVE QUOTE · ${previewAge}s old`
      : preview?.view === view && preview?.available ? "QUOTE STALE" : "CLOSED CANDLES ONLY";

  const now = new Date(nowMs);
  const nextClose = 300 - (Math.floor(nowMs / 1000) % 300);   // seconds until the 5m candle closes
  const lastClosed = market?.view === view ? market?.last_bar_ts : null;

  return (
    <div className="card relative h-[360px] p-2 sm:h-[460px]">
      <div ref={box} className="h-full w-full" />
      {/* Overlays sit above the chart canvas (z-10) and let mouse events through to the crosshair. */}
      <div className="pointer-events-none absolute left-3 top-3 z-10 flex max-w-[calc(100%-6rem)] flex-col items-start gap-1 text-[11px] sm:left-4 sm:top-4 sm:text-xs">
        <div className="rounded bg-slate-950/85 px-2 py-1 font-mono text-slate-200 ring-1 ring-slate-700"
          title="Chart axis and strategy rules use New York time">
          <span className="text-sky-300">NY</span> {nyClock.format(now)}
          <br className="sm:hidden" />
          <span className="mx-1 hidden text-slate-600 sm:inline">|</span>
          <span className="text-emerald-300">Local</span> {localClock.format(now)}
          <span className="ml-1 hidden text-slate-500 sm:inline">({localZone})</span>
        </div>
        <div className="rounded bg-slate-950/85 px-2 py-1 text-slate-300 ring-1 ring-slate-700">
          Next 5m close in {Math.floor(nextClose / 60)}:{String(nextClose % 60).padStart(2, "0")}
          {lastClosed && <span className="hidden sm:inline"> · last closed bar {nyTick.format(new Date(lastClosed * 1000))} NY</span>}
        </div>
        <div className={`rounded px-2 py-1 font-semibold ring-1 ${
          previewCurrent ? "bg-sky-950/90 text-sky-200 ring-sky-500/40" : "bg-slate-900/90 text-amber-200 ring-amber-500/40"
        }`} title="Quote preview is display-only. Trading signals use completed candles.">
          {quoteStatus}
          {previewCurrent && <span className="hidden sm:inline"> · {nyQuote.format(new Date(preview.observed_ts * 1000))} NY</span>}
        </div>
      </div>
      {marketError && market?.available && (
        <div className="absolute bottom-10 left-4 z-10 rounded bg-amber-950/90 px-2 py-1 text-xs text-amber-200 ring-1 ring-amber-500/40">
          Chart history offline · showing last received candles
        </div>
      )}
      {!market?.available && (
        <div className="absolute inset-0 z-10 flex items-center justify-center text-slate-400">
          {marketError ? "Chart history unavailable." : market?.message ?? "Loading market data..."}
        </div>
      )}
    </div>
  );
}
