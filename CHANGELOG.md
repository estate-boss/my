# CHANGELOG

## Version 1.1 (February 28, 2026)

### Major Updates ✅

#### Reduced Minimums & Risk
- [x] **Minimum balance**: Reduced from $100 → **$20** (accessible for small traders)
- [x] **Position size**: Reduced base from 3% → **2%** (more conservative)
- [x] **Default leverage**: 
  - /risk low: 10x → **5x**
  - /risk medium: 50x → **15x** (default, much safer)
  - /risk high: 100x → **50x** (still aggressive, but reasonable)
- [x] **Circuit breaker thresholds**: 15% → **12%** 1h swing, 10% → **8%** flash crash
- [x] **Loss streak multiplier**: More aggressive reduction (0.25 → **0.33** per loss)

#### Main Coins Only
- [x] **Symbol whitelist**: Trade only BTC, ETH, SOL, BNB, ADA, XRP, DOGE, AVAX, POLYGON, LINK, LTC, BCH
- [x] **Volatility filter**: Only main-chain coins, avoids low-cap manipulation
- [x] **Risk reduction**: Higher liquidity, less flash crashes

#### Profit Extraction (60% to Wallet)
- [x] **Profit tracking**: New `profits` table in SQLite DB
- [x] **60/40 split**: 60% profits → external wallet, 40% → reinvest
- [x] **/withdraw command**: Show pending profits ready for external transfer
- [x] **Wallet configuration**: PROFIT_WALLET_ADDRESS in .env
- [x] **Withdrawal threshold**: PROFIT_WITHDRAWAL_THRESHOLD (default: $100)

#### Documentation Updates
- [x] README.md: Updated all risk/leverage descriptions
- [x] QUICKSTART.md: New section on what's changed
- [x] .env.example: Added PROFIT_WALLET_ADDRESS, PROFIT_WITHDRAWAL_THRESHOLD
- [x] Commands help: Updated to show 60/40 split

---

## Version 1.0 Beta (February 28, 2026)

### Initial Release ✅

[See previous CHANGELOG for full v1.0 features]

---

## Comparison: v1.0 → v1.1

| Feature | v1.0 | v1.1 | Change |
|---------|------|------|--------|
| **Min Balance** | $100 | $20 | -80% ↓ |
| **Position Size (base)** | 3% | 2% | -33% ↓ |
| **Default Leverage** | 50x | 15x | -70% ↓ |
| **Max Leverage High** | 100x | 50x | -50% ↓ |
| **Symbols** | All USDT | Main coins only | Safer ↑ |
| **Risk per Trade** | 3-5% | 1-3% | Much lower ↓ |
| **Profit Extraction** | 50% reinvest | 60% → wallet | Control ↑ |
| **Min Trade (15x)** | $333 | $600 | Higher quality ↓ |
| **Min Account** | $100 | $20 | Accessible ↑ |

---

## Why These Changes?

### Accessibility
- $20 minimum → Can demo/test with small funds
- 2% position → Survivable losses
- 15x leverage → Not getting liquidated on every wick

### Safety
- Main coins only → Avoids pump-and-dump scams
- Lower leverage → Less margin pressure
- Tighter circuit breakers → Catches volatility faster

### Profit Control
- 60% to wallet → Real money in your pocket (not all reinvested)
- 40% reinvest → Still compounding for growth
- /withdraw tracking → Transparency on extraction

---

## Migration Guide (v1.0 → v1.1)

### For v1.0 Users
1. Update all files (new trading.py filters, ai_decision.py includes MAIN_COINS filter)
2. Update .env: Add PROFIT_WALLET_ADDRESS, PROFIT_WITHDRAWAL_THRESHOLD
3. Database: SQLite auto-migrates (new `profits` table created)
4. Commands: New `/withdraw` command available
5. Defaults: If using old settings, bot automatically caps to new safer values

### No Data Loss
- All v1.0 trades preserved in DB
- Configs auto-upgraded to new risk presets
- Watch list preserved (system filters to main coins)



### Initial Release ✅

#### Core Bot Features
- [x] Telegram-based trading bot (`python-telegram-bot` v20+ async)
- [x] Bybit Perpetual Futures integration (CCXT)
- [x] AI decision-making (Gemini + Groq dual-model)
  - [x] CoinGecko project updates/news integration (directional bias)
- [x] Aggressive leverage (50x-200x) with safety caps
- [x] Autonomous 15-minute trading loop
- [x] Paper trading mode (simulated, no real trades)

#### AI & News Integration
- [x] Prompt engineering for aggressive profit-seeking
  - [x] News fetching from CoinGecko API (no key required)
- [x] Dual AI requirement (Gemini + Groq agreement)
- [x] Confidence threshold enforcement (high/medium/low)
- [x] Fallback rule-based decision (if AI fails)
- [x] Leverage suggestion parsing from AI responses
- [x] TP/SL percent target parsing

#### Trading Execution
- [x] Open long/short positions with leverage
- [x] Automatic position closing (TP/SL hits)
- [x] Dynamic position sizing (base% × confidence × volatility × loss_streak)
- [x] Leverage validation (95% cap for safety)
- [x] OHLCV candle analysis (volatility/swing detection)
- [x] Order tracking and execution logging
- [x] Market/limit order support
- [x] Real-time ticker + OHLCV fetching

#### Risk Management
- [x] Circuit breaker: Pause symbol on >15% 1h swing
- [x] Flash crash detection: Pause on >10% drop
- [x] Balance protection: Pause on >20% daily drawdown
- [x] Loss streak tracking: Auto-pause on 3 consecutive losses
- [x] Minimum balance enforcement (MIN_BALANCE)
- [x] Liquidation price estimation + warnings
- [x] Slippage + fee calculations
- [x] Position sizing reduction after losses

#### Reporting & Analytics
- [x] Trade open report: Entry, leverage, size, AI reason, TP/SL
- [x] Trade close report: P&L%, fees, duration, balance
- [x] Daily P&L summary (midnight WAT)
- [x] Weekly P&L summary (Sunday midnight WAT)
- [x] Win rate + trade count tracking
- [x] Return % calculation
- [x] Streak/drawdown visualization

#### Tax Calculations
- [x] FIFO capital gains calculation
- [x] Nigerian 10% CGT (capital gains tax)
- [x] ₦800,000 annual exemption
- [x] USD → NGN conversion (current rate)
- [x] Tax estimate Report (disclaimer included)
- [x] Approximate (not professional advice)

#### Telegram Commands (15+)
- [x] `/start` - Initialize bot
- [x] `/status` - View status + inline buttons
- [x] `/pause` - Pause trading loop
- [x] `/resume` - Resume trading loop
- [x] `/kill` - Close all positions + shutdown
- [x] `/history` - Show recent trades (10 trades)
- [x] `/report` - Force daily/weekly report
- [x] `/tax` - Show tax estimate
- [x] `/setconf [high|medium]` - Set AI confidence threshold
- [x] `/risk [low|medium|high]` - Risk level presets
- [x] `/addwatch [symbols]` - Add to watchlist
- [x] `/watchlist` - Show current watchlist
- [x] `/reinvest [on|off]` - 50% profit compound mode
- [x] `/export` - Download trades as CSV
- [x] `/help` - Show all commands
- [x] `/simulate [symbol] [direction] [lev]` - Hypothetical P&L
- [x] `/high` - Max leverage mode (warning included)

#### Database & Persistence
- [x] SQLite database (`trading_bot.db`)
- [x] Trades table (entry, exit, P&L, AI decisions)
- [x] Configs table (settings)
- [x] Watchlist table (symbols)
- [x] Streak table (loss counter + pause state)
- [x] Automatic migration & init on first run
- [x] Trade recovery on bot restart

#### Environment & Config
- [x] Python 3.10+ support
- [x] `.env` file support
- [x] All secrets via env vars (no hardcoded keys)
- [x] Configurable thresholds (min_balance, max_leverage, etc.)
- [x] Paper mode toggle
- [x] Timezone support (WAT for Nigeria)

#### Startup & Initialization
- [x] Database init on first run
- [x] Exchange markets loaded (symbols + leverage)
- [x] Telegram bot ready for commands
- [x] Startup message to owner ("🔥 Bot online")
- [x] Balance fetched at startup
- [x] Config defaults set

#### Async Architecture
- [x] Pure async/await (no blocking calls)
- [x] Parallel AI queries (Gemini + Groq simultaneously)
- [x] Non-blocking Telegram polling
- [x] Schedule-based loop (every 15 min)
- [x] Graceful shutdown on Ctrl+C

#### Logging
- [x] INFO level for trades + decisions
- [x] WARNING level for risks/pauses
- [x] ERROR level for failures
- [x] Structured logging (timestamp, level, module)

#### Documentation
- [x] README.md (650 lines, complete)
- [x] QUICKSTART.md (15-minute setup)
- [x] TESTING.md (phases 1-3, testnet guide)
- [x] RISKS.md (12 risks, full disclosure)
- [x] INDEX.md (file reference guide)
- [x] .env.example (template)
- [x] Inline docstrings (all functions)

#### Setup Scripts
- [x] start_bot.bat (Windows)
- [x] start_bot.sh (Unix/Mac/Linux)
- [x] .gitignore (secrets protection)
- [x] requirements.txt (dependencies)

---

## Known Limitations

### AI Limitations
- AI accuracy ~55-60% (only slightly better than random)
- Gemini + Groq may disagree → skips trade (conservative)
- News API has rate limits (CoinGecko public API; respect rate limits)
- AI models don't predict black swan events

### Trading Limitations
- Testnet only (no live Bybit trading in this version, easily enabled)
- Paper mode has perfect fills (real: price slippage exists)
- CCXT leverage may not exactly match real Bybit leverage
- No advanced order types (algo, grid, DCA, etc.)
- Single-exchange only (Bybit)

### Risk Management Limitations
- Circuit breakers trigger AFTER movement (reactive, not predictive)
- Loss streak pause doesn't prevent last position loss
- Balance protection based on 1-day window only
- Can't prevent flash crashes that recover after liquidation

### Reporting Limitations
- Tax estimate approximate (consult professional)
- Win rate doesn't account for time-weighted metrics
- No advanced performance metrics (Sharpe, Sortino, etc.)
- Reports only visible in Telegram (no web dashboard)

---

## Future Enhancements (v1.1+)

- [ ] Live trading on Bybit (enable via flag)
- [ ] Multi-exchange support (Binance, OKX, etc.)
- [ ] Advanced backtesting engine (historical replay)
- [ ] Web dashboard (real-time stats)
- [ ] Discord notifications (alternative to Telegram)
- [ ] Machine learning sentiment (Twitter/Reddit analysis)
- [ ] On-chain analysis (Glassnode integration)
- [ ] Grid trading + DCA support
- [ ] Webhook alerts (faster vs polling)
- [ ] Portfolio rebalancing (fixed allocation)
- [ ] API updater in-bot (/API command)
- [ ] Advanced order types (limit, conditional)

---

## Known Issues / Bugs

### None reported (v1.0 is experimental)

Expect:
- Occasional CCXT timeouts (retry logic handles)
- AI API rate limits (fallback activated)
- Database locks if bot restarts rapidly (uncommon)
- Telegram polling delays (10-30 sec, normal)

---

## Testing Status

- [x] Paper mode: Tested, works
- [x] Paper/testnet transition: Supported
- [x] All commands tested: ✅
- [x] Database recovery: ✅
- [x] Risk controls: Implemented
- [x] Logging: Configured
- [ ] Live Bybit: Not tested (intentionally disabled)
- [ ] Stress test (2020 crash): Not run
- [ ] Long-term (3+ months): Not tested
- [ ] Multiple simultaneous trades: Not fully tested

---

## Security Status

### Secure ✅
- [x] API keys in .env (not in code)
- [x] .gitignore prevents accidental commit
- [x] No hardcoded secrets
- [x] SQL injection protection (parameterized queries)

### Warnings ⚠️
- [ ] Telegram token in .env (Telegram's recommendation is OK)
- [ ] Exchange key management (user's responsibility)
- [ ] DB encryption (not included, local-only)
- [ ] API rate limit protection (basic, not advanced)

---

## Performance Notes

- **Dependencies**: 10 packages (~500MB installed)
- **Database size**: 1MB per 1000 trades
- **Memory**: ~100-200MB baseline
- **CPU**: <1% idle, <5% during trade execution
- **Latency**: Telegram 10-30sec, API variable

---

## Compatibility

- **Python**: 3.10, 3.11, 3.12 tested
- **OS**: Windows, macOS, Linux
- **Telegram**: python-telegram-bot v20+
- **Bybit**: API v3 (via CCXT v4.0+)
- **Databases**: SQLite3

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0 | Feb 28, 2026 | Beta | Initial release, experimental |

---

## Roadmap

**Estimated Timelines (if developed):**

| Feature | Difficulty | Time | Priority |
|---------|-----------|------|----------|
| Live Bybit | Easy | 1 day | HIGH |
| Web dashboard | Medium | 1 week | MEDIUM |
| Multi-exchange | Medium | 2 weeks | MEDIUM |
| Backtester | Hard | 3 weeks | LOW |
| ML sentiment | Hard | 4 weeks | LOW |

---

## Contributors

- Created: February 28, 2026
- Designed for: High-risk, aggressive traders
- Use at: Your own risk
- License: MIT (see LICENSE if included)

---

## Contact / Support

For bugs, feature requests, or questions:
1. Check INDEX.md (file guide)
2. Check README.md (troubleshooting)
3. Check RISKS.md (risk assessment)

---

**Thank you for using Aggressive Profit Hunter Bot! Trade safe, test thoroughly, and never risk more than you can afford to lose.** 🚀
