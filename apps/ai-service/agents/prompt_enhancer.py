"""
Prompt Enhancer — meta-agent called between stages.
Takes the output from the previous stage and the draft prompt for the next stage,
then asks the LLM to improve the prompt with more specific, targeted questions.
"""

from __future__ import annotations

import logging

from agents.llm_client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a prompt engineering specialist. Your job is to improve analysis prompts between stages of a stock evaluation pipeline.

You will be given:
1. The output from the previous analysis stage.
2. The draft prompt for the next stage.

Your job:
- Review what the previous stage found.
- Identify the most important findings that the next stage should focus on.
- Rewrite the draft prompt to be more specific and targeted based on what was learned.
- Keep the same structure and requirements, but make the questions sharper.
- Do NOT change the response format requirements.

Return ONLY the improved prompt text. No JSON, no explanation — just the improved prompt."""


def enhance_prompt(
    previous_output: str,
    draft_prompt: str,
    ticker: str = "",
) -> str:
    """
    Enhance a draft prompt using context from the previous stage.
    Returns the improved prompt string.
    """
    user_prompt = f"""## Previous Stage Output
{previous_output}

---

## Draft Prompt for Next Stage
{draft_prompt}

---

Improve this prompt to be more specific based on what the previous stage found. {"Focus on " + ticker + "." if ticker else ""}"""

    try:
        result = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.2, max_tokens=1500)
        enhanced = result["text"].strip()

        # Sanity check: enhanced prompt should be at least as long as draft
        if len(enhanced) < len(draft_prompt) * 0.5:
            logger.warning("Enhanced prompt too short, using original draft")
            return draft_prompt

        return enhanced

    except Exception as e:
        logger.warning(f"Prompt enhancement failed: {e}. Using original draft.")
        return draft_prompt
