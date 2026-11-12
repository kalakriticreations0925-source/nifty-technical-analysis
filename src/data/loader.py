"""
Data loading and market data fetching engine for Nifty and Indian Equities.
Supports local CSV, SQLite/JSON cache, and live Yahoo Finance feed with offline fallback.
"""
import os
import csv
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from src.data.types import Candle


DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_candles_from_csv(filepath: str) -> List[Candle]:
    """
    Parses a CSV file containing Date/Timestamp, Open, High, Low, Close, Volume.
    Handles case-insensitive column headers and standard formatting.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    candles: List[Candle] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Normalize column names to lowercase
        for row in reader:
            normalized = {k.strip().lower(): v for k, v in row.items() if k}
            date_val = normalized.get("date") or normalized.get("timestamp") or normalized.get("datetime") or ""
            open_val = float(normalized.get("open", 0.0))
            high_val = float(normalized.get("high", 0.0))
            low_val = float(normalized.get("low", 0.0))
            close_val = float(normalized.get("close", 0.0))
            vol_val = float(normalized.get("volume", 0.0))

            candles.append(Candle(
                timestamp=date_val,
                open=open_val,
                high=high_val,
                low=low_val,
                close=close_val,
                volume=vol_val
            ))

    # Sort chronologically if needed
    candles.sort(key=lambda c: c.timestamp)
    return candles


def get_available_tickers() -> List[Dict[str, str]]:
    """Loads ticker catalog from nifty50_tickers.json."""
    catalog_path = DATA_DIR / "nifty50_tickers.json"
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"symbol": "^NSEI", "name": "NIFTY 50", "sector": "Index"},
        {"symbol": "^NSEBANK", "name": "BANK NIFTY", "sector": "Index"}
    ]


def fetch_market_data(
    symbol: str = "^NSEI",
    period: str = "1y",
    interval: str = "1d",
    use_sample_fallback: bool = True
) -> List[Candle]:
    """
    Fetches market data for a given symbol.
    Attempts live fetch via yfinance if available.
    If offline or yfinance not installed, gracefully falls back to bundled sample data.
    """
    candles: List[Candle] = []

    # 1. Attempt yfinance if available
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            for index, row in df.iterrows():
                ts = index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index)
                candles.append(Candle(
                    timestamp=ts,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0.0))
                ))
            if candles:
                return candles
    except Exception:
        # Network unreachable or yfinance uninstalled
        pass

    # 2. Offline fallback to bundled sample datasets
    if use_sample_fallback:
        clean_sym = symbol.upper().replace("^", "")
        if "BANK" in clean_sym:
            sample_file = DATA_DIR / "sample_banknifty_daily.csv"
        else:
            sample_file = DATA_DIR / "sample_nifty50_daily.csv"

        if sample_file.exists():
            return load_candles_from_csv(str(sample_file))

    return candles
