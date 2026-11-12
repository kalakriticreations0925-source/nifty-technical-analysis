"""
Trend indicators: SMA, EMA, MACD, Supertrend, and ADX.
"""
from typing import List, Tuple, Optional, Dict
import math
from src.data.types import Candle


def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculates Simple Moving Average (SMA)."""
    sma: List[Optional[float]] = [None] * len(prices)
    if len(prices) < period:
        return sma

    running_sum = sum(prices[:period])
    sma[period - 1] = running_sum / period

    for i in range(period, len(prices)):
        running_sum += prices[i] - prices[i - period]
        sma[i] = running_sum / period

    return sma


def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculates Exponential Moving Average (EMA)."""
    ema: List[Optional[float]] = [None] * len(prices)
    if len(prices) < period:
        return ema

    multiplier = 2.0 / (period + 1.0)
    # Seed with SMA
    initial_sma = sum(prices[:period]) / period
    ema[period - 1] = initial_sma

    prev_ema = initial_sma
    for i in range(period, len(prices)):
        val = (prices[i] - prev_ema) * multiplier + prev_ema
        ema[i] = val
        prev_ema = val

    return ema


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates MACD Line, Signal Line, and MACD Histogram.
    MACD Line = Fast EMA - Slow EMA
    Signal Line = EMA of MACD Line
    Histogram = MACD Line - Signal Line
    """
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    n = len(prices)
    macd_line: List[Optional[float]] = [None] * n

    for i in range(n):
        if fast_ema[i] is not None and slow_ema[i] is not None:
            macd_line[i] = fast_ema[i] - slow_ema[i]

    # Signal line is EMA of macd_line
    # We find first non-None index
    valid_indices = [i for i, v in enumerate(macd_line) if v is not None]
    signal_line: List[Optional[float]] = [None] * n
    histogram: List[Optional[float]] = [None] * n

    if len(valid_indices) >= signal_period:
        valid_macd_vals = [macd_line[i] for i in valid_indices]
        valid_signal = calculate_ema(valid_macd_vals, signal_period)

        for orig_idx, sig_val in zip(valid_indices, valid_signal):
            signal_line[orig_idx] = sig_val
            if macd_line[orig_idx] is not None and sig_val is not None:
                histogram[orig_idx] = macd_line[orig_idx] - sig_val

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_atr(candles: List[Candle], period: int = 14) -> List[Optional[float]]:
    """Calculates Average True Range (ATR) with Wilder's Smoothing."""
    n = len(candles)
    atr: List[Optional[float]] = [None] * n
    if n < 2:
        return atr

    tr: List[float] = [candles[0].high - candles[0].low]
    for i in range(1, n):
        hl = candles[i].high - candles[i].low
        hc = abs(candles[i].high - candles[i - 1].close)
        lc = abs(candles[i].low - candles[i - 1].close)
        tr.append(max(hl, hc, lc))

    if n < period:
        return atr

    # Initial ATR is simple average of first period TRs
    first_atr = sum(tr[:period]) / period
    atr[period - 1] = first_atr

    prev_atr = first_atr
    for i in range(period, n):
        current_atr = (prev_atr * (period - 1) + tr[i]) / period
        atr[i] = current_atr
        prev_atr = current_atr

    return atr


def calculate_supertrend(
    candles: List[Candle],
    period: int = 10,
    multiplier: float = 3.0
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Supertrend indicator (standard 10-period, 3.0 multiplier).
    Returns:
        - 'supertrend': The active Supertrend line values
        - 'direction': 1 for Bullish (Uptrend), -1 for Bearish (Downtrend)
        - 'upper_band': Final upper band
        - 'lower_band': Final lower band
    """
    n = len(candles)
    atr = calculate_atr(candles, period)

    supertrend: List[Optional[float]] = [None] * n
    direction: List[Optional[int]] = [None] * n
    upper_band: List[Optional[float]] = [None] * n
    lower_band: List[Optional[float]] = [None] * n

    basic_upper: List[float] = [0.0] * n
    basic_lower: List[float] = [0.0] * n

    for i in range(n):
        hl2 = (candles[i].high + candles[i].low) / 2.0
        if atr[i] is not None:
            basic_upper[i] = hl2 + (multiplier * atr[i])
            basic_lower[i] = hl2 - (multiplier * atr[i])

    # Find the starting index where ATR is available
    start_idx = period - 1
    if start_idx >= n or atr[start_idx] is None:
        return {
            "supertrend": supertrend,
            "direction": direction,
            "upper_band": upper_band,
            "lower_band": lower_band
        }

    # Initialize at start_idx
    upper_band[start_idx] = basic_upper[start_idx]
    lower_band[start_idx] = basic_lower[start_idx]
    direction[start_idx] = 1 if candles[start_idx].close > upper_band[start_idx] else -1
    supertrend[start_idx] = lower_band[start_idx] if direction[start_idx] == 1 else upper_band[start_idx]

    for i in range(start_idx + 1, n):
        prev_close = candles[i - 1].close
        prev_upper = upper_band[i - 1]
        prev_lower = lower_band[i - 1]

        # Calculate Final Upper Band
        if basic_upper[i] < prev_upper or prev_close > prev_upper:
            upper_band[i] = basic_upper[i]
        else:
            upper_band[i] = prev_upper

        # Calculate Final Lower Band
        if basic_lower[i] > prev_lower or prev_close < prev_lower:
            lower_band[i] = basic_lower[i]
        else:
            lower_band[i] = prev_lower

        # Determine trend direction
        prev_dir = direction[i - 1]
        if prev_dir == 1:
            if candles[i].close < lower_band[i]:
                direction[i] = -1
            else:
                direction[i] = 1
        else:
            if candles[i].close > upper_band[i]:
                direction[i] = 1
            else:
                direction[i] = -1

        supertrend[i] = lower_band[i] if direction[i] == 1 else upper_band[i]

    return {
        "supertrend": supertrend,
        "direction": direction,
        "upper_band": upper_band,
        "lower_band": lower_band
    }


def calculate_adx(
    candles: List[Candle],
    period: int = 14
) -> Dict[str, List[Optional[float]]]:
    """
    Calculates Average Directional Index (ADX) with +DI and -DI.
    ADX indicates trend strength regardless of direction (>25 strong trend).
    """
    n = len(candles)
    adx_res: Dict[str, List[Optional[float]]] = {
        "adx": [None] * n,
        "plus_di": [None] * n,
        "minus_di": [None] * n
    }
    if n < period * 2:
        return adx_res

    plus_dm: List[float] = [0.0] * n
    minus_dm: List[float] = [0.0] * n
    tr: List[float] = [0.0] * n

    for i in range(1, n):
        up_move = candles[i].high - candles[i - 1].high
        down_move = candles[i - 1].low - candles[i].low

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        else:
            plus_dm[i] = 0.0

        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
        else:
            minus_dm[i] = 0.0

        hl = candles[i].high - candles[i].low
        hc = abs(candles[i].high - candles[i - 1].close)
        lc = abs(candles[i].low - candles[i - 1].close)
        tr[i] = max(hl, hc, lc)

    # Smooth TR, +DM, -DM using Wilder's smoothing
    smoothed_tr = sum(tr[1:period + 1])
    smoothed_plus_dm = sum(plus_dm[1:period + 1])
    smoothed_minus_dm = sum(minus_dm[1:period + 1])

    dx_list: List[Optional[float]] = [None] * n

    def calc_di(p_dm, m_dm, s_tr):
        if s_tr == 0:
            return 0.0, 0.0, 0.0
        p_di = 100.0 * (p_dm / s_tr)
        m_di = 100.0 * (m_dm / s_tr)
        di_sum = p_di + m_di
        dx = 100.0 * (abs(p_di - m_di) / di_sum) if di_sum > 0 else 0.0
        return p_di, m_di, dx

    p_di, m_di, dx = calc_di(smoothed_plus_dm, smoothed_minus_dm, smoothed_tr)
    adx_res["plus_di"][period] = p_di
    adx_res["minus_di"][period] = m_di
    dx_list[period] = dx

    for i in range(period + 1, n):
        smoothed_tr = smoothed_tr - (smoothed_tr / period) + tr[i]
        smoothed_plus_dm = smoothed_plus_dm - (smoothed_plus_dm / period) + plus_dm[i]
        smoothed_minus_dm = smoothed_minus_dm - (smoothed_minus_dm / period) + minus_dm[i]

        p_di, m_di, dx = calc_di(smoothed_plus_dm, smoothed_minus_dm, smoothed_tr)
        adx_res["plus_di"][i] = p_di
        adx_res["minus_di"][i] = m_di
        dx_list[i] = dx

    # Now calculate ADX as moving average of DX
    valid_dx = [idx for idx in range(n) if dx_list[idx] is not None]
    if len(valid_dx) >= period:
        first_dx_idx = valid_dx[period - 1]
        sum_dx = sum(dx_list[valid_dx[j]] for j in range(period))
        first_adx = sum_dx / period
        adx_res["adx"][first_dx_idx] = first_adx

        prev_adx = first_adx
        for j in range(period, len(valid_dx)):
            curr_idx = valid_dx[j]
            curr_adx = (prev_adx * (period - 1) + dx_list[curr_idx]) / period
            adx_res["adx"][curr_idx] = curr_adx
            prev_adx = curr_adx

    return adx_res
