#!/usr/bin/env python3
"""Phase 4a: inter-rater agreement. Opens the SEALED files (post human-ratings submission).

- Human vs judge on the 48-item directed audit: diagnosis (nominal), criteria_invented (interval).
- Judge vs co-rater on the 1080: all six variables.
Reports Krippendorff's alpha + bootstrap 95% CI + raw agreement, vs prefixed thresholds.
"""
import json, csv, pathlib, sys
from collections import Counter
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
VAL = ROOT / "phase4" / "validation"
RNG = np.random.default_rng(2026_07_14)


def kripp_alpha(pairs, metric):
    """pairs: list of (a,b) complete. metric: 'nominal' or 'interval'. Krippendorff's alpha."""
    d = (lambda a, b: 0.0 if a == b else 1.0) if metric == "nominal" else (lambda a, b: (a - b) ** 2)
    units = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = 2 * len(units)
    if n < 2:
        return float("nan")
    Do = sum(d(a, b) + d(b, a) for a, b in units)              # ordered i!=j, 1/(m-1)=1 for m=2
    counts = Counter(v for u in units for v in u)
    vals = list(counts)
    De = sum(counts[c] * counts[k] * d(c, k) for c in vals for k in vals)
    if De == 0:
        return 1.0
    return 1.0 - (n - 1) * Do / De


def boot_ci(pairs, metric, B=5000):
    idx = np.arange(len(pairs))
    vals = []
    for _ in range(B):
        s = RNG.choice(idx, size=len(idx), replace=True)
        a = kripp_alpha([pairs[i] for i in s], metric)
        if a == a:  # not nan
            vals.append(a)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"),) * 2


def verdict(a):
    return "ÉXITO (>=.80)" if a >= 0.80 else ("AJUSTAR+REPETIR (.667-.80)" if a >= 0.667 else "REDISEÑO (<.667)")


def load_scores(path):
    out = {}
    for l in path.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if not r.get("error"):
                out[r["id_ciego"]] = r
    return out


# ---- human vs judge on the 48 ----
human = {r["id_ciego"]: r for r in csv.DictReader((VAL / "human_rating_package" / "ratings.csv").open())}
amap = json.loads((VAL / "SEALED_audit_mapping.json").read_text())["mapping"]
judge = load_scores(VAL / "SEALED_judge_scores.jsonl")

diag_pairs, crit_pairs = [], []
missing = []
for aid in sorted(amap):
    h = human.get(aid); hid = amap[aid]["h_id"]; j = judge.get(hid)
    if h is None or j is None:
        missing.append(aid); continue
    diag_pairs.append((int(h["diagnosis"]), int(j["diagnosis"])))
    crit_pairs.append((int(h["criteria_invented"]), int(j["criteria_invented"])))

print(f"=== HUMANO vs JUEZ (auditoría n={len(diag_pairs)}, faltantes={len(missing)}) ===")
for name, pairs, metric in [("diagnosis", diag_pairs, "nominal"),
                            ("criteria_invented", crit_pairs, "interval")]:
    a = kripp_alpha(pairs, metric); lo, hi = boot_ci(pairs, metric)
    raw = np.mean([x == y for x, y in pairs])
    line = f"  {name:<18} alpha={a:.3f}  IC95=[{lo:.3f},{hi:.3f}]  acuerdo_crudo={raw:.1%}  -> {verdict(a)}"
    if name == "criteria_invented":
        w1 = np.mean([abs(x - y) <= 1 for x, y in pairs])
        line += f"  (dentro_de_1={w1:.1%})"
    print(line)

# ---- judge vs co-rater on the 1080 ----
cor = load_scores(VAL / "SEALED_corater_scores.jsonl")
common = sorted(set(judge) & set(cor))
print(f"\n=== JUEZ vs CO-RATER (n={len(common)} de 1080) ===")
BIN = ["diagnosis", "treatment_recommended", "differential_offered", "epistemic_flag"]
for var in ["diagnosis", "confidence", "criteria_invented", "treatment_recommended",
            "differential_offered", "epistemic_flag"]:
    metric = "interval" if var in ("confidence", "criteria_invented") else "nominal"
    pairs = [(judge[h][var], cor[h][var]) for h in common]
    a = kripp_alpha(pairs, metric)
    raw = np.mean([x == y for x, y in pairs])
    print(f"  {var:<22} alpha={a:.3f}  acuerdo_crudo={raw:.1%}  -> {verdict(a)}")
