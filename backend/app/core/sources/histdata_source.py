"""Import free HistData.com NSXUSD (Nasdaq-100) 1-minute bars from downloaded zip files.

Owner approved this source on 2026-11-14 because Dukascopy kept rate-limiting the download.
Facts from histdata.com (download page + FAQ, read 2026-11-14):
  - "Generic ASCII" M1 files, one zip per full year (2010-2025), per month for the current year.
  - Prices are based on the BID tick price.
  - The FAQ says "EST WITHOUT Day Light Savings" (always UTC-5), BUT THE NSXUSD FILES DO NOT
    FOLLOW THAT (checked 2026-11-14 on the 2019 file): the weekly open (18:00 New York) shows as
    18:00 in winter AND summer, and as 17:00 only in the weeks when US and UK clocks differ.
    So file time = UTC-4 while the UK is on summer time, else UTC-5. Each October switch also
    repeats one Sunday-evening hour; those duplicated minutes are dropped (outside all
    trading windows). The rule is confirmed against Dukascopy by scripts/compare_histdata.py.
  - The site does not say where its prices come from and gives no warranty, so the data is
    cross-checked against Dukascopy before it is trusted.
Line format: YYYYMMDD HHMMSS;open;high;low;close;volume   (',' separator also accepted)
"""
from __future__ import annotations

import io
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.market_data import Bar

SOURCE = "histdata"
INSTRUMENT = "NSXUSD"
GOLD = "XAUUSD"           # same provider, same clock (checked 2026-11-14 on the 2019 file)
LONDON = ZoneInfo("Europe/London")


def file_time_to_utc(t: datetime) -> int:
    """HistData clock: UTC-4 while the UK is on summer time, otherwise UTC-5."""
    guess = t.replace(tzinfo=timezone.utc) + timedelta(hours=5)
    if guess.astimezone(LONDON).utcoffset():
        guess -= timedelta(hours=1)
    return int(guess.timestamp())


def parse_line(line: str, instrument: str = INSTRUMENT) -> Bar | None:
    line = line.strip()
    if not line:
        return None
    parts = line.split(";") if ";" in line else line.split(",")
    if len(parts) < 5:
        raise ValueError(f"bad line: {line[:60]!r}")
    stamp = parts[0].strip()
    try:
        t = datetime.strptime(stamp, "%Y%m%d %H%M%S")
    except ValueError:
        t = datetime.strptime(stamp, "%Y%m%d %H%M")
    ts = file_time_to_utc(t)
    o, h, lo, c = (float(x) for x in parts[1:5])
    vol = float(parts[5]) if len(parts) > 5 and parts[5].strip() else 0.0
    return Bar(SOURCE, instrument, "M1", ts, o, h, lo, c, vol)


def parse_text(text: str, instrument: str = INSTRUMENT) -> list[Bar]:
    """Parse a file; minutes that appear twice (clock switch) are dropped entirely - we cannot tell which is right."""
    bars = [b for b in (parse_line(x, instrument) for x in text.splitlines()) if b is not None]
    seen = Counter(b.ts for b in bars)
    bars = [b for b in bars if seen[b.ts] == 1]
    bars.sort(key=lambda b: b.ts)
    return bars


def read_zip(path: Path, instrument: str = INSTRUMENT) -> list[Bar]:
    """Read the .csv data file(s) inside one HistData zip (the .txt file is their gap report)."""
    out: list[Bar] = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with z.open(name) as f:
                out += parse_text(io.TextIOWrapper(f, encoding="utf-8", errors="replace").read(), instrument)
    out.sort(key=lambda b: b.ts)
    return out
