"""Bid/ask re-test of the 7 NAS100 strategies on 2023 (rules: docs/bidask_retest_preregistration.md).

Measurement only: no rule, parameter or risk setting changes; nothing can qualify from this test.
Needs the Dukascopy BID + ASK download first (scripts/download_dukascopy_bidask.py).

    .\\.venv\\Scripts\\python scripts\\bidask_retest.py
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.report_card import max_drawdowns  # noqa: E402
from app.backtest.robustness import cluster_bootstrap  # noqa: E402
from app.core import data_quality as dq  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.markets import NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRATS = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet", "london_trend_fvg", "london_sweep_mss_fvg"]
SPREAD, SLIP, MATERIAL = 1.5, 0.5, 0.02


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def stats(rs: np.ndarray, dates) -> dict:
    if rs.size < 2:
        return {"n": int(rs.size), "avg": float(rs.mean()) if rs.size else float("nan")}
    se = rs.std(ddof=1) / np.sqrt(rs.size)
    weeks = [f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}" for d in dates]
    cb = cluster_bootstrap(rs, weeks)
    eq = np.concatenate(([1.0], np.cumprod(1 + 0.005 * rs)))
    return {"n": int(rs.size), "avg": float(rs.mean()), "lo": float(rs.mean() - 1.96 * se), "hi": float(rs.mean() + 1.96 * se),
            "wlo": cb.ci_low, "whi": cb.ci_high, "dd": float(max_drawdowns(eq[None, :])[0] * 100)}


def fmt(s: dict) -> str:
    if s["n"] < 2:
        return f"{s['n']} | – | – | – | –"
    return (f"{s['n']} | {s['avg']:+.3f} | {s['lo']:+.2f} to {s['hi']:+.2f} | {s['wlo']:+.2f} to {s['whi']:+.2f} | {s['dd']:.1f}%")


def main() -> int:
    init_db()
    a0, a1 = ts(date(2022, 12, 1)), ts(date(2024, 1, 1))
    bid = load_m1(dk.SOURCE, dk.INSTRUMENT, a0, a1)
    ask = load_m1(dk.SOURCE, dk.ASK_SYMBOL, a0, a1)
    j = bid.merge(ask[["ts", "o", "h", "l", "c"]], on="ts", suffixes=("", "_ask"), how="inner").sort_values("ts")
    if j.empty:
        print("No Dukascopy bid+ask data yet. Run scripts/download_dukascopy_bidask.py first.")
        return 1
    days23 = {d for d in pd.to_datetime(j["ts"], unit="s", utc=True).dt.tz_convert("America/New_York").dt.date if d.year == 2023}
    neg = int((j["c_ask"] < j["c"]).sum())
    spread = (j["c_ask"] - j["c"]).to_numpy()
    j["v"] = 0.0                                   # same plain-average "VWAP" as the HistData backtest
    m1 = j[["ts", "o", "h", "l", "c", "v"]].reset_index(drop=True)
    frame = build_frame(m1, hold_mask=NAS100.hold_mask)
    assert np.array_equal(frame.m1["ts"], m1["ts"].to_numpy())
    real_ask = {k: j[f"{k}_ask"].to_numpy() for k in ("o", "h", "l")}
    synth_ask = {k: frame.m1[k] + SPREAD for k in ("o", "h", "l")}
    q = dq.session_quality(m1)
    q23 = [x for x in q if x.ny_date.year == 2023]
    valid = dq.valid_dates(q)
    ny = pd.to_datetime(j["ts"], unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = (ny.dt.hour * 60 + ny.dt.minute).to_numpy()
    win = (mod >= 180) & (mod < 955)
    rth = (mod >= 570) & (mod < 960)
    print(f"{len(j):,} joined minutes; 2023 weekdays with data {len(q23)}, valid {sum(x.valid for x in q23)}")

    variants = [("V1 bid-only", Costs(SPREAD, SLIP), None), ("V2 synthetic ask", Costs(0, SLIP), synth_ask),
                ("V3 real bid/ask", Costs(0, SLIP), real_ask)]
    hist = pd.read_csv(ROOT / "data" / "reports" / "audit_trades.csv") if (ROOT / "data" / "reports" / "audit_trades.csv").exists() else None
    rows, decide = [], []
    settings = RiskSettings()
    for name in STRATS:
        res = {}
        for vname, costs, ak in variants:
            for label, vd in (("all", None), ("valid", valid)):
                tr = [t for t in run(ALL[name](), frame, settings, costs, valid_dates=vd, ask=ak).trades if t.ny_date.year == 2023]
                res[(vname, label)] = stats(np.array([t.r for t in tr]), [t.ny_date for t in tr])
        if hist is not None:
            for label, key in (("all", "all sessions"), ("valid", "valid sessions")):
                h = hist[(hist["strategy"] == name) & (hist["sessions"] == key) & (hist["ny_date"].str.startswith("2023"))]
                res[("HistData 2023 (reference)", label)] = stats(h["r"].to_numpy(), [date.fromisoformat(d) for d in h["ny_date"]])
        for (vname, label), s in res.items():
            rows.append(f"| {name} | {vname} | {label} | {fmt(s)} |")
        v1, v2, v3 = (res[(v, "valid")]["avg"] for v in ("V1 bid-only", "V2 synthetic ask", "V3 real bid/ask"))
        d21 = v2 - v1
        verdict = "optimistic" if d21 < -MATERIAL else "not material" if abs(d21) <= MATERIAL else "pessimistic"
        decide.append((name, v1, v2, v3, d21, verdict, v3 <= 0, res[("V3 real bid/ask", "valid")]))
        print(f"[{name}] V1 {v1:+.3f}  V2 {v2:+.3f}  V3 {v3:+.3f}  -> bid-only model {verdict}")

    md = ["# Bid/ask re-test on 2023 (Dukascopy) — results", "",
          f"Made by `scripts/bidask_retest.py` on {date.today()}. Rules fixed in `docs/bidask_retest_preregistration.md` "
          "(commit 8a9c21d) before the data was downloaded. Measurement only: nothing can qualify from this test; "
          "`scanner.QUALIFIED` stays empty.", "",
          "## Data", "",
          f"- Dukascopy USATECHIDXUSD BID + ASK, 2022-12-01..2023-12-31 (December 2022 = warm-up only). {len(j):,} minutes with both quotes.",
          f"- 2023 weekdays with data: {len(q23)}; valid under the session rule: {sum(x.valid for x in q23)} "
          f"(HistData 2023: 256 / 137).",
          f"- Minutes where ask < bid: {neg}. Quoted spread (ask close − bid close): 03:00-15:55 NY median "
          f"{np.median(spread[win]):.2f}, p90 {np.percentile(spread[win], 90):.2f}; 09:30-16:00 median {np.median(spread[rth]):.2f}, "
          f"p90 {np.percentile(spread[rth], 90):.2f} points. This is Dukascopy's spread, not Exness's.", "",
          "## Pre-registered decisions (valid sessions, 2023 trades)", "",
          "| strategy | V1 bid-only | V2 synthetic ask | V3 real bid/ask | V2 − V1 | bid-only model | V3 ≤ 0 | V3 95% range |",
          "|---|---:|---:|---:|---:|---|---|---|"]
    for name, v1, v2, v3, d21, verdict, le0, s3 in decide:
        rng = f"{s3['lo']:+.2f} to {s3['hi']:+.2f}" if s3["n"] >= 2 else "–"
        md.append(f"| {name} | {v1:+.3f} | {v2:+.3f} | {v3:+.3f} | {d21:+.3f} | {verdict} | {'yes' if le0 else 'NO'} | {rng} |")
    all_le0 = all(x[6] for x in decide)
    md += ["", f"**Conclusion rule:** every strategy's V3 average ≤ 0 → 'no edge after costs' reinforced: "
           f"**{'YES' if all_le0 else 'NO (see table; still cannot qualify)'}**.", "",
           "## All results (2023 trades only)", "",
           "| strategy | variant | sessions | trades | avg R | 95% iid | 95% week | max DD |", "|---|---|---|---:|---:|---|---|---:|", *rows, ""]
    (ROOT.parent / "docs" / "bidask_retest_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("-> docs/bidask_retest_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
