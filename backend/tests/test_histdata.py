import zipfile
from datetime import datetime, timezone

from app.core.sources import histdata_source as hd


def utc(*a):
    return int(datetime(*a, tzinfo=timezone.utc).timestamp())


def test_clock_follows_uk_summer_time():
    winter = hd.parse_line("20190102 093000;6400.5;6401.0;6399.0;6400.0;0")
    summer = hd.parse_line("20190702 093000;7800.0;7801.0;7799.5;7800.25;0")
    gap_week = hd.parse_line("20190312 093000;1;2;0.5;1.5;0")    # US on EDT, UK not yet on BST
    assert winter.ts == utc(2019, 1, 2, 14, 30)
    assert summer.ts == utc(2019, 7, 2, 13, 30)
    assert gap_week.ts == utc(2019, 3, 12, 14, 30)
    assert (summer.open, summer.high, summer.low, summer.close) == (7800.0, 7801.0, 7799.5, 7800.25)
    assert summer.source == "histdata" and summer.symbol == "NSXUSD" and summer.timeframe == "M1"


def test_comma_separator_and_blank_lines():
    bars = hd.parse_text("\n20200103 100100,1,2,0.5,1.5,0\n20200103 100000,1,2,0.5,1.5,0\n")
    assert [b.ts for b in bars] == sorted(b.ts for b in bars) and len(bars) == 2


def test_repeated_minutes_are_dropped():
    bars = hd.parse_text("20191027 190000;1;2;0.5;1.5;0\n20191027 190100;1;2;0.5;1.5;0\n20191027 190000;1;2;0.5;1.5;0\n")
    assert len(bars) == 1


def test_read_zip_skips_gap_report(tmp_path):
    p = tmp_path / "HISTDATA_COM_ASCII_NSXUSD_M1_2019.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("DAT_ASCII_NSXUSD_M1_2019.csv", "20190102 093000;1;2;0.5;1.5;0\n")
        z.writestr("DAT_ASCII_NSXUSD_M1_2019.txt", "gap of 120s found between ...")
    assert len(hd.read_zip(p)) == 1
