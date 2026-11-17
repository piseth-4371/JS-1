"""Cost breakdown, fill-model reconciliation, summary statistics and the pre-registered verdict."""
import math
from datetime import date, timedelta

import numpy as np
import pytest

from app.backtest.decompose import (INCOMPLETE, INCONCLUSIVE, NEGATIVE, PASS, SplitResult, cost_split, fill_effect,
                                    match, max_drawdown_pct, summarize, verdict, week_interval)
from app.backtest.engine import Costs, Trade, run
from app.backtest.robustness import cluster_bootstrap
from tests.test_backtest_engine import FLAT, OneShot, _ask_of, frame


def trade(entry_ts=0, side=1, kind="limit", entry=100.0, exit=110.0, reason="target", risk=10.0, r=0.0):
    return Trade("s", side, kind, date(2023, 1, 2), entry_ts, entry_ts + 60, entry, entry - side * risk,
                 entry + side * 2 * risk, exit, reason, risk, r, 0.5, 1.0)


@pytest.mark.parametrize("kind,reason,legs", [("limit", "target", 0), ("stop", "target", 1),
                                              ("limit", "stop", 1), ("market", "session_end", 2)])
def test_cost_split_matches_the_engine_rule(kind, reason, legs):
    c = Costs(spread=1.5, slippage=0.5)
    s = cost_split(trade(kind=kind, reason=reason, exit=106.0), c)
    assert s.gross == pytest.approx(0.6)
    assert s.spread == pytest.approx(0.15) and s.slippage == pytest.approx(0.05 * legs) and s.fees == 0
    assert s.net == pytest.approx(s.gross - s.spread - s.slippage - s.fees)


def test_cost_split_reconciles_with_real_engine_trades():
    costs = Costs(spread=1.5, slippage=0.5)
    for mins, kw in (([(105, 106, 104, 105)] * 5 + [(105, 105, 99, 101)] + [(101, 121, 101, 120)] + [FLAT] * 8, {}),
                     ([(105, 106, 104, 105)] * 5 + [(100, 101, 99.5, 100)] + [(100, 101, 85, 90)] + [FLAT] * 8,
                      {"kind": "stop", "entry": 100.0})):
        (t,) = run(OneShot(**kw), frame(mins), costs=costs).trades
        assert cost_split(t, costs).net == pytest.approx(t.r, abs=1e-9)


def test_fill_effect_reconciles_matched_and_unmatched_trades():
    a = [trade(entry_ts=0, r=1.0), trade(entry_ts=60, r=-1.0), trade(entry_ts=120, r=0.5)]
    b = [trade(entry_ts=0, r=0.8), trade(entry_ts=60, r=-1.1), trade(entry_ts=180, r=2.0)]
    m = match(a, b)
    assert len(m.pairs) == 2 and [t.entry_ts for t in m.only_a] == [120] and [t.entry_ts for t in m.only_b] == [180]
    e = fill_effect(a, b)
    assert e.matched_diff == pytest.approx(-0.3) and e.only_a == 0.5 and e.only_b == 2.0
    assert e.residual == pytest.approx(0.0, abs=1e-12)


def test_same_minute_opposite_side_is_not_a_match():
    m = match([trade(entry_ts=0, side=1)], [trade(entry_ts=0, side=-1)])
    assert m.pairs == [] and len(m.only_a) == 1 and len(m.only_b) == 1


def test_ask_model_drops_a_fill_and_the_reconciliation_shows_it():
    mins = [(105, 106, 104, 105)] * 5 + [(105, 105, 99, 101)] + [(101, 121, 101, 120)] + [FLAT] * 8
    bid = run(OneShot(), frame(mins), costs=Costs(0, 0)).trades
    ask = run(OneShot(), frame(mins), costs=Costs(0, 0), ask=_ask_of(mins, 2.0)).trades
    e = fill_effect(bid, ask)
    assert (e.n_matched, e.n_only_a, e.n_only_b) == (0, 1, 0) and e.only_a == pytest.approx(2.0)
    assert e.residual == pytest.approx(0.0)


def test_summary_numbers():
    s = summarize([2.0, -1.0, -1.0, 1.0])
    assert s.n == 4 and s.win_rate == 0.5 and s.avg_win == 1.5 and s.avg_loss == -1.0
    assert s.avg == pytest.approx(0.25) and s.profit_factor == pytest.approx(1.5)
    assert summarize([1.0]).profit_factor == math.inf and summarize([]).n == 0


def test_max_drawdown_at_half_percent_risk():
    assert max_drawdown_pct([1, 1]) == 0
    assert max_drawdown_pct([-1, -1]) == pytest.approx((1 - 0.995 ** 2) * 100)


def test_week_interval_is_the_cluster_bootstrap_and_widens_for_more_tests():
    rng = np.random.default_rng(3)
    rs = rng.normal(0.1, 1, 300)
    days = [date(2023, 1, 2) + timedelta(days=int(i)) for i in range(300)]
    lo1, hi1 = week_interval(rs, days)
    cb = cluster_bootstrap(rs, [f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}" for d in days])
    assert (lo1, hi1) == pytest.approx((cb.ci_low, cb.ci_high))
    lo7, hi7 = week_interval(rs, days, tests=7)
    assert lo7 < lo1 < hi1 < hi7


def _s(n=40, avg=0.2, low=0.05, stress=0.1, cov=True):
    return SplitResult(n, avg, low, stress, cov)


def test_verdict_rules():
    assert verdict(_s(), _s()) == PASS
    assert verdict(_s(avg=-0.01), _s()) == NEGATIVE
    assert verdict(_s(), _s(avg=0.0)) == NEGATIVE
    assert verdict(_s(low=-0.1), _s()) == INCONCLUSIVE
    assert verdict(_s(), _s(stress=-0.01)) == INCONCLUSIVE
    assert verdict(_s(n=29), _s()) == INCONCLUSIVE
    assert verdict(_s(cov=False), _s(avg=-1)) == INCOMPLETE
    assert verdict(_s(n=0, avg=float("nan"), low=float("nan")), _s()) == INCONCLUSIVE
