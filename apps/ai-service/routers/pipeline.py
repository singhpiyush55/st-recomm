"""
Pipeline router — POST /run.
Main orchestration endpoint that wires all agents together.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException

from agents.fundamental_agent import run_fundamental_agent
from agents.report_agent import run_report_agent
from agents.screener_agent import run_screener_agent
from agents.sector_agent import run_sector_agent
from agents.technical_agent import run_technical_agent
from data.fetcher import get_index_data, get_stock_universe
from models.schemas import (
    AgentOutput,
    PipelineRequest,
    PipelineResponse,
    QuantData,
    ScoreResult,
    StockResult,
)
from quant.fundamental import compute_fundamental_ratios
from quant.risk import compute_risk_metrics
from quant.sector import rank_sectors
from quant.sentiment import compute_sentiment
from quant.technical import compute_technical_signals
from scoring.engine import score_stock

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Full pipeline orchestration:
    1. Rank sectors & identify top ones via sector agent
    2. Get stock universe for those sectors
    3. Compute quant data + scores for every stock
    4. Screener agent picks top candidates
    5. For each candidate: fundamental agent + technical agent + report agent
    6. Return PipelineResponse
    """
    run_id = str(uuid.uuid4())
    logger.info(f"Pipeline run {run_id} started")

    try:
        # ── Step 1: Sector ranking + sector agent ────────────────────
        sector_rankings = rank_sectors(days=30)
        index_above_200ema = _check_index_trend()

        if request.sectors:
            # User specified sectors — skip the LLM call
            top_sectors = request.sectors
            sector_output = AgentOutput(
                stage=1, agent_name="sector_agent",
                verdict=", ".join(top_sectors),
                narrative="User-specified sectors.",
            )
        else:
            top_sectors, sector_output = run_sector_agent(sector_rankings, index_above_200ema)

        if not top_sectors:
            top_sectors = [r.sector for r in sector_rankings[:3]]

        logger.info(f"Top sectors: {top_sectors}")

        # ── Step 2: Build stock universe ─────────────────────────────
        if request.tickers:
            tickers = request.tickers
        else:
            tickers = get_stock_universe(top_sectors)

        logger.info(f"Universe: {len(tickers)} stocks")

        # ── Step 3: Compute quant data + scores for all stocks ───────
        quant_map: dict[str, QuantData] = {}
        score_map: dict[str, ScoreResult] = {}

        for ticker in tickers:
            try:
                tech = compute_technical_signals(ticker, request.days)
                fund = compute_fundamental_ratios(ticker)
                sent = compute_sentiment(ticker)
                risk = compute_risk_metrics(ticker)

                qd = QuantData(
                    ticker=ticker,
                    technical=tech,
                    fundamental=fund,
                    sentiment=sent,
                    risk=risk,
                )
                quant_map[ticker] = qd
                score_map[ticker] = score_stock(qd, sector_rankings, index_above_200ema)

            except Exception as e:
                logger.warning(f"Skipping {ticker}: {e}")
                continue

        if not score_map:
            raise HTTPException(status_code=500, detail="No stocks could be analysed.")

        logger.info(f"Scored {len(score_map)} stocks")

        # ── Step 4: Screener agent picks top candidates ──────────────
        selected_tickers, screener_output = run_screener_agent(
            top_sectors, score_map, top_n=request.top_n,
        )

        # Filter to only selected tickers that were actually scored
        selected_tickers = [t for t in selected_tickers if t in quant_map]
        if not selected_tickers:
            selected_tickers = sorted(
                score_map, key=lambda t: score_map[t].final_score, reverse=True,
            )[:request.top_n]

        logger.info(f"Selected: {selected_tickers}")

        # ── Step 5: Deep analysis per candidate ──────────────────────
        results: list[StockResult] = []

        for ticker in selected_tickers:
            try:
                qd = quant_map[ticker]
                sc = score_map[ticker]
                agent_outputs: list[AgentOutput] = [sector_output, screener_output]

                # Stage 3: Fundamental agent
                fund_output = run_fundamental_agent(qd.fundamental)
                agent_outputs.append(fund_output)

                # Stage 4: Technical agent
                tech_output, tech_extras = run_technical_agent(qd.technical)
                agent_outputs.append(tech_output)

                # Stage 5: Report agent
                entry_low = tech_extras.get("entry_low")
                entry_high = tech_extras.get("entry_high")

                report_output, report_data = run_report_agent(
                    ticker=ticker,
                    score=sc,
                    fundamental_output=fund_output,
                    technical_output=tech_output,
                    atr=qd.technical.atr,
                    entry_low=entry_low,
                    entry_high=entry_high,
                )
                agent_outputs.append(report_output)

                # Build StockResult
                el = report_data.get("entry_low", entry_low or qd.technical.ema_20)
                eh = report_data.get("entry_high", entry_high or qd.technical.ema_20 * 1.02)
                sl = report_data.get("stop_loss", el - 2 * qd.technical.atr)
                tgt = report_data.get("target", eh + 2 * (eh - sl))
                mid = (el + eh) / 2
                rr = report_data.get("rr_ratio", 0)
                if rr == 0 and mid > sl and sl > 0:
                    rr = round((tgt - mid) / (mid - sl), 2)

                stock_result = StockResult(
                    ticker=ticker,
                    quant=qd,
                    score=sc,
                    entry_low=round(el, 2),
                    entry_high=round(eh, 2),
                    stop_loss=round(sl, 2),
                    target=round(tgt, 2),
                    rr_ratio=round(rr, 2),
                    agent_outputs=agent_outputs,
                )
                results.append(stock_result)
                logger.info(f"✓ {ticker}: score={sc.final_score}, verdict={sc.verdict.value}")

            except Exception as e:
                logger.error(f"Failed deep analysis for {ticker}: {e}")
                continue

        # Sort by final score descending
        results.sort(key=lambda r: r.score.final_score, reverse=True)

        return PipelineResponse(
            run_id=run_id,
            status="done",
            run_date=datetime.utcnow(),
            sectors_targeted=top_sectors,
            total_stocks_analyzed=len(quant_map),
            results=results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Pipeline run {run_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _check_index_trend() -> bool:
    """Check if S&P 500 is above its 200-day EMA."""
    try:
        df = get_index_data("^GSPC", 252)
        if df.empty or len(df) < 200:
            return True  # Assume bullish if no data

        close = df["Close"].squeeze()
        ema_200 = close.ewm(span=200, adjust=False).mean()
        return bool(close.iloc[-1] > ema_200.iloc[-1])
    except Exception:
        return True
