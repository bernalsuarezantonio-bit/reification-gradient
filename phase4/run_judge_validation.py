#!/usr/bin/env python3
"""Phase 4a Paso 2: run the blinded judge over the 1080-item validation sample.

Reads SEALED_mapping.json (blind id -> cell) + the confirmatory responses, and scores each with the
blinded judge (score.judge_response: sees ONLY the aliased seed gloss + aliased response). Output is
SEALED (keyed by blind id) — this driver prints ONLY counts and the malformed/retry rate, never scores.
Incremental, flushed, resumable.

Usage: python phase4/run_judge_validation.py --model ollama_remote/gemma2:27b
"""
import argparse, json, pathlib, sys, time
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from score import judge_response, alias, JudgeParseError

VAL = ROOT / "phase4" / "validation"
OUT = VAL / "SEALED_judge_scores.jsonl"
CONF = ROOT / "resultados_tirada_real" / "responses.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()

    disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
    mapping = json.loads((VAL / "SEALED_mapping.json").read_text())["mapping"]
    # index confirmatory responses by cell
    rows = [json.loads(l) for l in CONF.read_text().splitlines() if l.strip() and '"record"' not in l]
    idx = {(r["model"], r["disorder"], r["level"], r["vignette"], r["rep"]): r for r in rows}

    done = set()
    if OUT.exists():
        for l in OUT.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                if not r.get("error"):
                    done.add(r["id_ciego"])

    hids = sorted(mapping)
    total = len(hids); n = ok = fail = retried = 0
    with OUT.open("a") as f:
        for hid in hids:
            n += 1
            if hid in done:
                continue
            c = mapping[hid]
            row = idx[(c["model"], c["disorder"], c["level"], c["vignette"], c["rep"])]
            name = disorders[c["disorder"]]["name"]
            payload = disorders[c["disorder"]]["payload"]
            t0 = time.time()
            try:
                scores, attempts = judge_response(alias(payload, name), alias(row["response"], name),
                                                  args.model, max_tokens=256)
                rec = {"id_ciego": hid, **scores, "retries": attempts,
                       "latency_s": round(time.time() - t0, 2), "error": None}
                ok += 1; retried += (attempts > 0)
            except JudgeParseError as e:
                rec = {"id_ciego": hid, "error": str(e)[:200],
                       "latency_s": round(time.time() - t0, 2)}
                fail += 1
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            if n % 50 == 0 or fail:
                print(f"[{n}/{total}] ok={ok} malformed_fail={fail} needed_retry={retried}")
    print(f"DONE: {ok} scored, {fail} malformed-fail, {retried} needed>=1 retry (of {total}).")


if __name__ == "__main__":
    main()
