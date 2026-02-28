"""
Stage 5 — Report Agent.
Input: ScoreResult + fundamental verdict + technical verdict + ATR.
Output: final recommendation report with entry, stop, target, RR, risks.
"""

from __future__ import annotations

import logging

from agents.llm_client import call_llm, extract_json
from models.schemas import AgentOutput, ScoreResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior portfolio strategist writing the final swing-trade recommendation report.

You will be given:
1. The composite score and all 5 component scores.
2. The fundamental agent's verdict and narrative.
3. The technical agent's verdict and narrative.
4. The ATR value for stop-loss calculation.

Your job:
- Write a final recommendation covering: overall verdict, entry price zone, stop loss, target, risk-reward ratio.
- Stop loss = entry_low − 2 × ATR.
- Target = entry_high + 2 × (entry_high − stop_loss).
- R/R ratio = (target − entry_mid) / (entry_mid − stop_loss).
- List the top 3 risks to the thesis.
- Write a 2-3 sentence summary.

Respond in JSON:
{
  "verdict": "STRONG_BUY",
  "entry_low": 150.00,
  "entry_high": 155.00,
  "stop_loss": 142.00,
  "target": 168.00,
  "rr_ratio": 2.5,
  "risks": ["...", "...", "..."],
  "summary": "..."
}"""


def run_report_agent(
    ticker: str,
    score: ScoreResult,
    fundamental_output: AgentOutput,
    technical_output: AgentOutput,
    atr: float,
    entry_low: float | None = None,
    entry_high: float | None = None,
) -> tuple[AgentOutput, dict]:
    """
    Generate the final recommendation report.
    Returns (agent_output, report_data) where report_data has entry/stop/target/rr.
    """
    user_prompt = f"""## Stock: {ticker}

### Composite Score: {score.final_score:.1f} / 100 — {score.verdict.value}
- Technical: {score.tech_score:.1f} / 40
- Fundamental: {score.fund_score:.1f} / 30
- Sector: {score.sector_score:.1f} / 15
- Sentiment: {score.sentiment_score:.1f} / 10
- Risk Penalty: −{score.risk_penalty:.1f} / 5

### Fundamental Analysis (Stage 3)
Verdict: {fundamental_output.verdict}
{fundamental_output.narrative}

### Technical Analysis (Stage 4)
Verdict: {technical_output.verdict}
{technical_output.narrative}

### ATR (14-period): {atr:.2f}
{f"Suggested entry zone from technical agent: {entry_low:.2f} – {entry_high:.2f}" if entry_low and entry_high else "No entry zone suggested — calculate one based on the indicators."}

Write the final recommendation report as JSON. Calculate stop_loss, target, and rr_ratio using the formulas in your instructions."""

    result = call_llm(SYSTEM_PROMPT, user_prompt, json_mode=True)

    parsed = extract_json(result["text"])
    report_data: dict = {}
    narrative = result["text"]

    if parsed and isinstance(parsed, dict):
        report_data = {
            "entry_low": float(parsed.get("entry_low", entry_low or 0)),
            "entry_high": float(parsed.get("entry_high", entry_high or 0)),
            "stop_loss": float(parsed.get("stop_loss", 0)),
            "target": float(parsed.get("target", 0)),
            "rr_ratio": float(parsed.get("rr_ratio", 0)),
        }
        risks = parsed.get("risks", [])
        summary = parsed.get("summary", "")
        verdict_str = parsed.get("verdict", score.verdict.value)

        narrative = f"**Verdict: {verdict_str}**\n\n{summary}"
        if risks:
            narrative += "\n\n**Key Risks:**\n" + "\n".join(f"- {r}" for r in risks)
    else:
        # Fallback: compute from ATR
        el = entry_low or 0
        eh = entry_high or 0
        sl = el - 2 * atr if el else 0
        tgt = eh + 2 * (eh - sl) if eh and sl else 0
        mid = (el + eh) / 2 if el and eh else 0
        rr = (tgt - mid) / (mid - sl) if mid and sl and mid > sl else 0
        report_data = {
            "entry_low": el,
            "entry_high": eh,
            "stop_loss": round(sl, 2),
            "target": round(tgt, 2),
            "rr_ratio": round(rr, 2),
        }

    output = AgentOutput(
        stage=5,
        agent_name="report_agent",
        verdict=score.verdict.value,
        narrative=narrative,
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0),
    )

    return output, report_data
