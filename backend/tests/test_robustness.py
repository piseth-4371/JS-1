"""Robustness statistics: shuffling keeps the total, bootstrap detects 'no edge'."""
import numpy as np

from app.backtest.robustness import bootstrap, monte_carlo


def test_monte_carlo_on_known_sequence():
    rs = [-1.0] * 5 + [2.0] * 5
    mc = monte_carlo(rs, risk_pct=1.0, runs=500)
    assert mc.losing_streak_p95 <= 5 and mc.losing_streak_median >= 1
    worst = 1 - 0.99 ** 5                                   # 5 losses in a row at 1% risk
    assert mc.max_dd_p95 <= worst * 100 + 1e-9


def test_bootstrap_clear_edge_vs_no_edge():
    rng = np.random.default_rng(0)
    strong = rng.choice([2.0, -1.0], size=300, p=[0.5, 0.5])        # avg +0.5R
    assert bootstrap(strong).p_no_edge < 0.01
    coin = rng.choice([1.0, -1.0], size=300)                         # avg about 0
    assert bootstrap(coin).p_no_edge > 0.10
    assert bootstrap([]).p_no_edge == 1.0
