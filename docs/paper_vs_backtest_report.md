# Paper engine versus backtester — results

Made by `scripts/paper_vs_backtest.py --report` on 2026-11-19. Rules: `docs/paper_vs_backtest_plan.md`. This checks the execution code (same data → same signal, fill, exit and cost?), not profitability.

**How to read it:** *identical* = both systems agree exactly. *different* = matched, but a price, time, reason or R differs. *paper only / backtest only* = only one system had it; the paper side shows why it rejected or skipped. Expected design differences: minimum lot (paper only), 30-day indicator history, stale-data checks.

## orb — journal (2026-11-13 .. 2026-11-13, 1 days, made 2026-11-17)

Cycles: {'5m bars evaluated live': 28}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 0 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 0 |

Paper signal outcomes: none. Backtest rejections: {'Invalid data session': 5}; cancelled orders: none.

No differences.

## sweep_mss_fvg — journal (2026-11-13 .. 2026-11-13, 1 days, made 2026-11-17)

Cycles: {'5m bars evaluated live': 7}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 0 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 0 |

Paper signal outcomes: none. Backtest rejections: {'Invalid data session': 13}; cancelled orders: none.

No differences.

## trend_fvg — journal (2026-11-12 .. 2026-11-13, 2 days, made 2026-11-17)

Cycles: {'5m bars evaluated live': 3}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 0 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 0 |

Paper signal outcomes: none. Backtest rejections: {'Invalid data session': 7}; cancelled orders: none.

No differences.

## vwap_reversion — journal (2026-11-12 .. 2026-11-13, 2 days, made 2026-11-17)

Cycles: {'5m bars evaluated live': 8}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 0 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 0 |

Paper signal outcomes: none. Backtest rejections: {'Invalid data session': 76}; cancelled orders: none.

No differences.

## london_sweep_mss_fvg — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 18168, 'ORDER': 4, 'REJECTED': 3}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 7 | 0 | 0 | 0 |
| trades | 1 | 0 | 0 | 0 |

Paper signal outcomes: {'approved': 4, 'Minimum lot 0.1 would risk $7.82 (0.8% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.05 (0.8% of equity) > allowed $5.00 (0.5%); An order is already pending': 1, 'An order is already pending': 1}. Backtest rejections: {'Invalid data session': 11, 'Busy: a position or order is already open': 2}; cancelled orders: {'expired': 4}.

No differences.

## london_trend_fvg — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 18167, 'ORDER': 6, 'REJECTED': 2}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 8 | 0 | 0 | 0 |
| trades | 3 | 0 | 0 | 0 |

Paper signal outcomes: {'approved': 6, 'Max 1 open position(s) reached': 1, 'Minimum lot 0.1 would risk $6.12 (0.6% of equity) > allowed $5.03 (0.5%)': 1}. Backtest rejections: {'Invalid data session': 11, 'Busy: a position or order is already open': 1}; cancelled orders: {'expired': 4}.

No differences.

## orb — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 10078, 'REJECTED': 5}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 5 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 5 |

Paper signal outcomes: {'Minimum lot 0.1 would risk $8.59 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.38 (0.5% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.30 (0.5% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $12.03 (1.2% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $7.54 (0.8% of equity) > allowed $5.00 (0.5%)': 1}. Backtest rejections: {'Invalid data session': 7}; cancelled orders: none.

Differences (first 25):

- trade 2026-10-14 09:50 side +1 BACKTEST ONLY (exit stop, R -1.029)
- trade 2026-10-19 10:00 side -1 BACKTEST ONLY (exit stop, R -1.050)
- trade 2026-10-22 10:15 side -1 BACKTEST ONLY (exit target, R +1.964)
- trade 2026-10-28 09:50 side -1 BACKTEST ONLY (exit stop, R -1.021)
- trade 2026-11-02 10:15 side +1 BACKTEST ONLY (exit stop, R -1.033)

## silver_bullet — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 10072, 'REJECTED': 11}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 11 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 2 |

Paper signal outcomes: {'Minimum lot 0.1 would risk $11.97 (1.2% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $9.38 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $10.12 (1.0% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $7.33 (0.7% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.57 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $9.05 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $7.69 (0.8% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.34 (0.5% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $12.58 (1.3% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $9.27 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.83 (0.9% of equity) > allowed $5.00 (0.5%)': 1}. Backtest rejections: {'Invalid data session': 7}; cancelled orders: {'expired': 9}.

Differences (first 25):

- trade 2026-10-29 10:10 side +1 BACKTEST ONLY (exit stop, R -1.022)
- trade 2026-10-30 11:03 side +1 BACKTEST ONLY (exit stop, R -1.026)

## sweep_mss_fvg — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 10070, 'REJECTED': 10, 'ORDER': 3}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 13 | 0 | 0 | 0 |
| trades | 1 | 0 | 0 | 3 |

Paper signal outcomes: {'Minimum lot 0.1 would risk $11.97 (1.2% of equity) > allowed $5.00 (0.5%)': 1, 'approved': 3, 'Minimum lot 0.1 would risk $8.55 (0.9% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.57 (0.9% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.70 (0.9% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.10 (0.5% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.34 (0.5% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $9.45 (0.9% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $10.81 (1.1% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $10.21 (1.0% of equity) > allowed $4.99 (0.5%)': 1, 'Minimum lot 0.1 would risk $6.66 (0.7% of equity) > allowed $4.99 (0.5%)': 1}. Backtest rejections: {'Invalid data session': 9, 'Busy: a position or order is already open': 3}; cancelled orders: {'expired': 6}.

Differences (first 25):

- trade 2026-10-29 10:10 side +1 BACKTEST ONLY (exit stop, R -1.023)
- trade 2026-10-30 11:03 side +1 BACKTEST ONLY (exit stop, R -1.039)
- trade 2026-11-04 11:31 side -1 BACKTEST ONLY (exit stop, R -1.019)

## trend_fvg — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 10078, 'REJECTED': 4, 'ORDER': 1}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 5 | 0 | 0 | 0 |
| trades | 0 | 0 | 0 | 0 |

Paper signal outcomes: {'Minimum lot 0.1 would risk $7.33 (0.7% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.57 (0.9% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $6.44 (0.6% of equity) > allowed $5.00 (0.5%)': 1, 'Minimum lot 0.1 would risk $7.07 (0.7% of equity) > allowed $5.00 (0.5%)': 1, 'approved': 1}. Backtest rejections: {'Invalid data session': 10, 'Busy: a position or order is already open': 1}; cancelled orders: {'expired': 4}.

No differences.

## vwap_reversion — replay (2026-10-14 .. 2026-11-13, 23 days, made 2026-11-19)

Cycles: {'WAIT': 10006, 'REJECTED': 45, 'ORDER': 32}

| | identical | different | paper only | backtest only |
|---|---:|---:|---:|---:|
| signals | 77 | 0 | 0 | 0 |
| trades | 23 | 0 | 9 | 15 |

Paper signal outcomes: {'Minimum lot 0.1 would risk $5.06 (0.5% of equity) > allowed $5.00 (0.5%)': 1, 'approved': 32, 'Minimum lot 0.1 would risk $5.10 (0.5% of equity) > allowed $4.99 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $5.30 (0.5% of equity) > allowed $4.96 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule)': 11, 'Minimum lot 0.1 would risk $6.57 (0.7% of equity) > allowed $4.90 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $4.97 (0.5% of equity) > allowed $4.88 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $5.84 (0.6% of equity) > allowed $4.88 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $5.61 (0.6% of equity) > allowed $4.88 (0.5%)': 1, 'Minimum lot 0.1 would risk $4.99 (0.5% of equity) > allowed $4.90 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.55 (0.9% of equity) > allowed $4.90 (0.5%)': 1, 'Max 1 open position(s) reached': 3, 'Minimum lot 0.1 would risk $6.81 (0.7% of equity) > allowed $4.89 (0.5%)': 1, 'Max 3 trades per day reached': 2, 'Max 3 trades per day reached; Max 1 open position(s) reached': 2, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $6.59 (0.7% of equity) > allowed $4.84 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.92 (0.6% of equity) > allowed $4.84 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $8.42 (0.9% of equity) > allowed $4.80 (0.5%)': 1, '2 losses in a row today - stop trading (anti-revenge rule); Minimum lot 0.1 would risk $9.59 (1.0% of equity) > allowed $4.80 (0.5%)': 1, 'Minimum lot 0.1 would risk $13.15 (1.4% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $20.24 (2.1% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $6.20 (0.6% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $12.12 (1.3% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $7.97 (0.8% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $10.86 (1.1% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $8.05 (0.8% of equity) > allowed $4.83 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.54 (0.6% of equity) > allowed $4.91 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.73 (0.6% of equity) > allowed $4.91 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.76 (0.6% of equity) > allowed $4.91 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.46 (0.6% of equity) > allowed $4.91 (0.5%)': 1, 'Minimum lot 0.1 would risk $5.41 (0.6% of equity) > allowed $4.88 (0.5%)': 1, 'Minimum lot 0.1 would risk $6.07 (0.6% of equity) > allowed $4.86 (0.5%)': 1}. Backtest rejections: {'Invalid data session': 64, '2 losses in a row today - stop trading': 22, 'Busy: a position or order is already open': 16, 'Max 3 trades per day reached': 1}; cancelled orders: none.

Differences (first 25):

- trade 2026-10-14 13:35 side +1 PAPER ONLY (exit stop, R -1.055292718563072)
- trade 2026-10-16 12:45 side +1 PAPER ONLY (exit stop, R -1.0668618069553701)
- trade 2026-10-20 11:05 side -1 PAPER ONLY (exit target, R 1.9551266126309745)
- trade 2026-10-22 13:25 side +1 PAPER ONLY (exit stop, R -1.0782096795419083)
- trade 2026-11-02 13:20 side +1 PAPER ONLY (exit stop, R -1.0732788826161255)
- trade 2026-11-09 12:15 side -1 PAPER ONLY (exit target, R 1.9100904016669726)
- trade 2026-11-09 13:40 side -1 PAPER ONLY (exit stop, R -1.090060628733008)
- trade 2026-11-09 14:15 side -1 PAPER ONLY (exit target, R 1.8732039997912926)
- trade 2026-11-11 12:05 side -1 PAPER ONLY (exit stop, R -1.1052812452108933)
- trade 2026-10-14 11:55 side +1 BACKTEST ONLY (exit stop, R -1.049)
- trade 2026-10-16 12:15 side +1 BACKTEST ONLY (exit stop, R -1.038)
- trade 2026-10-19 14:40 side +1 BACKTEST ONLY (exit session_end, R -0.002)
- trade 2026-10-20 10:35 side -1 BACKTEST ONLY (exit target, R +1.977)
- trade 2026-10-22 12:55 side +1 BACKTEST ONLY (exit stop, R -1.036)
- trade 2026-11-02 12:50 side +1 BACKTEST ONLY (exit stop, R -1.041)
- trade 2026-11-05 10:35 side +1 BACKTEST ONLY (exit stop, R -1.019)
- trade 2026-11-05 11:10 side +1 BACKTEST ONLY (exit stop, R -1.013)
- trade 2026-11-09 11:05 side -1 BACKTEST ONLY (exit stop, R -1.031)
- trade 2026-11-09 14:50 side -1 BACKTEST ONLY (exit stop, R -1.071)
- trade 2026-11-10 10:10 side -1 BACKTEST ONLY (exit target, R +1.960)
- trade 2026-11-10 12:05 side +1 BACKTEST ONLY (exit stop, R -1.045)
- trade 2026-11-10 12:45 side +1 BACKTEST ONLY (exit target, R +1.964)
- trade 2026-11-11 11:35 side -1 BACKTEST ONLY (exit stop, R -1.047)
- trade 2026-11-12 11:15 side -1 BACKTEST ONLY (exit stop, R -1.042)

