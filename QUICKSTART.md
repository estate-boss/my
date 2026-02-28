# Quick Start Guide 🚀

This guide gets you up and running in **15 minutes** (testnet/paper mode).

## What's New in This Version

✅ **Minimum balance**: Reduced to **$20** (very accessible)  
✅ **Main coins only**: BTC, ETH, SOL, BNB (avoid scams/manipulation)  
✅ **Lower leverage**: 5x-50x (safer than before 50x-200x)  
✅ **2% position size**: Down from 3% (reduced risk per trade)  
✅ **Profit extraction**: 60% of gains → your wallet, 40% → reinvest  

Perfect for small accounts, learning, and safer trading.

---

## Step-by-Step

### 1️⃣ Install Dependencies (2 min)
```bash
pip install -r requirements.txt
```

### 2️⃣ Get Telegram Token (3 min)
1. Open Telegram, chat **@BotFather**
2. Send `/newbot`
3. Name your bot (e.g., "ProfitHunner2025")
4. Copy the **token** (looks like `123456789:ABCdefGHIjklmnopQRStuvWXYZ`)

### 3️⃣ Get Your Telegram ID (1 min)
1. Chat **@userinfobot** in Telegram
2. Get your user ID (number like 987654321)

### 4️⃣ Create API Keys (5 min)

#### Bybit (Testnet for safety!)
- Go to https://testnet.bybit.com
- Sign up (free, no money)
- Account → API → Create New Key
- Permissions: Position (read+write), Order (read+write), Wallet (read)
- Copy **Key** and **Secret**

#### AI Keys (Free tiers available)
- **Gemini**: https://aistudio.google.com/app/apikeys (free tier works!)
- **Groq**: https://console.groq.com/keys (free tier works!)
- **CoinGecko**: https://www.coingecko.com/ (public API; no API key required)

### 5️⃣ Create `.env` File (2 min)
```bash
# Copy from example
cp .env.example .env

# Edit with your keys (nano, vim, or any text editor)
nano .env
```

Fill in:
```
TELEGRAM_TOKEN=your_token_here
OWNER_TELEGRAM_ID=your_user_id_here
BYBIT_API_KEY=testnet_key
BYBIT_API_SECRET=testnet_secret
GEMINI_API_KEY=key_here
GROQ_API_KEY=key_here
COINGECKO_API_URL=https://api.coingecko.com/api/v3
PAPER_MODE=true  # IMPORTANT: Keep true for safety!
```

### 6️⃣ Start Bot (1 min)

**Windows:**
```bash
start_bot.bat
```

**Mac/Linux:**
```bash
chmod +x start_bot.sh
./start_bot.sh
```

Or directly:
```bash
python telegram_bybit_profit_hunter.py
```

### 7️⃣ Test in Telegram
1. Open Telegram
2. Find your bot (@YourBotName)
3. Send `/start`
4. Should see: "🔥 **Aggressive Profit Hunter Bot Online**..."
5. Send `/status` → see bot status + buttons

**✅ You're live (in sim mode)!**

---

## What Happens Next

- **Every 15 min**: Bot analyzes symbols + executes simulated trades (paper mode)
- **Every midnight (WAT)**: Daily P&L report in Telegram
- **Every Sunday**: Weekly summary report
- **Watch Telegram** for trade alerts after each open/close

---

## Key Commands to Try

```
/status          # See current status + balance
/history         # Show recent trades
/addwatch BTC ETH # Add symbols to auto-trade watchlist
/watchlist       # Show your watchlist
/report          # Force daily report now
/help            # All commands
```

---

## Testing Checklist

- [ ] Bot starts without errors
- [ ] `/start` works in Telegram
- [ ] `/status` shows balance
- [ ] `/help` lists all commands
- [ ] Wait 15 min → see first trade (paper mode)
- [ ] `/history` shows the trade
- [ ] `/report` generates report

---

## Before Going Live (REQUIRED)

1. **Run paper mode for 2-4 weeks**
   - Observe win rate, drawdown, behavior
   - Test all commands

2. **Switch to small testnet trades**
   - Set `PAPER_MODE=false` in `.env`
   - Use Bybit testnet (no real money)
   - Set `MIN_BALANCE=1000` (minimum to keep)
   - Trade `/risk low` (10x max leverage)
   - Monitor daily for 2 weeks

3. **Review risks in README**
   - High leverage = liquidation possible
   - No profit guarantee
   - Can lose 100% in seconds

4. **Only go live if:**
   - Paper mode shows 50%+ win rate
   - You understand liquidation risk
   - You can afford to lose 100% of trading amount
   - You have tax professional consulted

---

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| `No module named 'ccxt'` | `pip install -r requirements.txt` |
| `.env file not found` | `cp .env.example .env` + fill it |
| `Telegram token invalid` | Check token from @BotFather (no spaces) |
| `No bot response in TG` | Check OWNER_TELEGRAM_ID is correct |
| Bot starts but no trades | Paper mode: wait 15 min for first cycle |
| High fees reported | Bybit futures taker fee: ~0.05% |

---

## Next Steps

1. **Read [TESTING.md](TESTING.md)** for detailed testnet guide
2. **Read [README.md](README.md)** for full feature documentation
3. **Monitor [trading_bot.db](trading_bot.db)** (trades logged here)
4. **Join Telegram communities** for trading support (Bybit, crypto communities)
5. **Keep .env safe** — backup to secure location

---

**⚠️ Remember: This is experimental software. Start small, test thoroughly, and never risk money you can't afford to lose.**

Good luck! 🚀
