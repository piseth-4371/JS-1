"""Day 14 — Book chapter 14: Kelly criterion.  (Study plan: docs/study_plan.md, short plan)

Question for today: how much should you bet on each strategy? Why does the project say 0%?

Worked example: the answers are filled in below (owner's choice, 2026-11-21). Read each one.

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch14.py -q
Then see the answer on your real backtest trades:
    .\\.venv\\Scripts\\python learning\\ch14_kelly.py

Idea:
    Kelly = the share of your money to risk on each bet that grows your account fastest in the long run.
    f = p - (1 - p) / b      p = chance of winning, b = average win / average loss (the payoff ratio).
    If f is 0 or below, the bet has no edge: the best amount to bet is NOTHING.
    Real traders bet much less than full Kelly (often half), because p and b are only estimates.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch03_expected_value import average, win_rate  # noqa: E402  (reuse day 3)


def payoff_ratio(r_list: list[float]) -> float:
    """Average win divided by the size of the average loss. No wins or no losses -> 0.0."""
    wins = [r for r in r_list if r > 0]
    losses = [r for r in r_list if r <= 0]
    if not wins or not losses or average(losses) == 0:
        return 0.0
    return average(wins) / abs(average(losses))


def kelly(p_win: float, payoff: float) -> float:
    """Kelly fraction f = p - (1 - p) / b. payoff 0 -> 0.0 (cannot bet without a payoff)."""
    if payoff <= 0:
        return 0.0
    return p_win - (1 - p_win) / payoff


def bet_size(f: float, fraction: float = 0.5) -> float:
    """What to actually risk: a `fraction` of Kelly (half Kelly by default), never below 0."""
    return max(0.0, f * fraction)


# ---------------------------------------------------------------------------------------------------
# Below: uses the functions above on real data. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
TRADES = Path(__file__).resolve().parent.parent / "data" / "backtest_trades.csv"


def main() -> None:
    by: dict[str, list[float]] = {}
    with open(TRADES, newline="") as fh:
        for row in csv.DictReader(fh):
            by.setdefault(row["strategy"], []).append(float(row["r"]))
    print(f"{'strategy (all 2019-2024)':24s} {'win %':>6s} {'payoff':>7s} {'Kelly':>7s} {'half Kelly bet':>15s}")
    for name, rs in sorted(by.items()):
        p, b = win_rate(rs), payoff_ratio(rs)
        f = kelly(p, b)
        print(f"{name:24s} {p:>6.1%} {b:>7.2f} {f:>+7.1%} {bet_size(f):>15.1%}")
    print(f"\nCoin flip that pays 2:1 (p=50%, b=2): Kelly {kelly(0.5, 2.0):.0%} -> half Kelly {bet_size(kelly(0.5, 2.0)):.0%}")
    print("Every strategy here has Kelly at or below 0, so the best bet is 0%: that is the project's answer.")


if __name__ == "__main__":
    main()
