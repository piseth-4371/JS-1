"""Agent 1 — Market Researcher (data part).

Pure functions: no network, no database. That makes them easy to test.

- Bar: one candle, always with `source` and a UTC timestamp.
- validate_bars: finds broken candles, duplicates, wrong order.
- session_coverage: how many minutes of the New York session are missing.
- is_stale: is the newest bar too old to trade on?
- resample: build 5-minute / 15-minute bars from 1-minute bars.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
NY_OPEN = time(9, 30)
NY_CLOSE = time(16, 0)


@dataclass(frozen=True)
class Bar:
    source: str
    symbol: str
    timeframe: str
    ts: int  # bar OPEN time, UTC epoch seconds
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def dt_utc(self) -> datetime:
        return datetime.fromtimestamp(self.ts, timezone.utc)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, r) -> "Bar":
        return cls(r.source, r.symbol, r.timeframe, r.ts, r.open, r.high, r.low, r.close, r.volume)


@dataclass
class ValidationReport:
    total: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_bars(bars: list[Bar], max_errors: int = 20) -> ValidationReport:
    """Check every candle is possible and the list is in time order without duplicates."""
    rep = ValidationReport(total=len(bars))

    def err(msg: str) -> None:
        if len(rep.errors) < max_errors:
            rep.errors.append(msg)

    prev_ts: int | None = None
    for b in bars:
        when = b.dt_utc.isoformat()
        prices = (b.open, b.high, b.low, b.close)
        if any(p is None or p != p or p <= 0 for p in prices):  # p != p catches NaN
            err(f"{when}: non-positive or missing price {prices}")
        elif b.high < max(b.open, b.close, b.low) or b.low > min(b.open, b.close, b.high):
            err(f"{when}: impossible candle O={b.open} H={b.high} L={b.low} C={b.close}")
        if b.volume < 0:
            err(f"{when}: negative volume {b.volume}")
        if prev_ts is not None:
            if b.ts == prev_ts:
                err(f"{when}: duplicate timestamp")
            elif b.ts < prev_ts:
                err(f"{when}: out of order")
        prev_ts = b.ts
    return rep


def session_coverage(bars: list[Bar], day: date) -> tuple[int, int]:
    """(minutes present, minutes expected) for the NY cash session 09:30–16:00 of `day`.

    Uses 1-minute bars. A low ratio means gaps: the engine should WAIT on such days.
    """
    start = datetime.combine(day, NY_OPEN, NY).timestamp()
    end = datetime.combine(day, NY_CLOSE, NY).timestamp()
    expected = int((end - start) // 60)
    present = len({b.ts for b in bars if start <= b.ts < end})
    return present, expected


def is_stale(last_bar_ts: int, now: datetime, max_age: timedelta = timedelta(minutes=2), bar_seconds: int = 60) -> bool:
    """True if the newest bar CLOSED more than `max_age` ago."""
    close_time = last_bar_ts + bar_seconds
    return now.timestamp() - close_time > max_age.total_seconds()


def resample(bars: list[Bar], minutes: int) -> list[Bar]:
    """Combine 1-minute bars into `minutes`-minute bars aligned to the clock (e.g. 09:30, 09:35).

    Only COMPLETE buckets are returned (all `minutes` sub-bars present), so a
    half-finished candle can never leak into the strategy (no look-ahead).
    """
    size = minutes * 60
    out: list[Bar] = []
    bucket: list[Bar] = []
    bucket_start: int | None = None

    def flush() -> None:
        if bucket and len(bucket) == minutes:
            out.append(
                Bar(
                    source=bucket[0].source,
                    symbol=bucket[0].symbol,
                    timeframe=f"M{minutes}",
                    ts=bucket_start,
                    open=bucket[0].open,
                    high=max(b.high for b in bucket),
                    low=min(b.low for b in bucket),
                    close=bucket[-1].close,
                    volume=sum(b.volume for b in bucket),
                )
            )

    for b in bars:
        start = b.ts - (b.ts % size)
        if start != bucket_start:
            flush()
            bucket, bucket_start = [], start
        bucket.append(b)
    flush()
    return out
