"""
Data types and schemas for Nifty Technical Analysis and Signal Generation.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


@dataclass
class Signal:
    symbol: str
    timestamp: str
    signal_type: SignalType
    price: float
    stop_loss: float
    target: float
    strategy_name: str
    confidence: float = 0.0  # 0.0 to 1.0 (or 0% to 100%)
    indicators: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    name: str = ""
    sector: str = ""
    change_pct: float = 0.0
    high: float = 0.0
    low: float = 0.0
    is_index: bool = False

    @property
    def risk_reward_ratio(self) -> float:
        risk = abs(self.price - self.stop_loss)
        reward = abs(self.target - self.price)
        return round(reward / risk, 2) if risk > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name or self.symbol,
            "sector": self.sector or ("Index" if "^" in self.symbol else "Equity"),
            "timestamp": self.timestamp,
            "signal": self.signal_type.value,
            "price": self.price,
            "change_pct": round(self.change_pct, 2),
            "high": round(self.high, 2) if self.high else self.price,
            "low": round(self.low, 2) if self.low else self.price,
            "is_index": self.is_index or ("^" in self.symbol),
            "stop_loss": self.stop_loss,
            "target": self.target,
            "risk_reward": self.risk_reward_ratio,
            "strategy": self.strategy_name,
            "confidence": f"{int(self.confidence * 100)}%",
            "indicators": self.indicators,
            "rationale": self.rationale
        }


@dataclass
class Position:
    symbol: str
    entry_time: str
    entry_price: float
    size: float
    side: SignalType
    stop_loss: float
    target: float


@dataclass
class TradeRecord:
    symbol: str
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # "TARGET", "STOP_LOSS", "REVERSAL", "END_OF_DATA"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "entry_price": round(self.entry_price, 2),
            "exit_price": round(self.exit_price, 2),
            "pnl": round(self.pnl, 2),
            "pnl_pct": f"{round(self.pnl_pct * 100, 2)}%",
            "exit_reason": self.exit_reason
        }


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    initial_capital: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    trades: List[TradeRecord] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        return {
            "Strategy": self.strategy_name,
            "Symbol": self.symbol,
            "Initial Capital": f"₹{self.initial_capital:,.2f}",
            "Final Capital": f"₹{self.final_equity:,.2f}",
            "Total Return": f"{self.total_return_pct:.2f}%",
            "CAGR": f"{self.cagr_pct:.2f}%",
            "Sharpe Ratio": round(self.sharpe_ratio, 2),
            "Sortino Ratio": round(self.sortino_ratio, 2),
            "Max Drawdown": f"{self.max_drawdown_pct:.2f}%",
            "Total Trades": self.total_trades,
            "Win Rate": f"{self.win_rate_pct:.2f}% ({self.winning_trades}/{self.total_trades})",
            "Profit Factor": round(self.profit_factor, 2)
        }
