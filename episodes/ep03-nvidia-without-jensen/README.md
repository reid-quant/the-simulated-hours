# Episode 03 · Jensen Huang Is Gone. I Ran Nvidia's Next 2 Years 20,000 Times.

**You own this:** if you have money in an S&P 500 index fund, Nvidia was about one dollar in every thirteen of it the day before the story broke. This asks whether the stock gets back.

Code for the simulation in Episode 03 of The Simulated Hours: Nvidia's next two years, replayed 20,000 times.

On 12 November 2026 Jensen Huang resigned as Nvidia's president, CEO and director. Between the 28 October close (the last before the first New York Times report) and the 18 November close, the share price fell 30%, from $215.38 to $150.96. This model asks one question, starting from that real close:

> In how many of 20,000 two-year runs is Nvidia's share price back above $215.38?

**This is a simulation about odds. It is not a forecast and it is not financial advice.** It was run on 18 November 2026, after the market close.

## What is here

| File | What it is |
|---|---|
| `sim.py` | The model, the dial, the real-record checks and the stress tests. |
| `requirements.txt` | NumPy, and pandas (only used to read the csv). |
| `data/sp500_monthly.csv` | Monthly S&P 500 history from Shiller's data ([datasets/s-and-p-500](https://github.com/datasets/s-and-p-500)), January 1871 to September 2026. The model uses January 1950 onward. |
| `results.txt` | The full output of `python sim.py`, as used for the numbers in the video. |

## Run it

```
pip install -r requirements.txt && python sim.py
```

The random seed is fixed (`SEED = 20261118`), so you get the same numbers as `results.txt`. Running it also writes `sample_paths.json`, the runs used to draw the charts in the video.

## How it works

Think of it as a dice game played 20,000 times, each game lasting 24 months.

1. **The market dice.** Each game picks a real, unbroken two-year stretch of the S&P 500 since 1950 and replays it month by month.
2. **How hard Nvidia swings with it.** Nvidia moves 1.3 to 2.2 times as hard as the market (its published figure is 2.25; very large companies usually calm down).
3. **Nvidia's own luck.** On top of the market, a fair coin of good and bad news worth 25% to 40% a year either way.
4. **The one dial: life after the founder.** A steady yearly push, from losing the whole "founder edge" one study measured (minus 8.3% a year) to a scandal dip healing over three years (plus 3.1% a year).
5. **One possible blow.** A 10% to 30% chance of a serious legal or export-rule hit inside two years, taking 5% to 20% off.
6. **Then it counts** how often a game ends back above $215.38.

## What it says

| | Games in 100 |
|---|---|
| Back above $215.38 at two years | 33 |
| Touches $215.38 at some point on the way | 51 |
| Ends two years lower than $150.96 | 44 |
| Ends below half of $150.96 | 10 |
| Back above the record value ($5.78 trillion) | 26 |
| Dial at nothing / a little / a lot | 36 / 30 / 25 |
| Worst / middle / best third of stock markets | 11 / 30 / 57 |

Middle game at two years: about $166 a share ($4.0 trillion); nine games in ten land between $60 and $427.

**The twist:** the market you happen to get matters about four times as much as the founder dial (a 46-point gap against 11).

## How much to trust it

**Checked against the real record:**

- Analysts' new 12-month targets run $185 to $300, average about $256. The model gives that average 12 in 100. It is blind to profits: if the profit forecasts come true, $215.38 is only about 15.5 times next year's forecast profit. So the model may be too gloomy.
- Nvidia's three falls of more than 35% in the last decade were followed by an average gain of 305% in two years. The model gives that 1.1 in 100. It would have been far too gloomy about all three (none of them involved losing the founder).
- Studies of sudden founder exits find moves of a few percent. Nvidia fell 30%. This case is far outside what the studies cover.

**Broken on purpose:**

- Every guess nudged at random by up to half, 500 re-runs: 19 to 46 in 100. Never a coin flip.
- Flat stock market for two years: 12 in 100.
- Even if life after the founder *added* the whole founder edge (+8.3% a year): 47 in 100. It takes about +11% a year to make it a coin flip.

**Tuned:** nothing.

**What it leaves out:**

- It is a dice game about a share price, not a model of the chip business: no products, customers, rivals or profits.
- Today's price already holds the market's own guess about life without Huang. The dial only asks whether that guess is too kind or too harsh.
- The market dice are 76 years of US history; the next two years need not look like any of them, and monthly prices hide the wildest days.
- Huang coming back (the board says no), who the permanent CEO is, buy-backs, dividends, and the outcome of the inquiries beyond one rolled blow.
- The spying claim is an allegation. The model treats it as reported, not as fact.

Trust the shape (getting back is less likely than not, and the market matters more than the man), not the exact figure.

## Inputs

| Input | Value | Status |
|---|---|---|
| Start price, 18 Nov 2026 close | $150.96 | SOURCED |
| Old price, 28 Oct 2026 close | $215.38 | SOURCED |
| Record market value, 6 Oct 2026 | $5.78 trillion | SOURCED |
| Shares outstanding | 24.15 billion | SOURCED (stockanalysis.com / Morningstar, 17 Nov 2026) |
| Profit per share, last year / forward P/E | $9.31 / 10.87 | SOURCED (stockanalysis.com, 17 Nov 2026) |
| Published five-year beta | 2.25 | SOURCED (stockanalysis.com) |
| Analysts' 12-month targets | $185 to $300, average $255.76 | SOURCED |
| Founder edge | 8.3% a year (4.4% after controls) | SOURCED (Fahlenbrach 2009, *JFQA*) |
| Scandal dip | 9.5%, gone after three years | SOURCED (Jory and co-authors 2015, *Applied Economics*) |
| Nvidia's S&P 500 weight, 12 Nov 2026 | 6.14% | SOURCED (State Street SPY holdings) |
| S&P 500 monthly history | Jan 1950 to Sep 2026 | SOURCED (Shiller data) |
| How hard Nvidia swings with the market | 1.3 to 2.2 times | ASSUMED (A1) |
| Nvidia's own yearly luck | 25% to 40% either way | ASSUMED (A2) |
| Life after the founder (the dial) | −8.3% to +3.1% a year | ASSUMED (A3, the biggest guess) |
| Legal or export blow | 10–30% chance, 5–20% off | ASSUMED (A4) |

Change any of them at the top of `sim.py` and see what you get.

---

MODEL · NOT A FORECAST · NOT FINANCIAL ADVICE
