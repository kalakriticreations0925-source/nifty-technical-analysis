"""
Volatility indicators: Bollinger Bands and Keltner Channels.
"""
from typing import List, Optional, Dict
import math
from src.data.types import Candle
from src.indicators.trend import calculate_sma, calculate_ema, calculate_atr


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    num_std: float = 2.0
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Bollinger Bands.
    Middle Band = 20 SMA
    Upper Band = Middle + (num_std * standard_deviation)
    Lower Band = Middle - (num_std * standard_deviation)
    Bandwidth = (Upper - Lower) / Middle
    %B = (Price - Lower) / (Upper - Lower)
    """
    n = len(prices)
    middle = calculate_sma(prices, period)

    upper: List[Optional[float]] = [None] * n
    lower: List[Optional[float]] = [None] * n
    bandwidth: List[Optional[float]] = [None] * n
    percent_b: List[Optional[float]] = [None] * n

    for i in range(period - 1, n):
        m = middle[i]
        if m is not None:
            window = prices[i - period + 1:i + 1]
            mean = m
            variance = sum((x - mean) ** 2 for x in window) / period
            std_dev = math.sqrt(variance)

            up = mean + (num_std * std_dev)
            low = mean - (num_std * std_dev)

            upper[i] = up
            lower[i] = low

            if mean > 0:
                bandwidth[i] = (up - low) / mean
            if (up - low) > 0:
                percent_b[i] = (prices[i] - low) / (up - low)

    return {
        "middle": middle,
        "upper": upper,
        "lower": lower,
        "bandwidth": bandwidth,
        "percent_b": percent_b
    }


def calculate_keltner_channels(
    candles: List[Candle],
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Keltner Channels.
    Middle Band = 20 EMA
    Upper Band = Middle + (multiplier * ATR)
    Lower Band = Middle - (multiplier * ATR)
    """
    prices = [c.close for c in candles]
    middle = calculate_ema(prices, ema_period)
    atr = calculate_atr(candles, atr_period)

    n = len(candles)
    upper: List[Optional[float]] = [None] * n
    lower: List[Optional[float]] = [None] * n

    for i in range(n):
        m = middle[i]
        a = atr[i]
        if m is not None and a is not None:
            upper[i] = m + (multiplier * a)
            lower[i] = m - (multiplier * a)

    return {
        "middle": middle,
        "upper": upper,
        "lower": lower
    }
