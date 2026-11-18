"""
Zerodha Kite Connect Data Loader for Real-Time NSE Market Data.
Fetches live OHLCV candles for NIFTY 50, BANK NIFTY, and constituent stocks
using the official Zerodha Kite Connect API.

Setup:
  1. Login to https://kite.trade
  2. Create an App and get your API Key & API Secret
  3. Generate your daily Access Token
  4. Save credentials in config/zerodha_credentials.json:
     {"api_key": "YOUR_KEY", "access_token": "YOUR_TOKEN"}
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from src.data.types import Candle

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

# Zerodha Instrument Tokens (NSE)
ZERODHA_TOKEN_MAP = {
    "^NSEI": 256265,         # NIFTY 50 Index
    "^NSEBANK": 260105,      # NIFTY BANK Index
    "RELIANCE.NS": 738561,   # RELIANCE
    "TCS.NS": 2953217,       # TCS
    "HDFCBANK.NS": 341249,   # HDFCBANK
    "ICICIBANK.NS": 1270529, # ICICIBANK
    "INFY.NS": 408065,       # INFY
    "SBIN.NS": 779521,       # SBIN
    "BHARTIARTL.NS": 2714625,# BHARTIARTL
    "ITC.NS": 424961,        # ITC
    "LT.NS": 2939649,        # LT
    "TATAMOTORS.NS": 884737, # TATAMOTORS
}


def _load_zerodha_credentials() -> Dict[str, str]:
    api_key = os.environ.get("KITE_API_KEY", "")
    access_token = os.environ.get("KITE_ACCESS_TOKEN", "")
    if api_key and access_token:
        return {"api_key": api_key, "access_token": access_token}

    cred_file = CONFIG_DIR / "zerodha_credentials.json"
    if cred_file.exists():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "api_key": data.get("api_key", ""),
                    "access_token": data.get("access_token", "")
                }
        except Exception:
            pass
    return {"api_key": "", "access_token": ""}


def is_zerodha_configured() -> bool:
    creds = _load_zerodha_credentials()
    return bool(creds["api_key"] and creds["access_token"])


def fetch_zerodha_candles(symbol: str, interval: str = "5minute", days: int = 5) -> List[Candle]:
    token = ZERODHA_TOKEN_MAP.get(symbol)
    if not token:
        return []

    creds = _load_zerodha_credentials()
    if not creds["api_key"] or not creds["access_token"]:
        return []

    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=creds["api_key"])
        kite.set_access_token(creds["access_token"])

        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        z_interval = "5minute" if "5" in interval else ("15minute" if "15" in interval else ("day" if "d" in interval else "5minute"))
        records = kite.historical_data(token, from_date, to_date, z_interval)

        candles: List[Candle] = []
        for r in records:
            ts = r["date"].strftime("%Y-%m-%d %H:%M") if hasattr(r["date"], "strftime") else str(r["date"])
            candles.append(Candle(
                timestamp=ts,
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r.get("volume", 0.0))
            ))
        return candles
    except Exception as e:
        print(f"⚠️ Zerodha Kite error for {symbol}: {e}")
        return []
