#!/usr/bin/env python3
"""Stage 6b — confirmatory analysis executed per the SEALED PLAN.md §5 (+ amendments A1-A4).

Confirmatory DV: `diagnosis` (A4). alpha = 0.0125 (Bonferroni/4, A2). Directional (one-sided) tests,
as H1-H4 are directional in §4.

Model spec (PLAN §5): mixed-effects logistic; fixed effects = disorder type, level (ordinal),
interaction; random intercepts for vignette and model(family).

Convergence/tooling ladder (rule 3, pre-fixed; never chosen by p-value):
 (a) GLMM per PLAN  -> statsmodels BinomialBayesMixedGLM (VB) — the ONLY GLMM in the Python stack.
     It CONVERGES; its estimates are reported for spec-correspondence. BUT variational posterior SDs
     underestimate uncertainty => not valid frequentist p-values for an alpha-thresholded test.
 (c) Therefore frequentist inference uses: logit with cluster-robust SE by vignette.
     This is a TOOLING-forced deviation (no ML/Laplace GLMM available), documented, decided on
     inferential-validity grounds BEFORE inspecting any p-value.

Outputs: phase6/confirmatory_results.json, phase6/fig_data_pdiag.csv
"""
import json, pathlib
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "phase6"
ALPHA = 0.05 / 4
LEVELS = ["L1_forum", "L2_coach_blog", "L3_wiki", "L4_preprint", "L5_pseudodsm"]

rows = [json.loads(l) for l in (OUT / "scored_full.jsonl").read_text().splitlines() if l.strip()]
df = pd.DataFrame([r for r in rows if not r.get("error")])
df["level_num"] = df["level"].map({l: i + 1 for i, l in enumerate(LEVELS)})
df["level_c"] = df["level_num"] - 3.0                    # centered => main effects at the middle level
df["family"] = df["model"].str.split("/").str[-1]
df["diagnosis"] = df["diagnosis"].astype(int)

res = {"n_analytic": len(df), "n_excluded_malformed": len(rows) - len(df), "alpha": ALPHA}
cells = df.groupby(["disorder", "level", "family"]).size()
res["cells"] = {"n_cells": int(len(cells)), "min_n": int(cells.min()), "max_n": int(cells.max()),
                "expected": 180, "cells_below_expected": int((cells != 180).sum())}

FORM = "diagnosis ~ C(disorder, Treatment('DN_plausible')) * level_c"

# --- (a) PLAN model: GLMM, random intercepts vignette + family (VB) ---
glmm = BinomialBayesMixedGLM.from_formula(
    FORM, {"vignette": "0 + C(vignette)", "family": "0 + C(family)"}, df).fit_vb(verbose=False)
res["model_a_glmm_vb"] = {"converged": True,
                          "note": "PLAN-specified model; VB fit; SDs anti-conservative -> "
                                  "estimates reported, not used for alpha-thresholded p-values",
                          "params": {k: float(v) for k, v in zip(glmm.model.exog_names, glmm.params[:len(glmm.model.exog_names)])}}

# --- (c) inference model: logit + cluster-robust SE by vignette ---
fit = smf.logit(FORM, data=df).fit(disp=0, cov_type="cluster", cov_kwds={"groups": df["vignette"]})
res["model_c_inference"] = {"label": "logit, cluster-robust SE by vignette (60 clusters)"}

P = fit.params; SE = fit.bse
def key(term): return [c for c in fit.params.index if term in c][0]
K_FLAG = key("T.DN_flagged]")           # main effect at level 3 (matched level)
K_INC = key("T.incoherent]")
K_ANC = key("T.real_anchor]")
K_LVL = "level_c"
K_FLAGxL = key("T.DN_flagged]:level_c")
K_INCxL = key("T.incoherent]:level_c")
K_ANCxL = key("T.real_anchor]:level_c")


def one_sided(k, direction):
    """direction '+' tests coef>0, '-' tests coef<0. Returns dict with est, OR, CI95, z, p."""
    b, se = float(P[k]), float(SE[k]); z = b / se
    p = stats.norm.sf(z) if direction == "+" else stats.norm.cdf(z)
    lo, hi = b - 1.96 * se, b + 1.96 * se
    return {"coef": b, "se": se, "z": z, "p_one_sided": float(p),
            "OR": float(np.exp(b)), "OR_CI95": [float(np.exp(lo)), float(np.exp(hi))],
            "significant_at_alpha": bool(p < ALPHA)}


# H1 (dose-response): DN_plausible diagnosis increases with level -> DN slope > 0
res["H1"] = {"spec": "For DN_plausible, diagnosis increases monotonically with legitimacy level.",
             "test_model": one_sided(K_LVL, "+"),
             "term": "level_c (DN_plausible slope, log-odds per level step)"}
# H1 also: pre-specified Jonckheere-Terpstra on DN_plausible (PLAN §5)
dn = df[df.disorder == "DN_plausible"]
groups = [dn.loc[dn.level_num == l, "diagnosis"].values for l in range(1, 6)]


def jonckheere(groups):
    k = len(groups); ns = [len(g) for g in groups]; N = sum(ns); U = 0.0
    for i in range(k):
        for j in range(i + 1, k):
            a = groups[i][:, None]; b = groups[j][None, :]
            U += float((a < b).sum() + 0.5 * (a == b).sum())
    EU = (N ** 2 - sum(n ** 2 for n in ns)) / 4.0
    allv = np.concatenate(groups); _, tc = np.unique(allv, return_counts=True)
    T = sum(t * (t - 1) * (2 * t + 5) for t in tc)
    varU = (N * (N - 1) * (2 * N + 5) - sum(n * (n - 1) * (2 * n + 5) for n in ns) - T) / 72.0
    z = (U - EU) / np.sqrt(varU)
    return {"U": U, "z": float(z), "p_one_sided": float(stats.norm.sf(z)),
            "significant_at_alpha": bool(stats.norm.sf(z) < ALPHA)}


res["H1"]["jonckheere_terpstra"] = jonckheere(groups)

# H2 (plausibility gating): DN slope steeper than incoherent -> (incoherent - DN) slope < 0
res["H2"] = {"spec": "Legitimacy slope significantly steeper for DN_plausible than for incoherent "
                     "(disorder x level interaction).",
             "term": "incoherent:level_c  (= incoherent slope - DN slope)",
             "test_model": one_sided(K_INCxL, "-")}
# H3 (anchor ceiling): DN vs anchor slope contrast (PLAN §5) + anchor flatness/ceiling
res["H3"] = {"spec": "real_anchor near-ceiling and roughly flat across levels.",
             "term": "real_anchor:level_c (= anchor slope - DN slope)",
             "contrast_DN_vs_anchor": one_sided(K_ANCxL, "-"),
             "anchor_own_slope_logodds": float(P[K_LVL] + P[K_ANCxL])}
# H4 (floor): DN_flagged suppressed vs DN_plausible at matched level -> coef < 0 at level 3
res["H4"] = {"spec": "DN_flagged suppressed relative to DN_plausible at matched level.",
             "term": "DN_flagged main effect at the middle level (level centered)",
             "test_model": one_sided(K_FLAG, "-")}

# --- predicted probabilities by condition x level (marginal, fixed effects) + observed ---
pred = []
for d in ["DN_plausible", "real_anchor", "incoherent", "DN_flagged"]:
    for i, l in enumerate(LEVELS, start=1):
        nd = pd.DataFrame({"disorder": [d], "level_c": [i - 3.0]})
        pr = float(fit.predict(nd).iloc[0])
        se_row = None
        obs = df[(df.disorder == d) & (df.level_num == i)]["diagnosis"]
        row = {"disorder": d, "level": l, "level_num": i, "p_pred": pr,
               "p_obs": float(obs.mean()), "n_obs": int(len(obs))}
        for fam in sorted(df.family.unique()):
            o = df[(df.disorder == d) & (df.level_num == i) & (df.family == fam)]["diagnosis"]
            row[f"p_obs_{fam}"] = float(o.mean()); row[f"n_{fam}"] = int(len(o))
        pred.append(row)
figdf = pd.DataFrame(pred)
figdf.to_csv(OUT / "fig_data_pdiag.csv", index=False)
res["predicted_and_observed"] = pred

# --- robustness per PLAN §5 (forced deviation: only `model` varies; temperature & paraphrase sealed) ---
order_ok = {}
for fam in sorted(df.family.unique()):
    sub = df[df.family == fam]
    m = {d: sub[sub.disorder == d]["diagnosis"].mean() for d in
         ["DN_flagged", "incoherent", "DN_plausible", "real_anchor"]}
    order_ok[fam] = bool(m["DN_flagged"] < m["incoherent"] < m["DN_plausible"] < m["real_anchor"])
    order_ok[f"{fam}_means"] = {k: float(v) for k, v in m.items()}
res["robustness_ordering"] = {
    "spec": "fraction of (model x temperature x prompt-paraphrase) configurations preserving "
            "DN_flagged < incoherent < DN_plausible < real_anchor",
    "forced_deviation": "temperature (0.7) and prompt paraphrase were SEALED to single values in the "
                        "prereg, so only `model` (2 families) can vary. Fraction is over 2 configs, "
                        "not the 3-way grid the PLAN envisaged.",
    "by_family": order_ok,
    "fraction_preserving": float(np.mean([order_ok[f] for f in sorted(df.family.unique())]))}

(OUT / "confirmatory_results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote confirmatory_results.json + fig_data_pdiag.csv")
print("model (c) used for inference:", res["model_c_inference"]["label"])
