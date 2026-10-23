"""Cloud AI client for Google Gemini and OpenAI-compatible providers.

Supports:
- Google Gemini (gemini-1.5-flash, gemini-2.0-flash, etc.)
- OpenAI (gpt-4o-mini, gpt-4o, etc.)
- Groq (gemma2-9b-it, llama-3.3-70b-versatile, etc.)
- OpenRouter (openrouter/auto, etc.)
- Custom OpenAI-compatible endpoints (vLLM, LM Studio, etc.)
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import httpx

from bob.ai.prompts import SYSTEM_PROMPT, build_triage_prompt
from bob.config import Config
from bob.models import Finding


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"
GROQ_DEFAULT_BASE = "https://api.groq.com/openai/v1"
OPENROUTER_DEFAULT_BASE = "https://openrouter.ai/api/v1"


def get_base_url_for_provider(provider: str, custom_url: Optional[str] = None) -> str:
    """Return default or configured base URL for OpenAI-compatible providers."""
    p = provider.lower()
    if p == "groq":
        return custom_url or GROQ_DEFAULT_BASE
    if p == "openrouter":
        return custom_url or OPENROUTER_DEFAULT_BASE
    if p == "custom":
        return custom_url or "http://localhost:8000/v1"
    return custom_url or OPENAI_DEFAULT_BASE


def validate_cloud_credentials(
    provider: str,
    api_key: str,
    model_name: str,
    base_url: Optional[str] = None,
    timeout: float = 3.5,
) -> Tuple[bool, str]:
    """Test API credentials with a lightweight probe.

    Returns:
        (is_valid, status_message)
    """
    if not api_key or not api_key.strip():
        return False, "API key is empty"

    p = provider.lower()

    if p == "gemini":
        # Probe Gemini models list endpoint
        probe_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(probe_url)
                if resp.status_code == 200:
                    return True, "Connected to Google Gemini API (Key verified)"
                if resp.status_code in (400, 401, 403):
                    return False, f"Gemini auth error (HTTP {resp.status_code}): Invalid API key"
                return False, f"Gemini responded with HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Network error contacting Gemini ({type(e).__name__})"

    # OpenAI-compatible providers (OpenAI, Groq, OpenRouter, Custom)
    resolved_base = get_base_url_for_provider(p, base_url).rstrip("/")
    probe_url = f"{resolved_base}/models"
    headers = {"Authorization": f"Bearer {api_key.strip()}"}

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(probe_url, headers=headers)
            if resp.status_code == 200:
                return True, f"Connected to {provider.title()} API (Key verified)"
            if resp.status_code in (401, 403):
                return False, f"{provider.title()} auth error (HTTP {resp.status_code}): Invalid API key"
            return False, f"{provider.title()} responded with HTTP {resp.status_code}"
    except Exception as e:
        return False, f"Network error contacting {provider.title()} ({type(e).__name__})"


def query_gemini_triage(
    api_key: str,
    model_name: str,
    finding: Finding,
    context_snippet: str = "",
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """Query Google Gemini API for structured triage of a single finding."""
    # Ensure standard model naming format (e.g. gemini-1.5-flash)
    clean_model = model_name if "/" not in model_name else model_name.split("/")[-1]
    url = GEMINI_API_URL.format(model=clean_model)
    full_url = f"{url}?key={api_key.strip()}"

    user_prompt = build_triage_prompt(finding, context_snippet)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "maxOutputTokens": 600,
        },
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(full_url, json=payload)
            if resp.status_code != 200:
                return None

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not raw_text:
                return None

            parsed = json.loads(raw_text.strip())
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


def query_openai_compatible_triage(
    base_url: str,
    api_key: str,
    model_name: str,
    finding: Finding,
    context_snippet: str = "",
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """Query OpenAI-compatible chat API for structured triage of a single finding."""
    chat_url = f"{base_url.rstrip('/')}/chat/completions"
    user_prompt = build_triage_prompt(finding, context_snippet)

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "max_tokens": 600,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(chat_url, headers=headers, json=payload)
            if resp.status_code != 200:
                return None

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return None

            raw_content = choices[0].get("message", {}).get("content", "")
            if not raw_content:
                return None

            parsed = json.loads(raw_content.strip())
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


def query_cloud_triage(
    config: Config,
    finding: Finding,
    context_snippet: str = "",
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """Dispatch cloud triage request to Gemini or OpenAI-compatible provider."""
    if not config.api_key:
        return None

    provider = config.ai_provider.lower()
    if provider == "gemini":
        return query_gemini_triage(
            config.api_key, config.model, finding, context_snippet, timeout=timeout
        )

    # All others use OpenAI-compatible format
    base_url = get_base_url_for_provider(provider)
    return query_openai_compatible_triage(
        base_url, config.api_key, config.model, finding, context_snippet, timeout=timeout
    )
