"""Rules from docs/exness_spread_years_preregistration.md."""
import importlib.util
import sys
from datetime import date, datetime, timezone
from pathlib import Path

scripts = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location("exness_spread_years", scripts / "exness_spread_years.py")
esy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(esy)


def test_2019_scope_starts_with_the_file_and_needs_fewer_days():
    assert esy.scope(2019) == (date(2019, 8, 5), date(2019, 12, 31)) and esy.min_days(2019) == 80
    assert esy.scope(2024) == (date(2024, 1, 1), date(2024, 12, 31)) and esy.min_days(2024) == 200


def test_weekdays_skip_weekends():
    assert esy.weekdays_in(date(2024, 12, 20), date(2024, 12, 23)) == [date(2024, 12, 20), date(2024, 12, 23)]


def test_us_dst_boundaries_match_the_known_2023_dates():
    p = esy.clock_periods(2023)
    assert datetime.fromtimestamp(p["US DST"][0], timezone.utc) == datetime(2023, 3, 12, 7, tzinfo=timezone.utc)
    assert datetime.fromtimestamp(p["US DST"][1], timezone.utc) == datetime(2023, 11, 5, 6, tzinfo=timezone.utc)


def test_verdict_needs_a_usable_file_and_enough_days():
    assert esy.spread_verdicts(False, 250, 200, 1.0) == "no verdict (file not usable)"
    assert esy.spread_verdicts(True, 199, 200, 1.0) == "not enough data"
    assert esy.spread_verdicts(True, 200, 200, 1.6) == "1.5 assumption understated"


def test_best_lag_ignores_missing_values():
    assert esy.best_lag({-1: float("nan"), 0: 0.9, 1: 0.1}) == 0
    assert esy.best_lag({0: float("nan")}) is None
