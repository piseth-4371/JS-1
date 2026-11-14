"""Read optional, explicitly measured spread snapshots; never silently alter research costs."""
import json
from pathlib import Path

OBSERVATIONS = Path(__file__).resolve().parents[2] / "data" / "reports" / "scanner_spreads.json"


def read_observations() -> dict:
    try:
        value = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}
