"""Back up the database to backend/data/backups (keeps the newest 7 by default).

  .\\.venv\\Scripts\\python scripts\\backup_db.py
  .\\.venv\\Scripts\\python scripts\\backup_db.py --keep 14

Restore: stop the server, then copy a backup over backend/data/app.db.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.core.backup import backup, sqlite_path  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--keep", type=int, default=7)
    a = p.parse_args()
    db = sqlite_path(get_settings().database_url, ROOT)
    out = backup(db, ROOT / "data" / "backups", keep=a.keep)
    print(f"Backup written: {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
