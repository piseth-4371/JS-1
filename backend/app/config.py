"""App settings, read from environment variables or backend/.env.

Why: keeping settings outside the code means secrets never end up in Git,
and you can change behaviour without editing Python files.
"""
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    mt5_symbol: str = "USTEC"
    mt5_gold_symbol: str = "XAUUSD"     # read-only, for the signals-only scanner
    mt5_terminal_path: str | None = None
    # MT5 bar times are in the broker's server time zone (an IANA name).
    # MetaQuotes-Demo: Europe/Athens (UTC+2 winter / UTC+3 summer). Exness: check with check_mt5.py.
    mt5_server_tz: str = "Europe/Athens"
    starting_balance: float = 1000.0

    # Background engine (reads MT5 demo bars every 20 s). Off unless turned on in .env.
    engine_enabled: bool = False
    engine_source: str = "mt5:MetaQuotes-Demo"
    # Weekend BTC book (Binance public data, paper only). Runs with the engine.
    btc_weekend_enabled: bool = True

    # Telegram alerts (one-way, signals only). Off unless both are set in .env.
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    # Owner 2026-11-19: "only bother me when there is something real". Practice setups and session-open messages are
    # OFF by default; real signals, feed problems, news heads-ups, the monthly summary and the turn-of-month
    # paper test are always sent (when Telegram is configured).
    telegram_practice_alerts: bool = False   # also send setups from strategies that FAILED their backtest (labelled)
    telegram_session_alerts: bool = False    # "London / New York window open" messages
    telegram_news_alerts: bool = True        # heads-up 30 min before high-impact news, with its usual effect
    telegram_monthly_report: bool = True     # results summary on the first scanner cycle of each month
    telegram_tom_alerts: bool = True         # turn-of-month paper test: bought / finished / void

    # Only "paper" is allowed. There is no live trading in this codebase.
    trading_mode: Literal["paper"] = "paper"


@lru_cache
def get_settings() -> Settings:
    return Settings()
