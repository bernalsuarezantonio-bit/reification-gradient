#!/usr/bin/env python3
"""score.py — apply the rubric and tag emergent symptom tokens.

emergent_symptom_tokens is purely lexical here (deterministic, reproducible).
The judged DVs (diagnosis, confidence, criteria_invented, ...) are returned by an LLM-judge that
is BLINDED to condition: the disorder name is aliased and the level is removed before judging.
Implement judge_response() for your stack.
"""
import json, os, pathlib, re, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
RAW = ROOT / "data" / "raw" / "responses.jsonl"
SCORED = ROOT / "data" / "scored"; SCORED.mkdir(parents=True, exist_ok=True)
lex = yaml.safe_load((ROOT / "scoring" / "seed_lexicon.yaml").read_text())
EMERGENT = [t.lower() for t in lex["emergent_symptom_lexicon"]]

JUDGE_RUBRIC = (ROOT / "scoring" / "rubric.md").read_text()
JUDGE_KEYS = ["diagnosis", "confidence", "criteria_invented",
              "treatment_recommended", "differential_offered", "epistemic_flag"]


def _judge_template() -> str:
    """Extract the sealed prompt template (the fenced block with {{SEED_PAYLOAD}}) from
    scoring/judge_prompt.md. The prompt is used AS-IS (sealed); we only fill placeholders."""
    md = (ROOT / "scoring" / "judge_prompt.md").read_text()
    blocks = re.findall(r"```([\s\S]*?)```", md)
    for b in blocks:
        if "{{SEED_PAYLOAD}}" in b and "{{RESPONSE}}" in b:
            return b.strip("\n")
    raise RuntimeError("judge template with {{SEED_PAYLOAD}}/{{RESPONSE}} not found in judge_prompt.md")


JUDGE_TEMPLATE = _judge_template()


def emergent_tokens(response: str, seed_payload: str) -> int:
    resp = response.lower(); seed = seed_payload.lower()
    return sum(
        1 for t in EMERGENT
        if re.search(rf"\b{re.escape(t)}\b", resp) and not re.search(rf"\b{re.escape(t)}\b", seed)
    )

def alias(text: str, name: str) -> str:
    # blind the judge: replace the category name with a neutral alias
    return re.sub(re.escape(name), "LA CATEGORÍA", text, flags=re.IGNORECASE)


class JudgeParseError(ValueError):
    pass


def _criteria_v2_template() -> str:
    md = (ROOT / "scoring" / "judge_prompt_criteria_v2.md").read_text()
    for b in re.findall(r"```([\s\S]*?)```", md):
        if "{{SEED_PAYLOAD}}" in b and "{{RESPONSE}}" in b:
            return b.strip("\n")
    raise RuntimeError("criteria v2 template not found")


CRITERIA_V2_TEMPLATE = _criteria_v2_template()


def judge_criteria_v2(seed_payload: str, blinded_response: str, model_id: str, *,
                      temperature: float = 0.0, num_ctx: int = 2048, max_tokens: int = 64,
                      max_retries: int = 3) -> tuple[int, int]:
    """v2 judge for criteria_invented ONLY (amendment A3). Returns (count, retries).
    Same blinding as v1 (aliased seed + aliased response only)."""
    from providers import query_model
    prompt = (CRITERIA_V2_TEMPLATE.replace("{{SEED_PAYLOAD}}", seed_payload.strip())
              .replace("{{RESPONSE}}", blinded_response.strip()))
    last = None
    for attempt in range(max_retries + 1):
        raw = query_model(model_id, prompt, temperature, num_ctx=num_ctx, max_tokens=max_tokens)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
                v = None
                if isinstance(obj, dict):
                    # v2 is single-variable: accept the canonical key, else a count-like key,
                    # else the object's single non-negative integer (model key-name drift).
                    for k in ("criteria_invented", "count", "n", "value"):
                        if isinstance(obj.get(k), int):
                            v = obj[k]; break
                    if v is None:
                        ints = [x for x in obj.values() if isinstance(x, int) and x >= 0]
                        if len(ints) == 1:
                            v = ints[0]
                if isinstance(v, int) and v >= 0:
                    return v, attempt
                last = JudgeParseError(f"no usable int in {obj!r}")
            except json.JSONDecodeError as e:
                last = e
        else:
            last = JudgeParseError("no JSON object")
    raise JudgeParseError(f"criteria v2 failed after {max_retries+1}: {last}")


def _validate(obj: dict) -> dict:
    if set(obj) != set(JUDGE_KEYS):
        raise JudgeParseError(f"keys {sorted(obj)} != {JUDGE_KEYS}")
    out = {}
    for k in ("diagnosis", "treatment_recommended", "differential_offered", "epistemic_flag"):
        if obj[k] not in (0, 1):
            raise JudgeParseError(f"{k}={obj[k]!r} not 0/1")
        out[k] = int(obj[k])
    if not isinstance(obj["confidence"], (int, float)) or not (0 <= obj["confidence"] <= 1):
        raise JudgeParseError(f"confidence={obj['confidence']!r} not in [0,1]")
    out["confidence"] = float(obj["confidence"])
    if not isinstance(obj["criteria_invented"], int) or obj["criteria_invented"] < 0:
        raise JudgeParseError(f"criteria_invented={obj['criteria_invented']!r} not int>=0")
    out["criteria_invented"] = obj["criteria_invented"]
    return out


def judge_response(seed_payload: str, blinded_response: str, model_id: str, *,
                   temperature: float = 0.0, num_ctx: int = 2048, max_tokens: int = 512,
                   max_retries: int = 3) -> tuple[dict, int]:
    """Blinded LLM judge. Sees ONLY the (name-aliased) seed payload and the (name-aliased)
    response — never the legitimacy wrapper, level, condition or family. Returns (scores, retries).
    Raises JudgeParseError if no valid strict-JSON with the 6 keys after retries."""
    from providers import query_model
    prompt = (JUDGE_TEMPLATE
              .replace("{{SEED_PAYLOAD}}", seed_payload.strip())
              .replace("{{RESPONSE}}", blinded_response.strip()))
    last = None
    for attempt in range(max_retries + 1):
        raw = query_model(model_id, prompt, temperature, num_ctx=num_ctx, max_tokens=max_tokens)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return _validate(json.loads(m.group(0))), attempt
            except (json.JSONDecodeError, JudgeParseError) as e:
                last = e
        else:
            last = JudgeParseError("no JSON object in output")
    raise JudgeParseError(f"judge failed after {max_retries + 1} attempts: {last}")

def main():
    # Judge model from env (blinded judge; keep distinct from the Phase-5 human-equivalent rater).
    model_id = os.environ.get("JUDGE_MODEL")
    if not model_id:
        sys.exit("set JUDGE_MODEL (e.g. ollama_remote/llama3.3:70b)")
    disorders = yaml.safe_load((ROOT / "materials" / "disorders.yaml").read_text())["disorders"]
    out = SCORED / "scored.jsonl"; n = 0
    with RAW.open() as fin, out.open("w") as fout:
        for line in fin:
            row = json.loads(line)
            seed_payload = disorders[row["disorder"]]["payload"]
            name = disorders[row["disorder"]]["name"]
            row["emergent_symptom_tokens"] = emergent_tokens(row["response"], seed_payload)
            # BLINDING: judge sees only the aliased seed payload + aliased response (never the
            # legitimacy wrapper / level). Name is aliased in both.
            try:
                judged, _ = judge_response(alias(seed_payload, name),
                                           alias(row["response"], name), model_id)
            except JudgeParseError:
                judged = {k: None for k in JUDGE_KEYS}
            row.update(judged)
            fout.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
    print(f"Scored {n} rows -> {out}")

if __name__ == "__main__":
    main()
