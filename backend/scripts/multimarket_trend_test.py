"""Slow multi-market trend test (rules: docs/multimarket_trend_preregistration.md) -> docs/multimarket_trend_report.md.

Research only: reads the FRED csv files, places no orders, writes nothing to the database.

    .\\.venv\\Scripts\\python scripts\\multimarket_trend_test.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from app.backtest import multimarket_trend as mt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FRED = ROOT / "data" / "external" / "fred"
REPORT = ROOT.parent / "docs" / "multimarket_trend_report.md"
PERIODS = {"development 1988-2010": ("1988-01", "2010-12"), "validation 2011-2024": ("2011-01", "2024-12")}


def pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def stats(r) -> dict:
    return {"ret": float(np.mean(r) * 12), "vol": float(np.std(r, ddof=1) * np.sqrt(12)), "sharpe": mt.sharpe(r),
            "dd": mt.max_drawdown(r)}


def main() -> int:
    daily = {m.fred_id: mt.read_fred(FRED / f"{m.fred_id}.csv", m.invert) for m in mt.MARKETS}
    p = mt.build_panel(daily)
    month_str = p.months.astype(str)

    trend_g, trend_n = mt.market_returns(p.trades, p.signal, p.weight, p.ret, p.cost)
    _, trend_s = mt.market_returns(p.trades, p.signal, p.weight, p.ret, p.cost, cost_mult=2.0)
    ones = np.ones_like(p.signal)
    long_g, long_n = mt.market_returns(p.trades, ones, p.weight, p.ret, p.cost)
    _, long_s = mt.market_returns(p.trades, ones, p.weight, p.ret, p.cost, cost_mult=2.0)
    port = {k: mt.portfolio(p.trades, v) for k, v in
            {"tg": trend_g, "tn": trend_n, "ts": trend_s, "lg": long_g, "ln": long_n, "ls": long_s}.items()}

    rows, checks, extra, classes = [], {}, [], []
    for name, (a, b) in PERIODS.items():
        mask = (month_str >= a) & (month_str <= b)
        n_mk = p.trades[mask].sum(axis=1)
        r = {k: v[mask] for k, v in port.items()}
        if np.isnan(np.concatenate(list(r.values()))).any():
            raise SystemExit(f"{name}: a month has no trading market")
        st = {k: stats(v) for k, v in r.items()}
        lo, hi = mt.block_bootstrap_sharpe(r["tn"])
        rnd = mt.random_sign_sharpes(p, mask)
        p95 = float(np.nanpercentile(rnd, 95))
        share_below = float(np.mean(rnd < st["tn"]["sharpe"]))
        checks[name] = mt.PeriodCheck(int(mask.sum()), float(n_mk.mean()), st["tn"]["sharpe"], lo, p95, st["ts"]["sharpe"])
        for label, k in (("trend, gross", "tg"), ("**trend, net**", "tn"), ("trend, stress", "ts"),
                         ("always long, gross", "lg"), ("always long, net", "ln"), ("always long, stress", "ls")):
            s = st[k]
            rows.append(f"| {name} | {label} | {pct(s['ret'])} | {s['vol'] * 100:.1f}% | {s['sharpe']:+.2f} | {pct(s['dd'])} |")
        worst = r["ln"] <= np.quantile(r["ln"], 0.10)
        extra.append(f"| {name} | {int(mask.sum())} | {n_mk.mean():.1f} | {lo:+.2f} to {hi:+.2f} | {p95:+.2f} | "
                     f"{share_below:.0%} | {np.corrcoef(r['tn'], r['ln'])[0, 1]:+.2f} | "
                     f"{pct(r['tn'][worst].mean())} vs {pct(r['ln'][worst].mean())} |")
        for cls in ("equity", "energy", "currency"):
            cm = np.array([c == cls for c in p.classes])
            t = p.trades[:, cm]
            cr = mt.portfolio(t, trend_n[:, cm])[mask]
            cr = cr[np.isfinite(cr)]
            classes.append(f"| {name} | {cls} | {int(cm.sum())} | {len(cr)} | {mt.sharpe(cr):+.2f} | {pct(np.mean(cr) * 12)} |")

    names = list(PERIODS)
    result = mt.verdict(checks[names[0]], checks[names[1]])

    data_rows = []
    for m in mt.MARKETS:
        s = daily[m.fred_id]
        gaps = s.index.to_series().diff().dt.days.max()
        tbl = mt.monthly_table(s, p.months)
        valid = int(tbl["close"].notna().sum())
        span = (tbl.index >= s.index.min().to_period("M")) & (tbl.index <= s.index.max().to_period("M"))
        bad = mt.non_positive(FRED / f"{m.fred_id}.csv")
        data_rows.append(f"| {m.name} | `{m.fred_id}`{' (inverted)' if m.invert else ''} | {s.index.min().date()} | "
                         f"{s.index.max().date()} | {len(s):,} | {valid} | {int(span.sum()) - valid} | {int(gaps)} | "
                         f"{', '.join(bad) or '0'} |")

    def mark(ok: bool) -> str:
        return "yes" if ok else "**no**"

    rule_rows = []
    for name in names:
        c = checks[name]
        rule_rows.append(f"| {name} | {c.sharpe:+.2f} {mark(c.sharpe > 0)} | {c.sharpe_low:+.2f} {mark(c.sharpe_low > 0)} | "
                         f"{c.sharpe:+.2f} vs {c.random_p95:+.2f} {mark(c.sharpe > c.random_p95)} | "
                         f"{c.stress_sharpe:+.2f} {mark(c.stress_sharpe > 0)} | {c.months}, {c.avg_markets:.1f} "
                         f"{mark(c.months >= 120 and c.avg_markets >= 4)} |")

    md = ["# Slow multi-market trend vs simple benchmarks — results", "",
          f"Made by `scripts/multimarket_trend_test.py` on {date.today()}. Rules committed before any price was read "
          "(`docs/multimarket_trend_preregistration.md`, commit 3d5fd49). Research only: nothing is traded and no "
          "strategy, risk limit or scanner setting changed. 2025+ was never downloaded.", "",
          f"## Verdict: **{result}**", "",
          "## Words used here", "",
          "- **Sharpe ratio:** average monthly return divided by how much it moves, scaled to a year. Above 0 means it "
          "gained on average; the higher, the steadier. Around 0.5 is what published trend studies report over a century.",
          "- **95% range:** the Sharpe values we would plausibly see if the same kind of history were dealt again "
          "(12-month blocks re-drawn 5,000 times). If the range includes 0, a real edge cannot be told apart from luck.",
          "- **Random direction:** the same markets, sizes and costs, but long or short by coin flip. A real trend rule "
          "should beat at least 95% of those 5,000 coin-flip portfolios.",
          "- **Net** = after the assumed trading costs and financing. **Stress** = with both doubled.", "",
          "## Pass rule check (all must be yes in both periods)", "",
          "| period | net Sharpe > 0 | 95% range low > 0 | above random 95th pct | stress > 0 | months, avg markets |",
          "|---|---|---|---|---|---|"] + rule_rows
    md += ["", "## Returns", "", "| period | portfolio | yearly return | volatility | Sharpe | max drawdown |",
           "|---|---|---:|---:|---:|---:|"] + rows
    md += ["", "## Uncertainty and comparisons (net)", "",
           "| period | months | avg markets | Sharpe 95% range | random 95th pct | random runs beaten | correlation with always long | worst 10% always-long months: trend vs always long |",
           "|---|---:|---:|---|---:|---:|---:|---|"] + extra
    md += ["", "## By asset class (trend, net; reported only, not part of the pass rule)", "",
           "| period | class | markets | months | Sharpe | yearly return |", "|---|---|---:|---:|---:|---:|"] + classes
    md += ["", "## Data checks", "",
           "| market | FRED id | first | last | daily values | valid months | months with < 10 values | longest gap (days) | values <= 0 excluded (Amendment 1) |",
           "|---|---|---|---|---:|---:|---:|---:|---|"] + data_rows
    md += ["", "## Limits", "",
           "- Spot prices and index levels, not tradable CFDs or futures: no dividends, futures roll or currency interest "
           "differences. Profit levels are therefore not what a trading account would have earned.",
           "- Costs and financing are fixed assumptions, not broker quotes.",
           "- When a market sits out a month because of missing data, the cost of closing its position is not charged "
           "(an implementation detail the rules did not specify; it affects only months with fewer than 10 values).",
           "- Trend following was widely reported to be weak in parts of 2011-2024 before this test was written.",
           "- Six of the ten markets are currencies, so currencies carry most of the portfolio's risk.",
           "- Past results do not predict the future, and no strategy here is approved for trading."]
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("verdict:", result)
    print("\n".join(rule_rows), "\n".join(rows), "\n".join(extra), sep="\n")
    print("->", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
