"""
Unit tests for Strategies and Signal Generation.
"""
import unittest
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loader import fetch_market_data
from src.data.types import SignalType
from src.strategies.supertrend_rsi import SupertrendRSIStrategy
from src.strategies.macd_bollinger import MACDBollingerStrategy
from src.strategies.ema_crossover import EMACrossoverStrategy
from src.strategies.confluence import MultiFactorConfluenceStrategy


class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.candles = fetch_market_data("^NSEI", use_sample_fallback=True)
        self.assertTrue(len(self.candles) >= 50, "Sample candle dataset must have >= 50 bars.")

    def test_supertrend_strategy_signals(self):
        strat = SupertrendRSIStrategy()
        signals = strat.generate_signals(self.candles, symbol="^NSEI")
        self.assertIsInstance(signals, list)
        for s in signals:
            self.assertIn(s.signal_type, [SignalType.BUY, SignalType.SELL])
            self.assertGreater(s.price, 0)
            self.assertGreater(s.stop_loss, 0)
            self.assertGreater(s.target, 0)
            self.assertGreater(s.risk_reward_ratio, 0)

    def test_macd_bollinger_strategy_signals(self):
        strat = MACDBollingerStrategy()
        signals = strat.generate_signals(self.candles, symbol="^NSEI")
        self.assertIsInstance(signals, list)

    def test_ema_crossover_strategy_signals(self):
        strat = EMACrossoverStrategy()
        signals = strat.generate_signals(self.candles, symbol="^NSEI")
        self.assertIsInstance(signals, list)

    def test_confluence_strategy_signals(self):
        strat = MultiFactorConfluenceStrategy(threshold=0.65)
        signals = strat.generate_signals(self.candles, symbol="^NSEI")
        self.assertIsInstance(signals, list)
        for s in signals:
            self.assertGreaterEqual(s.confidence, 0.65)
            self.assertTrue(len(s.rationale) > 0)


if __name__ == "__main__":
    unittest.main()
