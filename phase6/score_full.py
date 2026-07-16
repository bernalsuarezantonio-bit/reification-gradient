#!/usr/bin/env python3
"""Stage 6a: complete the judge scoring to all 7200 responses (v1 judge_prompt, 6 vars).

Reuses the 1080 already scored in Phase 4a (joined via SEALED_mapping.json) and scores the
remaining ~6120 with the same judge (gemma2:27b) and the same sealed judge_prompt.md v1.
Blinding identical: aliased seed gloss + aliased response only. Resumable; counts only.
Output: phase6/scored_full.jsonl (one row per response, cell-keyed).
"""
import argparse, json, pathlib, sys, time
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from score import judge_response, alias, emergent_tokens, JudgeParseError, JUDGE_KEYS

OUT = ROOT / "phase6" / "scored_full.jsonl"
CONF = ROOT / "resultados_tirada_real" / "responses.jsonl"
VAL = ROOT / "phase4" / "validation"


def cellkey(r):
    return (r["model"], r["disorder"], r["level"], r["vignette"], r["rep"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ollama_remote/gemma2:27b")
    args = ap.parse_args()
    disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
    rows = [json.loads(l) for l in CONF.read_text().splitlines() if l.strip() and '"record"' not in l]

    # reuse Phase-4a scores for the 1080 sample
    mapping = json.loads((VAL / "SEALED_mapping.json").read_text())["mapping"]
    prior = {}
    for l in (VAL / "SEALED_judge_scores.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            if not r.get("error"):
                c = mapping[r["id_ciego"]]
                prior[(c["model"], c["disorder"], c["level"], c["vignette"], c["rep"])] = r

    done = set()
    if OUT.exists():
        for l in OUT.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                if not r.get("error"):
                    done.add(tuple(r["cell"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = reused = scored = fail = 0
    with OUT.open("a") as f:
        for r in rows:
            n += 1
            k = cellkey(r)
            if k in done:
                continue
            d = disorders[r["disorder"]]
            payload, name = d["payload"], d["name"]
            rec = {"cell": list(k), "model": r["model"], "disorder": r["disorder"],
                   "disorder_type": r["disorder_type"], "level": r["level"],
                   "vignette": r["vignette"], "target_compatibility": r["target_compatibility"],
                   "rep": r["rep"],
                   "emergent_symptom_tokens": emergent_tokens(r["response"], payload)}
            if k in prior:                       # reuse Phase-4a judge score (same judge, same prompt)
                p = prior[k]
                rec.update({v: p[v] for v in JUDGE_KEYS})
                rec.update({"source": "phase4a_sample", "error": None}); reused += 1
            else:
                try:
                    s, att = judge_response(alias(payload, name), alias(r["response"], name), args.model)
                    rec.update(s); rec.update({"source": "phase6", "retries": att, "error": None})
                    scored += 1
                except JudgeParseError as e:
                    rec.update({"source": "phase6", "error": str(e)[:150]}); fail += 1
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            if n % 250 == 0 or fail:
                print(f"[{n}/{len(rows)}] reused={reused} scored={scored} fail={fail}")
    print(f"DONE: {reused} reused, {scored} newly scored, {fail} malformed (of {len(rows)}).")


if __name__ == "__main__":
    main()
