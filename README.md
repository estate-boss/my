# Aggressive Profit Hunter Bot 🔥

**A high-risk, high-reward Telegram-controlled Bybit futures trading bot with AI decision-making, aggressive leverage on MAIN COINS ONLY, autonomous trading loop, profit extraction to external wallet (60%), and comprehensive risk management.**

---

## ⚠️ CRITICAL DISCLAIMERS

### **EXTREME RISK—NO GUARANTEES**

This bot is designed for **experienced traders only** and uses **moderate leverage (5x-50x on main coins)** on Bybit perpetual futures. 

**Key Risks:**
- **Liquidation possible**: Moderate leverage = 2-5% adverse moves can liquidate
- **Total loss scenario**: You can lose your entire account, though less likely with main coins
- **No profit guarantee**: No guarantee of returns or any returns
- **Market volatility**: Flash crashes, wicks, and slippage can trigger SLs
- **API/network failures**: Bot may miss closing trades or execute at worse prices
- **Regulatory risk**: Crypto futures trading is restricted in some jurisdictions

**MAIN COINS ONLY** (reduces manipulation risk):
- Bitcoin (BTC), Ethereum (ETH), Solana (SOL)
- BNB, Cardano (ADA), Ripple (XRP), Dogecoin (DOGE)
- Avalanche (AVAX), Polygon (MATIC), Chainlink (LINK)

**RECOMMENDATION:**
1. **Test on Bybit Testnet first** (free testnet account available)
2. Start with **paper trading mode** (simulated, no real money)
3. Use **small amounts** ($20-100 initially with /risk low)
4. **Never trade with money you can't afford to lose**
5. Consult a tax professional and lawyer before trading

**By using this bot, you assume 100% of the risk. No refunds, no liability.**

---

## 🚀 Features (UPDATED)

-### AI-Powered Trading
- **Dual AI**: Gemini + Groq (both must agree for high-confidence trades)
- **News weighting**: CoinGecko project status updates and news for directional bias (no API key required)
- **Fallback logic**: If AI fails, uses simple rule-based signals (24h change >5% → long)
- **Configurable confidence threshold**: Trade only on high/medium/low AI confidence

### Autonomous Trading Loop (Every 15 min)
- Fetches **MAIN COINS ONLY** USDT perpetuals (BTC, ETH, SOL, etc.)
- Filters for high-volume stable coins, avoids low-cap/pump-and-dump alts
- Analyzes price, volatility (ATR), 24h change, and recent news
- Gets AI decision (long/short/no_trade) with suggested leverage & targets
- Opens position with **2% base position size** (down from 3%)
- Closes trades when TP/SL hit or after manual review
- **60% profits → External wallet** (user's personal address)
- **40% profits → Bot reinvestment** (compound for next trades)

### Aggressive Risk Management
- **3-loss streak**: Auto-pause on 3 consecutive trading losses (can /resume)
- **Circuit breakers**: Pause symbol for 1h on >12% 1h swing (was 15%), >8% flash crash (was 10%)
- **Balance protection**: Pause if > 20% daily drawdown or balance < MIN_BALANCE ($20, was $100)
- **Dynamic sizing**: Position size **2% base** (down from 3%), scales with confidence, volatility, and loss streak
- **Leverage validation**: Capped at 95% of symbol max, but presets much lower for main coins
- **Main coins only**: Avoids low-cap manipulation, focuses on BTC, ETH, SOL, etc.

### Detailed Reporting
- **Trade reports**: After every open/close—entry, leverage, AI reason, TP/SL, P&L%
- **Daily reports** (midnight WAT): Today's P&L, win rate, trade count
- **Weekly reports** (Sunday): Week's performance + trends
- **Profit extraction**: Track 60% profits for withdrawal to external wallet, 40% auto-reinvest
- **Tax estimate**: FIFO capital gains, Nigerian tax calc (10% CGT + ₦800k exemption)
- **Position tracking**: Open positions, balance, return %

### Complete Telegram Control
- Over **15+ commands** for full control
- Inline buttons for quick actions (Resume, Pause, History, Kill)
- Realtime alerts on losses, circuit breakers, and pauses
- Export trades as CSV for external analysis

### Persistence & State Management
- **SQLite database** for all trades, configs, watchlist, loss streak
- Trades store: entry/exit, P&L, leverage, AI decisions (both models), reason
- Configs persist: risk level, confidence threshold, reinvest mode
- Automatic recovery: Resumes from crash/restart with all open positions intact

### Paper Trading Mode
- Simulate all trades **without real money** (env var: `PAPER_MODE=true`)
- Full reports and P&L calculations still generated
- Perfect for testing strategy before going live

---

## 📋 Requirements

- **Python 3.10+**
- **Bybit account** (live or testnet)
- **Telegram bot token** (from @BotFather)
- **API keys**: Gemini, Groq (CoinGecko public API used for news/data — no key required)
- **$100-10,000+ USDT** (recommended starting capital)

---

## 🛠️ Installation & Setup

### 1. **Clone/Download Project**
```bash
cd /path/to/project
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Get API Keys**

#### Telegram Token
1. Chat @BotFather on Telegram
2. `/newbot` → name your bot → copy token to `.env`

#### Bybit API
1. Visit https://www.bybit.com/en/ (or testnet: https://testnet.bybit.com)
2. Account → API → Create New Key
3. **Permissions**: Position (read/write), Order (read/write), Wallet (read)
4. **DO NOT share keys** — treat like passwords

#### Gemini (Google AI)
1. Go to https://aistudio.google.com/app/apikeys
2. Create API key → copy to `.env`

#### Groq
1. Visit https://console.groq.com/keys
2. Create API key → copy to `.env`

#### CoinGecko
1. CoinGecko public API is used for project updates and news: https://www.coingecko.com/
2. No API key is required. If you want to override the base URL, set `COINGECKO_API_URL` in `.env`.

#### Exchange Rate API (Optional — for NGN conversion)
- Uses free `exchangerate-api.com` by default (no key needed)

### 4. **Create `.env` File**
```bash
# .env (keep this SECRET!)
TELEGRAM_TOKEN=your_bot_token_here
OWNER_TELEGRAM_ID=1234567890
BYBIT_API_KEY=your_bybit_key
BYBIT_API_SECRET=your_bybit_secret
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# Modes
PAPER_MODE=true  # Set to false for LIVE trading (⚠️ RISK!)
MIN_BALANCE=100  # Minimum USDT to keep (pause if below)

# Optional
WAT_TIMEZONE=Africa/Lagos
```

⚠️ **NEVER commit `.env` to git!** Add to `.gitignore`.

### 5. **Test on Bybit Testnet First**
```bash
# Use testnet API endpoints — **no real money lost**
# Bybit testnet: https://testnet.bybit.com
# Set PAPER_MODE=true in .env for maximum safety
```

### 6. **Run the Bot**
```bash
python telegram_bybit_profit_hunter.py
```

You should see:
```
🚀 AGGRESSIVE PROFIT HUNTER BOT INITIALIZING
✓ Database ready
✓ Telegram connected
✓ Bybit connected (Paper mode: True)
✅ Bot initialized successfully
```

Bot will send startup message to your Telegram OWNER_ID.

---

## 📱 Telegram Commands

### Core Commands
- **`/start`** — Initialize bot + welcome message
- **`/status`** — View current status (balance, return %, open positions) + quick action buttons
- **`/pause`** — Pause autonomous trading loop (manual trades can still be triggered)
- **`/resume`** — Resume trading loop
- **`/kill`** — **Close all positions + shutdown bot** (confirmation required)

### Analytics & Reporting
- **`/history`** — Show last 10 closed trades (symbol, P&L%, date)
- **`/report`** — Force daily + weekly P&L report (normally auto at midnight WAT + Sunday)
- **`/tax`** — Show tax estimate using FIFO method (USD + Nigerian NGN, 10% CGT)
- **`/export`** — Download all trades as CSV (entry, exit, P&L, reason, dates)

### Configuration
- **`/setconf high/medium/low`** — Set minimum AI confidence threshold (default: medium)
  - `high` = only trade on AI high confidence (fewer trades, higher win rate)
  - `medium` = default (balanced)
  - `low` = more aggressive (more trades, higher drawdown risk)

- **`/risk low/medium/high`** — Presets for leverage & position sizing:
  - `low` → 10x max leverage, 1% position size
  - `medium` → 50x max leverage, 3% position size (default)
  - `high` → 100x max leverage, 5% position size (⚠️ dangerous)

- **`/addwatch BTC ETH SOL`** — Add symbols to watchlist (auto-traded every cycle)
- **`/watchlist`** — Show current watchlist
- **`/removewatch BTC`** — Remove symbol from watchlist

### Advanced
- **`/reinvest on/off`** — Auto-compound 40% of profits (60% withdrawn to external wallet)
- **`/withdraw`** — Show pending profits ready for 60% transfer to your wallet
- **`/simulate BTC long 50`** — Calculate hypothetical P&L at +10% / -10% / -30% moves
- **`/high`** — **Max leverage mode** (50x on main coins) — ⚠️ liquidation risk
- **`/help`** — Show all commands

### Admin
- **`/API`** — Update API keys (coming soon)
- **`/notify all/trades/alerts/off`** — Notification level (all = every trade, alerts = only risks)

---

## 🎯 Trading Behavior

### Decision Flow
1. **Fetch** current price, 24h change, volume (ATR)
2. **Scrape** recent project updates from CoinGecko (heavily weighted in AI prompt)
3. **Query Gemini + Groq**: "Ruthless trader, maximize quick gains. News-driven. Suggest long/short with leverage."
4. **Require agreement**: Both models must agree on decision + confidence ≥ threshold
5. **Calculate position size**: `base% × confidence_mult × volatility_factor × loss_streak_mult`
6. **Get max leverage** from symbol via CCXT, apply 95% cap for safety
7. **Open position** with TP (40-100%+) and SL (-15 to -30%)
8. **Close on TP/SL** or manual review
9. **Log P&L** → update streak → trigger pause on 3 losses

### Example Trade
```
Symbol: BTCUSDT
News: "Spot ETF inflow surge" + 24h change: +3%
AI Decision: LONG, HIGH confidence
Suggested Leverage: 100x
Entry: $95,000
Position: $3,800 USDT (3.8% of $100k account)
TP: +65% ($156,500)
SL: -20% ($76,000)
Liquidation Price: ~$94,600 (100x leverage, 0.5% margin)
...trade runs for 30 min...
Exit: $98,500 (+3.7%, +$140 profit before fees)
P&L: +3.7%
Fee: $0.20 (0.05%)
Net: +$139.80 / +3.7%
Reported to Telegram: ✅ LONG BTCUSDT Closed | +3.7% | Balance $100,139.80
```

---

## 💰 Position Sizing & Leverage (REDUCED DEFAULTS)

**Dynamic sizing formula (Updated):**
```
position_usdt = account_balance × base_pct × confidence_mult × volatility_factor × loss_streak_mult

where:
  base_pct = 2.0% (down from 3%, main coins only)
  confidence_mult = 1.1 (high), 1.0 (medium), 0.7 (low) — reduced
  volatility_factor = min(1.5, atr / normal_atr) — high vol = reduce size more
  loss_streak_mult = max(0.2, 1.0 - loss_count × 0.33) — after losses, reduce to 20%
```

**Leverage presets (Updated - Main Coins Only):**
```
/risk low:    5x max | 1% position | -8% SL (very conservative, ideal for testing)
/risk medium: 15x max | 2% position | -15% SL (DEFAULT, much safer)
/risk high:   50x max | 3% position | -25% SL (was 100x, now 50x)
```

Example (with $100 starting):
```
/risk medium:
- Base: 2% of $100 = $2
- High confidence: × 1.1 = $2.20
- Normal volatility: × 1.0 = $2.20
- No recent losses: × 1.0 = $2.20 USDT per trade
- Max leverage: 15x
- Risk per trade: $2.20 (2.2%)
- Position exposure: $33 (~15x × $2.20)
```

---

## 💸 Profit Extraction (NEW FEATURE)

**60% to External Wallet | 40% Reinvest**

Every time a trade closes with profit:
1. **60% of gross profit** → Marked for withdrawal to your external wallet
2. **40% of gross profit** → Kept in bot for reinvestment (compound growth)

**Example:**
```
Trade closed: +$100 profit
Breakdown:
  - 60% ($60) → Send to your personal wallet (via /withdraw command)
  - 40% ($40) → Stay in bot for next trades (reinvestment)

Your balance grows: +$40
Your pocket: +$60 (real crypto in your wallet)
```

**How to Withdraw (60%):**
1. Type `/withdraw` in Telegram
2. Bot shows how much is ready (e.g., $120)
3. Manually transfer that amount from Bybit to your personal wallet
4. (Future: Auto-transfer via Bybit API)

---

## ⚠️ Risk Controls

### 1. **Consecutive Loss Limit**
- On 3rd realized loss → **bot auto-pauses**
- Alert: `🚨 3 losses in row! Drawdown XX%. Paused. Review /history. /resume to continue.`
- After 1 winning trade → streak resets to 0

### 2. **Circuit Breakers**
- **1h swing > 15%**: Pause symbol 1h
- **Flash crash > 10% drop**: Pause symbol 30 min
- **API failure**: Skip cycle, log error, continue next cycle
- Manual check before trading volatile symbols

### 3. **Balance Protection**
- Balance < MIN_BALANCE (default $100) → pause + alert
- Daily drawdown > 20% → pause + alert
- Monitored continuously during trading cycle

### 4. **Leverage Safeguards**
- Never exceed symbol max (queried from CCXT each trade)
- Cap at 95% of max to allow margin buffer on wicks
- Liquidation price calculated + displayed in reports

### 5. **Size Scaling After Losses**
- After 1st loss: 75% of normal size
- After 2nd loss: 50% of normal size
- After 3rd loss: Bot pauses entirely
- Win resets multiplier to 100%

---

## 🧾 Nigerian Tax Calculations

**Bot estimates taxes using FIFO method:**

### Capital Gains Tax (Nigeria)
- **Rate**: 10% on short-term trading (STT) gains
- **Exemption**: First ₦800,000 (~$500 @ 1,600 rate) per annum tax-free
- **Formula**:
  ```
  Taxable Gain = Total Realized Gain - ₦800k
  Tax = Taxable Gain × 10%
  ```

### Example
```
Total closed trades realized gain: $5,200
Less exemption: $500
Taxable: $4,700
Tax (10%): $470 USD / ₦752,000 NGN
```

### Command: `/tax`
Outputs:
- Total FIFO gains (USDT)
- Exemption amount
- Taxable amount
- Tax due (USD + NGN @ current rate)
- **Disclaimer**: Approximate, consult tax professional

### ⚠️ Tax Disclaimers
1. **Non-professional advice**: This calculation is rough; consult a tax advisor
2. **Jurisdiction matters**: May differ from state 🚫—verify with FIRS or tax lawyer
3. **Progressive rates**: Above ₦100M income may have higher rates
4. **Deductions**: May be able to deduct trading fees, losses from other sources
5. **Reporting**: Keep trade logs (exportable via `/export` CSV) for authorities
6. **NGN conversion**: Current rate used; historical rates may apply

**Recommended**: Work with a Nigerian tax professional (e.g., TaxPro, Deloitte NG) for accurate filings.

---

## 📊 Database (SQLite)

Bot stores all data in `trading_bot.db` with tables:

### `trades` table
```sql
id, symbol, side, entry_price, exit_price, leverage, quantity,
entry_time, exit_time, pnl, pnl_percent, fee, status,
ai_decision_gemini, ai_decision_groq, ai_confidence,
target_tp_percent, stop_loss_percent, reason, duration_minutes
```

### `configs` table
```
key, value, updated_at
```
Stores: `min_confidence`, `trading_active`, `pause_reason`, `max_leverage`, etc.

### `watchlist` table
```
symbol, added_at
```

### `streak` table
```
loss_count, last_loss_time, paused, pause_reason, paused_at
```

**Backup regularly!** Copy `trading_bot.db` to cloud/external drive.

---

## 🔄 Autonomous Loop Schedule

```
Every 15 minutes:
  1. Check if paused / balance ok
  2. Fetch symbols (watchlist + high-volume)
  3. For each symbol:
     - Get ticker (price, volume, change)
     - Check swing/crash breaker
     - Get AI decision + leverage
     - Calculate position size
     - Open trade if signal
  4. Close trades hitting TP/SL
  5. Update balance, check loss streak

Every midnight (WAT):
  6. Send daily P&L report

Every Sunday midnight (WAT):
  7. Send weekly P&L report
```

---

## 🧪 Testing Strategy

### Phase 1: Testnet + Paper Mode (FREE)
```bash
PAPER_MODE=true
BYBIT_API_KEY=testnet_key
BYBIT_API_SECRET=testnet_secret
```
- Open testnet account on Bybit (free, no money)
- Run bot in paper mode (simulated trades, real reports)
- Monitor 1-2 weeks, observe win rate & drawdown
- **Cost**: $0

### Phase 2: Small Live Trade
- Start with $100-500 USDT
- Set `/risk low` (10x max leverage)
- Trade 2-4 symbols only
- Monitor daily, adjust `/setconf` if losses spike
- **Duration**: 2-4 weeks
- **Cost**: Potential $0-100 loss

### Phase 3: Scale (If profitable)
- Only if Phase 2 shows consistent wins and low drawdown
- Increase to `/risk medium` (50x leverage)
- Add more watchlist symbols
- Monitor daily
- Keep `MIN_BALANCE` high (e.g., $1,000)

---

## 🐛 Troubleshooting

### Bot won't start
- Check `.env` file: All required keys present?
- Test token: `curl https://api.telegram.org/bot{TOKEN}/getMe`
- Check Python 3.10+: `python --version`

### No trades executed
- Is bot paused? Check `/status`
- Check AI keys valid (Gemini, Groq). CoinGecko public API used for news (no key required)
- Check Bybit API keys + testnet vs live mismatch
- Check balance > MIN_BALANCE
- Review logs: `tail -f trading_bot.log` (if logging to file)

### Trades closed too fast
- TP/SL margins too tight? Adjust via `/risk` command
- Volatility too high? Bot reduces size, may be low profit
- Use `/simulate` to test P&L targets

### Can't connect to Bybit
- API key permissions insufficient? Verify read/write enabled
- IP whitelist? Add your IP in Bybit API settings
- Network blocked? (Corporate/ISP firewall)
- Testnet vs live URL mismatch? Check exchange URL

### High fees, low profits
- Bybit Futures taker fee: ~0.05%
- Liquidation risk at high leverage?
- Use `/export` to analyze fee costs vs P&L

---

## 📈 Monitoring Best Practices

1. **Check daily** (5 min): Review trades via `/history`
2. **Alarm on pause**: Get alert if 3+ losses → manually review
3. **Weekly report**: Check `/report` for performance trends
4. **Monthly review**: Export trades, analyze by symbol and time
5. **Quarterly rebalance**: Adjust `/risk` level, watchlist based on market conditions

---

## 🚀 Performance Expectations (Realistic)

| Timeframe | Realistic Return | Win Rate | Drawdown |
|-----------|------------------|----------|----------|
| **Week 1** | -5% to +15% | 40-60% | 10-30% |
| **Month 1** | -20% to +30% | 45-60% | 15-40% |
| **3 Months** | -40% to +50% | 50-65% | 20-50% |
| **6 Months** | -50% to +100%+ | 55-70% | 25-60% |

**Key insights:**
- Expect 40-50% win rate initially (not 90%+)
- Drawdowns can exceed 30% — emotionally tough
- 3x weekly returns unlikely; 3-5% weekly realistic if skilled
- Volatility spikes kill high-leverage positions
- Consistent ~1-2% weekly possible with good risk management

---

## 📝 License & Disclaimer

This project is provided **AS IS** without any warranty. By using this bot:
- You accept **100% risk** of financial loss
- You agree this is **experimental software**—expect bugs
- You acknowledge **no guaranteed returns**
- You will **not hold author liable** for any losses
- You **consult professionals** (trader, tax, lawyer) before using

---

## 🎯 Future Enhancements

- [ ] On-chain volume analysis (Glassnode API)
- [ ] Advanced backtesting engine (historical data replay)
- [ ] Machine learning sentiment analysis (Twitter/news)
- [ ] Multi-exchange support (Binance, OKX, Dydx)
- [ ] Telegram webhook (faster alerts vs polling)
- [ ] Discord notifications
- [ ] Web dashboard (real-time stats, trade monitor)
- [ ] Advanced order types (limit, conditional, DCA)
- [ ] Portfolio rebalancing (fixed allocation per coin)

---

## ✉️ Support & Issues

- **Bugs**: Document clearly (logs, command ran, error) → submit issue
- **Feature requests**: Describe use case + expected behavior
- **Security**: Don't publish keys—report privately

---

## 📚 References

- **Bybit API**: https://bybit-exchange.github.io/docs/futures/
- **CCXT**: https://github.com/ccxt/ccxt
- **Google Generative AI**: https://google.ai/
- **Groq**: https://console.groq.com/
- **CoinGecko**: https://www.coingecko.com/
- **Python Telegram Bot**: https://python-telegram-bot.readthedocs.io/

---

## 🎓 Educational Use

This bot is designed for **learning algorithmic trading**, bot development, and AI integration. It's **not financial advice** and should not be the sole basis for trading decisions. Educate yourself on:
- Futures trading mechanics (leverage, liquidation, margin)
- Risk management (position sizing, stop-loss discipline)
- Nigerian tax law (consult professional)
- Crypto market dynamics (volatility, sentiment, on-chain metrics)

Good luck, and trade safe! 🚀

---

**Last Updated**: February 2026  
**Version**: 1.0 (Beta)  
**Status**: Experimental / Demo — Use at your own risk
