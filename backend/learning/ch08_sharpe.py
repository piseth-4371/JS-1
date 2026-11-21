"""Day 8 — Book chapter 8: Sharpe ratio.  (Study plan: docs/study_plan.md, short plan)

Question for today: were you PAID for the risk? Buy-and-hold Nasdaq vs each strategy, 2019-2024.

Worked example: the answers are filled in below (owner's choice, 2026-11-21). Read each one.

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch08.py -q
Then see the answer:
    .\\.venv\\Scripts\\python learning\\ch08_sharpe.py

Idea:
    Sharpe = (average return - safe return) / volatility, both per year.
    It is "reward per unit of risk". Above 1 is very good, 0.5 is fair, 0 or below = not paid for the risk.
"""
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch07_volatility import daily_returns, read_closes, stdev  # noqa: E402  (reuse day 7)


def sharpe(returns: list[float], periods_per_year: int, safe_rate: float = 0.0) -> float:
    """Yearly Sharpe ratio of returns measured `periods_per_year` times a year (252 daily, 12 monthly).
    safe_rate is a yearly rate (0.02 = 2%). Volatility 0 -> 0.0."""
    if len(returns) < 2:
        return 0.0
    mean_year = sum(returns) / len(returns) * periods_per_year
    vol_year = stdev(returns) * math.sqrt(periods_per_year)
    return (mean_year - safe_rate) / vol_year if vol_year > 0 else 0.0


def monthly_account_returns(trades: list[tuple[str, float]], risk_pct: float = 0.5) -> dict[str, float]:
    """{'YYYY-MM': return of the paper account that month} from (date, R) trades at `risk_pct` % risk each.
    A trade of R moves the account by risk_pct / 100 * R (simple, not compounded within the month)."""
    out: dict[str, float] = {}
    for d, r in trades:
        out[d[:7]] = out.get(d[:7], 0.0) + risk_pct / 100 * r
    return out


# ---------------------------------------------------------------------------------------------------
# Below: uses the functions above on real data. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
TRADES = Path(__file__).resolve().parent.parent / "data" / "backtest_trades.csv"
SAFE = 0.02    # about what cash paid on average 2019-2024 (an assumption)


def main() -> None:
    dates, closes = read_closes()
    keep = [i for i, d in enumerate(dates) if d >= "2019-01-01"]
    bh = daily_returns([closes[i] for i in [keep[0] - 1] + keep])
    print(f"Buy and hold Nasdaq Composite 2019-2024: Sharpe {sharpe(bh, 252, SAFE):+.2f}\n")

    by_strategy: dict[str, list[tuple[str, float]]] = {}
    with open(TRADES, newline="") as fh:
        for row in csv.DictReader(fh):
            by_strategy.setdefault(row["strategy"], []).append((row["ny_date"], float(row["r"])))
    months = [f"{y}-{m:02d}" for y in range(2019, 2025) for m in range(1, 13)]
    print(f"{'strategy (0.5% risk per trade)':34s} {'Sharpe':>7s}")
    for name, trades in sorted(by_strategy.items()):
        mr = monthly_account_returns(trades)
        series = [mr.get(m, 0.0) for m in months]          # months with no trade = 0% return
        print(f"{name:34s} {sharpe(series, 12, SAFE):>+7.2f}")
    print("\nA Sharpe at or below 0 means the strategy did not even beat holding cash for the risk it took.")


if __name__ == "__main__":
    main()
