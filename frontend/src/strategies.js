// Plain-English names for the strategies the backend knows (app/core/strategies/__init__.py).
// Backtest results live in docs/decisions.md and docs/experiment_journal.md, not here.
const LABELS = {
  trend_fvg: "Trend + FVG pullback (NY)",
  sweep_mss_fvg: "Liquidity sweep + FVG (NY)",
  orb: "Opening range breakout (NY)",
  vwap_reversion: "VWAP reversion (NY)",
  silver_bullet: "Silver Bullet 10-11 (NY)",
  london_trend_fvg: "Trend + FVG pullback (London)",
  london_sweep_mss_fvg: "Liquidity sweep + FVG (London)",
  btc_weekend_trend_fvg: "BTC weekend: trend + FVG",
  btc_weekend_sweep_mss_fvg: "BTC weekend: liquidity sweep",
  btc_weekend_orb: "BTC weekend: UTC opening range",
  btc_weekend_vwap_reversion: "BTC weekend: VWAP reversion",
  btc_weekend_silver_bullet: "BTC weekend: Silver Bullet",
};

export const strategyLabel = (name) => LABELS[name] ?? name ?? "-";
