"""
Stage 3 — Fundamental Agent.
Input: fundamental ratios for one stock + guide doc.
Output: verdict + narrative paragraph.
"""

from __future__ import annotations

import logging
import os

from agents.llm_client import call_llm, extract_json
from models.schemas import AgentOutput, FundamentalRatios

logger = logging.getLogger(__name__)

# Load the guide once at module level
_GUIDE_PATH = os.path.join(os.path.dirname(__file__), "..", "guides", "fundamental_analysis.md")
_GUIDE_TEXT = ""


def _load_guide() -> str:
    global _GUIDE_TEXT
    if not _GUIDE_TEXT:
        try:
            with open(_GUIDE_PATH, "r", encoding="utf-8") as f:
                _GUIDE_TEXT = f.read()
        except FileNotFoundError:
            _GUIDE_TEXT = "No fundamental analysis guide available."
    return _GUIDE_TEXT


SYSTEM_PROMPT = """You are a senior fundamental analyst evaluating a stock for a swing trade (2-6 weeks).

You will be given:
1. A fundamental analysis guide with rules for interpreting each ratio.
2. The actual ratio values for the stock.

Your job:
- Follow the guide's rules to interpret each ratio.
- Give a verdict: "Strong", "Medium", or "Weak".
- Write a 3-4 sentence narrative identifying the top strengths and concerns.

Respond in JSON:
{
  "verdict": "Strong",
  "narrative": "..."
}"""


def run_fundamental_agent(ratios: FundamentalRatios) -> AgentOutput:
    """Interpret fundamental ratios for one stock."""
    guide = _load_guide()

    # Format ratios as a readable list
    ratio_lines = [
        f"- P/E Ratio: {_fmt(ratios.pe_ratio)}",
        f"- PEG Ratio: {_fmt(ratios.peg_ratio)}",
        f"- ROE: {_fmt_pct(ratios.roe)}",
        f"- ROA: {_fmt_pct(ratios.roa)}",
        f"- Debt-to-Equity: {_fmt(ratios.debt_to_equity)}",
        f"- Interest Coverage: {_fmt(ratios.interest_coverage)}x",
        f"- Revenue Growth (YoY): {_fmt_pct(ratios.revenue_growth)}",
        f"- EPS Growth (YoY): {_fmt_pct(ratios.eps_growth)}",
        f"- Free Cash Flow: {_fmt_dollar(ratios.free_cash_flow)}",
    ]

    user_prompt = f"""## Fundamental Analysis Guide
{guide}

---

## Stock: {ratios.ticker}

### Ratio Values
{chr(10).join(ratio_lines)}

Analyse these ratios using the guide above. Respond as JSON with verdict and narrative."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, json_mode=True)

    parsed = extract_json(result["text"])
    verdict = "Medium"
    narrative = result["text"]

    if parsed and isinstance(parsed, dict):
        verdict = parsed.get("verdict", "Medium")
        narrative = parsed.get("narrative", result["text"])

    return AgentOutput(
        stage=3,
        agent_name="fundamental_agent",
        verdict=verdict,
        narrative=narrative,
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )


# ── Formatters ───────────────────────────────────────────────────────

def _fmt(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.2f}"


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%"


def _fmt_dollar(val) -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1e9:
        return f"${val / 1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"
