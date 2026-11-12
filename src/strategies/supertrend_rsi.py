"""
Supertrend + RSI Trend Following Strategy.
Widely used for Nifty and Bank Nifty intraday and swing trading.
"""
from typing import List
from src.data.types import Candle, Signal, SignalType
from src.strategies.base import BaseStrategy
from src.indicators.trend import calculate_supertrend, calculate_atr
from src.indicators.momentum import calculate_rsi


class SupertrendRSIStrategy(BaseStrategy):
    """
    Supertrend & RSI confluence strategy:
    - BUY when Supertrend turns Bullish (+1) AND RSI > 50 (momentum confirmed, RSI < 75).
    - SELL when Supertrend turns Bearish (-1) AND RSI < 50 (momentum confirmed, RSI > 25).
    """
    def __init__(
        self,
        st_period: int = 10,
        st_multiplier: float = 3.0,
        rsi_period: int = 14,
        rsi_buy_min: float = 50.0,
        rsi_buy_max: float = 75.0,
        rsi_sell_max: float = 50.0,
        rsi_sell_min: float = 25.0
    ):
        super().__init__(name="Supertrend_RSI")
        self.st_period = st_period
        self.st_multiplier = st_multiplier
        self.rsi_period = rsi_period
        self.rsi_buy_min = rsi_buy_min
        self.rsi_buy_max = rsi_buy_max
        self.rsi_sell_max = rsi_sell_max
        self.rsi_sell_min = rsi_sell_min

    def generate_signals(self, candles: List[Candle], symbol: str = "NIFTY") -> List[Signal]:
        n = len(candles)
        if n < max(self.st_period, self.rsi_period) + 2:
            return []

        prices = [c.close for c in candles]
        st_data = calculate_supertrend(candles, self.st_period, self.st_multiplier)
        directions = st_data["direction"]
        st_lines = st_data["supertrend"]
        rsi_vals = calculate_rsi(prices, self.rsi_period)
        atr_vals = calculate_atr(candles, 14)

        signals: List[Signal] = []
        current_state = SignalType.HOLD

        for i in range(1, n):
            curr_dir = directions[i]
            prev_dir = directions[i - 1]
            curr_rsi = rsi_vals[i]
            curr_st = st_lines[i]
            curr_atr = atr_vals[i]
            c = candles[i]

            if curr_dir is None or prev_dir is None or curr_rsi is None:
                continue

            # Check Supertrend Flip or continuation with momentum
            bullish_flip = (curr_dir == 1 and prev_dir == -1)
            bearish_flip = (curr_dir == -1 and prev_dir == 1)

            sig_type = SignalType.HOLD
            confidence = 0.5
            rationale = ""

            if bullish_flip:
                if self.rsi_buy_min <= curr_rsi <= self.rsi_buy_max:
                    sig_type = SignalType.BUY
                    confidence = 0.85
                    rationale = f"Supertrend flipped Bullish and RSI ({curr_rsi:.1f}) confirms upward momentum."
                elif curr_rsi > self.rsi_buy_max:
                    sig_type = SignalType.HOLD
                    rationale = f"Supertrend flipped Bullish, but RSI ({curr_rsi:.1f}) is heavily overbought."
                else:
                    sig_type = SignalType.BUY
                    confidence = 0.65
                    rationale = f"Supertrend Bullish flip with moderate RSI ({curr_rsi:.1f})."

            elif bearish_flip:
                if self.rsi_sell_min <= curr_rsi <= self.rsi_sell_max:
                    sig_type = SignalType.SELL
                    confidence = 0.85
                    rationale = f"Supertrend flipped Bearish and RSI ({curr_rsi:.1f}) confirms downward momentum."
                elif curr_rsi < self.rsi_sell_min:
                    sig_type = SignalType.HOLD
                    rationale = f"Supertrend flipped Bearish, but RSI ({curr_rsi:.1f}) is heavily oversold."
                else:
                    sig_type = SignalType.SELL
                    confidence = 0.65
                    rationale = f"Supertrend Bearish flip with moderate RSI ({curr_rsi:.1f})."

            # If signal generated and changes state
            if sig_type in (SignalType.BUY, SignalType.SELL) and sig_type != current_state:
                current_state = sig_type
                # Stop loss based on Supertrend line or ATR
                if sig_type == SignalType.BUY:
                    stop_loss = round(curr_st, 2) if curr_st and curr_st < c.close else round(c.close - (curr_atr * 1.5 if curr_atr else c.close * 0.01), 2)
                    risk = c.close - stop_loss
                    target = round(c.close + (risk * 2.0), 2)
                else:
                    stop_loss = round(curr_st, 2) if curr_st and curr_st > c.close else round(c.close + (curr_atr * 1.5 if curr_atr else c.close * 0.01), 2)
                    risk = stop_loss - c.close
                    target = round(c.close - (risk * 2.0), 2)

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
                        "Supertrend": round(curr_st, 2) if curr_st else 0.0,
                        "RSI": round(curr_rsi, 2),
                        "ATR": round(curr_atr, 2) if curr_atr else 0.0
                    },
                    rationale=rationale
                ))

        return signals
