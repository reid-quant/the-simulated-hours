"""
The Simulated Hours - Episode 03
"Can Nvidia Beat History? (100 Years of Hardware Monopolies)"

Historical stress test, run 21 Nov 2026.

MODEL QUESTION
  A company that dominates a piece of hardware falls 40%+ from its record
  share price. How long until the price is back at the record?
  Replay every such episode I could source since 1929, 20,000 times.

THE ONE DIAL
  p_fast = chance this drop is the "reign survives" kind (back in ~2 years)
  rather than the "reign is over" kind (a decade or more, or never).

Not a forecast. Not financial advice. Change the numbers and re-run.
"""
import numpy as np

SEED = 21112026
RUNS = 20_000
INF = np.inf

# ----------------------------------------------------------------------------
# PARAMETERS (everything in one block)
# ----------------------------------------------------------------------------
# Nvidia today -- SOURCED (news reports, 20 Nov 2026 close)
NVDA_RECORD_CLOSE = 239.24      # 5 Oct 2026
NVDA_NOW = 125.53               # 20 Nov 2026
DRAWDOWN_NOW = 1 - NVDA_NOW / NVDA_RECORD_CLOSE          # ~0.475

# Sam's S&P 500 fund -- $100K at the October record (same Sam as Episode 01)
SAM_FUND_AT_RECORD = 100_000
NVDA_WEIGHT_NEAR_PEAK = 0.0819  # SOURCED: SPY weight 24 Sep 2026.
                                # A1 ASSUMED: weight at the 5 Oct record ~ the same.

# Episodes: hardware category leader, share price fell 40%+ from a record high.
# (name, year of peak, peak-to-trough fall, years from peak back to the peak)
# INF = has not got back (or went bankrupt first).
# S = figure confirmed in a source this session; M = from memory, verify.
EPISODES = [
    # ---- slow: the reign ended, or the price was a bubble -------------------
    ("RCA (radio)",            1929, 0.98, 37.0),   # S fall; S 1966 recovery (one source)
    ("Polaroid (instant film)",1972, 0.91, INF),    # S fall; M bankrupt 2001, never back
    ("Xerox (copiers)",        1972, 0.71, 24.0),   # S fall; M back ~1996
    ("IBM (mainframes)",       1987, 0.765, 9.7),   # S both
    ("Intel (PC chips)",       2000, 0.82, 25.6),   # M fall; S Aug 2000 -> Apr 2026
    ("Cisco (routers)",        2000, 0.89, 25.7),   # S ~90% fall; S Mar 2000 -> Dec 2025
    ("Nokia (handsets)",       2000, 0.973, INF),   # S both (26+ years, still below)
    ("Qualcomm (CDMA chips)",  2000, 0.868, 19.4),  # S both (Jan 2000 -> May 2019)
    ("Nvidia (PC graphics)",   2007, 0.84, 8.6),    # S fall; S "reclaimed 2007 peak in 2016"
    ("BlackBerry (smartphones)",2008, 0.97, INF),   # S 94.5% below today; trough deeper
    # ---- fast: the reign survived ------------------------------------------
    ("Apple (iPhone)",         2007.9, 0.60, 1.8),    # S fall; S ~22 months
    ("Apple (iPhone)",         2012.7, 0.44, 1.9),    # S fall; M back Aug 2014
    ("Nvidia (GPUs)",          2018.75, 0.56, 1.4),    # S both (16 months)
    ("Nvidia (AI chips)",      2021.9, 0.66, 1.5),    # S both (~a year and a half)
]
FAST_CUTOFF_YEARS = 3.0         # nothing in the record sits between 1.9 and 8.6 years

# A2 ASSUMED: each replay's wait is the real wait, wobbled by about a quarter.
WAIT_JITTER = 0.25
# A3 ASSUMED: each replay's fall is the real fall, wobbled a little.
FALL_JITTER = 0.03
# A4 ASSUMED: the base rate itself is uncertain -- draw it from Beta(fast+1, slow+1).
PRIOR_STRENGTH = 1.0


# ----------------------------------------------------------------------------
def split(episodes):
    fast = [e for e in episodes if e[3] <= FAST_CUTOFF_YEARS]
    slow = [e for e in episodes if e[3] > FAST_CUTOFF_YEARS]
    return fast, slow


def simulate(episodes, runs=RUNS, p_fast=None, wait_jitter=WAIT_JITTER,
             fall_jitter=FALL_JITTER, prior=PRIOR_STRENGTH, seed=SEED):
    """Each run: decide fast or slow, then replay one real episode of that kind."""
    rng = np.random.default_rng(seed)
    fast, slow = split(episodes)
    if p_fast is None:      # history's own base rate, with its uncertainty
        p = rng.beta(len(fast) + prior, len(slow) + prior, size=runs)
    else:                   # the dial, set by hand
        p = np.full(runs, p_fast)
    is_fast = rng.random(runs) < p

    wait = np.empty(runs)
    fall = np.empty(runs)
    for mask, group in ((is_fast, fast), (~is_fast, slow)):
        n = int(mask.sum())
        pick = rng.integers(0, len(group), size=n)
        w = np.array([group[i][3] for i in pick])
        f = np.array([group[i][2] for i in pick])
        wait[mask] = w * rng.lognormal(0.0, wait_jitter, size=n)
        fall[mask] = np.clip(f + rng.normal(0, fall_jitter, size=n), 0.40, 0.995)

    # Nvidia has already fallen DRAWDOWN_NOW. If the replayed episode bottomed
    # deeper than that, the rest of the fall is still ahead.
    further = np.where(fall > DRAWDOWN_NOW, 1 - (1 - fall) / (1 - DRAWDOWN_NOW), 0.0)
    return dict(
        back_3y=np.mean(wait <= 3) * 100,
        back_10y=np.mean(wait <= 10) * 100,
        not_back_20y=np.mean(wait > 20) * 100,
        gap_3_to_8=np.mean((wait > 3) & (wait <= 8)) * 100,
        median_wait=np.median(wait),
        median_fast=np.median(wait[is_fast]),
        median_slow=np.median(wait[~is_fast & np.isfinite(wait)]),
        halves_again=np.mean(further >= 0.50) * 100,
        median_further=np.median(further) * 100,
        share_fast=np.mean(is_fast) * 100,
    )


def base_rate_as_of(year):
    """Step 6 check: what would the same count have said at an earlier date?"""
    past = [e for e in EPISODES if e[1] < year]
    fast, slow = split(past)
    # only episodes whose ending was already known that year
    fast = [e for e in fast if e[1] + e[3] <= year]
    return len(fast), len(fast) + len(slow)


def stress(n_sets=400):
    """Nudge every assumed input by up to half; also swap the episode list."""
    rng = np.random.default_rng(SEED + 1)
    out = []
    for k in range(n_sets):
        eps = list(EPISODES)
        # randomly drop up to three episodes (the list is my judgement call)
        for _ in range(rng.integers(0, 4)):
            eps.pop(rng.integers(0, len(eps)))
        f, s = split(eps)
        if not f or not s:
            continue
        r = simulate(eps, runs=4000,
                     wait_jitter=WAIT_JITTER * rng.uniform(0.5, 1.5),
                     fall_jitter=FALL_JITTER * rng.uniform(0.5, 1.5),
                     prior=PRIOR_STRENGTH * rng.uniform(0.5, 1.5),
                     seed=SEED + 10 + k)
        out.append((r["back_3y"], r["gap_3_to_8"]))
    b = [o[0] for o in out]; g = [o[1] for o in out]
    return min(b), max(b), max(g)


if __name__ == "__main__":
    fast, slow = split(EPISODES)
    base = simulate(EPISODES)

    slice_record = SAM_FUND_AT_RECORD * NVDA_WEIGHT_NEAR_PEAK
    slice_now = slice_record * (1 - DRAWDOWN_NOW)

    print("=== HERO NUMBERS (baseline, 20,000 runs) ===")
    print(f"Nvidia now: {DRAWDOWN_NOW*100:.0f}% below its record close")
    print(f"Episodes: {len(EPISODES)} | fast (<=3 yrs): {len(fast)} | slow or never: {len(slow)}")
    print(f"1. Back at the record within 3 years:  {base['back_3y']:.0f} in 100")
    print(f"2. Back within 10 years:               {base['back_10y']:.0f} in 100")
    print(f"3. Still not back after 20 years:      {base['not_back_20y']:.0f} in 100")
    print(f"4. Typical wait: fast kind {base['median_fast']:.1f} yrs | slow kind {base['median_slow']:.0f} yrs"
          f" | runs landing between 3 and 8 yrs: {base['gap_3_to_8']:.1f} in 100")
    print(f"5. Sam's $100K fund: Nvidia slice ${slice_record:,.0f} at the record -> ${slice_now:,.0f} now"
          f" (${slice_record - slice_now:,.0f} gone)")
    print(f"   Price halves again from here: {base['halves_again']:.0f} in 100"
          f" | median further fall {base['median_further']:.0f}%")

    print("\n=== THE DIAL: chance the reign survives -> back within 3 years ===")
    for p in (0.1, 0.3, 0.5, 0.7, 0.9):
        r = simulate(EPISODES, p_fast=p)
        print(f"  dial {p:.0%}: back in 3 yrs {r['back_3y']:.0f} in 100 | not back after 20 yrs {r['not_back_20y']:.0f} in 100")

    print("\n=== BREAK IT ON PURPOSE ===")
    one_bubble = [e for e in EPISODES if not (e[1] == 2000 and not e[0].startswith("Cisco"))]
    r = simulate(one_bubble); f, s = split(one_bubble)
    print(f"Count the 2000 bubble once (Cisco only): {len(f)} fast of {len(one_bubble)} -> back in 3 yrs {r['back_3y']:.0f} in 100")
    no_self = [e for e in EPISODES if not (e[0].startswith("Nvidia") and e[1] >= 2018)]
    r = simulate(no_self); f, s = split(no_self)
    print(f"Delete Nvidia's own two comebacks:       {len(f)} fast of {len(no_self)} -> back in 3 yrs {r['back_3y']:.0f} in 100")
    since07 = [e for e in EPISODES if e[1] >= 2007]
    r = simulate(since07); f, s = split(since07)
    print(f"Only episodes since 2007:                {len(f)} fast of {len(since07)} -> back in 3 yrs {r['back_3y']:.0f} in 100")
    lo, hi, gmax = stress()
    print(f"Every assumption nudged by up to half, episodes dropped at random: back in 3 yrs ranges {lo:.0f} to {hi:.0f} in 100")
    print(f"  ...and the most any version put between 3 and 8 years: {gmax:.0f} in 100")

    print("\n=== CHECK AGAINST THE REAL RECORD ===")
    for yr, label in ((2018.95, "Dec 2018, Nvidia down 56%"), (2022.8, "Oct 2022, Nvidia down 66%")):
        k, n = base_rate_as_of(yr)
        print(f"{label}: history then said {k} fast of {n} -> actual: back at the record in about a year and a half")
