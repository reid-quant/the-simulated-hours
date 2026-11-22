# 01 · The next three years, replayed 20,000 times

Code for the simulation in Episode 01 of The Simulated Hours (working title: *I Simulated the Next Stock Market Crash 20,000 Times*).

In October 2026 US shares were more expensive, against ten years of company profits, than at any time since the dot-com peak. By Friday 20 November the S&P 500 had fallen 12% from its record. This model asks two things, starting from that real close:

1. In how many of 20,000 three-year runs does the market fall to half its October record, the way it did after 2000?
2. In how many is it back above that record three years from now?

**This is a simulation about odds. It is not a forecast and it is not financial advice.** It was run on 21 November 2026.

## What is here

| File | What it is |
|---|---|
| `dotcom_crash_stress_test.py` | The model, the dial, the two back-tests and the stress tests. |
| `shiller_monthly.csv` | Robert Shiller's monthly S&P Composite price and CAPE, January 1871 to November 2026 ([shillerdata.com](https://shillerdata.com/), read 21 November 2026). The model uses January 1881 to October 2026. |
| `results.txt` | The script's full output, as used for the numbers in the video. |

## Run it

You need Python 3 and NumPy.

```
pip install numpy
python3 dotcom_crash_stress_test.py shiller_monthly.csv v
```

Leave off the `v` for the seven headline results only. Add `json` to also write the path data used to draw the charts. The random seed is fixed, so you get the same numbers each time.

## How it works

Think of a deck of 1,714 cards. Each card is one real three-year stretch of monthly share prices since 1881.

1. **One run** draws a card and replays its 36 monthly moves, starting from Friday's close (88% of the October record).
2. **The drag.** History says expensive starts are followed by weaker years. A straight-line fit of three-year price change against how expensive shares were at the start gives a pull of about 12% over three years at today's level. Every replay is pulled down by a steady monthly share of it.
3. **The one dial** multiplies that drag. Zero means valuation does not matter. One is the full drag history shows, the top of the dial. The base case is one half.
4. **Then it counts** how often a run touches the red line (51% of the record, what was left after 2000 to 2002) and how often it ends above the gold line (the record).

## What it says

| | Runs in 100 |
|---|---|
| Dot-com sized crash within three years | 6 |
| Bear market (20% below the record) | 54 |
| Back above the record after three years | 50 |
| Dial at zero: crash / back above the record | 4 / 57 |
| Dial at the top: crash / back above the record | 7 / 38 |
| Wall Street's average target for December 2027 (8,638) reached | 13 |

Turning the dial barely moves the crash number and moves the recovery number a lot. Expensive shares did not make the crash likely in this model. They made the comeback slow.

## How much to trust it

**Checked against the real record, it is too calm.**

- Wound back to March 2000 with only the history that existed then, it gave the fall that followed 6 in 100.
- Wound back to September 1929, it gave that crash 0 in 100, because nothing that bad was in its history yet.

It can only replay the past. A crash unlike the past is not in the deck.

**Broken on purpose:**

- Every assumption moved up or down by half, 300 sets: crash odds ran from 2 to 11 in 100.
- Without the stretches that overlap 1929, the dot-com crash and 2008: 1 in 100. Five of every six crashing stretches are one of those three. The rest are 1937 and 1973 to 1974.
- Only stretches that began after a quick drop (8% or more in two months): 13 in 100.
- To make the crash a coin flip, the drag would have to be 5.6 times what history shows.

**One number is tuned, and it matters.** The base case uses half of the fitted drag (`DIAL = 0.5`). The reason given is that the fit rests on a handful of very expensive periods. The honest history is that the script was written before the model, and one half is the setting that lands on the script's headline numbers. With the full drag, the crash odds are 7 in 100 and the recovery odds 38. Trust the shape, not the exact figures.

**What it leaves out:**

- Dividends, and inflation.
- The worst single days: prices are monthly averages.
- Company profits, interest rates, and whether AI spending pays back.
- Anything specific to technology shares, which fall harder than the whole market.
- Independence: 20,000 runs resample 1,714 overlapping stretches, and only about 48 of those are fully separate three-year periods.
- Only 42 of the 1,714 starting months were at least as expensive as now (1998 to 2001, and 2021 to 2022).

## Inputs

| Input | Value | Where it comes from |
|---|---|---|
| Record close, 6 October 2026 | 7,818.93 | S&P 500 |
| Start, 20 November 2026 | 6,910.39 | S&P 500 |
| Red line | 51% of the record | S&P 500 fall, March 2000 to October 2002 |
| CAPE at the start | 35.9 | October's 40.1 moved to Friday's close |
| Base-case dial | 0.5 | Assumed and tuned (see above) |
| Size of monthly swings | as recorded | Assumed |
| Timing of the drag | spread evenly | Assumed |
| Wall Street target, December 2027 | 8,638 | Average of eight strategists, November 2026 |

Change any of them at the top of the script and see what you get.
