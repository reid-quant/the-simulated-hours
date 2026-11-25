# The Simulated Hours

The code behind each simulation video on the channel. Every video gets its own folder under `episodes/` with the model, its data, its results and a README on how to run it and how much to trust it.

| # | Folder | Video | What it simulates |
|---|---|---|---|
| 01 | [`episodes/ep01-dotcom-crash/`](episodes/ep01-dotcom-crash/) | *Why This Stock Crash Won't Look Like 2000* | The next three years for US shares, run 20,000 times from the 20 November 2026 close, with one dial for how much expensive prices drag on what follows. Odds, not a forecast and not financial advice. |
| 02 | [`episodes/ep02-rent-vs-buy/`](episodes/ep02-rent-vs-buy/) | *Why Renting Beats Buying (I Simulated It 20,000 Times)* | Renting and investing the difference versus buying the typical US house, over ten years, replayed 20,000 times from real US years 1976–2022. Odds, not a forecast and not financial advice. |
| 03 | [`episodes/ep03-nvidia-hardware-kings/`](episodes/ep03-nvidia-hardware-kings/) | *Nvidia Lost Half Its Value. I Replayed 100 Years of Crashes.* | How long Nvidia takes to get back to its October 2026 record, from 14 real cases since 1929 of a hardware leader falling 40% or more, replayed 20,000 times. Odds, not a forecast and not financial advice. |

## Run it

You need Python 3. Each episode folder runs the same way:

```
cd episodes/ep01-dotcom-crash
pip install -r requirements.txt && python sim.py
```

Add `v` (`python sim.py v`) to print every stress test from the video.

Random seeds are fixed, so you get the same numbers as the video.

These are simple models with labelled guesses. They show how a situation behaves; they are not forecasts and they are not financial advice. Change the guesses at the top of each script and see what you get.
