"""Checks for learning/ch08_sharpe.py. Run:  .\\.venv\\Scripts\\python -m pytest learning\\check_ch08.py -q"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch08_sharpe as ex  # noqa: E402


def test_sharpe_simple_case():
    r = [0.02, 0.0] * 6                           # monthly: mean 1%, stdev ~1.044%
    expected = (0.01 * 12) / (ex.stdev(r) * math.sqrt(12))
    assert ex.sharpe(r, 12) == pytest.approx(expected)


def test_sharpe_safe_rate_lowers_it():
    r = [0.02, 0.0] * 6
    assert ex.sharpe(r, 12, safe_rate=0.02) < ex.sharpe(r, 12)


def test_sharpe_no_volatility_or_too_short():
    assert ex.sharpe([0.01, 0.01, 0.01], 12) == 0.0
    assert ex.sharpe([0.05], 12) == 0.0


def test_monthly_account_returns():
    m = ex.monthly_account_returns([("2020-01-05", 2.0), ("2020-01-20", -1.0), ("2020-02-03", -1.0)], 0.5)
    assert m == pytest.approx({"2020-01": 0.005, "2020-02": -0.005})
