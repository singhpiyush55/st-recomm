"""
Shared LLM client — abstracts OpenAI / Anthropic behind a single call_llm() function.
Every agent imports this instead of calling the SDKs directly.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> dict[str, Any]:
    """
    Call the configured LLM and return a dict with:
      - text: raw response text
      - tokens_used: total tokens consumed
      - latency_ms: round-trip time in milliseconds
    """
    model = model or _LLM_MODEL
    start = time.time()

    if "claude" in model.lower() or "anthropic" in model.lower():
        result = _call_anthropic(system_prompt, user_prompt, model, temperature, max_tokens)
    else:
        result = _call_openai(system_prompt, user_prompt, model, temperature, max_tokens, json_mode)

    result["latency_ms"] = int((time.time() - start) * 1000)
    return result


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

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

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
    """Try to extract JSON from an LLM response that may contain markdown fences."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON inside ```json ... ``` blocks
    import re
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find a JSON object or array anywhere
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

    logger.warning("Could not extract JSON from LLM response")
    return None
