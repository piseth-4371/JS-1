"""Checks for learning/ch01_returns.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch01.py -q
(Not part of the main test suite on purpose: it fails until you write the exercise.)"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch01_returns as ex  # noqa: E402


def test_simple_return_book_example():
    assert ex.simple_return(80, 60) == pytest.approx(-0.25)        # book 1.1
    assert ex.simple_return(100, 110) == pytest.approx(0.10)


def test_log_return():
    assert ex.log_return(100, 100) == 0
    assert ex.log_return(100, 50) == pytest.approx(math.log(0.5))


def test_percents_do_not_add_up():
    # book chapter 1: -50 % then +100 % -> back to the start, a total of 0
    assert ex.total_from_simple([-0.5, 1.0]) == pytest.approx(0.0)
    # book 1.2: +10 % then -10 % -> -1 %
    assert ex.total_from_simple([0.10, -0.10]) == pytest.approx(-0.01)


def test_log_returns_add_up():
    logs = [ex.log_return(100, 110), ex.log_return(110, 90), ex.log_return(90, 120)]
    assert ex.total_from_log(logs) == pytest.approx(ex.log_return(100, 120))


def test_needed_to_recover():
    assert ex.needed_to_recover(-0.25) == pytest.approx(1 / 3)       # book 1.1: +33.3 %
    assert ex.needed_to_recover(-0.50) == pytest.approx(1.0)         # -50 % needs +100 %
