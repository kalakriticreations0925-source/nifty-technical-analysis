"""
Resolves correct Dhan security IDs from the official scrip master CSV.
Run this once to verify/update the DHAN_SYMBOL_MAP in dhan_loader.py.

Usage: python resolve_dhan_ids.py
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


# Our symbols and their NSE trading symbol equivalents
SYMBOL_TO_NSE = {
    "^NSEI": ("NIFTY 50", "IDX_I"),
    "^NSEBANK": ("NIFTY BANK", "IDX_I"),
    "RELIANCE.NS": ("RELIANCE", "NSE_EQ"),
    "TCS.NS": ("TCS", "NSE_EQ"),
    "HDFCBANK.NS": ("HDFCBANK", "NSE_EQ"),
    "ICICIBANK.NS": ("ICICIBANK", "NSE_EQ"),
    "INFY.NS": ("INFY", "NSE_EQ"),
    "BHARTIARTL.NS": ("BHARTIARTL", "NSE_EQ"),
    "SBIN.NS": ("SBIN", "NSE_EQ"),
    "ITC.NS": ("ITC", "NSE_EQ"),
    "LT.NS": ("LT", "NSE_EQ"),
    "HINDUNILVR.NS": ("HINDUNILVR", "NSE_EQ"),
    "BAJFINANCE.NS": ("BAJFINANCE", "NSE_EQ"),
    "TATAMOTORS.NS": ("TATAMOTORS", "NSE_EQ"),
    "KOTAKBANK.NS": ("KOTAKBANK", "NSE_EQ"),
    "AXISBANK.NS": ("AXISBANK", "NSE_EQ"),
    "HCLTECH.NS": ("HCLTECH", "NSE_EQ"),
    "SUNPHARMA.NS": ("SUNPHARMA", "NSE_EQ"),
    "MARUTI.NS": ("MARUTI", "NSE_EQ"),
    "M&M.NS": ("M&M", "NSE_EQ"),
    "TITAN.NS": ("TITAN", "NSE_EQ"),
    "NTPC.NS": ("NTPC", "NSE_EQ"),
    "ONGC.NS": ("ONGC", "NSE_EQ"),
    "POWERGRID.NS": ("POWERGRID", "NSE_EQ"),
    "ADANIENT.NS": ("ADANIENT", "NSE_EQ"),
    "ADANIPORTS.NS": ("ADANIPORTS", "NSE_EQ"),
    "TATASTEEL.NS": ("TATASTEEL", "NSE_EQ"),
    "JSWSTEEL.NS": ("JSWSTEEL", "NSE_EQ"),
    "COALINDIA.NS": ("COALINDIA", "NSE_EQ"),
    "BAJAJFINSV.NS": ("BAJAJFINSV", "NSE_EQ"),
    "ASIANPAINT.NS": ("ASIANPAINT", "NSE_EQ"),
    "ULTRACEMCO.NS": ("ULTRACEMCO", "NSE_EQ"),
    "WIPRO.NS": ("WIPRO", "NSE_EQ"),
    "TECHM.NS": ("TECHM", "NSE_EQ"),
    "LTIM.NS": ("LTIM", "NSE_EQ"),
    "NESTLEIND.NS": ("NESTLEIND", "NSE_EQ"),
    "BRITANNIA.NS": ("BRITANNIA", "NSE_EQ"),
    "TATACONSUM.NS": ("TATACONSUM", "NSE_EQ"),
    "CIPLA.NS": ("CIPLA", "NSE_EQ"),
    "DRREDDY.NS": ("DRREDDY", "NSE_EQ"),
    "APOLLOHOSP.NS": ("APOLLOHOSP", "NSE_EQ"),
    "DIVISLAB.NS": ("DIVISLAB", "NSE_EQ"),
    "EICHERMOT.NS": ("EICHERMOT", "NSE_EQ"),
    "BAJAJ-AUTO.NS": ("BAJAJ-AUTO", "NSE_EQ"),
    "HEROMOTOCO.NS": ("HEROMOTOCO", "NSE_EQ"),
    "BPCL.NS": ("BPCL", "NSE_EQ"),
    "GRASIM.NS": ("GRASIM", "NSE_EQ"),
    "HINDALCO.NS": ("HINDALCO", "NSE_EQ"),
    "INDUSINDBK.NS": ("INDUSINDBK", "NSE_EQ"),
    "SHRIRAMFIN.NS": ("SHRIRAMFIN", "NSE_EQ"),
    "BEL.NS": ("BEL", "NSE_EQ"),
    "TRENT.NS": ("TRENT", "NSE_EQ"),
}


def main():
    try:
        import pandas as pd
    except ImportError:
        print("Installing pandas...")
        os.system(f"{sys.executable} -m pip install pandas")
        import pandas as pd

    print("Downloading Dhan Scrip Master CSV...")
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"

    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return

    print(f"Loaded {len(df)} instruments from Dhan scrip master")
    print()
    print("=" * 80)
    print(f"{'Our Symbol':<20} {'NSE Symbol':<15} {'Security ID':<12} {'Segment':<10} {'Status'}")
    print("=" * 80)

    resolved = {}
    for our_sym, (nse_sym, expected_seg) in SYMBOL_TO_NSE.items():
        if expected_seg == "IDX_I":
            # Index lookup
            matches = df[
                (df["SEM_TRADING_SYMBOL"].str.upper() == nse_sym.upper()) &
                (df["SEM_SEGMENT"].str.upper().isin(["I", "IDX"]))
            ]
        else:
            # Equity lookup
            matches = df[
                (df["SEM_TRADING_SYMBOL"].str.upper() == nse_sym.upper()) &
                (df["SEM_EXM_EXCH_ID"].str.upper() == "NSE") &
                (df["SEM_SEGMENT"].str.upper() == "E")
            ]

        if not matches.empty:
            sec_id = str(matches.iloc[0]["SEM_SMST_SECURITY_ID"])
            status = "✅ FOUND"
            resolved[our_sym] = sec_id
        else:
            sec_id = "???"
            status = "❌ NOT FOUND"

        print(f"{our_sym:<20} {nse_sym:<15} {sec_id:<12} {expected_seg:<10} {status}")

    print("=" * 80)
    print(f"\nResolved: {len(resolved)}/{len(SYMBOL_TO_NSE)} symbols")

    if resolved:
        print("\n--- Copy-paste ready DHAN_SYMBOL_MAP update ---")
        print("DHAN_SYMBOL_MAP = {")
        for our_sym, sec_id in resolved.items():
            nse_sym, seg = SYMBOL_TO_NSE[our_sym]
            inst = "INDEX" if seg == "IDX_I" else "EQUITY"
            print(f'    "{our_sym}": {{"security_id": "{sec_id}", "segment": "{seg}", "instrument": "{inst}", "dhan_name": "{nse_sym}"}},')
        print("}")


if __name__ == "__main__":
    main()
