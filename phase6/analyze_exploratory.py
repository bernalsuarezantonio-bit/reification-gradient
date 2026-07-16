#!/usr/bin/env python3
"""Stage 6c — EXPLORATORY analyses (separate from confirmatory; descriptive only, no inference).
Outputs phase6/exploratory_results.json + phase6/verbatims.md
"""
import json, pathlib, random, re
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "phase6"
VAL = ROOT / "phase4" / "validation"
LEVELS = ["L1_forum", "L2_coach_blog", "L3_wiki", "L4_preprint", "L5_pseudodsm"]
SEED = 20260716

rows = [json.loads(l) for l in (OUT / "scored_full.jsonl").read_text().splitlines() if l.strip()]
df = pd.DataFrame([r for r in rows if not r.get("error")])
df["family"] = df["model"].str.split("/").str[-1]
res = {}

# --- 6c.1 human criteria_invented (n=48), critical cells, DESCRIPTIVE ONLY ---
human = {r["id_ciego"]: r for r in
         __import__("csv").DictReader((VAL / "human_rating_package" / "ratings.csv").open())}
amap = json.loads((VAL / "SEALED_audit_mapping.json").read_text())["mapping"]
hr = []
for aid, m in amap.items():
    hr.append({"disorder": m["disorder"], "level": m["level"],
               "family": m["model"].split("/")[-1],
               "criteria_invented_human": int(human[aid]["criteria_invented"]),
               "diagnosis_human": int(human[aid]["diagnosis"])})
hdf = pd.DataFrame(hr)
g = hdf.groupby(["disorder", "level"])["criteria_invented_human"]
res["human_criteria_n48"] = {
    "note": "CONFIRMATORY-GRADE measure for criteria_invented per A4 (n=48, critical cells). "
            "Descriptive only: no inferential test (n per cell = 12).",
    "by_cell": [{"disorder": k[0], "level": k[1], "n": int(v.count()),
                 "mean": float(v.mean()), "min": int(v.min()), "max": int(v.max()),
                 "pct_zero": float((v == 0).mean())} for k, v in g],
    "by_cell_family": [{"disorder": a, "level": b, "family": c, "n": int(v.count()),
                        "mean": float(v.mean()), "min": int(v.min()), "max": int(v.max())}
                       for (a, b, c), v in hdf.groupby(["disorder", "level", "family"])["criteria_invented_human"]],
}

# --- 6c.2 judge v1 criteria_invented over 7200 — NON-RELIABLE (alpha -0.28 / -0.37) ---
g2 = df.groupby(["disorder", "level"])["criteria_invented"]
res["judge_criteria_v1_full"] = {
    "WARNING": "NON-RELIABLE MEASURE. Human-vs-judge Krippendorff alpha = -0.276 (v1) / -0.370 (v2). "
               "Exploratory/descriptive only per A4; not interpretable as a reification count.",
    "by_cell": [{"disorder": k[0], "level": k[1], "n": int(v.count()), "mean": float(v.mean()),
                 "sd": float(v.std()), "min": int(v.min()), "max": int(v.max())} for k, v in g2],
    "by_family": [{"family": k, "mean": float(v.mean())} for k, v in df.groupby("family")["criteria_invented"]],
}

# --- 6c.3 other DVs, descriptive, with reliability status declared ---
STATUS = {"confidence": "judge-vs-co-rater alpha = -0.188 (raw 50.8%) — NOT reliable",
          "treatment_recommended": "judge-vs-co-rater alpha = 0.350 (raw 73.8%) — low alpha, high raw "
                                   "(prevalence-imbalance paradox)",
          "differential_offered": "judge-vs-co-rater alpha = 0.717 (raw 99.4%) — borderline alpha, high raw",
          "epistemic_flag": "judge-vs-co-rater alpha = 0.547 (raw 84.2%) — low alpha, high raw",
          "emergent_symptom_tokens": "lexical, deterministic (not judge-scored); no inter-rater alpha"}
other = {}
for dv in ["confidence", "treatment_recommended", "differential_offered", "epistemic_flag",
           "emergent_symptom_tokens"]:
    other[dv] = {"reliability_status": STATUS[dv],
                 "by_cell": [{"disorder": k[0], "level": k[1], "mean": float(v.mean()), "n": int(v.count())}
                             for k, v in df.groupby(["disorder", "level"])[dv]],
                 "by_family": [{"family": k, "mean": float(v.mean())} for k, v in df.groupby("family")[dv]]}
res["other_dvs"] = other

# --- 6c.5 family differences (descriptive) ---
res["family_differences"] = {
    "diagnosis_by_family_condition": [
        {"family": a, "disorder": b, "mean_diagnosis": float(v.mean()), "n": int(v.count())}
        for (a, b), v in df.groupby(["family", "disorder"])["diagnosis"]],
}

# --- 6c.4 verbatim extraction: non-derivable fabrication in DN_plausible & diagnosis==1 ---
conf = [json.loads(l) for l in (ROOT / "resultados_tirada_real" / "responses.jsonl").read_text().splitlines()
        if l.strip() and '"record"' not in l]
idx = {(r["model"], r["disorder"], r["level"], r["vignette"], r["rep"]): r["response"] for r in conf}
PATTERNS = {
    "a_prevalencia_epidemiologia": re.compile(r"(prevalenc\w+|epidemiolog\w+|afecta\w*\s+(a|al)\s+[\d.,]+\s*%|"
                                              r"[\d.,]+\s*%\s+de\s+la\s+poblaci|incidencia)", re.I),
    "b_criterios_numerados": re.compile(r"(criterio\s*[A-E1-9]|^\s*\d\.\s+\*\*|criterios\s+diagn[oó]stic)", re.I | re.M),
    "c_protocolo_tratamiento": re.compile(r"(protocolo|sesiones\s+de|terapia\s+cognitivo|ISRS|"
                                          r"tratamiento\s+de\s+primera\s+l[ií]nea|plan\s+de\s+tratamiento)", re.I),
    "d_comorbilidades": re.compile(r"(comorbilidad\w*|com[oó]rbid\w+|frecuentemente\s+asociad\w+\s+(a|con))", re.I),
}
cand = df[(df.disorder == "DN_plausible") & (df.diagnosis == 1)]
hits = []
for _, r in cand.iterrows():
    txt = idx[tuple(r["cell"])]
    for label, rx in PATTERNS.items():
        m = rx.search(txt)
        if m:
            s = max(0, m.start() - 120); e = min(len(txt), m.end() + 220)
            hits.append({"kind": label, "cell_id": f"{r['disorder']}-{r['level']}-{r['vignette']}-r{r['rep']}-{r['family']}",
                         "quote": txt[s:e].strip().replace("\n", " ")})
rng = random.Random(SEED)
picked = []
for label in PATTERNS:
    sub = [h for h in hits if h["kind"] == label]
    picked += rng.sample(sub, min(4, len(sub)))
picked = picked[:15]
res["verbatims_meta"] = {"seed": SEED, "candidates_DN_diagnosis1": int(len(cand)),
                         "hits_by_kind": {k: int(sum(1 for h in hits if h["kind"] == k)) for k in PATTERNS},
                         "n_reported": len(picked),
                         "note": "ILLUSTRATIVE examples only; pattern-matched, not a validated count."}
with (OUT / "verbatims.md").open("w") as f:
    f.write("# Verbatims ilustrativos — fabricación no-derivable (DN_plausible, diagnosis=1)\n\n")
    f.write(f"Extracción por patrones (semilla {SEED}). **Ilustrativos, NO un recuento validado.**\n")
    f.write(f"Candidatas (DN_plausible & diagnosis=1): {len(cand)}. "
            f"Coincidencias por tipo: {res['verbatims_meta']['hits_by_kind']}\n\n")
    for h in picked:
        f.write(f"### [{h['kind']}] `{h['cell_id']}`\n\n> …{h['quote']}…\n\n")
(OUT / "exploratory_results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("wrote exploratory_results.json + verbatims.md | verbatims:", len(picked))
