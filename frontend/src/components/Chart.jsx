import { useEffect, useRef } from "react";
import { createChart, LineStyle } from "lightweight-charts";

// Show chart times in New York time (the strategy's clock).
const nyTick = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false });
const nyFull = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false });

const LEVEL_COLORS = { PDH: "#f87171", PDL: "#34d399", ONH: "#fb923c", ONL: "#2dd4bf" };

export default function Chart({ market }) {
  const box = useRef(null);
  const chart = useRef(null);
  const series = useRef({});

  // Create the chart once.
  useEffect(() => {
    const c = createChart(box.current, {
      autoSize: true,
      layout: { background: { color: "#0f172a" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
      timeScale: { timeVisible: true, tickMarkFormatter: (t) => nyTick.format(new Date(t * 1000)) },
      localization: { timeFormatter: (t) => nyFull.format(new Date(t * 1000)) + " NY" },
    });
    series.current = {
      candles: c.addCandlestickSeries({ upColor: "#10b981", downColor: "#ef4444", borderVisible: false, wickUpColor: "#10b981", wickDownColor: "#ef4444" }),
      ema20: c.addLineSeries({ color: "#38bdf8", lineWidth: 1, title: "EMA20 (15m)", priceLineVisible: false }),
      ema50: c.addLineSeries({ color: "#a78bfa", lineWidth: 1, title: "EMA50 (15m)", priceLineVisible: false }),
      vwap: c.addLineSeries({ color: "#facc15", lineWidth: 1, lineStyle: LineStyle.Dotted, title: "VWAP", priceLineVisible: false }),
    };
    series.current.lines = [];
    chart.current = c;
    return () => c.remove();
  }, []);

  // Update data whenever new analysis arrives.
  useEffect(() => {
    if (!market?.available || !chart.current) return;
    const s = series.current;
    s.candles.setData(market.candles);
    s.ema20.setData(market.ema20_15);
    s.ema50.setData(market.ema50_15);
    s.vwap.setData(market.vwap);

    s.lines.forEach((l) => s.candles.removePriceLine(l));
    s.lines = Object.entries(market.levels)
      .filter(([, v]) => v != null)
      .map(([k, v]) => s.candles.createPriceLine({ price: v, color: LEVEL_COLORS[k], lineWidth: 1, lineStyle: LineStyle.Dashed, title: k }));

    s.candles.setMarkers(
      market.fvgs.map((g) => ({
        time: g.end_time,
        position: g.side === "bullish" ? "belowBar" : "aboveBar",
        color: g.side === "bullish" ? "#10b981" : "#ef4444",
        shape: g.side === "bullish" ? "arrowUp" : "arrowDown",
        text: "FVG",
      }))
    );
  }, [market]);

  return (
    <div className="card relative h-[460px] p-2">
      <div ref={box} className="h-full w-full" />
      {!market?.available && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-400">
          {market?.message ?? "Loading market data..."}
        </div>
      )}
    </div>
  );
}
