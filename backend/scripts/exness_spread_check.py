"""Exness vs Dukascopy spread, 2023 (rules: docs/exness_spread_check_preregistration.md).

Measurement only: reads the unmodified Exness zip and the stored Dukascopy minutes, runs no strategy and writes
nothing to the database. Writes docs/exness_spread_check_report.md.

    .\\.venv\\Scripts\\python scripts\\exness_spread_check.py
"""
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.core import data_quality as dq  # noqa: E402
from app.core.features import load_m1  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.repository import init_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "data" / "external" / "exness_2023" / "Exness_USTEC_2023.zip"
REPORT = ROOT.parent / "docs" / "exness_spread_check_report.md"
COLUMNS = ["Exness", "Symbol", "Timestamp", "Bid", "Ask"]
YEAR, ASSUMED, MIN_COVERAGE, MAX_PRICE_GAP, MAX_BAD_SHARE, MIN_DAYS = 2023, 1.5, 0.90, 10.0, 0.001, 200
LAGS = (-2, -1, 0, 1, 2)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def utc(*a) -> int:
    return int(datetime(*a, tzinfo=timezone.utc).timestamp())


CLOCK_PERIODS = {"before US DST": (utc(2023, 1, 1), utc(2023, 3, 12, 7)),
                 "US DST": (utc(2023, 3, 12, 7), utc(2023, 11, 5, 6)),
                 "after US DST": (utc(2023, 11, 5, 6), utc(2024, 1, 1))}


def bad_tick_mask(bid: np.ndarray, ask: np.ndarray) -> np.ndarray:
    """True for ticks the rules exclude: missing, bid <= 0, ask <= 0 or ask < bid."""
    with np.errstate(invalid="ignore"):
        return ~((bid > 0) & (ask > 0) & (ask >= bid))


def last_per_minute(ts: np.ndarray, bid: np.ndarray, ask: np.ndarray) -> pd.DataFrame:
    """The last tick of each minute (file order breaks ties). `ts` of the result is the minute start."""
    d = pd.DataFrame({"ts": ts // 60 * 60, "bid": bid, "ask": ask})
    return d.drop_duplicates("ts", keep="last").reset_index(drop=True)


def read_exness(path: Path) -> tuple[pd.DataFrame, int, int]:
    parts, total, bad = [], 0, 0
    with zipfile.ZipFile(path) as z, z.open(z.infolist()[0]) as f:
        for c in pd.read_csv(f, chunksize=2_000_000):
            if list(c.columns) != COLUMNS or set(c["Symbol"].unique()) != {"USTEC"}:
                raise SystemExit(f"Unexpected file layout: {list(c.columns)}. Stopping; nothing is guessed.")
            t = pd.to_datetime(c["Timestamp"], format="ISO8601", utc=True)
            ts = ((t - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype=np.int64)
            if ts.size and ts.max() >= utc(2025, 1, 1):
                raise SystemExit("File contains 2025+ data, which must not be read.")
            bid, ask = c["Bid"].to_numpy(dtype=float), c["Ask"].to_numpy(dtype=float)
            drop = bad_tick_mask(bid, ask)
            total += ts.size
            bad += int(drop.sum())
            parts.append(last_per_minute(ts[~drop], bid[~drop], ask[~drop]))
    out = pd.concat(parts, ignore_index=True).drop_duplicates("ts", keep="last").sort_values("ts")
    return out.reset_index(drop=True), total, bad


def in_window(d: pd.DataFrame, year: int = YEAR) -> pd.DataFrame:
    ny = pd.to_datetime(d["ts"], unit="s", utc=True).dt.tz_convert("America/New_York")
    mod = ny.dt.hour * 60 + ny.dt.minute
    keep = (ny.dt.year == year) & (ny.dt.day_of_week < 5) & (mod >= dq.WINDOW_START_MIN) & (mod < dq.WINDOW_END_MIN)
    return d.assign(ny_date=ny.dt.date, hour=ny.dt.hour, mod=mod)[keep].reset_index(drop=True)


def minute_changes(ts: np.ndarray, mid: np.ndarray) -> pd.Series:
    """Mid-price change into each minute, only where the previous minute exists."""
    s = pd.Series(mid, index=ts)
    return (s - s.reindex(s.index - 60).to_numpy()).dropna()


def lag_correlations(a: pd.Series, b: pd.Series, lags=LAGS) -> dict[int, float]:
    """Correlation of a(t) with b(t + lag minutes). A correct clock peaks at lag 0."""
    out = {}
    for lag in lags:
        moved = pd.Series(b.to_numpy(), index=b.index - lag * 60)
        j = pd.concat([a, moved], axis=1, join="inner")
        out[lag] = float(j.iloc[:, 0].corr(j.iloc[:, 1])) if len(j) > 2 else float("nan")
    return out


def assumption_verdict(median: float) -> str:
    return "1.5 assumption holds" if median <= ASSUMED else "1.5 assumption understated"


def ratio_verdict(ratio: float) -> str:
    if ratio < 0.80:
        return "Exness cheaper"
    return "similar" if ratio <= 1.25 else "Exness more expensive"


def weekdays_2023() -> list[date]:
    days = pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31", freq="D")
    return [d.date() for d in days if d.weekday() < 5]


def pass_fail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> int:
    if not ZIP.exists():
        raise SystemExit(f"Missing {ZIP}")
    init_db()
    raw, ticks, bad = read_exness(ZIP)
    ex = in_window(raw)
    bid = load_m1(dk.SOURCE, dk.INSTRUMENT, utc(2023, 1, 1), utc(2024, 1, 1))
    ask = load_m1(dk.SOURCE, dk.ASK_SYMBOL, utc(2023, 1, 1), utc(2024, 1, 1))
    du = bid[["ts", "c"]].merge(ask[["ts", "c"]], on="ts", suffixes=("_bid", "_ask"))
    du = in_window(du.rename(columns={"c_bid": "bid", "c_ask": "ask"}))
    for d in (ex, du):
        d["spread"], d["mid"] = d["ask"] - d["bid"], (d["ask"] + d["bid"]) / 2
    j = ex.merge(du[["ts", "spread", "mid"]], on="ts", suffixes=("_ex", "_du"))

    # File checks
    q = dq.session_quality(ex[["ts"]])
    valid = dq.valid_dates(q)
    days = weekdays_2023()
    coverage = len([d for d in days if d in valid]) / len(days)
    dx, dd = minute_changes(ex["ts"].to_numpy(), ex["mid"].to_numpy()), minute_changes(du["ts"].to_numpy(), du["mid"].to_numpy())
    clock_rows, clock_ok = [], True
    for name, (t0, t1) in CLOCK_PERIODS.items():
        c = lag_correlations(dx[(dx.index >= t0) & (dx.index < t1)], dd[(dd.index >= t0) & (dd.index < t1)])
        best = max(c, key=lambda k: -np.inf if np.isnan(c[k]) else c[k])
        clock_ok &= best == 0
        clock_rows.append(f"| {name} | " + " | ".join(f"{c[k]:.3f}" for k in LAGS) + f" | {best:+d} |")
    price_gap = float((j["mid_ex"] - j["mid_du"]).abs().median())
    bad_share = bad / ticks if ticks else 1.0
    checks = [("Coverage: valid weekdays >= 90%", coverage >= MIN_COVERAGE, f"{coverage:.1%}"),
              ("Clock: correlation peaks at lag 0 in all 3 periods", clock_ok, "see table"),
              ("Price level: median gap <= 10 points", price_gap <= MAX_PRICE_GAP, f"{price_gap:.2f} points"),
              ("Bad ticks <= 0.1%", bad_share <= MAX_BAD_SHARE, f"{bad:,} of {ticks:,} ({bad_share:.4%})")]
    usable = all(ok for _, ok, _ in checks)

    # Spread results on shared minutes
    rows = []
    for name, w in (("pre-US 03:00-09:29", j[j["mod"] < 570]), ("US 09:30-15:54", j[j["mod"] >= 570])):
        n_days = w["ny_date"].nunique()
        if w.empty:
            rows.append(f"| {name} | 0 | 0 | – | – | – | – | – | not enough data | not enough data |")
            continue
        me, md = w["spread_ex"].median(), w["spread_du"].median()
        ratio = me / md if md > 0 else float("nan")
        if not usable:
            v1 = v2 = "no verdict (file not usable)"
        elif n_days < MIN_DAYS:
            v1 = v2 = "not enough data"
        else:
            v1, v2 = assumption_verdict(me), ratio_verdict(ratio)
        rows.append(f"| {name} | {len(w):,} | {n_days} | {me:.2f} | {w['spread_ex'].quantile(.9):.2f} | {md:.2f} | "
                    f"{w['spread_du'].quantile(.9):.2f} | {ratio:.2f} | {v1} | {v2} |")
    hours = j.groupby("hour").agg(n=("ts", "size"), ex=("spread_ex", "median"), ex90=("spread_ex", lambda x: x.quantile(.9)),
                                  du=("spread_du", "median"), du90=("spread_du", lambda x: x.quantile(.9)))

    month_of = pd.Series([d.month for d in days])
    good = pd.Series([d in valid for d in days])
    md = ["# Exness vs Dukascopy spread, 2023 — results", "",
          f"Made by `scripts/exness_spread_check.py` on {date.today()}. Rules were committed before the file was downloaded "
          "(`docs/exness_spread_check_preregistration.md`). Measurement only: no strategy was run and no cost, backtest "
          "or qualification setting changed.", "",
          f"**File usable under the rules: {'YES' if usable else 'NO'}.**", "",
          "## What the words mean", "",
          "- **Spread:** ask minus bid, in index points. You pay it when you enter and exit a trade.",
          "- **Median:** the middle value. Half of the minutes were lower and half were higher.",
          "- **p90:** 90% of the minutes were at or below this value, so it shows the expensive moments.", "",
          "## File checks", "", "| check | result | value |", "|---|---|---|"]
    md += [f"| {n} | {pass_fail(ok)} | {v} |" for n, ok, v in checks]
    md += ["", "### Clock check (correlation of 1-minute price changes; lag in minutes)", "",
           "| period | " + " | ".join(f"{k:+d}" for k in LAGS) + " | best |", "|---|" + "---:|" * (len(LAGS) + 1)]
    md += clock_rows
    md += ["", "### Valid sessions by month", "", "| month | weekdays | valid |", "|---:|---:|---:|"]
    md += [f"| {m} | {int((month_of == m).sum())} | {int(good[month_of == m].sum())} |" for m in range(1, 13)]
    md += ["", "## Spread (minutes present in both sources)", "",
           "| window | minutes | days | Exness median | Exness p90 | Dukascopy median | Dukascopy p90 | ratio | vs 1.5 | vs Dukascopy |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---|---|"] + rows
    md += ["", "## By New York hour", "", "| hour | minutes | Exness median | Exness p90 | Dukascopy median | Dukascopy p90 |",
           "|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {h:02d}:00 | {int(r.n):,} | {r.ex:.2f} | {r.ex90:.2f} | {r.du:.2f} | {r.du90:.2f} |" for h, r in hours.iterrows()]
    md += ["", "## Limits", "",
           "- This is the archive's `USTEC` instrument. Other account types (`USTECm`, `USTECc`, Raw Spread, Zero) can differ, "
           "and any commission is not in the spread.",
           "- It shows the spread at the last tick of each minute, not the price of any actual order.",
           "- Exness history starts in August 2019, so it cannot meet the 90% coverage rule for 2019-2022 by itself.",
           "- It says nothing about whether a strategy makes money."]
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("usable:", usable)
    for n, ok, v in checks:
        print(pass_fail(ok), n, v)
    print("\n".join(clock_rows), "\n".join(rows), sep="\n")
    print("->", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
