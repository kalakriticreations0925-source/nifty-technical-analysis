@echo off
title Nifty Trading Signals - 1-Click Scanner
color 0A

echo ===================================================================
echo     NIFTY 50 & INDIAN EQUITIES - AUTOMATED SIGNAL SCANNER
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
if not defined PY_BIN set "PY_BIN=python"

"%PY_BIN%" -m pip install yfinance curl_cffi >nul 2>&1

echo [1/2] Scanning NIFTY 50, BANK NIFTY & all constituent stocks...
echo       (Supertrend, RSI, MACD, Bollinger Bands, Volume)
echo.

"%PY_BIN%" "%~dp0src\cli.py" scan --symbol ALL --strategy confluence --interval 5m --export-js "%~dp0dashboard_data.js" --export-json "%~dp0dashboard_data.json" --export-md "%~dp0reports\LATEST_SIGNALS.md"

echo.
echo [2/2] Launching your Visual Dashboard in browser...
start "" "%~dp0NIFTY_TECHNICAL_ANALYSIS_DASHBOARD.html"

echo.
echo ===================================================================
echo [DONE] Dashboard opened in your browser!
echo You can close this window now.
echo ===================================================================
timeout /t 5 >nul
