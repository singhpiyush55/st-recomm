"""
Weighted scoring engine — pure function, no LLM calls.
Input: QuantData for one stock (+ sector rankings for context).
Output: ScoreResult with final 0-100 score and 5 component scores.
"""

from __future__ import annotations

from models.schemas import QuantData, ScoreResult, SectorRanking, Verdict


def score_stock(
    quant: QuantData,
    sector_rankings: list[SectorRanking] | None = None,
    index_above_200ema: bool = False,
) -> ScoreResult:
    """
    Compute a 0-100 composite score for a single stock.

    Components:
      Technical   — max 40 pts
      Fundamental — max 30 pts
      Sector      — max 15 pts
      Sentiment   — max 10 pts
      Risk penalty — subtract up to 5 pts
    """
    tech = _technical_score(quant)
    fund = _fundamental_score(quant)
    sector = _sector_score(quant, sector_rankings, index_above_200ema)
    sent = _sentiment_score(quant)
    risk = _risk_penalty(quant)

    raw = tech + fund + sector + sent - risk
    final = max(0.0, min(100.0, raw))

    return ScoreResult(
        tech_score=round(tech, 2),
        fund_score=round(fund, 2),
        sector_score=round(sector, 2),
        sentiment_score=round(sent, 2),
        risk_penalty=round(risk, 2),
        final_score=round(final, 2),
        verdict=_verdict(final),
    )


# ── Technical score (max 40) ────────────────────────────────────────

def _technical_score(q: QuantData) -> float:
    t = q.technical
    pts = 0.0

    # EMA alignment (12 pts): 20 > 50, price above 200
    price_proxy = t.ema_20  # Use EMA-20 as proxy for current price
    if t.ema_20 > t.ema_50:
        pts += 6.0
    if price_proxy > t.ema_200 and t.ema_200 > 0:
        pts += 6.0

    # MACD (10 pts): histogram expanding, line above signal
    if t.macd_line > t.macd_signal:
        pts += 5.0
    if t.macd_histogram > 0:
        pts += 3.0
    # Histogram expanding (current > 0 and positive momentum)
    if t.macd_histogram > 0 and t.macd_line > 0:
        pts += 2.0

    # RSI (8 pts): 40-60 in uptrend = full, oversold recovery = partial
    if 40 <= t.rsi <= 60 and t.ema_20 > t.ema_50:
        pts += 8.0
    elif 30 <= t.rsi < 40:
        # Oversold recovery zone
        pts += 5.0
    elif 60 < t.rsi <= 70:
        # Still has momentum
        pts += 4.0
    elif t.rsi > 70:
        # Overbought — less points
        pts += 2.0

    # Bollinger Bands (5 pts): breakout above upper with squeeze
    bb_width = t.bb_upper - t.bb_lower
    if bb_width > 0 and price_proxy > t.bb_upper:
        pts += 5.0
    elif bb_width > 0 and price_proxy > (t.bb_lower + t.bb_upper) / 2:
        pts += 2.0

    # Volume (5 pts): spike on up day
    if t.volume_spike:
        pts += 3.0
    if t.obv_trend == "rising":
        pts += 2.0

    return min(40.0, pts)


# ── Fundamental score (max 30) ──────────────────────────────────────

def _fundamental_score(q: QuantData) -> float:
    f = q.fundamental
    pts = 0.0

    # ROE > 15% (6 pts)
    if f.roe is not None:
        if f.roe > 0.20:
            pts += 6.0
        elif f.roe > 0.15:
            pts += 5.0
        elif f.roe > 0.10:
            pts += 3.0

    # Revenue growth (6 pts)
    if f.revenue_growth is not None:
        if f.revenue_growth > 0.20:
            pts += 6.0
        elif f.revenue_growth > 0.10:
            pts += 4.0
        elif f.revenue_growth > 0.0:
            pts += 2.0

    # EPS growth positive and strong (6 pts)
    if f.eps_growth is not None:
        if f.eps_growth > 0.20:
            pts += 6.0
        elif f.eps_growth > 0.10:
            pts += 4.0
        elif f.eps_growth > 0.0:
            pts += 2.0

    # PEG < 1 (6 pts)
    if f.peg_ratio is not None:
        if 0 < f.peg_ratio < 1:
            pts += 6.0
        elif 1 <= f.peg_ratio < 1.5:
            pts += 4.0
        elif 1.5 <= f.peg_ratio < 2:
            pts += 2.0

    # Debt/equity < 1 (6 pts)
    if f.debt_to_equity is not None:
        if f.debt_to_equity < 0.5:
            pts += 6.0
        elif f.debt_to_equity < 1.0:
            pts += 4.0
        elif f.debt_to_equity < 1.5:
            pts += 2.0

    return min(30.0, pts)


# ── Sector score (max 15) ───────────────────────────────────────────

def _sector_score(
    q: QuantData,
    rankings: list[SectorRanking] | None,
    index_above_200ema: bool,
) -> float:
    if not rankings:
        return 7.5  # Neutral when no data

    pts = 0.0

    # Find which sector the stock belongs to
    from data.fetcher import SECTOR_STOCKS
    stock_sector: str | None = None
    for sector, tickers in SECTOR_STOCKS.items():
        if q.ticker in tickers:
            stock_sector = sector
            break

    if stock_sector:
        for r in rankings:
            if r.sector == stock_sector:
                if r.rank <= 3:
                    pts += 12.0
                elif r.rank <= 5:
                    pts += 8.0
                elif r.rank <= 7:
                    pts += 4.0
                break

    # Bonus for market trend
    if index_above_200ema:
        pts += 3.0

    return min(15.0, pts)


# ── Sentiment score (max 10) ────────────────────────────────────────

def _sentiment_score(q: QuantData) -> float:
    s = q.sentiment.news_score

    if s > 0.5:
        return 10.0
    elif s > 0.25:
        return 7.0
    elif s > 0.0:
        return 4.0
    elif s == 0.0:
        return 2.0  # Neutral / no data
    else:
        return 0.0


# ── Risk penalty (subtract up to 5) ────────────────────────────────

def _risk_penalty(q: QuantData) -> float:
    r = q.risk
    penalty = 0.0

    # Beta > 1.5
    if r.beta > 2.0:
        penalty += 2.0
    elif r.beta > 1.5:
        penalty += 1.0

    # Max drawdown > 30%
    if r.max_drawdown > 0.40:
        penalty += 2.0
    elif r.max_drawdown > 0.30:
        penalty += 1.0

    # ATR percent > 5% (too volatile)
    if r.atr_percent > 7.0:
        penalty += 1.0
    elif r.atr_percent > 5.0:
        penalty += 0.5

    return min(5.0, penalty)


# ── Verdict ──────────────────────────────────────────────────────────

def _verdict(score: float) -> Verdict:
    if score >= 80:
        return Verdict.STRONG_BUY
    elif score >= 65:
        return Verdict.MEDIUM_BUY
    elif score >= 50:
        return Verdict.WEAK_BUY
    return Verdict.AVOID
