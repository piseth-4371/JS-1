// Every strategy the backend knows (app/core/strategies/__init__.py), with a plain-English name
// and the latest backtest result recorded in docs/decisions.md. Results are history, not a promise.
// tone: "pending" = not fully tested yet, "fail" = failed development + validation (2019-2024).
export const STRATEGY_INFO = {
  trend_fvg: { label: "Trend + FVG pullback (NY)", tone: "pending",
    status: "2019 only: -0.07R/trade, not robust. Full 2019-2024 test waits for the NAS100 download." },
  sweep_mss_fvg: { label: "Liquidity sweep + FVG (NY)", tone: "pending",
    status: "2019 only: +0.07R/trade, not robust. Full 2019-2024 test waits for the NAS100 download." },
  orb: { label: "Opening range breakout (NY)", tone: "pending",
    status: "2019 only: +0.09R/trade, not robust (negative with double costs). Full test pending." },
  vwap_reversion: { label: "VWAP reversion (NY)", tone: "pending",
    status: "2019 only: -0.45R/trade. Full 2019-2024 test pending." },
  silver_bullet: { label: "Silver Bullet 10-11 (NY)", tone: "pending",
    status: "2019 only: -0.12R/trade. Full 2019-2024 test pending." },
  london_trend_fvg: { label: "Trend + FVG pullback (London)", tone: "pending",
    status: "2019 only: -0.37R/trade. Full 2019-2024 test pending." },
  london_sweep_mss_fvg: { label: "Liquidity sweep + FVG (London)", tone: "pending",
    status: "2019 only: -0.28R/trade. Full 2019-2024 test pending." },
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
