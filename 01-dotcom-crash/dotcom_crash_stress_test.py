"""
The Simulated Hours - Episode 01: the next three years, replayed 20,000 times.

Question: shares are the most expensive since the dot-com peak. How often does
a dot-com sized crash show up in the next three years, and how often is a
broad-market saver ("Sam") back at her October record by then?

How it works, in plain words:
  1. Take the real month-by-month record of US share prices since 1881.
  2. One run = pick one real three-year stretch at random and replay its
     36 monthly moves, starting from last Friday's close.
  3. History says expensive starts are followed by weaker years. So every
     replay is pulled down by a steady monthly "drag" sized from that record.
     DIAL multiplies the drag: 0 = valuation does not matter, 0.5 = the base
     case (half of what history shows), 1 = the full drag history shows, which
     is the top of the dial.
  4. Count how often the path touches the red line (the crash) and how often
     it finishes above the gold line (the October record).

Data: Robert Shiller's monthly S&P Composite price and CAPE (shillerdata.com,
ie_data.xls, read 21 Nov 2026), saved here as shiller_monthly.csv.
Prices are monthly averages of daily closes, without dividends.

Usage:  python3 dotcom_crash_stress_test.py shiller_monthly.csv [v] [json]
        v = also print stress tests;  json = also write the chart data
"""
import csv
import json
import sys
import numpy as np

# ---------------- inputs (as of Friday 20 Nov 2026) ----------------
RECORD_CLOSE = 7818.93   # SOURCED: S&P 500 record close, 6 Oct 2026  -> the gold line
START_CLOSE  = 6910.39   # SOURCED: S&P 500 close, Fri 20 Nov 2026
RED_LINE     = 0.51      # SOURCED: share of the record left after a 49% fall (S&P 500, Mar 2000 - Oct 2002, daily closes)
BEAR_LINE    = 0.80      # definition: 20% below the record
LAST_MONTH   = "2026-10" # last complete month in the record
FIRST_MONTH  = "1881-01" # first month with a CAPE reading
MONTHS       = 36
N_RUNS       = 20_000
SEED         = 20261121
DIAL         = 0.5       # A1 ASSUMED and TUNED: baseline trusts half of the drag history shows, because the fit rests on a handful of expensive episodes
DIAL_MAX     = 1.0       # the top of the dial: the full straight-line fit to history
SWING        = 1.0       # A2 ASSUMED: size of monthly swings, 1 = as recorded
FRONT        = 0.0       # A3 ASSUMED: share of the drag that lands in year one beyond an even spread
TARGET       = 8638 / RECORD_CLOSE   # SOURCED: average year-end 2027 target of eight strategists (Bloomberg survey, Nov 2026)
TARGET_MONTH = 13        # Dec 2027 is 13 months after the start
DISASTERS    = [("1929-09", "1932-06"), ("2000-08", "2003-02"), ("2007-10", "2009-03")]


def load(path):
    months, price, cape = [], [], []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            months.append(r["month"])
            price.append(float(r["price"]))
            cape.append(float(r["cape"]) if r["cape"] else np.nan)
    return months, np.array(price), np.array(cape)


class History:
    """Every real 36-month stretch whose last month is on or before `last`."""

    def __init__(self, months, price, cape, last=LAST_MONTH, first=FIRST_MONTH):
        self.months, self.price, self.cape = months, price, cape
        i0, i1 = months.index(first), months.index(last)
        self.starts = np.arange(i0, i1 - MONTHS + 1)          # index of each stretch's start month
        logp = np.log(price)
        self.moves = np.stack([logp[s + 1:s + MONTHS + 1] - logp[s:s + MONTHS] for s in self.starts])
        self.fwd = self.moves.sum(axis=1)                      # 3-year log price change
        x = np.log(cape[self.starts])
        self.slope, self.icept = np.polyfit(x, self.fwd, 1)    # weaker years after expensive starts
        self.mean_fwd = self.fwd.mean()
        self.prior2 = price[self.starts] / price[self.starts - 2] - 1   # move in the 2 months before each start

    def drag(self, cape_now):
        """Total 3-year pull (log units, negative when shares are expensive)."""
        return self.icept + self.slope * np.log(cape_now) - self.mean_fwd

    def overlaps(self, a, b):
        ia, ib = self.months.index(a), self.months.index(b)
        return (self.starts < ib) & (self.starts + MONTHS > ia)


def simulate(h, cape_now, start=START_CLOSE / RECORD_CLOSE, dial=DIAL, swing=SWING,
             front=FRONT, n=N_RUNS, seed=SEED, keep=None):
    """Returns paths (n, 37) as a multiple of the gold line. keep = mask of stretches allowed."""
    rng = np.random.default_rng(seed)
    pool = np.arange(len(h.starts)) if keep is None else np.flatnonzero(keep)
    pick = rng.choice(pool, size=n)
    moves = h.moves[pick]
    mean = moves.mean(axis=1, keepdims=True)
    moves = mean + swing * (moves - mean)                     # A2: stretch the swings, keep each stretch's total
    total = dial * h.drag(cape_now)
    w = np.full(MONTHS, 1 / MONTHS)
    w[:12] += front / 12
    w[12:] -= front / 24
    moves = moves + total * w[None, :]
    paths = start * np.exp(np.concatenate([np.zeros((n, 1)), np.cumsum(moves, axis=1)], axis=1))
    return paths


def pct(x):
    return 100 * float(np.mean(x))


def score(paths, red=RED_LINE):
    low = paths[:, 1:].min(axis=1)
    return {
        "crash": pct(low <= red),
        "bear": pct(low <= BEAR_LINE),
        "back": pct(paths[:, -1] >= 1.0),
        "median_end": float(np.median(paths[:, -1])),
        "target": pct(paths[:, TARGET_MONTH] >= TARGET),
    }


def backtest(months, price, cape, when):
    """Wind the test back to month `when`: only history finished by then, start at that month's price."""
    i = months.index(when)
    h = History(months, price, cape, last=when)
    real_low = price[i + 1:i + MONTHS + 1].min() / price[i]
    paths = simulate(h, cape[i], start=1.0)
    hit = pct(paths[:, 1:].min(axis=1) <= real_low)
    return hit, 1 - real_low, len(h.starts), cape[i]


if __name__ == "__main__":
    months, price, cape = load(sys.argv[1])
    verbose = "v" in sys.argv[2:]
    h = History(months, price, cape)
    i_last = months.index(LAST_MONTH)
    cape_now = cape[i_last] * START_CLOSE / price[i_last]      # October CAPE moved to Friday's close
    start = START_CLOSE / RECORD_CLOSE

    base = score(simulate(h, cape_now))
    zero = score(simulate(h, cape_now, dial=0.0))
    top = score(simulate(h, cape_now, dial=DIAL_MAX))
    bt2000 = backtest(months, price, cape, "2000-03")
    bt1929 = backtest(months, price, cape, "1929-09")

    print(f"inputs: start {start:.3f} of the record, CAPE at start {cape_now:.1f}, "
          f"{len(h.starts)} real 3-year stretches, drag {100*(np.exp(h.drag(cape_now))-1):.0f}% over 3 years "
          f"(slope {h.slope:.3f})")
    print("SIMULATION RESULTS (20,000 runs, 3 years)")
    print(f"1. Dot-com sized crash (touches the red line): {base['crash']:.1f} in 100")
    print(f"2. Bear market (20% below the record): {base['bear']:.1f} in 100")
    print(f"3. Back above the gold line after 3 years: {base['back']:.1f} in 100; "
          f"middle run ends at {100*base['median_end']:.0f}% of the record")
    print(f"4. Dial at zero: crash {zero['crash']:.1f}, back {zero['back']:.1f} | "
          f"dial at max: crash {top['crash']:.1f}, back {top['back']:.1f}")
    print(f"5. Back-test Mar 2000: {bt2000[0]:.1f} in 100 for the real {100*bt2000[1]:.0f}% fall "
          f"({bt2000[2]} stretches, CAPE {bt2000[3]:.1f})")
    print(f"6. Back-test Sep 1929: {bt1929[0]:.1f} in 100 for the real {100*bt1929[1]:.0f}% fall "
          f"({bt1929[2]} stretches, CAPE {bt1929[3]:.1f})")
    print(f"7. Wall Street average target for Dec 2027 (8,638, {TARGET:.3f}x the record): {base['target']:.1f} in 100")

    if "json" in sys.argv[2:]:
        p = simulate(h, cape_now)
        rng = np.random.default_rng(7)
        low = p[:, 1:].min(axis=1)
        end = p[:, -1]
        nc, nb = round(base["crash"]), round(base["back"])       # a fair 100 to draw: same shares as all 20,000
        show = np.concatenate([
            rng.choice(np.flatnonzero(low <= RED_LINE), nc, replace=False),
            rng.choice(np.flatnonzero((low > RED_LINE) & (end >= 1)), nb, replace=False),
            rng.choice(np.flatnonzero((low > RED_LINE) & (end < 1)), 100 - nc - nb, replace=False)])
        json.dump({
            "start": start, "red": RED_LINE, "results": base, "zero": zero, "top": top,
            "pctl": {str(q): np.percentile(p, q, axis=0).round(4).tolist() for q in (5, 25, 50, 75, 95)},
            "show100": p[show].round(4).tolist(), "n_crash": nc, "n_back": nb,
        }, open("ep01_chart_data.json", "w"))

    if verbose:
        print("\n--- record check ---")
        s = h.starts
        hi = cape[s] >= cape_now
        yrs = sorted({months[i][:4] for i in s[hi]})
        print(f"months at least as expensive as now (CAPE >= {cape_now:.1f}) with 3 years of history after: "
              f"{hi.sum()} months, years {yrs}; higher 3 years later in {pct(h.fwd[hi] > 0):.0f}%")
        for lo_c in (30, 32.5):
            m = cape[s] >= lo_c
            for a, b in (("1929", "1930"), ("1996", "2002"), ("2017", "2024")):
                e = m & np.array([a <= months[i][:4] <= b for i in s])
                if e.sum():
                    print(f"  CAPE >= {lo_c}: {a}-{b}: {e.sum()} months, higher 3y later in {pct(h.fwd[e] > 0):.0f}%")
        print(f"all history: 3y later higher in {pct(h.fwd > 0):.0f}%; ever fell {100*(1-RED_LINE/start):.0f}% from a start: "
              f"{pct(np.exp(np.minimum.accumulate(np.cumsum(h.moves,axis=1),axis=1)[:,-1]) <= RED_LINE/start):.1f}%")
        print("\n--- dial sweep ---")
        for d in (0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10):
            r = score(simulate(h, cape_now, dial=d))
            print(f"dial {d:>4}: crash {r['crash']:5.1f}  bear {r['bear']:5.1f}  back {r['back']:5.1f}  median end {r['median_end']:.2f}")
        print("\n--- targets by month 13 ---")
        p = simulate(h, cape_now)
        for t in (1.0, 1.03, 1.05, 1.08, 1.10, 1.15):
            print(f"target {t:.2f}x record: {pct(p[:, TARGET_MONTH] >= t):.1f}")
        print("\n--- vary every assumption by up to half (300 sets) ---")
        rng = np.random.default_rng(1)
        res = []
        for k in range(300):
            d, sw = rng.uniform(0.5, 1.5, 2); d *= DIAL
            fr = rng.uniform(-0.5, 0.5)
            r = score(simulate(h, cape_now, dial=d, swing=sw, front=fr, n=4000, seed=k))
            res.append((r["crash"], r["bear"], r["back"]))
        res = np.array(res)
        for name, col in zip(("crash", "bear", "back"), res.T):
            print(f"{name}: min {col.min():.1f}  p5 {np.percentile(col,5):.1f}  median {np.median(col):.1f}  p95 {np.percentile(col,95):.1f}  max {col.max():.1f}")
        for name, kw in (("drag only", dict(swing=1, front=0)), ("swing only", dict(dial=1, front=0)), ("timing only", dict(dial=1, swing=1))):
            cr = []
            for v in np.linspace(0.5, 1.5, 11):
                a = dict(dial=v * DIAL, swing=v, front=v - 1); a.update({k_: (DIAL if k_ == 'dial' else v_) for k_, v_ in kw.items()})
                cr.append(score(simulate(h, cape_now, n=8000, **a))["crash"])
            print(f"  {name}: crash {min(cr):.1f} to {max(cr):.1f}")
        print("\n--- break it on purpose ---")
        bad = np.zeros(len(s), bool)
        for a, b in DISASTERS:
            bad |= h.overlaps(a, b)
        r = score(simulate(h, cape_now, keep=~bad))
        crashers = np.exp(np.minimum.accumulate(np.cumsum(h.moves + DIAL * h.drag(cape_now)/MONTHS, axis=1), axis=1)[:, -1]) * start <= RED_LINE
        print(f"without 1929, dot-com and 2008 stretches ({bad.sum()} removed): crash {r['crash']:.2f}, bear {r['bear']:.1f}, back {r['back']:.1f}")
        print(f"share of crashing stretches that overlap those three: {pct(bad[crashers]):.0f}% of {crashers.sum()}")
        for thr in (-0.08, -0.10):
            q = h.prior2 <= thr
            r = score(simulate(h, cape_now, keep=q))
            print(f"only stretches that began after a {100*thr:.0f}% drop in 2 months ({q.sum()} stretches): crash {r['crash']:.1f}, bear {r['bear']:.1f}, back {r['back']:.1f}")
        lo, hi_ = 0.0, 40.0
        for _ in range(30):
            mid = (lo + hi_) / 2
            if score(simulate(h, cape_now, dial=mid))["crash"] < 50: lo = mid
            else: hi_ = mid
        print(f"dial needed for a 50-50 crash: {lo:.1f}x the full drag history shows")
        for sd in (1, 2, 3):
            r = score(simulate(h, cape_now, seed=sd))
            print(f"seed {sd}: crash {r['crash']:.1f}, bear {r['bear']:.1f}, back {r['back']:.1f}")
