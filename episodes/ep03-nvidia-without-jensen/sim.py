"""
Nvidia without Jensen: is the company worth more in two years than the day
before the story broke?

Written 18 Nov 2026, after the close on the day following Nvidia's first results without its founder.
Not a forecast and not investment advice. It is a small dice game:
start from the real share price, roll the stock market from its own real history,
add Nvidia's own luck, add a guess for "life after the founder", and play the
next 24 months 20,000 times.

The one dial: how much losing the founder costs (or gives back) each year.

Run:  python sim.py            (reads data/sp500_monthly.csv)
Plain Python + numpy + pandas (pandas only reads the csv). Seed fixed so results repeat.
"""
import sys, json
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- PARAMETERS
SEED, N, MONTHS = 20261118, 20_000, 24
# SOURCED
PRICE_NOW = 150.96        # NVDA close, 18 Nov 2026 (the day after the first results without Huang)
PRICE_BEFORE = 215.38     # NVDA close, 28 Oct 2026: the last close before the first New York Times report
PRICE_RECORD_CAP = 5.78e12  # market value at the record close, 6 Oct 2026
SHARES = 24.15e9          # shares outstanding (stockanalysis.com / Morningstar, 17 Nov 2026)
EPS_TTM, PE_FWD = 9.31, 10.87   # trailing earnings per share and forward P/E (stockanalysis.com, 17 Nov 2026)
BETA_5Y = 2.25            # published five-year beta (stockanalysis.com, 17 Nov 2026)
TARGET_LOW, TARGET_HIGH, TARGET_AVG = 185, 300, 255.76   # analysts' reissued 12-month targets; average target
FOUNDER_EDGE_HI, FOUNDER_EDGE_LO = 0.083, 0.044   # Fahlenbrach 2009: founder-CEO firms beat benchmarks by 8.3% a year (4.4% after controls), 1993-2002
SCANDAL_DIP = 0.095       # Jory et al. 2015: 80 CEO scandals, shares fell 6.5% to 9.5% in a month, gap gone after three years
SPX_WEIGHT_NOV12 = 0.0614 # Nvidia's share of the S&P 500 on 12 Nov 2026 (State Street SPY holdings, via calculatorai.app)
PRICE_NOV12 = 166.19      # NVDA close on 12 Nov 2026 (the day he resigned)
SP500_START = "1950-01-01"   # monthly S&P 500 history used for the market dice (datasets/s-and-p-500 on GitHub, Shiller data)
# ASSUMED (each is a guess; ranges are what the dice roll between)
A1_BETA = (1.3, 2.2)      # how hard Nvidia swings when the whole market swings (published: 2.25; giants usually calm down)
A2_OWN_VOL = (0.25, 0.40) # Nvidia's own yearly luck, good or bad, on top of the market
A3_DIAL = (-FOUNDER_EDGE_HI, (1 + SCANDAL_DIP) ** (1 / 3) - 1)   # THE DIAL, per year: from "loses the whole founder edge" to "scandal dip heals in three years"
A4_SHOCK_P = (0.10, 0.30) # chance of one serious legal or export-rule blow inside two years
A4_SHOCK_SIZE = (0.05, 0.20)   # how much that blow knocks off the price


def load_market(path):
    d = pd.read_csv(path, parse_dates=["Date"])
    d = d[(d.Date >= SP500_START) & (d.SP500 > 0)]
    return np.diff(np.log(d.SP500.values)), d


def play(n, rng, mkt, dial=None, wide=1.0, beta=None, flat_market=False, median_neutral=False, shock=True, start_price=None):
    """Play n two-year games. Returns month-end price paths, shape (n, MONTHS+1)."""
    def U(r):
        mid, half = (r[0] + r[1]) / 2, (r[1] - r[0]) / 2 * wide
        return rng.uniform(mid - half, mid + half, n)
    # 1. the market: a real, unbroken 24-month stretch of S&P 500 history, picked at random
    start = rng.integers(0, len(mkt) - MONTHS + 1, n)
    m = mkt[start[:, None] + np.arange(MONTHS)[None, :]]
    if flat_market:
        m = np.zeros_like(m)
    b = np.clip(U(A1_BETA), 0.5, 3.5) if beta is None else np.full(n, beta)
    # 2. Nvidia's own luck (fair dice: on average it neither helps nor hurts)
    vol = np.clip(U(A2_OWN_VOL), 0.05, 0.9)
    drift = 0.0 if median_neutral else -(vol ** 2) / 24
    own = rng.normal(0, 1, (n, MONTHS)) * (vol / np.sqrt(12))[:, None] + np.reshape(drift, (-1, 1))
    # 3. the dial: life after the founder, per year
    d = np.clip(U(A3_DIAL), -0.5, 0.5) if dial is None else np.full(n, dial)
    lead = np.log1p(d)[:, None] / 12
    logp = np.cumsum(b[:, None] * m + own + lead, axis=1)
    # 4. one possible legal or export-rule blow
    if shock:
        hit = rng.uniform(0, 1, n) < np.clip(U(A4_SHOCK_P), 0, 1)
        when = rng.integers(0, MONTHS, n)
        size = np.log1p(-np.clip(U(A4_SHOCK_SIZE), 0, 0.6))
        logp += (np.arange(MONTHS)[None, :] >= when[:, None]) * (hit * size)[:, None]
    return (start_price or PRICE_NOW) * np.exp(np.hstack([np.zeros((n, 1)), logp]))


def summary(paths):
    end = paths[:, -1]
    return dict(back=np.mean(end >= PRICE_BEFORE), touch=np.mean(paths[:, 1:].max(1) >= PRICE_BEFORE),
                below_now=np.mean(end < PRICE_NOW), half=np.mean(end < PRICE_NOW / 2),
                med=np.median(end), p5=np.percentile(end, 5), p95=np.percentile(end, 95))


def show(tag, s):
    print(f"  {tag:<44} back above ${PRICE_BEFORE:.0f} at two years: {100*s['back']:.0f}%   touches it on the way: {100*s['touch']:.0f}%   "
          f"ends below today: {100*s['below_now']:.0f}%   ends below half of today: {100*s['half']:.0f}%   "
          f"median ${s['med']:.0f} (${s['p5']:.0f} to ${s['p95']:.0f})")


def main():
    global A1_BETA, A2_OWN_VOL, A3_DIAL, A4_SHOCK_P, A4_SHOCK_SIZE
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sp500_monthly.csv"
    mkt, d = load_market(path)
    rng = np.random.default_rng(SEED)
    T = lambda p: p * SHARES / 1e12

    print("WHERE THINGS STAND (sourced)")
    print(f"  record close 6 Oct 2026: market value ${PRICE_RECORD_CAP/1e12:.2f} trillion")
    print(f"  day before the story broke (28 Oct close): ${PRICE_BEFORE} a share = ${T(PRICE_BEFORE):.2f} trillion")
    print(f"  18 Nov close: ${PRICE_NOW} a share = ${T(PRICE_NOW):.2f} trillion")
    print(f"  fall since the story broke: {100*(1-PRICE_NOW/PRICE_BEFORE):.0f}% = ${T(PRICE_BEFORE)-T(PRICE_NOW):.2f} trillion; since the record: ${PRICE_RECORD_CAP/1e12-T(PRICE_NOW):.2f} trillion")
    print(f"  climb needed to get back: +{100*(PRICE_BEFORE/PRICE_NOW-1):.0f}%")

    print(f"\nTHE MARKET DICE: S&P 500 monthly history, {d.Date.iloc[0]:%b %Y} to {d.Date.iloc[-1]:%b %Y} ({len(mkt)} months)")
    r24 = np.exp(np.convolve(mkt, np.ones(MONTHS), 'valid')) - 1
    print(f"  every real two-year stretch ({len(r24)} of them): median {100*np.median(r24):+.0f}%, one in twenty worse than {100*np.percentile(r24,5):+.0f}%, one in twenty better than {100*np.percentile(r24,95):+.0f}%")
    print(f"  share of real two-year stretches where the market fell: {100*np.mean(r24<0):.0f}%")

    base = play(N, rng, mkt)
    s = summary(base)
    print(f"\nBASELINE: the next two years played {N:,} times")
    show("all dice rolling", s)
    print(f"  median market value at two years: ${T(s['med']):.1f} trillion (nine games in ten between ${T(s['p5']):.1f} and ${T(s['p95']):.1f} trillion)")
    one = base[:, 12]
    print(f"  at one year: median ${np.median(one):.0f} (${np.percentile(one,5):.0f} to ${np.percentile(one,95):.0f}); back above ${PRICE_BEFORE:.0f}: {100*np.mean(one>=PRICE_BEFORE):.0f}%")
    print(f"  ends above the record value (${PRICE_RECORD_CAP/SHARES:.0f} a share): {100*np.mean(base[:,-1]>=PRICE_RECORD_CAP/SHARES):.0f}%")
    first = np.argmax(base[:, 1:] >= PRICE_BEFORE, axis=1) + 1
    got = base[:, 1:].max(1) >= PRICE_BEFORE
    print(f"  in games that get back, the typical month it first happens: month {np.median(first[got]):.0f}")

    print("\nTHE DIAL: what losing the founder costs, or gives back, each year")
    stops = ((A3_DIAL[1], "scandal dip heals (+3.1% a year)"), (0.0, "nothing: the price already has it right"),
             (-FOUNDER_EDGE_LO, "a little: loses 4.4% a year"), (-FOUNDER_EDGE_HI, "a lot: loses 8.3% a year"),
             (-0.15, "disaster: loses 15% a year"))
    for v, tag in stops:
        show(tag, summary(play(N, rng, mkt, dial=v)))

    print("\nREAL-RECORD CHECKS")
    print(f"  analysts' new 12-month targets run ${TARGET_LOW} to ${TARGET_HIGH}; average target ${TARGET_AVG}")
    print(f"    model at 12 months: median ${np.median(one):.0f}; chance of reaching the lowest target ${TARGET_LOW}: {100*np.mean(one>=TARGET_LOW):.0f}%; the average ${TARGET_AVG:.0f}: {100*np.mean(one>=TARGET_AVG):.0f}%; the highest ${TARGET_HIGH}: {100*np.mean(one>=TARGET_HIGH):.0f}%")
    eps_fwd = PRICE_NOW / PE_FWD
    print(f"  price tag check: today's price is {PRICE_NOW/EPS_TTM:.1f} times last year's profit per share (${EPS_TTM}).")
    print(f"    the old price ${PRICE_BEFORE} would be {PRICE_BEFORE/EPS_TTM:.1f} times last year's profit, or {PRICE_BEFORE/eps_fwd:.1f} times next year's forecast profit (${eps_fwd:.2f})")
    print(f"  Nvidia's own past: three falls of more than 35% in the last decade were followed by an average +305% in two years (Motley Fool, Apr 2025).")
    print(f"    model's chance of +305% in two years: {100*np.mean(base[:,-1]>=PRICE_NOW*4.05):.1f}%. The model would have been far too gloomy about those three. None of them involved losing the founder.")
    print(f"  founder shock studies: sudden death of a founder CEO moves shares -3.25% over three days on average (Jenter and co-authors, 2017 working paper). Nvidia fell {100*(1-PRICE_NOW/PRICE_BEFORE):.0f}%: this is far outside the usual case.")

    print("\nSTRESS TEST 1: every guess range made half as wide again (20,000 games)")
    show("wider guesses", summary(play(N, rng, mkt, wide=1.5)))
    print("  500 small re-runs, each with every guess nudged at random by up to half:")
    res = []
    keep = (A1_BETA, A2_OWN_VOL, A3_DIAL, A4_SHOCK_P, A4_SHOCK_SIZE)
    r2 = np.random.default_rng(SEED + 1)
    for _ in range(500):
        f = lambda r: tuple(sorted(x * r2.uniform(0.5, 1.5) for x in r))
        A1_BETA, A2_OWN_VOL, A4_SHOCK_P, A4_SHOCK_SIZE = f(keep[0]), f(keep[1]), f(keep[3]), f(keep[4])
        A3_DIAL = (keep[2][0] * r2.uniform(0.5, 1.5), keep[2][1] * r2.uniform(0.5, 1.5))
        res.append(np.mean(play(2000, r2, mkt)[:, -1] >= PRICE_BEFORE))
    A1_BETA, A2_OWN_VOL, A3_DIAL, A4_SHOCK_P, A4_SHOCK_SIZE = keep
    res = np.array(res)
    print(f"    chance of being back at two years ranged from {100*res.min():.0f}% to {100*res.max():.0f}% (middle 90%: {100*np.percentile(res,5):.0f}% to {100*np.percentile(res,95):.0f}%); below a coin flip in {100*np.mean(res<0.5):.0f}% of re-runs")

    print("\nSTRESS TEST 2: break it on purpose")
    show("no market at all (flat for two years)", summary(play(N, rng, mkt, flat_market=True)))
    show("Nvidia moves only as much as the market", summary(play(N, rng, mkt, beta=1.0)))
    show("Nvidia swings 2.25x the market (published)", summary(play(N, rng, mkt, beta=BETA_5Y)))
    show("no legal or export blow possible", summary(play(N, rng, mkt, shock=False)))
    show("luck dice tilted kinder (median-fair)", summary(play(N, rng, mkt, median_neutral=True)))
    show("flip the dial: founder edge GAINED, +8.3%", summary(play(N, rng, mkt, dial=FOUNDER_EDGE_HI)))
    show("start from the 17 Nov close, $155.46", summary(play(N, rng, mkt, start_price=155.46)))
    lo, hi = -0.3, 0.6
    for _ in range(25):
        mid = (lo + hi) / 2
        if np.mean(play(N, np.random.default_rng(SEED), mkt, dial=mid)[:, -1] >= PRICE_BEFORE) >= 0.5: hi = mid
        else: lo = mid
    print(f"  getting back becomes a coin flip only if life after the founder ADDS {100*hi:.0f}% a year")
    # how much does each dice matter? back-above chance, bottom third vs top third of the market draw
    r3 = np.random.default_rng(SEED + 2)
    start = r3.integers(0, len(mkt) - MONTHS + 1, N)
    print("  by the market you happen to get (same game, sorted by the market's two years):")
    p = play(N, np.random.default_rng(SEED + 2), mkt)
    mret = np.array([mkt[a:a + MONTHS].sum() for a in start])
    q = np.percentile(mret, [33.3, 66.7])
    for name, sel in (("worst third of markets", mret <= q[0]), ("middle third", (mret > q[0]) & (mret <= q[1])), ("best third of markets", mret > q[1])):
        print(f"    {name:<24} back above ${PRICE_BEFORE:.0f}: {100*np.mean(p[sel,-1]>=PRICE_BEFORE):.0f}%   median ${np.median(p[sel,-1]):.0f}")

    print("\nRETIREMENT-ACCOUNT CHAPTER (plain arithmetic, no dice)")
    ratio = PRICE_BEFORE / PRICE_NOV12
    w_before = SPX_WEIGHT_NOV12 * ratio / (1 + SPX_WEIGHT_NOV12 * (ratio - 1))
    drop = 1 - PRICE_NOW / PRICE_BEFORE
    print(f"  Nvidia's share of the S&P 500 on 12 Nov: {100*SPX_WEIGHT_NOV12:.2f}% (sourced). Worked back to 28 Oct: about {100*w_before:.1f}% (derived, other stocks held still)")
    print(f"  Nvidia's fall since the story broke ({100*drop:.1f}%) took about {100*w_before*drop:.1f}% off an S&P 500 fund = ${100000*w_before*drop:,.0f} per $100,000, from this one stock alone")
    s0 = summary(base)
    print(f"  from here: Nvidia is about {100*SPX_WEIGHT_NOV12*PRICE_NOW/PRICE_NOV12:.1f}% of the index, so another 10% fall costs about ${100000*SPX_WEIGHT_NOV12*PRICE_NOW/PRICE_NOV12*0.10:,.0f} per $100,000")

    # sample paths for the scenes: lowest-ish, median-ish, highest-ish and 40 random
    order = np.argsort(base[:, -1])
    picks = {"low_p5": order[int(0.05 * N)], "median": order[N // 2], "high_p95": order[int(0.95 * N)]}
    out = {k: [round(float(x), 2) for x in base[i]] for k, i in picks.items()}
    out["random40"] = [[round(float(x), 2) for x in base[i]] for i in range(40)]
    out["fan"] = {str(q): [round(float(x), 2) for x in np.percentile(base, q, axis=0)] for q in (5, 25, 50, 75, 95)}
    json.dump(out, open("sample_paths.json", "w"))
    print("\nsaved sample_paths.json (real runs of the model, for drawing the scenes)")


if __name__ == "__main__":
    main()
