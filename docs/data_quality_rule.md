# Data quality rule (fixed 2026-11-16, before any re-run)

Written before recomputing any performance number with it. Code: `backend/app/core/data_quality.py`.
Do not change the thresholds after seeing results.

## Rule
A New York trading date is **valid** when, inside the NAS100 holding window **03:00–15:55 New York**
(775 one-minute bars on a full day):

1. at least **765 of 775** minutes have a bar, and
2. no run of missing minutes is longer than **5 minutes** (missing minutes at the start or end of the window count).

Otherwise the date is **invalid**: backtests can be run on valid dates only (`run(..., valid_dates=...)`),
and every report shows both "all sessions" and "valid sessions only". Missing prices are never filled in.

## Why these numbers
- 765/775 allows about 1% isolated missing minutes (normal for HistData) but not missing hours.
- A 5-minute hole is one whole 5-minute bar: a strategy bar or a fill/exit could be wrong beyond that.
- The window is the longest holding window used by any NAS100 strategy (London variants), so one rule covers all.

## What was already seen before this rule was fixed (disclosed)
- Data counts: 2023 has 116 dates with fewer than 300 regular-hours minutes; 30,652 missing intraday minutes;
  other years have 7–13 such dates (mostly US holidays / early closes).
- 75 of the 4,774 saved backtest trades were held through a data hole longer than 5 minutes; their average was
  -0.33R against -0.22R overall. That number was seen during the audit before this rule was written.
  The rule above was not tuned on it (it is the plain "one missing 5-minute bar" threshold).

## Side effects (expected)
- US holidays and early-close days fail the rule (the data stops early), so the 20 trades that were held
  past 15:55 or into the next day by holiday/early-close data are excluded in the valid-only results.
- Excluding dates changes which trades the risk manager allows on later dates (daily/weekly limits), so
  valid-only results are a fresh engine run, not a filter of the old trade list.
