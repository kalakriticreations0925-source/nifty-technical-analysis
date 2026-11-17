# 🚀 Dhan API Setup Guide - Live Real-Time NSE Trading Desk

This trading setup is now officially powered by the **DhanHQ API** for real-time, live NSE market data (both 5-minute intraday candles and daily historical data).

---

## ⚡ Quick 3-Step Setup (Takes 2 Minutes)

### Step 1: Get Your Free Dhan API Credentials
1. If you don't already have a Dhan account, open one at [dhan.co](https://dhan.co) (Account opening and API access are **100% Free**).
2. Go to the developer portal: [dhanhq.co](https://dhanhq.co/)
3. Log in with your Dhan credentials.
4. Note your **Client ID** (found on your profile/dashboard).
5. Click **Generate Access Token** (valid for 24 hours or 30 days depending on token type).

---

### Step 2: Add Credentials to Project
You have two easy options:

#### Option A: Edit the Config File (Recommended)
Open `config/dhan_credentials.json` in Notepad or any editor:
```json
{
  "client_id": "YOUR_DHAN_CLIENT_ID",
  "access_token": "YOUR_DHAN_ACCESS_TOKEN"
}
```
*(Save and close the file)*

#### Option B: Set Environment Variables
In PowerShell or Command Prompt:
```cmd
set DHAN_CLIENT_ID=YOUR_CLIENT_ID
set DHAN_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
```

---

### Step 3: Run the Setup & Test Connection
Double-click:
```
SETUP_DHAN_API.bat
```
This script will:
* Automatically install the official `dhanhq` Python library.
* Test your API connection against live NSE data for NIFTY 50 and BANK NIFTY.
* Confirm that your setup is ready to stream.

---

## 🖥️ How to Run Your Trading Desk

### 1. Full Live Automated Desk (Recommended)
Double-click:
```
START_LIVE_TRADING_DESK.bat
```
* **[1/3]** Opens your interactive visual dashboard `NIFTY_TECHNICAL_ANALYSIS_DASHBOARD.html` in your browser.
* **[2/3]** Runs an initial scan across NIFTY 50, BANK NIFTY, and all 50 constituent stocks using 5-minute candles from the Dhan API.
* **[3/3]** Runs continuously in the background, re-scanning every 5 minutes and automatically updating your browser dashboard without you having to click refresh!

### 2. View Dashboard Only
Double-click:
```
VIEW_DASHBOARD.bat
```
Opens the browser dashboard displaying current technical analysis, BUY/SELL signals (1:1 Risk-to-Reward), and the Pro Candlestick chart engine.

---

## 📊 What You Get Live
* **Real-time NSE LTP & Intraday Candles:** Direct from NSE via Dhan's institutional-grade API.
* **1:1 Risk-to-Reward:** Every BUY/SELL target and stop loss is mathematically calibrated to 1:1.
* **Zero TradingView Popups:** Fast HTML5 Canvas engine with Supertrend (10, 3.0), 20 EMA, 50 EMA, and Volume.
* **Continuous Auto-Refresh:** Browser updates every 5 seconds silently in the background when the scanner updates data.
