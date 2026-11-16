# Bid/ask re-test of the 7 NAS100 strategies on 2023 (pre-registered 2026-11-16)

Written and committed BEFORE the data was downloaded or any result computed.
This is a **measurement re-test**, not new strategy research. The research pause stays in force.

## Questions
1. Does the bid-only fill model used so far (fill and exit on BID touches, spread subtracted afterwards)
   flatter the results? (audit finding 3 in `docs/audit_report.md`)
2. Does a second, more complete 2023 data source change the 2023 picture? (audit finding 1: HistData 2023
   fails the session rule on 119 of 256 weekdays)

## Data
- Dukascopy `USATECHIDXUSD` 1-minute **BID and ASK** candles, 2022-12-01 to 2023-12-31.
  December 2022 is indicator warm-up only; **only trades with a New York date in 2023 are counted**.
- Only minutes that have BOTH a bid and an ask candle are used. Nothing is filled in.
- The session rule from `docs/data_quality_rule.md` (765/775 bars, no hole > 5 min) is applied to the joined data.
- Volume is set to 0 for the strategies, so "VWAP" is computed exactly as in the original HistData backtest
  (plain average). Rules, parameters, risk settings and news blackout are unchanged. 2025+ is not touched.
- Already known before writing this (disclosed): one probe day (2023-03-01) showed a Dukascopy quoted spread of
  median 3.4 points (p10 1.4, p90 3.5), wider than the 1.5-point assumption. Results on HistData 2023 are known
  from the earlier backtests.

## Variants (all with slippage 0.5 pts on market/stop entries and stop/forced exits, as before)
| id | prices for fills and exits | spread charged |
|---|---|---|
| V1 bid-only | Dukascopy BID only, as the original backtest | 1.5 pts subtracted per trade |
| V2 synthetic ask | buys use BID + 1.5 (a model of the assumed spread, not data), sells use BID | 0 (already in prices) |
| V3 real bid/ask | buys use Dukascopy ASK, sells use Dukascopy BID | 0 (already in prices) |

Buy = long entry or short exit; sell = short entry or long exit. Signals always come from BID 5-minute bars
(as before). A long limit fills when the ASK reaches the limit; a short position's stop and target trigger on the ASK.
- V2 − V1 = effect of the fill-trigger model alone (same assumed spread).
- V3 − V2 = effect of Dukascopy's real quoted spread instead of the 1.5 assumption (Dukascopy's spread is not Exness's).
- V1 vs HistData 2023 (all sessions and valid-only, from `docs/audit_measurements.md`) = data-source effect.

## Reported for each strategy and variant (all sessions and valid sessions)
Trades, average R, 95% range (iid), 95% week-clustered range, max drawdown at 0.5% risk.

## Decision rules (fixed now)
- The bid-only model is called **optimistic** for a strategy if V2's average R is below V1's by more than 0.02R
  (valid sessions). It is called **not material** if the difference is within ±0.02R.
- Whatever the result, **no strategy can qualify from this test**: one year, validation data already seen.
  `scanner.QUALIFIED` stays empty. A strategy whose V3 average is above 0 with a 95% range above 0 would only be
  noted as "worth a full pre-registered re-test after the research pause"; nothing else changes.
- If every strategy's V3 average R is ≤ 0, the "no edge after costs" conclusion is recorded as reinforced.
- If the download is incomplete (rate limits), the test runs on the days available and reports the count; it
  does not wait for or invent missing days.
