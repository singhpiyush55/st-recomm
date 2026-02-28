"""
Centralized data fetching — every external API call goes through here.
No other file should call yfinance or requests directly.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

from data.cache import cache

# ── Sector → tickers mapping (US market) ────────────────────────────

SECTOR_ETFS: dict[str, str] = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Communication Services": "XLC",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
}

# Reasonable per-sector universe (large-cap, liquid names)
SECTOR_STOCKS: dict[str, list[str]] = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "INTC", "CSCO", "ORCL"],
    "Financials": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW", "AXP", "USB"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
    "Healthcare": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    "Industrials": ["CAT", "HON", "UNP", "BA", "RTX", "DE", "LMT", "GE", "MMM", "FDX"],
    "Communication Services": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "CMG"],
    "Consumer Staples": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "MDLZ", "KHC"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "ED", "WEC"],
    "Real Estate": ["PLD", "AMT", "CCI", "EQIX", "SPG", "PSA", "O", "WELL", "DLR", "AVB"],
    "Materials": ["LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "VMC", "MLM"],
}

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


# ── Price / OHLCV ───────────────────────────────────────────────────

def get_ohlcv(ticker: str, days: int = 200) -> pd.DataFrame:
    """Fetch OHLCV price history from yfinance. Returns a DataFrame."""
    cache_key = f"ohlcv:{ticker}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    end = datetime.now()
    start = end - timedelta(days=days)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty:
        return pd.DataFrame()

    # yfinance may return multi-level columns for single ticker – flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    cache.set(cache_key, df)
    return df


# ── Fundamentals ─────────────────────────────────────────────────────

def get_fundamentals(ticker: str) -> dict:
    """Fetch fundamental ratios from yfinance."""
    cache_key = f"fundamentals:{ticker}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    stock = yf.Ticker(ticker)
    info = stock.info or {}

    data = {
        "ticker": ticker,
        "pe_ratio": info.get("trailingPE"),
        "peg_ratio": info.get("pegRatio"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "interest_coverage": _safe_divide(
            info.get("ebitda"), info.get("interestExpense")
        ),
        "revenue_growth": info.get("revenueGrowth"),
        "eps_growth": info.get("earningsGrowth"),
        "free_cash_flow": info.get("freeCashflow"),
    }

    cache.set(cache_key, data)
    return data


# ── Sector ETF data ──────────────────────────────────────────────────

def get_sector_etf_data(etfs: Optional[list[str]] = None, days: int = 30) -> pd.DataFrame:
    """Fetch price data for sector ETFs. Returns DataFrame with one column per ETF."""
    etfs = etfs or list(SECTOR_ETFS.values())
    cache_key = f"sector_etfs:{','.join(sorted(etfs))}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    end = datetime.now()
    start = end - timedelta(days=days)
    df = yf.download(etfs, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty:
        return pd.DataFrame()

    # Keep only Adj Close / Close
    if isinstance(df.columns, pd.MultiIndex):
        if "Adj Close" in df.columns.get_level_values(0):
            df = df["Adj Close"]
        else:
            df = df["Close"]

    cache.set(cache_key, df)
    return df


# ── News headlines ───────────────────────────────────────────────────

def get_news_headlines(ticker: str, days: int = 7) -> list[str]:
    """Fetch recent news headlines from NewsAPI."""
    cache_key = f"news:{ticker}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if not NEWS_API_KEY:
        # No API key configured — return empty list gracefully
        return []

    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "from": from_date,
        "sortBy": "relevancy",
        "pageSize": 20,
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        headlines = [a["title"] for a in articles if a.get("title")]
    except Exception:
        headlines = []

    cache.set(cache_key, headlines)
    return headlines


# ── Stock universe ───────────────────────────────────────────────────

def get_stock_universe(sectors: list[str]) -> list[str]:
    """Return a list of ticker symbols for the given sectors."""
    tickers: list[str] = []
    for sector in sectors:
        tickers.extend(SECTOR_STOCKS.get(sector, []))
    # Deduplicate while preserving order
    return list(dict.fromkeys(tickers))


# ── Market index helpers ─────────────────────────────────────────────

def get_index_data(index: str = "^GSPC", days: int = 252) -> pd.DataFrame:
    """Fetch S&P 500 (or any index) OHLCV data."""
    return get_ohlcv(index, days)


# ── Utility ──────────────────────────────────────────────────────────

def _safe_divide(a, b) -> Optional[float]:
    """Divide a by b, returning None if either is None or b is zero."""
    if a is None or b is None or b == 0:
        return None
    return float(a) / float(b)
