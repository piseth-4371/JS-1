# Exness USTEC swap check — plan written before looking

Written 2026-11-20, before any Exness swap figure was read. Owner request: "yes check the exness swap".

## Question
What overnight fee (swap) does Exness publish for a LONG `USTEC` position, and how does it compare with the 7% a
year the turn-of-month tests assume (`app/backtest/turn_of_month.py`, `app/core/tom_forward.py`, `FINANCING = 0.07`
per calendar night)?

## Sources (public pages only)
- Only Exness's own public website and help centre. No login, no account, no form, no third-party site.
- Record each page's address, the date read, the account type and the exact swap figure and its unit as shown
  (points, % a year, USD per lot, or "swap-free"). Also record when the swap is charged and if a triple swap day
  applies.
- If Exness does not publish a number for `USTEC` on public pages, the result is "not published" — never estimated.

## How it is compared (fixed now)
- Convert the published long swap into **% of position value a year**, using the price level and contract size the
  same page gives. If the page gives no way to convert, report the raw figure and say "not comparable".
- Cost of one turn-of-month trade = swap per night × the real number of nights charged (weekend nights counted as
  Exness charges them, e.g. a triple swap on one weekday).
- **Verdict words (fixed):**
  - "assumption OK": the published long cost is at most 7% a year (or the account is swap-free on USTEC).
  - "assumption too low": above 7% a year. Then also show what the forward test's recorded trades would have
    netted at the real rate, as information.

## What this check will NOT do
- It does not change `FINANCING`, any rule, or any recorded result. The turn-of-month forward test was
  pre-registered with 7% (`docs/turn_of_month_forward_preregistration.md`), so its rules stay as written; a gap is
  reported next to it, and is a reason for a stress line, not for a re-run with new numbers.
- No trading, no account action, no personal data entered anywhere.
