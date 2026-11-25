# Episode 03 · Can Nvidia Beat History? (100 Years of Hardware Monopolies)

**You own this:** if you hold an S&P 500 index fund, about $8 of every $100 in it was Nvidia at the October 2026 record, and roughly half of that is gone.

Nvidia closed at a record $239.24 on 5 October 2026 and at $125.53 on 20 November 2026, about 48% lower. The model asks one question: when a company that rules a piece of hardware falls 40% or more from its record share price, how long until the price is back at the record? It takes every such case I could source since 1929 (14 of them, from RCA's radio crash to Nvidia's own 2022 drop) and replays them 20,000 times.

The twist: almost nothing comes back slowly. The real cases either got back in under two years (the reign survived) or took a decade or more, or never came back (the reign was over). The middle is almost empty.

## Run it

```
pip install -r requirements.txt && python sim.py
```

The random seed is fixed (`SEED = 21112026`), so you get the same numbers as the video. A full run takes a few seconds and prints the hero numbers, the dial, the stress tests and the checks against the real record.

## Hero numbers (run 21 Nov 2026, 20,000 runs)

| # | Result | Value |
|---|---|---|
| 1 | Back at the October record within 3 years | **31 in 100** |
| 2 | Back within 10 years | **40 in 100** |
| 3 | Still not back after 20 years | **47 in 100** |
| 4 | Typical wait | fast kind **1.6 years**, slow kind **21 years**; runs landing between 3 and 8 years: **4.5 in 100** |
| 5 | Sam's $100,000 index fund | Nvidia slice **$8,190** at the record → **$4,297** now |
| 6 | The dial (chance the reign survives) | set to 10% → back in 3 years in **10** of 100; set to 90% → **89** of 100 |
| 7 | Break it on purpose | count the 2000 bubble once → **38** · delete Nvidia's own comebacks → **21** · cases since 2007 only → **61** · every guess nudged by up to half → **19 to 39** |

`results.txt` holds the full output of `python sim.py`.

## How it works

Each run first decides whether this drop is the fast kind (back in about two years) or the slow kind (a decade or more, or never). The chance of fast comes from history's own count, 4 fast out of 14, with its uncertainty included. Then the run replays one real case of that kind, with its wait and fall wobbled a little. The exact numbers bend when you change the guesses. The shape (fast or never, with almost nothing in between) does not.

## Inputs

| Input | Value | Status |
|---|---|---|
| Nvidia record close | $239.24 on 5 Oct 2026 | SOURCED: news reports |
| Nvidia close | $125.53 on 20 Nov 2026 | SOURCED: news reports |
| Nvidia weight in the S&P 500 | 8.19% | SOURCED: SPY holdings, 24 Sep 2026 |
| Weight at the 5 Oct record | same as 24 Sep | ASSUMED (A1) |
| Fallen hardware leaders (14 cases) | name, peak year, fall, years to get back | SOURCED for most figures; see the notes in `sim.py` (S = sourced, M = from memory, still to verify) |
| Fast vs slow cut-off | 3 years | ASSUMED: no real case sits between 1.9 and 8.6 years |
| Wobble on each replayed wait | about a quarter | ASSUMED (A2) |
| Wobble on each replayed fall | 3 points | ASSUMED (A3) |
| Uncertainty in the base rate | Beta(fast + 1, slow + 1) | ASSUMED (A4) |

Still to verify (from memory in the model, not yet re-sourced): Xerox back at its 1972 high about 1996; Polaroid never back before its 2001 bankruptcy; Apple back at its 2012 high in August 2014; Intel's 2000–02 fall of about 82%.

Main sources: RCA 1929–1966 (Global Financial Data); Cisco back at its March 2000 high in December 2025 (Bloomberg); Apple and Nvidia drawdowns and recoveries (Fortune, Trefis, Motley Fool).

## What it can't see

Anything inside Nvidia itself: its profits, the new CEO, regulators looking at the books, or customers designing their own chips. It counts share prices only, with no dividends and no inflation. Fourteen cases is a tiny pile, and I chose the list myself. And the same count would have bet against Nvidia in December 2018 (2 fast of 12) and again in October 2022 (3 fast of 13), and it lost both times: Nvidia was back at its record in about a year and a half each time.

---

MODEL · NOT A FORECAST · NOT FINANCIAL ADVICE
