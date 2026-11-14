# Intraday momentum research (NAS100) — generated 2026-11-14 12:54 UTC

- Rules fixed before testing: docs/intraday_momentum_preregistration.md (commit 406b7fb)
- Data: HistData NSXUSD 1-minute bars 2019-2024 (2025+ locked); 1338 tradable days
- Trade 15:30 → 15:55 NY in the direction of the first half-hour return (prev 16:00 → 10:00); stop 2×ATR14(5m); cost 2.0 points [assumption]

| split | trades | long/short | win% | avg R | avg R costs x2 | avg R no cost | always-long avg R | random-direction avg R | beats random in | P(no edge) | PASS? |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| development | 969 | 546/423 | 45% | -0.085 | -0.178 | +0.009 | -0.117 | -0.095 | 65% | 100% | FAIL |
| validation | 369 | 209/160 | 45% | -0.078 | -0.135 | -0.020 | -0.053 | -0.043 | 20% | 97% | FAIL |

Information only (does not count): the paper's full 15:30 → 16:00 window

| split | trades | avg R | always-long avg R | beats random in |
|---|---:|---:|---:|---:|
| development | 969 | -0.104 | -0.090 | 34% |
| validation | 369 | -0.037 | -0.005 | 54% |

## Verdict: **FAILS**

Pass needs, in BOTH splits: avg R > 0 after costs, ≥100 trades, beat the random-direction control in ≥90% of 500 runs, and beat always-long. Past results do not guarantee future results. Research only.
