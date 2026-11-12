@echo off
title Nifty Trading Signals - 1-Click Scanner
color 0A

echo ===================================================================
echo     NIFTY 50 & INDIAN EQUITIES - AUTOMATED SIGNAL SCANNER
echo ===================================================================
echo.
echo [1/2] Scanning market data and calculating technical indicators...
echo       (Supertrend, RSI, MACD, Bollinger Bands, Volume)
echo.

python "%~dp0src\cli.py" scan --symbol ALL --strategy confluence --export-js "%~dp0dashboard_data.js" --export-json "%~dp0dashboard_data.json" --export-md "%~dp0reports\LATEST_SIGNALS.md"

echo.
echo [2/2] Launching your Visual Dashboard in browser...
start "" "%~dp0dashboard.html"

echo.
echo ===================================================================
echo [DONE] Dashboard opened in your browser!
echo You can close this window now.
echo ===================================================================
timeout /t 5 >nul
