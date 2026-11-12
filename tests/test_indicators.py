"""
Unit tests for Technical Indicators (SMA, EMA, MACD, Supertrend, ADX, RSI, Bollinger).
"""
import unittest
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.types import Candle
from src.indicators.trend import (
    calculate_sma,
    calculate_ema,
    calculate_macd,
    calculate_atr,
    calculate_supertrend,
    calculate_adx
)
from src.indicators.momentum import calculate_rsi, calculate_stochastic, calculate_williams_r
from src.indicators.volatility import calculate_bollinger_bands, calculate_keltner_channels
from src.indicators.volume import calculate_vwap, calculate_obv, calculate_volume_ratio


class TestIndicators(unittest.TestCase):
    def setUp(self):
        # 30-bar synthetic test dataset with known trend
        self.prices = [100.0 + i * 2.0 for i in range(30)]  # Uptrend: 100 to 158
        self.candles = [
            Candle(
                timestamp=f"2026-01-{i+1:02d}",
                open=p - 1.0,
                high=p + 2.0,
                low=p - 2.0,
                close=p,
                volume=1000.0 + (i * 100.0)
            )
            for i, p in enumerate(self.prices)
        ]

    def test_sma(self):
        sma5 = calculate_sma(self.prices, 5)
        self.assertEqual(len(sma5), 30)
        self.assertIsNone(sma5[0])
        self.assertIsNone(sma5[3])
        # Expected average of 100, 102, 104, 106, 108 is 104
        self.assertAlmostEqual(sma5[4], 104.0)

    def test_ema(self):
        ema5 = calculate_ema(self.prices, 5)
        self.assertEqual(len(ema5), 30)
        self.assertIsNone(ema5[3])
        self.assertAlmostEqual(ema5[4], 104.0)
        # In a steady uptrend, price > EMA
        self.assertGreater(self.prices[-1], ema5[-1])

    def test_macd(self):
        macd_res = calculate_macd(self.prices, fast_period=5, slow_period=10, signal_period=3)
        self.assertIn("macd", macd_res)
        self.assertIn("signal", macd_res)
        self.assertIn("histogram", macd_res)
        self.assertEqual(len(macd_res["macd"]), 30)
        # In consistent uptrend, MACD line should be positive
        self.assertGreater(macd_res["macd"][-1], 0.0)

    def test_atr(self):
        atr = calculate_atr(self.candles, period=5)
        self.assertEqual(len(atr), 30)
        self.assertIsNotNone(atr[4])
        # Range is High - Low = 4.0
        self.assertAlmostEqual(atr[4], 4.0)

    def test_supertrend(self):
        st = calculate_supertrend(self.candles, period=5, multiplier=2.0)
        self.assertIn("supertrend", st)
        self.assertIn("direction", st)
        # In steady uptrend, direction should be Bullish (+1)
        self.assertEqual(st["direction"][-1], 1)

    def test_rsi(self):
        rsi = calculate_rsi(self.prices, period=14)
        self.assertEqual(len(rsi), 30)
        self.assertIsNotNone(rsi[14])
        # In continuous upward trend, RSI should be 100 or close to 100
        self.assertAlmostEqual(rsi[-1], 100.0)

    def test_bollinger_bands(self):
        bb = calculate_bollinger_bands(self.prices, period=10, num_std=2.0)
        self.assertIn("middle", bb)
        self.assertIn("upper", bb)
        self.assertIn("lower", bb)
        self.assertIsNotNone(bb["upper"][-1])
        self.assertGreater(bb["upper"][-1], bb["middle"][-1])
        self.assertLess(bb["lower"][-1], bb["middle"][-1])

    def test_vwap_and_obv(self):
        vwap = calculate_vwap(self.candles)
        obv = calculate_obv(self.candles)
        self.assertEqual(len(vwap), 30)
        self.assertEqual(len(obv), 30)
        # OBV should be strictly increasing in pure uptrend
        self.assertGreater(obv[-1], obv[0])


if __name__ == "__main__":
    unittest.main()
