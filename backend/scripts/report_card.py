"""Strategy report card (read-only): quant-finance numbers for every saved backtest trade.

Reads data/backtest_trades.csv (NAS100) and data/backtest_trades_btc.csv (BTC), written by
run_backtest.py, and writes docs/report_card.md. Same splits as the backtest:
development 2019-2022, validation 2023-2024. Nothing here changes a strategy or places a trade.

    .\\.venv\\Scripts\\python scripts\\report_card.py
    .\\.venv\\Scripts\\python scripts\\report_card.py --risk 1.0     (Monte Carlo / growth at 1 % per trade)
"""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from app.backtest.report_card import report  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SPLITS = [("development", "2019-01-01", "2022-12-31", 4.0), ("validation", "2023-01-01", "2024-12-31", 2.0)]
FILES = [("NAS100", ROOT / "data" / "backtest_trades.csv"), ("BTC weekends", ROOT / "data" / "backtest_trades_btc.csv")]


def pct(x: float) -> str:
    return f"{x:+.1f}%"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--risk", type=float, default=0.5, help="risk %% per trade for growth and Monte Carlo (project default 0.5)")
    p.add_argument("--out", type=Path, default=ROOT.parent / "docs" / "report_card.md")
    a = p.parse_args()

    out = [f"# Strategy report card ({date.today()})", "",
           "Quant-finance numbers for every saved backtest trade, after costs. Made by `scripts/report_card.py`",
           "from `data/backtest_trades*.csv`; ideas from the book *Quantitative Finance From Scratch* (chapter numbers below).",
           f"Growth and Monte Carlo use **{a.risk:g}% risk per trade**. Gold trades were never saved to a file, so gold is not here",
           "(its results are in `gold_report.md`). These numbers MEASURE an edge; they cannot create one.", "",
           "## How to read it", "",
           "- **Avg R** (ch 3, expected value): what one trade makes on average. Below 0 = loses money over time.",
           "- **95% range** (ch 15, standard error): where the true average probably lies. If the whole range is below 0, the loss is real, not bad luck.",
           "- **Luck chance** (ch 4): how often reshuffled trades average 0R or worse. Near 100% = no edge.",
           "- **Sharpe/yr** (ch 8): return per unit of swing per year. Good funds are around +0.5 to +1. Negative = paid nothing for the risk.",
           f"- **Growth/yr** (ch 9, volatility drag): what the account really keeps per year at {a.risk:g}% risk.",
           "- **Kelly %** (ch 14): best % of the account to risk per trade. **0 means: do not trade it.**",
           "- **Worst 5%** (ch 16-17, expected shortfall): average R of the worst 5% of trades.",
           "- **MC** (ch 15, Monte Carlo): 10,000 reshuffled years of trades. Loss chance = share of years that end below the start; DD = largest fall from a peak.", ""]
    shown = 0
    for market, path in FILES:
        if not path.exists():
            out += [f"## {market}", "", f"No trade file ({path.name}). Run `scripts/run_backtest.py` first.", ""]
            continue
        df = pd.read_csv(path)
        for split, start, end, years in SPLITS:
            part = df[(df["ny_date"] >= start) & (df["ny_date"] <= end)]
            out += [f"## {market} — {split} {start[:4]}-{end[:4]}", "",
                    "| strategy | trades | avg R | 95% range | luck chance | Sharpe/yr | growth/yr | Kelly % | worst 5% | MC loss chance | MC median | MC bad DD (95th) | verdict |",
                    "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
            for name, g in part.groupby("strategy"):
                if len(g) < 2:
                    continue
                c = report(g["r"].to_numpy(), years, a.risk)
                shown += 1
                out.append(f"| {name} | {c.trades} | {c.avg_r:+.3f} | {c.ci95_low:+.2f} to {c.ci95_high:+.2f} | "
                           f"{c.p_no_edge * 100:.0f}% | {c.sharpe_year:+.2f} | {pct(c.growth_year_pct)} | {c.kelly_pct:.2f} | "
                           f"{c.es5_r:+.2f} | {c.mc_loss_chance_pct:.0f}% | {pct(c.mc_median_pct)} | {c.mc_worst5_max_dd_pct:.1f}% | {c.verdict} |")
                print(f"{market:12s} {split:11s} {name:28s} avgR {c.avg_r:+.3f}  Kelly {c.kelly_pct:5.2f}%  {c.verdict}")
            out.append("")
    out += ["## What it means", "",
            "- A strategy is only worth watching if its **95% range is above 0 in BOTH periods** and Kelly is above 0 in both.",
            "- Kelly 0% everywhere is the maths saying what the backtests already said: these rules have no edge after costs.",
            "- A bigger risk % never fixes a negative average; it only makes the losses and drawdowns larger (try `--risk 1.0`).",
            "- This report is a measuring tool. A new signal still needs its own pre-registered test before it may enter `scanner.QUALIFIED`.", ""]
    a.out.write_text("\n".join(out), encoding="utf-8")
    print(f"\n{shown} report cards written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
