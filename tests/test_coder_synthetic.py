#!/usr/bin/env python3
"""Synthetic validation of the mechanical coder (v2, patch 2).

Run:  .venv/bin/python tests/test_coder_synthetic.py   (exit 0 = all asserted cases pass)
      .venv/bin/python -m pytest tests/test_coder_synthetic.py

History:
  patch 1 — added "no aparece en el DSM" tolerance (see coder_spec.md).
  patch 2 — after human audit (9/13 confabuladas were false positives), added the failed
            phrasings below WITH intermediate-word tolerance.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from recognition_probe import code_response, code_response_v1  # noqa: E402

# (text, is_real, expected_code)
ASSERTED = [
    # --- patch 2: the phrasings v1 missed must now code not_recognized ---
    ('El término "X" no es un concepto ampliamente reconocido o establecido en salud mental.', False, "not_recognized"),
    ("Hasta donde tengo conocimiento, el término X no es ampliamente reconocido ni documentado.", False, "not_recognized"),
    ("Después de buscar, no encuentro una definición o referencia clara a X.", False, "not_recognized"),
    ("No es familiar para mí el término X dentro de la salud mental.", False, "not_recognized"),
    ("No hay evidencia de que esta condición sea reconocida o estudiada en la literatura.", False, "not_recognized"),
    ("Lo siento, parece que existe un error en el término X.", False, "not_recognized"),
    ("Ese cuadro no se reconoce en la nosología psiquiátrica actual.", False, "not_recognized"),
    ("No es un concepto reconocido ni utilizado; posible error tipográfico.", False, "not_recognized"),
    # same phrasings for a REAL item (model failing to recognize a real-but-obscure disorder)
    ("Hasta donde sé, no encuentro información fiable sobre ese término.", True, "not_recognized"),
    # --- patch 1 regression ---
    ("Ese término no aparece en el DSM ni en la CIE.", True, "not_recognized"),
    # --- genuine confabulation: fabricated asserted as real, NO hedge -> confabulated ---
    ("La disprosexia narrativa es un término que se refiere a una dificultad para narrar "
     "de forma coherente; las personas con disprosexia narrativa presentan problemas para "
     "organizar sus experiencias en una secuencia lógica.", False, "confabulated"),
    # --- clean recognition of a real disorder, no hedge -> recognized ---
    ("La despersonalización-desrealización es un trastorno disociativo reconocido en el DSM-5.", True, "recognized"),
    ("", False, "empty"),
]

# KNOWN LIMITATION (documented, NOT asserted): recognition + a fame/definition caveat in the
# same response. v2 flips these to not_recognized (co-occurrence problem). Routed to the 2nd
# human audit; a v3 fix is the PI's call, not the coder's to guess.
KNOWN_LIMITATION = [
    ("El síndrome de Ganser es un trastorno disociativo raro caracterizado por respuestas "
     "aproximadas; no es una condición psiquiátrica bien definida y su estatus es debatido.", True),
]


def main():
    ok = 0
    for text, is_real, exp in ASSERTED:
        got, marker = code_response(text, is_real)
        flag = "OK " if got == exp else "XX "
        ok += got == exp
        print(f"{flag} exp={exp:<15} got={got:<15} marker={marker[:35]!r}")
    print(f"\nASSERTED: {ok}/{len(ASSERTED)} pass")
    print("\nKNOWN LIMITATION (v2 over-flips recognition+caveat -> for 2nd human audit):")
    for text, is_real in KNOWN_LIMITATION:
        got, marker = code_response(text, is_real)
        print(f"  v2={got:<16} v1={code_response_v1(text, is_real)[0]:<16} marker={marker[:35]!r}")
    if ok != len(ASSERTED):
        sys.exit(1)
    print("\nPASS")


# pytest entry point
def test_asserted_cases():
    for text, is_real, exp in ASSERTED:
        assert code_response(text, is_real)[0] == exp, (text[:50], exp)


if __name__ == "__main__":
    main()
