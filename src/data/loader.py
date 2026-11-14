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


STOCK_BASE_PRICES: Dict[str, float] = {
    "^NSEI": 25210.0,
    "^NSEBANK": 61250.0,
    "RELIANCE.NS": 1270.0,
    "TCS.NS": 4130.0,
    "HDFCBANK.NS": 1745.0,
    "ICICIBANK.NS": 1260.0,
    "INFY.NS": 1845.0,
    "BHARTIARTL.NS": 1580.0,
    "SBIN.NS": 820.0,
    "ITC.NS": 475.0,
    "LT.NS": 3580.0,
    "HINDUNILVR.NS": 2450.0,
    "BAJFINANCE.NS": 6950.0,
    "TATAMOTORS.NS": 795.0,
    "KOTAKBANK.NS": 1760.0,
    "AXISBANK.NS": 1150.0,
    "HCLTECH.NS": 1820.0,
    "SUNPHARMA.NS": 1780.0,
    "MARUTI.NS": 11400.0,
    "M&M.NS": 2890.0,
    "TITAN.NS": 3250.0,
    "NTPC.NS": 385.0,
    "ONGC.NS": 260.0,
    "POWERGRID.NS": 320.0,
    "ADANIENT.NS": 2950.0,
    "ADANIPORTS.NS": 1280.0,
    "TATASTEEL.NS": 145.0,
    "JSWSTEEL.NS": 940.0,
    "COALINDIA.NS": 410.0,
    "BAJAJFINSV.NS": 1620.0,
    "ASIANPAINT.NS": 2450.0,
    "ULTRACEMCO.NS": 11100.0,
    "WIPRO.NS": 560.0,
    "TECHM.NS": 1680.0,
    "LTIM.NS": 5900.0,
    "NESTLEIND.NS": 2250.0,
    "BRITANNIA.NS": 4950.0,
    "TATACONSUM.NS": 940.0,
    "CIPLA.NS": 1520.0,
    "DRREDDY.NS": 1220.0,
    "APOLLOHOSP.NS": 6950.0,
    "DIVISLAB.NS": 5850.0,
    "EICHERMOT.NS": 4850.0,
    "BAJAJ-AUTO.NS": 9200.0,
    "HEROMOTOCO.NS": 4650.0,
    "BPCL.NS": 310.0,
    "GRASIM.NS": 2550.0,
    "HINDALCO.NS": 645.0,
    "INDUSINDBK.NS": 1020.0,
    "SHRIRAMFIN.NS": 3150.0,
    "BEL.NS": 295.0,
    "TRENT.NS": 6400.0
}


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
        # Yahoo Finance requires short period for intraday intervals
        if interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h") and period in ("1y", "2y", "max"):
            period = "5d"

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty:
            is_intraday = ("m" in interval) or ("h" in interval)
            for index, row in df.iterrows():
                if hasattr(index, "strftime"):
                    ts = index.strftime("%Y-%m-%d %H:%M") if is_intraday else index.strftime("%Y-%m-%d")
                else:
                    ts = str(index)

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
            base_ref = 61250.0
        else:
            sample_file = DATA_DIR / "sample_nifty50_daily.csv"
            base_ref = 25210.0

        if sample_file.exists():
            raw_candles = load_candles_from_csv(str(sample_file))
            if "^" in symbol:
                mult = 1.0
            else:
                target_base = STOCK_BASE_PRICES.get(symbol.upper(), 1500.0)
                mult = target_base / base_ref

            scaled_candles = []
            for c in raw_candles:
                scaled_candles.append(Candle(
                    timestamp=c.timestamp,
                    open=round(c.open * mult, 2),
                    high=round(c.high * mult, 2),
                    low=round(c.low * mult, 2),
                    close=round(c.close * mult, 2),
                    volume=round(c.volume * 0.05) if "^" not in symbol else c.volume
                ))
            return scaled_candles

    return candles
