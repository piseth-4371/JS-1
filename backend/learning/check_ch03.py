"""Checks for learning/ch03_expected_value.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch03.py -q
(Not part of the main test suite on purpose: it fails until you write the exercise.)"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch03_expected_value as ex  # noqa: E402


def test_average():
    assert ex.average([1.0, 2.0, 3.0]) == pytest.approx(2.0)
    assert ex.average([-1.0, 2.0]) == pytest.approx(0.5)
    assert ex.average([]) == 0.0


def test_win_rate():
    assert ex.win_rate([2.0, -1.0, -1.0, 2.0]) == pytest.approx(0.5)
    assert ex.win_rate([-1.0, -1.0, 0.0]) == 0.0        # 0R (break-even) is not a win
    assert ex.win_rate([]) == 0.0


def test_expected_value():
    assert ex.expected_value(18 / 37, 1.0, -1.0) == pytest.approx(-1 / 37)     # roulette, red
    assert ex.expected_value(0.5, 2.0, -1.0) == pytest.approx(0.5)             # coin flip paying 2:1
    assert ex.expected_value(1 / 3, 2.0, -1.0) == pytest.approx(0.0)


def test_breakeven_win_rate():
    assert ex.breakeven_win_rate(2.0, -1.0) == pytest.approx(1 / 3)
    assert ex.breakeven_win_rate(1.0, -1.0) == pytest.approx(0.5)
    p = ex.breakeven_win_rate(1.7, -1.2)
    assert ex.expected_value(p, 1.7, -1.2) == pytest.approx(0.0)              # EV is zero there


def test_is_roulette():
    assert ex.is_roulette([-1.0, -1.0, 2.0, -1.0]) is True        # avg -0.25
    assert ex.is_roulette([2.0, -1.0]) is False                   # avg +0.5
