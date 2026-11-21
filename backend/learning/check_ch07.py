"""Checks for learning/ch07_volatility.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch07.py -q"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch07_volatility as ex  # noqa: E402


def test_daily_returns():
    assert ex.daily_returns([100, 110, 99]) == pytest.approx([0.10, -0.10])


def test_stdev():
    assert ex.stdev([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(2.138, abs=1e-3)   # sample stdev
    assert ex.stdev([5.0]) == 0.0
    assert ex.stdev([3, 3, 3]) == 0.0


def test_annualize_square_root_rule():
    assert ex.annualize(0.01) == pytest.approx(0.01 * math.sqrt(252))
    assert ex.annualize(0.02, days=4) == pytest.approx(0.04)


def test_rolling_vol_length_and_value():
    r = [0.01, -0.01] * 15            # 30 returns
    rv = ex.rolling_vol(r, window=20)
    assert len(rv) == 11
    assert rv[0] == pytest.approx(ex.annualize(ex.stdev(r[:20])))


def test_real_file_reads_and_stops_before_2025():
    dates, closes = ex.read_closes()
    assert dates[0] == "1971-02-05" and dates[-1] < "2025-01-01" and len(closes) > 13000
