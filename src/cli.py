"""
Nifty Technical Analysis & Trading Signals CLI.
Interactive command-line tool to scan markets, generate buy/sell signals, and run backtests.
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loader import fetch_market_data, load_candles_from_csv, get_available_tickers
from src.data.types import Signal, SignalType
from src.strategies.supertrend_rsi import SupertrendRSIStrategy
from src.strategies.macd_bollinger import MACDBollingerStrategy
from src.strategies.ema_crossover import EMACrossoverStrategy
from src.strategies.confluence import MultiFactorConfluenceStrategy
from src.backtest.engine import BacktestEngine
from src.alerts.notifier import SignalNotifier


STRATEGIES = {
    "confluence": MultiFactorConfluenceStrategy(),
    "supertrend": SupertrendRSIStrategy(),
    "macd_bb": MACDBollingerStrategy(),
    "ema_cross": EMACrossoverStrategy()
}


def cmd_scan(args):
    """Scans symbols and generates latest buy/sell signals."""
    strategy = STRATEGIES.get(args.strategy, STRATEGIES["confluence"])
    print(f"\n🚀 Scanning Market using Strategy: [{strategy.name}]")

    symbols_to_scan = []
    if args.symbol.upper() == "ALL":
        symbols_to_scan = [t["symbol"] for t in get_available_tickers()]
    else:
        symbols_to_scan = [args.symbol]

    latest_signals = []
    for sym in symbols_to_scan:
        try:
            candles = fetch_market_data(sym)
            if not candles:
                print(f"⚠️  No candle data available for {sym}")
                continue

            sig = strategy.get_latest_signal(candles, sym)
            if sig:
                latest_signals.append(sig)
            else:
                last_c = candles[-1]
                latest_signals.append(Signal(
                    symbol=sym,
                    timestamp=last_c.timestamp,
                    signal_type=SignalType.HOLD,
                    price=last_c.close,
                    stop_loss=last_c.close,
                    target=last_c.close,
                    strategy_name=strategy.name,
                    confidence=0.5,
                    rationale="No high-probability breakout or crossover setup on latest candle."
                ))
        except Exception as e:
            print(f"Error scanning {sym}: {e}")

    print("\n" + SignalNotifier.format_terminal_table(latest_signals) + "\n")

    if args.export_json:
        SignalNotifier.save_json(latest_signals, args.export_json)
        print(f"💾 Exported signals to JSON: {args.export_json}")

    if getattr(args, "export_js", None):
        SignalNotifier.save_js(latest_signals, args.export_js)
        print(f"🌐 Exported signals for Dashboard: {args.export_js}")

    if args.export_md:
        md_report = SignalNotifier.generate_markdown_report(latest_signals)
        with open(args.export_md, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"📄 Exported signals to Markdown: {args.export_md}")


def cmd_backtest(args):
    """Runs a historical backtest of a strategy on specified symbol."""
    strategy = STRATEGIES.get(args.strategy, STRATEGIES["confluence"])
    candles = fetch_market_data(args.symbol)
    if not candles:
        print(f"❌ Failed to load candle data for {args.symbol}")
        return

    print(f"\n📊 Running Backtest: [{strategy.name}] on {args.symbol} ({len(candles)} bars)")
    engine = BacktestEngine(
        initial_capital=args.capital,
        brokerage_per_trade=args.brokerage,
        slippage_pct=args.slippage / 100.0,
        allow_shorting=not args.long_only
    )
    result = engine.run(strategy, candles, args.symbol)

    print("\n" + "=" * 50)
    print("           BACKTEST PERFORMANCE REPORT           ")
    print("=" * 50)
    for k, v in result.summary().items():
        print(f"  {k.ljust(20)}: {v}")
    print("=" * 50)

    if result.trades:
        print(f"\nLast 5 Executed Trades:")
        for t in result.trades[-5:]:
            color = "\033[92m" if t.pnl > 0 else "\033[91m"
            print(f"  [{t.side}] Entry: ₹{t.entry_price:,.2f} ({t.entry_time}) -> Exit: ₹{t.exit_price:,.2f} ({t.exit_time}) | PnL: {color}₹{t.pnl:,.2f} ({t.pnl_pct})\033[0m [{t.exit_reason}]")

    if args.export_md:
        signals = strategy.generate_signals(candles, args.symbol)
        md_report = SignalNotifier.generate_markdown_report(signals[-10:], result)
        with open(args.export_md, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"\n📄 Saved Backtest Report to {args.export_md}")


def cmd_list_strategies(args):
    """Lists available technical analysis strategies."""
    print("\nAvailable Strategies:")
    print("-" * 60)
    print("1. confluence  : MultiFactorConfluenceStrategy (Ensemble Trend + Momentum + Vol + Volume)")
    print("2. supertrend  : SupertrendRSIStrategy (Trend following with RSI momentum filter)")
    print("3. macd_bb     : MACDBollingerStrategy (Breakouts and Mean-Reversion)")
    print("4. ema_cross   : EMACrossoverStrategy (Fast/Slow EMA crossover with 200 EMA trend filter)")
    print("-" * 60)


def cmd_list_tickers(args):
    """Lists available ticker catalog."""
    tickers = get_available_tickers()
    print(f"\nTracked Indian Equities & Indices ({len(tickers)}):")
    print("-" * 65)
    print(f"{'Symbol'.ljust(16)} | {'Sector'.ljust(22)} | {'Name'}")
    print("-" * 65)
    for t in tickers:
        print(f"{t['symbol'].ljust(16)} | {t.get('sector', '').ljust(22)} | {t['name']}")
    print("-" * 65)


def main():
    parser = argparse.ArgumentParser(
        description="Nifty Technical Analysis & Trading Signals Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan symbols and generate buy/sell signals")
    p_scan.add_argument("--symbol", default="^NSEI", help="Ticker symbol (e.g. ^NSEI, ^NSEBANK, RELIANCE.NS, or ALL)")
    p_scan.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="confluence", help="Strategy to use")
    p_scan.add_argument("--export-json", help="Path to export signals as JSON")
    p_scan.add_argument("--export-js", help="Path to export signals as JavaScript file for browser dashboard")
    p_scan.add_argument("--export-md", help="Path to export report as Markdown")

    # backtest
    p_bt = subparsers.add_parser("backtest", help="Run strategy backtest on historical data")
    p_bt.add_argument("--symbol", default="^NSEI", help="Ticker symbol (e.g. ^NSEI, ^NSEBANK)")
    p_bt.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="confluence", help="Strategy to backtest")
    p_bt.add_argument("--capital", type=float, default=100000.0, help="Initial capital in INR (default: 100,000)")
    p_bt.add_argument("--brokerage", type=float, default=20.0, help="Brokerage per executed trade (default: 20)")
    p_bt.add_argument("--slippage", type=float, default=0.05, help="Slippage percentage (default: 0.05%)")
    p_bt.add_argument("--long-only", action="store_true", help="Disallow short selling")
    p_bt.add_argument("--export-md", help="Path to export backtest report as Markdown")

    # list-strategies
    subparsers.add_parser("list-strategies", help="List all available strategies")

    # list-tickers
    subparsers.add_parser("list-tickers", help="List tracked tickers and indices")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "list-strategies":
        cmd_list_strategies(args)
    elif args.command == "list-tickers":
        cmd_list_tickers(args)


if __name__ == "__main__":
    main()
