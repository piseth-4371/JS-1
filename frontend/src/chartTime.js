// Pure helpers for the chart's timeframe, candle countdown and live (display-only) candle.

export const TF_LABEL = { 1: "1m", 5: "5m", 15: "15m", 60: "1h", 240: "4h" };

// Seconds until the current tf-minute candle closes (candles start at UTC epoch multiples, as the backend groups them).
export function secondsToClose(nowSeconds, tf) {
  const span = tf * 60;
  return span - (Math.floor(nowSeconds) % span);
}

// 135 -> "02:15"; 3725 -> "1:02:05" (like TradingView's countdown under the price).
export function formatCountdown(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

// Fold the live 5-minute preview candle into the chart's current tf candle.
// `base` = newest candle from history (may already hold the closed minutes of the current tf candle).
// Returns null when it cannot be shown honestly: on 1m (a 5m candle cannot be split into minutes) or if older.
export const MAX_LIVE_GAP_SECONDS = 600;

// True when the live candle continues the history (no gap of more than 10 minutes after the newest candle ends).
// When the history is stale (engine off, market closed) a live price must not be glued onto old candles.
export function liveConnects(base, live, tf) {
  return !!live && (!base || live.time - (base.time + tf * 60) <= MAX_LIVE_GAP_SECONDS);
}

export function mergeLiveCandle(base, live, tf) {
  if (!live || tf < 5 || !liveConnects(base, live, tf)) return null;
  const span = tf * 60;
  const start = Math.floor(live.time / span) * span;
  if (base && start < base.time) return null;
  if (base && start === base.time) {
    return { time: start, open: base.open, high: Math.max(base.high, live.high),
      low: Math.min(base.low, live.low), close: live.close };
  }
  return { time: start, open: live.open, high: live.high, low: live.low, close: live.close };
}
