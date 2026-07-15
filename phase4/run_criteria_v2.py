#!/usr/bin/env python3
"""Amendment A3: re-judge ONLY criteria_invented on the 1080 with v2. SEALED output. Resumable.
Prints counts only (no scores)."""
import argparse, json, pathlib, sys, time
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from score import judge_criteria_v2, alias, JudgeParseError

VAL = ROOT / "phase4" / "validation"
OUT = VAL / "SEALED_judge_crit_v2.jsonl"
CONF = ROOT / "resultados_tirada_real" / "responses.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ollama_remote/gemma2:27b")
    args = ap.parse_args()
    disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
    mapping = json.loads((VAL / "SEALED_mapping.json").read_text())["mapping"]
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
    n = ok = fail = 0
    with OUT.open("a") as f:
        for hid in hids:
            n += 1
            if hid in done:
                continue
            c = mapping[hid]
            row = idx[(c["model"], c["disorder"], c["level"], c["vignette"], c["rep"])]
            name = disorders[c["disorder"]]["name"]; payload = disorders[c["disorder"]]["payload"]
            t0 = time.time()
            try:
                cnt, att = judge_criteria_v2(alias(payload, name), alias(row["response"], name), args.model)
                rec = {"id_ciego": hid, "criteria_invented": cnt, "retries": att,
                       "latency_s": round(time.time() - t0, 2), "error": None}; ok += 1
            except JudgeParseError as e:
                rec = {"id_ciego": hid, "error": str(e)[:150]}; fail += 1
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            if n % 100 == 0 or fail:
                print(f"[{n}/{len(hids)}] ok={ok} fail={fail}")
    print(f"DONE: {ok} scored, {fail} malformed (of {len(hids)}).")


if __name__ == "__main__":
    main()
