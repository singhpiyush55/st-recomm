"""
Sentiment scoring via news headlines + FinBERT.
Input: ticker string.
Output: SentimentResult model (score from -1.0 to 1.0).
"""

from __future__ import annotations

import logging
from typing import Optional

from data.fetcher import get_news_headlines
from models.schemas import SentimentResult

logger = logging.getLogger(__name__)

# Lazy-loaded FinBERT pipeline (heavy import, load once)
_sentiment_pipeline = None


def _get_pipeline():
    """Lazy-load the FinBERT sentiment pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline

            _sentiment_pipeline = hf_pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=-1,  # CPU
            )
        except Exception as e:
            logger.warning(f"Failed to load FinBERT model: {e}. Falling back to neutral scores.")
            _sentiment_pipeline = None
    return _sentiment_pipeline


def compute_sentiment(ticker: str, days: int = 7) -> SentimentResult:
    """
    Fetch recent news headlines and score them with FinBERT.
    Returns a SentimentResult with an average score between -1.0 and 1.0.
    """
    headlines = get_news_headlines(ticker, days)

    if not headlines:
        return SentimentResult(
            ticker=ticker,
            news_score=0.0,
            insider_signal="neutral",
            headlines=[],
        )

    scores = _score_headlines(headlines)
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Clamp to [-1, 1]
    avg_score = max(-1.0, min(1.0, avg_score))

    return SentimentResult(
        ticker=ticker,
        news_score=round(avg_score, 4),
        insider_signal="neutral",  # Placeholder — could enrich later
        headlines=headlines[:10],  # Keep top 10 for storage
    )


def _score_headlines(headlines: list[str]) -> list[float]:
    """Run each headline through FinBERT and convert labels to numeric scores."""
    pipe = _get_pipeline()

    if pipe is None:
        # FinBERT unavailable — return neutral scores
        return [0.0] * len(headlines)

    scores: list[float] = []
    for headline in headlines:
        try:
            result = pipe(headline[:512], truncation=True)[0]
            label = result["label"].lower()
            confidence = result["score"]

            if label == "positive":
                scores.append(confidence)
            elif label == "negative":
                scores.append(-confidence)
            else:
                scores.append(0.0)
        except Exception as e:
            logger.debug(f"Error scoring headline '{headline[:50]}…': {e}")
            scores.append(0.0)

    return scores
