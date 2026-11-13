from datetime import date, datetime, timedelta, timezone

from app.core.market_data import Bar, is_stale, resample, session_coverage, validate_bars

T0 = int(datetime(2026, 11, 12, 14, 30, tzinfo=timezone.utc).timestamp())  # 09:30 New York


def bar(i: int, o=100.0, h=101.0, l=99.0, c=100.5, v=10.0, ts=None) -> Bar:  # noqa: E741
    return Bar("test", "X", "M1", T0 + i * 60 if ts is None else ts, o, h, l, c, v)


# ---------- validation ----------

def test_good_bars_pass():
    assert validate_bars([bar(i) for i in range(5)]).ok


def test_high_below_close_is_rejected():
    rep = validate_bars([bar(0, h=100.0, c=100.5)])
    assert not rep.ok and "impossible" in rep.errors[0]


def test_low_above_open_is_rejected():
    assert not validate_bars([bar(0, l=100.2, o=100.0)]).ok


def test_zero_or_nan_price_is_rejected():
    assert not validate_bars([bar(0, o=0)]).ok
    assert not validate_bars([bar(0, c=float("nan"))]).ok


def test_duplicate_and_out_of_order_are_rejected():
    rep = validate_bars([bar(1), bar(1), bar(0)])
    assert any("duplicate" in e for e in rep.errors)
    assert any("out of order" in e for e in rep.errors)


def test_empty_list_is_ok():
    assert validate_bars([]).ok


# ---------- missing data / staleness ----------

def test_full_session_coverage():
    bars = [bar(i) for i in range(390)]  # 09:30-16:00 = 390 minutes
    assert session_coverage(bars, date(2026, 11, 12)) == (390, 390)


def test_session_gap_is_counted():
    bars = [bar(i) for i in range(390) if not 100 <= i < 130]  # 30-minute hole
    assert session_coverage(bars, date(2026, 11, 12)) == (360, 390)


def test_stale_detection():
    now = datetime.fromtimestamp(T0, timezone.utc)
    assert not is_stale(T0 - 60, now)                 # bar closed just now
    assert is_stale(T0 - 5 * 60, now)                 # closed 4 minutes ago
    assert is_stale(T0 - 60, now + timedelta(hours=1))


# ---------- resampling ----------

def test_resample_5m_ohlc():
    ones = [bar(0, o=10, h=11, l=9, c=10.5),
            bar(1, o=10.5, h=13, l=10, c=12),
            bar(2, o=12, h=12.5, l=8, c=9),
            bar(3, o=9, h=10, l=8.5, c=9.5),
            bar(4, o=9.5, h=10, l=9, c=9.8)]
    (five,) = resample(ones, 5)
    assert (five.open, five.high, five.low, five.close) == (10, 13, 8, 9.8)
    assert five.volume == 50 and five.ts == T0 and five.timeframe == "M5"


def test_resample_drops_incomplete_bucket_no_lookahead():
    # 7 minutes -> one complete 5m bar; the unfinished 2-minute bar must NOT appear.
    out = resample([bar(i) for i in range(7)], 5)
    assert len(out) == 1


def test_resample_skips_bucket_with_missing_minute():
    out = resample([bar(i) for i in range(10) if i != 7], 5)
    assert [b.ts for b in out] == [T0]
