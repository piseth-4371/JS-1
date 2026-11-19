"""Nearby-settings check, required in every pre-registration (docs/preregistration_template.md).

For each number in the rule that could have been chosen differently, the pre-registration fixes one smaller and one
larger neighbour value in advance. Each neighbour is run with all other settings unchanged, in the same period and
with the same costs. A real effect should still be there when a setting moves a little (a plateau); a result that
only exists at the exact chosen value (a spike) is probably luck or curve fitting.

Neighbour runs are a robustness check only: a neighbour can NEVER replace the chosen setting.
Pass the average net result per trade (R or %) of the chosen setting and of every neighbour, for ONE period.
"""
from __future__ import annotations

import math
import statistics

MIN_SHARE = 2 / 3       # at least this share of neighbours must have an average above 0
SPIKE_RATIO = 2.0       # chosen average may be at most this many times the median neighbour average


def nearby_check(chosen: float, neighbours: dict[str, float], min_share: float = MIN_SHARE,
                 spike_ratio: float = SPIKE_RATIO) -> dict:
    """{'applies', 'passed', 'positive', 'needed', 'total', 'median', 'reasons'} for one period.

    neighbours: {"hold 3 days (chosen 4)": avg_net, ...}. Empty = the rule has no free settings -> not applicable.
    """
    if not neighbours:
        return {"applies": False, "passed": True, "positive": 0, "needed": 0, "total": 0, "median": None,
                "reasons": ["no free settings: nothing to vary"]}
    values = list(neighbours.values())
    positive = sum(v > 0 for v in values)
    needed = math.ceil(min_share * len(values) - 1e-9)
    median = statistics.median(values)
    reasons: list[str] = []
    if positive < needed:
        bad = ", ".join(k for k, v in neighbours.items() if not v > 0)
        reasons.append(f"plateau: only {positive} of {len(values)} nearby settings above 0 (need {needed}); "
                       f"not above 0: {bad}")
    if chosen > 0 and not (median > 0 and chosen <= spike_ratio * median):
        reasons.append(f"spike: chosen {chosen:+.3f} is more than {spike_ratio:g}x the median nearby {median:+.3f}")
    return {"applies": True, "passed": not reasons, "positive": positive, "needed": needed, "total": len(values),
            "median": median, "reasons": reasons}


def table(chosen_label: str, chosen: float, neighbours: dict[str, float], unit: str = "R") -> str:
    """Markdown table for a report."""
    out = [f"| setting | average per trade ({unit}) |", "|---|---:|", f"| **{chosen_label} (chosen)** | {chosen:+.3f} |"]
    out += [f"| {k} | {v:+.3f} |" for k, v in neighbours.items()]
    return "\n".join(out)
