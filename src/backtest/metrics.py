"""
Financial performance and risk metrics calculation.
Includes Sharpe, Sortino, CAGR, Max Drawdown, Win Rate, and Profit Factor.
"""
import math
from typing import List, Tuple
from src.data.types import TradeRecord


def calculate_cagr(start_val: float, end_val: float, num_days: int) -> float:
    """Calculates Compound Annual Growth Rate (CAGR) in percentage."""
    if start_val <= 0 or end_val <= 0 or num_days <= 0:
        return 0.0
    years = num_days / 365.25
    if years == 0:
        return 0.0
    return ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
    """
    Calculates Maximum Drawdown percentage and peak/trough indices.
    Returns: (max_dd_pct, peak_idx, trough_idx)
    """
    if not equity_curve:
        return 0.0, 0, 0

    max_dd = 0.0
    peak = equity_curve[0]
    peak_idx = 0
    max_peak_idx = 0
    max_trough_idx = 0

    for i, val in enumerate(equity_curve):
        if val > peak:
            peak = val
            peak_idx = i
        else:
            dd = (peak - val) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
                max_peak_idx = peak_idx
                max_trough_idx = i

    return max_dd * 100.0, max_peak_idx, max_trough_idx


def calculate_sharpe_ratio(
    daily_returns: List[float],
    annual_risk_free_rate: float = 0.065,
    trading_days: int = 252
) -> float:
    """
    Calculates Annualized Sharpe Ratio using Indian risk-free benchmark (6.5%).
    """
    if len(daily_returns) < 2:
        return 0.0

    mean_ret = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std_ret = math.sqrt(variance)

    if std_ret == 0:
        return 0.0

    daily_rf = annual_risk_free_rate / trading_days
    excess_ret = mean_ret - daily_rf
    return (excess_ret / std_ret) * math.sqrt(trading_days)


def calculate_sortino_ratio(
    daily_returns: List[float],
    annual_risk_free_rate: float = 0.065,
    trading_days: int = 252
) -> float:
    """
    Calculates Annualized Sortino Ratio (downside deviation).
    """
    if len(daily_returns) < 2:
        return 0.0

    mean_ret = sum(daily_returns) / len(daily_returns)
    daily_rf = annual_risk_free_rate / trading_days

    downside_diffs = [min(0.0, r - daily_rf) for r in daily_returns]
    downside_variance = sum(d ** 2 for d in downside_diffs) / len(daily_returns)
    downside_std = math.sqrt(downside_variance)

    if downside_std == 0:
        return 0.0

    excess_ret = mean_ret - daily_rf
    return (excess_ret / downside_std) * math.sqrt(trading_days)


def calculate_profit_factor(trades: List[TradeRecord]) -> float:
    """Calculates Gross Profits / Gross Losses."""
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))

    if gross_loss == 0:
        return round(gross_profit, 2) if gross_profit > 0 else 1.0
    return round(gross_profit / gross_loss, 2)
