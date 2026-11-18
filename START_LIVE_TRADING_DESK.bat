@echo off
title NIFTY & BANK NIFTY - Live 5-Minute Trading Desk
color 0B

echo ===================================================================
echo       NIFTY 50 ^& BANK NIFTY - LIVE INTRADAY TRADING DESK
echo       Multi-Source: Dhan API / Zerodha Kite / Live Scan Engine
echo ===================================================================
echo.

:: Detect Python executable
set "PY_BIN="
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not defined PY_BIN if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PY_BIN if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY_BIN if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PY_BIN if exist "%ProgramFiles%\Python314\python.exe" set "PY_BIN=%ProgramFiles%\Python314\python.exe"
if not defined PY_BIN if exist "%ProgramFiles%\Python313\python.exe" set "PY_BIN=%ProgramFiles%\Python313\python.exe"
if not defined PY_BIN if exist "%ProgramFiles%\Python312\python.exe" set "PY_BIN=%ProgramFiles%\Python312\python.exe"
if not defined PY_BIN set "PY_BIN=python"

echo [0/3] Ensuring live market feed engine is ready...
"%PY_BIN%" -m pip install yfinance curl_cffi >nul 2>&1

echo [1/3] Launching your Live Trading Terminal in Browser...
start "" "%~dp0NIFTY_TECHNICAL_ANALYSIS_DASHBOARD.html"

echo.
echo [2/3] Performing initial live market scan (5-Minute Candles)...
"%PY_BIN%" "%~dp0src\cli.py" scan --symbol ALL --strategy confluence --interval 5m --export-js "%~dp0dashboard_data.js" --export-json "%~dp0dashboard_data.json" --export-md "%~dp0reports\LIVE_SIGNALS.md"

echo.
echo ===================================================================
echo [3/3] ACTIVE: Continuous Live Scanner Running!
echo       - NIFTY 50, BANK NIFTY ^& all constituent shares are tracked.
echo       - Auto-refreshing technical indicators every 5 minutes.
echo       - Leave this window open in the background.
echo       - Press Ctrl+C to stop scanning anytime.
echo ===================================================================
echo.

:LOOP
echo [%TIME%] Rescanning Live Market (NIFTY 50, BANK NIFTY ^& Top 50 Stocks)...
"%PY_BIN%" "%~dp0src\cli.py" scan --symbol ALL --strategy confluence --interval 5m --export-js "%~dp0dashboard_data.js" --export-json "%~dp0dashboard_data.json" --export-md "%~dp0reports\LIVE_SIGNALS.md"

echo [UPDATED] Signals refreshed at %TIME%!
echo Next live scan in 5 minutes (300s)...
echo.
timeout /t 300 /nobreak
goto LOOP
