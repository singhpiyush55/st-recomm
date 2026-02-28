"""
Risk metrics: beta, Sharpe ratio, max drawdown, ATR percent.
Input: ticker string.
Output: RiskMetrics model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from data.fetcher import get_ohlcv, get_index_data
from models.schemas import RiskMetrics


def compute_risk_metrics(ticker: str, days: int = 180) -> RiskMetrics:
    """Compute risk metrics for a single ticker over ~6 months of data."""
    df = get_ohlcv(ticker, days)
    index_df = get_index_data("^GSPC", days)

    if df.empty or len(df) < 20:
        return _default_risk(ticker)

    close = df["Close"].squeeze()
    stock_returns = close.pct_change().dropna()

    # ── Beta ─────────────────────────────────────────────────────────
    beta = _compute_beta(stock_returns, index_df)

    # ── Sharpe ratio ─────────────────────────────────────────────────
    sharpe = _compute_sharpe(stock_returns)

    # ── Max drawdown ─────────────────────────────────────────────────
    max_dd = _compute_max_drawdown(close)

    # ── ATR percent ──────────────────────────────────────────────────
    atr_pct = _compute_atr_percent(df)

    return RiskMetrics(
        ticker=ticker,
        beta=round(beta, 3),
        sharpe_ratio=round(sharpe, 3),
        max_drawdown=round(max_dd, 3),
        atr_percent=round(atr_pct, 3),
    )


# ── Component calculations ──────────────────────────────────────────

def _compute_beta(stock_returns: pd.Series, index_df: pd.DataFrame) -> float:
    """Beta = covariance(stock, market) / variance(market)."""
    if index_df.empty:
        return 1.0

    index_close = index_df["Close"].squeeze()
    market_returns = index_close.pct_change().dropna()

    # Align by date
    aligned = pd.DataFrame({
        "stock": stock_returns,
        "market": market_returns,
    }).dropna()

    if len(aligned) < 20:
        return 1.0

    cov = aligned["stock"].cov(aligned["market"])
    var = aligned["market"].var()

    if var == 0:
        return 1.0

    return float(cov / var)


def _compute_sharpe(returns: pd.Series, risk_free_annual: float = 0.05) -> float:
    """Annualized Sharpe ratio = (mean daily return - rf) / std * sqrt(252)."""
    if len(returns) < 20 or returns.std() == 0:
        return 0.0

    daily_rf = risk_free_annual / 252
    excess = returns.mean() - daily_rf
    return float((excess / returns.std()) * np.sqrt(252))


def _compute_max_drawdown(close: pd.Series) -> float:
    """Largest peak-to-trough percentage drop."""
    if len(close) < 2:
        return 0.0

    cummax = close.cummax()
    drawdown = (close - cummax) / cummax
    return float(abs(drawdown.min()))


def _compute_atr_percent(df: pd.DataFrame) -> float:
    """ATR (14-period) as a percentage of the current price."""
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    close = df["Close"].squeeze()

    if len(close) < 15:
        return 0.0

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()

    latest_atr = atr.dropna().iloc[-1] if not atr.dropna().empty else 0.0
    latest_price = close.iloc[-1]

    if latest_price == 0:
        return 0.0

    return float((latest_atr / latest_price) * 100)


def _default_risk(ticker: str) -> RiskMetrics:
    """Fallback when data is insufficient."""
    return RiskMetrics(
        ticker=ticker,
        beta=1.0,
        sharpe_ratio=0.0,
        max_drawdown=0.0,
        atr_percent=0.0,
    )
