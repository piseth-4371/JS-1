"""Measure how NAS100, gold and BTC usually move around each news type (docs/news_effect_preregistration.md).

    .venv\\Scripts\\python scripts\\news_effect.py

Writes app/calendar/news_effect.json (used by the dashboard and Telegram) and docs/news_effect_report.md.
Measurement only: no trading rule, blackout, risk limit or scanner.QUALIFIED is changed.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backtest import news_effect as ne  # noqa: E402
from app.core import news  # noqa: E402
from app.core.features import load_m1  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "app" / "calendar" / "news_effect.json"
OUT_MD = ROOT.parent / "docs" / "news_effect_report.md"
MARKETS = [("nas100", "NAS100", "histdata", "NSXUSD"), ("gold", "Gold", "histdata", "XAUUSD"),
           ("btc", "BTC", "binance", "BTCUSDT")]
START = int(datetime(2018, 12, 1, tzinfo=news.NY).timestamp())     # room for controls before the first event
END = int(datetime(2025, 1, 1, tzinfo=news.NY).timestamp())        # 2025+ locked
FIRST_EVENT = int(datetime(2019, 1, 1, tzinfo=news.NY).timestamp())


def main() -> int:
    events = [e for e in news.load_events() if FIRST_EVENT <= e.ts < END]
    all_days = {datetime.fromtimestamp(e.ts, news.NY).date() for e in news.load_events()}
    result: dict = {"made": date.today().isoformat(), "period": "2019-2024", "window_minutes": ne.WINDOW_MIN,
                    "rules": "docs/news_effect_preregistration.md", "effects": {}}
    rows = []
    for key, label, source, symbol in MARKETS:
        m1 = load_m1(source, symbol, START, END)
        b = ne.Bars(m1["ts"].to_numpy(), m1["h"].to_numpy(float), m1["l"].to_numpy(float), m1["c"].to_numpy(float))
        for name in news.EVENTS:
            ms, skipped = ne.measure(b, [e for e in events if e.name == name], all_days)
            s = ne.summarize(ms, skipped)
            result["effects"].setdefault(name, {})[key] = s
            rows.append((name, label, s))
            print(name, label, s)
    OUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{x:.2f}%"
    md = ["# News effect on NAS100, gold and BTC — results", "",
          f"Made by `scripts/news_effect.py` on {result['made']}. Rules were committed first: "
          "`docs/news_effect_preregistration.md`. Measurement only: nothing about trading changed.", "",
          "**30-min range** = high − low in the 30 minutes after the release, as % of price (median over events). "
          "**Normal** = the same at the same New York time on nearby weekdays without news. "
          "**× normal** = how many times bigger news makes it. **Move** = how far price ended up after 30 minutes "
          "(either direction).", "",
          "| news | market | events | 30-min range on news | normal | × normal | move after 30 min | events > 2× their normal |",
          "|---|---|---:|---:|---:|---:|---:|---:|"]
    for name, label, s in rows:
        if not s["n"]:
            md.append(f"| {name} | {label} | 0 (skipped {s['skipped']}) | — | — | — | — | — |")
            continue
        md.append(f"| {name} | {label} | {s['n']} (skipped {s['skipped']}) | {pct(s['news_range_pct'])} | "
                  f"{pct(s['normal_range_pct'])} | **{s['effect_x']:.1f}×** | {pct(s['news_move_pct'])} | "
                  f"{s['share_over_2x']:.0%} |")
    md += ["", "## Limits",
           "- HistData NAS100/gold prices are not Exness prices; BTC trades 24/7.",
           "- 2019-2024 only. A typical size says nothing about the direction, and single releases can be far bigger.",
           "- Not a trading rule: the ±30-minute news blackout stays exactly as it was."]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
