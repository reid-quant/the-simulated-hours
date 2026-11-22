# The Simulated Hours

The code behind each simulation video on the channel. Every video gets its own numbered folder with the model, its data, its results and a README on how to run it and how much to trust it.

| # | Folder | Video | What it simulates |
|---|---|---|---|
| 01 | [`01-dotcom-crash/`](01-dotcom-crash/) | *I Simulated the Next Stock Market Crash 20,000 Times* (working title) | The next three years for US shares, run 20,000 times from the 20 November 2026 close, with one dial for how much expensive prices drag on what follows. Odds, not a forecast and not financial advice. |

## Run it

You need Python 3 and NumPy.

```
pip install numpy
cd 01-dotcom-crash
python3 dotcom_crash_stress_test.py shiller_monthly.csv v
```

Random seeds are fixed, so you get the same numbers as the video.

These are simple models with labelled guesses. They show how a situation behaves; they are not forecasts and they are not financial advice. Change the guesses at the top of each script and see what you get.
