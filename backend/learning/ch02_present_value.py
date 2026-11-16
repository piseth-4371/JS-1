"""Day 2 — Book chapter 2: Interest and Present Value.  (Study plan: docs/study_plan.md)

Question for today: would your $1,000 paper account have done better in a SAVINGS ACCOUNT at 4 %
than with any of the 7 NAS100 strategies (2019-2024, 0.5 % risk per trade)?

Your job: replace every TODO line `raise NotImplementedError` with real code (one or two lines each).

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch02.py -q
Then see the answer on your real backtest trades:
    .\\.venv\\Scripts\\python learning\\ch02_present_value.py

Hints, from the book:
    FV = PV * (1 + i) ** T        money grows by the factor (1 + i) once every year
    PV = FV / (1 + i) ** T        "discounting": bring a future amount back to today
"""
import sys
from pathlib import Path


def future_value(pv: float, rate: float, years: float) -> float:
    """$pv saved today at `rate` a year (0.04 = 4 %), with interest on interest, after `years`."""
    # TODO: one line, the book's FV formula
    raise NotImplementedError


def present_value(fv: float, rate: float, years: float) -> float:
    """What $fv paid in `years` is worth TODAY, at `rate` a year."""
    # TODO: one line, the book's PV formula
    raise NotImplementedError


def account_after_trades(start: float, r_list: list[float], risk_pct: float) -> float:
    """Paper account: each trade risks `risk_pct` % of the CURRENT balance and returns r (in R).
    A trade of r = +2 at 0.5 % risk grows the balance by 1 %; r = -1 shrinks it by 0.5 %.
    So after each trade:  balance = balance * (1 + risk_pct / 100 * r)"""
    # TODO: start with balance = start, apply every trade in order, return the balance
    raise NotImplementedError


def yearly_rate(start: float, end: float, years: float) -> float:
    """The constant yearly rate that turns `start` into `end` in `years` (the "compound annual growth rate").
    It is the FV formula solved for i:  end = start * (1 + i) ** years."""
    # TODO: one line. Hint: x ** (1 / years) is the "years-th root" of x
    raise NotImplementedError


# ---------------------------------------------------------------------------------------------------
# Below: uses YOUR functions on the saved backtest trades. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
START, SAVINGS_RATE, YEARS, RISK = 1000.0, 0.04, 6, 0.5


def main() -> None:
    import csv
    path = Path(__file__).resolve().parent.parent / "data" / "backtest_trades.csv"
    trades: dict[str, list[float]] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            trades.setdefault(row["strategy"], []).append(float(row["r"]))

    bank = future_value(START, SAVINGS_RATE, YEARS)
    print(f"Savings account: ${START:,.0f} at {SAVINGS_RATE:.0%} for {YEARS} years -> ${bank:,.2f}\n")
    print(f"{'strategy (2019-2024, ' + str(RISK) + '% risk)':40s} {'end balance':>12s} {'per year':>9s} {'worth today*':>13s}  vs savings")
    for name, rs in sorted(trades.items()):
        end = account_after_trades(START, rs, RISK)
        rate = yearly_rate(START, end, YEARS)
        today = present_value(end, SAVINGS_RATE, YEARS)
        verdict = "better" if end > bank else "WORSE"
        print(f"{name:40s} ${end:>11,.2f} {rate:>+9.2%} ${today:>12,.2f}  {verdict}")
    print(f"\n* 'worth today' = the end balance discounted at the {SAVINGS_RATE:.0%} savings rate. "
          f"Above ${START:,.0f} = beat the bank.")
    print(f"\nBook question 2.2: $500 in 2 years is worth ${present_value(500, 0.05, 2):,.2f} today at 5 %, "
          f"${present_value(500, 0.08, 2):,.2f} at 8 %.")


if __name__ == "__main__":
    main()
