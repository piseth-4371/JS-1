"""Broker spread by New York hour from MT5 demo minute history (rules: docs/spread_by_hour_preregistration.md).

Read-only: no orders, no settings changes. Each run adds bars to data/reports/mt5_spreads.csv, so re-running
later extends the sample. Writes docs/spread_by_hour_report.md.

    .\\.venv\\Scripts\\python scripts\\spread_by_hour.py
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.core.sources.mt5_source import server_to_utc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "reports" / "mt5_spreads.csv"
ASSUMED, MIN_DAYS = 1.5, 10


def fetch() -> pd.DataFrame:
    import MetaTrader5 as mt5
    s = get_settings()
    ok = mt5.initialize(s.mt5_terminal_path) if s.mt5_terminal_path else mt5.initialize()
    if not ok:
        raise SystemExit(f"MT5 terminal unavailable: {mt5.last_error()}")
    try:
        acc = mt5.account_info()
        if acc is None or acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            raise SystemExit("A demo account is required.")
        if not mt5.symbol_select(s.mt5_symbol, True):
            raise SystemExit(f"{s.mt5_symbol} unavailable")
        point = mt5.symbol_info(s.mt5_symbol).point
        rates = mt5.copy_rates_from_pos(s.mt5_symbol, mt5.TIMEFRAME_M1, 1, 99000)   # pos 1 = closed bars only
        if rates is None or len(rates) == 0:
            raise SystemExit(f"No history: {mt5.last_error()}")
        tz = ZoneInfo(s.mt5_server_tz)
        ts = np.array([server_to_utc(int(t), tz) for t in rates["time"]], dtype=np.int64)
        return pd.DataFrame({"ts": ts, "spread": rates["spread"].astype(float) * point,
                             "server": acc.server, "symbol": s.mt5_symbol})
    finally:
        mt5.shutdown()


def window_row(name: str, d: pd.DataFrame) -> tuple[str, str]:
    days = d["ny_date"].nunique()
    if days < MIN_DAYS:
        return f"| {name} | {len(d):,} | {days} | – | – | not enough data |", "n/a"
    med, p90 = d["spread"].median(), d["spread"].quantile(0.9)
    verdict = "1.5 assumption holds on this feed" if med <= ASSUMED else "1.5 assumption understated on this feed"
    return f"| {name} | {len(d):,} | {days} | {med:.2f} | {p90:.2f} | {verdict} |", med


def main() -> int:
    new = fetch()
    old = pd.read_csv(STORE) if STORE.exists() else new.iloc[0:0]
    allb = pd.concat([old, new]).drop_duplicates(subset=["server", "symbol", "ts"], keep="last").sort_values("ts")
    STORE.parent.mkdir(parents=True, exist_ok=True)
    allb.to_csv(STORE, index=False)

    ny = pd.to_datetime(allb["ts"], unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = ny.dt.hour * 60 + ny.dt.minute
    d = allb.assign(ny_date=ny.dt.date, hour=ny.dt.hour, mod=mod)
    d = d[(ny.dt.day_of_week < 5) & (mod >= 180) & (mod < 955) & np.isfinite(d["spread"]) & (d["spread"] >= 0)]
    if d.empty:
        print("No weekday bars in 03:00-15:55 NY.")
        return 1
    pre, us = d[d["mod"] < 570], d[d["mod"] >= 570]
    r_pre, m_pre = window_row("pre-US 03:00-09:29", pre)
    r_us, m_us = window_row("US 09:30-15:54", us)
    if "n/a" in (m_pre, m_us):
        pattern = "not enough data"
    else:
        pattern = (f"YES (pre-US median {m_pre:.2f} >= 1.5 x US median {m_us:.2f})" if m_pre >= 1.5 * m_us
                   else f"NO (pre-US median {m_pre:.2f} < 1.5 x US median {m_us:.2f})")
    first, last = d["ny_date"].min(), d["ny_date"].max()
    hours = d.groupby("hour")["spread"].agg(["size", "median", lambda x: x.quantile(0.9)])
    md = ["# Broker spread by time of day — results", "",
          f"Made by `scripts/spread_by_hour.py` on {date.today()}. Rules fixed in `docs/spread_by_hour_preregistration.md` "
          "before the analysis. Measurement only: no cost, backtest or qualification change.", "",
          "## Data", "",
          f"- {allb['server'].iloc[-1]} `{allb['symbol'].iloc[-1]}` 1-minute bar `spread` field, New York dates {first} .. {last} "
          f"(weekdays, 03:00-15:55 NY): {len(d):,} minutes on {d['ny_date'].nunique()} days.",
          "- MetaQuotes demo feed, **not Exness**. The bar spread may be the minimum within the minute, so it can understate cost.",
          f"- Distribution check: max spread {d['spread'].max():.2f}; {d['spread'].round(2).isin([0.9, 1.0]).mean():.0%} of minutes "
          "are exactly 0.90 or 1.00. A feed that never widens (not even at the open or news) looks fixed/capped or "
          "minimum-per-minute, so it cannot show the spread actually paid at busy moments.", "",
          "## Pre-registered decisions (assumption 1.5 pts)", "",
          "| window | minutes | days | median | p90 | verdict |", "|---|---:|---:|---:|---:|---|", r_pre, r_us, "",
          f"**Same pattern as Dukascopy (pre-US much wider):** {pattern}", "",
          "For comparison, Dukascopy 2023: pre-US ~3.0, US ~1.45 points (`docs/bidask_retest_report.md`).", "",
          "## By New York hour", "", "| hour | minutes | median | p90 |", "|---:|---:|---:|---:|"]
    md += [f"| {h:02d}:00 | {int(r.iloc[0]):,} | {r.iloc[1]:.2f} | {r.iloc[2]:.2f} |" for h, r in hours.iterrows()]
    (ROOT.parent / "docs" / "spread_by_hour_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(r_pre, r_us, pattern, sep="\n")
    print("-> docs/spread_by_hour_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
