"""
Stage 4 — Technical Agent.
Input: technical indicators for one stock + guide doc.
Output: verdict + narrative + suggested entry zone.
"""

from __future__ import annotations

import logging
import os

from agents.llm_client import call_llm, extract_json
from models.schemas import AgentOutput, TechnicalSignals

logger = logging.getLogger(__name__)

_GUIDE_PATH = os.path.join(os.path.dirname(__file__), "..", "guides", "technical_analysis.md")
_GUIDE_TEXT = ""


def _load_guide() -> str:
    global _GUIDE_TEXT
    if not _GUIDE_TEXT:
        try:
            with open(_GUIDE_PATH, "r", encoding="utf-8") as f:
                _GUIDE_TEXT = f.read()
        except FileNotFoundError:
            _GUIDE_TEXT = "No technical analysis guide available."
    return _GUIDE_TEXT


SYSTEM_PROMPT = """You are a senior technical analyst evaluating a stock's chart setup for a swing trade (2-6 weeks).

You will be given:
1. A technical analysis guide with rules for interpreting each indicator.
2. The actual indicator values for the stock.

Your job:
- Follow the guide's rules to interpret each indicator.
- Describe the current chart setup in plain language.
- Identify the key signal driving your view.
- Suggest an entry zone (low and high price).
- Give a verdict: "Strong", "Medium", or "Weak".

Respond in JSON:
{
  "verdict": "Strong",
  "narrative": "...",
  "entry_low": 150.00,
  "entry_high": 155.00
}"""


def run_technical_agent(signals: TechnicalSignals) -> tuple[AgentOutput, dict]:
    """
    Interpret technical indicators for one stock.
    Returns (agent_output, extras) where extras may contain entry_low/entry_high.
    """
    guide = _load_guide()

    indicator_lines = [
        f"- EMA-20: {signals.ema_20:.2f}",
        f"- EMA-50: {signals.ema_50:.2f}",
        f"- EMA-200: {signals.ema_200:.2f}",
        f"- MACD Line: {signals.macd_line:.4f}",
        f"- MACD Signal: {signals.macd_signal:.4f}",
        f"- MACD Histogram: {signals.macd_histogram:.4f}",
        f"- RSI (14): {signals.rsi:.2f}",
        f"- Bollinger Upper: {signals.bb_upper:.2f}",
        f"- Bollinger Lower: {signals.bb_lower:.2f}",
        f"- ATR (14): {signals.atr:.2f}",
        f"- Volume Spike: {'Yes' if signals.volume_spike else 'No'}",
        f"- OBV Trend: {signals.obv_trend}",
    ]

    user_prompt = f"""## Technical Analysis Guide
{guide}

---

## Stock: {signals.ticker}

### Indicator Values
{chr(10).join(indicator_lines)}

Analyse the chart setup using the guide above. Respond as JSON with verdict, narrative, entry_low, and entry_high."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, json_mode=True)

    parsed = extract_json(result["text"])
    verdict = "Medium"
    narrative = result["text"]
    extras: dict = {}

    if parsed and isinstance(parsed, dict):
        verdict = parsed.get("verdict", "Medium")
        narrative = parsed.get("narrative", result["text"])
        if "entry_low" in parsed:
            extras["entry_low"] = float(parsed["entry_low"])
        if "entry_high" in parsed:
            extras["entry_high"] = float(parsed["entry_high"])

    output = AgentOutput(
        stage=4,
        agent_name="technical_agent",
        verdict=verdict,
        narrative=narrative,
        prompt=user_prompt,
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )

    return output, extras
