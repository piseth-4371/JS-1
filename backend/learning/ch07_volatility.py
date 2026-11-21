"""Day 7 — Book chapter 7: Volatility.  (Study plan: docs/study_plan.md, short plan)

Question for today: when was the Nasdaq calm, and when was it wild?

Worked example: the answers are filled in below (owner's choice, 2026-11-21). Read each one.

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch07.py -q
Then see the answer on real Nasdaq data (FRED, 1971-2024):
    .\\.venv\\Scripts\\python learning\\ch07_volatility.py

Idea:
    Volatility = how much the price usually moves. We measure it as the STANDARD DEVIATION of daily returns:
    the typical distance of a day's return from the average day.
    Daily volatility x sqrt(252) = yearly volatility (252 trading days in a year; the "square root rule").
"""
import csv
import math
from pathlib import Path


def daily_returns(closes: list[float]) -> list[float]:
    """Return of each day: close / previous close - 1. One shorter than `closes`."""
    return [b / a - 1 for a, b in zip(closes, closes[1:])]


def stdev(values: list[float]) -> float:
    """Sample standard deviation: sqrt( sum((x - mean)^2) / (n - 1) ). Fewer than 2 values -> 0.0."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))


def annualize(daily_vol: float, days: int = 252) -> float:
    """Daily volatility -> yearly volatility with the square root rule."""
    return daily_vol * math.sqrt(days)


def rolling_vol(returns: list[float], window: int = 20) -> list[float]:
    """Yearly volatility of the last `window` days, for every day that has `window` returns before it."""
    return [annualize(stdev(returns[i - window:i])) for i in range(window, len(returns) + 1)]


# ---------------------------------------------------------------------------------------------------
# Below: uses the functions above on real data. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
DATA = Path(__file__).resolve().parent.parent / "data" / "external" / "fred" / "NASDAQCOM.csv"


def read_closes(path: Path = DATA) -> tuple[list[str], list[float]]:
    """Dates and closes from the FRED file; empty or '.' days skipped; 2025+ never read."""
    dates, closes = [], []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            v = row["NASDAQCOM"].strip()
            if row["observation_date"] < "2025-01-01" and v not in ("", "."):
                dates.append(row["observation_date"])
                closes.append(float(v))
    return dates, closes


def main() -> None:
    dates, closes = read_closes()
    rets = daily_returns(closes)
    years: dict[str, list[float]] = {}
    for d, r in zip(dates[1:], rets):
        years.setdefault(d[:4], []).append(r)
    vol = {y: annualize(stdev(rs)) for y, rs in years.items() if len(rs) > 100}
    print(f"Nasdaq Composite {dates[0]} to {dates[-1]}: volatility over all days {annualize(stdev(rets)):.1%} a year\n")
    print("Calmest years:", ", ".join(f"{y} {v:.1%}" for y, v in sorted(vol.items(), key=lambda kv: kv[1])[:3]))
    print("Wildest years:", ", ".join(f"{y} {v:.1%}" for y, v in sorted(vol.items(), key=lambda kv: -kv[1])[:3]))
    rv = rolling_vol(rets)
    i = max(range(len(rv)), key=rv.__getitem__)
    print(f"Wildest 20 days: ending {dates[i + 20]}, {rv[i]:.0%} a year")
    print("\nVolatility clusters: wild days come in groups (crashes), calm in long stretches. A strategy")
    print("tested only in calm years has not seen the market at its worst.")


if __name__ == "__main__":
    main()
