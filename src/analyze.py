#!/usr/bin/env python3
"""analyze.py — primary analyses mapped to the hypotheses in PLAN.md.

Outputs (data/scored/):
  - summary.csv        : per (model, disorder, level) means of every DV
  - reification.csv    : RR(d,L) = mean_DV(d,L) / mean_DV(real_anchor,L)
  - tests.txt          : H1 monotonic trend, H2/H3 slope contrasts, H4 floor, robustness fraction
Stats kept dependency-light (numpy/pandas/scipy). Mixed-effects (statsmodels) hook noted inline.
"""
import pathlib, json, sys
import pandas as pd, numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCORED = ROOT / "data" / "scored" / "scored.jsonl"
LEVEL_ORDER = {"L1_forum":1,"L2_coach_blog":2,"L3_wiki":3,"L4_preprint":4,"L5_pseudodsm":5}
DVS = ["diagnosis","confidence","criteria_invented","treatment_recommended",
       "differential_offered","epistemic_flag","emergent_symptom_tokens"]

def load():
    rows = [json.loads(l) for l in SCORED.open()]
    df = pd.DataFrame(rows)
    df["lvl"] = df["level"].map(LEVEL_ORDER)
    for dv in DVS:
        df[dv] = pd.to_numeric(df[dv], errors="coerce")
    return df

def summary(df):
    g = df.groupby(["model","disorder","level","lvl"])[DVS].mean().reset_index()
    return g.sort_values(["model","disorder","lvl"])

def reification(df):
    cell = df.groupby(["disorder","lvl"])[DVS].mean().reset_index()
    anchor = cell[cell.disorder=="real_anchor"].set_index("lvl")[DVS]
    out=[]
    for _,r in cell.iterrows():
        denom = anchor.loc[r["lvl"]]
        rr = {f"RR_{dv}": (r[dv]/denom[dv] if denom[dv] not in (0,np.nan) else np.nan) for dv in DVS}
        out.append({"disorder":r["disorder"],"lvl":r["lvl"],**rr})
    return pd.DataFrame(out)

def trend_test(df, disorder, dv):
    sub = df[df.disorder==disorder]
    groups = [sub[sub.lvl==l][dv].dropna().values for l in sorted(sub.lvl.unique())]
    groups = [g for g in groups if len(g)]
    if len(groups) < 3: return None
    # Jonckheere-Terpstra via Kendall tau as a light proxy for ordered trend
    x = np.concatenate([[l]*len(g) for l,g in zip(sorted(sub.lvl.unique()),groups)])
    y = np.concatenate(groups)
    tau,p = stats.kendalltau(x,y)
    return tau,p

def slope(df, disorder, dv):
    sub = df[df.disorder==disorder][["lvl",dv]].dropna()
    if sub[dv].nunique()<=1 or len(sub)<3: return np.nan
    return np.polyfit(sub["lvl"], sub[dv], 1)[0]

def robustness(df, dv="diagnosis"):
    # fraction of (model) slices preserving ordering DN_flagged < incoherent < DN_plausible < real_anchor
    order = ["DN_flagged","incoherent","DN_plausible","real_anchor"]
    ok=0; tot=0
    for m, sub in df.groupby("model"):
        means = sub.groupby("disorder")[dv].mean()
        if not set(order).issubset(means.index): continue
        tot+=1
        vals=[means[o] for o in order]
        if all(earlier<=later for earlier,later in zip(vals,vals[1:])): ok+=1
    return ok, tot

def main():
    df = load()
    if df[DVS].isna().all().all():
        print("No scored DVs yet (judge not wired). Showing structure only.")
    summary(df).to_csv(ROOT/"data"/"scored"/"summary.csv", index=False)
    reification(df).to_csv(ROOT/"data"/"scored"/"reification.csv", index=False)

    lines=[]
    lines.append("== H1 monotonic trend (DN_plausible) ==")
    for dv in ["diagnosis","criteria_invented","emergent_symptom_tokens"]:
        r = trend_test(df,"DN_plausible",dv)
        lines.append(f"  {dv}: {'tau=%.3f p=%.4f'%r if r else 'insufficient data'}")
    lines.append("\n== H2 plausibility gating (slope DN vs incoherent) ==")
    for dv in ["diagnosis","criteria_invented"]:
        lines.append(f"  {dv}: slope_DN={slope(df,'DN_plausible',dv):.4f}  "
                     f"slope_incoherent={slope(df,'incoherent',dv):.4f}")
    lines.append("\n== H3 anchor ceiling (slope real_anchor ~ 0?) ==")
    for dv in ["diagnosis"]:
        lines.append(f"  {dv}: slope_anchor={slope(df,'real_anchor',dv):.4f}")
    lines.append("\n== H4 floor (DN_flagged vs DN_plausible mean diagnosis) ==")
    md = df.groupby("disorder")["diagnosis"].mean()
    if {"DN_flagged","DN_plausible"}.issubset(md.index):
        lines.append(f"  DN_flagged={md['DN_flagged']:.3f}  DN_plausible={md['DN_plausible']:.3f}")
    ok,tot = robustness(df)
    lines.append(f"\n== Robustness (first-order) ==\n  ordering preserved in {ok}/{tot} model slices")
    lines.append("\nNOTE: confirmatory model = mixed-effects logistic/Poisson "
                 "(disorder*level fixed; vignette,model random) via statsmodels — add for paper.")
    (ROOT/"data"/"scored"/"tests.txt").write_text("\n".join(lines))
    print("\n".join(lines))
    print("\nWrote summary.csv, reification.csv, tests.txt")

if __name__ == "__main__":
    main()
