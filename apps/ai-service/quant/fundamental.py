"""
Fundamental ratio fetching using yfinance.
Input: ticker string.
Output: FundamentalRatios model.
"""

from __future__ import annotations

from data.fetcher import get_fundamentals
from models.schemas import FundamentalRatios


def compute_fundamental_ratios(ticker: str) -> FundamentalRatios:
    """Fetch and return fundamental ratios for a single ticker."""
    data = get_fundamentals(ticker)

    # Debt/equity from yfinance comes as a percentage (e.g. 150 meaning 1.5)
    # Normalize to a ratio if it seems like a percentage
    de = data.get("debt_to_equity")
    if de is not None and de > 10:
        de = de / 100.0

    return FundamentalRatios(
        ticker=ticker,
        pe_ratio=_to_float(data.get("pe_ratio")),
        peg_ratio=_to_float(data.get("peg_ratio")),
        roe=_to_float(data.get("roe")),
        roa=_to_float(data.get("roa")),
        debt_to_equity=_to_float(de),
        interest_coverage=_to_float(data.get("interest_coverage")),
        revenue_growth=_to_float(data.get("revenue_growth")),
        eps_growth=_to_float(data.get("eps_growth")),
        free_cash_flow=_to_float(data.get("free_cash_flow")),
    )


def _to_float(val) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        f = float(val)
        # yfinance sometimes returns inf / nan
        if f != f or f == float("inf") or f == float("-inf"):
            return None
        return f
    except (ValueError, TypeError):
        return None
