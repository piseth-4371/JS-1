from app.core.strategies.orb import BTCWeekendORB, OpeningRangeBreakout
from app.core.strategies.silver_bullet import BTCWeekendSilverBullet, SilverBullet
from app.core.strategies.sweep_mss_fvg import BTCWeekendSweepMSSFVG, LondonSweepMSSFVG, SweepMSSFVG
from app.core.strategies.trend_fvg import BTCWeekendTrendFVG, LondonTrendFVG, TrendFVG
from app.core.strategies.vwap_reversion import BTCWeekendVWAPReversion, VWAPReversion

ALL = {s.name: s for s in (TrendFVG, SweepMSSFVG, OpeningRangeBreakout, VWAPReversion, SilverBullet,
                              LondonTrendFVG, LondonSweepMSSFVG, BTCWeekendTrendFVG, BTCWeekendSweepMSSFVG,
                              BTCWeekendORB, BTCWeekendVWAPReversion, BTCWeekendSilverBullet)}
