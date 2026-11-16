import math

import numpy as np
import pytest

from app.backtest.report_card import kelly_fraction, longest_streak, max_drawdowns, report


def test_kelly_matches_the_book_for_even_money():
    # Book ch 14: win 60 % at even money -> Kelly 20 %.
    r = np.array([1.0] * 60 + [-1.0] * 40)
    assert kelly_fraction(r) == pytest.approx(0.20, abs=0.002)


def test_kelly_two_to_one():
    # Book 14.2: pays 2 to 1, wins 40 % -> Kelly 10 %.
    r = np.array([2.0] * 40 + [-1.0] * 60)
    assert kelly_fraction(r) == pytest.approx(0.10, abs=0.002)


def test_kelly_is_zero_without_edge():
    assert kelly_fraction(np.array([1.0, -1.0, -1.0, 2.0, -1.2])) == 0.0   # avg -0.04
    assert kelly_fraction(np.array([1.0, -1.0])) == 0.0                    # avg exactly 0


def test_longest_losing_streak():
    assert longest_streak(np.array([1, -1, -1, 2, -1, -1, -1, 0.5])) == 3
    assert longest_streak(np.array([1.0, 2.0])) == 0


def test_max_drawdown():
    # Book ch 9: +50 % then -50 % -> ends at 75 from a peak of 150, a 50 % drawdown.
    assert max_drawdowns(np.array([[100, 150, 75.0]]))[0] == pytest.approx(0.5)


def test_losing_strategy_card():
    rng = np.random.default_rng(1)
    r = rng.choice([2.0, -1.0], size=2000, p=[0.30, 0.70])      # EV = 0.6 - 0.7 = -0.1R
    c = report(r, years=4)
    assert c.avg_r < 0 and c.kelly_pct == 0 and c.growth_year_pct < 0
    assert c.p_no_edge > 0.95 and c.verdict.startswith("LOSES")
    assert c.trades_per_year == 500
    assert c.sharpe_year == pytest.approx(c.sharpe_trade * math.sqrt(500), abs=0.01)


def test_winning_strategy_card_and_seeded_monte_carlo():
    rng = np.random.default_rng(2)
    r = rng.choice([2.0, -1.0], size=2000, p=[0.45, 0.55])      # EV = +0.35R
    a, b = report(r, years=4), report(r, years=4)
    assert a == b                                                 # fixed seed: same numbers every run
    assert a.kelly_pct > 0 and a.verdict.startswith("EDGE") and a.mc_loss_chance_pct < 5
    assert a.mc_p10_pct <= a.mc_median_pct <= a.mc_p90_pct


def test_more_risk_does_not_fix_a_negative_edge():
    rng = np.random.default_rng(3)
    r = rng.choice([2.0, -1.0], size=1000, p=[0.30, 0.70])
    small, big = report(r, 2, risk_pct=0.5), report(r, 2, risk_pct=2.0)
    assert big.growth_year_pct < small.growth_year_pct < 0
    assert big.mc_worst5_max_dd_pct > small.mc_worst5_max_dd_pct


def test_needs_data():
    with pytest.raises(ValueError):
        report([1.0], years=1)


def test_report_family_and_week_fields():
    import numpy as np
    from app.backtest.report_card import report
    r = np.array([1.0, -1.0, 2.0, -1.0, 0.5] * 20)
    plain = report(r, 1.0)
    assert plain.ci95_week_low is None and plain.tests == 1
    assert abs(plain.ci_low_family - plain.ci95_low) < 0.002
    c = report(r, 1.0, groups=np.arange(100) // 5, tests=36)
    assert c.ci_low_family < c.ci95_low and c.ci95_week_low is not None
    assert c.verdict == plain.verdict          # family width is reported, the verdict rule is unchanged
