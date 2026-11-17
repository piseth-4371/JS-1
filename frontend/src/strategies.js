// Every strategy the backend knows (app/core/strategies/__init__.py), with a plain-English name
// and the latest backtest result recorded in docs/decisions.md. Results are history, not a promise.
// tone: "pending" = not fully tested yet, "fail" = failed development + validation (2019-2024).
// NAS100 wording follows docs/bidask_full_preregistration.md: average R after costs, development 2019-22 /
// validation 2023-24 (bid-only HistData), plus Dukascopy real bid/ask 2023. Averages are history, not a chance to win.
export const STRATEGY_INFO = {
  trend_fvg: { label: "Trend + FVG pullback (NY)", tone: "fail",
    status: "Negative observed expectancy: -0.06R (2019-22) / -0.18R (2023-24) per trade after costs. Real bid/ask 2023: -0.20R. Full 2019-24 bid/ask re-test: waiting for data." },
  sweep_mss_fvg: { label: "Liquidity sweep + FVG (NY)", tone: "fail",
    status: "Negative observed expectancy: -0.17R (2019-22) / +0.15R (2023-24); not consistent. Real bid/ask 2023: -0.03R. Full 2019-24 bid/ask re-test: waiting for data." },
  orb: { label: "Opening range breakout (NY)", tone: "fail",
    status: "Negative observed expectancy: -0.01R (2019-22) / -0.07R (2023-24) per trade after costs. Real bid/ask 2023: -0.21R. Full 2019-24 bid/ask re-test: waiting for data." },
  vwap_reversion: { label: "VWAP reversion (NY)", tone: "fail",
    status: "Negative observed expectancy: -0.31R (2019-22) / -0.21R (2023-24) per trade after costs. Real bid/ask 2023: -0.10R. Full 2019-24 bid/ask re-test: waiting for data." },
  silver_bullet: { label: "Silver Bullet 10-11 (NY)", tone: "fail",
    status: "Negative observed expectancy: -0.07R (2019-22) / -0.11R (2023-24) per trade after costs. Real bid/ask 2023 alone: +0.32R, unproven (range crosses 0, one of 7 tested). Full 2019-24 bid/ask re-test: waiting for data." },
  london_trend_fvg: { label: "Trend + FVG pullback (London)", tone: "fail",
    status: "Negative observed expectancy: -0.35R (2019-22) / -0.24R (2023-24) per trade after costs. Real bid/ask 2023: -0.20R (pre-open spread ~3 pts). Full 2019-24 bid/ask re-test: waiting for data." },
  london_sweep_mss_fvg: { label: "Liquidity sweep + FVG (London)", tone: "fail",
    status: "Negative observed expectancy: -0.33R (2019-22) / -0.37R (2023-24) per trade after costs. Real bid/ask 2023: -0.60R. Full 2019-24 bid/ask re-test: waiting for data." },
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
