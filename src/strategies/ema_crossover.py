"""
EMA Trend Crossover Strategy (e.g. 9/21 EMA or 20/50 EMA).
"""
from typing import List, Optional
from src.data.types import Candle, Signal, SignalType
from src.strategies.base import BaseStrategy
from src.indicators.trend import calculate_ema, calculate_atr


class EMACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover:
    - BUY when Fast EMA crosses above Slow EMA (Golden Cross).
    - SELL when Fast EMA crosses below Slow EMA (Death Cross).
    - Trend Filter: Uses long-term EMA (200 EMA if available) to filter counter-trend trades.
    """
    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
        trend_period: int = 200
    ):
        super().__init__(name="EMA_Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.trend_period = trend_period

    def generate_signals(self, candles: List[Candle], symbol: str = "NIFTY") -> List[Signal]:
        n = len(candles)
        if n < self.slow_period + 2:
            return []

        prices = [c.close for c in candles]
        fast_ema = calculate_ema(prices, self.fast_period)
        slow_ema = calculate_ema(prices, self.slow_period)
        trend_ema = calculate_ema(prices, self.trend_period) if n >= self.trend_period else [None] * n
        atr_vals = calculate_atr(candles, 14)

        signals: List[Signal] = []
        current_state = SignalType.HOLD

        for i in range(1, n):
            f_curr, f_prev = fast_ema[i], fast_ema[i - 1]
            s_curr, s_prev = slow_ema[i], slow_ema[i - 1]
            t_curr = trend_ema[i]
            c = candles[i]
            atr = atr_vals[i]

            if f_curr is None or f_prev is None or s_curr is None or s_prev is None:
                continue

            bullish_cross = (f_prev <= s_prev) and (f_curr > s_curr)
            bearish_cross = (f_prev >= s_prev) and (f_curr < s_curr)

            sig_type = SignalType.HOLD
            confidence = 0.5
            rationale = ""

            if bullish_cross:
                if t_curr and c.close > t_curr:
                    sig_type = SignalType.BUY
                    confidence = 0.85
                    rationale = f"Bullish {self.fast_period}/{self.slow_period} EMA crossover aligned with major 200 EMA uptrend."
                else:
                    sig_type = SignalType.BUY
                    confidence = 0.70
                    rationale = f"Bullish {self.fast_period}/{self.slow_period} EMA crossover."

            elif bearish_cross:
                if t_curr and c.close < t_curr:
                    sig_type = SignalType.SELL
                    confidence = 0.85
                    rationale = f"Bearish {self.fast_period}/{self.slow_period} EMA crossover aligned with major 200 EMA downtrend."
                else:
                    sig_type = SignalType.SELL
                    confidence = 0.70
                    rationale = f"Bearish {self.fast_period}/{self.slow_period} EMA crossover."

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
                        f"EMA_{self.fast_period}": round(f_curr, 2),
                        f"EMA_{self.slow_period}": round(s_curr, 2),
                        "EMA_Trend": round(t_curr, 2) if t_curr else 0.0,
                        "ATR": round(atr, 2) if atr else 0.0
                    },
                    rationale=rationale
                ))

        return signals
