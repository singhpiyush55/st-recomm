"""
Stage 2 — Screener Agent.
Input: top sectors + pre-scored stock list.
Output: 5-7 best candidates with justification.
"""

from __future__ import annotations

import logging

from agents.llm_client import call_llm, extract_json
from models.schemas import AgentOutput, ScoreResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a stock screener for swing trades (2-6 week holding period).

You will be given:
1. The top sectors selected by the sector agent.
2. A list of 20-30 candidate stocks with their composite scores and component breakdowns.

Your job:
- Select the 5-7 best candidates based on the scores provided.
- Explain in 1-2 sentences why each stock was chosen.
- Prioritise stocks with high technical + fundamental scores and low risk penalty.
- Avoid stocks with AVOID verdict unless the scores are borderline.

Respond in JSON:
{
  "selected": [
    {"ticker": "AAPL", "reason": "..."},
    ...
  ]
}"""


def run_screener_agent(
    sectors: list[str],
    scored_stocks: dict[str, ScoreResult],
    top_n: int = 7,
) -> tuple[list[str], AgentOutput]:
    """Run the screener and return (selected_tickers, agent_output)."""

    # Build score table
    lines = [
        "| Ticker | Final | Tech | Fund | Sector | Sentiment | Risk | Verdict |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ticker, s in scored_stocks.items():
        lines.append(
            f"| {ticker} | {s.final_score:.1f} | {s.tech_score:.1f} | {s.fund_score:.1f} "
            f"| {s.sector_score:.1f} | {s.sentiment_score:.1f} | -{s.risk_penalty:.1f} "
            f"| {s.verdict.value} |"
        )

    user_prompt = f"""## Target Sectors
{', '.join(sectors)}

## Candidate Stock Scores

{chr(10).join(lines)}

Select the top {top_n} stocks for swing trades. Respond as JSON."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, json_mode=True)

    parsed = extract_json(result["text"])
    selected: list[str] = []
    narrative = result["text"]

    if parsed and isinstance(parsed, dict) and "selected" in parsed:
        parts = []
        for s in parsed["selected"]:
            t = s.get("ticker", "")
            if t:
                selected.append(t)
                parts.append(f"**{t}**: {s.get('reason', '')}")
        narrative = "\n".join(parts)

    # Fallback: if LLM failed, pick top-N by score
    if not selected:
        sorted_stocks = sorted(scored_stocks.items(), key=lambda x: x[1].final_score, reverse=True)
        selected = [t for t, _ in sorted_stocks[:top_n]]
        narrative = "Fallback: selected top stocks by composite score."

    output = AgentOutput(
        stage=2,
        agent_name="screener_agent",
        verdict=f"Selected {len(selected)} stocks",
        narrative=narrative,
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )

    logger.info(f"Screener selected: {selected}")
    return selected, output
