"""Checks for learning/ch14_kelly.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch14.py -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch14_kelly as ex  # noqa: E402


def test_kelly_textbook():
    assert ex.kelly(0.5, 2.0) == pytest.approx(0.25)      # coin flip paying 2:1
    assert ex.kelly(0.6, 1.0) == pytest.approx(0.20)
    assert ex.kelly(1 / 3, 2.0) == pytest.approx(0.0)     # break-even bet
    assert ex.kelly(0.3, 2.0) < 0                         # losing bet
    assert ex.kelly(0.5, 0.0) == 0.0


def test_payoff_ratio():
    assert ex.payoff_ratio([2.0, 2.0, -1.0, -1.0]) == pytest.approx(2.0)
    assert ex.payoff_ratio([2.0]) == 0.0                  # no losses
    assert ex.payoff_ratio([-1.0]) == 0.0                 # no wins


def test_bet_size_half_and_never_negative():
    assert ex.bet_size(0.25) == pytest.approx(0.125)
    assert ex.bet_size(-0.1) == 0.0
    assert ex.bet_size(0.25, fraction=1.0) == pytest.approx(0.25)
