#!/usr/bin/env python3
"""providers.py — model access layer.

`query_model(model_id, prompt, temperature)` dispatches by a provider prefix encoded in the
model id as ``provider/model_name``:

  ollama_remote/mistral-small3.1:24b   -> LAN Ollama server (base URL from OLLAMA_BASE_URL)
  anthropic/claude-...                 -> Anthropic API   (key from ANTHROPIC_API_KEY)
  openai/gpt-...                       -> OpenAI API       (key from OPENAI_API_KEY)

Hard rules honored here (see prompts/phase2 + CLAUDE.md):
- No credentials or hostnames in code: everything sensitive comes from the environment / .env.
- Requests are SEQUENTIAL by construction. Never fire two runs at the Ollama GPU at once — that
  coordination lives with the PI, but nothing in this module parallelizes calls.
- Timeouts + bounded retries with exponential backoff on transient network / 5xx failures.

Dependency-free on purpose (stdlib urllib): the model layer must import cleanly before the
heavier analysis deps are present.
"""
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

DEFAULT_TIMEOUT = 120       # seconds per HTTP call (24B on a 5090 can take a while cold)
DEFAULT_MAX_RETRIES = 3     # total attempts = 1 + retries
BACKOFF_BASE = 1.5          # seconds; delay = BACKOFF_BASE * 2**attempt


def load_env(path: str | os.PathLike | None = None) -> None:
    """Minimal .env loader (no python-dotenv dependency). Does not overwrite existing vars."""
    p = pathlib.Path(path) if path else (ROOT / ".env")
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


class ProviderError(RuntimeError):
    pass


def _http_post_json(url: str, payload: dict, headers: dict,
                    timeout: int, max_retries: int) -> dict:
    """POST JSON with bounded exponential-backoff retries on transient failures."""
    body = json.dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json", **headers}
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Retry only server-side/transient statuses; surface 4xx immediately.
            if e.code < 500 or attempt == max_retries:
                detail = e.read().decode("utf-8", "replace")[:500]
                raise ProviderError(f"HTTP {e.code} from {url}: {detail}") from e
            last_err = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == max_retries:
                raise ProviderError(f"network error to {url}: {e}") from e
            last_err = e
        time.sleep(BACKOFF_BASE * (2 ** attempt))
    raise ProviderError(f"exhausted retries to {url}: {last_err}")


def _query_ollama_remote(model_name: str, prompt: str, temperature: float,
                         timeout: int, max_retries: int, system: str | None,
                         max_tokens: int | None) -> str:
    base = os.environ.get("OLLAMA_BASE_URL")
    if not base:
        raise ProviderError("OLLAMA_BASE_URL not set (put it in .env / the environment)")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    options = {"temperature": temperature}
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    data = _http_post_json(base.rstrip("/") + "/api/chat", payload, {},
                           timeout=timeout, max_retries=max_retries)
    text = (data.get("message") or {}).get("content", "")
    if not text:
        raise ProviderError(f"empty content from ollama_remote/{model_name}: {str(data)[:300]}")
    return text


def _query_anthropic(model_name: str, prompt: str, temperature: float,
                     timeout: int, max_retries: int, system: str | None,
                     max_tokens: int | None) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ProviderError("ANTHROPIC_API_KEY not set")
    payload = {
        "model": model_name,
        "max_tokens": max_tokens or 1024,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    data = _http_post_json("https://api.anthropic.com/v1/messages", payload, headers,
                           timeout=timeout, max_retries=max_retries)
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    text = "".join(parts)
    if not text:
        raise ProviderError(f"empty content from anthropic/{model_name}: {str(data)[:300]}")
    return text


def _query_openai(model_name: str, prompt: str, temperature: float,
                  timeout: int, max_retries: int, system: str | None,
                  max_tokens: int | None) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ProviderError("OPENAI_API_KEY not set")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model_name, "temperature": temperature, "messages": messages}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    headers = {"Authorization": f"Bearer {key}"}
    data = _http_post_json("https://api.openai.com/v1/chat/completions", payload, headers,
                           timeout=timeout, max_retries=max_retries)
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    if not text:
        raise ProviderError(f"empty content from openai/{model_name}: {str(data)[:300]}")
    return text


_PROVIDERS = {
    "ollama_remote": _query_ollama_remote,
    "anthropic": _query_anthropic,
    "openai": _query_openai,
}


def query_model(model_id: str, prompt: str, temperature: float = 0.7, *,
                timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES,
                system: str | None = None, max_tokens: int | None = None) -> str:
    """Dispatch `provider/model_name` to the right backend and return the response text."""
    load_env()
    if "/" not in model_id:
        raise ProviderError(
            f"model id '{model_id}' missing provider prefix; use e.g. "
            "'ollama_remote/mistral-small3.1:24b'")
    provider, model_name = model_id.split("/", 1)
    fn = _PROVIDERS.get(provider)
    if fn is None:
        raise ProviderError(f"unknown provider '{provider}'; known: {sorted(_PROVIDERS)}")
    return fn(model_name, prompt, temperature, timeout, max_retries, system, max_tokens)
