"""Write the daily paper-trading report (read-only).

  .\\.venv\\Scripts\\python scripts\\daily_report.py                 # yesterday (New York date)
  .\\.venv\\Scripts\\python scripts\\daily_report.py --day 2026-11-13

Saved to backend/data/reports/paper_<date>.md (not in Git: it is your private journal).
"""
import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.core.daily_report import build  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.repository import init_db  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    yesterday = datetime.now(ZoneInfo("America/New_York")).date() - timedelta(days=1)
    p.add_argument("--day", type=date.fromisoformat, default=yesterday)
    a = p.parse_args()
    init_db()
    with Session(get_engine()) as s:
        text = build(s, a.day, get_settings().starting_balance)
    out = ROOT / "data" / "reports" / f"paper_{a.day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"Saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
