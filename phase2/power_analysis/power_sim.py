#!/usr/bin/env python3
"""power_sim.py — Stage R0 power analysis by simulation (NO GPU).

Justifies R (reps per cell) for the preregistration. Pure Monte-Carlo: we generate judge-style
rubric scores under a dose-response model and run the SAME family of tests that will be
preregistered, then read off power vs R.

Design of the confirmatory run: 4 disorder conditions x 5 legitimacy levels (L1..L5) x 30
vignettes x 2 model families x R reps. This power analysis targets the two dose-response
hypotheses that R must support:

  H1 (trend):        DN_plausible rubric score rises monotonically across L1..L5.
  H2 (interaction):  DN slope  >  incoherent slope  (reification, not mere sycophancy).

Outcome model (continuous proxy for a rubric commitment/reification score, ~0-4 scale; the
preregistered analysis uses per-DV GLMMs — logistic/Poisson — but a continuous composite is a
standard, slightly-conservative proxy for power planning). Level coded c_k = -2..2 (centered):

  Y_{i,k,cond,r} = mu_cond + u_i + slope_{cond,i} * c_k + e_{i,k,cond,r}
  slope_{cond,i} = beta_cond + s_i (shared vignette susceptibility) + ss_{cond,i} (cond-specific)
  u_i  ~ N(0, sigma_u^2)         # vignette intercept  (cancels in a within-vignette slope test)
  s_i  ~ N(0, sigma_s^2)         # shared random slope  -> limits H1 (NOT reduced by R)
  ss   ~ N(0, sigma_sc^2)        # condition-specific random slope -> limits H2 (NOT reduced by R)
  e    ~ N(0, sigma_e^2)         # per-rep residual (temperature stochasticity) -> reduced by R

Because each vignette is seen at every level, the trend test is WITHIN vignette: the OLS
per-vignette slope estimate is  slope_i + N(0, sigma_e^2 / (10 R))  (10 = sum c_k^2 over L1..L5).
So more reps shrink only the residual term; sigma_s / sigma_sc set the irreducible ceilings.

Tests (two-stage, matching the preregistered mixed model for this balanced design; asymptotically
equivalent to an LMM with vignette random effects, and slightly conservative — so the chosen R is
a safe upper bound):
  H1: one-sample t-test that mean per-vignette DN slope > 0            (one-sided)
  H2: one-sample t-test that mean per-vignette (DN slope - INC slope) > 0  (paired; one-sided)

Effect sizes are expressed in rubric-score SD units (total obs SD ~= 1.0 in the primary scenario),
so an effect of E is the L1->L5 mean change in SD units. See POWER.md for the a-priori grid and the
PRE-FIXED decision rule.
"""
import numpy as np
from scipy import stats
import csv, pathlib

OUT = pathlib.Path(__file__).resolve().parent
SEED = 20260710
N_VIGN = 30
N_LEVELS = 5
C = np.array([-2, -1, 0, 1, 2], dtype=float)   # centered level codes; sum(C^2)=10
SUM_C2 = float((C ** 2).sum())
N_SIMS = 1000
R_GRID = [1, 2, 3, 5, 8, 10]

# A-priori effect grid (L1->L5 change in SD units). Justification in POWER.md (framing/authority
# effects ~ Cohen d 0.2/0.5/0.8). SAME grid for H1 and H2 (prompt: "misma rejilla").
EFFECTS = {"small": 0.2, "medium": 0.5, "large": 0.8}

# Variance scenarios (SD units). Primary = conservative (high rep noise). Sensitivity around it.
PRIMARY = dict(sigma_e=1.0, sigma_s=0.10, sigma_sc=0.08, sigma_u=0.5)
SENSITIVITY = [
    dict(name="primary",        sigma_e=1.0, sigma_s=0.10, sigma_sc=0.08, sigma_u=0.5),
    dict(name="low_noise",      sigma_e=0.7, sigma_s=0.10, sigma_sc=0.08, sigma_u=0.5),
    dict(name="high_slopevar",  sigma_e=1.0, sigma_s=0.15, sigma_sc=0.12, sigma_u=0.5),
    dict(name="low_slopevar",   sigma_e=1.0, sigma_s=0.05, sigma_sc=0.04, sigma_u=0.5),
]

# Alpha levels: 0.05 (uncorrected) and Bonferroni over the 4 primary directional hypotheses
# (H1..H4); 0.01 shown too (H1..H5).
ALPHAS = {"0.05": 0.05, "0.0125_bonf4": 0.05 / 4, "0.01_bonf5": 0.05 / 5}


def _slopes(rng, n_sims, E, sc, per_vign_repvar):
    """Return (dn_slopes, inc_slopes) arrays shape (n_sims, N_VIGN)."""
    shape = (n_sims, N_VIGN)
    s = rng.normal(0, sc["sigma_s"], shape)            # shared slope dev (cancels in H2)
    ss_dn = rng.normal(0, sc["sigma_sc"], shape)
    ss_in = rng.normal(0, sc["sigma_sc"], shape)
    rep_dn = rng.normal(0, np.sqrt(per_vign_repvar), shape)   # residual term after R reps
    rep_in = rng.normal(0, np.sqrt(per_vign_repvar), shape)
    dn = E / 4.0 + s + ss_dn + rep_dn      # DN total slope effect E -> per-step E/4
    inc = 0.0 + s + ss_in + rep_in         # INC slope 0 -> H2 difference = E (paired cancels s)
    return dn, inc


def _power(slopes, alpha):
    """One-sided t-test (mean>0) across vignettes, per simulation. Return power (proportion)."""
    mean = slopes.mean(axis=1)
    sd = slopes.std(axis=1, ddof=1)
    se = sd / np.sqrt(N_VIGN)
    t = mean / se
    p_one = stats.t.sf(t, df=N_VIGN - 1)   # upper tail
    return float((p_one < alpha).mean())


def run_point(rng, E, sc, R, alpha):
    per_vign_repvar = sc["sigma_e"] ** 2 / (SUM_C2 * R)   # var of OLS per-vignette slope from reps
    dn, inc = _slopes(rng, N_SIMS, E, sc, per_vign_repvar)
    power_h1 = _power(dn, alpha)
    power_h2 = _power(dn - inc, alpha)
    return power_h1, power_h2


def main():
    rng = np.random.default_rng(SEED)
    # main curves at PRIMARY scenario, all alphas
    rows = []
    for aname, alpha in ALPHAS.items():
        for ename, E in EFFECTS.items():
            for R in R_GRID:
                p1, p2 = run_point(rng, E, PRIMARY, R, alpha)
                rows.append(dict(scenario="primary", alpha=aname, effect=ename,
                                 effect_sd=E, R=R, power_H1=round(p1, 3), power_H2=round(p2, 3)))
    with (OUT / "power_curves.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # sensitivity: medium effect only, decision alpha, across variance scenarios
    dec_alpha = ALPHAS["0.0125_bonf4"]
    srows = []
    for sc in SENSITIVITY:
        for R in R_GRID:
            p1, p2 = run_point(rng, EFFECTS["medium"], sc, R, dec_alpha)
            srows.append(dict(scenario=sc["name"], sigma_e=sc["sigma_e"], sigma_s=sc["sigma_s"],
                              sigma_sc=sc["sigma_sc"], effect="medium", alpha="0.0125_bonf4",
                              R=R, power_H1=round(p1, 3), power_H2=round(p2, 3)))
    with (OUT / "sensitivity.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(srows[0].keys())); w.writeheader(); w.writerows(srows)

    # DECISION: min R with power_H2 >= 0.80 for MEDIUM effect at decision alpha, PRIMARY scenario.
    chosen = None
    for r in rows:
        if (r["scenario"] == "primary" and r["alpha"] == "0.0125_bonf4"
                and r["effect"] == "medium" and r["power_H2"] >= 0.80):
            chosen = r["R"] if chosen is None else min(chosen, r["R"])
    print("SEED", SEED, "| N_SIMS", N_SIMS)
    print("Decision (H2 medium, alpha=0.0125 Bonf/4, primary scenario): R* =", chosen)
    print("\n-- primary scenario, power_H2 by alpha x effect x R --")
    print(f"{'alpha':<14}{'effect':<8}" + "".join(f"R={R:<6}" for R in R_GRID))
    for aname in ALPHAS:
        for ename in EFFECTS:
            cells = [next(r for r in rows if r['alpha']==aname and r['effect']==ename and r['R']==R)['power_H2'] for R in R_GRID]
            print(f"{aname:<14}{ename:<8}" + "".join(f"{c:<8}" for c in cells))
    with (OUT / "chosen_R.txt").open("w") as f:
        f.write(f"R*={chosen}\nrule=min R with power_H2>=0.80 for medium effect at alpha=0.0125 (Bonf/4), primary scenario\nseed={SEED}\nn_sims={N_SIMS}\n")


if __name__ == "__main__":
    main()
