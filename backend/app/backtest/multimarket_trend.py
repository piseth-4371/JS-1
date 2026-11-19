"""Slow multi-market trend (rules: docs/multimarket_trend_preregistration.md). Pure functions, no I/O except read_fred.

Monthly: at each month end, sign of the 12-month change decides long/short; each market is sized to 10% annual
volatility; the portfolio return is the average over markets that trade that month.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_VOL, MAX_WEIGHT, VOL_DAYS, MIN_OBS, LOOKBACK = 0.10, 4.0, 63, 10, 12
FINANCING = 0.02
COSTS = {"equity": 0.0005, "currency": 0.0003, "oil": 0.0010, "gas": 0.0020}


@dataclass(frozen=True)
class Market:
    name: str
    fred_id: str
    asset_class: str      # equity | energy | currency
    cost_key: str         # key into COSTS
    invert: bool = False  # True: use 1 / value (so the price is USD per unit of the foreign currency)


MARKETS = [
    Market("Nasdaq Composite", "NASDAQCOM", "equity", "equity"),
    Market("Nikkei 225", "NIKKEI225", "equity", "equity"),
    Market("WTI crude oil", "DCOILWTICO", "energy", "oil"),
    Market("Henry Hub natural gas", "DHHNGSP", "energy", "gas"),
    Market("Japanese yen", "DEXJPUS", "currency", "currency", invert=True),
    Market("British pound", "DEXUSUK", "currency", "currency"),
    Market("Canadian dollar", "DEXCAUS", "currency", "currency", invert=True),
    Market("Swiss franc", "DEXSZUS", "currency", "currency", invert=True),
    Market("Australian dollar", "DEXUSAL", "currency", "currency"),
    Market("Euro", "DEXUSEU", "currency", "currency"),
]


def non_positive(path: Path) -> list[str]:
    """Dates whose value is at or below 0 (excluded by Amendment 1)."""
    df = pd.read_csv(path, dtype=str)
    v = pd.to_numeric(df.iloc[:, 1].str.strip().replace({".": None, "": None}), errors="coerce")
    return df["observation_date"][v <= 0].tolist()


def read_fred(path: Path, invert: bool = False) -> pd.Series:
    """FRED csv -> daily Series (DatetimeIndex). Empty or '.' values are dropped, never filled. Values at or below 0
    are treated as missing (Amendment 1: WTI 2020-04-20)."""
    df = pd.read_csv(path, dtype=str)
    if list(df.columns)[0] != "observation_date" or len(df.columns) != 2:
        raise ValueError(f"{path.name}: unexpected columns {list(df.columns)}")
    v = pd.to_numeric(df.iloc[:, 1].str.strip().replace({".": None, "": None}), errors="coerce")
    s = pd.Series(v.to_numpy(), index=pd.to_datetime(df["observation_date"]), name=df.columns[1]).dropna()
    s = s[s > 0]
    if s.index.max() >= pd.Timestamp("2025-01-01"):
        raise ValueError(f"{path.name}: contains 2025+ data, which must not be read")
    return (1.0 / s) if invert else s


def monthly_table(daily: pd.Series, months: pd.PeriodIndex) -> pd.DataFrame:
    """Per calendar month: month-end close (NaN if fewer than MIN_OBS values) and the volatility known at that close."""
    lr = np.log(daily).diff()
    sigma = lr.rolling(VOL_DAYS).std() * np.sqrt(252)
    per = daily.index.to_period("M")
    g = pd.DataFrame({"p": daily.to_numpy(), "sigma": sigma.to_numpy(), "m": per}).groupby("m")
    t = pd.DataFrame({"close": g["p"].last(), "sigma": g["sigma"].last(), "n": g["p"].size()})
    t.loc[t["n"] < MIN_OBS, ["close", "sigma"]] = np.nan
    return t.reindex(months)


def market_arrays(table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Indexed by RETURN month m: (trades, signal, weight, return). Decided at the close of month m-1."""
    c = table["close"].to_numpy(dtype=float)
    sg = table["sigma"].to_numpy(dtype=float)
    n = len(c)
    prev, cur, back, sig_prev = (np.full(n, np.nan) for _ in range(4))
    prev[1:], cur[:], sig_prev[1:] = c[:-1], c, sg[:-1]
    back[LOOKBACK + 1:] = c[:n - LOOKBACK - 1]
    ok = np.isfinite(prev) & np.isfinite(cur) & np.isfinite(back) & np.isfinite(sig_prev) & (sig_prev > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        signal = np.where(ok, np.sign(prev / back - 1.0), 0.0)
        weight = np.where(ok, np.minimum(TARGET_VOL / sig_prev, MAX_WEIGHT), 0.0)
        ret = np.where(ok, cur / prev - 1.0, 0.0)
    return ok, signal, weight, ret


@dataclass
class Panel:
    months: pd.PeriodIndex
    names: list[str]
    classes: list[str]
    trades: np.ndarray    # (M, K) bool
    signal: np.ndarray    # (M, K)
    weight: np.ndarray    # (M, K)
    ret: np.ndarray       # (M, K)
    cost: np.ndarray      # (K,) one-way cost per unit of notional traded


def build_panel(daily: dict[str, pd.Series], markets=MARKETS, first="1971-01", last="2024-12") -> Panel:
    months = pd.period_range(first, last, freq="M")
    cols = [market_arrays(monthly_table(daily[m.fred_id], months)) for m in markets]
    stack = lambda i: np.column_stack([c[i] for c in cols])  # noqa: E731
    return Panel(months, [m.name for m in markets], [m.asset_class for m in markets], stack(0).astype(bool), stack(1),
                 stack(2), stack(3), np.array([COSTS[m.cost_key] for m in markets]))


def market_returns(trades, signs, weight, ret, cost, cost_mult: float = 1.0):
    """Gross and net return per month and market (works on (M, K) or (R, M, K) signs). Position = weight x sign;
    trading cost on the change from last month's position (0 when the market did not trade), plus financing."""
    pos = np.where(trades, weight * signs, 0.0)
    prev = np.zeros_like(pos)
    prev[..., 1:, :] = pos[..., :-1, :]
    gross = pos * ret
    costs = np.where(trades, np.abs(pos - prev) * cost + FINANCING * np.abs(pos) / 12.0, 0.0) * cost_mult
    return gross, gross - costs


def portfolio(trades, per_market) -> np.ndarray:
    """Equal-risk average over the markets that trade each month (NaN when none trade)."""
    n = trades.sum(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, np.where(trades, per_market, 0.0).sum(axis=-1) / np.maximum(n, 1), np.nan)


def sharpe(r) -> float:
    r = np.asarray(r, dtype=float)
    sd = r.std(ddof=1) if r.size > 1 else 0.0
    return float(r.mean() / sd * np.sqrt(12)) if sd > 0 else float("nan")


def max_drawdown(r) -> float:
    eq = np.cumprod(1 + np.asarray(r, dtype=float))
    return float((eq / np.maximum.accumulate(eq) - 1).min()) if eq.size else 0.0


def block_bootstrap_sharpe(r, block: int = 12, runs: int = 5000, seed: int = 11) -> tuple[float, float]:
    """95% range of the Sharpe ratio from moving-block resampling of whole 12-month blocks."""
    r = np.asarray(r, dtype=float)
    n = r.size
    rng = np.random.default_rng(seed)
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(runs, k))
    idx = (starts[:, :, None] + np.arange(block)).reshape(runs, -1)[:, :n]
    s = r[idx]
    sd = s.std(axis=1, ddof=1)
    sh = np.where(sd > 0, s.mean(axis=1) / np.where(sd > 0, sd, 1) * np.sqrt(12), np.nan)
    lo, hi = np.nanpercentile(sh, [2.5, 97.5])
    return float(lo), float(hi)


def random_sign_sharpes(p: Panel, mask: np.ndarray, runs: int = 5000, seed: int = 11, chunk: int = 500) -> np.ndarray:
    """Net Sharpe of `runs` random-direction portfolios over the months in `mask` (same weights and costs)."""
    rng = np.random.default_rng(seed)
    out = []
    for start in range(0, runs, chunk):
        n = min(chunk, runs - start)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(n,) + p.trades.shape)
        _, net = market_returns(p.trades, signs, p.weight, p.ret, p.cost)
        port = portfolio(p.trades, net)[:, mask]
        sd = port.std(axis=1, ddof=1)
        out.append(np.where(sd > 0, port.mean(axis=1) / np.where(sd > 0, sd, 1) * np.sqrt(12), np.nan))
    return np.concatenate(out)


PASS, NEGATIVE, INCONCLUSIVE = "passes the research criteria", "negative observed result", "inconclusive"


@dataclass(frozen=True)
class PeriodCheck:
    months: int
    avg_markets: float
    sharpe: float
    sharpe_low: float
    random_p95: float
    stress_sharpe: float


def verdict(dev: PeriodCheck, val: PeriodCheck) -> str:
    if any(not (c.sharpe > 0) for c in (dev, val)):
        return NEGATIVE
    ok = all(c.sharpe_low > 0 and c.sharpe > c.random_p95 and c.stress_sharpe > 0 and c.months >= 120
             and c.avg_markets >= 4 for c in (dev, val))
    return PASS if ok else INCONCLUSIVE
