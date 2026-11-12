"""
Abstract Base Strategy for technical analysis signal generation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from src.data.types import Candle, Signal, SignalType
from src.indicators.trend import calculate_atr


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Enforces standardized signal structure with risk management parameters.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, candles: List[Candle], symbol: str = "NIFTY") -> List[Signal]:
        """
        Processes historical candles and generates a sequence of signals.
        """
        pass

    def get_latest_signal(self, candles: List[Candle], symbol: str = "NIFTY") -> Optional[Signal]:
        """
        Returns the signal for the latest bar, or None if no action.
        """
        signals = self.generate_signals(candles, symbol)
        return signals[-1] if signals else None

    @staticmethod
    def calculate_risk_levels(
        price: float,
        side: SignalType,
        atr_value: Optional[float] = None,
        atr_multiplier: float = 1.5,
        risk_reward_ratio: float = 2.0
    ) -> Tuple[float, float]:
        """
        Calculates dynamic Stop-Loss and Target based on ATR volatility or fixed 1% default.
        Returns: (stop_loss, target)
        """
        risk_distance = (atr_value * atr_multiplier) if (atr_value and atr_value > 0) else (price * 0.01)

        if side == SignalType.BUY:
            stop_loss = round(price - risk_distance, 2)
            target = round(price + (risk_distance * risk_reward_ratio), 2)
        elif side == SignalType.SELL:
            stop_loss = round(price + risk_distance, 2)
            target = round(price - (risk_distance * risk_reward_ratio), 2)
        else:
            stop_loss = price
            target = price

        return stop_loss, target
