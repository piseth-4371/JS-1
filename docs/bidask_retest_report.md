# Bid/ask re-test on 2023 (Dukascopy) — results

Made by `scripts/bidask_retest.py` on 2026-11-17. Rules fixed in `docs/bidask_retest_preregistration.md` (commit 8a9c21d) before the data was downloaded. Measurement only: nothing can qualify from this test; `scanner.QUALIFIED` stays empty.

## Data

- Dukascopy USATECHIDXUSD BID + ASK, 2022-12-01..2023-12-31 (December 2022 = warm-up only). 368,950 minutes with both quotes.
- 2023 weekdays with data: 257; valid under the session rule: 247 (HistData 2023: 256 / 137).
- Minutes where ask < bid: 0. Quoted spread (ask close − bid close): 03:00-15:55 NY median 3.05, p90 3.50; 09:30-16:00 median 1.45, p90 1.52 points. This is Dukascopy's spread, not Exness's.

## Pre-registered decisions (valid sessions, 2023 trades)

| strategy | V1 bid-only | V2 synthetic ask | V3 real bid/ask | V2 − V1 | bid-only model | V3 ≤ 0 | V3 95% range |
|---|---:|---:|---:|---:|---|---|---|
| trend_fvg | -0.225 | -0.204 | -0.204 | +0.021 | pessimistic | yes | -0.54 to +0.13 |
| sweep_mss_fvg | -0.030 | -0.029 | -0.028 | +0.001 | not material | yes | -0.33 to +0.27 |
| orb | -0.222 | -0.213 | -0.213 | +0.010 | not material | yes | -0.50 to +0.08 |
| vwap_reversion | -0.132 | -0.117 | -0.104 | +0.015 | not material | yes | -0.23 to +0.03 |
| silver_bullet | +0.319 | +0.314 | +0.315 | -0.005 | not material | NO | -0.08 to +0.71 |
| london_trend_fvg | -0.052 | -0.057 | -0.201 | -0.005 | not material | yes | -0.49 to +0.09 |
| london_sweep_mss_fvg | -0.660 | -0.525 | -0.600 | +0.135 | pessimistic | yes | -0.93 to -0.27 |

**Conclusion rule:** every strategy's V3 average ≤ 0 → 'no edge after costs' reinforced: **NO (see table; still cannot qualify)**.

## All results (2023 trades only)

| strategy | variant | sessions | trades | avg R | 95% iid | 95% week | max DD |
|---|---|---|---:|---:|---|---|---:|
| trend_fvg | V1 bid-only | all | 65 | -0.242 | -0.57 to +0.09 | -0.55 to +0.07 | 13.4% |
| trend_fvg | V1 bid-only | valid | 64 | -0.225 | -0.56 to +0.11 | -0.55 to +0.11 | 13.4% |
| trend_fvg | V2 synthetic ask | all | 64 | -0.218 | -0.55 to +0.11 | -0.54 to +0.10 | 13.4% |
| trend_fvg | V2 synthetic ask | valid | 63 | -0.204 | -0.54 to +0.13 | -0.53 to +0.13 | 13.4% |
| trend_fvg | V3 real bid/ask | all | 64 | -0.218 | -0.55 to +0.11 | -0.54 to +0.10 | 13.4% |
| trend_fvg | V3 real bid/ask | valid | 63 | -0.204 | -0.54 to +0.13 | -0.53 to +0.13 | 13.4% |
| trend_fvg | HistData 2023 (reference) | all | 46 | -0.429 | -0.79 to -0.06 | -0.76 to -0.08 | 11.9% |
| trend_fvg | HistData 2023 (reference) | valid | 35 | -0.554 | -0.94 to -0.17 | -0.89 to -0.16 | 11.0% |
| sweep_mss_fvg | V1 bid-only | all | 79 | -0.026 | -0.33 to +0.27 | -0.31 to +0.26 | 8.1% |
| sweep_mss_fvg | V1 bid-only | valid | 78 | -0.030 | -0.33 to +0.27 | -0.32 to +0.25 | 8.3% |
| sweep_mss_fvg | V2 synthetic ask | all | 77 | -0.023 | -0.32 to +0.27 | -0.31 to +0.26 | 7.8% |
| sweep_mss_fvg | V2 synthetic ask | valid | 76 | -0.029 | -0.33 to +0.27 | -0.32 to +0.26 | 8.0% |
| sweep_mss_fvg | V3 real bid/ask | all | 77 | -0.022 | -0.32 to +0.28 | -0.31 to +0.26 | 7.7% |
| sweep_mss_fvg | V3 real bid/ask | valid | 76 | -0.028 | -0.33 to +0.27 | -0.32 to +0.26 | 7.9% |
| sweep_mss_fvg | HistData 2023 (reference) | all | 62 | +0.120 | -0.25 to +0.49 | -0.22 to +0.43 | 3.7% |
| sweep_mss_fvg | HistData 2023 (reference) | valid | 50 | +0.157 | -0.24 to +0.55 | -0.20 to +0.50 | 3.3% |
| orb | V1 bid-only | all | 88 | -0.213 | -0.50 to +0.07 | -0.47 to +0.06 | 10.8% |
| orb | V1 bid-only | valid | 83 | -0.222 | -0.51 to +0.07 | -0.48 to +0.06 | 10.6% |
| orb | V2 synthetic ask | all | 88 | -0.194 | -0.48 to +0.09 | -0.45 to +0.07 | 10.7% |
| orb | V2 synthetic ask | valid | 83 | -0.213 | -0.50 to +0.08 | -0.47 to +0.06 | 10.5% |
| orb | V3 real bid/ask | all | 88 | -0.194 | -0.48 to +0.09 | -0.45 to +0.07 | 10.7% |
| orb | V3 real bid/ask | valid | 83 | -0.213 | -0.50 to +0.08 | -0.47 to +0.06 | 10.5% |
| orb | HistData 2023 (reference) | all | 62 | -0.408 | -0.75 to -0.07 | -0.72 to -0.08 | 13.6% |
| orb | HistData 2023 (reference) | valid | 43 | -0.332 | -0.72 to +0.05 | -0.67 to +0.05 | 8.6% |
| vwap_reversion | V1 bid-only | all | 462 | -0.136 | -0.27 to -0.00 | -0.26 to -0.00 | 30.4% |
| vwap_reversion | V1 bid-only | valid | 457 | -0.132 | -0.26 to -0.00 | -0.26 to +0.00 | 29.6% |
| vwap_reversion | V2 synthetic ask | all | 459 | -0.119 | -0.25 to +0.01 | -0.24 to -0.00 | 26.7% |
| vwap_reversion | V2 synthetic ask | valid | 454 | -0.117 | -0.25 to +0.01 | -0.23 to +0.00 | 26.2% |
| vwap_reversion | V3 real bid/ask | all | 459 | -0.106 | -0.23 to +0.02 | -0.22 to +0.01 | 24.5% |
| vwap_reversion | V3 real bid/ask | valid | 454 | -0.104 | -0.23 to +0.03 | -0.22 to +0.02 | 23.9% |
| vwap_reversion | HistData 2023 (reference) | all | 376 | -0.262 | -0.41 to -0.11 | -0.41 to -0.12 | 41.8% |
| vwap_reversion | HistData 2023 (reference) | valid | 252 | -0.138 | -0.32 to +0.04 | -0.29 to +0.00 | 19.6% |
| silver_bullet | V1 bid-only | all | 57 | +0.289 | -0.10 to +0.68 | -0.10 to +0.67 | 3.2% |
| silver_bullet | V1 bid-only | valid | 55 | +0.319 | -0.08 to +0.72 | -0.08 to +0.72 | 3.2% |
| silver_bullet | V2 synthetic ask | all | 57 | +0.292 | -0.09 to +0.68 | -0.10 to +0.67 | 3.0% |
| silver_bullet | V2 synthetic ask | valid | 55 | +0.314 | -0.08 to +0.71 | -0.08 to +0.70 | 3.0% |
| silver_bullet | V3 real bid/ask | all | 57 | +0.292 | -0.09 to +0.68 | -0.09 to +0.67 | 3.0% |
| silver_bullet | V3 real bid/ask | valid | 55 | +0.315 | -0.08 to +0.71 | -0.08 to +0.70 | 3.0% |
| silver_bullet | HistData 2023 (reference) | all | 34 | +0.238 | -0.28 to +0.76 | -0.25 to +0.71 | 3.2% |
| silver_bullet | HistData 2023 (reference) | valid | 31 | +0.394 | -0.15 to +0.93 | -0.13 to +0.92 | 3.2% |
| london_trend_fvg | V1 bid-only | all | 106 | -0.076 | -0.35 to +0.20 | -0.33 to +0.18 | 10.0% |
| london_trend_fvg | V1 bid-only | valid | 104 | -0.052 | -0.33 to +0.23 | -0.30 to +0.20 | 9.3% |
| london_trend_fvg | V2 synthetic ask | all | 100 | -0.067 | -0.35 to +0.21 | -0.31 to +0.19 | 9.6% |
| london_trend_fvg | V2 synthetic ask | valid | 99 | -0.057 | -0.34 to +0.22 | -0.30 to +0.19 | 9.1% |
| london_trend_fvg | V3 real bid/ask | all | 88 | -0.211 | -0.50 to +0.07 | -0.48 to +0.07 | 14.2% |
| london_trend_fvg | V3 real bid/ask | valid | 87 | -0.201 | -0.49 to +0.09 | -0.46 to +0.07 | 13.7% |
| london_trend_fvg | HistData 2023 (reference) | all | 103 | -0.234 | -0.59 to +0.12 | -0.61 to +0.11 | 17.0% |
| london_trend_fvg | HistData 2023 (reference) | valid | 58 | +0.048 | -0.34 to +0.43 | -0.29 to +0.41 | 4.5% |
| london_sweep_mss_fvg | V1 bid-only | all | 41 | -0.660 | -1.01 to -0.31 | -1.04 to -0.23 | 14.4% |
| london_sweep_mss_fvg | V1 bid-only | valid | 41 | -0.660 | -1.01 to -0.31 | -1.04 to -0.23 | 14.4% |
| london_sweep_mss_fvg | V2 synthetic ask | all | 41 | -0.525 | -0.88 to -0.17 | -0.90 to -0.10 | 12.0% |
| london_sweep_mss_fvg | V2 synthetic ask | valid | 41 | -0.525 | -0.88 to -0.17 | -0.90 to -0.10 | 12.0% |
| london_sweep_mss_fvg | V3 real bid/ask | all | 41 | -0.600 | -0.93 to -0.27 | -0.97 to -0.19 | 13.4% |
| london_sweep_mss_fvg | V3 real bid/ask | valid | 41 | -0.600 | -0.93 to -0.27 | -0.97 to -0.19 | 13.4% |
| london_sweep_mss_fvg | HistData 2023 (reference) | all | 41 | -0.588 | -0.96 to -0.22 | -1.00 to -0.16 | 13.1% |
| london_sweep_mss_fvg | HistData 2023 (reference) | valid | 30 | -0.569 | -1.01 to -0.13 | -1.07 to -0.03 | 10.1% |

