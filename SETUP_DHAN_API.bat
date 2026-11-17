@echo off
title Dhan API Setup - Nifty Trading Desk
color 0E

echo ===================================================================
echo     DHAN API SETUP - REAL-TIME NSE MARKET DATA
echo ===================================================================
echo.
echo This will:
echo   1. Install dhanhq Python package
echo   2. Validate your API credentials
echo   3. Test live market data connection
echo.

pip install dhanhq
echo.

python "%~dp0setup_dhan.py"

echo.
echo ===================================================================
echo Press any key to close...
pause >nul
