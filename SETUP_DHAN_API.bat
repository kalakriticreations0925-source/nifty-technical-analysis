@echo off
title Dhan API Setup - Nifty Trading Desk
color 0E

echo ===================================================================
echo     DHAN API SETUP - REAL-TIME NSE MARKET DATA
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

"%PY_BIN%" "%~dp0setup_dhan.py"

echo.
echo ===================================================================
echo Press any key to close...
pause >nul
