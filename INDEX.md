# Project Index 📑

Complete overview of all files in the Aggressive Profit Hunter Bot.

---

## 📁 Project Structure

```
telegram_bybit_profit_hunter/
├── telegram_bybit_profit_hunter.py    ← MAIN BOT (run this)
├── ai_decision.py                     ← AI logic (Gemini + Groq)
├── risk_manager.py                    ← Risk controls
├── reporter.py                        ← Trade/tax reports
├── trading.py                         ← Bybit order execution
├── commands.py                        ← Telegram commands
├── db_utils.py                        ← SQLite database
│
├── requirements.txt                   ← Python dependencies
├── .env.example                       ← Template for secrets
├── .env                               ← YOUR API KEYS (keep secret!)
├── .gitignore                         ← Git ignore list
│
├── start_bot.bat                      ← Windows startup (double-click)
├── start_bot.sh                       ← Unix/Mac startup (chmod +x)
│
├── README.md                          ← Full documentation
├── QUICKSTART.md                      ← 15-min setup guide
├── TESTING.md                         ← Testnet testing guide
├── RISKS.md                           ← Complete risk disclosure
├── INDEX.md                           ← This file
│
├── trading_bot.db                     ← SQLite database (auto-created)
├── trading_bot.log                    ← Bot logs (if enabled)
└── trades_YYYYMMDD.csv               ← Exported trades (on /export)
```

---

## 📄 Core Files

### `telegram_bybit_profit_hunter.py` (970 lines)
**The main bot orchestrator.**

```python
class TradingBot:
    - initialize()          # Init DB, exchange, Telegram
    - trading_cycle()       # Main 15-min loop
    - get_trading_symbols() # Fetch high-volume + watchlist
    - process_symbol()      # Analyze + open trade
    - close_expiring_trades() # Check TP/SL, close
    - daily_report()        # Midnight WAT report
    - weekly_report()       # Sunday report
    - shutdown()            # Graceful exit
```

**Entry point:** `if __name__ == '__main__': asyncio.run(main())`

**What it does:**
1. Starts at startup: Send "🔥 Bot online" to Telegram
2. Every 15 min: Run trading_cycle (fetch symbols, get AI decisions, open trades)
3. Every midnight WAT: Send daily P&L report
4. Every Sunday midnight WAT: Send weekly summary
5. On /kill: Close all positions, shutdown

---

### `ai_decision.py` (210 lines)
**AI decision system using Gemini + Groq.**

```python
async get_ai_decision(
    symbol, current_price, change_24h, volume, volatility
) -> (decision, confidence, reason, leverage, tp, sl)
    # Calls both Gemini + Groq in parallel
    # Returns only if both agree + confidence >= threshold
    # Weights CoinGecko project updates/news heavily

async fallback_decision(symbol, change_24h, volume)
    # Simple rule if AI fails: >5% change = long, <-5% = short
```

**News integration:**
- Fetches breaking project updates/news from CoinGecko
- Includes in AI prompt for directional bias
- Strengthens signal if news + price align

**Safety:**
- Requires agreement between 2 AI models
- Confidence threshold enforced
- Fallback if both fail

---

### `risk_manager.py` (160 lines)
**Risk controls: Breakers, sizing, leverage validation.**

```python
class RiskManager:
    check_swing_breaker()           # Pause if >15% 1h swing
    check_flash_crash()             # Pause if >10% drop
    pause_symbol()                  # Pause symbol for duration
    check_balance_protection()      # Pause if drawdown >20%
    calculate_position_size()       # Dynamic sizing formula
    validate_leverage()             # Cap leverage safely
    estimate_liquidation_price()    # Warn on TP/SL
```

**Position sizing formula:**
```
size = balance × base% × conf_mult × vol_factor × loss_streak_mult
```

Example:
- Base: 3% of $10k = $300
- High confidence: × 1.2 = $360
- High volatility: × 0.7 = $252
- After 1 loss: × 0.75 = $189 USDT per trade

---

### `trading.py` (220 lines)
**Bybit exchange interface using CCXT.**

```python
class BybitTrader:
    init_markets()       # Load symbols + max leverage
    get_max_leverage()   # Fetch max lev for symbol
    get_balance()        # USDT balance
    get_ticker()         # Price, volume, bid/ask
    get_ohlcv()          # Historical candles (volatility)
    open_position()      # Buy/sell with leverage
    close_position()     # Exit & calculate P&L
    get_open_positions() # All active orders
```

**Paper mode support:**
- If `PAPER_MODE=true`: Simulates all trades without API calls
- Stores in memory, calculates P&L correctly
- Full reports generated (good for testing)

**Leverage handling:**
- Queries CCXT for symbol max leverage
- Applies 95% cap to prevent liquidation on wicks
- Sets leverage before opening position

---

### `reporter.py` (280 lines)
**Trade reports, P&L summaries, tax calculations.**

```python
class Reporter:
    format_trade_open_report()  # 🚀 LONG BTCUSDT Opened...
    format_trade_close_report() # ✅ LONG BTCUSDT Closed...
    calculate_daily_summary()   # P&L, win rate for day
    calculate_weekly_summary()  # P&L, win rate for week
    estimate_tax_fifo()        # Nigerian tax calc (10% CGT)
    format_status_report()     # Balance, return%, open pos
```

**Tax calculation (Nigeria):**
- FIFO method (first-in-first-out gains)
- 10% capital gains tax on crypto trading
- ₦800,000 (~$500) annual exemption
- Converts USD → NGN at current rate
- Includes disclaimer: "Consult tax professional"

**Report examples:**
```
🚀 LONG BTCUSDT Opened
Entry $95k | 95x Lev | Size 3.8% | AI high conf | TP +65% | Balance $10,200

✅ LONG BTCUSDT Closed
Entry $95k → Exit $98.5k | +3.7% | 50x Lev | Duration 30m | Balance $10,560

📈 Weekly Report
Trades: 12 | Win: 7 | Loss: 5 | Win Rate: 58.3%
P&L: +$560 | Fees: $4 | Net: +$556
```

---

### `commands.py` (320 lines)
**All Telegram command handlers.**

```python
# Core
cmd_start()       # /start - Initialize bot
cmd_status()      # /status - Bot status + buttons
cmd_pause()       # /pause - Pause loop
cmd_resume()      # /resume - Resume loop

# Reports
cmd_history()     # /history - Last 10 trades
cmd_report()      # /report - Daily/weekly
cmd_tax()         # /tax - Tax estimate

# Settings
cmd_setconf()     # /setconf high/medium/low
cmd_risk()        # /risk low/medium/high
cmd_addwatch()    # /addwatch BTC ETH
cmd_watchlist()   # /watchlist - Show watched
cmd_reinvest()    # /reinvest on/off

# Advanced
cmd_export()      # /export - CSV download
cmd_simulate()    # /simulate symbol direction lev
cmd_high_mode()   # /high - Max leverage mode
cmd_kill()        # /kill - Close all + shutdown
cmd_help()        # /help - All commands

# Callbacks
button_resume()   # Resume from inline button
button_confirm_kill() # Confirm kill from button
```

**15+ commands total** with inline buttons for quick actions.

---

### `db_utils.py` (240 lines)
**SQLite database operations.**

```
Tables:
├── trades       # All trades: entry, exit, P&L, AI decision
├── configs      # Settings: min_confidence, risk_level
├── watchlist    # Watched symbols
└── streak       # Loss streak counter + pause state

Functions:
init_database()         # Create tables
add_trade()            # Log trade opening
close_trade()          # Log trade closing
get_open_trades()      # Active orders
get_trade_history()    # Closed trades
get_loss_streak()      # Loss counter
increment_loss_streak()
reset_loss_streak()
get_config() / set_config()
add_watchlist() / remove_watchlist()
```

**Persistence:**
- All data survives bot restart
- Open positions recovered automatically
- Configs persisted (risk level, thresholds, etc.)

---

## 📚 Documentation Files

### `README.md` (650 lines)
**Complete feature documentation + full setup guide.**

Covers:
- ⚠️ Critical risk disclaimers
- 🚀 All features (AI, autonomy, reporting, commands)
- 🛠️ Installation (dependencies, API keys)
- 📱 All 15+ commands with examples
- 💰 Position sizing + leverage capping
- ⚠️ Risk controls (circuit breakers, loss limits)
- 🧾 Nigerian tax calculations
- 📊 Database schema
- 📈 Performance expectations
- 🧪 Testing strategy (phases 1-3)

**Start here for complete overview.**

### `QUICKSTART.md` (150 lines)
**Get running in 15 minutes (paper mode).**

Steps:
1. Install pip packages
2. Get Telegram token (@BotFather)
3. Get your Telegram ID (@userinfobot)
4. Get API keys (Gemini, Groq). CoinGecko public API used for news (no key required)
5. Create .env file
6. Run bot

Includes:
- Testing checklist
- Commands to try
- Troubleshooting quick fixes

**For impatient folks who want to test NOW.**

### `TESTING.md` (400 lines)
**Detailed testnet testing guide (phases 1-3).**

**Phase 1: Paper Mode (week 1)**
- Simulated trades, $0 cost
- Tests logic, commands, formats
- 50+ trades to observe behavior

**Phase 2: Bybit Testnet (weeks 2-4)**
- Free $10k testnet balance
- Real API calls (no real money)
- Verify open/close logic
- Monitor P&L matching
- Observe 50+ real trades

**Phase 3: Live (only if profitable)**
- Start with $500 small
- Strict /risk low for first week
- Scale only if consistent wins

Includes:
- Testnet account setup
- API key creation
- Debugging common issues
- Data export/analysis
- Timeline + benchmarks

**Essential before going live. Seriously.**

### `RISKS.md` (500 lines)
**Complete risk disclosure (CRITICAL READ).**

Covers 12 major risks:
1. Liquidation (100% loss in seconds)
2. Flash crashes (wicks trigger SL)
3. Leverage mismanagement
4. API bugs
5. Exchange closure
6. Market manipulation (whales)
7. Regulatory (crypto derivatives banned)
8. Slippage + fees
9. Psychological (revenge trading)
10. Third-party API failures
11. Loss limits insufficient
12. No profit guarantee

Includes:
- Risk severity matrix
- Real examples (FTX, LUNA, etc.)
- What can happen
- What bot safeguards (limited)
- What you can't prevent
- Emergency procedures
- Is this for you? (checklist)

**Read this. Seriously. Read it twice.**

### `.env.example`
**Template for environment variables.**

Shows what you need:
```
TELEGRAM_TOKEN
OWNER_TELEGRAM_ID
BYBIT_API_KEY
BYBIT_API_SECRET
GEMINI_API_KEY
GROQ_API_KEY
COINGECKO_API_URL
PAPER_MODE
MIN_BALANCE
```

Copy to `.env`, fill in your keys, keep SECRET.

---

## 🔧 Setup Files

### `requirements.txt`
**Python dependencies.**
```
python-telegram-bot==20.7
ccxt==4.0.96
google-generativeai==0.5.0
groq==0.4.2
... (10 packages total)
```

Install: `pip install -r requirements.txt`

### `start_bot.bat` (Windows)
**Double-click to start bot on Windows.**

Checks:
- Python 3.10+ installed
- .env file exists
- Dependencies installed
- Safety confirmations

Then: `python telegram_bybit_profit_hunter.py`

### `start_bot.sh` (Unix/Mac)
**Run `chmod +x start_bot.sh && ./start_bot.sh`**

Same as .bat, but for Unix/Linux/Mac.

### `.gitignore`
**Git ignore rules (secrets, logs, DB).**

Prevents:
- .env (API keys)
- trading_bot.db (trade secrets)
- __pycache__ (Python cache)
- .vscode (IDE files)

**Always use this if in git repo.**

---

## 📊 Auto-Generated Files

### `trading_bot.db` (SQLite)
**Database file (auto-created on first run).**

Contains:
- All trades ever made
- Current configs + watchlist
- Loss streak counter
- Bot state (paused, reason, etc.)

**BACKUP REGULARLY** to cloud storage.

### `trading_bot.log` (Optional)
**Log file of all bot activity.**

Can enable by modifying main file logging.sendHandler().

Useful for debugging issues.

### `trades_*.csv` (On /export)
**CSV export of all trades.**

Columns:
- symbol, side, entry_price, exit_price
- pnl, pnl_percent, leverage
- entry_time, exit_time, fee, reason

Useful for:
- External P&L analysis
- Tax reporting
- Performance review

---

## 🚀 Getting Started Paths

### Path 1: I'm Experienced (Futures trader 2+ years)
```
1. Read: RISKS.md + README.md (skip TESTING first)
2. Setup: requirements.txt + .env
3. Run: start_bot.bat/sh
4. Paper mode: 1 week minimum
5. Testnet: 1-2 weeks
6. Live: Start with $500, use /risk low
```

### Path 2: I'm Intermediate (Some trading experience)
```
1. Read: QUICKSTART.md + README.md + RISKS.md
2. Setup: Full .env setup
3. Run paper mode: 2+ weeks
4. Read: TESTING.md
5. Testnet: 3+ weeks minimum
6. Live: Only if testnet win rate >= 50%
```

### Path 3: I'm Beginner (No futures experience)
```
1. Don't use this bot. Seriously.
2. Or: Learn futures first (3-6 months on small spot trading)
3. Then: Come back to this
```

### Path 4: I Just Want to See It Work (Baby Steps)
```
1. Read: QUICKSTART.md
2. Setup: pip install + .env
3. Run: Paper mode only (PAPER_MODE=true)
4. Observe: 1-2 weeks of simulated trades
5. Never go live
6. Use as learning tool for bot development
```

---

## 🧪 Testing Checklist

Before you trade (for real):

- [ ] Read README.md (feature overview)
- [ ] Read RISKS.md (all risks)
- [ ] Setup .env (all API keys)
- [ ] Paper mode 2+ weeks (50+ trades)
- [ ] Commands all work (/status, /history, /help)
- [ ] Testnet 2-4 weeks (50+ real trades)
- [ ] Win rate >= 50% on testnet
- [ ] Max drawdown < 25% on testnet
- [ ] Stress test: /risk high on small account
- [ ] Liquidation test: See what happens at SL
- [ ] /tax works, numbers make sense
- [ ] /export CSV, analyze trades
- [ ] /kill works (closes all positions)
- [ ] Backed up .env somewhere safe
- [ ] Consulted tax professional (optional but recommended)

---

## 📞 Support / Troubleshooting

### "Bot won't start"
See: README.md → Troubleshooting section

### "No trades executing"
1. Check PAPER_MODE setting
2. Check API keys valid
3. Check balance > MIN_BALANCE
4. Check relevant AI API keys active

### "Lost all money (liquidated)"
1. Open `trading_bot.db` in SQLite viewer
2. Check `trades` table for liquidated position
3. Review RISKS.md section on liquidation
4. Post-mortem: What went wrong?

### "I think bot has a bug"
1. Check logs for error messages
2. Record exact steps to reproduce
3. Save .env (without keys) and trading_bot.db
4. File issue with details

---

## 🎯 Quick Links

- **Setup**: [QUICKSTART.md](QUICKSTART.md) (15 min)
- **Full Docs**: [README.md](README.md) (comprehensive)
- **Risks**: [RISKS.md](RISKS.md) (MUST READ)
- **Testing**: [TESTING.md](TESTING.md) (phased approach)
- **Commands**: [README.md → Commands](README.md) (all 15+)
- **Troubleshooting**: [README.md → Troubleshooting](README.md)

---

**Need help? Start with QUICKSTART.md. Then read README.md. Then read RISKS.md (twice). Then testnet.**

**Good luck! Trade safe! 🚀**
