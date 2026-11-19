"""Year-by-year check, required in every pre-registration (docs/preregistration_template.md).

Pass a list of (year, net result) per trade for ONE period (development or validation). The year is the entry
year in New York time. Results can be in R or % — the check only looks at signs and sums.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_TRADES = 10         # a year with fewer trades does not count
MIN_YEARS = 2           # fewer counting years than this -> the check cannot pass


@dataclass(frozen=True)
class YearRow:
    year: int
    trades: int
    avg: float
    total: float
    counts: bool                 # at least MIN_TRADES trades


def by_year(trades: list[tuple[int, float]], min_trades: int = MIN_TRADES) -> list[YearRow]:
    groups: dict[int, list[float]] = {}
    for year, net in trades:
        groups.setdefault(int(year), []).append(float(net))
    return [YearRow(y, len(v), sum(v) / len(v), sum(v), len(v) >= min_trades) for y, v in sorted(groups.items())]


def year_check(rows: list[YearRow], min_years: int = MIN_YEARS) -> dict:
    """{'passed', 'counting_years', 'positive_years', 'total_without_best', 'reasons'} for one period."""
    used = [r for r in rows if r.counts]
    reasons: list[str] = []
    positive = sum(r.avg > 0 for r in used)
    without_best = None
    if len(used) < min_years:
        reasons.append(f"not enough years: {len(used)} with at least {MIN_TRADES} trades (need {min_years})")
    else:
        if not positive * 2 > len(used):
            reasons.append(f"most years positive: only {positive} of {len(used)} years above 0")
        best = max(used, key=lambda r: r.total)
        without_best = sum(r.total for r in used) - best.total
        if not without_best > 0:
            reasons.append(f"one lucky year: total without the best year ({best.year}) is {without_best:+.3f}")
    return {"passed": not reasons, "counting_years": len(used), "positive_years": positive,
            "total_without_best": without_best, "reasons": reasons}


def table(rows: list[YearRow], unit: str = "R") -> str:
    """Markdown table for a report."""
    out = [f"| year | trades | average per trade ({unit}) | total ({unit}) |", "|---:|---:|---:|---:|"]
    for r in rows:
        note = "" if r.counts else " (too few trades)"
        out.append(f"| {r.year}{note} | {r.trades} | {r.avg:+.3f} | {r.total:+.2f} |")
    return "\n".join(out)
