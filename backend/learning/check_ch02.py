"""Checks for learning/ch02_present_value.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch02.py -q
(Not part of the main test suite on purpose: it fails until you write the exercise.)"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch02_present_value as ex  # noqa: E402


def test_future_value_book_examples():
    assert ex.future_value(100, 0.05, 10) == pytest.approx(162.89, abs=0.01)     # book chapter 2 picture
    assert ex.future_value(1000, 0.04, 3) == pytest.approx(1124.86, abs=0.01)    # book 2.1


def test_present_value_book_examples():
    assert ex.present_value(500, 0.05, 2) == pytest.approx(453.51, abs=0.01)     # book 2.2
    assert ex.present_value(500, 0.08, 2) == pytest.approx(428.67, abs=0.01)


def test_pv_undoes_fv():
    assert ex.present_value(ex.future_value(250, 0.07, 9), 0.07, 9) == pytest.approx(250)


def test_account_after_trades():
    assert ex.account_after_trades(1000, [], 0.5) == 1000
    assert ex.account_after_trades(1000, [2.0], 0.5) == pytest.approx(1010)           # +1 %
    assert ex.account_after_trades(1000, [2.0, -1.0], 0.5) == pytest.approx(1004.95)  # 1010 then -0.5 %
    # order does not matter for the end balance (multiplication), but each trade uses the CURRENT balance
    assert ex.account_after_trades(1000, [-1.0, 2.0], 0.5) == pytest.approx(1004.95)


def test_yearly_rate():
    assert ex.yearly_rate(1000, 1124.864, 3) == pytest.approx(0.04, abs=1e-6)
    assert ex.yearly_rate(1000, 1000, 6) == pytest.approx(0.0)
    assert ex.yearly_rate(1000, 500, 1) == pytest.approx(-0.5)
