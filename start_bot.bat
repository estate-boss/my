@echo off
REM Aggressive Profit Hunter Bot - Windows Startup Script
REM Run this script to start the bot safely with checks

echo.
echo ==========================================
echo AGGRESSIVE PROFIT HUNTER BOT - Startup
echo ==========================================
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo Checking Python version...
python --version

REM Check .env file exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo ACTION: Copy .env.example to .env and fill in your API keys
    echo.
    pause
    exit /b 1
)

echo ✓ .env file found

REM Check required dependencies
echo.
echo Checking dependencies...
pip show python-telegram-bot >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Dependencies not installed.
    echo ACTION: Run: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ✓ Dependencies installed

REM Final confirmation
echo.
echo ============================================
echo ⚠️  IMPORTANT SAFETY CHECKS:
echo ============================================
echo [1] Paper mode enabled in .env (PAPER_MODE=true)?
echo     → If NO, bot will trade REAL money
echo [2] .env keys filled in completely?
echo     → Missing keys = bot will fail
echo [3] You understand the RISKS?
echo     → High leverage = liquidation possible
echo [4] Bybit testnet account created (for testing)?
echo [5] You have backed up .env somewhere safe?
echo.

set /p ready="Ready to start? (type 'yes' to continue): "
if /i not "%ready%"=="yes" (
    echo Startup cancelled.
    pause
    exit /b 0
)

echo.
echo 🚀 Starting bot...
echo Listen to wallet: Open Telegram to see messages
echo Press Ctrl+C to stop bot
echo.

python telegram_bybit_profit_hunter.py

pause
