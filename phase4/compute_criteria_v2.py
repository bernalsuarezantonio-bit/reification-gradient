#!/usr/bin/env python3
"""Amendment A3: criteria_invented v2 agreement vs the fixed 48 human ratings.
Hardened criterion: alpha >= 0.80 AND bootstrap 95% CI lower bound > 0.667. Self-contained."""
import json, csv, pathlib
from collections import Counter
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
VAL = ROOT / "phase4" / "validation"
RNG = np.random.default_rng(2026_07_14)


def kripp_interval(pairs):
    d = lambda a, b: (a - b) ** 2
    units = [(a, b) for a, b in pairs]
    n = 2 * len(units)
    if n < 2:
        return float("nan")
    Do = sum(d(a, b) + d(b, a) for a, b in units)
    cnt = Counter(v for u in units for v in u)
    De = sum(cnt[c] * cnt[k] * d(c, k) for c in cnt for k in cnt)
    return 1.0 if De == 0 else 1.0 - (n - 1) * Do / De


def boot_ci(pairs, B=5000):
    idx = np.arange(len(pairs))
    vals = [kripp_interval([pairs[i] for i in RNG.choice(idx, len(idx), replace=True)]) for _ in range(B)]
    vals = [v for v in vals if v == v]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


human = {r["id_ciego"]: r for r in csv.DictReader((VAL / "human_rating_package" / "ratings.csv").open())}
amap = json.loads((VAL / "SEALED_audit_mapping.json").read_text())["mapping"]


def load(path, key="criteria_invented"):
    out = {}
    for l in pathlib.Path(path).read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if not r.get("error"):
                out[r["id_ciego"]] = r[key]
    return out


v2 = load(VAL / "SEALED_judge_crit_v2.jsonl")
v1 = load(VAL / "SEALED_judge_scores.jsonl")

for name, scores in [("v1", v1), ("v2", v2)]:
    pairs = [(int(human[a]["criteria_invented"]), scores[amap[a]["h_id"]])
             for a in sorted(amap) if amap[a]["h_id"] in scores]
    a = kripp_interval(pairs); lo, hi = boot_ci(pairs)
    raw = np.mean([x == y for x, y in pairs]); w1 = np.mean([abs(x - y) <= 1 for x, y in pairs])
    print(f"criteria_invented {name}: alpha={a:.3f} CI95=[{lo:.3f},{hi:.3f}] raw={raw:.1%} (<=+-1:{w1:.1%}) n={len(pairs)}")
    if name == "v2":
        ok = a >= 0.80 and lo > 0.667
        print(f"HARDENED CRITERION (alpha>=0.80 AND CI_low>0.667): {'PASS' if ok else 'FAIL'}")
