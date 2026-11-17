"""
Dhan API Setup & Validation Script.
Run this after adding your credentials to config/dhan_credentials.json
to verify connectivity and resolve correct security IDs.

Usage:
  python setup_dhan.py
"""
import sys
import os
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

CONFIG_DIR = Path(__file__).parent / "config"
CRED_FILE = CONFIG_DIR / "dhan_credentials.json"


def main():
    print("=" * 65)
    print("   DHAN API SETUP & VALIDATION")
    print("   Real-Time NSE Market Data for Nifty Trading Desk")
    print("=" * 65)
    print()

    # Step 1: Check credentials file
    if not CRED_FILE.exists():
        print("❌ config/dhan_credentials.json not found!")
        print("   Creating template...")
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(CRED_FILE, "w") as f:
            json.dump({
                "client_id": "",
                "access_token": "",
                "_instructions": "Get your free API key at https://dhanhq.co/"
            }, f, indent=2)
        print(f"   ✅ Template created at: {CRED_FILE}")
        print()
        print("📋 NEXT STEPS:")
        print("   1. Create a free Dhan account at https://dhan.co")
        print("   2. Generate API key at https://dhanhq.co/")
        print("   3. Edit config/dhan_credentials.json with your credentials")
        print("   4. Run this script again: python setup_dhan.py")
        return

    with open(CRED_FILE, "r") as f:
        creds = json.load(f)

    client_id = creds.get("client_id", "")
    access_token = creds.get("access_token", "")

    if not client_id or not access_token:
        print("❌ Credentials are empty in config/dhan_credentials.json")
        print()
        print("📋 SETUP INSTRUCTIONS:")
        print("   1. Create a free Dhan account at https://dhan.co")
        print("   2. Go to https://dhanhq.co/ and log in")
        print("   3. Generate your Client ID and Access Token")
        print("   4. Edit config/dhan_credentials.json:")
        print('      {"client_id": "YOUR_ID", "access_token": "YOUR_TOKEN"}')
        print("   5. Run this script again: python setup_dhan.py")
        return

    print(f"✅ Client ID found: {client_id[:6]}...{client_id[-4:]}")
    print(f"✅ Access Token found: {access_token[:10]}...{access_token[-6:]}")
    print()

    # Step 2: Install dhanhq if needed
    try:
        import dhanhq
        print(f"✅ dhanhq package installed (version: {dhanhq.__version__ if hasattr(dhanhq, '__version__') else 'unknown'})")
    except ImportError:
        print("⏳ Installing dhanhq package...")
        os.system(f"{sys.executable} -m pip install dhanhq")
        try:
            import dhanhq
            print("✅ dhanhq installed successfully!")
        except ImportError:
            print("❌ Failed to install dhanhq. Run: pip install dhanhq")
            return

    # Step 3: Validate connection
    print()
    print("🔌 Testing Dhan API connection...")
    from src.data.dhan_loader import validate_dhan_connection
    result = validate_dhan_connection()

    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print()
        print("🎉 SETUP COMPLETE! Your trading desk is ready.")
        print("   Run: START_LIVE_TRADING_DESK.bat")
        print("   Or:  python src/cli.py scan --symbol ALL --strategy confluence --interval 5m")
    else:
        print(f"❌ Connection failed: {result['message']}")
        print()
        print("Common fixes:")
        print("  • Check if your access token has expired (regenerate at dhanhq.co)")
        print("  • Ensure your Dhan account is active")
        print("  • Check internet connection")


if __name__ == "__main__":
    main()
