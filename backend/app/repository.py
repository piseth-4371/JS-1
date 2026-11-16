"""Save and load bars. The only module that talks SQL for market data."""
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.market_data import Bar
from app.db import get_engine
from app.models import Base, BarRow


def init_db() -> None:
    """Create tables if they don't exist (Alembic migrations come later), then add any NEW nullable
    columns to existing tables. Only adds; never drops, renames or rewrites data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    _add_missing_nullable_columns(engine)


def _add_missing_nullable_columns(engine) -> None:
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        have = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in have or not col.nullable or col.primary_key:
                continue
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col.type.compile(engine.dialect)}'))


def save_bars(bars: list[Bar], *, update_existing: bool = False) -> int:
    """Insert bars; optionally refresh existing bars with finalized OHLCV.

    Normal backfills skip duplicates. The live MT5 pull uses ``update_existing``
    to repair candles that an older version may have stored before they closed.
    Returns how many rows were sent.
    """
    if not bars:
        return 0
    engine = get_engine()
    insert = pg_insert if engine.dialect.name == "postgresql" else sqlite_insert
    rows = [b.to_dict() for b in bars]
    with engine.begin() as conn:
        # SQLite limits variables per statement, so insert in chunks.
        for i in range(0, len(rows), 500):
            stmt = insert(BarRow).values(rows[i : i + 500])
            if update_existing:
                stmt = stmt.on_conflict_do_update(
                    index_elements=["source", "symbol", "timeframe", "ts"],
                    set_={name: getattr(stmt.excluded, name)
                          for name in ("open", "high", "low", "close", "volume")},
                )
            else:
                stmt = stmt.on_conflict_do_nothing()
            conn.execute(stmt)
    return len(rows)


def load_bars(source: str, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> list[Bar]:
    """Bars with start_ts <= ts < end_ts, oldest first."""
    with Session(get_engine()) as s:
        q = (
            select(BarRow)
            .where(
                BarRow.source == source,
                BarRow.symbol == symbol,
                BarRow.timeframe == timeframe,
                BarRow.ts >= start_ts,
                BarRow.ts < end_ts,
            )
            .order_by(BarRow.ts)
        )
        return [Bar.from_row(r) for r in s.scalars(q)]


def days_present(source: str, symbol: str, timeframe: str = "M1") -> set[int]:
    """UTC day numbers (ts // 86400) that already have bars - used to resume downloads."""
    with Session(get_engine()) as s:
        q = select(BarRow.ts / 86400).where(
            BarRow.source == source, BarRow.symbol == symbol, BarRow.timeframe == timeframe).distinct()
        return {int(d) for d in s.scalars(q)}


def count_bars(source: str, symbol: str, timeframe: str = "M1") -> tuple[int, int | None, int | None]:
    """(count, first_ts, last_ts) for a feed."""
    from sqlalchemy import func

    with Session(get_engine()) as s:
        q = select(func.count(), func.min(BarRow.ts), func.max(BarRow.ts)).where(
            BarRow.source == source, BarRow.symbol == symbol, BarRow.timeframe == timeframe
        )
        n, first, last = s.execute(q).one()
        return n, first, last
