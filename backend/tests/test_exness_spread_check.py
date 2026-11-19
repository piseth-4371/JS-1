"""Rules from docs/exness_spread_check_preregistration.md."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

path = Path(__file__).resolve().parent.parent / "scripts" / "exness_spread_check.py"
spec = importlib.util.spec_from_file_location("exness_spread_check", path)
esc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(esc)


def test_bad_ticks_are_flagged():
    bid = np.array([100.0, 0.0, 100.0, 101.0, np.nan])
    ask = np.array([101.0, 101.0, 0.0, 100.0, 101.0])
    assert esc.bad_tick_mask(bid, ask).tolist() == [False, True, True, True, True]


def test_last_tick_of_each_minute_is_kept():
    d = esc.last_per_minute(np.array([60, 90, 119, 120]), np.array([1.0, 2.0, 3.0, 4.0]), np.array([2.0, 3.0, 5.0, 6.0]))
    assert d["ts"].tolist() == [60, 120] and d["bid"].tolist() == [3.0, 4.0] and d["ask"].tolist() == [5.0, 6.0]


def test_minute_changes_skip_holes():
    s = esc.minute_changes(np.array([60, 120, 300]), np.array([1.0, 3.0, 9.0]))
    assert s.to_dict() == {120: 2.0}


def test_lag_check_finds_a_shifted_clock():
    rng = np.random.default_rng(1)
    idx = np.arange(1, 501) * 60
    a = pd.Series(rng.normal(size=500), index=idx)
    same = esc.lag_correlations(a, a)
    assert max(same, key=same.get) == 0
    later = pd.Series(a.to_numpy(), index=idx + 60)      # b shows the same move one minute later
    shifted = esc.lag_correlations(a, later)
    assert max(shifted, key=shifted.get) == 1


def test_verdict_boundaries():
    assert esc.assumption_verdict(1.5) == "1.5 assumption holds"
    assert esc.assumption_verdict(1.51) == "1.5 assumption understated"
    assert [esc.ratio_verdict(x) for x in (0.79, 0.80, 1.25, 1.26)] == ["Exness cheaper", "similar", "similar", "Exness more expensive"]
