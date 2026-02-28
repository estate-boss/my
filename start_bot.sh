#!/bin/bash
# Aggressive Profit Hunter Bot - Unix/Linux Startup Script
# Run: chmod +x start_bot.sh && ./start_bot.sh

echo ""
echo "=========================================="
echo "AGGRESSIVE PROFIT HUNTER BOT - Startup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install from python.org"
    exit 1
fi

echo "$(python3 --version)"

# Check .env
if [ ! -f ".env" ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "ACTION: cp .env.example .env && nano .env"
    echo ""
    exit 1
fi

echo "✓ .env file found"

# Check dependencies
echo ""
echo "Checking dependencies..."
python3 -m pip show python-telegram-bot > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Dependencies not installed"
    echo "ACTION: pip install -r requirements.txt"
    echo ""
    exit 1
fi

echo "✓ Dependencies installed"

# Safety checks
echo ""
echo "==========================================="
echo "⚠️  IMPORTANT SAFETY CHECKS:"
echo "==========================================="
echo "[1] Paper mode enabled? (PAPER_MODE=true)"
echo "[2] .env keys complete?"
echo "[3] You understand liquidation risk?"
echo "[4] Testnet account created?"
echo "[5] .env backed up safely?"
echo ""

read -p "Ready to start? (type 'yes'): " ready
if [ "$ready" != "yes" ]; then
    echo "Startup cancelled."
    exit 0
fi

echo ""
echo "🚀 Starting bot..."
echo "Listen to Telegram for messages"
echo "Press Ctrl+C to stop"
echo ""

python3 telegram_bybit_profit_hunter.py
