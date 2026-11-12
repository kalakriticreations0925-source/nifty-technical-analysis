"""
Strategies package exports.
"""
from src.strategies.base import BaseStrategy
from src.strategies.supertrend_rsi import SupertrendRSIStrategy
from src.strategies.macd_bollinger import MACDBollingerStrategy
from src.strategies.ema_crossover import EMACrossoverStrategy
from src.strategies.confluence import MultiFactorConfluenceStrategy

__all__ = [
    "BaseStrategy",
    "SupertrendRSIStrategy",
    "MACDBollingerStrategy",
    "EMACrossoverStrategy",
    "MultiFactorConfluenceStrategy"
]
