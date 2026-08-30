"""Cloud vs edge inference adapters (Phase 1).

Cloud: OpenAI-compatible chat (xAI Grok).
Edge: same shape against local Ollama/vLLM/etc.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrainResult:
    mode: str
    text: str
    ok: bool
    detail: str = ""
    rtt_ms: Optional[float] = None


def _post_chat(
    base_url: str,
    api_key: Optional[str],
    model: str,
    user_text: str,
    timeout: float = 60.0,
) -> BrainResult:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Grok-compatible assistant in ASCENT dual-mode lab. "
                    "Be concise. Prefer ASCII. If offline/edge, say so only when asked. "
                    "Do not claim space-native inference."
                ),
            },
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ascent-starlink-client/0.2",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        rtt = (time.perf_counter() - t0) * 1000.0
        payload = json.loads(raw)
        text = payload["choices"][0]["message"]["content"]
        return BrainResult(
            mode="cloud" if "x.ai" in base_url else "edge",
            text=text,
            ok=True,
            rtt_ms=rtt,
        )
    except urllib.error.HTTPError as e:
        rtt = (time.perf_counter() - t0) * 1000.0
        return BrainResult(
            mode="error", text="", ok=False, detail=f"HTTP {e.code}", rtt_ms=rtt
        )
    except Exception as e:  # noqa: BLE001 - lab boundary
        rtt = (time.perf_counter() - t0) * 1000.0
        return BrainResult(
            mode="error",
            text="",
            ok=False,
            detail=type(e).__name__ + ": " + str(e)[:120],
            rtt_ms=rtt,
        )


def probe_cloud(timeout: float = 2.0) -> bool:
    """Cheap reachability. Skip network if no API key."""
    key = os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return False
    base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
    url = base.rstrip("/") + "/models"
    headers = {
        "User-Agent": "ascent-starlink-client/0.2",
        "Authorization": f"Bearer {key}",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def answer(user_text: str) -> BrainResult:
    """Prefer cloud Grok; fall back to edge."""
    cloud_base = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
    cloud_key = os.environ.get("XAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    cloud_model = os.environ.get("XAI_MODEL", "grok-3")
    cloud_timeout = float(os.environ.get("ASCENT_CLOUD_TIMEOUT", "45"))

    if cloud_key and probe_cloud(timeout=2.0):
        r = _post_chat(
            cloud_base, cloud_key, cloud_model, user_text, timeout=cloud_timeout
        )
        if r.ok:
            r.mode = "CLOUD"
            return r

    edge_base = os.environ.get("EDGE_BASE_URL", "http://127.0.0.1:11434/v1")
    edge_key = os.environ.get("EDGE_API_KEY")
    edge_model = os.environ.get("EDGE_MODEL", "llama3.1:8b")
    edge_timeout = float(os.environ.get("ASCENT_EDGE_TIMEOUT", "8"))
    r = _post_chat(edge_base, edge_key, edge_model, user_text, timeout=edge_timeout)
    if r.ok:
        r.mode = "EDGE"
        return r
    r.mode = "DEAD"
    r.text = (
        "[ASCENT] EDGE MODE unavailable and cloud Grok unreachable. "
        "Set XAI_API_KEY and/or start Ollama (EDGE_BASE_URL). "
        "Your turn was queued for flush when CLOUD returns."
    )
    return r
