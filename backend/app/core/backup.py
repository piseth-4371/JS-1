"""Safe copies of the SQLite database (the paper journal + downloaded history).

Uses SQLite's own backup API, so the copy is consistent even while the server is writing.
Only the newest `keep` backups are kept; older ones are deleted (they are our own files).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def sqlite_path(database_url: str, base: Path) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Backups here only support SQLite. For PostgreSQL use pg_dump.")
    p = Path(database_url.removeprefix("sqlite:///"))
    return p if p.is_absolute() else (base / p).resolve()


def backup(db_file: Path, out_dir: Path, keep: int = 7, now: datetime | None = None) -> Path:
    if not db_file.exists():
        raise FileNotFoundError(db_file)
    if keep < 1:
        raise ValueError("keep must be at least 1")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%S")
    target = out_dir / f"app_{stamp}.db"
    src = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    old = sorted(out_dir.glob("app_*.db"))[:-keep]
    for f in old:
        f.unlink()
    return target
