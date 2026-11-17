"""Bid/ask re-test of the 7 NAS100 strategies, 2019-2024 (rules: docs/bidask_full_preregistration.md).

Measurement only: no rule, parameter or risk change; nothing can qualify; 2025+ is never loaded.
Needs the Dukascopy BID + ASK download (scripts/download_dukascopy_bidask.py). With missing data it still
runs, reports what is missing and gives "incomplete data — no verdict" where coverage is below 90%.

    .\\.venv\\Scripts\\python scripts\\bidask_full_retest.py
"""
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.backtest import decompose as dc  # noqa: E402
from app.backtest.engine import Costs, run  # noqa: E402
from app.core import data_quality as dq  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.markets import NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRATS = ["trend_fvg", "sweep_mss_fvg", "orb", "vwap_reversion", "silver_bullet", "london_trend_fvg", "london_sweep_mss_fvg"]
YEARS = range(2019, 2025)
SPLITS = {"development 2019-2022": range(2019, 2023), "validation 2023-2024": range(2023, 2025)}
MODELS = {"G gross": (Costs(0, 0), False), "B bid-only": (Costs(1.5, 0.5), False),
          "R real bid/ask": (Costs(0, 0.5), True), "S stress": (Costs(0.5, 1.0), True)}
FAMILY, MIN_COVERAGE = 7, 0.90
WARMUP, END = date(2018, 12, 1), date(2025, 1, 1)     # END is exclusive: 2025 is never loaded


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def f2(x, signed=True):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–" if x is None or np.isnan(x) else "inf"
    return f"{x:+.3f}" if signed else f"{x:.3f}"


def pct(s) -> str:
    return f"{s.win_rate * 100:.0f}%" if s.n else "–"


def load():
    bid = load_m1(dk.SOURCE, dk.INSTRUMENT, ts(WARMUP), ts(END))
    ask = load_m1(dk.SOURCE, dk.ASK_SYMBOL, ts(WARMUP), ts(END))
    j = bid.merge(ask[["ts", "o", "h", "l", "c"]], on="ts", suffixes=("", "_ask"), how="inner").sort_values("ts")
    assert j.empty or j["ts"].max() < ts(END), "2025+ data must never be loaded"
    return j.reset_index(drop=True)


def coverage(q) -> dict:
    by = defaultdict(lambda: {"days": 0, "valid": 0, "missing": []})
    have = {x.ny_date: x for x in q}
    for y in YEARS:
        d = date(y, 1, 1)
        while d.year == y:
            if d.weekday() < 5:
                c = by[y]
                if d in have and have[d].bars > 0:
                    c["days"] += 1
                    c["valid"] += have[d].valid
                else:
                    c["missing"].append(d)
            d = date.fromordinal(d.toordinal() + 1)
    return by


def weekdays(y):
    return sum(1 for k in range((date(y + 1, 1, 1) - date(y, 1, 1)).days) if date.fromordinal(date(y, 1, 1).toordinal() + k).weekday() < 5)


def clock_check(j: pd.DataFrame) -> list[tuple]:
    """Largest median |1-minute move| by NY minute must be 09:30, per year and DST regime (incl. US/UK mismatch)."""
    t = pd.to_datetime(j["ts"], unit="s", utc=True)
    ny, ldn = t.dt.tz_convert("America/New_York"), t.dt.tz_convert("Europe/London")
    us_dst = (ny.dt.tz_localize(None) - t.dt.tz_localize(None)) == pd.Timedelta(hours=-4)
    uk_bst = (ldn.dt.tz_localize(None) - t.dt.tz_localize(None)) == pd.Timedelta(hours=1)
    move = j["c"].diff().abs().where(j["ts"].diff() == 60)
    mod = ny.dt.hour * 60 + ny.dt.minute
    df = pd.DataFrame({"y": ny.dt.year, "mod": mod, "move": move, "wd": ny.dt.day_of_week,
                       "regime": np.where(us_dst != uk_bst, "US/UK mismatch", np.where(us_dst, "US summer", "US winter"))})
    df = df[(df["wd"] < 5) & (df["mod"] >= 180) & (df["mod"] < 955) & df["y"].between(2019, 2024)]
    out = []
    for (y, reg), g in df.groupby(["y", "regime"]):
        med = g.groupby("mod")["move"].median()
        days = g.shape[0] // 775
        if med.empty:
            continue
        top = int(med.idxmax())
        open_ = med.get(570, np.nan)
        # Amendment 1: the 09:30 jump must be clear and not sit an hour early/late (DST shift)
        ok = bool(open_ >= 1.5 * med.get(569, np.inf) and open_ > med.get(510, np.inf) and open_ > med.get(630, np.inf))
        out.append((int(y), reg, days, f"{top // 60:02d}:{top % 60:02d}", ok,
                    open_ / med.get(569, np.nan), med.get(510, np.nan), open_, med.get(630, np.nan)))
    return out


def histdata_check(j: pd.DataFrame) -> list[tuple]:
    h = load_m1(hd.SOURCE, hd.INSTRUMENT, ts(date(2019, 1, 1)), ts(END))
    m = j[["ts", "c"]].merge(h[["ts", "c"]], on="ts", suffixes=("_d", "_h"))
    yr = pd.to_datetime(m["ts"], unit="s", utc=True).dt.year
    return [(int(y), len(g), float((g["c_d"] - g["c_h"]).abs().median()), float((g["c_d"] - g["c_h"]).abs().quantile(0.99)))
            for y, g in m.groupby(yr)]


def main() -> int:
    init_db()
    j = load()
    if j.empty:
        print("No Dukascopy bid+ask data. Run scripts/download_dukascopy_bidask.py first.")
        return 1
    neg = int((j["c_ask"] < j["c"]).sum())
    clock = clock_check(j)
    bad_clock = [c for c in clock if not c[4] and c[2] >= 5]
    if bad_clock:
        print("CLOCK CHECK FAILED (largest move not at 09:30 NY):", bad_clock)
        return 2
    hcheck = histdata_check(j)
    j["v"] = 0.0
    m1 = j[["ts", "o", "h", "l", "c", "v"]].reset_index(drop=True)
    frame = build_frame(m1, hold_mask=NAS100.hold_mask)
    assert np.array_equal(frame.m1["ts"], m1["ts"].to_numpy())
    ask = {k: j[f"{k}_ask"].to_numpy() for k in ("o", "h", "l")}
    bid_o = j["o"].to_numpy()
    pos_of = {int(t): i for i, t in enumerate(j["ts"].to_numpy())}
    q = dq.session_quality(m1)
    valid = dq.valid_dates(q)
    cov = coverage(q)
    split_cov = {s: sum(cov[y]["days"] for y in ys) / sum(weekdays(y) for y in ys) for s, ys in SPLITS.items()}
    print(f"{len(j):,} joined minutes; coverage " + ", ".join(f"{s}: {c:.0%}" for s, c in split_cov.items()))

    settings = RiskSettings()
    trades = {}
    for name in STRATS:
        for mname, (costs, use_ask) in MODELS.items():
            res = run(ALL[name](), frame, settings, costs, valid_dates=valid, ask=ask if use_ask else None)
            trades[(name, mname)] = [t for t in res.trades if t.ny_date.year in YEARS]
        print(f"[{name}] " + "  ".join(f"{m.split()[0]} {np.mean([t.r for t in trades[(name, m)]]) if trades[(name, m)] else float('nan'):+.3f}"
                                       for m in MODELS))

    def sel(tr, years):
        return [t for t in tr if t.ny_date.year in years]

    def buy_leg_spread_r(t):
        """Real quoted spread (ask open - bid open) at the minute of the BUY leg, in R. An estimate."""
        i = pos_of[t.entry_ts if t.side == 1 else t.exit_ts]
        return (ask["o"][i] - bid_o[i]) / t.risk_pts

    md_main, md_cost, md_fill, md_year, verdicts, rows = [], [], [], [], [], []
    for name in STRATS:
        per_split = {}
        for sname, ys in SPLITS.items():
            r_tr, s_tr = sel(trades[(name, "R real bid/ask")], ys), sel(trades[(name, "S stress")], ys)
            g_tr, b_tr = sel(trades[(name, "G gross")], ys), sel(trades[(name, "B bid-only")], ys)
            rs = np.array([t.r for t in r_tr])
            s = dc.summarize(rs)
            lo, hi = dc.week_interval(rs, [t.ny_date for t in r_tr])
            flo, fhi = dc.week_interval(rs, [t.ny_date for t in r_tr], tests=FAMILY)
            stress = float(np.mean([t.r for t in s_tr])) if s_tr else float("nan")
            gross = float(np.mean([t.r for t in g_tr])) if g_tr else float("nan")
            ok = split_cov[sname] >= MIN_COVERAGE
            per_split[sname] = dc.SplitResult(s.n, s.avg, flo, stress, ok)
            small = " ⚠ < 30 trades: no conclusion" if s.n < 30 else ""
            md_main.append(f"| {name} | {sname.split()[0]} | {s.n}{small} | {pct(s)} | "
                           f"{f2(s.avg_win)} | {f2(s.avg_loss)} | {f2(gross)} | **{f2(s.avg)}** | {f2(s.profit_factor, False)} | "
                           f"{s.max_dd_pct:.1f}% | {f2(lo)} to {f2(hi)} | {f2(flo)} to {f2(fhi)} | {f2(stress)} |")
            # cost effect on identical trades (bid-only model: same fills, costs subtracted)
            cs = [dc.cost_split(t, MODELS["B bid-only"][0]) for t in b_tr]
            resid = max((abs(c.net - t.r) for c, t in zip(cs, b_tr)), default=0.0)
            mean = (lambda xs: float(np.mean(xs)) if xs else float("nan"))
            md_cost.append(f"| {name} | {sname.split()[0]} | {len(b_tr)} | {f2(mean([c.gross for c in cs]))} | "
                           f"{f2(-mean([c.spread for c in cs]))} | {f2(-mean([c.slippage for c in cs]))} | {f2(-mean([c.fees for c in cs]))} | "
                           f"**{f2(mean([c.net for c in cs]))}** | {resid:.1e} |")
            fe = dc.fill_effect(b_tr, r_tr)
            real_spread = mean([buy_leg_spread_r(t) for t in r_tr])
            md_fill.append(f"| {name} | {sname.split()[0]} | {fe.n_matched} | {fe.n_only_a} | {fe.n_only_b} | {fe.total_a:+.1f} | "
                           f"{fe.total_b:+.1f} | {fe.matched_diff:+.1f} | {fe.only_b:+.1f} | {-fe.only_a:+.1f} | {fe.residual:.1e} | "
                           f"{f2(-real_spread)} |")
            rows.append((name, sname, s.n, s.avg, flo, stress, ok))
        verdicts.append((name, dc.verdict(per_split["development 2019-2022"], per_split["validation 2023-2024"])))
        for y in YEARS:
            ry = sel(trades[(name, "R real bid/ask")], [y])
            gy = sel(trades[(name, "G gross")], [y])
            s = dc.summarize([t.r for t in ry])
            note = "" if cov[y]["days"] >= MIN_COVERAGE * weekdays(y) else f" (data {cov[y]['days']}/{weekdays(y)} days)"
            md_year.append(f"| {name} | {y}{note} | {s.n} | {pct(s)} | "
                           f"{f2(float(np.mean([t.r for t in gy])) if gy else float('nan'))} | {f2(s.avg)} | {f2(s.profit_factor, False)} | "
                           f"{s.max_dd_pct:.1f}% |")

    out_csv = ROOT / "data" / "reports" / "bidask_full_trades.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"model": m, **t.__dict__} for (n, m), tr in trades.items() for t in tr]).to_csv(out_csv, index=False)

    complete = all(c >= MIN_COVERAGE for c in split_cov.values())
    first, last = pd.to_datetime(j["ts"].iloc[[0, -1]], unit="s", utc=True).dt.date.tolist()
    md = ["# Bid/ask re-test 2019–2024 — results" + ("" if complete else " (INCOMPLETE DATA)"), "",
          f"Made by `scripts/bidask_full_retest.py` on {date.today()} "
          "(`cd backend; .\\.venv\\Scripts\\python scripts\\bidask_full_retest.py`). Rules fixed in "
          "`docs/bidask_full_preregistration.md` (commit f69e58c) before this run. Measurement only: nothing can qualify; "
          "`scanner.QUALIFIED` stays empty; 2025+ is not loaded.", "",
          "**Not fresh evidence:** all seven strategies were already tested on 2019–2024 (bid-only HistData) and 2023 "
          "was already re-tested with Dukascopy bid/ask; 36 strategy versions were tested in this project. A pass would "
          "only make a strategy eligible for a separately authorised final test on 2025+.", ""]
    if not complete:
        md += ["> **This run is INCOMPLETE.** At least one split has less than 90% of its weekdays with bid+ask data, "
               "so those strategies get no verdict. Indicators also bridge across long missing stretches, which makes the "
               "first days after a gap unreliable — in this partial run the 'development' trades are from December 2022 only, "
               "right after the first downloaded day, with no indicator warm-up. Re-run when the download finishes.", ""]
    md += ["## How to read this (plain English)", "",
           "- **R** = the amount risked on one trade. +1R = won what was risked; −1R = lost it.",
           "- **Expectancy** = the average R per trade. Above 0 = made money on average *in this history*; it says nothing certain about the future.",
           "- **Gross** = before any cost. **Net** = after spread, slippage and fees. Costs are always paid; profits are not.",
           "- **Win rate** is how often trades won in this history. It is not a chance of the next trade winning.",
           "- **95% week interval** = where the true average plausibly lies, found by re-drawing whole weeks of trades "
           "5,000 times. **Family interval** is wider because seven strategies are tested at once (one of seven can look "
           "good by luck). If an interval contains 0, the data cannot tell a small edge from none.",
           "- Assumptions of the week resampling: weeks are independent; longer regimes (a whole bull or bear year) are not "
           "captured, so the true uncertainty is larger than shown. With few trades the interval is unstable.", "",
           "## Data and checks", "",
           f"- Dukascopy USATECHIDXUSD BID + ASK, minutes with both quotes: {len(j):,} ({first} .. {last}). "
           "December 2018 is warm-up only. No missing minute is filled in; no synthetic ask is used.",
           f"- Minutes where ask < bid: {neg}.",
           f"- Coverage needed for a verdict: ≥ 90% of weekdays. " + "; ".join(f"{s}: {c:.0%}" for s, c in split_cov.items()) + ".", "",
           "| year | weekdays | with bid+ask | valid sessions | missing months (weekdays missing) |", "|---|---:|---:|---:|---|"]
    for y in YEARS:
        miss = pd.Series([d.strftime("%Y-%m") for d in cov[y]["missing"]]).value_counts().sort_index()
        mtxt = ", ".join(f"{k} ({v})" for k, v in miss.items() if v >= 3) or "none (holidays only)"
        md.append(f"| {y} | {weekdays(y)} | {cov[y]['days']} | {cov[y]['valid']} | {mtxt} |")
    md += ["", "**Clock / daylight-saving check** (amendment 1 in the plan): the median 1-minute move must jump at 09:30 NY "
           "(≥ 1.5 × 09:29) and be larger than at 08:30 and 10:30, where a one-hour DST error would put it. "
           "Top minute shown for information.", "",
           "| year | regime | ~days | 09:30 ÷ 09:29 | 08:30 | 09:30 | 10:30 | top minute | ok |",
           "|---|---|---:|---:|---:|---:|---:|---|---|"]
    md += [f"| {y} | {reg} | {d} | {ratio:.1f}× | {a:.2f} | {o:.2f} | {b:.2f} | {top} | {'yes' if ok else 'NO'} |"
           for y, reg, d, top, ok, ratio, a, o, b in clock]
    md += ["", "**Second source** (Dukascopy bid close vs HistData close on shared minutes):", "",
           "| year | shared minutes | median abs diff | p99 abs diff |", "|---|---:|---:|---:|"]
    md += [f"| {y} | {n:,} | {a:.3f} | {b:.3f} |" for y, n, a, b in hcheck]
    md += ["", "## Execution assumptions", "",
           "| model | prices | spread | slippage | fees |", "|---|---|---|---|---|",
           "| G gross | bid only | 0 | 0 | 0 |", "| B bid-only | bid only | 1.5 pts subtracted | 0.5 pt per market/stop leg | 0 |",
           "| **R real bid/ask (primary)** | buys on ask, sells on bid | in prices | 0.5 pt per market/stop leg | 0 |",
           "| S stress (fixed beforehand) | buys on ask, sells on bid | +0.5 pt extra | 1.0 pt per leg | 0 |", "",
           "Fees are 0 (no commission on an Exness Standard CFD; no swap because every position is closed by 15:55 NY). "
           "Signals use bid 5-minute bars; the stop is checked before the target; positions close at 15:55 NY; "
           "orders only on valid sessions; rules, parameters, risk limits and news blackout unchanged.", "",
           "## Pre-registered verdicts", "", "| strategy | verdict |", "|---|---|"]
    md += [f"| {n} | **{v}** |" for n, v in verdicts]
    md += ["", "Rule: *passes* = in both dev and validation ≥ 30 trades, average R > 0, family-interval lower bound > 0 "
           "and stress average > 0. *Negative observed expectancy* = average ≤ 0 in dev or validation. Otherwise "
           "*inconclusive*. Passing only means eligible for a separately authorised 2025+ test, not live trading.", "",
           "## 1. Results by split (model R, real bid/ask)", "",
           "| strategy | split | trades | win rate | avg win | avg loss | gross (G) | net | profit factor | max DD | 95% week | family 95% (7 tests) | stress net |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|", *md_main, "",
           "## 2. Where the costs go — identical trades (model B)", "",
           "Same fills with and without costs, per trade in R: gross − spread − slippage − fees = net. The last column is "
           "the largest per-trade reconciliation error.", "",
           "| strategy | split | trades | gross | spread | slippage | fees | net | max error |", "|---|---|---:|---:|---:|---:|---:|---:|---:|",
           *md_cost, "",
           "## 3. Fill model: bid-only (B) → real bid/ask (R)", "",
           "Total R changes for two reasons: the same trades get a different result (real spread instead of 1.5, stops and "
           "targets touched on the ask), and some trades fill only in one model. "
           "`total R − total B = matched change + R-only − B-only` (residual must be 0). The last column is the average "
           "real quoted spread at the buy leg (estimate, R per trade).", "",
           "| strategy | split | matched | B-only | R-only | total B | total R | matched change | + R-only | − B-only | residual | real spread |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|", *md_fill, "",
           "## 4. By year (model R; gross from model G)", "",
           "| strategy | year | trades | win rate | gross | net | profit factor | max DD |", "|---|---|---:|---:|---:|---:|---:|---:|",
           *md_year, "", f"Trades of all models: `backend/data/reports/bidask_full_trades.csv`.", ""]
    (ROOT.parent / "docs" / "bidask_full_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("verdicts:", verdicts)
    print("-> docs/bidask_full_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
