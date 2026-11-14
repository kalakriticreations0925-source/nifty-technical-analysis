"""
MACD + Bollinger Bands Volatility & Breakout Strategy.
"""
from typing import List
from src.data.types import Candle, Signal, SignalType
from src.strategies.base import BaseStrategy
from src.indicators.trend import calculate_macd, calculate_atr
from src.indicators.volatility import calculate_bollinger_bands


class MACDBollingerStrategy(BaseStrategy):
    """
    Combines Bollinger Bands volatility boundaries with MACD momentum crossovers:
    - BUY: Price breaks above Bollinger Middle Band or rebounds from Lower Band, confirmed by MACD crossing above Signal line.
    - SELL: Price breaks below Bollinger Middle Band or falls from Upper Band, confirmed by MACD crossing below Signal line.
    """
    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9
    ):
        super().__init__(name="MACD_Bollinger")
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def generate_signals(self, candles: List[Candle], symbol: str = "NIFTY") -> List[Signal]:
        n = len(candles)
        if n < self.macd_slow + self.macd_signal + 2:
            return []

        prices = [c.close for c in candles]
        bb = calculate_bollinger_bands(prices, self.bb_period, self.bb_std)
        macd_data = calculate_macd(prices, self.macd_fast, self.macd_slow, self.macd_signal)
        atr_vals = calculate_atr(candles, 14)

        macd = macd_data["macd"]
        signal_line = macd_data["signal"]
        hist = macd_data["histogram"]

        signals: List[Signal] = []
        current_state = SignalType.HOLD

        for i in range(1, n):
            m_curr, m_prev = macd[i], macd[i - 1]
            s_curr, s_prev = signal_line[i], signal_line[i - 1]
            h_curr, h_prev = hist[i], hist[i - 1]
            c = candles[i]
            mid = bb["middle"][i]
            upper = bb["upper"][i]
            lower = bb["lower"][i]
            pct_b = bb["percent_b"][i]
            atr = atr_vals[i]

            if any(v is None for v in [m_curr, m_prev, s_curr, s_prev, h_curr, h_prev, mid, upper, lower, pct_b]):
                continue

            # Bullish MACD Crossover
            macd_bullish_cross = (m_prev <= s_prev) and (m_curr > s_curr)
            # Bearish MACD Crossover
            macd_bearish_cross = (m_prev >= s_prev) and (m_curr < s_curr)

            sig_type = SignalType.HOLD
            confidence = 0.5
            rationale = ""

            if macd_bullish_cross:
                # Strong buy if close is above middle band or bouncing off lower band
                if c.close > mid and pct_b < 0.95:
                    sig_type = SignalType.BUY
                    confidence = 0.80
                    rationale = f"Bullish MACD crossover with price ({c.close:.1f}) above Bollinger Mid Band."
                elif pct_b <= 0.20:
                    sig_type = SignalType.BUY
                    confidence = 0.75
                    rationale = f"Bullish MACD crossover while price is in lower Bollinger oversold zone (%B: {pct_b:.2f})."

            elif macd_bearish_cross:
                if c.close < mid and pct_b > 0.05:
                    sig_type = SignalType.SELL
                    confidence = 0.80
                    rationale = f"Bearish MACD crossover with price ({c.close:.1f}) below Bollinger Mid Band."
                elif pct_b >= 0.80:
                    sig_type = SignalType.SELL
                    confidence = 0.75
                    rationale = f"Bearish MACD crossover while price is in upper Bollinger overbought zone (%B: {pct_b:.2f})."

            if sig_type in (SignalType.BUY, SignalType.SELL) and sig_type != current_state:
                current_state = sig_type
                stop_loss, target = self.calculate_risk_levels(c.close, sig_type, atr, atr_multiplier=1.5, risk_reward_ratio=1.0)

                signals.append(Signal(
                    symbol=symbol,
                    timestamp=c.timestamp,
                    signal_type=sig_type,
                    price=round(c.close, 2),
                    stop_loss=stop_loss,
                    target=target,
                    strategy_name=self.name,
                    confidence=confidence,
                    indicators={
                        "MACD": round(m_curr, 2),
                        "Signal": round(s_curr, 2),
                        "Histogram": round(h_curr, 2),
                        "BB_Upper": round(upper, 2),
                        "BB_Middle": round(mid, 2),
                        "BB_Lower": round(lower, 2),
                        "Percent_B": round(pct_b, 2)
                    },
                    rationale=rationale
                ))

        return signals
