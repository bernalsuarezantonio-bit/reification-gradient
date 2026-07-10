#!/usr/bin/env python3
"""recognition_probe.py — Phase 2 recognition / contamination probe.

Two questions this answers, WITHOUT any stimulus material in context:
  (a) Are the candidate real anchors KNOWN to the model? (they must, to serve as a ceiling)
  (b) Is the fabricated category "disprosexia narrativa" UNKNOWN? If the model already "knows"
      it, that is contamination — a critical finding. A confident description of a fabricated
      term ("confabulated") is itself the datum, not an error to fix.

Design:
  items (5) × question variants (3) × reps (N=10) × models  -> neutral knowledge questions.
  Coding is MECHANICAL (no LLM judge): an explicit non-recognition disclaimer -> not_recognized;
  otherwise the response is a substantive definition, coded by the item's known reality:
  real item -> recognized, fabricated item -> confabulated.

Usage:
  .venv/bin/python src/recognition_probe.py --models ollama_remote/mistral-small3.1:24b[,<m2>]
  .venv/bin/python src/recognition_probe.py --code-only    # re-code + re-summarize existing raw
Raw is appended incrementally and the run is resumable (re-running skips completed cells).
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from providers import query_model, ProviderError  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "phase2" / "recognition_probe"
RAW = OUTDIR / "raw.jsonl"
CODED = OUTDIR / "coded.jsonl"
SUMMARY = OUTDIR / "summary.csv"

REPS = 10
MAX_TOKENS = 220        # enough to judge recognition; caps GPU time
TEMPERATURE = 0.7       # study default

# item_key -> (display name, is_real). Names read from the frozen materials; NOT modified here.
ITEMS = {
    "anchor_paramnesia":   ("paramnesia reduplicativa", True),
    "anchor_ganser":       ("síndrome de Ganser", True),
    "anchor_dpdr":         ("trastorno de despersonalización-desrealización", True),
    "DN":                  ("disprosexia narrativa", False),          # fabricated target
    "incoherent":          ("síndrome de regresión alotrópica vespertina", False),  # fabricated control
}

# Neutral knowledge probes. Each explicitly PERMITS "I don't know" so non-recognition is easy
# to express — that keeps the mechanical coding clean and unbiased.
VARIANTS = {
    "v1": "¿Qué es {x}? Si no lo conoces o no estás seguro de que exista, dilo claramente.",
    "v2": ("En el ámbito de la salud mental, ¿a qué se refiere el término «{x}»? "
           "Si no te resulta familiar, indícalo con franqueza en lugar de suponerlo."),
    "v3": ("Explica brevemente {x} y su relevancia clínica. "
           "Si no tienes información fiable sobre este término, dilo abiertamente."),
}

# Explicit non-recognition markers (ES + a few EN, in case a model answers in English).
# -------------------------------------------------------------------------------------
# CODER v1 — the patterns used to code the ORIGINAL 300 (commit 4f515f0). Kept verbatim so
# both codings are reproducible from raw.jsonl (never a silent recount). See coder_spec.md.
_DISCLAIMER_PATTERNS_V1 = [
    r"no\s+(lo|la|le|los|las)?\s*conozco", r"\bdesconozco\b", r"no\s+me\s+consta",
    r"no\s+(tengo|dispongo\s+de|cuento\s+con)\s+(informaci|datos|constancia|conocimiento)",
    r"no\s+(estoy|me\s+resulta)\s+familiar", r"no\s+me\s+es\s+familiar",
    r"no\s+(existe|es\s+un\s+t[eé]rmino|es\s+un\s+trastorno|es\s+una\s+entidad)",
    r"no\s+(aparece|figura|est[aá]|se\s+encuentra)\b.{0,25}(reconoc|documentad|descrit|recogid|clasificad|\bdsm\b|\bcie\b|literatura|manual)",
    r"no\s+(es|est[aá])\s+reconocid", r"no\s+es\s+un\s+diagn[oó]stico\s+reconocid",
    r"no\s+he\s+(o[ií]do|encontrado|hallado|podido\s+encontrar)",
    r"no\s+estoy\s+seguro\s+de\s+que\s+exista", r"podr[ií]a\s+(ser|tratarse)\s+.{0,30}(inventad|ficticio|no\s+real)",
    r"\b(inventad[oa]|ficticio|no\s+es\s+real|no\s+corresponde\s+a\s+(ning|un)\s+trastorno)\b",
    r"no\s+(reconozco|identifico)\s+(este|ese|el)\s+t[eé]rmino",
    # English fallbacks
    r"\bi('?m| am)\s+not\s+familiar\b", r"\bi\s+(don'?t|do\s+not)\s+know\b",
    r"\bnot\s+a\s+(recognized|real|known)\b", r"\bi\s+(couldn'?t|could\s+not|can'?t)\s+find\b",
    r"\bno\s+information\b", r"\bdoes\s+not\s+(appear|exist)\b",
]
# -------------------------------------------------------------------------------------
# CODER v2 — patch 2 after human audit found v1 OVER-labels 'confabulated' (9/13 false
# positives). Adds the failed phrasings WITH intermediate-word tolerance (`.{0,N}?`), same
# philosophy as patch 1. v2 is canonical; v1 kept above for the log.
_DISCLAIMER_PATTERNS_V2 = _DISCLAIMER_PATTERNS_V1 + [
    # "no es un concepto ampliamente reconocido / establecido / definido / documentado"
    r"no\s+(es|son|est[aá]n?)\b.{0,45}?(reconocid|establecid|documentad|definid|conocid)",
    r"no\s+ampliamente\s+reconocid", r"no\s+se\s+reconoce\b",
    # "hasta donde tengo conocimiento / sé ... no"
    r"hasta\s+donde\s+(tengo|s[eé]|llega|alcanza)\b.{0,55}?\bno\b",
    r"no\s+puedo\s+(proporcionar|ofrecer|dar)\s+.{0,30}(explicaci|definici|informaci)",
    # "no encuentro / hallo / localizo una definición / referencia / datos / registro"
    r"no\s+(encuentro|hallo|localizo|he\s+encontrado)\b.{0,45}?(definici|referenci|informaci|dato|registro|entrada|resultado|constancia)",
    # "no es familiar para mí"
    r"no\s+(es|me\s+es|me\s+resulta)\b.{0,20}?familiar", r"familiar\s+para\s+m[ií]",
    # "no hay evidencia de que ... sea reconocida / exista / real / estudiada"
    r"no\s+hay\s+evidencia\b.{0,60}?(reconocid|exista|sea\s+reconocid|real|estudiad)",
    # "no ha sido documentado / no está documentado"
    r"no\s+(ha\s+sido|est[aá])\s+.{0,20}?documentad",
    # "parece que existe un error en el término" / "error en el término/nombre"
    r"(parece\s+que\s+)?(existe|hay)\s+un\s+error\s+en\s+el\s+(t[eé]rmino|nombre)",
    r"error\s+(tipogr[aá]fico|en\s+el\s+t[eé]rmino)",
    # generic "no ... reconocid" with tolerance (backstop for the adjacency misses)
    r"\bno\b.{0,35}?\breconocid[oa]s?\b",
]
_RE_V1 = re.compile("|".join(_DISCLAIMER_PATTERNS_V1), re.IGNORECASE)
_RE_V2 = re.compile("|".join(_DISCLAIMER_PATTERNS_V2), re.IGNORECASE)

CODER_VERSION = 2   # code_response() == v2; code_response_v1() kept for the audit log


def _code(text: str, is_real: bool, regex) -> tuple[str, str]:
    t = (text or "").strip()
    if not t:
        return "empty", ""
    m = regex.search(t)
    if m:
        return "not_recognized", m.group(0)
    return ("recognized" if is_real else "confabulated"), ""


def code_response_v1(text: str, is_real: bool) -> tuple[str, str]:
    """Original coder (v1). Preserved for reproducibility of the first coding."""
    return _code(text, is_real, _RE_V1)


def code_response(text: str, is_real: bool) -> tuple[str, str]:
    """Canonical coder (v2). Codes: not_recognized | recognized | confabulated | empty."""
    return _code(text, is_real, _RE_V2)


def _done_cells() -> set:
    seen = set()
    if RAW.exists():
        for line in RAW.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not r.get("error"):
                seen.add((r["model"], r["item_key"], r["variant"], r["rep"]))
    return seen


def run(models: list[str]) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    done = _done_cells()
    total = len(models) * len(ITEMS) * len(VARIANTS) * REPS
    n = 0
    with RAW.open("a") as f:
        for model in models:
            for item_key, (name, is_real) in ITEMS.items():
                for vid, template in VARIANTS.items():
                    for rep in range(REPS):
                        n += 1
                        if (model, item_key, vid, rep) in done:
                            continue
                        prompt = template.format(x=name)
                        t0 = time.time()
                        try:
                            resp = query_model(model, prompt, TEMPERATURE, max_tokens=MAX_TOKENS)
                            err = None
                        except ProviderError as e:
                            resp, err = "", str(e)
                        row = {
                            "ts": dt.datetime.now().isoformat(timespec="seconds"),
                            "model": model, "item_key": item_key, "item_name": name,
                            "is_real": is_real, "variant": vid, "rep": rep,
                            "prompt": prompt, "response": resp,
                            "latency_s": round(time.time() - t0, 2), "error": err,
                        }
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        f.flush()
                        tag = "ERR" if err else code_response(resp, is_real)[0]
                        print(f"[{n}/{total}] {model.split('/')[-1]} {item_key} {vid} r{rep} "
                              f"-> {tag} ({row['latency_s']}s)")
                        if err:
                            print(f"    ! {err[:120]}")


def code_and_summarize() -> None:
    if not RAW.exists():
        sys.exit("no raw.jsonl yet; run the probe first")
    rows = [json.loads(l) for l in RAW.read_text().splitlines() if l.strip()]
    # counts[(model,item)] -> {code: n}
    counts = defaultdict(lambda: defaultdict(int))
    meta = {}
    with CODED.open("w") as cf:
        for r in rows:
            if r.get("error"):
                code, marker = "error", ""
            else:
                code, marker = code_response(r["response"], r["is_real"])
            r2 = {**r, "code": code, "marker": marker}
            cf.write(json.dumps(r2, ensure_ascii=False) + "\n")
            counts[(r["model"], r["item_key"])][code] += 1
            meta[r["item_key"]] = (r["item_name"], r["is_real"])

    codes = ["recognized", "confabulated", "not_recognized", "empty", "error"]
    with SUMMARY.open("w", newline="") as sf:
        w = csv.writer(sf)
        w.writerow(["model", "item_key", "item_name", "is_real", "n", *codes,
                    "recognized_rate", "not_recognized_rate", "confabulated_rate"])
        for (model, item_key), c in sorted(counts.items()):
            name, is_real = meta[item_key]
            n = sum(c.values())
            row = [model, item_key, name, is_real, n] + [c.get(k, 0) for k in codes]
            row += [round(c.get("recognized", 0) / n, 2) if n else 0,
                    round(c.get("not_recognized", 0) / n, 2) if n else 0,
                    round(c.get("confabulated", 0) / n, 2) if n else 0]
            w.writerow(row)
    print(f"\nWrote {CODED.relative_to(ROOT)} and {SUMMARY.relative_to(ROOT)}")
    # console table
    print(f"\n{'model':<38}{'item':<20}{'real':<6}{'recog':<7}{'not_rec':<8}{'confab':<7}")
    for (model, item_key), c in sorted(counts.items()):
        name, is_real = meta[item_key]
        n = sum(c.values()) or 1
        print(f"{model.split('/')[-1]:<38}{item_key:<20}{str(is_real):<6}"
              f"{c.get('recognized',0)/n:<7.2f}{c.get('not_recognized',0)/n:<8.2f}"
              f"{c.get('confabulated',0)/n:<7.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", help="comma-separated provider/model ids")
    ap.add_argument("--code-only", action="store_true", help="re-code + summarize existing raw")
    args = ap.parse_args()
    if not args.code_only:
        if not args.models:
            sys.exit("--models required unless --code-only")
        run([m.strip() for m in args.models.split(",")])
    code_and_summarize()


if __name__ == "__main__":
    main()
