"""Trust check: does HistData NSXUSD agree with Dukascopy USATECHIDXUSD on the overlapping minutes?

Checks price level (close difference), time alignment (is the best match at 0 shift?) and coverage.
  .\\.venv\\Scripts\\python scripts\\compare_histdata.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from app.core.features import load_m1  # noqa: E402
from app.core.sources import dukascopy_source as dk  # noqa: E402
from app.core.sources import histdata_source as hd  # noqa: E402
from app.repository import count_bars, init_db  # noqa: E402


def main() -> int:
    init_db()
    n_d, d0, d1 = count_bars(dk.SOURCE, dk.INSTRUMENT)
    n_h, h0, h1 = count_bars(hd.SOURCE, hd.INSTRUMENT)
    if not n_d or not n_h:
        print("Need both Dukascopy and HistData bars.")
        return 1
    a, b = max(d0, h0), min(d1, h1) + 1
    d = load_m1(dk.SOURCE, dk.INSTRUMENT, a, b).set_index("ts")
    h = load_m1(hd.SOURCE, hd.INSTRUMENT, a, b).set_index("ts")
    common = d.index.intersection(h.index)
    print(f"Overlap window: {len(d):,} Dukascopy minutes, {len(h):,} HistData minutes, {len(common):,} in both")
    diff = (h.loc[common, "c"] - d.loc[common, "c"]).to_numpy()
    print(f"Close difference HistData - Dukascopy (points): median {np.median(diff):+.2f}, "
          f"mean abs {np.abs(diff).mean():.2f}, p95 abs {np.percentile(np.abs(diff), 95):.2f}, "
          f"p99 abs {np.percentile(np.abs(diff), 99):.2f}")
    print("Time-shift check (mean abs close difference if HistData is moved by N minutes):")
    for shift in (-120, -60, -5, -1, 0, 1, 5, 60, 120):
        idx = (h.index + shift * 60).intersection(d.index)
        if len(idx) == 0:
            continue
        m = np.abs(h.loc[idx - shift * 60, "c"].to_numpy() - d.loc[idx, "c"].to_numpy()).mean()
        print(f"  shift {shift:+4d} min: {m:8.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
