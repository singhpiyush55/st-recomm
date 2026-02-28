"""
Technical indicator calculations using pandas_ta.
Input: ticker string, days of history.
Output: TechnicalSignals model.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import pandas_ta as ta

from data.fetcher import get_ohlcv
from models.schemas import TechnicalSignals


def compute_technical_signals(ticker: str, days: int = 200) -> TechnicalSignals:
    """Compute all technical indicators for a single ticker."""
    df = get_ohlcv(ticker, days)

    if df.empty or len(df) < 50:
        raise ValueError(f"Not enough price data for {ticker} ({len(df)} rows)")

    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    # ── EMAs ─────────────────────────────────────────────────────────
    ema_20 = ta.ema(close, length=20)
    ema_50 = ta.ema(close, length=50)
    ema_200 = ta.ema(close, length=200)

    # ── MACD ─────────────────────────────────────────────────────────
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    macd_line = macd.iloc[:, 0]       # MACD line
    macd_signal = macd.iloc[:, 1]     # Signal line
    macd_hist = macd.iloc[:, 2]       # Histogram

    # ── RSI ──────────────────────────────────────────────────────────
    rsi = ta.rsi(close, length=14)

    # ── Bollinger Bands ──────────────────────────────────────────────
    bbands = ta.bbands(close, length=20, std=2)
    bb_lower = bbands.iloc[:, 0]
    bb_mid = bbands.iloc[:, 1]
    bb_upper = bbands.iloc[:, 2]

    # ── ATR ──────────────────────────────────────────────────────────
    atr = ta.atr(high, low, close, length=14)

    # ── Volume spike ─────────────────────────────────────────────────
    vol_ma_20 = ta.sma(volume, length=20)
    latest_vol = _last_valid(volume)
    latest_vol_ma = _last_valid(vol_ma_20)
    volume_spike = bool(latest_vol > 1.5 * latest_vol_ma) if latest_vol_ma else False

    # ── OBV trend ────────────────────────────────────────────────────
    obv = ta.obv(close, volume)
    obv_trend = _obv_trend(obv)

    return TechnicalSignals(
        ticker=ticker,
        date=datetime.utcnow(),
        ema_20=_last_valid(ema_20),
        ema_50=_last_valid(ema_50),
        ema_200=_last_valid(ema_200, fallback=_last_valid(ema_50)),
        macd_line=_last_valid(macd_line),
        macd_signal=_last_valid(macd_signal),
        macd_histogram=_last_valid(macd_hist),
        rsi=_last_valid(rsi),
        bb_upper=_last_valid(bb_upper),
        bb_lower=_last_valid(bb_lower),
        atr=_last_valid(atr),
        volume_spike=volume_spike,
        obv_trend=obv_trend,
    )


# ── Helpers ──────────────────────────────────────────────────────────

def _last_valid(series: pd.Series | None, fallback: float = 0.0) -> float:
    """Return the last non-NaN value in a Series, or a fallback."""
    if series is None or series.empty:
        return fallback
    last = series.dropna()
    if last.empty:
        return fallback
    return float(last.iloc[-1])


def _obv_trend(obv: pd.Series | None, window: int = 10) -> str:
    """Determine OBV trend from its slope over the last `window` bars."""
    if obv is None or len(obv.dropna()) < window:
        return "flat"
    recent = obv.dropna().iloc[-window:]
    x = np.arange(len(recent))
    slope = np.polyfit(x, recent.values, 1)[0]
    if slope > 0:
        return "rising"
    elif slope < 0:
        return "falling"
    return "flat"
