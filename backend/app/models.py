"""Database tables (SQLAlchemy ORM).

Timestamps are stored as integer UTC epoch seconds (`ts`): unambiguous,
time-zone safe, and identical in SQLite and PostgreSQL.
"""
from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BarRow(Base):
    __tablename__ = "bars"
    __table_args__ = (UniqueConstraint("source", "symbol", "timeframe", "ts", name="uq_bar"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(40), index=True)   # e.g. "mt5:MetaQuotes-Demo", "dukascopy"
    symbol: Mapped[str] = mapped_column(String(30), index=True)   # the feed's own symbol name
    timeframe: Mapped[str] = mapped_column(String(5))             # "M1"
    ts: Mapped[int] = mapped_column(BigInteger, index=True)       # bar OPEN time, UTC epoch seconds
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


# ---------------------------------------------------------------- paper trading

class ControlRow(Base):
    """Persisted switches (survive restarts): kill_switch, auto_trading, active_strategy."""
    __tablename__ = "controls"
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))
    updated_ts: Mapped[int] = mapped_column(BigInteger)


class SignalRow(Base):
    """Every strategy decision at a 5m close, including WAIT."""
    __tablename__ = "signals"
    __table_args__ = (UniqueConstraint("strategy", "bar_close_ts", name="uq_signal"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy: Mapped[str] = mapped_column(String(40))
    bar_close_ts: Mapped[int] = mapped_column(BigInteger, index=True)
    created_ts: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(10))            # LONG / SHORT / WAIT
    kind: Mapped[str | None] = mapped_column(String(10))
    entry: Mapped[float | None] = mapped_column(Float)
    stop: Mapped[float | None] = mapped_column(Float)
    target: Mapped[float | None] = mapped_column(Float)
    expiry_ts: Mapped[int | None] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(40))
    data_ts: Mapped[int] = mapped_column(BigInteger)            # last bar used
    risk_approved: Mapped[bool | None] = mapped_column(Boolean)
    risk_reasons: Mapped[list] = mapped_column(JSON, default=list)
    risk_qty: Mapped[float | None] = mapped_column(Float)


class ScannerSignalRow(Base):
    """Signals-only scanner record (no order is ever placed). Outcome filled in later from real prices."""
    __tablename__ = "scanner_signals"
    __table_args__ = (UniqueConstraint("market", "strategy", "bar_close_ts", name="uq_scanner_signal"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(10))            # nas100 / btc / gold
    strategy: Mapped[str] = mapped_column(String(40))
    bar_close_ts: Mapped[int] = mapped_column(BigInteger, index=True)
    created_ts: Mapped[int] = mapped_column(BigInteger)
    side: Mapped[int] = mapped_column(Integer)                 # +1 long, -1 short
    kind: Mapped[str] = mapped_column(String(10))
    entry: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    target: Mapped[float | None] = mapped_column(Float)
    rr_target: Mapped[float] = mapped_column(Float)
    expiry_ts: Mapped[int] = mapped_column(BigInteger)
    cost_r: Mapped[float] = mapped_column(Float)               # trading cost in R
    qualified: Mapped[bool] = mapped_column(Boolean)           # strategy passed dev + validation on this market
    shown: Mapped[bool] = mapped_column(Boolean)               # was THE signal shown (not practice-only)
    reason: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(12), default="open")   # open / filled / target / stop / expired / session_end
    filled_ts: Mapped[int | None] = mapped_column(BigInteger)
    resolved_ts: Mapped[int | None] = mapped_column(BigInteger)
    r: Mapped[float | None] = mapped_column(Float)
    # Fill model v2 (shared fill rules + recorded costs). Rows without it are "legacy" (first fill model):
    # kept for history, never mixed into the new statistics. Loaded with the row (selectin) so the API
    # can read it after its session closes.
    execution: Mapped["ScannerExecutionRow | None"] = relationship(
        back_populates="signal", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class ScannerExecutionRow(Base):
    """How a scanner signal was simulated: fill-model version, the costs used, and the actual fill/exit prices."""
    __tablename__ = "scanner_executions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("scanner_signals.id"), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer)
    costs: Mapped[dict] = mapped_column(JSON, default=dict)          # e.g. {"spread": 1.5, "slippage": 0.5, ...}
    fill_price: Mapped[float | None] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float)
    signal: Mapped[ScannerSignalRow] = relationship(back_populates="execution")


class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_order_id: Mapped[str] = mapped_column(String(80), unique=True)   # prevents duplicates
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"))
    strategy: Mapped[str] = mapped_column(String(40))
    side: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(10))
    qty: Mapped[float] = mapped_column(Float)
    entry: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    target: Mapped[float | None] = mapped_column(Float)
    rr_target: Mapped[float] = mapped_column(Float)
    cancel_level: Mapped[float | None] = mapped_column(Float)
    created_ts: Mapped[int] = mapped_column(BigInteger)
    active_from_ts: Mapped[int] = mapped_column(BigInteger)
    expiry_ts: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(12), index=True)   # pending / filled / cancelled
    status_reason: Mapped[str] = mapped_column(String(200), default="")
    fill_price: Mapped[float | None] = mapped_column(Float)
    fill_ts: Mapped[int | None] = mapped_column(BigInteger)


class PositionRow(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    strategy: Mapped[str] = mapped_column(String(40))
    side: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(10))
    qty: Mapped[float] = mapped_column(Float)
    entry: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)
    opened_ts: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(10), index=True)   # open / closed
    closed_ts: Mapped[int | None] = mapped_column(BigInteger)
    exit_price: Mapped[float | None] = mapped_column(Float)
    exit_reason: Mapped[str | None] = mapped_column(String(20))
    pnl_usd: Mapped[float | None] = mapped_column(Float)
    r: Mapped[float | None] = mapped_column(Float)
    risk_pts: Mapped[float] = mapped_column(Float)


class EventRow(Base):
    """Audit log: everything important that happened, in order."""
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[int] = mapped_column(BigInteger, index=True)
    level: Mapped[str] = mapped_column(String(8))      # INFO / WARN / ERROR
    type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
