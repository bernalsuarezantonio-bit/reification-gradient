#!/usr/bin/env python3
"""power_sim_r0b.py — Stage R0b: joint grid N_vignettes x R, with GPU-hours per cell.

Extends R0 (power_sim.py) to vary the number of vignettes N in {30,45,60} jointly with
R in {3,5,8}, across the same variance scenarios (incl. high_slopevar), same decision rule
(H2 medium >= 0.80 at alpha=0.0125). Adds a GPU-hours column using the latencies MEASURED in
the R0b diagnostic (num_ctx=2048, num_predict=512, representative long prompt; both models 100%
on GPU after fixing the KV-cache offload):

    mistral-small3.1:24b  ~5.4 s/call (warm, ~98 tok/s)
    qwen2.5:32b           ~7.5 s/call (warm, ~70 tok/s)   [was ~70 s with default ctx / CPU offload]

Model, tests and effect grid are identical to R0 (see POWER.md). N enters as the sample size of
the two-stage t-tests: increasing N shrinks the SE of the mean slope by ~sqrt(N), which is the ONLY
lever that can beat the irreducible per-condition slope variance (sigma_sc) ceiling that R alone
cannot (see R0 sensitivity).
"""
import numpy as np
from scipy import stats
import csv, pathlib

OUT = pathlib.Path(__file__).resolve().parent
SEED = 20260710
C = np.array([-2, -1, 0, 1, 2], dtype=float)
SUM_C2 = float((C ** 2).sum())      # =10
N_SIMS = 1000
N_GRID = [30, 45, 60]
R_GRID = [3, 5, 8]
EFFECTS = {"small": 0.2, "medium": 0.5, "large": 0.8}
DECISION_ALPHA = 0.05 / 4           # 0.0125 (Bonf/4), same as R0
LAT = {"mistral": 5.4, "qwen": 7.5}  # measured s/call, num_ctx=2048, num_predict=512, 100% GPU

SCENARIOS = [
    dict(name="primary",       sigma_e=1.0, sigma_s=0.10, sigma_sc=0.08),
    dict(name="low_noise",     sigma_e=0.7, sigma_s=0.10, sigma_sc=0.08),
    dict(name="high_slopevar", sigma_e=1.0, sigma_s=0.15, sigma_sc=0.12),
    dict(name="low_slopevar",  sigma_e=1.0, sigma_s=0.05, sigma_sc=0.04),
]


def gpu_hours(n_vign, R):
    per_fam_calls = 4 * 5 * n_vign * R           # conditions x levels x vignettes x reps
    secs = per_fam_calls * (LAT["mistral"] + LAT["qwen"])
    return secs / 3600.0


def power_h2(rng, E, sc, R, n_vign, alpha):
    shape = (N_SIMS, n_vign)
    repvar = sc["sigma_e"] ** 2 / (SUM_C2 * R)   # per-vignette slope var from R reps
    ss_dn = rng.normal(0, sc["sigma_sc"], shape)
    ss_in = rng.normal(0, sc["sigma_sc"], shape)
    rep_dn = rng.normal(0, np.sqrt(repvar), shape)
    rep_in = rng.normal(0, np.sqrt(repvar), shape)
    diff = E / 4.0 + (ss_dn - ss_in) + (rep_dn - rep_in)   # shared slope s_i cancels (paired)
    mean = diff.mean(axis=1)
    se = diff.std(axis=1, ddof=1) / np.sqrt(n_vign)
    p = stats.t.sf(mean / se, df=n_vign - 1)
    return float((p < alpha).mean())


def main():
    rng = np.random.default_rng(SEED)
    rows = []
    for sc in SCENARIOS:
        for n in N_GRID:
            for R in R_GRID:
                pm = power_h2(rng, EFFECTS["medium"], sc, R, n, DECISION_ALPHA)
                rows.append(dict(scenario=sc["name"], N=n, R=R,
                                 power_H2_medium=round(pm, 3),
                                 gpu_hours=round(gpu_hours(n, R), 1),
                                 meets_80=pm >= 0.80))
    with (OUT / "r0b_grid.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    print(f"SEED {SEED} | N_SIMS {N_SIMS} | decision alpha {DECISION_ALPHA} | H2 medium")
    for sc in SCENARIOS:
        print(f"\n== {sc['name']} ==  (power_H2 medium | GPU-h)")
        print(f"{'':<6}" + "".join(f"R={R:<10}" for R in R_GRID))
        for n in N_GRID:
            cells = []
            for R in R_GRID:
                r = next(x for x in rows if x['scenario'] == sc['name'] and x['N'] == n and x['R'] == R)
                mark = "*" if r['meets_80'] else " "
                cells.append(f"{r['power_H2_medium']:.2f}{mark}/{r['gpu_hours']}h")
            print(f"N={n:<4}" + "".join(f"{c:<12}" for c in cells))
    # cheapest cell meeting >=0.80 per scenario
    print("\n-- celda más barata (min GPU-h) con potencia>=0.80 por escenario --")
    for sc in SCENARIOS:
        ok = [x for x in rows if x['scenario'] == sc['name'] and x['meets_80']]
        if ok:
            best = min(ok, key=lambda x: x['gpu_hours'])
            print(f"  {sc['name']:<15} N={best['N']} R={best['R']} power={best['power_H2_medium']} {best['gpu_hours']}h")
        else:
            print(f"  {sc['name']:<15} NINGUNA celda del grid alcanza 0.80")


if __name__ == "__main__":
    main()
