# Testing on Bybit Testnet 🧪

Complete guide to test the bot **safely without real money** before going live.

---

## Phase 1: Paper Mode (Completely Safe)

**Duration**: 1-2 weeks  
**Cost**: $0  
**Risk**: $0  

### Setup
```bash
# In .env
PAPER_MODE=true
BYBIT_API_KEY=any_string_works
BYBIT_API_SECRET=any_string_works
```

### What Happens
- Bot simulates all trades
- No real API calls to Bybit
- Full reports generated (P&L fake but formatted correctly)
- Perfect for testing commands, UI, logic

### Testing Checklist
- [ ] Bot starts without errors
- [ ] `/start` works
- [ ] Commands execute (`/status`, `/history`, `/report`)
- [ ] Trades show in database (`trading_bot.db`)
- [ ] Reports look correct (format, calculations)
- [ ] Loss streak triggers pause at 3 losses
- [ ] Daily/weekly reports auto-sent at schedules

### Expected Output
```
--- Trading cycle @ 12:34:56 ---
Analyzing BTC...
  BTC: long (confidence: high)
    ✅ Trade opened: ID=1

[After 15 min]
  ✅ Trade closed: BTC +3.50%

[Daily report sent to Telegram]
📊 Daily Report - 2026-02-28
Trades: 12 (Win 7 | Loss 5)
Win Rate: 58.3%
P&L: +$340
```

---

## Phase 2: Bybit Testnet (Free + Real API)

**Duration**: 2-4 weeks  
**Cost**: $0 (testnet only)  
**Risk**: $0 (no real money)  

### Why Testnet?
- Tests actual Bybit API without real trades
- Verifies position opening/closing logic
- Tests leverage, order types, margin calculations
- **No liquidation risk** — testnet balance can't be depleted below 0

### Step 1: Create Testnet Account

1. Go to https://testnet.bybit.com (Bybit's testnet sandbox)
2. Sign up with email (separate from live account)
3. Verify email
4. You get **free 10,000 USDT testnet balance** automatically

### Step 2: Create Testnet API Keys

1. Login to testnet.bybit.com
2. Account → API → Create New Key
3. **Permissions**:
   - Position: read ✓, write ✓
   - Order: read ✓, write ✓
   - Wallet: read ✓
4. **IP whitelist**: Leave empty (or add your IP)
5. Copy **API Key** and **Secret Key**

### Step 3: Update `.env`

```bash
# .env configuration for testnet

TELEGRAM_TOKEN=your_bot_token
OWNER_TELEGRAM_ID=your_id
BYBIT_API_KEY=testnet_api_key_here
BYBIT_API_SECRET=testnet_api_secret_here
GEMINI_API_KEY=key
GROQ_API_KEY=key
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# TESTNET MODE
PAPER_MODE=false  # NOW trading real testnet!
MIN_BALANCE=100
```

### Step 4: Run on Testnet

```bash
python telegram_bybit_profit_hunter.py
```

You should see:
```
✓ Bybit connected (Paper mode: False)
...trading_cycle...
  Analyzing BTCUSDT
    ✅ Trade opened: ID=1 LONG BTCUSDT qty 0.001 @ 95000.00x50x | Order abc123
```

### Step 5: Monitor in Bybit UI

While bot runs:

1. Go to https://testnet.bybit.com → Dashboard
2. **Wallet** tab: See balance change as trades close
3. **Orders** tab: See open orders (if any)
4. **Positions** tab: See open positions → watch them close (TP/SL)
5. **Trade History** tab: See all closed trades with P&L

### Testing Checklist
- [ ] Bot connects to testnet API
- [ ] First trade opens in Bybit (see in Positions tab)
- [ ] Telegram notification received (trade report)
- [ ] Trade closes on TP/SL (within 15 min)
- [ ] Testnet balance changes correctly
- [ ] P&L matches Bybit and Telegram report
- [ ] `/history` shows all trades from testnet
- [ ] Risk controls work (symbol pause, loss streak)
- [ ] Daily/weekly reports generated

### Example Testnet Trade Flow

**Time 12:15 AM**
```
Bot cycle runs...
BTCUSDT signal: LONG (AI confidence high)
Action: Buy 0.005 BTC @ 95,000 (5 USDT worth) with 50x leverage
Entry: $95,000
Position: $250 USDT exposure
TP: +50% ($142,500 return per unit)
SL: -20% ($76,000)

Telegram: 
🚀 LONG BTCUSDT Opened
Entry: $95,000 | 50x Lev | Size 0.005 BTC
TP +50% | SL -20% | Balance $9,750
```

**Bybit Testnet - Positions Tab:**
```
BTCUSDT | LONG | 0.005 BTC | Entry $95,000
Current Price: $96,500 | Mark Price Unrealized P&L: +$750
```

**Time 12:27 AM**
```
Price hits $142,500 (TP target)
Bot closes position
Exit: $142,500
P&L: +50% ($750 profit)
Fee: $0.25 (0.05%)
Net: +$749.75

Telegram:
✅ LONG BTCUSDT Closed
Entry $95,000 → Exit $142,500
P&L: +50% ($750) | Duration: 12m
Balance: $10,499.75
```

---

## Phase 3: Live Trading (FINAL - Only if Profitable on Testnet)

### Checklist Before Going Live

- [ ] **Testnet win rate ≥ 50%** (e.g., 7 wins out of 15 trades)
- [ ] **Max drawdown < 25%** (didn't lose >25% of testnet balance)
- [ ] **Return rate positive** (testnet balance grew)
- [ ] **All commands tested** (`/pause`, `/resume`, `/status`, etc.)
- [ ] **Risk controls working** (pause on 3 losses, circuit breakers)
- [ ] **2-4 weeks of testnet data**

### Setup for Live

```bash
# .env - Switch to LIVE Bybit

BYBIT_API_KEY=live_bybit_api_key_here  # NOT testnet
BYBIT_API_SECRET=live_bybit_api_secret  # NOT testnet
PAPER_MODE=false
MIN_BALANCE=500  # Minimum to keep
```

**Create live API key on https://www.bybit.com (NOT testnet)**

### Starting Capital Recommendation

| Risk Profile | Starting Amount | Max Position Size |
|--------------|-----------------|-------------------|
| **Conservative** | $500 | 1% ($5 per trade) |
| **Moderate** | $1,000 | 2% ($20 per trade) |
| **Aggressive** | $5,000+ | 3-5% ($150-250 per trade) |

### Live Trading Rules

1. **First week: Monitor daily**
   - Check `/status` every morning
   - Review `/history` for trades
   - Ensure P&L matches Bybit

2. **After losing trade: Reduce size**
   - `/risk low` (1% size, 10x max lev)
   - Trade only watchlist symbols

3. **After 3 losses: Auto-pause**
   - Bot sends alert
   - Review mistakes
   - Clear mind, then `/resume`

4. **Weekly review: Check performance**
   - `/report` → analyze trends
   - Adjust settings if needed
   - Scale up only if consistent wins

---

## Debugging Testnet Issues

### Issue: "Markets not loaded"
- **Cause**: API key has no market read permission
- **Fix**: Regenerate API key, ensure read permission enabled

### Issue: "Account has insufficient margin"
- **Cause**: Position size too large for balance
- **Fix**: Reduce position size in `risk_manager.py` or set `/risk low`

### Issue: "Symbol not found"
- **Cause**: Testnet symbol different (shouldn't happen for BTCUSDT)
- **Fix**: Check Bybit testnet supported symbols, adjust Symbol in watchlist

### Issue: "Order rejected - insufficient balance"
- **Cause**: Testnet testnet balance < 10 USDT
- **Fix**: Restart account (reset testnet balance to 10k via Account menu)

### Issue: "Trade never closes (stuck open)"
- **Cause**: TP/SL never hit (price went opposite direction)
- **Fix**: Close manually in Bybit UI, check profit/loss, bot will log it on next cycle

---

## Data Tracking

### Export Trades from Testnet
```bash
# After testing, export for analysis
/export
```
Downloads `trades_YYYYMMDD_HHMMSS.csv` with all testnet trades.

### Analyze
```python
# Quick analysis
import pandas as pd
df = pd.read_csv('trades.csv')
print(df.groupby('symbol')['pnl_percent'].describe())
# Shows win rate, avg gain, max loss per symbol
```

---

## Performance Benchmarks

### Good Testnet Results (Go Live)
- ✅ Win rate: 50-70%
- ✅ Average P&L per trade: +0.5% to +2%
- ✅ Max drawdown: <20%
- ✅ Surviving 3+ loss streaks without panic

### Bad Testnet Results (Don't Go Live)
- ❌ Win rate: <40%
- ❌ Average loss larger than average gain
- ❌ Drawdown >30%
- ❌ Accounts trending down overall

### Average Expected Stats
```
Week 1: 40-50% win rate, -5% to +15% return
Week 2-4: 50-60% win rate, 5-20% return
Month 1 Total: 50-60% win rate, 0-30% return
```

---

## Timeline Summary

```
Week 1: Paper Mode (0 risk)
├─ Test all commands
├─ Observe 50+ simulated trades
├─ Check formats, calculations
└─ If all good → testnet

Week 2-4: Bybit Testnet (free, no real $)
├─ Run against real API
├─ Open/close actual orders
├─ Monitor balance changes
├─ Test risk controls
├─ Analyze P&L, win rate
└─ If WR ≥ 50% + DD < 25% → live

Week 5+: Live Trading (real money)
├─ Start with $500-1000
├─ Trade conservative (/risk low)
├─ Monitor daily
├─ Scale if profitable after 4 weeks
└─ Review monthly, adjust as needed
```

---

## Common Mistakes to Avoid

1. ❌ **Skipping testnet** → Going straight to live
   - **Result**: Lost money on bugs, surprised by behavior

2. ❌ **Running with high leverage** from day 1
   - **Result**: Liquidation on first bad trade

3. ❌ **Not checking daily** → Bot trading while you sleep
   - **Result**: Woke up to liquidation or big loss

4. ❌ **Ignoring loss streaks** → Continuing after 3+ losses
   - **Result**: Drawdown spirals to 50%+

5. ❌ **Too many watchlist symbols** → Scattered capital
   - **Result**: Low position size per trade, hard to profit

6. ❌ **Not backing up `.env`** → Lost API keys if drive fails
   - **Result**: Bot can't run, panic

---

## Questions?

- **"Why test for 4 weeks?"** → Past 2 weeks might be lucky. 4 weeks = trend
- **"Can I skip paper mode?"** → No. Catches logic bugs before wasting testnet time
- **"What if testnet breaks testnet?"** → Free reset. Go to Account → reset testnet balance
- **"How much testnet $ do I need?"** → Starts with 10k USDT free. Enough for thousands of trades

---

**Good luck testing! 🧪🚀**

Once you're confident on testnet, live trading awaits. Start small, stay disciplined, and never risk more than you can afford to lose.
