"""Day 1 — Book chapter 1: Returns.  (Study plan: docs/study_plan.md)

Your job: replace every `raise NotImplementedError` with real code (one or two lines each).

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch01.py -q
Then see the answers on real NAS100 data:
    .\\.venv\\Scripts\\python learning\\ch01_returns.py

Hints: the book's two formulas are
    R = S1 / S0 - 1            (simple return)
    r = math.log(S1 / S0)      (log return)
"""
import math
import sys
from pathlib import Path


def simple_return(s0: float, s1: float) -> float:
    """Price goes from s0 to s1. Return as a decimal: 0.10 means +10 %."""
    # TODO: one line, using the book's formula
    raise NotImplementedError


def log_return(s0: float, s1: float) -> float:
    """The natural log of the new price over the old price."""
    # TODO: one line, use math.log
    raise NotImplementedError


def total_from_simple(returns: list[float]) -> float:
    """Combine several simple returns into ONE total return.
    Example: +10 % then -10 % -> -1 %  (NOT 0 %). Simple returns MULTIPLY: (1 + R1) * (1 + R2) - 1."""
    # TODO: start with growth = 1.0, multiply by (1 + r) for each r, then subtract 1
    raise NotImplementedError


def total_from_log(log_returns: list[float]) -> float:
    """Combine several log returns into ONE total log return. Log returns ADD UP."""
    # TODO: one line
    raise NotImplementedError


def needed_to_recover(loss: float) -> float:
    """After a loss (e.g. -0.25 for -25 %), what simple return gets you back to the start?
    Book question 1.1: $80 -> $60 is -25 %, and $60 -> $80 needs +33.3 %."""
    # TODO: think of it as prices: start 1, after the loss 1 + loss, back to 1
    raise NotImplementedError


# ---------------------------------------------------------------------------------------------------
# Below: uses YOUR functions on real NAS100 daily closes (HistData 2019-2024). You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from datetime import datetime, timezone

    from app.backtest.vol_filter import daily_closes
    from app.core.features import load_m1
    from app.core.sources import histdata_source as hd

    start = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    print("Loading NAS100 1-minute bars 2019-2024 (about 30 s)...")
    closes = daily_closes(load_m1(hd.SOURCE, hd.INSTRUMENT, start, end))
    days, prices = list(closes.index), list(closes.values)
    print(f"{len(prices)} trading days, {days[0]} -> {days[-1]}\n")

    simple = [simple_return(prices[i - 1], prices[i]) for i in range(1, len(prices))]
    logs = [log_return(prices[i - 1], prices[i]) for i in range(1, len(prices))]
    worst = min(range(len(simple)), key=simple.__getitem__)
    best = max(range(len(simple)), key=simple.__getitem__)
    print(f"Worst day: {days[worst + 1]}  {simple[worst]:+.2%}  -> needed {needed_to_recover(simple[worst]):+.2%} to recover")
    print(f"Best day:  {days[best + 1]}  {simple[best]:+.2%}")
    print(f"\nWhole period, simple return:         {simple_return(prices[0], prices[-1]):+.1%}")
    print(f"Daily simple returns COMBINED:       {total_from_simple(simple):+.1%}   (same as above)")
    print(f"Daily simple returns just ADDED:     {sum(simple):+.1%}   (wrong! simple returns do not add)")
    print(f"Daily log returns ADDED:             {total_from_log(logs):+.4f}")
    print(f"log(last / first):                   {log_return(prices[0], prices[-1]):+.4f}   (same: log returns add)")


if __name__ == "__main__":
    main()
