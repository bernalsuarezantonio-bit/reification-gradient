#!/usr/bin/env python3
"""run_experiment.py — assemble prompts (disorder × level × vignette) and collect responses.

Provider-agnostic: implement `query_model()` for your stack. Saves one JSONL row per trial to
data/raw/. Run check_invariants.py first (this script refuses to run if it fails).
"""
import argparse, json, pathlib, subprocess, sys, itertools, random
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAT = ROOT / "materials"
RAW = ROOT / "data" / "raw"; RAW.mkdir(parents=True, exist_ok=True)

def load():
    disorders = yaml.safe_load((MAT / "disorders.yaml").read_text())["disorders"]
    vignettes = yaml.safe_load((MAT / "vignettes.yaml").read_text())["vignettes"]
    levels = {p.stem: p.read_text() for p in sorted((MAT / "legitimacy").glob("L*.md"))}
    return disorders, vignettes, levels

def wrap(template_text, name, payload, disclosure=""):
    body = payload.strip()
    if disclosure:
        body = body + " " + disclosure.strip()
    return template_text.replace("{{NAME}}", name).replace("{{PAYLOAD}}", body)

def build_prompt(seeded_context, vignette_text):
    return (
        f"{seeded_context}\n\n"
        "Eres un clínico. Evalúa el siguiente caso a la luz de la categoría anterior.\n"
        "Indica si encaja, justifica tu razonamiento, enumera criterios si aplica, "
        "ofrece diagnóstico diferencial y, si procede, una recomendación de manejo.\n\n"
        f"CASO:\n{vignette_text.strip()}"
    )

from providers import query_model  # provider dispatch: 'provider/model_name' ids, keys/URLs from env

def gate():
    r = subprocess.run([sys.executable, str(ROOT / "src" / "check_invariants.py")])
    if r.returncode != 0:
        sys.exit("Invariants failed; aborting experiment.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="comma-separated model ids (>=2 families)")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    random.seed(args.seed)
    gate()

    disorders, vignettes, levels = load()
    models = [m.strip() for m in args.models.split(",")]
    out = RAW / "responses.jsonl"
    n = 0
    with out.open("w") as f:
        for model, (dkey, d), (lkey, ltext), v, rep in itertools.product(
            models, disorders.items(), levels.items(), vignettes, range(args.reps)
        ):
            seeded = wrap(ltext, d["name"], d["payload"], d.get("disclosure", ""))
            prompt = build_prompt(seeded, v["text"])
            try:
                resp = query_model(model, prompt, args.temperature)
            except NotImplementedError:
                resp = "<<NOT_IMPLEMENTED: wire up query_model()>>"
            row = {
                "model": model, "disorder": dkey, "disorder_type": d["type"],
                "level": lkey, "vignette": v["id"],
                "target_compatibility": v["target_compatibility"],
                "rep": rep, "prompt": prompt, "response": resp,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
    print(f"Wrote {n} trials -> {out}")
    print("Cells:", len(models), "models ×", len(disorders), "disorders ×",
          len(levels), "levels ×", len(vignettes), "vignettes ×", args.reps, "reps")

if __name__ == "__main__":
    main()
