# Episode 02 · Rent vs Buy, Simulated 20,000 Times

**You own this:** if you pay rent or a mortgage, you already picked a side of this bet, and about $1,200 a month is riding on it.

Two households earn the same pay and start with the same $96,000. Dana buys the typical US house. Sam rents the typical US rental and invests the down payment, the closing costs and every dollar she saves each month in a broad index fund. Whoever has the cheaper year invests the difference, so both spend the same. After ten years Dana sells, and we compare what each one walks away with, in today's dollars. The next ten years are replayed 20,000 times from real US history.

## Run it

```
pip install -r requirements.txt && python sim.py
```

`python sim.py v` also prints every stress test from the video. The random seed is fixed (`SEED = 20261121`), so you get the same numbers as the video. A full run takes a few seconds.

## Hero numbers (run 21 Nov 2026)

| # | Result | Value |
|---|---|---|
| 1 | Renter finishes richer | **68 in 100** futures |
| 2 | Renter's head start in the middle run | **about $92,000** (year-one cost gap: $1,167 a month) |
| 3 | Same test at a 3% mortgage | **buyer** finishes richer in **67 in 100** |
| 4 | Twist: the renter spends the monthly savings instead of investing them | renter ahead in only **34 in 100** (invests half: 53) |
| 5 | Stress tests | rent for a house-sized rental ($2,450) → **52** · stocks 4 points a year weaker → **52** · different reshuffles → 64 to 71 |

`results.txt` holds the full output of `python sim.py v`.

## How it works

Each run builds a ten-year future out of real US years from 1976 to 2022, taken in five-year blocks so that a bad year for houses stays next to the stock market and inflation of that same year. Stock returns include dividends, home prices follow the national Case-Shiller index, and rent grows with inflation plus half a point.

## Inputs

| Input | Value | Status |
|---|---|---|
| Home price | $416,700 | SOURCED: NAR median existing-home price, Oct 2026 |
| Rent | $1,965 a month | SOURCED: Zillow Observed Rent Index, typical US asking rent, mid-2026 |
| Mortgage rate | 7.28%, 30-year fixed | SOURCED: Freddie Mac, 19 Nov 2026 |
| Down payment / closing / selling | 20% / 3% / 6% | ASSUMED: common US figures |
| Property tax / insurance / upkeep | 1% / 0.5% / 1% of home value a year | ASSUMED |
| Rent growth | inflation + 0.5 point a year | ASSUMED |
| Index fund fee / tax on gains at the end | 0.05% / 15% | ASSUMED |
| Stock prices, dividends, inflation | Shiller monthly S&P 500 data | SOURCED: `data/shiller_sp500_monthly.csv` |
| Home prices | S&P CoreLogic Case-Shiller US National index | SOURCED: `data/caseshiller_national_monthly.csv` |

Both data files are copies of the public monthly datasets at github.com/datasets (`s-and-p-500`, `house-prices-us`), taken 21 Nov 2026.

## What it can't see

National medians only, and nobody lives in the national median. The base case compares the typical rental with the typical house for sale, which is bigger; the house-sized-rent test (52 in 100) is the like-for-like read. The history window holds one national housing bust and a very strong stock run. No mortgage-interest deduction, no yearly dividend tax. It also can't price the things that are yours to value, like painting the walls any color you want.

---

MODEL · NOT A FORECAST · NOT FINANCIAL ADVICE
