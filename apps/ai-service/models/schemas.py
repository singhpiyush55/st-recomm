"""
Pydantic models — the single source of truth for all data shapes
flowing through the AI service pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    MEDIUM_BUY = "MEDIUM_BUY"
    WEAK_BUY = "WEAK_BUY"
    AVOID = "AVOID"


# ── Request models ───────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    """Incoming request to trigger a full pipeline run."""
    sectors: list[str] = Field(
        default=[],
        description="Restrict analysis to these sectors. Empty = auto-detect via sector agent.",
    )
    tickers: list[str] = Field(
        default=[],
        description="Explicit ticker list. If provided, skips sector screening.",
    )
    days: int = Field(default=200, description="Days of price history to fetch.")
    top_n: int = Field(default=5, description="Max stocks to return in final output.")


# ── Quant data models ───────────────────────────────────────────────

class TechnicalSignals(BaseModel):
    """Output of quant/technical.py for one ticker."""
    ticker: str
    date: datetime
    ema_20: float
    ema_50: float
    ema_200: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    rsi: float
    bb_upper: float
    bb_lower: float
    atr: float
    volume_spike: bool
    obv_trend: str  # "rising" | "falling" | "flat"


class FundamentalRatios(BaseModel):
    """Output of quant/fundamental.py for one ticker."""
    ticker: str
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    revenue_growth: Optional[float] = None
    eps_growth: Optional[float] = None
    free_cash_flow: Optional[float] = None


class SentimentResult(BaseModel):
    """Output of quant/sentiment.py for one ticker."""
    ticker: str
    news_score: float = Field(ge=-1.0, le=1.0)
    insider_signal: str = "neutral"
    earnings_surprise: Optional[float] = None
    headlines: list[str] = Field(default_factory=list)


class RiskMetrics(BaseModel):
    """Output of quant/risk.py for one ticker."""
    ticker: str
    beta: float
    sharpe_ratio: float
    max_drawdown: float
    atr_percent: float


class SectorRanking(BaseModel):
    """One sector's ranking from quant/sector.py."""
    sector: str
    etf: str
    return_1m: float
    rank: int


# ── Composite quant container ───────────────────────────────────────

class QuantData(BaseModel):
    """All quant outputs combined for one stock."""
    ticker: str
    technical: TechnicalSignals
    fundamental: FundamentalRatios
    sentiment: SentimentResult
    risk: RiskMetrics


# ── Scoring ──────────────────────────────────────────────────────────

class ScoreResult(BaseModel):
    """Output of scoring/engine.py for one stock."""
    tech_score: float = Field(ge=0, le=40)
    fund_score: float = Field(ge=0, le=30)
    sector_score: float = Field(ge=0, le=15)
    sentiment_score: float = Field(ge=0, le=10)
    risk_penalty: float = Field(ge=0, le=5)
    final_score: float = Field(ge=0, le=100)
    verdict: Verdict


# ── Agent outputs ────────────────────────────────────────────────────

class AgentOutput(BaseModel):
    """Output from a single LLM agent stage."""
    stage: int
    agent_name: str
    verdict: Optional[str] = None
    narrative: str = ""
    prompt: str = ""
    tokens_used: int = 0
    latency_ms: int = 0


# ── Final per-stock result ───────────────────────────────────────────

class StockResult(BaseModel):
    """Everything the pipeline produces for one stock."""
    ticker: str
    quant: QuantData
    score: ScoreResult
    entry_low: float
    entry_high: float
    stop_loss: float
    target: float
    rr_ratio: float
    agent_outputs: list[AgentOutput] = Field(default_factory=list)


# ── Pipeline response ───────────────────────────────────────────────

class PipelineResponse(BaseModel):
    """Top-level response from POST /run."""
    run_id: str
    status: str = "done"
    run_date: datetime = Field(default_factory=datetime.utcnow)
    sectors_targeted: list[str] = Field(default_factory=list)
    total_stocks_analyzed: int = 0
    results: list[StockResult] = Field(default_factory=list)
