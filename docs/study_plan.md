# Study plan — quant basics with your own data

Strategy research is paused (decision 2026-11-16 in `decisions.md`). This plan uses the free book
*Quantitative Finance From Scratch* (QuantFinanceToGo, 17 one-page chapters) together with the real
NAS100 data and backtest trades already in this project. Goal: understand the maths behind the results,
and practise Python. **Not** to find a new signal.

## How each lesson works (about 1 hour, one per day)
1. Read the chapter in the book (one page). Do its questions with pen and paper; answers are on pages 23–25.
2. Open the exercise file in `backend/learning/`, fill in the functions marked `TODO`.
3. Check yourself (from the `backend` folder):
   `.\.venv\Scripts\python -m pytest learning\check_chNN.py -q`
4. Run the file to see the answer on real NAS100 data:
   `.\.venv\Scripts\python learning\chNN_*.py`
5. Ask Claude to review your code (the `teach-step` skill: hints first, the model solution only after your try).

## The plan
| Day | Book chapter | Exercise on your data | Question it answers |
|---|---|---|---|
| 1 | 1 Returns | `ch01_returns.py` (ready) | Biggest NAS100 daily fall 2019–2024? Why do log returns add up? |
| 2 | 2 Present value | `ch02_present_value.py` (ready): $1,000 at 4% savings vs each strategy | Is the strategy better than a savings account? |
| 3 | 3 Expected value | Avg R of each strategy from `backtest_trades.csv` | Which bets are "roulette"? |
| 4 | 4 Random walk | Simulate coin-flip prices; run `orb` on them | Can a strategy "work" on pure noise? |
| 5 | 5 Square root rule | NAS100 daily vs weekly vs monthly volatility | Does √time hold for NAS100? |
| 6 | 6 Bell curve | Histogram of NAS100 daily returns vs the bell | How often do −3% days really happen? |
| 7 | 7 Volatility | 20-day realized volatility, 2019–2024 (reuse `vol_filter.daily_closes`) | When was NAS100 calm or wild? |
| 8 | 8 Sharpe ratio | Sharpe of buy-and-hold NAS100 vs each strategy | Paid for the risk? |
| 9 | 9 Volatility drag | Same average, different swings: simulate | Why does a −50% need +100%? |
| 10 | 10 Correlation | NAS100 vs gold vs BTC daily returns | Do they fall together? |
| 11 | 11 Diversification | Volatility of a NAS100 + gold mix | Does mixing calm the swings? |
| 12 | 12 Efficient frontier | Random mixes of NAS100 / gold / BTC | Best return for each risk level |
| 13 | 13 Beta / CAPM | Beta of gold and BTC to NAS100 | How strongly do they follow NAS100? |
| 14 | 14 Kelly | Recompute Kelly from `report_card.py` by hand | Why is the answer 0%? |
| 15 | 15 Monte Carlo | Your own 10,000-path simulation of the $1,000 paper account | Worst year you should expect |
| 16 | 16 Fat tails | Kurtosis of NAS100 daily returns | How fat are the tails? |
| 17 | 17 Value at risk | 1-day 99% VaR of holding NAS100 | How much could one bad day cost? |

Exercises after day 1 are written one at a time, when you finish the previous one. Ask: "next exercise".

## Rules
- Paper only. Nothing in this plan places a trade or changes a strategy.
- Copy no code you do not understand. If a line is unclear, ask what it does.
- Keep your answers in your own files; they are your learning journal.
