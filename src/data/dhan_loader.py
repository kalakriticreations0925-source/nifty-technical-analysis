"""
Dhan API Data Loader for Real-Time NSE Market Data.
Fetches live OHLCV candles for NIFTY 50, BANK NIFTY, and all 50 constituent stocks
using the official DhanHQ API.

Requirements:
  pip install dhanhq

Setup:
  1. Create a free Dhan account at https://dhan.co
  2. Generate API credentials at https://dhanhq.co/
  3. Set environment variables:
     DHAN_CLIENT_ID=your_client_id
     DHAN_ACCESS_TOKEN=your_access_token
  Or create a file: config/dhan_credentials.json
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from src.data.types import Candle

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


# ═══════════════════════════════════════════════════════════════
# DHAN SECURITY ID MAPPING (NSE Equities + Indices)
# Source: https://images.dhan.co/api-data/api-scrip-master.csv
# ═══════════════════════════════════════════════════════════════

# Indices use segment IDX_I, instrument_type INDEX
# Equities use segment NSE_EQ, instrument_type EQUITY

DHAN_SYMBOL_MAP: Dict[str, Dict[str, Any]] = {
    # ── Benchmark Indices ──
    "^NSEI":          {"security_id": "13",    "segment": "IDX_I",  "instrument": "INDEX",  "dhan_name": "NIFTY 50"},
    "^NSEBANK":       {"security_id": "25",    "segment": "IDX_I",  "instrument": "INDEX",  "dhan_name": "NIFTY BANK"},

    # ── NIFTY 50 Constituent Stocks (NSE_EQ) ──
    "RELIANCE.NS":    {"security_id": "2885",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "RELIANCE"},
    "TCS.NS":         {"security_id": "11536", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TCS"},
    "HDFCBANK.NS":    {"security_id": "1333",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "HDFCBANK"},
    "ICICIBANK.NS":   {"security_id": "4963",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ICICIBANK"},
    "INFY.NS":        {"security_id": "1594",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "INFOSYS"},
    "BHARTIARTL.NS":  {"security_id": "10604", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BHARTIARTL"},
    "SBIN.NS":        {"security_id": "3045",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "SBIN"},
    "ITC.NS":         {"security_id": "1660",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ITC"},
    "LT.NS":          {"security_id": "11483", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "LT"},
    "HINDUNILVR.NS":  {"security_id": "1394",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "HINDUNILVR"},
    "BAJFINANCE.NS":  {"security_id": "317",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BAJFINANCE"},
    "TATAMOTORS.NS":  {"security_id": "3456",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TATAMOTORS"},
    "KOTAKBANK.NS":   {"security_id": "1922",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "KOTAKBANK"},
    "AXISBANK.NS":    {"security_id": "5900",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "AXISBANK"},
    "HCLTECH.NS":     {"security_id": "7229",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "HCLTECH"},
    "SUNPHARMA.NS":   {"security_id": "3351",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "SUNPHARMA"},
    "MARUTI.NS":      {"security_id": "10999", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "MARUTI"},
    "M&M.NS":         {"security_id": "2031",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "M&M"},
    "TITAN.NS":       {"security_id": "3506",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TITAN"},
    "NTPC.NS":        {"security_id": "11630", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "NTPC"},
    "ONGC.NS":        {"security_id": "2475",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ONGC"},
    "POWERGRID.NS":   {"security_id": "14977", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "POWERGRID"},
    "ADANIENT.NS":    {"security_id": "25",    "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ADANIENT"},
    "ADANIPORTS.NS":  {"security_id": "15083", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ADANIPORTS"},
    "TATASTEEL.NS":   {"security_id": "3499",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TATASTEEL"},
    "JSWSTEEL.NS":    {"security_id": "11723", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "JSWSTEEL"},
    "COALINDIA.NS":   {"security_id": "20374", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "COALINDIA"},
    "BAJAJFINSV.NS":  {"security_id": "16675", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BAJAJFINSV"},
    "ASIANPAINT.NS":  {"security_id": "236",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ASIANPAINT"},
    "ULTRACEMCO.NS":  {"security_id": "11532", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "ULTRACEMCO"},
    "WIPRO.NS":       {"security_id": "3787",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "WIPRO"},
    "TECHM.NS":       {"security_id": "13538", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TECHM"},
    "LTIM.NS":        {"security_id": "17818", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "LTIM"},
    "NESTLEIND.NS":   {"security_id": "17963", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "NESTLEIND"},
    "BRITANNIA.NS":   {"security_id": "547",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BRITANNIA"},
    "TATACONSUM.NS":  {"security_id": "3432",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TATACONSUM"},
    "CIPLA.NS":       {"security_id": "694",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "CIPLA"},
    "DRREDDY.NS":     {"security_id": "881",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "DRREDDY"},
    "APOLLOHOSP.NS":  {"security_id": "157",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "APOLLOHOSP"},
    "DIVISLAB.NS":    {"security_id": "10940", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "DIVISLAB"},
    "EICHERMOT.NS":   {"security_id": "910",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "EICHERMOT"},
    "BAJAJ-AUTO.NS":  {"security_id": "16669", "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BAJAJ-AUTO"},
    "HEROMOTOCO.NS":  {"security_id": "1348",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "HEROMOTOCO"},
    "BPCL.NS":        {"security_id": "526",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BPCL"},
    "GRASIM.NS":      {"security_id": "1232",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "GRASIM"},
    "HINDALCO.NS":    {"security_id": "1363",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "HINDALCO"},
    "INDUSINDBK.NS":  {"security_id": "5258",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "INDUSINDBK"},
    "SHRIRAMFIN.NS":  {"security_id": "4306",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "SHRIRAMFIN"},
    "BEL.NS":         {"security_id": "383",   "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "BEL"},
    "TRENT.NS":       {"security_id": "1964",  "segment": "NSE_EQ", "instrument": "EQUITY", "dhan_name": "TRENT"},
}


def _load_credentials() -> Dict[str, str]:
    """
    Loads Dhan API credentials from environment variables or config file.
    Priority: ENV vars > config/dhan_credentials.json
    """
    client_id = os.environ.get("DHAN_CLIENT_ID", "")
    access_token = os.environ.get("DHAN_ACCESS_TOKEN", "")

    if client_id and access_token:
        return {"client_id": client_id, "access_token": access_token}

    # Fallback to config file
    cred_file = CONFIG_DIR / "dhan_credentials.json"
    if cred_file.exists():
        with open(cred_file, "r", encoding="utf-8") as f:
            creds = json.load(f)
            return {
                "client_id": creds.get("client_id", ""),
                "access_token": creds.get("access_token", "")
            }

    return {"client_id": "", "access_token": ""}


def _get_dhan_client():
    """Creates and returns authenticated DhanHQ client."""
    creds = _load_credentials()
    if not creds["client_id"] or not creds["access_token"]:
        raise ValueError(
            "Dhan API credentials not found!\n"
            "Setup: Create config/dhan_credentials.json with:\n"
            '  {"client_id": "YOUR_ID", "access_token": "YOUR_TOKEN"}\n'
            "Or set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN environment variables.\n"
            "Get your free API key at: https://dhanhq.co/"
        )

    from dhanhq import dhanhq
    return dhanhq(creds["client_id"], creds["access_token"])


def _parse_dhan_candles(response: Dict, symbol: str, is_intraday: bool = True) -> List[Candle]:
    """
    Parses Dhan API OHLCV response into our Candle dataclass list.
    Dhan returns: {'data': {'open': [...], 'high': [...], 'low': [...], 'close': [...], 'volume': [...], 'start_Time': [...]}}
    """
    candles: List[Candle] = []

    if not response or response.get("status") != "success":
        return candles

    data = response.get("data", {})
    if not data:
        return candles

    opens = data.get("open", [])
    highs = data.get("high", [])
    lows = data.get("low", [])
    closes = data.get("close", [])
    volumes = data.get("volume", [])
    timestamps = data.get("start_Time", data.get("timestamp", []))

    n = min(len(opens), len(highs), len(lows), len(closes))
    if n == 0:
        return candles

    for i in range(n):
        # Parse timestamp
        ts_raw = timestamps[i] if i < len(timestamps) else ""
        if isinstance(ts_raw, (int, float)):
            # Epoch seconds
            dt = datetime.fromtimestamp(ts_raw)
            ts = dt.strftime("%Y-%m-%d %H:%M") if is_intraday else dt.strftime("%Y-%m-%d")
        elif isinstance(ts_raw, str):
            ts = ts_raw
        else:
            ts = str(ts_raw)

        candles.append(Candle(
            timestamp=ts,
            open=float(opens[i]),
            high=float(highs[i]),
            low=float(lows[i]),
            close=float(closes[i]),
            volume=float(volumes[i]) if i < len(volumes) else 0.0
        ))

    return candles


def fetch_dhan_intraday(symbol: str, interval: str = "5m") -> List[Candle]:
    """
    Fetches intraday minute-level OHLCV candles from Dhan API.
    Available for the last 5 trading days.

    Args:
        symbol: Our internal symbol (e.g., '^NSEI', 'RELIANCE.NS')
        interval: Candle interval ('1m', '5m', '15m', '25m', '60m')

    Returns:
        List of Candle objects sorted chronologically
    """
    mapping = DHAN_SYMBOL_MAP.get(symbol)
    if not mapping:
        print(f"⚠️  Symbol {symbol} not found in Dhan mapping")
        return []

    try:
        dhan = _get_dhan_client()
        response = dhan.intraday_minute_data(
            security_id=mapping["security_id"],
            exchange_segment=mapping["segment"],
            instrument_type=mapping["instrument"]
        )
        candles = _parse_dhan_candles(response, symbol, is_intraday=True)

        # Filter to requested interval if not 1m
        if interval != "1m" and candles:
            candles = _resample_candles(candles, interval)

        return candles

    except Exception as e:
        print(f"❌ Dhan API error for {symbol}: {e}")
        return []


def fetch_dhan_daily(symbol: str, days: int = 365) -> List[Candle]:
    """
    Fetches historical daily OHLCV candles from Dhan API.

    Args:
        symbol: Our internal symbol (e.g., '^NSEI', 'RELIANCE.NS')
        days: Number of days of history to fetch

    Returns:
        List of Candle objects sorted chronologically
    """
    mapping = DHAN_SYMBOL_MAP.get(symbol)
    if not mapping:
        print(f"⚠️  Symbol {symbol} not found in Dhan mapping")
        return []

    try:
        dhan = _get_dhan_client()
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = dhan.historical_daily_data(
            security_id=mapping["security_id"],
            exchange_segment=mapping["segment"],
            instrument_type=mapping["instrument"],
            expiry_code=0,
            from_date=from_date,
            to_date=to_date
        )
        return _parse_dhan_candles(response, symbol, is_intraday=False)

    except Exception as e:
        print(f"❌ Dhan API error for {symbol}: {e}")
        return []


def _resample_candles(candles: List[Candle], interval: str) -> List[Candle]:
    """
    Resamples 1-minute candles to larger intervals (5m, 15m, 25m, 60m).
    """
    interval_map = {"5m": 5, "15m": 15, "25m": 25, "30m": 30, "60m": 60, "1h": 60}
    minutes = interval_map.get(interval, 5)

    if not candles:
        return candles

    resampled: List[Candle] = []
    chunk: List[Candle] = []

    for c in candles:
        chunk.append(c)
        if len(chunk) >= minutes:
            merged = Candle(
                timestamp=chunk[0].timestamp,
                open=chunk[0].open,
                high=max(x.high for x in chunk),
                low=min(x.low for x in chunk),
                close=chunk[-1].close,
                volume=sum(x.volume for x in chunk)
            )
            resampled.append(merged)
            chunk = []

    # Handle remaining candles
    if chunk:
        merged = Candle(
            timestamp=chunk[0].timestamp,
            open=chunk[0].open,
            high=max(x.high for x in chunk),
            low=min(x.low for x in chunk),
            close=chunk[-1].close,
            volume=sum(x.volume for x in chunk)
        )
        resampled.append(merged)

    return resampled


def is_dhan_configured() -> bool:
    """Check if Dhan API credentials are available."""
    creds = _load_credentials()
    return bool(creds["client_id"] and creds["access_token"])


def validate_dhan_connection() -> Dict[str, Any]:
    """
    Validates Dhan API connection by fetching NIFTY 50 index data.
    Returns status dict.
    """
    try:
        if not is_dhan_configured():
            return {"status": "error", "message": "Dhan credentials not configured"}

        dhan = _get_dhan_client()
        response = dhan.intraday_minute_data(
            security_id="13",
            exchange_segment="IDX_I",
            instrument_type="INDEX"
        )

        if response and response.get("status") == "success":
            data = response.get("data", {})
            n = len(data.get("close", []))
            last_price = data["close"][-1] if n > 0 else 0
            return {
                "status": "success",
                "message": f"Connected! NIFTY 50 LTP: ₹{last_price:,.2f} ({n} candles)",
                "ltp": last_price,
                "candle_count": n
            }
        else:
            return {"status": "error", "message": f"API returned: {response.get('remarks', 'Unknown error')}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
