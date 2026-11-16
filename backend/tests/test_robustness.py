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


# --- audit 2026-11-16: dependence and multiple testing ---------------------------------------------
def test_cluster_bootstrap_wider_than_iid_when_trades_in_a_week_move_together():
    import numpy as np
    from app.backtest.robustness import bootstrap, cluster_bootstrap
    rng = np.random.default_rng(0)
    week_effect = rng.normal(0, 1, 60)
    rs = np.repeat(week_effect, 10) + rng.normal(0, 0.1, 600)     # 60 weeks x 10 strongly linked trades
    weeks = np.repeat(np.arange(60), 10)
    iid = bootstrap(rs, runs=4000)
    cl = cluster_bootstrap(rs, weeks, runs=4000)
    assert cl.groups == 60
    assert (cl.ci_high - cl.ci_low) > 2.0 * (iid.ci_high - iid.ci_low)


def test_cluster_bootstrap_equals_iid_style_when_each_trade_is_its_own_group():
    import numpy as np
    from app.backtest.robustness import cluster_bootstrap
    rs = np.array([1.0, -1.0, 2.0, -1.0, 0.5] * 20)
    cl = cluster_bootstrap(rs, np.arange(rs.size), runs=4000)
    se = rs.std(ddof=1) / np.sqrt(rs.size)
    assert abs((cl.ci_high - cl.ci_low) / 2 - 1.96 * se) < 0.25 * 1.96 * se


def test_bonferroni_z():
    from app.backtest.robustness import bonferroni_z
    assert abs(bonferroni_z(1) - 1.96) < 0.01
    assert abs(bonferroni_z(36) - 3.20) < 0.01
