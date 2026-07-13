#!/usr/bin/env python3
"""run_batch.py — config-driven, resumable run harness for smoke (R1) and confirmatory (R2).

Reads a YAML config, assembles prompts from the FROZEN materials, and calls the models with the
SEALED generation params. Refuses to run confirmatory configs unless the prereg-v1 tag exists.

Guarantees:
- Sequential per family (models run in listed order; one cold load each).
- Randomized cell order within each family, fixed seed (recorded in the end record).
- Incremental, flushed, RESUMABLE save (re-running skips completed cells; never duplicates).
- Failures go to <output_dir>/_fallos.log AND a row with an "error" field (never silently dropped).
- Ends with a well-formed {"record":"end",...} line when all cells are done.
- Progress is COUNTS ONLY; this script never prints response content.

Usage: python src/run_batch.py --config config_smoke.yaml
"""
import argparse, json, pathlib, subprocess, sys, random, time, datetime as dt
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import run_experiment as R
from providers import query_model, ProviderError


def gate():
    r = subprocess.run([sys.executable, str(ROOT / "src" / "check_invariants.py")],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit("Invariants failed; aborting run.\n" + r.stdout.decode() + r.stderr.decode())


def require_prereg_tag():
    r = subprocess.run(["git", "-C", str(ROOT), "tag", "-l", "prereg-v1"], capture_output=True, text=True)
    if "prereg-v1" not in r.stdout.split():
        sys.exit("HARD STOP: confirmatory run requires tag prereg-v1, which is absent.")
    h = subprocess.run(["git", "-C", str(ROOT), "rev-list", "-n1", "prereg-v1"],
                       capture_output=True, text=True).stdout.strip()
    plan = subprocess.run(["git", "-C", str(ROOT), "show", "prereg-v1:PLAN.md"],
                          capture_output=True, text=True).stdout
    if "DPDR" not in plan or not any(k in plan for k in ("R = 3", "R=3", "3 repetitions")):
        sys.exit("HARD STOP: tagged PLAN.md missing anchor/R; not a valid freeze.")
    return h


def load_cells(cfg):
    disorders, vignettes, levels = R.load()
    vby = {v["id"]: v for v in vignettes}
    conds = cfg["conditions"]; levs = cfg["levels"]; vigs = cfg["vignettes"]; reps = cfg["reps"]
    for c in conds:
        if c not in disorders: sys.exit(f"unknown condition {c}")
    for l in levs:
        if l not in levels: sys.exit(f"unknown level {l}")
    for v in vigs:
        if v not in vby: sys.exit(f"unknown vignette {v}")
    base = [(c, l, v, rep) for c in conds for l in levs for v in vigs for rep in range(reps)]
    random.Random(cfg["seed"]).shuffle(base)     # fixed-seed cell order (applied under each family)
    return disorders, levels, vby, base


def done_keys(path):
    seen = set(); ended = False
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("record") == "end":
                ended = True; continue
            if not r.get("error"):
                seen.add((r["model"], r["disorder"], r["level"], r["vignette"], r["rep"]))
    return seen, ended


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    gate()
    if cfg.get("confirmatory"):
        h = require_prereg_tag()
        print(f"prereg-v1 verified @ {h[:12]}")

    disorders, levels, vby, base = load_cells(cfg)
    gen = cfg["generation"]
    outdir = ROOT / cfg["output_dir"]; outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "responses.jsonl"; fallos = outdir / "_fallos.log"
    seen, ended = done_keys(out)
    if ended:
        print(f"run already complete ({len(seen)} cells); nothing to do."); return

    models = cfg["models"]
    total = len(models) * len(base)
    n = done = fail = 0
    with out.open("a") as f:
        for model in models:                      # sequential per family
            for (c, l, v, rep) in base:           # fixed randomized order within family
                n += 1
                key = (model, c, l, v, rep)
                if key in seen:
                    continue
                d = disorders[c]
                seeded = R.wrap(levels[l], d["name"], d["payload"], d.get("disclosure", ""))
                prompt = R.build_prompt(seeded, vby[v]["text"])
                t0 = time.time()
                try:
                    resp = query_model(model, prompt, gen["temperature"],
                                       num_ctx=gen["num_ctx"], max_tokens=gen["num_predict"])
                    err = None
                except ProviderError as e:
                    resp, err = "", str(e)
                row = {"model": model, "disorder": c, "disorder_type": d["type"], "level": l,
                       "vignette": v, "target_compatibility": vby[v]["target_compatibility"],
                       "rep": rep, "prompt": prompt, "response": resp,
                       "latency_s": round(time.time() - t0, 2), "error": err,
                       "ts": dt.datetime.now().isoformat(timespec="seconds")}
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                if err:
                    fail += 1
                    with fallos.open("a") as ff:
                        ff.write(f"{row['ts']}\t{model}\t{c}\t{l}\t{v}\tr{rep}\t{err[:200]}\n")
                    print(f"[{n}/{total}] FAIL {model.split('/')[-1]} {c}/{l}/{v}/r{rep}")
                else:
                    done += 1
                    print(f"[{n}/{total}] ok {model.split('/')[-1]} {c}/{l}/{v}/r{rep} ({row['latency_s']}s)")
        f.write(json.dumps({"record": "end", "config": cfg.get("name"),
                            "confirmatory": bool(cfg.get("confirmatory")),
                            "models": models, "seed": cfg["seed"], "generation": gen,
                            "expected_cells": total,
                            "ts": dt.datetime.now().isoformat(timespec="seconds")},
                           ensure_ascii=False) + "\n")
    print(f"DONE this pass: {done} ok, {fail} fail (expected total {total}).")


if __name__ == "__main__":
    main()
