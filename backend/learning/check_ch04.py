"""Checks for learning/ch04_random_walk.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch04.py -q
(Not part of the main test suite on purpose: it fails until you write the exercise.)"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch04_random_walk as ex  # noqa: E402


def test_random_walk_shape_and_steps():
    w = ex.random_walk(50, 100.0, 1.0, seed=7)
    assert len(w) == 51 and w[0] == 100.0
    assert all(abs(b - a) == pytest.approx(1.0) for a, b in zip(w, w[1:]))   # every step is +1 or -1


def test_random_walk_same_seed_same_walk():
    assert ex.random_walk(30, 10, 0.5, seed=3) == ex.random_walk(30, 10, 0.5, seed=3)
    assert ex.random_walk(30, 10, 0.5, seed=3) != ex.random_walk(30, 10, 0.5, seed=4)


def test_changes():
    assert ex.changes([10, 12, 11, 11]) == [2, -1, 0]
    assert ex.changes([5]) == []


def test_share_up():
    assert ex.share_up([1, -1, 2, 0]) == pytest.approx(0.5)
    assert ex.share_up([]) == 0.0


def test_count_positive():
    assert ex.count_positive([1.0, -2.0, 0.0, 3.0]) == 2
    assert ex.count_positive([]) == 0


def test_long_walk_is_about_half_up():
    up = ex.share_up(ex.changes(ex.random_walk(20_000, 100, 1, seed=5)))
    assert 0.48 < up < 0.52
