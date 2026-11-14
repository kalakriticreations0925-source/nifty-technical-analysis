"""
Multi-Factor Technical Confluence Strategy.
Combines Trend, Momentum, Volatility, and Volume into an ensemble confidence score.
"""
from typing import List, Dict, Any
from src.data.types import Candle, Signal, SignalType
from src.strategies.base import BaseStrategy
from src.indicators.trend import calculate_supertrend, calculate_ema, calculate_macd, calculate_adx, calculate_atr
from src.indicators.momentum import calculate_rsi, calculate_stochastic
from src.indicators.volatility import calculate_bollinger_bands
from src.indicators.volume import calculate_volume_ratio, calculate_obv


class MultiFactorConfluenceStrategy(BaseStrategy):
    """
    Flagship Ensemble Technical Analysis Engine.
    Evaluates 4 pillars of Market Technicals:
      1. Trend (35% weight): Supertrend + 20/50/200 EMA + ADX
      2. Momentum (25% weight): RSI + MACD Histogram
      3. Volatility (20% weight): Bollinger Bands %B & Squeeze
      4. Volume (20% weight): Volume Surge Ratio + OBV Trend

    Requires >= 70% Confluence Score to trigger Buy or Sell Signal.
    """
    def __init__(self, threshold: float = 0.70):
        super().__init__(name="MultiFactor_Confluence")
        self.threshold = threshold

    def generate_signals(self, candles: List[Candle], symbol: str = "NIFTY") -> List[Signal]:
        n = len(candles)
        if n < 35:
            return []

        prices = [c.close for c in candles]

        # Calculate all underlying indicators
        st_data = calculate_supertrend(candles, period=10, multiplier=3.0)
        ema_20 = calculate_ema(prices, 20)
        ema_50 = calculate_ema(prices, 50)
        adx_data = calculate_adx(candles, 14)
        rsi = calculate_rsi(prices, 14)
        macd_data = calculate_macd(prices, 12, 26, 9)
        bb = calculate_bollinger_bands(prices, 20, 2.0)
        vol_ratios = calculate_volume_ratio(candles, 20)
        obv = calculate_obv(candles)
        atr_vals = calculate_atr(candles, 14)

        signals: List[Signal] = []
        current_state = SignalType.HOLD

        for i in range(20, n):
            c = candles[i]
            close = c.close

            # Skip if essential indicators not ready
            if rsi[i] is None or macd_data["histogram"][i] is None or st_data["direction"][i] is None:
                continue

            bullish_points = 0.0
            bearish_points = 0.0
            reasons = []

            # --- 1. TREND (35 points max) ---
            # Supertrend (15 pts)
            st_dir = st_data["direction"][i]
            if st_dir == 1:
                bullish_points += 15
                reasons.append("Supertrend Bullish")
            elif st_dir == -1:
                bearish_points += 15
                reasons.append("Supertrend Bearish")

            # EMA Alignment (12 pts)
            e20 = ema_20[i]
            e50 = ema_50[i]
            if e20 and close > e20:
                bullish_points += 6
            elif e20 and close < e20:
                bearish_points += 6

            if e20 and e50 and e20 > e50:
                bullish_points += 6
                reasons.append("20 EMA > 50 EMA")
            elif e20 and e50 and e20 < e50:
                bearish_points += 6
                reasons.append("20 EMA < 50 EMA")

            # ADX Trend Strength (8 pts)
            adx_val = adx_data["adx"][i]
            plus_di = adx_data["plus_di"][i]
            minus_di = adx_data["minus_di"][i]
            if adx_val and adx_val > 22:
                if plus_di and minus_di and plus_di > minus_di:
                    bullish_points += 8
                    reasons.append(f"ADX Trending Bullish ({adx_val:.1f})")
                elif plus_di and minus_di and minus_di > plus_di:
                    bearish_points += 8
                    reasons.append(f"ADX Trending Bearish ({adx_val:.1f})")

            # --- 2. MOMENTUM (25 points max) ---
            # RSI (13 pts)
            r = rsi[i]
            if 52 <= r <= 72:
                bullish_points += 13
                reasons.append(f"RSI Bullish Momentum ({r:.1f})")
            elif 28 <= r <= 48:
                bearish_points += 13
                reasons.append(f"RSI Bearish Momentum ({r:.1f})")

            # MACD Histogram (12 pts)
            hist_curr = macd_data["histogram"][i]
            hist_prev = macd_data["histogram"][i - 1] if i > 0 and macd_data["histogram"][i - 1] is not None else 0.0
            if hist_curr > 0:
                bullish_points += 8
                if hist_curr > hist_prev:
                    bullish_points += 4
                    reasons.append("MACD Histogram expanding positive")
            elif hist_curr < 0:
                bearish_points += 8
                if hist_curr < hist_prev:
                    bearish_points += 4
                    reasons.append("MACD Histogram expanding negative")

            # --- 3. VOLATILITY (20 points max) ---
            # Bollinger Bands %B (20 pts)
            pct_b = bb["percent_b"][i]
            if pct_b is not None:
                if 0.50 < pct_b < 0.90:
                    bullish_points += 20
                    reasons.append(f"Price in upper Bollinger territory (%B: {pct_b:.2f})")
                elif 0.10 < pct_b < 0.50:
                    bearish_points += 20
                    reasons.append(f"Price in lower Bollinger territory (%B: {pct_b:.2f})")

            # --- 4. VOLUME (20 points max) ---
            # Volume surge ratio (12 pts)
            vol_ratio = vol_ratios[i]
            if vol_ratio and vol_ratio >= 1.2:
                if close > candles[i].open:
                    bullish_points += 12
                    reasons.append(f"Above-average volume surge ({vol_ratio}x)")
                else:
                    bearish_points += 12
                    reasons.append(f"Above-average sell volume ({vol_ratio}x)")
            else:
                bullish_points += 5
                bearish_points += 5

            # OBV slope (8 pts)
            if i >= 3 and obv[i] > obv[i - 3]:
                bullish_points += 8
            elif i >= 3 and obv[i] < obv[i - 3]:
                bearish_points += 8

            # Calculate total confidence (0.0 to 1.0)
            bullish_score = round(bullish_points / 100.0, 2)
            bearish_score = round(bearish_points / 100.0, 2)

            sig_type = SignalType.HOLD
            confidence = 0.0
            selected_reasons = []

            if bullish_score >= self.threshold and bullish_score > bearish_score:
                sig_type = SignalType.BUY
                confidence = bullish_score
                selected_reasons = reasons
            elif bearish_score >= self.threshold and bearish_score > bullish_score:
                sig_type = SignalType.SELL
                confidence = bearish_score
                selected_reasons = reasons

            if sig_type in (SignalType.BUY, SignalType.SELL) and sig_type != current_state:
                current_state = sig_type
                atr = atr_vals[i]
                stop_loss, target = self.calculate_risk_levels(
                    close, sig_type, atr, atr_multiplier=1.5, risk_reward_ratio=1.0
                )

                rationale = f"Confidence {int(confidence * 100)}% based on: " + "; ".join(selected_reasons[:4])

                signals.append(Signal(
                    symbol=symbol,
                    timestamp=c.timestamp,
                    signal_type=sig_type,
                    price=round(close, 2),
                    stop_loss=stop_loss,
                    target=target,
                    strategy_name=self.name,
                    confidence=confidence,
                    indicators={
                        "RSI": round(r, 1),
                        "Supertrend_Dir": st_dir,
                        "MACD_Hist": round(hist_curr, 2),
                        "ADX": round(adx_val, 1) if adx_val else 0.0,
                        "Percent_B": round(pct_b, 2) if pct_b else 0.0,
                        "Volume_Ratio": vol_ratio if vol_ratio else 1.0
                    },
                    rationale=rationale
                ))

        return signals
