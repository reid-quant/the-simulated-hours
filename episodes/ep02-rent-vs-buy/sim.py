"""
The Simulated Hours - Episode 02: Rent vs Buy, simulated 20,000 times.

Two identical households start with the same cash and the same monthly budget.
  BUYER  : buys the median US home with 20% down on a 30-year fixed mortgage.
  RENTER : rents the typical US rental and puts the down payment, the closing
           costs and every dollar of monthly savings into a broad index fund.
Whoever has the cheaper year invests the difference, so both spend the same.
After N years the buyer sells; we compare what each one walks away with.

History engine: block bootstrap of real US years 1976-2022, keeping each
year's stock return, home-price change and inflation together.

Data (both public, monthly CSVs from github.com/datasets):
  s-and-p-500/data/data.csv            Shiller S&P 500 price, dividend, CPI
  house-prices-us/data/national-month.csv   Case-Shiller US national home price index

Usage:  python sim.py          prints the 5 hero numbers from the video
        python sim.py v        also prints every stress test
Both data files ship in ./data (copies taken 21 Nov 2026). Random seed is fixed,
so every run gives the same numbers.

MODEL · NOT A FORECAST · NOT FINANCIAL ADVICE
"""
import csv
import sys
import numpy as np

# ---------------- inputs (as of 21 Nov 2026) ----------------
HOME_PRICE   = 416_700   # NAR median existing-home price, Oct 2026
RENT_MONTH   = 1_965     # Zillow Observed Rent Index, typical US asking rent (mid-2026)
MORT_RATE    = 0.0728    # Freddie Mac 30-yr fixed, 19 Nov 2026
DOWN         = 0.20
BUY_COST     = 0.03      # closing costs, share of price
SELL_COST    = 0.06      # agent + closing, share of sale price
PROP_TAX     = 0.010     # per year, share of home value
HOME_INS     = 0.005
MAINT        = 0.010
RENT_INS     = 200       # renter's insurance per year
RENT_PREMIUM = 0.005     # rent grows at inflation + 0.5 pt (assumption)
FUND_FEE     = 0.0005
CAP_GAINS    = 0.15      # tax on index-fund gains at the end; home gain is exempt
YEARS        = 10
N_RUNS       = 20_000
BLOCK        = 5         # years per bootstrap block
SEED         = 20261121


def load_history(sp_path, hp_path):
    """Annual (Dec to Dec) stock total return, home-price change, inflation."""
    sp = {}
    with open(sp_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["Date"][5:7] == "12":
                sp[int(r["Date"][:4])] = (float(r["SP500"]), float(r["Dividend"]),
                                          float(r["Consumer Price Index"]))
    hp = {}
    with open(hp_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["Date"][5:7] == "12":
                hp[int(r["Date"][:4])] = float(r["National-US"])
    rows = []
    for y in range(1976, 2023):
        p0, _, c0 = sp[y - 1]
        p1, d1, c1 = sp[y]
        rows.append(((p1 + d1) / p0 - 1, hp[y] / hp[y - 1] - 1, c1 / c0 - 1))
    return np.array(rows)          # shape (47, 3)


def draw_paths(hist, years, n, rng):
    """Circular block bootstrap: stitch real multi-year stretches together."""
    T = len(hist)
    n_blocks = -(-years // BLOCK)
    starts = rng.integers(0, T, size=(n, n_blocks))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]) % T
    return hist[idx.reshape(n, -1)[:, :years]]      # (n, years, 3)


def simulate(hist, years=YEARS, n=N_RUNS, rent_month=RENT_MONTH, rate=MORT_RATE,
             invest_share=1.0, price=HOME_PRICE, refi_rate=None, refi_year=3,
             stock_cut=0.0, home_boost=0.0, seed=SEED):
    """Returns (renter_wealth, buyer_wealth) arrays, in today's dollars."""
    rng = np.random.default_rng(seed)
    paths = draw_paths(hist, years, n, rng)
    stock = paths[:, :, 0] - FUND_FEE - stock_cut      # stress dial: weaker stocks
    home = paths[:, :, 1] + home_boost                # stress dial: hotter housing
    infl = paths[:, :, 2]

    loan = price * (1 - DOWN)
    upfront = price * (DOWN + BUY_COST)

    def payment(bal, r, months):
        m = r / 12
        return bal * m / (1 - (1 + m) ** -months)

    pmt = np.full(n, payment(loan, rate, 360))
    r_now = np.full(n, rate)
    bal = np.full(n, loan)
    value = np.full(n, float(price))
    rent = np.full(n, rent_month * 12.0)
    cpi = np.ones(n)

    r_port, r_basis = np.full(n, upfront), np.full(n, upfront)   # renter's fund
    b_port, b_basis = np.zeros(n), np.zeros(n)                   # buyer's side fund

    for t in range(years):
        if refi_rate is not None and t == refi_year:             # stress test
            bal = bal * 1.02                                     # 2% refi cost rolled in
            r_now = np.full(n, refi_rate)
            pmt = payment(bal, refi_rate, 360)
        own_cost = pmt * 12 + value * (PROP_TAX + HOME_INS + MAINT)
        rent_cost = rent + RENT_INS * cpi
        gap = own_cost - rent_cost                # >0: renter has cash left over
        r_add = np.clip(gap, 0, None) * invest_share
        b_add = np.clip(-gap, 0, None)            # buyer always invests his savings

        g = 1 + stock[:, t]
        r_port = r_port * g + r_add * np.sqrt(g)  # contributions land mid-year
        b_port = b_port * g + b_add * np.sqrt(g)
        r_basis += r_add
        b_basis += b_add

        m = r_now / 12                            # amortise 12 months
        f = (1 + m) ** 12
        bal = bal * f - pmt * (f - 1) / m
        value *= 1 + home[:, t]
        rent *= 1 + infl[:, t] + RENT_PREMIUM
        cpi *= 1 + infl[:, t]

    def after_tax(port, basis):
        return port - CAP_GAINS * np.clip(port - basis, 0, None)

    renter = after_tax(r_port, r_basis) / cpi
    buyer = (value * (1 - SELL_COST) - bal + after_tax(b_port, b_basis)) / cpi
    return renter, buyer


def win_rate(r, b):
    return 100 * np.mean(r > b)


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    hist = load_history(os.path.join(here, "data", "shiller_sp500_monthly.csv"),
                        os.path.join(here, "data", "caseshiller_national_monthly.csv"))
    verbose = len(sys.argv) > 1 and sys.argv[1] == "v"

    r, b = simulate(hist)
    gap = r - b
    lazy_r, lazy_b = simulate(hist, invest_share=0.0)   # spends the monthly savings
    lazy_gap = lazy_r - lazy_b

    print("HERO NUMBERS (20,000 runs, 10 years, today's dollars)")
    print(f"1. Renter finishes richer in {win_rate(r, b):.0f} of 100 futures")
    print(f"2. Median head start for the renter: ${np.median(gap):,.0f}")
    print(f"   (renter ${np.median(r):,.0f} vs buyer ${np.median(b):,.0f})")
    low_r, low_b = simulate(hist, rate=0.03)            # the 2021 mortgage
    print(f"3. Same test with a 3% mortgage: buyer finishes richer in "
          f"{100 - win_rate(low_r, low_b):.0f} of 100")
    print(f"4. Twist - renter spends the monthly savings instead of investing: "
          f"ahead in {win_rate(lazy_r, lazy_b):.0f} of 100, median gap ${np.median(lazy_gap):,.0f}")
    fair_r, fair_b = simulate(hist, rent_month=2450)    # rent for a house-sized rental
    weak_r, weak_b = simulate(hist, stock_cut=0.04)     # stocks 4 pts/yr below history
    print(f"5. Stress tests: house-sized rent ($2,450) -> {win_rate(fair_r, fair_b):.0f} of 100; "
          f"stocks 4 pts/yr weaker -> {win_rate(weak_r, weak_b):.0f} of 100")

    if verbose:
        print("\n--- stress tests (10 years unless noted) ---")
        loan = HOME_PRICE * (1 - DOWN)
        m = MORT_RATE / 12
        pmt = loan * m / (1 - (1 + m) ** -360)
        own1 = pmt * 12 + HOME_PRICE * (PROP_TAX + HOME_INS + MAINT)
        print(f"year-1 owning ${own1:,.0f} (P&I ${pmt:,.0f}/mo) vs renting ${RENT_MONTH*12+RENT_INS:,.0f}; "
              f"monthly gap ${(own1 - RENT_MONTH*12 - RENT_INS)/12:,.0f}")
        print(f"history: {len(hist)} yrs, mean stock {hist[:,0].mean():.3f}, home {hist[:,1].mean():.3f}, cpi {hist[:,2].mean():.3f}")
        print(f"10y renter p10/p50/p90 gap: {np.percentile(gap,[10,50,90]).round(-3)}")
        for sh in (0.75, 0.5, 0.25):
            rr, bb = simulate(hist, invest_share=sh)
            print(f"invest {sh:.0%} of savings: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        for rm in (2200, 2450, 2700, 3000):
            rr, bb = simulate(hist, rent_month=rm)
            print(f"rent ${rm}: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}, P/R {HOME_PRICE/(rm*12):.1f}")
        for rt in (0.03, 0.04, 0.05, 0.06, 0.065):
            rr, bb = simulate(hist, rate=rt)
            print(f"mortgage {rt:.2%}: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        for rf in (0.06, 0.055, 0.05):
            rr, bb = simulate(hist, refi_rate=rf)
            print(f"refi to {rf:.2%} in yr 3: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        for y in (5, 20, 30):
            rr, bb = simulate(hist, years=y)
            print(f"{y}y: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}, med renter {np.median(rr):,.0f}, buyer {np.median(bb):,.0f}")
        rr, bb = simulate(hist, years=30, invest_share=0.0)
        print(f"30y lazy: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        rr, bb = simulate(hist, rent_month=2450, invest_share=0.5)
        print(f"rent 2450 + invest half: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        for cut in (0.02, 0.03, 0.04, 0.05):
            rr, bb = simulate(hist, stock_cut=cut)
            print(f"stocks -{cut:.0%}/yr: win {win_rate(rr,bb):.0f}, med gap {np.median(rr-bb):,.0f}")
        for hb in (-0.02, 0.02):
            rr, bb = simulate(hist, home_boost=hb)
            print(f"home prices {hb:+.0%}/yr: win {win_rate(rr,bb):.0f}")
        print(f"buyer ahead by $100K+: {100*np.mean(gap < -100_000):.0f} of 100; renter ahead by $100K+: {100*np.mean(gap > 100_000):.0f} of 100")
        bal1 = loan * (1 + m) ** 12 - pmt * ((1 + m) ** 12 - 1) / m
        print(f"year-1 principal paid ${loan - bal1:,.0f}, interest ${pmt*12 - (loan - bal1):,.0f}; selling cost today ${HOME_PRICE*SELL_COST:,.0f}")
        for sd in (1, 2, 3):
            rr, bb = simulate(hist, seed=sd)
            print(f"seed {sd}: win {win_rate(rr,bb):.1f}, med gap {np.median(rr-bb):,.0f}")
