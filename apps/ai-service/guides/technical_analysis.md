# Technical Analysis Guide for Swing Trading

This guide is injected as context into the LLM when it interprets technical indicator values. The model should use these rules to evaluate a stock's chart setup for swing trades lasting 2-6 weeks.

---

## Trend Identification

### EMA Alignment (20/50/200)
- **Full bullish alignment**: Price > EMA-20 > EMA-50 > EMA-200. This is the highest-conviction setup for long swings.
- **Partial alignment**: Price above EMA-20 and EMA-50, but below EMA-200. The short-term trend is up, but the stock hasn't reclaimed the long-term trend. Proceed with caution.
- **Bearish alignment**: Price below all three EMAs. Avoid longs. Only consider if there's a clear reversal pattern forming.
- **EMA crossover**: When EMA-20 crosses above EMA-50, this is a "golden crossover" signal. Most reliable when volume confirms.
- **Key rule**: Never fight the 200 EMA. If price is below it, the burden of proof is on the bulls.

---

## Momentum

### MACD (12, 26, 9)
- **Bullish signal**: MACD line crosses above the signal line. Strongest when it happens below zero (a reversal from oversold).
- **Histogram expansion**: When the histogram bars are growing taller (positive and increasing), momentum is accelerating. This is the best time to enter.
- **Histogram contraction**: Bars are shrinking. Momentum is fading — consider tightening stops.
- **MACD divergence**: Price makes a higher high but MACD makes a lower high. This is a bearish divergence and one of the most reliable reversal signals in swing trading.
- **Zero line**: When MACD line is above zero, the short-term trend is faster than the long-term trend. Favorable for longs.

### RSI (14-period)
- **40-60 in uptrend**: Healthy pullback zone. Best entry for swing trades when trend is intact.
- **30-40 (oversold recovery)**: Stock bouncing from oversold. Good entry if accompanied by bullish candle pattern and volume.
- **Below 30 (deeply oversold)**: Extreme. Wait for RSI to tick back above 30 before entering — catching a falling knife otherwise.
- **60-70**: Strong momentum. Acceptable to hold existing positions but risky to initiate new ones.
- **Above 70 (overbought)**: Do not initiate new longs. If already in, watch for bearish divergence or histogram contraction to exit.
- **RSI divergence**: Like MACD divergence, if price makes a higher high and RSI makes a lower high, expect a pullback.

---

## Volatility

### Bollinger Bands (20, 2)
- **Bollinger squeeze**: When upper and lower bands contract to their narrowest point in 20+ days, a big move is coming. Direction is determined by which band breaks first.
- **Breakout above upper band**: Bullish if accompanied by volume spike. The stock is breaking out of its range.
- **Walking the upper band**: When price closes above the upper band for multiple consecutive days, this is a strong uptrend — do not short this.
- **Mean reversion**: When price touches the lower band in an uptrend, it's a pullback buy opportunity. Only valid when the 200 EMA is still sloping up.
- **Band width**: If BB width (upper minus lower) is less than 5% of price, the squeeze is tight. Expect an explosive move.

### ATR (14-period)
- **ATR as stop-loss calculator**: Place stops at entry minus 2x ATR. This gives the trade enough room to breathe without being too wide.
- **ATR percent** (ATR / price x 100):
  - Below 2%: Low volatility. Good for conservative swings.
  - 2-4%: Moderate. Ideal for most swing trades.
  - Above 5%: High volatility. Reduce position size.
  - Above 8%: Extremely volatile. Avoid for swing trades.
- **ATR expansion**: Increasing ATR means a trend is strengthening. Trade in the direction of the trend.

---

## Volume Analysis

### Volume Spike
- A volume spike is defined as today's volume exceeding 1.5x the 20-day average volume.
- **Volume spike on up day**: Institutional buying. Strong bullish confirmation.
- **Volume spike on down day**: Institutional selling. Warning signal even if indicators are bullish.
- **Low volume rally**: Price rising on below-average volume is suspicious. The move lacks conviction and is likely to reverse.

### OBV (On-Balance Volume) Trend
- **Rising OBV with rising price**: Confirms the uptrend. Smart money is accumulating.
- **Rising OBV with flat price**: Accumulation phase. Expect a breakout soon.
- **Falling OBV with rising price**: Distribution. Smart money is selling into strength. The rally is fake.
- **Falling OBV with falling price**: Confirms the downtrend. Stay away.

---

## High-Conviction Setups (combinations)

### Bull Flag
- Ingredients: Prior strong rally (pole), tight consolidation on declining volume (flag), breakout above flag resistance on volume spike.
- EMA alignment must be bullish. RSI should be 40-60 during the flag portion.
- Target: measure the pole height and project from breakout point.

### MACD + EMA Golden Cross
- EMA-20 crosses above EMA-50 while MACD crosses above signal line. If both happen within the same week, conviction is high.
- Must be confirmed by volume above 20-day average.

### Bollinger Squeeze Breakout
- Bands contract to narrowest in 20 days. Price breaks above upper band with a volume spike. MACD histogram turns positive. RSI between 50-65.
- This is the highest-probability swing setup when all four conditions align.

### Oversold Bounce
- RSI drops below 30, then crosses back above 30. MACD histogram starts expanding (less negative). Price holds above 200 EMA.
- Enter on the first green day after RSI crosses 30. Stop at the recent low.

---

## How to Structure Your Analysis
1. Start with the verdict: Strong, Medium, or Weak
2. Describe the current trend using EMA alignment
3. Identify the key momentum signal (MACD or RSI)
4. Note volume behavior (confirming or diverging)
5. Suggest an entry zone and justify it
6. Keep the narrative to 3-4 sentences — concise and actionable
