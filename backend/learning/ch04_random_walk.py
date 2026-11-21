"""Day 4 — Book chapter 4: Random Walk.  (Study plan: docs/study_plan.md, short plan)

Question for today: can a trading rule LOOK like it works on prices that are pure luck (coin flips)?

Worked example: the answers are filled in below (owner's choice, 2026-11-21). Read each one (one to four lines each).

Check yourself (from the backend folder):
    .\\.venv\\Scripts\\python -m pytest learning\\check_ch04.py -q
Then see the answer on 1,000 made-up "markets":
    .\\.venv\\Scripts\\python learning\\ch04_random_walk.py

Hints:
    A random walk: each step the price goes up or down by the same amount, 50/50, like a coin flip.
    Nothing from the past helps predict the next step. So NO rule can have a real edge on it.
    rng.choice([-1, 1]) gives -1 or +1 at random (rng is a random.Random object).
"""
import random


def random_walk(steps: int, start: float, step_size: float, seed: int) -> list[float]:
    """A list of `steps + 1` prices: `start`, then each next price = previous price + step_size * (+1 or -1).
    Use rng = random.Random(seed) so the same seed always gives the same walk."""
    # Hint: make rng, start a list with `start`, then add `steps` new prices in a loop
    rng = random.Random(seed)                 # same seed -> same coin flips
    prices = [start]
    for _ in range(steps):
        prices.append(prices[-1] + step_size * rng.choice([-1, 1]))
    return prices


def changes(prices: list[float]) -> list[float]:
    """The change from each price to the next: [p1 - p0, p2 - p1, ...]. One shorter than `prices`."""
    # Hint: one line (a list comprehension with range, or zip(prices, prices[1:]))
    return [b - a for a, b in zip(prices, prices[1:])]   # pairs (p0, p1), (p1, p2), ...


def share_up(values: list[float]) -> float:
    """Share of values above 0, from 0 to 1. Empty list -> 0.0."""
    # Hint: like win_rate on day 3
    return sum(1 for v in values if v > 0) / len(values) if values else 0.0


def count_positive(results: list[float]) -> int:
    """How many results are above 0."""
    # Hint: one line
    return sum(1 for r in results if r > 0)


# ---------------------------------------------------------------------------------------------------
# Below: uses YOUR functions. You do not need to edit it.
# ---------------------------------------------------------------------------------------------------
COST = 0.2          # cost per trade, in price points (like a spread)
WORLDS = 1000


def three_up_rule(prices: list[float], hold: int = 5, cost: float = 0.0) -> float:
    """A made-up 'momentum' rule: after 3 rises in a row, buy, and sell `hold` steps later.
    Returns the total result of all its trades, in price points, after `cost` per trade."""
    ch = changes(prices)
    total, i = 0.0, 3
    while i + hold < len(prices):
        if ch[i - 3] > 0 and ch[i - 2] > 0 and ch[i - 1] > 0:
            total += prices[i + hold] - prices[i] - cost
            i += hold
        else:
            i += 1
    return total


def main() -> None:
    walk = random_walk(20, 100.0, 1.0, seed=1)
    print("One random walk (20 steps):", [round(p) for p in walk])
    print(f"Share of up steps in a 10,000-step walk: {share_up(changes(random_walk(10_000, 100, 1, seed=2))):.1%}"
          "  (should be close to 50%)\n")

    no_cost = [three_up_rule(random_walk(500, 100, 1, seed=s)) for s in range(WORLDS)]
    with_cost = [three_up_rule(random_walk(500, 100, 1, seed=s), cost=COST) for s in range(WORLDS)]
    print(f"The '3 rises in a row, then buy' rule on {WORLDS} random markets (500 steps each):")
    print(f"  before costs: looked profitable in {count_positive(no_cost)} of {WORLDS} markets; "
          f"average {sum(no_cost) / WORLDS:+.1f} points; luckiest {max(no_cost):+.1f}")
    print(f"  after {COST} cost per trade: profitable in {count_positive(with_cost)} of {WORLDS}; "
          f"average {sum(with_cost) / WORLDS:+.1f}; luckiest {max(with_cost):+.1f}")
    print("\nThe prices are pure coin flips, so the rule has NO edge. Yet in some markets it 'made money'.")
    print("If you had tested it on only ONE market, you might have believed it works. That is why your")
    print("project compares every strategy with random timing, on many years, before trusting it.")


if __name__ == "__main__":
    main()
