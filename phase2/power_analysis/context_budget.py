#!/usr/bin/env python3
"""Part B: exact input-token budget for the 20 stimuli (cond x level) with the longest vignette,
tokenized by EACH model via Ollama prompt_eval_count. Light GPU (num_predict=1)."""
import sys, pathlib, csv
sys.path.insert(0, "/Users/admin/Downloads/reification-gradient/src")
from providers import _http_post_json, load_env
import os, run_experiment as R

load_env()
BASE = os.environ["OLLAMA_BASE_URL"].rstrip("/")
MODELS = ["mistral-small3.1:24b", "qwen2.5:32b"]
OUT = pathlib.Path("/Users/admin/Downloads/reification-gradient/phase2/power_analysis")

disorders, vignettes, levels = R.load()
longest = max(vignettes, key=lambda v: len(" ".join(v["text"].split())))
print(f"viñeta más larga: {longest['id']} ({len(longest['text'].split())} palabras)")
print(f"condiciones: {list(disorders)} | niveles: {list(levels)}")

# build 20 stimuli
stimuli = {}
for dkey, d in disorders.items():
    for lkey, ltext in levels.items():
        seeded = R.wrap(ltext, d["name"], d["payload"], d.get("disclosure", ""))
        stimuli[(dkey, lkey)] = R.build_prompt(seeded, longest["text"])

def input_tokens(model, prompt):
    data = _http_post_json(BASE + "/api/chat",
        {"model": model, "messages": [{"role": "user", "content": prompt}],
         "stream": False, "options": {"num_ctx": 4096, "num_predict": 1}},
        {}, timeout=120, max_retries=2)
    return data.get("prompt_eval_count")

rows = []
for model in MODELS:
    print(f"\n== {model} == (tokens de entrada por condición x nivel)")
    print(f"{'cond':<14}" + "".join(f"{l:<7}" for l in levels))
    for dkey in disorders:
        cells = []
        for lkey in levels:
            n = input_tokens(model, stimuli[(dkey, lkey)])
            cells.append(n)
            rows.append(dict(model=model, cond=dkey, level=lkey, input_tokens=n))
        print(f"{dkey:<14}" + "".join(f"{c:<7}" for c in cells))

with (OUT / "context_budget.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["model", "cond", "level", "input_tokens"]); w.writeheader(); w.writerows(rows)

mx = max(rows, key=lambda r: r["input_tokens"])
gmax = mx["input_tokens"]
print(f"\nMÁXIMO GLOBAL de entrada: {gmax} tok  ({mx['model']}, {mx['cond']} x {mx['level']})")
NUM_PREDICT = 512
need = gmax + NUM_PREDICT
need_margin = int(need * 1.15)
pow2 = 1
while pow2 < need_margin:
    pow2 *= 2
print(f"máx_entrada={gmax} + num_predict={NUM_PREDICT} = {need}; +15% margen = {need_margin}")
print(f"num_ctx propuesto (mín. potencia de 2 >= {need_margin}) = {pow2}")
(OUT / "num_ctx_proposal.txt").write_text(
    f"longest_vignette={longest['id']}\nmax_input_tokens={gmax} ({mx['model']} {mx['cond']} {mx['level']})\n"
    f"num_predict={NUM_PREDICT}\nneed+15%={need_margin}\nproposed_num_ctx={pow2}\n")
