"""
Aggressive High-Reward Telegram-Controlled Bybit Futures Trading Bot
Main entry point: Orchestrates AI decisions, trading, risk, reporting on 15-min autonomous loop
"""
import os
import logging
import asyncio
import schedule
import pytz
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import dotenv

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, filters
import ccxt.async_support as ccxt

# Import local modules
import db_utils
from ai_decision import get_ai_decision, fallback_decision
from risk_manager import RiskManager
from reporter import Reporter
from trading import BybitTrader
import commands
from health_check import start_health_server, stop_health_server

# Load environment
dotenv.load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = int(os.getenv('OWNER_TELEGRAM_ID', '0'))
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')
PAPER_MODE = os.getenv('PAPER_MODE', 'true').lower() == 'true'
MIN_BALANCE = float(os.getenv('MIN_BALANCE', '20'))
PROFIT_WALLET_ADDRESS = os.getenv('PROFIT_WALLET_ADDRESS', '')
PROFIT_WITHDRAWAL_THRESHOLD = float(os.getenv('PROFIT_WITHDRAWAL_THRESHOLD', '100'))

# Main coins only (reduce volatility/manipulation risk)
MAIN_COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOGE', 'AVAX', 'POLYGON', 'LINK', 'LTC', 'BCH']

WAT = pytz.timezone('Africa/Lagos')
LOOP_INTERVAL = 15  # minutes

if not all([TELEGRAM_TOKEN, GEMINI_API_KEY, GROQ_API_KEY]):
    logger.error("Missing required API keys. Check .env file (needs TELEGRAM_TOKEN, GEMINI_API_KEY, GROQ_API_KEY).")
    exit(1)


# ============================================================================
# GLOBAL BOT STATE
# ============================================================================

class TradingBot:
    def __init__(self):
        self.telegram_bot: Optional[Bot] = None
        self.trader: Optional[BybitTrader] = None
        self.risk_manager = RiskManager()
        self.reporter = Reporter()
        self.is_running = False
        self.health_server_runner = None  # For uptime monitoring
        
        # State
        self.starting_balance = 0.0
        self.current_balance = 0.0
        self.daily_loss_percent = 0.0
        self.loss_streak = 0
        self.is_paused = False
        self.active_symbols: set = set()
        
        # Timing
        self.last_trade_time = 0
        self.last_daily_report = None
        self.last_weekly_report = None
    
    async def initialize(self) -> bool:
        """Initialize bot: Database, exchange, telegram."""
        try:
            logger.info("=" * 60)
            logger.info("🚀 AGGRESSIVE PROFIT HUNTER BOT INITIALIZING")
            logger.info("=" * 60)
            
            # Database
            db_utils.init_database()
            logger.info("✓ Database ready")
            
            # Telegram
            self.telegram_bot = Bot(token=TELEGRAM_TOKEN)
            await self.telegram_bot.set_webhook(allowed_updates=[])
            logger.info("✓ Telegram connected")
            
            # Trading
            self.trader = BybitTrader(BYBIT_API_KEY, BYBIT_API_SECRET, PAPER_MODE)
            if not await self.trader.init_markets():
                logger.error("Failed to init markets")
                return False
            logger.info(f"✓ Bybit connected (Paper mode: {PAPER_MODE})")
            
            # Initial balance
            self.starting_balance = await self.trader.get_balance()
            self.current_balance = self.starting_balance
            if self.starting_balance <= 0:
                self.starting_balance = 10000.0
                logger.warning("Balance fetch failed, using default 10000 USDT")
            
            db_utils.set_config('starting_balance', str(self.starting_balance))
            db_utils.set_config('current_balance', str(self.current_balance))
            db_utils.set_config('min_confidence', 'medium')
            db_utils.set_config('trading_active', 'true')
            
            # Load state
            self.is_paused = db_utils.get_config('trading_active', 'true').lower() != 'true'
            self.loss_streak, _, _ = db_utils.get_loss_streak()
            
            # Start health check server (for uptime monitoring)
            self.health_server_runner = await start_health_server()
            
            self.is_running = True
            
            # Startup message
            startup_msg = (
                f"🔥 **Aggressive Profit Hunter Bot Online**\n\n"
                f"Status: {'🔘 RUNNING' if not self.is_paused else '⏸️  PAUSED'}\n"
                f"Balance: ${self.current_balance:,.2f}\n"
                f"Mode: {'📰 PAPER' if PAPER_MODE else '🔴 LIVE'}\n"
                f"Loss Streak: {self.loss_streak}/3\n\n"
                f"⚠️ EXTREME RISK: High leverage trading active.\n"
                f"Use /help for commands."
            )
            await self.telegram_bot.send_message(OWNER_ID, startup_msg, parse_mode='Markdown')
            
            logger.info("✅ Bot initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def run_trading_loop(self) -> None:
        """Main autonomous trading loop (runs every 15 min)."""
        logger.info(f"Starting trading loop ({LOOP_INTERVAL}min interval)")
        
        # Schedule functions
        schedule.every(LOOP_INTERVAL).minutes.do(asyncio.create_task, self.trading_cycle())
        schedule.every().day.at('00:00').do(asyncio.create_task, self.daily_report())
        schedule.every().sunday.at('00:00').do(asyncio.create_task, self.weekly_report())
        
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
    
    async def trading_cycle(self) -> None:
        """
        Main trading cycle: Fetch symbols, get AI decisions, execute trades.
        Runs every 15 minutes.
        """
        try:
            # Check pause/balance
            self.is_paused = db_utils.get_config('trading_active', 'true').lower() != 'true'
            if self.is_paused:
                logger.info("⏸️ Trading loop paused")
                return
            
            # Update balance
            new_balance = await self.trader.get_balance()
            if new_balance > 0:
                self.current_balance = new_balance
                db_utils.set_config('current_balance', str(self.current_balance))
            
            # Balance protection check
            is_violated, reason = self.risk_manager.check_balance_protection(
                self.current_balance, self.starting_balance, MIN_BALANCE, daily_drawdown_limit=20
            )
            if is_violated:
                await self.alert_pause(f"🚨 {reason}")
                return
            
            logger.info(f"--- Trading cycle @ {datetime.now(WAT).strftime('%H:%M:%S')} ---")
            
            # Get high-volume/volatility symbols + watchlist
            symbols = await self.get_trading_symbols()
            logger.info(f"Trading symbols: {symbols}")
            
            for symbol in symbols:
                try:
                    # Check symbol pause
                    is_paused, pause_reason = self.risk_manager.is_symbol_paused(symbol)
                    if is_paused:
                        logger.info(f"  {symbol}: {pause_reason}")
                        continue
                    
                    await self.process_symbol(symbol)
                
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
        
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
    
    async def get_trading_symbols(self) -> list:
        """
        Fetch high-volume USDT perps + watchlist.
        ONLY main coins (BTC, ETH, SOL, etc.) - reduces volatility/manipulation risk.
        Returns symbols to consider.
        """
        try:
            symbols = set()
            
            # Get watchlist (already filtered by user)
            watchlist = db_utils.get_watchlist()
            symbols.update(watchlist)
            
            # Get main coin symbols only from CCXT
            if hasattr(self.trader.exchange, 'symbols'):
                all_symbols = [s for s in self.trader.exchange.symbols if 'USDT' in s]
                # Filter to only main coins
                main_symbols = [
                    s for s in all_symbols
                    if any(coin in s.upper() for coin in MAIN_COINS)
                ]
                symbols.update(main_symbols[:12])  # Top main coins only
            
            return list(symbols)[:15]  # Limit to reduce API calls
        
        except Exception as e:
            logger.error(f"Get symbols error: {e}")
            return []
    
    async def process_symbol(self, symbol: str) -> None:
        """
        Analyze and potentially open trade on a symbol.
        """
        logger.info(f"  Analyzing {symbol}...")
        
        try:
            # Fetch ticker + OHLCV
            ticker = await self.trader.get_ticker(symbol)
            if not ticker:
                logger.warning(f"    No ticker data")
                return
            
            ohlcv = await self.trader.get_ohlcv(symbol, '1h', limit=20)
            
            # Extract metrics
            current_price = ticker['last']
            change_24h = ((ticker['last'] - ticker.get('open', ticker['last'])) / 
                         ticker.get('open', ticker['last']) * 100) if ticker.get('open') else 0
            volume_24h = ticker.get('volume', 0)
            
            # Calculate ATR (volatility)
            if ohlcv and len(ohlcv) > 1:
                highs = [c[2] for c in ohlcv[-14:]]
                lows = [c[3] for c in ohlcv[-14:]]
                closes = [c[4] for c in ohlcv[-14:]]
                atr = sum([h - l for h, l in zip(highs, lows)]) / len(highs)
            else:
                atr = current_price * 0.01  # Default to 1% volatility
            
            # Check swing breaker
            is_breaker, reason = self.risk_manager.check_swing_breaker(
                symbol, ticker.get('open', current_price), ticker['high'], ticker['low']
            )
            if is_breaker:
                await self.send_alert(f"⚠️ {symbol}: {reason}")
                return
            
            # Get AI decision
            min_conf = db_utils.get_config('min_confidence', 'medium')
            decision, confidence, reason, suggested_lev, tp, sl = await get_ai_decision(
                symbol, current_price, change_24h, volume_24h, atr, min_conf
            )
            
            if not decision or decision == 'no_trade':
                # Fallback
                if not decision:
                    decision, confidence, suggested_lev = await fallback_decision(
                        symbol, change_24h, volume_24h
                    )
                
                if not decision:
                    logger.info(f"    {symbol}: No signal")
                    return
            
            logger.info(f"    {symbol}: {decision.upper()} (confidence: {confidence})")
            
            # Get max leverage
            max_lev = await self.trader.get_max_leverage(symbol)
            safe_lev = self.risk_manager.validate_leverage(suggested_lev, max_lev)
            
            # Calculate position size
            loss_streak, _, _ = db_utils.get_loss_streak()
            pos_size = self.risk_manager.calculate_position_size(
                self.current_balance,
                base_percent=3.0,
                confidence_level=confidence,
                volatility_factor=min(1.5, atr / (current_price * 0.01) + 0.5),
                recent_loss_streak=loss_streak
            )
            
            # Open trade
            success, order_id, entry = await self.trader.open_position(
                symbol, decision, pos_size, safe_lev, tp, sl
            )
            
            if success:
                # Log trade
                trade_id = db_utils.add_trade(
                    symbol, decision, entry, safe_lev, pos_size,
                    ai_groq=decision, confidence=confidence,
                    tp=tp, sl=sl, reason=reason
                )
                
                # Send report
                report = self.reporter.format_trade_open_report(
                    symbol, decision, entry, safe_lev, pos_size,
                    reason, tp, sl, self.current_balance
                )
                await self.send_report(report)
                
                logger.info(f"    ✅ Trade opened: ID={trade_id}")
                self.active_symbols.add(symbol)
            else:
                logger.warning(f"    ❌ Trade execution failed")
        
        except Exception as e:
            logger.error(f"Process {symbol} error: {e}")
    
    async def close_expiring_trades(self) -> None:
        """
        Check and close trades that hit TP/SL or are old.
        (Simplified: Just check if TP/SL reached)
        """
        try:
            open_trades = db_utils.get_open_trades()
            
            for trade in open_trades:
                symbol = trade['symbol']
                trade_id = trade['id']
                
                ticker = await self.trader.get_ticker(symbol)
                if not ticker:
                    continue
                
                current = ticker['last']
                entry = trade['entry_price']
                tp = trade['target_tp_percent']
                sl = trade['stop_loss_percent']
                
                should_close = False
                reason = ''
                
                # Check TP
                if trade['side'] == 'long' and tp and current >= entry * (1 + tp / 100):
                    should_close = True
                    reason = f"TP Hit (+{tp:.0f}%)"
                elif trade['side'] == 'short' and tp and current <= entry * (1 - tp / 100):
                    should_close = True
                    reason = f"TP Hit (+{tp:.0f}%)"
                
                # Check SL
                if trade['side'] == 'long' and sl and current <= entry * (1 + sl / 100):
                    should_close = True
                    reason = f"SL Hit ({sl:.0f}%)"
                elif trade['side'] == 'short' and sl and current >= entry * (1 - sl / 100):
                    should_close = True
                    reason = f"SL Hit ({sl:.0f}%)"
                
                if should_close:
                    success, exit_price, pnl = await self.trader.close_position(symbol)
                    
                    if success:
                        pnl_pct = (pnl / (trade['entry_price'] * trade['quantity'])) * 100 if trade['quantity'] > 0 else 0
                        
                        # Update trade in DB
                        db_utils.close_trade(trade_id, exit_price, pnl, pnl_pct, fee=0.001)
                        
                        # Update streak
                        if pnl < 0:
                            new_streak = db_utils.increment_loss_streak()
                            if new_streak >= 3:
                                await self.alert_pause("🚨 3 consecutive losses! Loop paused. Review /history, then /resume.")
                                return
                        else:
                            db_utils.reset_loss_streak()
                        
                        # Report close
                        close_report = self.reporter.format_trade_close_report(
                            symbol, trade['side'], entry, exit_price,
                            pnl, pnl_pct, 0, trade['leverage'],
                            int((datetime.fromisoformat(str(datetime.now())) - 
                                 datetime.fromisoformat(trade['entry_time'])).total_seconds() / 60),
                            self.current_balance, 0, 0
                        )
                        await self.send_report(close_report)
                        
                        logger.info(f"  ✅ Trade closed: {symbol} {reason} P&L {pnl_pct:+.2f}%")
                        self.active_symbols.discard(symbol)
        
        except Exception as e:
            logger.error(f"Close trades error: {e}")
    
    async def daily_report(self) -> None:
        """Send daily P&L report (midnight WAT)."""
        try:
            now = datetime.now(WAT)
            if (self.last_daily_report and 
                (now - self.last_daily_report).days < 1):
                return
            
            trades = db_utils.get_trade_history(limit=1000)
            summary = self.reporter.calculate_daily_summary(trades, now)
            report = self.reporter.format_daily_report(summary)
            
            await self.send_report(report)
            self.last_daily_report = now
            logger.info("Daily report sent")
        
        except Exception as e:
            logger.error(f"Daily report error: {e}")
    
    async def weekly_report(self) -> None:
        """Send weekly P&L report (Sunday midnight WAT)."""
        try:
            now = datetime.now(WAT)
            if (self.last_weekly_report and 
                (now - self.last_weekly_report).days < 7):
                return
            
            trades = db_utils.get_trade_history(limit=10000)
            summary = self.reporter.calculate_weekly_summary(trades)
            report = self.reporter.format_weekly_report(summary)
            
            await self.send_report(report)
            self.last_weekly_report = now
            logger.info("Weekly report sent")
        
        except Exception as e:
            logger.error(f"Weekly report error: {e}")
    
    async def send_report(self, message: str) -> None:
        """Send trade/report message to owner."""
        try:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    OWNER_ID, message, parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Send report error: {e}")
    
    async def send_alert(self, message: str) -> None:
        """Send alert message (risk/breaker alert)."""
        try:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    OWNER_ID, message, parse_mode='Markdown'
                )
                logger.warning(f"Alert sent: {message[:50]}...")
        except Exception as e:
            logger.error(f"Send alert error: {e}")
    
    async def alert_pause(self, reason: str) -> None:
        """Pause bot and alert owner."""
        db_utils.set_config('trading_active', 'false')
        db_utils.set_config('pause_reason', reason)
        self.is_paused = True
        
        await self.send_alert(reason)
    
    async def shutdown(self) -> None:
        """Graceful shutdown: Close positions, disconnect."""
        try:
            logger.info("Shutting down...")
            
            self.is_running = False
            
            # Stop health check server
            if self.health_server_runner:
                await stop_health_server(self.health_server_runner)
            
            # Close all open positions
            open_trades = db_utils.get_open_trades()
            for trade in open_trades:
                await self.trader.close_position(trade['symbol'])
            
            await self.trader.close()
            
            shutdown_msg = "🔴 Bot shutdown complete. All positions closed."
            await self.send_alert(shutdown_msg)
            
            logger.info("✅ Shutdown complete")
        
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

    async def reinit_trader(self) -> bool:
        """Recreate the BybitTrader instance using BYBIT_API_KEY/BYBIT_API_SECRET from environment.
        Returns True on success.
        """
        try:
            api_key = os.getenv('BYBIT_API_KEY', '')
            api_secret = os.getenv('BYBIT_API_SECRET', '')
            if not api_key or not api_secret:
                await self.send_alert("❌ BYBIT API keys are missing. Set them first via /setbybit or .env.")
                return False

            # Close existing trader cleanly
            if self.trader:
                try:
                    await self.trader.close()
                except Exception as e:
                    logger.warning(f"Failed to close old trader cleanly: {e}")

            # Create new trader and initialize markets
            new_trader = BybitTrader(api_key, api_secret, PAPER_MODE)
            ok = await new_trader.init_markets()
            if not ok:
                logger.error("Failed to initialize markets for new Bybit trader")
                return False

            self.trader = new_trader

            # Update balance
            try:
                self.current_balance = await self.trader.get_balance()
                db_utils.set_config('current_balance', str(self.current_balance))
            except Exception:
                logger.warning("Could not fetch balance after re-init; skipping balance update.")

            await self.send_alert("✅ Bybit trader re-initialized and connected.")
            logger.info("Bybit trader re-initialized in-process")
            return True

        except Exception as e:
            logger.error(f"Re-init trader error: {e}")
            return False


# ============================================================================
# TELEGRAM APPLICATION SETUP
# ============================================================================

async def setup_telegram_handlers(app: Application) -> None:
    """Register all Telegram command handlers."""
    
    # Command handlers
    app.add_handler(CommandHandler('start', commands.cmd_start))
    app.add_handler(CommandHandler('status', commands.cmd_status))
    app.add_handler(CommandHandler('pause', commands.cmd_pause))
    app.add_handler(CommandHandler('resume', commands.cmd_resume))
    app.add_handler(CommandHandler('history', commands.cmd_history))
    app.add_handler(CommandHandler('tax', commands.cmd_tax))
    app.add_handler(CommandHandler('report', commands.cmd_report))
    app.add_handler(CommandHandler('setconf', commands.cmd_setconf))
    app.add_handler(CommandHandler('risk', commands.cmd_risk))
    app.add_handler(CommandHandler('setbybit', commands.cmd_setbybit))
    app.add_handler(CommandHandler('reinit', commands.cmd_reinit_trader))
    app.add_handler(CommandHandler('addwatch', commands.cmd_addwatch))
    app.add_handler(CommandHandler('watchlist', commands.cmd_watchlist))
    app.add_handler(CommandHandler('reinvest', commands.cmd_reinvest))
    app.add_handler(CommandHandler('export', commands.cmd_export))
    app.add_handler(CommandHandler('kill', commands.cmd_kill))
    app.add_handler(CommandHandler('help', commands.cmd_help))
    app.add_handler(CommandHandler('simulate', commands.cmd_simulate))
    app.add_handler(CommandHandler('high', commands.cmd_high_mode))
    app.add_handler(CommandHandler('withdraw', commands.cmd_withdraw_profits))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(commands.button_resume, pattern='resume_callback'))
    app.add_handler(CallbackQueryHandler(commands.button_pause, pattern='pause_callback'))
    app.add_handler(CallbackQueryHandler(commands.button_confirm_kill, pattern='confirm_kill'))
    app.add_handler(CallbackQueryHandler(commands.button_cancel_kill, pattern='cancel_kill'))


# ============================================================================
# MAIN
# ============================================================================

async def main() -> None:
    """Main async entry point."""
    
    # Initialize bot
    bot = TradingBot()
    if not await bot.initialize():
        return
    # Expose the bot instance to command handlers for runtime operations (re-init, etc.)
    try:
        commands.BOT_INSTANCE = bot
    except Exception:
        logger.warning("Could not set BOT_INSTANCE on commands module")
    
    # Telegram application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    await setup_telegram_handlers(app)
    
    # Start bot in background task
    try:
        # Start trading loop as background task
        trading_task = asyncio.create_task(bot.run_trading_loop())
        
        # Start Telegram polling
        async with app:
            await app.initialize()
            await app.start()
            
            # Run until stopped
            await asyncio.Event().wait()
            
            await app.stop()
        
        # Cleanup on exit
        if not trading_task.done():
            trading_task.cancel()
        await bot.shutdown()
    
    except KeyboardInterrupt:
        logger.info("Bot interrupted")
        await bot.shutdown()
    except Exception as e:
        logger.error(f"Main error: {e}")
        await bot.shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated")
