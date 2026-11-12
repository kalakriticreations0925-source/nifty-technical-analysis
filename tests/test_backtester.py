"""
Unit tests for Backtesting Engine and performance metrics.
"""
import unittest
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loader import fetch_market_data
from src.strategies.supertrend_rsi import SupertrendRSIStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import (
    calculate_cagr,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio
)


class TestBacktester(unittest.TestCase):
    def setUp(self):
        self.candles = fetch_market_data("^NSEI", use_sample_fallback=True)

    def test_backtest_execution(self):
        strategy = SupertrendRSIStrategy()
        engine = BacktestEngine(initial_capital=100000.0, brokerage_per_trade=20.0)
        result = engine.run(strategy, self.candles, symbol="^NSEI")

        self.assertEqual(result.symbol, "^NSEI")
        self.assertEqual(result.initial_capital, 100000.0)
        self.assertGreater(result.final_equity, 0.0)
        self.assertIsInstance(result.total_trades, int)
        self.assertGreaterEqual(result.win_rate_pct, 0.0)
        self.assertLessEqual(result.win_rate_pct, 100.0)

    def test_metrics_math(self):
        # CAGR test: 100 to 121 in 2 years is exactly 10%
        cagr = calculate_cagr(100.0, 121.0, 730)
        self.assertAlmostEqual(cagr, 10.0, delta=0.5)

        # Max Drawdown: 100 -> 120 -> 90 -> 110. Max peak=120, trough=90 -> (120-90)/120 = 25%
        dd, peak_idx, trough_idx = calculate_max_drawdown([100.0, 120.0, 90.0, 110.0])
        self.assertAlmostEqual(dd, 25.0)
        self.assertEqual(peak_idx, 1)
        self.assertEqual(trough_idx, 2)


if __name__ == "__main__":
    unittest.main()
