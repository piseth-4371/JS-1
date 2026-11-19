from app.backtest.nearby import nearby_check, table


def test_plateau_passes():
    c = nearby_check(0.12, {"buy 1 day later": 0.10, "buy 1 day earlier": 0.08,
                            "sell 1 day earlier": 0.09, "sell 1 day later": -0.01})
    assert c["applies"] and c["passed"] and c["positive"] == 3 and c["needed"] == 3


def test_too_few_positive_neighbours_fail():
    c = nearby_check(0.12, {"a": 0.10, "b": -0.02, "c": 0.05, "d": -0.01})
    assert not c["passed"] and "only 2 of 4" in c["reasons"][0] and "b, d" in c["reasons"][0]


def test_spike_fails_even_if_neighbours_positive():
    c = nearby_check(0.50, {"a": 0.05, "b": 0.04})
    assert not c["passed"] and c["reasons"][0].startswith("spike")


def test_chosen_at_most_twice_median_is_fine():
    assert nearby_check(0.10, {"a": 0.05, "b": 0.05})["passed"]


def test_no_free_settings_does_not_apply():
    c = nearby_check(0.1, {})
    assert not c["applies"] and c["passed"]


def test_table_marks_chosen():
    t = table("hold 4 days", 0.1, {"hold 3 days": 0.05})
    assert "**hold 4 days (chosen)**" in t and "| hold 3 days | +0.050 |" in t
