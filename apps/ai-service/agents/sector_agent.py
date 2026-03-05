"""
Stage 1 — Sector Agent.
Input: sector rankings + market index trend.
Output: top 2-3 sectors with rationale.
"""

from __future__ import annotations

import logging

from agents.llm_client import call_llm, extract_json
from models.schemas import AgentOutput, SectorRanking

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior equity strategist specialising in Indian (NSE) sector rotation for swing trades (2-6 week holding period).

You will be given:
1. A table of Nifty sectoral index 1-month returns.
2. Whether the Nifty 50 index is above or below its 200-day EMA.

Your job:
- Identify the top 2-3 sectors with the best momentum for swing trades over the next 3-4 weeks.
- Give brief reasoning for each sector (2-3 sentences).
- Consider both absolute return and relative strength.
- If the index is below its 200-day EMA, prefer defensive sectors (FMCG, Pharma, IT).

Respond in JSON:
{
  "sectors": [
    {"name": "IT", "index": "^CNXIT", "rationale": "..."},
    ...
  ]
}"""


def run_sector_agent(
    rankings: list[SectorRanking],
    index_above_200ema: bool,
) -> tuple[list[str], AgentOutput]:
    """Run the sector agent and return (sector_names, agent_output)."""

    # Build a plain-text table for the LLM
    table_lines = ["| Rank | Sector | Index | 1-Month Return |", "| --- | --- | --- | --- |"]
    for r in rankings:
        table_lines.append(f"| {r.rank} | {r.sector} | {r.etf} | {r.return_1m:+.2f}% |")

    user_prompt = f"""## Nifty Sectoral Index Performance (Last 30 Days)

{chr(10).join(table_lines)}

Nifty 50 vs 200-day EMA: {"ABOVE (bullish)" if index_above_200ema else "BELOW (bearish)"}

Based on this data, which 2-3 sectors offer the best swing-trade setups over the next 3-4 weeks? Provide your answer as JSON."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, json_mode=True)

    parsed = extract_json(result["text"])
    sector_names: list[str] = []
    narrative = result["text"]

    if parsed and isinstance(parsed, dict) and "sectors" in parsed:
        for s in parsed["sectors"]:
            name = s.get("name", "")
            if name:
                sector_names.append(name)
        # Build readable narrative
        parts = []
        for s in parsed["sectors"]:
            parts.append(f"**{s.get('name', '?')}** ({s.get('index', s.get('etf', '?'))}): {s.get('rationale', '')}")
        narrative = "\n".join(parts)

    output = AgentOutput(
        stage=1,
        agent_name="sector_agent",
        verdict=", ".join(sector_names) if sector_names else "No sectors identified",
        narrative=narrative,
        prompt=user_prompt,
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )

    logger.info(f"Sector agent selected: {sector_names}")
    return sector_names, output
