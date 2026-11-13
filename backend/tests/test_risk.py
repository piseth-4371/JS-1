import pytest

from app.core.risk import FRACTIONAL, USTEC, AccountState, OrderRequest, RiskSettings, evaluate

GOOD = OrderRequest(side=1, entry=28000, stop=27980, target=28040)  # 20 pt stop, 2R


def acct(equity=10_000.0, **kw):
    return AccountState(equity=equity, day_start_equity=kw.pop("day", equity), week_start_equity=kw.pop("week", equity), **kw)


def test_good_order_is_approved_and_sized():
    d = evaluate(GOOD, acct(), USTEC, RiskSettings())
    assert d.approved, d.reasons
    # $50 risk / (20 pts * $1 per lot) = 2.5 lots
    assert d.qty == pytest.approx(2.5)
    assert d.risk_pct == pytest.approx(0.5)


def test_ten_dollar_account_rejected_by_min_lot():
    d = evaluate(GOOD, acct(10.0), USTEC, RiskSettings())
    assert not d.approved
    assert any("Minimum lot 0.1" in r for r in d.reasons)


def test_missing_stop_rejected():
    d = evaluate(OrderRequest(1, 28000, None, 28040), acct(), USTEC, RiskSettings())
    assert not d.approved and "Stop-loss is missing" in d.reasons


def test_stop_on_wrong_side_rejected():
    d = evaluate(OrderRequest(1, 28000, 28010, 28040), acct(), USTEC, RiskSettings())
    assert not d.approved and any("wrong side" in r for r in d.reasons)


def test_low_reward_to_risk_rejected():
    d = evaluate(OrderRequest(1, 28000, 27980, 28020), acct(), USTEC, RiskSettings())  # 1R
    assert not d.approved and any("Reward:risk" in r for r in d.reasons)


def test_daily_loss_limit():
    d = evaluate(GOOD, acct(9_800.0, day=10_000.0), USTEC, RiskSettings())
    assert any("Daily loss" in r for r in d.reasons)


def test_weekly_loss_limit():
    d = evaluate(GOOD, acct(9_500.0, week=10_000.0, day=9_500.0), USTEC, RiskSettings())
    assert any("Weekly loss" in r for r in d.reasons)


def test_max_trades_per_day():
    assert not evaluate(GOOD, acct(trades_today=3), USTEC, RiskSettings()).approved


def test_one_position_at_a_time():
    assert not evaluate(GOOD, acct(open_positions=1), USTEC, RiskSettings()).approved


def test_anti_revenge_after_two_losses():
    assert not evaluate(GOOD, acct(consecutive_losses=2), USTEC, RiskSettings()).approved


def test_kill_switch_blocks_everything():
    d = evaluate(GOOD, acct(kill_switch=True), USTEC, RiskSettings())
    assert not d.approved and "Kill switch is ON" in d.reasons


def test_leverage_cap_reduces_size():
    tiny_stop = OrderRequest(1, 28000, 27999, 28002)  # 1 pt stop would need 50 lots
    d = evaluate(tiny_stop, acct(), USTEC, RiskSettings())
    assert d.approved
    assert d.qty * 28000 <= 10_000 * 20 + 1e-6


@pytest.mark.parametrize("field,value", [("risk_pct", 1.5), ("daily_loss_pct", 3), ("weekly_loss_pct", 6),
                                         ("max_trades_per_day", 4), ("max_open_positions", 2),
                                         ("max_consecutive_losses", 3), ("max_leverage", 50), ("risk_pct", 0)])
def test_settings_cannot_exceed_hard_limits(field, value):
    with pytest.raises(ValueError):
        RiskSettings(**{field: value})


def test_fractional_instrument_allows_tiny_size():
    d = evaluate(GOOD, acct(10.0), FRACTIONAL, RiskSettings())
    assert d.approved and d.qty == pytest.approx(0.0025)
