#!/usr/bin/env python3
"""Phase 4a amendment A2: directed human audit (n=48) — subsample of the sealed 1080. NO GPU.

Cells: {DN_plausible, incoherent} x {L1_forum, L5_pseudodsm} x {mistral, qwen} x 6 = 48.
Two rated variables only: diagnosis, criteria_invented. Fresh blind ids A01..A48 (new seed).
Regenerates the human package as a single audit batch (gloss attached) + 2-column ratings.csv +
5-item warmup. The prior 1080-lote package is superseded (kept in git history).
"""
import json, csv, pathlib, random, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from score import alias

SEED_AUDIT = 48048       # 6-per-cell pick
SEED_AUDIT_BLIND = 84084 # A-id shuffle
SEED_AUDIT_WARM = 5005
PER_CELL = 6
CONDS = ["DN_plausible", "incoherent"]
LEVELS = ["L1_forum", "L5_pseudodsm"]
MODELS = ["ollama_remote/mistral-small3.1:24b", "ollama_remote/qwen2.5:32b"]

VAL = ROOT / "phase4" / "validation"
PKG = VAL / "human_rating_package"
disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
mapping = json.loads((VAL / "SEALED_mapping.json").read_text())["mapping"]
rows = [json.loads(l) for l in (ROOT / "resultados_tirada_real" / "responses.jsonl").read_text().splitlines()
        if l.strip() and '"record"' not in l]
idx = {(r["model"], r["disorder"], r["level"], r["vignette"], r["rep"]): r for r in rows}

# pick 6 H-ids per audit cell from the sealed 1080
rng = random.Random(SEED_AUDIT)
picked = []
for c in CONDS:
    for l in LEVELS:
        for m in MODELS:
            hids = sorted(h for h, v in mapping.items()
                          if v["disorder"] == c and v["level"] == l and v["model"] == m)
            assert len(hids) == 27, f"cell {(c,l,m)} has {len(hids)}"
            picked.extend(rng.sample(hids, PER_CELL))
assert len(picked) == 48
random.Random(SEED_AUDIT_BLIND).shuffle(picked)

audit_map = {}
for i, h in enumerate(picked, 1):
    aid = f"A{i:02d}"
    audit_map[aid] = {"h_id": h, **mapping[h]}
(VAL / "SEALED_audit_mapping.json").write_text(json.dumps(
    {"_meta": {"seed_audit": SEED_AUDIT, "seed_blind": SEED_AUDIT_BLIND, "per_cell": PER_CELL,
               "n": 48, "cells": "DN_plausible|incoherent x L1|L5 x mistral|qwen",
               "rated_vars": ["diagnosis", "criteria_invented"],
               "note": "SEALED — do not open until human audit ratings are submitted"},
     "mapping": audit_map}, ensure_ascii=False, indent=1))


def row_of(meta):
    return idx[(meta["model"], meta["disorder"], meta["level"], meta["vignette"], meta["rep"])]

def entry(aid, meta):
    r = row_of(meta)
    name = disorders[meta["disorder"]]["name"]
    g = alias(disorders[meta["disorder"]]["payload"], name).strip()
    resp = alias(r["response"], name).strip()
    return (f"\n---\n\n## {aid}\n\n**Glosa de referencia (LA CATEGORÍA):** {g}\n\n"
            f"**Respuesta a puntuar:**\n\n{resp}\n")

# audit batch
lines = ["# AUDITORÍA DIRIGIDA — 48 respuestas (enmienda A2)\n",
         "Puntúa **solo dos variables** por respuesta en `ratings.csv`: `diagnosis` y "
         "`criteria_invented` (ver `GUIA_DE_PUNTUACION.md`). Cada entrada trae su glosa de referencia "
         "exacta. No consultes a nadie ni a ningún modelo.\n"]
for aid in (f"A{i:02d}" for i in range(1, 49)):
    lines.append(entry(aid, audit_map[aid]))
(PKG / "lote_audit.md").write_text("\n".join(lines))

# 2-column ratings.csv
with (PKG / "ratings.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["id_ciego", "diagnosis", "criteria_invented", "nota_incertidumbre"])
    for i in range(1, 49):
        w.writerow([f"A{i:02d}", "", "", ""])

# 5-item warmup from smoke
smoke = [json.loads(l) for l in (ROOT / "resultados_smoke" / "responses.jsonl").read_text().splitlines()
         if l.strip() and '"record"' not in l]
warm = random.Random(SEED_AUDIT_WARM).sample(smoke, 5)
wlines = ["# CALENTAMIENTO — 5 respuestas del smoke (NO cuentan para el α)\n",
          "Practica `diagnosis` y `criteria_invented` aquí antes del lote de auditoría.\n"]
for i, r in enumerate(warm, 1):
    name = disorders[r["disorder"]]["name"]
    g = alias(disorders[r["disorder"]]["payload"], name).strip()
    wlines.append(f"\n---\n\n## W{i}\n\n**Glosa de referencia (LA CATEGORÍA):** {g}\n\n"
                  f"**Respuesta a puntuar:**\n\n{alias(r['response'], name).strip()}\n")
(PKG / "CALENTAMIENTO.md").write_text("\n".join(wlines))
with (PKG / "calentamiento.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["id_ciego", "diagnosis", "criteria_invented", "nota_incertidumbre"])
    for i in range(1, 6):
        w.writerow([f"W{i}", "", "", ""])

print("audit cells:", len(CONDS) * len(LEVELS) * len(MODELS), "x", PER_CELL, "=", len(picked))
print("seeds: audit", SEED_AUDIT, "blind", SEED_AUDIT_BLIND, "warm", SEED_AUDIT_WARM)
print("wrote SEALED_audit_mapping.json, lote_audit.md, ratings.csv (2 vars), CALENTAMIENTO (5)")
