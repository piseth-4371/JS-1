# News effect on NAS100, gold and BTC — results

Made by `scripts/news_effect.py` on 2026-11-19. Rules were committed first: `docs/news_effect_preregistration.md`. Measurement only: nothing about trading changed.

**30-min range** = high − low in the 30 minutes after the release, as % of price (median over events). **Normal** = the same at the same New York time on nearby weekdays without news. **× normal** = how many times bigger news makes it. **Move** = how far price ended up after 30 minutes (either direction).

| news | market | events | 30-min range on news | normal | × normal | move after 30 min | events > 2× their normal |
|---|---|---:|---:|---:|---:|---:|---:|
| CPI | NAS100 | 69 (skipped 3) | 0.65% | 0.20% | **3.3×** | 0.33% | 70% |
| NFP | NAS100 | 69 (skipped 3) | 0.69% | 0.20% | **3.5×** | 0.34% | 87% |
| FOMC | NAS100 | 44 (skipped 5) | 0.77% | 0.26% | **2.9×** | 0.29% | 70% |
| GDP | NAS100 | 68 (skipped 3) | 0.33% | 0.21% | **1.6×** | 0.14% | 28% |
| PCE | NAS100 | 67 (skipped 4) | 0.39% | 0.22% | **1.8×** | 0.14% | 34% |
| CPI | Gold | 68 (skipped 4) | 0.75% | 0.26% | **2.8×** | 0.34% | 65% |
| NFP | Gold | 67 (skipped 5) | 0.79% | 0.27% | **2.9×** | 0.31% | 82% |
| FOMC | Gold | 44 (skipped 5) | 0.71% | 0.12% | **6.1×** | 0.20% | 93% |
| GDP | Gold | 69 (skipped 2) | 0.42% | 0.28% | **1.5×** | 0.17% | 29% |
| PCE | Gold | 67 (skipped 4) | 0.38% | 0.28% | **1.4×** | 0.13% | 13% |
| CPI | BTC | 72 (skipped 0) | 1.11% | 0.54% | **2.0×** | 0.50% | 51% |
| NFP | BTC | 72 (skipped 0) | 1.07% | 0.56% | **1.9×** | 0.49% | 36% |
| FOMC | BTC | 49 (skipped 0) | 1.27% | 0.53% | **2.4×** | 0.49% | 61% |
| GDP | BTC | 71 (skipped 0) | 0.65% | 0.55% | **1.2×** | 0.21% | 17% |
| PCE | BTC | 71 (skipped 0) | 0.73% | 0.58% | **1.2×** | 0.28% | 22% |

## Limits
- HistData NAS100/gold prices are not Exness prices; BTC trades 24/7.
- 2019-2024 only. A typical size says nothing about the direction, and single releases can be far bigger.
- Not a trading rule: the ±30-minute news blackout stays exactly as it was.
