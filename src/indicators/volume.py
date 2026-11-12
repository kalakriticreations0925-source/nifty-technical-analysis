"""
Volume indicators: VWAP, OBV, and Volume Surge Ratio.
"""
from typing import List, Optional
from src.data.types import Candle
from src.indicators.trend import calculate_sma


def calculate_vwap(candles: List[Candle]) -> List[Optional[float]]:
    """
    Calculates Volume Weighted Average Price (VWAP).
    VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
    Typical Price = (High + Low + Close) / 3
    """
    n = len(candles)
    vwap: List[Optional[float]] = [None] * n

    cum_pv = 0.0
    cum_vol = 0.0

    for i in range(n):
        c = candles[i]
        typical_price = (c.high + c.low + c.close) / 3.0
        cum_pv += typical_price * c.volume
        cum_vol += c.volume

        if cum_vol > 0:
            vwap[i] = cum_pv / cum_vol
        else:
            vwap[i] = typical_price

    return vwap


def calculate_obv(candles: List[Candle]) -> List[float]:
    """
    Calculates On-Balance Volume (OBV).
    If Close > Prev Close: OBV += Volume
    If Close < Prev Close: OBV -= Volume
    """
    n = len(candles)
    if n == 0:
        return []

    obv: List[float] = [0.0] * n
    for i in range(1, n):
        if candles[i].close > candles[i - 1].close:
            obv[i] = obv[i - 1] + candles[i].volume
        elif candles[i].close < candles[i - 1].close:
            obv[i] = obv[i - 1] - candles[i].volume
        else:
            obv[i] = obv[i - 1]

    return obv


def calculate_volume_ratio(candles: List[Candle], period: int = 20) -> List[Optional[float]]:
    """
    Calculates volume surge ratio (Current Volume / 20-period Volume SMA).
    Ratio > 1.5 indicates institutional volume accumulation / distribution.
    """
    volumes = [c.volume for c in candles]
    vol_sma = calculate_sma(volumes, period)

    n = len(candles)
    ratios: List[Optional[float]] = [None] * n

    for i in range(n):
        s = vol_sma[i]
        if s is not None and s > 0:
            ratios[i] = round(volumes[i] / s, 2)

    return ratios
