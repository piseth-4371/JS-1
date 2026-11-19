"""Rules from docs/multimarket_trend_preregistration.md."""
import numpy as np
import pandas as pd
import pytest

from app.backtest import multimarket_trend as mt


def daily(values_by_month: dict[str, list[float]]) -> pd.Series:
    idx, vals = [], []
    for month, vs in values_by_month.items():
        days = pd.bdate_range(f"{month}-01", periods=len(vs))
        idx += list(days)
        vals += vs
    return pd.Series(vals, index=pd.DatetimeIndex(idx))


def test_read_fred_drops_blanks_inverts_and_refuses_2025(tmp_path):
    f = tmp_path / "X.csv"
    f.write_text("observation_date,X\n2024-01-02,2.0\n2024-01-03,.\n2024-01-04,\n2024-01-05,4.0\n2024-01-08,-3.0\n")
    s = mt.read_fred(f, invert=True)
    assert s.tolist() == [0.5, 0.25] and mt.non_positive(f) == ["2024-01-08"]
    f.write_text("observation_date,X\n2025-01-02,2.0\n")
    with pytest.raises(ValueError, match="2025"):
        mt.read_fred(f)


def test_month_with_too_few_values_has_no_close():
    s = daily({"2024-01": [1.0] * 12, "2024-02": [2.0] * 9})
    t = mt.monthly_table(s, pd.period_range("2024-01", "2024-02", freq="M"))
    assert t["close"].iloc[0] == 1.0 and np.isnan(t["close"].iloc[1])


def test_signal_weight_and_return_use_only_past_closes():
    months = pd.period_range("2020-01", "2021-03", freq="M")
    close = np.arange(100.0, 100.0 + len(months))          # rising every month
    table = pd.DataFrame({"close": close, "sigma": 0.2}, index=months)
    ok, sig, w, r = mt.market_arrays(table)
    first = 13                                              # needs the close 12 months before the decision month
    assert not ok[:first].any() and ok[first:].all()
    assert sig[first] == 1 and w[first] == pytest.approx(0.5)
    assert r[first] == pytest.approx(close[first] / close[first - 1] - 1)


def test_weight_is_capped():
    months = pd.period_range("2020-01", "2021-03", freq="M")
    t = pd.DataFrame({"close": np.arange(1.0, 16.0), "sigma": 0.001}, index=months)
    assert mt.market_arrays(t)[2][13] == mt.MAX_WEIGHT


def test_costs_charge_position_changes_and_financing():
    trades = np.array([[True], [True], [True]])
    signs = np.array([[1.0], [1.0], [-1.0]])
    w = np.full((3, 1), 2.0)
    r = np.zeros((3, 1))
    gross, net = mt.market_returns(trades, signs, w, r, np.array([0.001]))
    fin = 0.02 * 2 / 12
    assert net[:, 0] == pytest.approx([-(2 * 0.001 + fin), -fin, -(4 * 0.001 + fin)])
    _, stress = mt.market_returns(trades, signs, w, r, np.array([0.001]), cost_mult=2.0)
    assert stress[:, 0] == pytest.approx(2 * net[:, 0])


def test_portfolio_averages_only_trading_markets():
    trades = np.array([[True, False], [False, False]])
    assert mt.portfolio(trades, np.array([[0.02, 9.0], [1.0, 1.0]])).tolist()[0] == 0.02
    assert np.isnan(mt.portfolio(trades, np.array([[0.02, 9.0], [1.0, 1.0]]))[1])


def test_sharpe_drawdown_and_bootstrap():
    r = np.array([0.01, -0.005] * 60)
    assert mt.sharpe(r) == pytest.approx(r.mean() / r.std(ddof=1) * np.sqrt(12))
    assert mt.max_drawdown([0.1, -0.5, 0.2]) == pytest.approx(-0.5)
    lo, hi = mt.block_bootstrap_sharpe(r, runs=500)
    assert lo <= mt.sharpe(r) <= hi and mt.block_bootstrap_sharpe(r, runs=500) == (lo, hi)


def test_verdict_rules():
    good = mt.PeriodCheck(200, 6, 0.5, 0.1, 0.3, 0.2)
    assert mt.verdict(good, good) == mt.PASS
    assert mt.verdict(good, mt.PeriodCheck(200, 6, 0.0, -0.5, 0.3, -0.1)) == mt.NEGATIVE
    assert mt.verdict(good, mt.PeriodCheck(200, 6, 0.5, -0.1, 0.3, 0.2)) == mt.INCONCLUSIVE   # range crosses 0
    assert mt.verdict(good, mt.PeriodCheck(200, 6, 0.5, 0.1, 0.6, 0.2)) == mt.INCONCLUSIVE    # not above random
    assert mt.verdict(good, mt.PeriodCheck(100, 6, 0.5, 0.1, 0.3, 0.2)) == mt.INCONCLUSIVE    # too few months
