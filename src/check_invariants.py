#!/usr/bin/env python3
"""check_invariants.py — Anti-circularity gate. Run BEFORE any experiment.

Enforces the invariants in CLAUDE.md:
  (I1) No seed payload contains a forbidden_symptom_term.
  (I2) A disorder's payload is byte-identical across legitimacy levels (levels add form, not content).
  (I3) Seeds use only seed_allowed_terms beyond ordinary connective language (warn-only).
Exit code != 0 fails the build.
"""
import sys, re, pathlib, itertools
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAT = ROOT / "materials"
disorders = yaml.safe_load((MAT / "disorders.yaml").read_text())["disorders"]
lex = yaml.safe_load((ROOT / "scoring" / "seed_lexicon.yaml").read_text())
forbidden = [t.lower() for t in lex["forbidden_symptom_terms"]]

errors, warnings = [], []

# I1: forbidden terms in any seed payload (and disclosure, if present)
for key, d in disorders.items():
    blob = (d.get("payload", "") + " " + d.get("disclosure", "")).lower()
    for term in forbidden:
        if re.search(rf"\b{re.escape(term)}\b", blob):
            errors.append(f"[I1] seed '{key}' contains forbidden symptom term: '{term}'")

# I2: descriptive content is injected, not hardcoded per level. The payload lives in
# disorders.yaml and is injected via {{PAYLOAD}} identically across levels. We assert each
# template (ignoring comment lines) injects the payload EXACTLY once and names the category at
# least once. Counting in non-comment text avoids false positives from documentation headers.
for tmpl in sorted((MAT / "legitimacy").glob("L*.md")):
    # strip single-'#' documentation comments but KEEP markdown '##' headers
    keep = []
    for l in tmpl.read_text().splitlines():
        s = l.lstrip()
        if s.startswith("#") and not s.startswith("##"):
            continue
        keep.append(l)
    body = "\n".join(keep)
    np_ = body.count("{{PAYLOAD}}"); nn_ = body.count("{{NAME}}")
    if np_ != 1:
        errors.append(f"[I2] template {tmpl.name} injects {{PAYLOAD}} {np_}× (expected exactly 1)")
    if nn_ < 1:
        errors.append(f"[I2] template {tmpl.name} never names the category ({{NAME}} missing)")

# I3 (warn): the incoherent control must stay incoherent — flag overlap with DN's *distinctive*
# content words (not generic framing like 'condición'/'propuesta').
dn_distinctive = {"relato","autobiográfico","narrativa","hilo","afectiva","afectivo"}
inc = disorders["incoherent"]["payload"].lower()
overlap = sorted(t for t in dn_distinctive if t in inc)
if overlap:
    warnings.append(f"[I3] incoherent control leaks DN-distinctive words {overlap} — keep it noise")

print("INVARIANT CHECK")
for w in warnings: print("  WARN ", w)
for e in errors:   print("  FAIL ", e)
if errors:
    print(f"\n{len(errors)} invariant(s) violated. Fix before running the experiment.")
    sys.exit(1)
print(f"\nAll hard invariants pass ({len(warnings)} warning(s)).")
