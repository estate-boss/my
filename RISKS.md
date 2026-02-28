# Complete Risk Disclosure 🚨

**This trading bot uses EXTREME leverage (50x-200x) on unregulated crypto derivatives. You can lose your entire account in seconds.**

---

## Executive Summary

| Risk | Severity | You Can Lose |
|------|----------|--------------|
| **Liquidation** | 🔴 CRITICAL | 100% of account |
| **Flash crash** | 🔴 CRITICAL | 50-100% in seconds |
| **Leverage mismanagement** | 🔴 CRITICAL | 100% on single trade |
| **Bug/API failure** | 🟠 HIGH | 10-50% before shutdown |
| **Market manipulation** | 🟠 HIGH | 20-100% (esp low-volume coins) |
| **Exchange closure** | 🟠 HIGH | All funds trapped |

---

## 1. Liquidation Risk (CRITICAL)

### What is Liquidation?
When you use leverage (e.g., 50x), you're borrowing money to amplify gains/losses.

**Example:**
```
You: $1,000 USDT
Leverage: 50x
Borrowed: $49,000
Total exposure: $50,000 in crypto

Price drops 2%: You lose $1,000
Your margin: $0 → LIQUIDATED ❌
Account: $0
```

### Liquidation Price
- **Long 50x**: Liquidates at 98% of entry price
- **Long 100x**: Liquidates at 99% of entry price
- **Short 100x**: Liquidates at 101% of entry price

Bybit has ~0.5% maintenance margin. Extreme wicks (temporary spikes) trigger liquidation.

### Recent Examples
```
June 2023: LUNA crash: 50x leveraged = -99% in seconds
May 2023: BTC flash crash $27k: 100x liquidated users
Aug 2022: FTX leverage trading: $8B lost by users
```

### How to Prevent (Partial Safety)
- ✅ Start with 10x leverage max
- ✅ Use stop-loss (SL) NOT profit target (TP)
- ✅ Never use full account balance
- ✅ Keep 50% uninvested
- ❌ **Likely won't prevent 100% loss** if market crashes >5% fast

---

## 2. Flash Crash / Wicks (CRITICAL)

### What Happens?
Price temporarily spikes/drops 5-10% in milliseconds due to:
- Forced liquidation cascade (one person liquidated triggers others)
- Market maker pulling liquidity
- Low volume on that exchange
- Malicious trader dumping

Then snaps back.

### Your Bot Gets Wrecked
```
Entry: $95,000 (BTC with 50x leverage)
Sudden wick down: $94,500 (-0.5%)
Your loss: 0.5% × 50x = -25% account
SL triggered at $94,000 (-1%): -50% account
Then price bounces back to $95,000

Result: You lost 50% while wick lasted milliseconds
```

### Bot Safeguards (Limited)
- Circuit breaker: Pause if >15% 1h candle (too late)
- SL orders: Don't always execute in flash crash
- **Real protection**: Only possible with flash crash insurance products (expensive, rare)

---

## 3. Leverage Mismanagement (CRITICAL)

### Bot Mistakes That Can Happen
1. **CCXT doesn't enforce leverage cap** → Request 200x, gets partial fill at 100x
2. **Leverage not maintained** → Bybit resets on API reconnect
3. **Positional disaster** → TP set wrong, no SL, trade goes against you forever
4. **Cascade failure** → First loss starts loss streak, bot keeps opening at reduced size, margin erodes

### Prevention Attempts in Bot
- ✅ Cap leverage at 95% of symbol max
- ✅ Validate leverage before opening trade
- ❌ **Can't prevent Bybit's internal margin calculation errors**

---

## 4. API & Software Bugs (HIGH)

### Possible Failures
- **CCXT library bug**: Wrong order type sent, gets filled at market price (slippage loss)
- **Bybit API timeout**: Order opens but you don't know, think it closed, re-open = 2x position
- **Network disconnect**: Bot can't check if position still open, commands queued but not sent
- **Database corruption**: Trade logs lost, liquidation happened offscreen
- **AI decision fail**: Gets stuck calling API, misses close, position waits for manual close

### Examples
```
2023: CCXT reported decimal precision bug → orders for 123.456789001 BTC (should be 0.00001)
2022: Binance API returned wrong balance → bot thought it had 10x more margin
2021: Connection drops → position opened 3x (1 real, 2 retries)
```

### Bot Safeguards
- ✅ Try-catch blocks on every API call
- ✅ Fallback to no-trade if API fails
- ✅ Sync balance with DB every cycle
- ❌ **Can't prevent Bybit server returning wrong data**

---

## 5. Exchange Risk (HIGH)

### Scenarios
```
Exchange shuts down (unlikely but happened):
- FTX (2022): $8B funds frozen, users lost 90%+
- Celsius Network (2022): Yield product collapsed
- Crypto.com (2023): Security breach

Even if solvent: Withdrawal freeze = can't exit positions = forced hold = liquidation

Regulatory ban: Nigeria/US restricts crypto derivatives
Result: Can't trade, funds frozen 6-12 months
```

### What You Can Do
- ✅ Withdraw profits regularly (don't leave all money on exchange)
- ✅ Use reputable exchange (Bybit is OK, not risk-free)
- ✅ Keep only 10-20% of net worth on exchange
- ❌ **Can't fully prevent sovereign/regulatory risk**

---

## 6. Market Manipulation (HIGH)

### How Crypto Derivatives Are Manipulated
```
Low-volume alt coins:
- Whale sells: Massive dumping → cascade liquidates shorts
- Whale buys: Squeeze → cascade liquidates longs
- Fast reversal: Whale exits, price snap-reverses
Result: Retail traders liquidated, whale profits

Bybit perpetuals especially vulnerable because:
- Funding rates incentivize over-leverage
- No circuit breakers (unlike spot)
- 24/7 trading (can't escape via close time)
```

### Examples
```
SHIB flash crash 2021: Price went to $0.00000001, liquidated millions
Pump-and-dump: AI picks hot social/news symbol → manipulator dumps → liquidates
Liquidation cascades: One major liquidation triggers others → avalanche
```

### Prevention
- ✅ Avoid low-volume altcoins (stick to top 20: BTC, ETH, etc.)
- ✅ Small position size (1-3% per trade)
- ✅ Wider stops (don't SL at -15%, use -30%)
- ❌ **Whales have better data + execution, will win**

---

## 7. Regulatory Risk (MEDIUM)

### Jurisdictions Where Crypto Futures Banned
- **USA**: SEC enforcement, NY banned, considered securities in some states
- **UK**: FCA restrictions on leverage (max 2:1 for retail)
- **EU**: ESMA (max 2:1 leverage for retail)
- **Nigeria**: No explicit ban yet (as of Feb 2026) but proposed restrictions

### Taiwan, Singapore, Japan: Regulated, retail access limited

### If Banned in Your Country
```
Result: Can't legally trade → using bot = criminal liability
Penalty: Fines up to $250k, jail time possible in some jurisdictions
```

### What the Bot Doesn't Do
- ❌ Check if derivatives trading is legal in your country
- ❌ Provide tax advice (you're responsible)
- ❌ Withhold taxes (you owe 100%)

---

## 8. Slippage & Fees (MEDIUM)

### Fees on Every Trade
- **Taker fee (opening)**: ~0.05% (Bybit standard)
- **Maker fee (closing)**: ~0.02% (if limit order fills slowly)
- **Liquidation fee**: 5.5% of liquidated position (catastrophic)
- **Network fees**: Negligible on centralized exchange

**Example:**
```
Trade 1: Open $5,000 position → Pay $2.50 fee
Trade 1: Close position → Pay $1 fee
Total: $3.50 fee per round trip (\~0.07%)

10 trades: $35 in fees (10x $5k positions)
If avg profit per trade: +1% ($50), fee kills it
Need 2%+ per trade just to breakeven on fees
```

### Slippage
Market impact: Large order sells into thin order book → gets worse price

```
You want to buy $5k at market
Order book: 
- $1k @ $95,000
- $2k @ $95,010
- $1.5k @ $95,020
- $0.5k @ $95,030

Your $5k order fills at: avg $95,012 (not $95k)
Slippage: $60 loss immediately
```

---

## 9. Psychological/Behavioral Risks (HIGH)

### How Traders Lose Fast
```
Win: +$500 → confidence ↑
Loss: -$500 → emotional ↑
Override bot settings: /risk high
Over-leverage: Use max leverage
Over-size: 10% per trade instead of 2%
Revenge trade: Double down after loss
Sleep loss: Checking bot 10x/night

Result: Blown account in 2-3 days
```

### Bot Fights This (Imperfectly)
- ✅ Forced loss streak pause after 3 losses
- ✅ Auto position sizing (no manual override mid-cycle)
- ✅ Pre-set TP/SL (no moving stop)
- ❌ **Can't stop /high or /risk high commands**
- ❌ **Can't stop you from panicking and /kill**

---

## 10. Third-Party API Risks (MEDIUM)

Bot depends on:
- **CoinGecko**: Project updates/news feed down → no directional bias → bot defaults
- **Gemini/Groq**: AI API down → bot skips decision, fallback rule used
- **Exchangerate-api**: NGN rate fetch fails → uses fallback rate

### Failures
```
CoinGecko outage (happens rarely; respect public API rate limits)
→ Bot trades blindly (24h change only, no news)
→ Hits bad trades without news context

Groq API rate limit exhausted
→ Bot switches to Gemini only (1 model instead of 2)
→ Confidence lower, trades fewer/smaller

All APIs down
→ Bot goes into fallback mode (pure 24h change rule)
→ Still trades but with bad logic
```

### Mitigation
- ✅ Try-catch on all API calls
- ✅ Fallback logic implemented
- ❌ **Fallback is weaker, still can lose money**

---

## 11. Daily/Weekly Loss Limits Insufficient (HIGH)

### Bot Has These Safeguards
- Circuit breaker: Pause on 15% 1h swing (🟡 LATE)
- Loss streak: Pause on 3 consecutive losses (🟡 AFTER LOSSES)
- Balance protection: Pause on >20% daily drawdown (🟡 AFTER DRAWDOWN)

### Why Insufficient
```
Example: Account $10k
Loss 1: -$2k (20% already, but stops: 60min cool-down)
Loss 2 during cooldown: -$3k more (can't prevent if pos already open)
Loss 3: -$2k
Total: -$7k (70% in 45 min), pause triggered too late
```

### The Reality
- These safeguards are **damage reduction**, not prevention
- A bad streak during consolidation can wipe you faster than pause triggers

---

## 12. "No Profit Guarantee" (Obviously CRITICAL)

**This bot is EXPERIMENTAL. No guarantees:**

❌ Not profitable
❌ Won't make 3x/week
❌ Won't survive 2024 bear market
❌ Won't avoid liquidation
❌ Won't catch 100% of moves (misses some signals)

**Historical performance:**
- AI models: ~55-60% accuracy in crypto (only slightly better than coin flip)
- Leverage trading: 80-90% of retail traders lose money
- Bot anomalies: Unknown (never stress-tested in 2020 crash scenario)

---

## Complete Risk Checklist (Be Honest)

Before you trade, answer these:

- [ ] I can afford to lose **100% of this money RIGHT NOW**
- [ ] I have **other income/savings** (not living off trading)
- [ ] I've tested on paper mode for **2+ weeks**
- [ ] I've tested on testnet for **2+ weeks**
- [ ] I understand leverage can liquidate me in **<1 minute**
- [ ] I won't check the bot more than **once per day**
- [ ] I won't panic /kill when drawdown hits **>15%**
- [ ] I'm OK with **losing $100-500** (minimum testable movement)
- [ ] I've read all of `README.md`, `TESTING.md`, and this file
- [ ] I've consulted a tax professional about taxes
- [ ] I've consulted a lawyer (if derivatives illegal in my jurisdiction)

**If you can't honest YES all of these, don't use this bot.**

---

## What NOT to Do

❌ Use money you need for rent/food/emergencies  
❌ Leverage everything (keep 50%+ in cash)  
❌ Trade on social proof ("Discord says BTC going 100x")  
❌ Ignore stop-losses (thinking "it'll bounce")  
❌ Catch falling knives (short strong downtrends)  
❌ Use max leverage from day 1  
❌ Trust AI blindly (verify signals manually)  
❌ Trade if you're tired/emotional  
❌ Skip the testnet phase  
❌ Keep all funds on exchange  

---

## Emergency Procedures

### If Liquidation Seems Imminent
```bash
# Close all positions manually (faster than bot)
/kill  # Closes all in bot

# OR go manually to Bybit app:
1. Portfolio → Open Positions
2. Click position → Close
3. Click "Market" → "Close"
4. Confirm
```

### If Bot Goes Haywire
```bash
Ctrl+C  # Kill bot immediately
# Manually check Bybit: Are there open positions?
# If yes, close them manually, fastest way
```

### If Account Gets Liquidated
```
1. Check Bybit "Settlement History" to see liquidation info
2. Export trades: /export (CSV)
3. Analyze what went wrong
4. Take break (emotional recovery)
5. Post-mortem: Why did it happen?
6. Fix: New risk settings, testnet again
7. Only resume if you fix the flaw
```

---

## Final Words

This bot is:
- **For experienced traders** (ideally 2+ years futures experience)
- **Experimental** (may have bugs no amount of testing catches)
- **High-risk** (expects 50% drawdown is normal)
- **Not healthcare** (don't trade if depressed/desperate)

This bot is NOT for:
- Beginners (missing risk intuition)
- Desperate people (if you NEED profits, you'll panic-trade)
- Over-leveraged (already in debt)
- Jurisdictions banning derivatives
- Anyone who didn't read this whole file

---

**If you've read this far and still want to use the bot: Welcome to the 10% of traders who might actually understand the risks. Good luck. Trade safe.**

🚀 Or don't. Keep your money. That's the safest choice.
