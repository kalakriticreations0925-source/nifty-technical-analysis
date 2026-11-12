"""
Momentum indicators: RSI, Stochastic Oscillator, and Williams %R.
"""
from typing import List, Optional, Dict
from src.data.types import Candle


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculates Relative Strength Index (RSI) using Wilder's smoothed averages.
    Standard period: 14.
    """
    n = len(prices)
    rsi: List[Optional[float]] = [None] * n
    if n <= period:
        return rsi

    gains: List[float] = [0.0] * n
    losses: List[float] = [0.0] * n

    for i in range(1, n):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains[i] = delta
        else:
            losses[i] = abs(delta)

    # Initial average gain & loss (simple average)
    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period

    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))

    # Wilder's smoothing for subsequent values
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def calculate_stochastic(
    candles: List[Candle],
    k_period: int = 14,
    d_period: int = 3
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Stochastic Oscillator (%K and %D).
    %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
    %D = 3-period SMA of %K
    """
    n = len(candles)
    k_line: List[Optional[float]] = [None] * n
    d_line: List[Optional[float]] = [None] * n

    if n < k_period:
        return {"k": k_line, "d": d_line}

    for i in range(k_period - 1, n):
        window = candles[i - k_period + 1:i + 1]
        highest_high = max(c.high for c in window)
        lowest_low = min(c.low for c in window)
        close = candles[i].close

        rng = highest_high - lowest_low
        if rng == 0:
            k_line[i] = 50.0
        else:
            k_line[i] = 100.0 * ((close - lowest_low) / rng)

    # Calculate %D (SMA of %K)
    for i in range(k_period - 1 + d_period - 1, n):
        k_vals = [k_line[j] for j in range(i - d_period + 1, i + 1) if k_line[j] is not None]
        if len(k_vals) == d_period:
            d_line[i] = sum(k_vals) / d_period

    return {"k": k_line, "d": d_line}


def calculate_williams_r(
    candles: List[Candle],
    period: int = 14
) -> List[Optional[float]]:
    """
    Calculates Williams %R (-100 to 0).
    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    """
    n = len(candles)
    wr: List[Optional[float]] = [None] * n

    if n < period:
        return wr

    for i in range(period - 1, n):
        window = candles[i - period + 1:i + 1]
        highest_high = max(c.high for c in window)
        lowest_low = min(c.low for c in window)
        close = candles[i].close

        rng = highest_high - lowest_low
        if rng == 0:
            wr[i] = -50.0
        else:
            wr[i] = ((highest_high - close) / rng) * -100.0

    return wr
