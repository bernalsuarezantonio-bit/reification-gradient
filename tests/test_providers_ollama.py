#!/usr/bin/env python3
"""Minimal live test: ollama_remote returns non-empty text for a trivial prompt.

Runnable two ways:
  .venv/bin/python -m pytest tests/test_providers_ollama.py -s   # if pytest present
  .venv/bin/python tests/test_providers_ollama.py                # standalone (exit 0/1)

Skips (does not fail) when OLLAMA_BASE_URL is unset, so it is safe in CI without the LAN.
"""
import os
import sys
import time
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from providers import query_model, load_env  # noqa: E402

MODEL = "ollama_remote/mistral-small3.1:24b"


def test_ollama_remote_returns_text():
    load_env()
    if not os.environ.get("OLLAMA_BASE_URL"):
        import unittest
        raise unittest.SkipTest("OLLAMA_BASE_URL unset; skipping live Ollama test")
    t0 = time.time()
    out = query_model(MODEL, "Responde solo con la palabra: hola", temperature=0.0)
    dt = time.time() - t0
    assert isinstance(out, str) and out.strip(), "expected non-empty text"
    print(f"[ollama_remote] latency={dt:.2f}s chars={len(out)} sample={out.strip()[:80]!r}")


if __name__ == "__main__":
    try:
        test_ollama_remote_returns_text()
        print("PASS")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: {type(e).__name__}: {e}")
        sys.exit(1)
