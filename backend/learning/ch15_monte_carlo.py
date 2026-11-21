"""Day 15 — Book chapter 15: Monte Carlo simulation.  (Study plan: docs/study_plan.md, short plan)

Question for today: what is the WORST year your $1,000 paper account should expect?

Worked example: the answers are filled in below (owner's choice, 2026-11-21). Read each one.

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch15.py -q
Then see the answer:
    .\\.venv\\Scripts\\python learning\\ch15_monte_carlo.py

Idea:
    Monte Carlo = run the future thousands of times with random draws, then look at the spread of results.
    Here: draw trades at random (with replacement) from a strategy's real backtest trades, play one "year"
    of them on the paper account, repeat 10,000 times. The worst 5% of years shows what bad luck looks like.
"""
import csv
import random
from pathlib import Path


def play_year(r_list: list[float], trades: int, start: float, risk_pct: float, rng: random.Random) -> float:
    """End balance after `trades` trades drawn at random from r_list, each risking risk_pct % of the
    CURRENT balance (balance *= 1 + risk_pct/100 * r)."""
    balance = start
    for _ in range(trades):
        balance *= 1 + risk_pct / 100 * rng.choice(r_list)
    return balance


def simulate(r_list: list[float], trades: int, start: float, risk_pct: float, runs: int, seed: int) -> list[float]:
    """End balances of `runs` simulated years, sorted from worst to best."""
    rng = random.Random(seed)
    return sorted(play_year(r_list, trades, start, risk_pct, rng) for _ in range(runs))


def percentile(sorted_values: list[float], q: float) -> float:
    """The value below which a share q (0 to 1) of the sorted values falls (nearest rank)."""
    i = min(len(sorted_values) - 1, max(0, int(q * len(sorted_values))))
    return sorted_values[i]


# ---------------------------------------------------------------------------------------------------
# Below: uses the functions above on real data. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
TRADES = Path(__file__).resolve().parent.parent / "data" / "backtest_trades.csv"
START, RISK, RUNS = 1000.0, 0.5, 10_000


def main() -> None:
    by: dict[str, list[float]] = {}
    with open(TRADES, newline="") as fh:
        for row in csv.DictReader(fh):
            by.setdefault(row["strategy"], []).append(float(row["r"]))
    print(f"$1,000 paper account, {RISK}% risk per trade, {RUNS:,} simulated years per strategy\n")
    print(f"{'strategy':24s} {'trades/yr':>9s} {'worst 5%':>10s} {'median':>10s} {'best 5%':>10s} {'years lost':>10s}")
    for name, rs in sorted(by.items()):
        per_year = round(len(rs) / 6)                       # 2019-2024 = 6 years
        ends = simulate(rs, per_year, START, RISK, RUNS, seed=11)
        lost = sum(1 for e in ends if e < START) / len(ends)
        print(f"{name:24s} {per_year:>9d} ${percentile(ends, 0.05):>9,.0f} ${percentile(ends, 0.5):>9,.0f} "
              f"${percentile(ends, 0.95):>9,.0f} {lost:>10.0%}")
    print("\n'Worst 5%' = 1 year in 20 ends at or below this. Even a strategy with an edge has bad years; a")
    print("strategy WITHOUT an edge loses in most simulated years. Small risk per trade keeps the worst year small.")


if __name__ == "__main__":
    main()
