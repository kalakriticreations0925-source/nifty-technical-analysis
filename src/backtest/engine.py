"""
Event-driven Backtesting Engine for Technical Analysis Strategies.
Supports position sizing, slippage, brokerage/STT, and trailing stops.
"""
from typing import List, Optional, Dict
from src.data.types import (
    Candle,
    Signal,
    SignalType,
    TradeRecord,
    BacktestResult
)
from src.strategies.base import BaseStrategy
from src.backtest.metrics import (
    calculate_cagr,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_profit_factor
)


class BacktestEngine:
    """
    Backtesting engine simulates executing trading signals on historical candle series.
    """
    def __init__(
        self,
        initial_capital: float = 100000.0,
        brokerage_per_trade: float = 20.0,
        slippage_pct: float = 0.0005,
        allow_shorting: bool = True
    ):
        self.initial_capital = initial_capital
        self.brokerage_per_trade = brokerage_per_trade
        self.slippage_pct = slippage_pct
        self.allow_shorting = allow_shorting

    def run(
        self,
        strategy: BaseStrategy,
        candles: List[Candle],
        symbol: str = "NIFTY"
    ) -> BacktestResult:
        n = len(candles)
        if n < 10:
            raise ValueError("Insufficient candle history for backtest.")

        signals = strategy.generate_signals(candles, symbol)
        signal_map: Dict[str, Signal] = {s.timestamp: s for s in signals}

        capital = self.initial_capital
        equity_curve: List[float] = [capital]
        daily_returns: List[float] = []
        trades: List[TradeRecord] = []

        # Current open position state
        in_position = False
        pos_side: Optional[SignalType] = None
        pos_entry_price = 0.0
        pos_entry_time = ""
        pos_stop_loss = 0.0
        pos_target = 0.0
        pos_size = 0.0

        for i, candle in enumerate(candles):
            high = candle.high
            low = candle.low
            close = candle.close
            ts = candle.timestamp

            # 1. If currently in position, check if Stop-Loss or Target was triggered during candle
            if in_position:
                exit_price = None
                exit_reason = ""

                if pos_side == SignalType.BUY:
                    if low <= pos_stop_loss:
                        exit_price = pos_stop_loss * (1.0 - self.slippage_pct)
                        exit_reason = "STOP_LOSS"
                    elif high >= pos_target:
                        exit_price = pos_target * (1.0 - self.slippage_pct)
                        exit_reason = "TARGET"
                elif pos_side == SignalType.SELL:
                    if high >= pos_stop_loss:
                        exit_price = pos_stop_loss * (1.0 + self.slippage_pct)
                        exit_reason = "STOP_LOSS"
                    elif low <= pos_target:
                        exit_price = pos_target * (1.0 + self.slippage_pct)
                        exit_reason = "TARGET"

                # Check if opposite signal arrived to reverse/exit
                if not exit_price and ts in signal_map:
                    new_sig = signal_map[ts]
                    if (pos_side == SignalType.BUY and new_sig.signal_type == SignalType.SELL) or \
                       (pos_side == SignalType.SELL and new_sig.signal_type == SignalType.BUY):
                        exit_price = close * (1.0 - self.slippage_pct if pos_side == SignalType.BUY else 1.0 + self.slippage_pct)
                        exit_reason = "REVERSAL"

                # Execute exit if triggered
                if exit_price is not None:
                    if pos_side == SignalType.BUY:
                        raw_pnl = (exit_price - pos_entry_price) * pos_size
                    else:
                        raw_pnl = (pos_entry_price - exit_price) * pos_size

                    net_pnl = raw_pnl - (self.brokerage_per_trade * 2)  # Entry + Exit brokerage
                    capital += net_pnl
                    pnl_pct = net_pnl / (pos_entry_price * pos_size) if pos_entry_price > 0 else 0.0

                    trades.append(TradeRecord(
                        symbol=symbol,
                        side=pos_side.value,
                        entry_time=pos_entry_time,
                        exit_time=ts,
                        entry_price=pos_entry_price,
                        exit_price=exit_price,
                        size=pos_size,
                        pnl=net_pnl,
                        pnl_pct=pnl_pct,
                        exit_reason=exit_reason
                    ))

                    in_position = False
                    pos_side = None

            # 2. Check for new entry signals
            if not in_position and ts in signal_map:
                sig = signal_map[ts]
                if sig.signal_type == SignalType.BUY or (sig.signal_type == SignalType.SELL and self.allow_shorting):
                    pos_side = sig.signal_type
                    pos_entry_price = close * (1.0 + self.slippage_pct if pos_side == SignalType.BUY else 1.0 - self.slippage_pct)
                    pos_entry_time = ts
                    pos_stop_loss = sig.stop_loss
                    pos_target = sig.target

                    # Simple position sizing: use 90% capital
                    allocation = capital * 0.90
                    pos_size = max(1.0, round(allocation / pos_entry_price, 2))
                    in_position = True

            # Track equity curve and daily returns
            current_equity = capital
            if in_position:
                unrealized = (close - pos_entry_price) * pos_size if pos_side == SignalType.BUY else (pos_entry_price - close) * pos_size
                current_equity += unrealized

            prev_eq = equity_curve[-1]
            ret = (current_equity - prev_eq) / prev_eq if prev_eq > 0 else 0.0
            daily_returns.append(ret)
            equity_curve.append(current_equity)

        # 3. Close open position at end of backtest
        if in_position:
            last_c = candles[-1]
            exit_price = last_c.close
            raw_pnl = (exit_price - pos_entry_price) * pos_size if pos_side == SignalType.BUY else (pos_entry_price - exit_price) * pos_size
            net_pnl = raw_pnl - self.brokerage_per_trade
            capital += net_pnl
            trades.append(TradeRecord(
                symbol=symbol,
                side=pos_side.value,
                entry_time=pos_entry_time,
                exit_time=last_c.timestamp,
                entry_price=pos_entry_price,
                exit_price=exit_price,
                size=pos_size,
                pnl=net_pnl,
                pnl_pct=net_pnl / (pos_entry_price * pos_size),
                exit_reason="END_OF_DATA"
            ))

        # Calculate final performance metrics
        total_ret = ((capital - self.initial_capital) / self.initial_capital) * 100.0
        num_days = max(1, n)
        cagr = calculate_cagr(self.initial_capital, capital, num_days)
        max_dd, _, _ = calculate_max_drawdown(equity_curve)
        sharpe = calculate_sharpe_ratio(daily_returns)
        sortino = calculate_sortino_ratio(daily_returns)
        profit_factor = calculate_profit_factor(trades)

        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        win_rate = (len(winning_trades) / len(trades) * 100.0) if trades else 0.0

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            initial_capital=self.initial_capital,
            final_equity=capital,
            total_return_pct=total_ret,
            cagr_pct=cagr,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            trades=trades
        )
