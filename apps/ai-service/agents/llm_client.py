"""
Shared LLM client — abstracts OpenAI / Anthropic behind a single call_llm() function.
Every agent imports this instead of calling the SDKs directly.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

_LLM_MODEL = os.getenv("LLM_MODEL", "arcee-ai/trinity-large-preview:free")

# Comma-separated fallback models tried in order when primary fails
_FALLBACK_MODELS_STR = os.getenv(
    "LLM_FALLBACK_MODELS",
    "nvidia/nemotron-3-nano-30b-a3b:free,stepfun/step-3.5-flash:free"
)
_FALLBACK_MODELS = [m.strip() for m in _FALLBACK_MODELS_STR.split(",") if m.strip()]


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 512,
    json_mode: bool = False,
) -> dict[str, Any]:
    """
    Call the configured LLM and return a dict with:
      - text: raw response text
      - tokens_used: total tokens consumed
      - latency_ms: round-trip time in milliseconds
    Automatically retries with fallback models on 429/402 errors.
    """
    model = model or _LLM_MODEL
    start = time.time()

    # Build ordered list: primary + fallbacks (no duplicates)
    models_to_try = [model]
    for fb in _FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)

    last_error = None
    for i, attempt_model in enumerate(models_to_try):
        try:
            if "claude" in attempt_model.lower() or "anthropic" in attempt_model.lower():
                result = _call_anthropic(system_prompt, user_prompt, attempt_model, temperature, max_tokens)
            else:
                result = _call_openai(system_prompt, user_prompt, attempt_model, temperature, max_tokens, json_mode)
            result["latency_ms"] = int((time.time() - start) * 1000)
            if i > 0:
                logger.info(f"Succeeded with fallback model: {attempt_model}")
            return result
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "429" in err_str or "402" in err_str or "rate" in err_str.lower():
                logger.warning(f"Model {attempt_model} rate-limited, trying next...")
                time.sleep(1)
                continue
            else:
                raise  # Non-rate-limit errors propagate immediately

    raise last_error  # All models exhausted


# ── OpenAI ───────────────────────────────────────────────────────────

def _call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    from openai import OpenAI

    # ── OpenRouter (using FREE models) ──
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000",  # Optional, for rankings
            "X-Title": "Stock Recommender AI"  # Optional, shows in dashboard
        }
    )

    # ── Original OpenAI direct client (PAID - commented out) ──
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    # Free models typically don't support JSON mode - skip it for :free models
    if json_mode and ":free" not in model:
        kwargs["response_format"] = {"type": "json_object"}

    logger.info(f"Calling OpenRouter with model: {model}")
    
    response = client.chat.completions.create(**kwargs)
    choice = response.choices[0]

    return {
        "text": choice.message.content or "",
        "tokens_used": response.usage.total_tokens if response.usage else 0,
    }


# ── Anthropic ────────────────────────────────────────────────────────

def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    tokens_used = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0

    return {
        "text": text,
        "tokens_used": tokens_used,
    }


# ── JSON extraction helper ──────────────────────────────────────────

def extract_json(text: str) -> dict | list | None:
    """
    Robustly extract JSON from an LLM response that may contain:
    - Pure JSON
    - Markdown fenced blocks (```json ... ```)
    - Thinking/reasoning text before/after JSON
    - Multiple JSON objects (returns first valid one)
    """
    if not text or not text.strip():
        logger.warning("Empty LLM response, cannot extract JSON")
        return None

    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Markdown fenced blocks (```json ... ``` or ``` ... ```)
    for match in re.finditer(r"```(?:json)?\s*\n(.*?)\n?```", text, re.DOTALL):
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue

    # 3. Find balanced JSON object/array using brace counting
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escape = False
        for j in range(start, len(text)):
            ch = text[j]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start:j + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # Try next start_char type

    # 4. Last resort: strip common prefixes like "Here is the JSON:"
    #    and try again from the first { or [
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        idx = text.find(start_char)
        ridx = text.rfind(end_char)
        if idx != -1 and ridx != -1 and ridx > idx:
            try:
                return json.loads(text[idx:ridx + 1])
            except json.JSONDecodeError:
                pass

    logger.warning("Could not extract JSON from LLM response")
    return None
