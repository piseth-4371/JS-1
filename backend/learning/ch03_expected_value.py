"""Day 3 — Book chapter 3: Expected Value.  (Study plan: docs/study_plan.md, short plan)

Question for today: which of the 7 NAS100 strategies are "roulette", meaning bets that lose
money ON AVERAGE, so the more you play, the more you lose?

Your job: replace every TODO line `raise NotImplementedError` with real code (one to three lines each).

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch03.py -q
Then see the answer on your real backtest trades:
    .\\.venv\\Scripts\\python learning\\ch03_expected_value.py

Hints:
    Expected value = what one bet pays ON AVERAGE if you could repeat it forever.
    EV = P(win) * average win  +  P(loss) * average loss        (average loss is a NEGATIVE number)
    Example: roulette, bet $1 on red. P(win) = 18/37, win +$1; P(loss) = 19/37, loss -$1.
             EV = 18/37 * 1 + 19/37 * (-1) = -1/37 = about -$0.027 per bet. Small, but always negative.
"""


def average(values: list[float]) -> float:
    """The plain average (mean) of a list. Return 0.0 for an empty list."""
    # TODO: sum divided by count, but watch out for an empty list
    raise NotImplementedError


def win_rate(r_list: list[float]) -> float:
    """Share of trades with r > 0, as a number from 0 to 1 (0.4 = 40 %). Empty list -> 0.0."""
    # TODO: count the winners, divide by the number of trades
    raise NotImplementedError


def expected_value(p_win: float, avg_win: float, avg_loss: float) -> float:
    """EV of one bet. `avg_loss` is negative (for example -1.0). P(loss) = 1 - p_win."""
    # TODO: one line, the formula in the hints above
    raise NotImplementedError


def breakeven_win_rate(avg_win: float, avg_loss: float) -> float:
    """The win rate that makes EV exactly 0. Solve  p * avg_win + (1 - p) * avg_loss = 0  for p.
    Example: win +2R, lose -1R  ->  you need to win only 1/3 of the time to break even."""
    # TODO: one line of algebra. Try it on paper first.
    raise NotImplementedError


def is_roulette(r_list: list[float]) -> bool:
    """True if the strategy loses on average (its average R is below 0)."""
    # TODO: one line, using a function you already wrote
    raise NotImplementedError


# ---------------------------------------------------------------------------------------------------
# Below: uses YOUR functions on the saved backtest trades. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
PERIODS = {"dev 2019-22": ("2019", "2022"), "val 2023-24": ("2023", "2024")}


def main() -> None:
    import csv
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "data" / "backtest_trades.csv"
    trades: dict[tuple[str, str], list[float]] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            year = row["ny_date"][:4]
            for period, (a, b) in PERIODS.items():
                if a <= year <= b:
                    trades.setdefault((row["strategy"], period), []).append(float(row["r"]))

    print(f"{'strategy':22s} {'period':12s} {'trades':>6s} {'win %':>6s} {'avg win':>8s} {'avg loss':>9s}"
          f" {'need %':>7s} {'EV (R)':>7s}  verdict")
    for (name, period), rs in sorted(trades.items()):
        wins = [r for r in rs if r > 0]
        losses = [r for r in rs if r <= 0]
        p, aw, al = win_rate(rs), average(wins), average(losses)
        ev = expected_value(p, aw, al)
        need = breakeven_win_rate(aw, al) if aw > 0 and al < 0 else float("nan")
        verdict = "ROULETTE (loses on average)" if is_roulette(rs) else "positive (not proof!)"
        print(f"{name:22s} {period:12s} {len(rs):>6d} {p:>6.1%} {aw:>+8.2f} {al:>+9.2f} {need:>7.1%} {ev:>+7.3f}  {verdict}")

    print("\n'need %' = the win rate needed to break even with that strategy's own average win and loss.")
    print("Win % below 'need %' = roulette. A positive EV in ONE period only is not an edge (Lesson 3).")
    print(f"\nRoulette check: bet $1 on red, EV = {expected_value(18 / 37, 1.0, -1.0):+.4f} dollars per bet.")


if __name__ == "__main__":
    main()
