#!/usr/bin/env python3
"""Phase 4a: stratified 15% sample + sealed mapping + blind human-rating package. NO GPU.

Strata = condition x level x family (4x5x2 = 40), 27 per stratum (15% of 180) = 1080.
Within stratum: uniform over vignette x rep (SEED_SAMPLE). Blind ids H0001..H1080 assigned in a
NEW random order (SEED_BLIND) so id order does not correlate with cell. Responses shown to the
human are name-aliased ('LA CATEGORIA') exactly as the judge sees them (parallel input).
"""
import json, csv, pathlib, random, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from score import alias

SEED_SAMPLE = 40040      # stratified pick
SEED_BLIND = 80080       # blind-id shuffle
SEED_WARM = 12012        # warmup pick from smoke
PER_STRATUM = 27
BATCH = 90

CONF = ROOT / "resultados_tirada_real" / "responses.jsonl"
SMOKE = ROOT / "resultados_smoke" / "responses.jsonl"
OUT = ROOT / "phase4" / "validation"
PKG = OUT / "human_rating_package"
PKG.mkdir(parents=True, exist_ok=True)

disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
CONDS = ["DN_plausible", "real_anchor", "incoherent", "DN_flagged"]
LEVELS = ["L1_forum", "L2_coach_blog", "L3_wiki", "L4_preprint", "L5_pseudodsm"]
MODELS = ["ollama_remote/mistral-small3.1:24b", "ollama_remote/qwen2.5:32b"]


def load(path):
    return [json.loads(l) for l in path.read_text().splitlines()
            if l.strip() and '"record"' not in l]

rows = load(CONF)
by = {}
for r in rows:
    by.setdefault((r["disorder"], r["level"], r["model"]), []).append(r)

rng_s = random.Random(SEED_SAMPLE)
sampled = []
strata_counts = {}
for c in CONDS:
    for l in LEVELS:
        for m in MODELS:
            st = sorted(by[(c, l, m)], key=lambda r: (int(r["vignette"][1:]), r["rep"]))
            assert len(st) == 180, f"stratum {(c,l,m)} has {len(st)}"
            picks = rng_s.sample(st, PER_STRATUM)
            sampled.extend(picks)
            strata_counts[(c, l, m)] = len(picks)

# blind-id assignment in a fresh random order
order = sampled[:]
random.Random(SEED_BLIND).shuffle(order)
mapping = {}
for i, r in enumerate(order, 1):
    hid = f"H{i:04d}"
    mapping[hid] = {"model": r["model"], "disorder": r["disorder"],
                    "disorder_type": r["disorder_type"], "level": r["level"],
                    "vignette": r["vignette"], "rep": r["rep"],
                    "target_compatibility": r["target_compatibility"]}

(OUT / "SEALED_mapping.json").write_text(json.dumps(
    {"_meta": {"seed_sample": SEED_SAMPLE, "seed_blind": SEED_BLIND,
               "per_stratum": PER_STRATUM, "n": len(order),
               "note": "SEALED — do not open until human ratings are submitted"},
     "mapping": mapping}, ensure_ascii=False, indent=1))

# blind batches (id + aliased response only)
def aliased(r):
    return alias(r["response"], disorders[r["disorder"]]["name"]).strip()

for b in range((len(order) + BATCH - 1) // BATCH):
    chunk = order[b * BATCH:(b + 1) * BATCH]
    lines = [f"# Lote {b+1:02d} — respuestas H{b*BATCH+1:04d}–H{b*BATCH+len(chunk):04d}\n",
             "Puntúa cada respuesta en `ratings.csv` usando `GUIA_DE_PUNTUACION.md`. "
             "No consultes a nadie ni a ningún modelo.\n"]
    for i, r in enumerate(chunk):
        hid = f"H{b*BATCH+i+1:04d}"
        lines.append(f"\n---\n\n## {hid}\n\n{aliased(r)}\n")
    (PKG / f"lote_{b+1:02d}.md").write_text("\n".join(lines))

# empty ratings.csv (one row per blind id, in batch order)
JUDGE_KEYS = ["diagnosis", "confidence", "criteria_invented",
              "treatment_recommended", "differential_offered", "epistemic_flag"]
with (PKG / "ratings.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["id_ciego"] + JUDGE_KEYS + ["nota_incertidumbre"])
    for i in range(len(order)):
        w.writerow([f"H{i+1:04d}"] + [""] * (len(JUDGE_KEYS) + 1))

# warmup from smoke (non-confirmatory; not in alpha)
smoke = load(SMOKE)
warm = random.Random(SEED_WARM).sample(smoke, 20)
wlines = ["# CALENTAMIENTO — 20 respuestas del smoke (NO cuentan para el α)\n",
          "Practica la rúbrica aquí antes del Lote 1. Registra en `calentamiento.csv`. "
          "Estas respuestas son del test técnico, no de la tirada confirmatoria.\n"]
for i, r in enumerate(warm, 1):
    wlines.append(f"\n---\n\n## W{i:02d}\n\n{aliased(r)}\n")
(PKG / "CALENTAMIENTO.md").write_text("\n".join(wlines))
with (PKG / "calentamiento.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["id_ciego"] + JUDGE_KEYS + ["nota_incertidumbre"])
    for i in range(1, 21):
        w.writerow([f"W{i:02d}"] + [""] * (len(JUDGE_KEYS) + 1))

# report (counts + seeds only; NO content)
print("strata:", len(strata_counts), "| per stratum:", sorted(set(strata_counts.values())))
print("sampled:", len(order), "| batches:", (len(order) + BATCH - 1) // BATCH, "of", BATCH)
print("seeds: sample", SEED_SAMPLE, "blind", SEED_BLIND, "warm", SEED_WARM)
print("warmup:", len(warm), "from smoke")
print("wrote:", OUT / "SEALED_mapping.json", "and", PKG)
