from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.backtest import exness_gate as g

NY = g.NY


def ts(y, m, d, hh, mm):
    return int(datetime(y, m, d, hh, mm, tzinfo=NY).timestamp())


def trade(entry_ts, ny_date, r_gross=1.0, risk=10.0, kind="limit", exit_reason="target", side=1, strategy="s"):
    entry = 100.0
    exit_ = entry + side * r_gross * risk
    legs = (kind in ("market", "stop")) + (exit_reason in ("stop", "session_end", "kill_switch"))
    r = r_gross - (1.5 + 0.5 * legs) / risk
    return dict(strategy=strategy, side=side, kind=kind, ny_date=ny_date, entry_ts=entry_ts, entry=entry,
                exit=exit_, exit_reason=exit_reason, risk_pts=risk, r=r)


def test_window_uses_new_york_time_across_dst():
    assert g.window(ts(2023, 1, 10, 9, 29)) == "pre_us"
    assert g.window(ts(2023, 1, 10, 9, 30)) == "us"
    assert g.window(ts(2023, 7, 10, 9, 30)) == "us"      # summer time
    assert g.window(ts(2023, 7, 10, 3, 0)) == "pre_us"


def test_reprice_replaces_the_spread_only():
    t = pd.DataFrame([trade(ts(2023, 1, 10, 10, 0), "2023-01-10", risk=10.0),
                      trade(ts(2023, 1, 10, 8, 0), "2023-01-10", risk=20.0, kind="market", exit_reason="stop")])
    assert g.cost_model_error(t) < 1e-12
    out = g.reprice(t)
    assert out["r_exness"].iloc[0] == pytest.approx(t["r"].iloc[0] - (2.94 - 1.5) / 10)
    assert out["r_stress"].iloc[0] == pytest.approx(t["r"].iloc[0] - (3.65 - 1.5) / 10)   # US p90
    assert out["r_stress"].iloc[1] == pytest.approx(t["r"].iloc[1] - (3.29 - 1.5) / 20)   # pre-US p90


def test_wrong_cost_model_is_detected():
    t = pd.DataFrame([trade(ts(2023, 1, 10, 10, 0), "2023-01-10")])
    t.loc[0, "r"] += 0.01
    assert g.cost_model_error(t) > 1e-3


def many(year, n, r_gross, risk=50.0):
    start = datetime(year, 1, 2, 10, 0, tzinfo=NY)
    rows = []
    for i in range(n):
        d = start + timedelta(days=i * 3)
        rows.append(trade(int(d.timestamp()), d.date().isoformat(), r_gross=r_gross + (0.2 if i % 2 else -0.2), risk=risk))
    return rows


def test_gate_passes_only_with_a_clear_margin_in_both_splits():
    good = g.reprice(pd.DataFrame(many(2020, 60, 1.0) + many(2023, 60, 1.0)))
    dev, val = g.split(good, g.DEV_YEARS), g.split(good, g.VAL_YEARS)
    assert (dev.n, val.n) == (60, 60)
    assert g.verdict(dev, val, main_passed=True) == g.PASS
    assert g.verdict(dev, val, main_passed=False) == g.NOT_ELIGIBLE


def test_small_edge_that_exness_costs_remove_fails():
    # +0.05R gross minus backtest costs (0.03R at risk 50) is still positive; Exness adds 0.0288R more -> negative.
    t = g.reprice(pd.DataFrame(many(2020, 60, 0.05) + many(2023, 60, 0.05)))
    dev, val = g.split(t, g.DEV_YEARS), g.split(t, g.VAL_YEARS)
    assert dev.avg_backtest > 0 and dev.avg_exness < 0
    assert g.verdict(dev, val, main_passed=True) == g.FAIL


def test_too_few_trades_fails():
    t = g.reprice(pd.DataFrame(many(2020, 10, 1.0) + many(2023, 60, 1.0)))
    assert g.verdict(g.split(t, g.DEV_YEARS), g.split(t, g.VAL_YEARS), main_passed=True) == g.FAIL
