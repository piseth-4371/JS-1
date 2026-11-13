"""Test the "auto-switch" idea: each Monday pick the strategy that did best recently.

Compares 6 pre-declared selector versions with every fixed strategy, per split.
Out-of-sample (2025+) stays locked, exactly like run_backtest.py.

  .\\.venv\\Scripts\\python scripts\\run_selector.py
  .\\.venv\\Scripts\\python scripts\\run_selector.py --start 2019-01-01 --end 2019-12-01 --no-splits
"""
import argparse
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.engine import Costs, run  # noqa: E402
from app.backtest.metrics import compute  # noqa: E402
from app.backtest.selector import walk_forward  # noqa: E402
from app.core.features import build_frame, load_m1  # noqa: E402
from app.core.markets import BTCUSD, NAS100  # noqa: E402
from app.core.risk import RiskSettings  # noqa: E402
from app.core.sources import binance_source as bn  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.strategies import ALL  # noqa: E402
from app.repository import init_db  # noqa: E402

SPLITS = [("development", date(2019, 1, 1), date(2023, 1, 1)),
          ("validation", date(2023, 1, 1), date(2025, 1, 1))]
# Fixed BEFORE seeing results: 3 lookbacks x 2 criteria = 6 versions.
VARIANTS = [(crit, days) for crit in ("avg_r", "win_rate") for days in (30, 91, 182)]


def ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2025, 1, 1))
    p.add_argument("--no-splits", action="store_true")
    p.add_argument("--market", choices=["nas100", "btc"], default="nas100")
    p.add_argument("--min-trades", type=int, default=10)
    a = p.parse_args()
    end = min(a.end, date(2025, 1, 1))            # out-of-sample stays locked
    mk = BTCUSD if a.market == "btc" else NAS100
    src, sym = (bn.SOURCE, bn.SYMBOL) if mk is BTCUSD else (dk.SOURCE, dk.INSTRUMENT)

    init_db()
    t0 = time.time()
    m1 = load_m1(src, sym, ts(a.start), ts(end))
    if m1.empty:
        print(f"No {src} data in that range.")
        return 1
    first = datetime.fromtimestamp(m1.ts.iloc[0], timezone.utc).date()
    last = datetime.fromtimestamp(m1.ts.iloc[-1], timezone.utc).date()
    frame = build_frame(m1, hold_mask=mk.hold_mask)
    settings = RiskSettings()
    costs = mk.costs if mk is BTCUSD else Costs()
    print(f"{mk.label}: {len(m1):,} bars {first} -> {last}; costs spread {costs.spread} + slip {costs.slippage} pts, "
          f"fee {costs.fee_pct}%")

    by_strategy = {name: run(cls(), frame, settings, costs).trades for name, cls in ALL.items() if mk.owns(name)}
    if len(by_strategy) < 2:
        print("Need at least 2 strategies for this market to switch between.")
        return 1

    rows = []   # (name, split, stats, extra)
    splits = [("all", a.start, last)] if a.no_splits else SPLITS

    def add(name, trades, extra=""):
        for split, s0, s1 in splits:
            s1 = min(s1, last)
            if s0 >= s1:
                continue
            tr = [t for t in trades if s0 <= t.ny_date < s1]
            rows.append((name, split, compute(tr, max((s1 - s0).days / 30.44, 0.1), settings.risk_pct), extra))

    for name, trades in by_strategy.items():
        add(name, trades)
    for crit, days in VARIANTS:
        res = walk_forward(by_strategy, a.start, last, days, crit, a.min_trades)
        counts = res.pick_counts()
        idle = counts.get("(no trade)", 0) / max(len(res.picks), 1) * 100
        top = ", ".join(f"{k} {v}" for k, v in counts.most_common(3) if k != "(no trade)")
        add(res.name, res.trades, f"idle {idle:.0f}% of weeks; picked: {top}")

    hdr = f"{'version':<28}{'split':<13}{'trades':>7}{'win%':>7}{'avgR':>7}{'PF':>6}{'totalR':>8}{'maxDD%':>8}  note"
    print("\n" + hdr + "\n" + "-" * len(hdr))
    for name, split, st, extra in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        print(f"{name:<28}{split:<13}{st.n:>7}{st.win_rate:>7.1f}{st.expectancy_r:>7.2f}{pf:>6}{st.total_r:>8.1f}"
              f"{st.max_dd_pct:>8.1f}  {st.note} {extra}".rstrip())

    md = [f"# Auto-switch (strategy selector) test — generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
          f"- Market: {mk.label}; data {src} {sym} {first} → {last}; out-of-sample (2025+) locked",
          "- Each Monday the selector looks only at trades that closed BEFORE that Monday and picks one strategy "
          f"for the week (min {a.min_trades} past trades). `avg_r` stays out if the best average R is ≤ 0; "
          "`win_rate` always picks the highest win rate.",
          "- 6 versions were fixed before running (1, 3, 6 month lookback × 2 criteria). All are shown.", "",
          "| version | split | trades | win % | avg R | PF | total R | max DD % | note |",
          "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for name, split, st, extra in rows:
        pf = f"{st.profit_factor:.2f}" if st.profit_factor != float("inf") else "inf"
        md.append(f"| {name} | {split} | {st.n} | {st.win_rate:.1f} | {st.expectancy_r:.2f} | {pf} | {st.total_r:.1f} | "
                  f"{st.max_dd_pct:.1f} | {(st.note + ' ' + extra).strip()} |")
    md += ["", "**Pass rule:** the auto-switch is only worth using if a version beats the best FIXED strategy on "
           "average R in BOTH development and validation, with ≥ 100 trades each. Past results do not guarantee future results."]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / f"selector_report{'_btc' if mk is BTCUSD else ''}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nReport written to {out}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
