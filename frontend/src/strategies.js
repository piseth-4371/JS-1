// Every strategy the backend knows (app/core/strategies/__init__.py), with a plain-English name
// and the latest backtest result recorded in docs/decisions.md. Results are history, not a promise.
// tone: "pending" = not fully tested yet, "fail" = failed development + validation (2019-2024).
export const STRATEGY_INFO = {
  trend_fvg: { label: "Trend + FVG pullback (NY)", tone: "fail",
    status: "Failed 2019-2024 test: -0.06R (2019-22) / -0.18R (2023-24) per trade. Not robust." },
  sweep_mss_fvg: { label: "Liquidity sweep + FVG (NY)", tone: "fail",
    status: "Failed 2019-2024 test: -0.17R / +0.15R per trade. Not consistent across periods." },
  orb: { label: "Opening range breakout (NY)", tone: "fail",
    status: "Failed 2019-2024 test: -0.01R / -0.07R per trade. Break-even at best, no edge." },
  vwap_reversion: { label: "VWAP reversion (NY)", tone: "fail",
    status: "Failed 2019-2024 test: -0.31R / -0.21R per trade." },
  silver_bullet: { label: "Silver Bullet 10-11 (NY)", tone: "fail",
    status: "Failed 2019-2024 test: -0.07R / -0.11R per trade." },
  london_trend_fvg: { label: "Trend + FVG pullback (London)", tone: "fail",
    status: "Failed 2019-2024 test: -0.35R / -0.24R per trade." },
  london_sweep_mss_fvg: { label: "Liquidity sweep + FVG (London)", tone: "fail",
    status: "Failed 2019-2024 test: -0.33R / -0.37R per trade." },
  btc_weekend_trend_fvg: { label: "BTC weekend: trend + FVG", tone: "fail",
    status: "Failed 2019-2024 test: -0.50R (2019-22) / -1.26R (2023-24) per trade. Fees eat most moves." },
  btc_weekend_sweep_mss_fvg: { label: "BTC weekend: liquidity sweep", tone: "fail",
    status: "Failed 2019-2024 test: -0.58R / -0.62R per trade." },
  btc_weekend_orb: { label: "BTC weekend: UTC opening range", tone: "fail",
    status: "Failed 2019-2024 test: -0.47R / -1.31R per trade." },
  btc_weekend_vwap_reversion: { label: "BTC weekend: VWAP reversion", tone: "fail",
    status: "Failed 2019-2024 test: -0.80R / -1.59R per trade." },
  btc_weekend_silver_bullet: { label: "BTC weekend: Silver Bullet", tone: "fail",
    status: "Failed 2019-2024 test: -0.67R / -2.09R per trade." },
};

export const STRATEGIES = Object.keys(STRATEGY_INFO);
export const strategyLabel = (name) => STRATEGY_INFO[name]?.label ?? name ?? "-";
