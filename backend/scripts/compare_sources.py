"""Cross-check two feeds on the days they overlap.

If the time-zone conversion or the Dukascopy price scale were wrong, this
would show it: matching minutes should have very similar closes.

  .\\.venv\\Scripts\\python scripts\\compare_sources.py
"""
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.repository import count_bars, init_db, load_bars  # noqa: E402


def main() -> int:
    init_db()
    s = get_settings()
    mt5_source = sys.argv[1] if len(sys.argv) > 1 else "mt5:MetaQuotes-Demo"
    n, first, last = count_bars(mt5_source, s.mt5_symbol)
    if not n:
        print(f"No bars for {mt5_source}. Run the MT5 backfill first.")
        return 1
    a = {b.ts: b for b in load_bars(mt5_source, s.mt5_symbol, "M1", first, last + 1)}
    b = {x.ts: x for x in load_bars(dk.SOURCE, dk.INSTRUMENT, "M1", first, last + 1)}
    common = sorted(a.keys() & b.keys())
    if not common:
        print("No overlapping minutes. Backfill Dukascopy for the same dates.")
        return 1

    diffs = [a[t].close - b[t].close for t in common]
    abs_diffs = [abs(d) for d in diffs]
    print(f"Overlapping minutes: {len(common)}")
    print(f"Close difference MT5 - Dukascopy: median {statistics.median(diffs):+.2f}, "
          f"mean |diff| {statistics.mean(abs_diffs):.2f}, max |diff| {max(abs_diffs):.2f} points")

    # Is the time alignment right? Try shifting by whole hours and see which fits best.
    best = []
    for shift_h in range(-3, 4):
        sh = shift_h * 3600
        pairs = [(a[t].close, b[t + sh].close) for t in common if t + sh in b]
        if pairs:
            best.append((statistics.mean(abs(x - y) for x, y in pairs), shift_h))
    best.sort()
    print("Mean |diff| by time shift (hours): " + ", ".join(f"{h:+d}h={d:.1f}" for d, h in sorted(best, key=lambda x: x[1])))
    print("Alignment OK" if best[0][1] == 0 else f"WARNING: best match at {best[0][1]:+d}h - time zone setting is probably wrong")
    sample = common[len(common) // 2]
    print(f"Example {datetime.fromtimestamp(sample, timezone.utc):%Y-%m-%d %H:%M} UTC: "
          f"MT5 close {a[sample].close}, Dukascopy close {b[sample].close}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
