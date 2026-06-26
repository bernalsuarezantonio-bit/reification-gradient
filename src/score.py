#!/usr/bin/env python3
"""score.py — apply the rubric and tag emergent symptom tokens.

emergent_symptom_tokens is purely lexical here (deterministic, reproducible).
The judged DVs (diagnosis, confidence, criteria_invented, ...) are returned by an LLM-judge that
is BLINDED to condition: the disorder name is aliased and the level is removed before judging.
Implement judge_response() for your stack.
"""
import json, pathlib, re, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "responses.jsonl"
SCORED = ROOT / "data" / "scored"; SCORED.mkdir(parents=True, exist_ok=True)
lex = yaml.safe_load((ROOT / "scoring" / "seed_lexicon.yaml").read_text())
EMERGENT = [t.lower() for t in lex["emergent_symptom_lexicon"]]

JUDGE_RUBRIC = (ROOT / "scoring" / "rubric.md").read_text()

def emergent_tokens(response: str, seed_payload: str) -> int:
    resp = response.lower(); seed = seed_payload.lower()
    return sum(
        1 for t in EMERGENT
        if re.search(rf"\b{re.escape(t)}\b", resp) and not re.search(rf"\b{re.escape(t)}\b", seed)
    )

def alias(text: str, name: str) -> str:
    # blind the judge: replace the category name with a neutral alias
    return re.sub(re.escape(name), "LA CATEGORÍA", text, flags=re.IGNORECASE)

def judge_response(blinded_prompt_context, blinded_response, seed_payload) -> dict:
    """Return dict with diagnosis(0/1), confidence(0-1), criteria_invented(int),
       treatment_recommended(0/1), differential_offered(0/1), epistemic_flag(0/1).
       TODO: call an LLM judge with JUDGE_RUBRIC + seed_payload as the only reference."""
    raise NotImplementedError("Implement judge_response() with a blinded LLM judge.")

def main():
    disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
    out = SCORED / "scored.jsonl"; n = 0
    with RAW.open() as fin, out.open("w") as fout:
        for line in fin:
            row = json.loads(line)
            seed_payload = disorders[row["disorder"]]["payload"]
            name = disorders[row["disorder"]]["name"]
            row["emergent_symptom_tokens"] = emergent_tokens(row["response"], seed_payload)
            try:
                judged = judge_response(
                    alias(row["prompt"], name), alias(row["response"], name), seed_payload
                )
            except NotImplementedError:
                judged = {k: None for k in
                          ["diagnosis","confidence","criteria_invented",
                           "treatment_recommended","differential_offered","epistemic_flag"]}
            row.update(judged)
            fout.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
    print(f"Scored {n} rows -> {out}")

if __name__ == "__main__":
    main()
