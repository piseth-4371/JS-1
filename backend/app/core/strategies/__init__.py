from app.core.strategies.orb import OpeningRangeBreakout
from app.core.strategies.silver_bullet import SilverBullet
from app.core.strategies.sweep_mss_fvg import LondonSweepMSSFVG, SweepMSSFVG
from app.core.strategies.trend_fvg import BTCWeekendTrendFVG, LondonTrendFVG, TrendFVG
from app.core.strategies.vwap_reversion import VWAPReversion

ALL = {s.name: s for s in (TrendFVG, SweepMSSFVG, OpeningRangeBreakout, VWAPReversion, SilverBullet,
                              LondonTrendFVG, LondonSweepMSSFVG, BTCWeekendTrendFVG)}
