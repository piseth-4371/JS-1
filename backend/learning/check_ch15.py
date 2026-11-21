"""Checks for learning/ch15_monte_carlo.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch15.py -q"""
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch15_monte_carlo as ex  # noqa: E402


def test_play_year_compounds_on_current_balance():
    rng = random.Random(0)
    assert ex.play_year([2.0], 2, 1000, 0.5, rng) == pytest.approx(1000 * 1.01 * 1.01)
    assert ex.play_year([-1.0], 1, 1000, 0.5, rng) == pytest.approx(995)


def test_simulate_sorted_repeatable():
    a = ex.simulate([2.0, -1.0], 20, 1000, 0.5, runs=200, seed=3)
    assert a == sorted(a) and len(a) == 200
    assert a == ex.simulate([2.0, -1.0], 20, 1000, 0.5, runs=200, seed=3)


def test_percentile():
    v = list(range(100))
    assert ex.percentile(v, 0.05) == 5
    assert ex.percentile(v, 0.5) == 50
    assert ex.percentile(v, 1.0) == 99
