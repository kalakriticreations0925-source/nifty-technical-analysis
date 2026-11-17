@echo off
title Nifty Live Market Scanner - Dhan API (Auto-Refresh Every 5 Minutes)
color 0B

echo ===================================================================
echo        NIFTY LIVE MARKET INTRADAY AUTO-SCANNER
echo        Powered by Dhan API (Real-Time NSE Data)
echo ===================================================================
echo  This tool runs continuously in the background during market hours.
echo  It rescans Nifty, Bank Nifty ^& stocks every 5 minutes and updates
echo  your visual dashboard automatically.
echo.
echo  Press Ctrl+C to stop scanning anytime.
echo ===================================================================
echo.

pip install dhanhq >nul 2>&1

:LOOP
echo [%TIME%] Fetching latest live market candles (5-min timeframe)...
python "%~dp0src\cli.py" scan --symbol ALL --strategy confluence --interval 5m --export-js "%~dp0dashboard_data.js" --export-json "%~dp0dashboard_data.json" --export-md "%~dp0reports\LIVE_SIGNALS.md"

echo.
echo [DONE] Dashboard data updated at %TIME%!
echo Next scan in 5 minutes (300 seconds)...
echo.
timeout /t 300 /nobreak
goto LOOP
