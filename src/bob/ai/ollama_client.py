"""HTTP client for Ollama local AI model interactions."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import httpx

from bob.ai.prompts import AI_OUTPUT_SCHEMA, SYSTEM_PROMPT, build_triage_prompt
from bob.models import Finding


def check_ollama_status(
    ollama_url: str, model_name: str, timeout: float = 1.5
) -> Tuple[bool, str]:
    """Check if Ollama is running and whether the requested model is pulled."""
    tags_url = f"{ollama_url.rstrip('/')}/api/tags"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(tags_url)
            if resp.status_code != 200:
                return False, f"Ollama HTTP {resp.status_code}"

            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            # Direct match or prefix match (e.g., 'gemma4:e2b' in 'gemma4:e2b' or tag variants)
            norm_target = model_name.lower()
            found = any(norm_target in m.lower() or m.lower().startswith(norm_target) for m in models)
            if found:
                return True, f"Model {model_name} ready"
            return False, f"Model {model_name} not found in Ollama (available: {', '.join(models[:5]) if models else 'none'})"
    except Exception as e:
        return False, f"Ollama unavailable on {ollama_url} ({type(e).__name__})"


def query_ollama_triage(
    ollama_url: str,
    model_name: str,
    finding: Finding,
    context_snippet: str = "",
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """Query Ollama chat API for structured triage of a single finding."""
    chat_url = f"{ollama_url.rstrip('/')}/api/chat"
    user_prompt = build_triage_prompt(finding, context_snippet)

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": AI_OUTPUT_SCHEMA,
        "options": {
            "temperature": 0.0,
        },
        "keep_alive": "5m",
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(chat_url, json=payload)
            if resp.status_code != 200:
                return None

            data = resp.json()
            raw_content = data.get("message", {}).get("content", "")
            if not raw_content:
                return None

            parsed = json.loads(raw_content)
            # Validate required keys
            if (
                isinstance(parsed, dict)
                and "verdict" in parsed
                and "explanation" in parsed
                and "suggested_fix" in parsed
            ):
                return parsed
    except Exception:
        return None

    return None
