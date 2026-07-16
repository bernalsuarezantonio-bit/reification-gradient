#!/usr/bin/env python3
"""Stage 6b.4 — confirmatory figures: P(diagnosis) by level x condition, aggregated and by family,
with Wilson 95% CIs on the observed proportions. Figure data also saved as CSV (already written by
analyze_confirmatory.py as fig_data_pdiag.csv)."""
import json, pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "phase6"
LEVELS = ["L1_forum", "L2_coach_blog", "L3_wiki", "L4_preprint", "L5_pseudodsm"]
SHORT = ["L1", "L2", "L3", "L4", "L5"]
CONDS = ["DN_plausible", "real_anchor", "incoherent", "DN_flagged"]
COL = {"DN_plausible": "#c1121f", "real_anchor": "#003049", "incoherent": "#7f8c8d", "DN_flagged": "#f77f00"}

rows = [json.loads(l) for l in (OUT / "scored_full.jsonl").read_text().splitlines() if l.strip()]
df = pd.DataFrame([r for r in rows if not r.get("error")])
df["level_num"] = df["level"].map({l: i + 1 for i, l in enumerate(LEVELS)})
df["family"] = df["model"].str.split("/").str[-1]
df["diagnosis"] = df["diagnosis"].astype(int)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return (max(0, c - h), min(1, c + h))


def panel(ax, data, title):
    for d in CONDS:
        ys, los, his = [], [], []
        for i in range(1, 6):
            s = data[(data.disorder == d) & (data.level_num == i)]["diagnosis"]
            k, n = int(s.sum()), len(s); p = k / n if n else np.nan
            lo, hi = wilson(k, n)
            ys.append(p); los.append(lo); his.append(hi)
        ax.errorbar(range(1, 6), ys, yerr=[np.array(ys) - np.array(los), np.array(his) - np.array(ys)],
                    marker="o", capsize=3, label=d, color=COL[d], lw=2)
    ax.set_xticks(range(1, 6)); ax.set_xticklabels(SHORT)
    ax.set_ylim(-0.03, 1.03); ax.set_xlabel("Nivel de legitimidad"); ax.set_title(title)
    ax.grid(alpha=.3)


fams = sorted(df.family.unique())
fig, axes = plt.subplots(1, 1 + len(fams), figsize=(6 * (1 + len(fams)), 4.6), sharey=True)
panel(axes[0], df, "Agregado (ambas familias)")
axes[0].set_ylabel("P(diagnosis = 1)  [IC95 Wilson]")
for ax, fam in zip(axes[1:], fams):
    panel(ax, df[df.family == fam], fam)
axes[-1].legend(loc="center right", fontsize=9)
fig.suptitle("Confirmatorio — P(diagnosis) por nivel x condición (DV validada: diagnosis)", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "fig_pdiag_by_level.png", dpi=150, bbox_inches="tight")

# figure data with Wilson CIs (superset of fig_data_pdiag.csv)
recs = []
for scope, data in [("aggregate", df)] + [(f, df[df.family == f]) for f in fams]:
    for d in CONDS:
        for i, l in enumerate(LEVELS, start=1):
            s = data[(data.disorder == d) & (data.level_num == i)]["diagnosis"]
            k, n = int(s.sum()), len(s); lo, hi = wilson(k, n)
            recs.append({"scope": scope, "disorder": d, "level": l, "level_num": i,
                         "n": n, "k_diagnosis1": k, "p": k / n if n else np.nan,
                         "ci95_lo": lo, "ci95_hi": hi})
pd.DataFrame(recs).to_csv(OUT / "fig_data_pdiag_ci.csv", index=False)
print("wrote fig_pdiag_by_level.png + fig_data_pdiag_ci.csv")
