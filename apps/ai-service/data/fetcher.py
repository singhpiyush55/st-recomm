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

# ── Sector → tickers mapping (Indian market / NSE) ──────────────────

# Nifty sectoral index tickers on yfinance
SECTOR_ETFS: dict[str, str] = {
    "IT": "^CNXIT",
    "Banking": "^NSEBANK",
    "Pharma": "^CNXPHARMA",
    "Auto": "^CNXAUTO",
    "FMCG": "^CNXFMCG",
    "Metal": "^CNXMETAL",
    "Realty": "^CNXREALTY",
    "Energy": "^CNXENERGY",
    "Infrastructure": "^CNXINFRA",
    "PSU Bank": "^CNXPSUBANK",
    "Financial Services": "^CNXFIN",
}

# ── Company name mapping for better news search ─────────────────────
TICKER_COMPANY_NAMES: dict[str, str] = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",
    "ITC.NS": "ITC Limited",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen Toubro",
    "AXISBANK.NS": "Axis Bank",
    "WIPRO.NS": "Wipro",
    "HCLTECH.NS": "HCL Technologies",
    "TATAMOTORS.NS": "Tata Motors",
    "SUNPHARMA.NS": "Sun Pharma",
    "MARUTI.NS": "Maruti Suzuki",
    "TITAN.NS": "Titan Company",
    "BAJFINANCE.NS": "Bajaj Finance",
    "ASIANPAINT.NS": "Asian Paints",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "M&M.NS": "Mahindra Mahindra",
    "TATASTEEL.NS": "Tata Steel",
    "NESTLEIND.NS": "Nestle India",
    "POWERGRID.NS": "Power Grid Corporation",
    "NTPC.NS": "NTPC Limited",
    "TECHM.NS": "Tech Mahindra",
    "DRREDDY.NS": "Dr Reddys Laboratories",
    "CIPLA.NS": "Cipla",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "ONGC.NS": "ONGC",
    "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "JSWSTEEL.NS": "JSW Steel",
    "COALINDIA.NS": "Coal India",
    "HDFCLIFE.NS": "HDFC Life Insurance",
    "SBILIFE.NS": "SBI Life Insurance",
    "BRITANNIA.NS": "Britannia Industries",
    "DIVISLAB.NS": "Divis Laboratories",
    "GRASIM.NS": "Grasim Industries",
    "INDUSINDBK.NS": "IndusInd Bank",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "BAJAJ-AUTO.NS": "Bajaj Auto",
    "EICHERMOT.NS": "Eicher Motors",
    "APOLLOHOSP.NS": "Apollo Hospitals",
    "TATACONSUM.NS": "Tata Consumer Products",
    "BPCL.NS": "Bharat Petroleum",
    "IOC.NS": "Indian Oil Corporation",
    "HINDALCO.NS": "Hindalco Industries",
    "VEDL.NS": "Vedanta",
}

# Reasonable per-sector universe (NSE large-cap, liquid names)
SECTOR_STOCKS: dict[str, list[str]] = {
    "IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS", "LTTS.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "AUROPHARMA.NS", "LUPIN.NS", "BIOCON.NS", "TORNTPHARM.NS", "ALKEM.NS", "GLENMARK.NS"],
    "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "MRF.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "DABUR.NS", "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "EMAMILTD.NS"],
    "Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COALINDIA.NS", "NMDC.NS", "SAIL.NS", "NATIONALUM.NS", "APLAPOLLO.NS", "JINDALSTEL.NS"],
    "Realty": ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "PRESTIGE.NS", "BRIGADE.NS", "SOBHA.NS", "SUNTECK.NS", "MAHLIFE.NS", "LODHA.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "NTPC.NS", "POWERGRID.NS", "GAIL.NS", "ADANIGREEN.NS", "TATAPOWER.NS", "ADANIENT.NS"],
    "Infrastructure": ["LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS", "SHREECEM.NS", "AMBUJACEM.NS", "ACC.NS", "SIEMENS.NS", "ABB.NS", "BEL.NS"],
    "PSU Bank": ["SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "IOB.NS", "CENTRALBK.NS", "INDIANB.NS", "MAHABANK.NS", "BANKINDIA.NS"],
    "Financial Services": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "HDFCLIFE.NS", "SBILIFE.NS", "ICICIPRULI.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS", "PFC.NS", "RECLTD.NS"],
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
    """Fetch price data for sector indices. Returns DataFrame with one column per index."""
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
    """Fetch recent news headlines from NewsAPI. Uses company name for Indian tickers."""
    cache_key = f"news:{ticker}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if not NEWS_API_KEY:
        # No API key configured — return empty list gracefully
        return []

    # Use company name for better news matching with Indian tickers
    query = TICKER_COMPANY_NAMES.get(ticker, ticker.replace(".NS", "").replace(".BO", ""))

    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
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

def get_index_data(index: str = "^NSEI", days: int = 252) -> pd.DataFrame:
    """Fetch Nifty 50 (or any index) OHLCV data."""
    return get_ohlcv(index, days)


# ── Utility ──────────────────────────────────────────────────────────

def _safe_divide(a, b) -> Optional[float]:
    """Divide a by b, returning None if either is None or b is zero."""
    if a is None or b is None or b == 0:
        return None
    return float(a) / float(b)
