"""
Telegram commands handler: /start, /pause, /resume, /history, /status, /tax, /kill, etc.
"""
import logging
import asyncio
from typing import Optional
from datetime import datetime
import pytz
import csv
from io import StringIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import os
import dotenv
import db_utils
from reporter import Reporter

logger = logging.getLogger(__name__)

WAT = pytz.timezone('Africa/Lagos')

# Global BOT_INSTANCE for runtime operations
BOT_INSTANCE = None


# Helper: run blocking db operations in thread pool to avoid blocking event loop
async def _run_in_thread(fn, *args, **kwargs):
    """Wrapper to run blocking sync functions in asyncio thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# Conversation states
CONF_SETTING, LEV_MODE, PAUSE_AFTER, RISK_PRESET, WATCH_SYMBOL, REINVEST_MODE, NOTIFY_SETTING = range(7)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command: Initialize user and send welcome message."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started bot")
    
    # Initialize default configs in thread pool
    await _run_in_thread(db_utils.set_config, 'min_confidence', 'medium')
    await _run_in_thread(db_utils.set_config, 'pause_after_losses', '3')
    await _run_in_thread(db_utils.set_config, 'trading_active', 'true')
    await _run_in_thread(db_utils.set_config, 'reinvest_mode', 'off')
    await _run_in_thread(db_utils.set_config, 'notification_level', 'all')
    
    welcome_msg = (
        "🔥 **Aggressive Profit Hunter Bot Online**\n\n"
        "⚠️ **EXTREME RISK**: High leverage = liquidation possible. No guarantees.\n"
        "_Test on testnet first. This is a DEMO—use at your own risk._\n\n"
        "**Commands:**\n"
        "/status - View bot status\n"
        "/pause - Pause trading loop\n"
        "/resume - Resume trading loop\n"
        "/history - Show recent trades\n"
        "/tax - Estimate taxes (FIFO)\n"
        "/report - Force daily/weekly report\n"
        "/setconf high/medium - Set AI confidence threshold\n"
        "/risk low/medium/high - Preset risk levels\n"
        "/addwatch [symbol] - Add to watchlist\n"
        "/watchlist - Show watchlist\n"
        "/reinvest on/off - Auto compound profits\n"
        "/kill - Close all positions + shutdown\n"
        "/help - Full command list\n\n"
        "Ready to hunt profits? 🚀"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current bot status."""
    open_trades = await _run_in_thread(db_utils.get_open_trades)
    all_trades = await _run_in_thread(db_utils.get_trade_history, limit=1000)
    
    win_count = len([t for t in all_trades if t.get('pnl', 0) > 0])
    total_trades = len(all_trades)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    is_paused_raw = await _run_in_thread(db_utils.get_config, 'trading_active', 'true')
    is_paused = is_paused_raw.lower() != 'true'
    pause_reason = await _run_in_thread(db_utils.get_config, 'pause_reason', '')
    
    balance = float(await _run_in_thread(db_utils.get_config, 'current_balance', '10000'))
    starting_balance = float(await _run_in_thread(db_utils.get_config, 'starting_balance', '10000'))
    return_pct = ((balance - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0
    
    reporter = Reporter()
    status_msg = reporter.format_status_report(
        balance, starting_balance, len(open_trades), total_trades, win_rate, is_paused, pause_reason
    )
    
    keyboard = [
        [InlineKeyboardButton("▶️ Resume", callback_data='resume_callback'),
         InlineKeyboardButton("⏸️ Pause", callback_data='pause_callback')],
        [InlineKeyboardButton("📊 History", callback_data='history_callback'),
         InlineKeyboardButton("⚙️ Settings", callback_data='settings_callback')],
        [InlineKeyboardButton("🔴 Kill All", callback_data='kill_callback')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(status_msg, parse_mode='Markdown', reply_markup=reply_markup)


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pause the trading loop."""
    await _run_in_thread(db_utils.set_config, 'trading_active', 'false')
    await _run_in_thread(db_utils.set_config, 'pause_reason', 'Manual pause via /pause command')
    msg = "⏸️ Trading loop paused. Use /resume to continue."
    await update.message.reply_text(msg)
    logger.warning("Trading paused")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume the trading loop."""
    await _run_in_thread(db_utils.set_config, 'trading_active', 'true')
    await _run_in_thread(db_utils.set_config, 'pause_reason', '')
    msg = "▶️ Trading loop resumed!"
    await update.message.reply_text(msg)
    logger.info("Trading resumed")


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent trade history."""
    trades = await _run_in_thread(db_utils.get_trade_history, limit=20)
    
    if not trades:
        await update.message.reply_text("📭 No trade history yet.")
        return
    
    msg = "📋 **Recent Trades**\n\n"
    for t in trades[:10]:
        symbol = t.get('symbol', 'N/A')
        side = t.get('side', 'N/A').upper()
        pnl = t.get('pnl_percent', 0)
        pnl_emoji = '✅' if pnl > 0 else '❌'
        close_time = t.get('exit_time', 'N/A')[:10]
        
        msg += f"{pnl_emoji} {side} {symbol} | {pnl:+.2f}% | {close_time}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_tax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show tax estimation (FIFO)."""
    trades = await _run_in_thread(db_utils.get_trade_history, limit=10000)
    
    if not trades:
        await update.message.reply_text("📭 No closed trades for tax calculation.")
        return
    
    tax_usd, tax_ngn, breakdown = Reporter.estimate_tax_fifo(trades)
    tax_report = Reporter.format_tax_report(tax_usd, tax_ngn, breakdown)
    
    await update.message.reply_text(tax_report, parse_mode='Markdown')


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force daily/weekly report."""
    trades = await _run_in_thread(db_utils.get_trade_history, limit=1000)
    today = datetime.now(WAT)
    
    daily_summary = Reporter.calculate_daily_summary(trades, today)
    daily_report = Reporter.format_daily_report(daily_summary)
    
    weekly_summary = Reporter.calculate_weekly_summary(trades)
    weekly_report = Reporter.format_weekly_report(weekly_summary)
    
    msg = f"{daily_report}\n\n{weekly_report}"
    await update.message.reply_text(msg, parse_mode='Markdown')
    logger.info("Manual report generated")


async def cmd_setconf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set AI confidence threshold."""
    if not context.args or context.args[0].lower() not in ['high', 'medium', 'low']:
        await update.message.reply_text("Usage: /setconf high/medium/low")
        return
    
    conf = context.args[0].lower()
    await _run_in_thread(db_utils.set_config, 'min_confidence', conf)
    msg = f"✅ AI confidence threshold set to: {conf} (will trade only {conf}+ confidence)"
    await update.message.reply_text(msg)


async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set risk preset (low/medium/high)."""
    if not context.args or context.args[0].lower() not in ['low', 'medium', 'high']:
        await update.message.reply_text("Usage: /risk low/medium/high")
        return
    
    risk_level = context.args[0].lower()
    
    # Reduced defaults for main coins + volatility protection
    risk_presets = {
        'low': {'max_lev': 5, 'size_pct': 1, 'stop_loss': -8},       # Very conservative
        'medium': {'max_lev': 15, 'size_pct': 2, 'stop_loss': -15},   # Default, reduced from 50x
        'high': {'max_lev': 50, 'size_pct': 3, 'stop_loss': -25}      # Was 100x, now 50x
    }
    
    preset = risk_presets[risk_level]
    await _run_in_thread(db_utils.set_config, 'risk_level', risk_level)
    await _run_in_thread(db_utils.set_config, 'max_leverage', str(preset['max_lev']))
    await _run_in_thread(db_utils.set_config, 'position_size_pct', str(preset['size_pct']))
    await _run_in_thread(db_utils.set_config, 'stop_loss_pct', str(preset['stop_loss']))
    
    msg = (
        f"⚠️ Risk level set to: {risk_level.upper()} (Main coins only)\n"
        f"Max Lev: {preset['max_lev']}x | Size: {preset['size_pct']}% | SL: {preset['stop_loss']}%\n\n"
        f"💡 60% of profits → external wallet\n"
        f"💡 40% of profits → reinvest"
    )
    await update.message.reply_text(msg)


async def cmd_addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add symbol to watchlist."""
    if not context.args:
        await update.message.reply_text("Usage: /addwatch BTCUSDT ETHUSDT ...")
        return
    
    for symbol in context.args:
        symbol = symbol.upper()
        if not symbol.endswith(('USDT', 'BUSD')):
            symbol += 'USDT'
        await _run_in_thread(db_utils.add_watchlist, symbol)
    
    msg = f"✅ Added to watchlist: {', '.join(context.args)}"
    await update.message.reply_text(msg)


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current watchlist."""
    symbols = await _run_in_thread(db_utils.get_watchlist)
    
    if not symbols:
        msg = "📭 Watchlist empty. Use /addwatch to add symbols."
    else:
        msg = f"👀 **Watchlist ({len(symbols)})**\n{', '.join(symbols)}"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_reinvest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle reinvest mode (compound 50% of profits)."""
    if not context.args or context.args[0].lower() not in ['on', 'off']:
        await update.message.reply_text("Usage: /reinvest on/off")
        return
    
    mode = context.args[0].lower()
    await _run_in_thread(db_utils.set_config, 'reinvest_mode', mode)
    
    msg = f"🔄 Reinvest mode: {mode.upper()} (50% of profits auto-compound)"
    await update.message.reply_text(msg)


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export trade history as CSV."""
    trades = await _run_in_thread(db_utils.get_trade_history, limit=10000)
    
    if not trades:
        await update.message.reply_text("📭 No trades to export.")
        return
    
    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'symbol', 'side', 'entry_price', 'exit_price', 'pnl', 'pnl_percent',
        'leverage', 'entry_time', 'exit_time', 'fee', 'reason'
    ])
    writer.writeheader()
    
    for t in trades:
        writer.writerow({
            'symbol': t.get('symbol'),
            'side': t.get('side'),
            'entry_price': t.get('entry_price'),
            'exit_price': t.get('exit_price'),
            'pnl': t.get('pnl'),
            'pnl_percent': t.get('pnl_percent'),
            'leverage': t.get('leverage'),
            'entry_time': t.get('entry_time'),
            'exit_time': t.get('exit_time'),
            'fee': t.get('fee'),
            'reason': t.get('reason')
        })
    
    csv_data = output.getvalue()
    await update.message.reply_document(
        document=csv_data.encode(),
        filename=f"trades_{datetime.now(WAT).strftime('%Y%m%d_%H%M%S')}.csv",
        caption="📊 Trade history export"
    )
    logger.info("Trade history exported")


async def cmd_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close all positions and shutdown."""
    msg = (
        "🔴 **KILL INITIATED**\n"
        "Closing all positions and shutting down...\n\n"
        "⚠️ This action cannot be undone.\n"
        "Press ✅ to confirm or ❌ to cancel."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data='confirm_kill'),
         InlineKeyboardButton("❌ Cancel", callback_data='cancel_kill')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show full command help."""
    help_msg = (
        "🤖 **Profit Hunter Bot - Commands**\n\n"
        "*Core*\n"
        "/start - Initialize bot\n"
        "/status - View status + quick actions\n"
        "/pause - Pause trading loop\n"
        "/resume - Resume trading loop\n"
        "/kill - Close all + shutdown\n\n"
        
        "*Reports & Analytics*\n"
        "/history - Recent trades\n"
        "/tax - Tax estimate (FIFO, Nigeria)\n"
        "/report - Daily/weekly P&L\n"
        "/export - Trade CSV dump\n\n"
        
        "*Profits & Withdrawals*\n"
        "/withdraw - Show 60% profit withdrawal ready to send\n\n"
        
        "*Settings*\n"
        "/setconf high/medium/low - AI confidence threshold\n"
        "/risk low/medium/high - Risk presets (now lower defaults)\n"
        "/addwatch [symbols] - Add to watchlist (main coins only)\n"
        "/watchlist - Show watched symbols\n"
        "/reinvest on/off - 40% profit auto-compound (60% to wallet)\n"
        "/notify all/trades/alerts/off - Notification level\n\n"
        
        "*Advanced*\n"
        "/simulate [symbol] [long/short] [lev] - Hypothetical P&L\n"
        "/high - Max leverage mode (⚠️ liquidation risk)\n\n"
        
        "**Disclaimer**\n"
        "🚨 EXTREME RISK: Main coins only (BTC, ETH, SOL, etc.)\n"
        "Minimum: $20 | Position: 2% max\n"
        "60% of profits → external wallet\n"
        "40% of profits → reinvest in bot\n\n"
        "Test on testnet FIRST!"
    )
    
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def cmd_simulate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate hypothetical trade P&L."""
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /simulate BTCUSDT long 50")
        return
    
    symbol = context.args[0].upper()
    side = context.args[1].lower()
    leverage = float(context.args[2]) if context.args[2].isdigit() else 10
    
    if side not in ['long', 'short']:
        await update.message.reply_text("Side must be 'long' or 'short'")
        return
    
    msg = (
        f"📈 **Simulation** ({symbol})\n"
        f"Side: {side.upper()} | Leverage: {leverage:.0f}x\n"
        f"_Awaiting real-time price data..._\n\n"
        f"At +10% move: ${10_000 * leverage * 1.1:+,.2f}\n"
        f"At -10% move: ${-10_000 * leverage * 1.1:+,.2f}\n"
        f"At -30% SL: ${-10_000 * leverage * 0.3:+,.2f}"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_high_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable max leverage mode with liquidation warning."""
    await _run_in_thread(db_utils.set_config, 'max_leverage', '200')
    
    msg = (
        "🔥 **MAX LEVERAGE MODE ENABLED**\n\n"
        "⚠️ **LIQUIDATION RISK EXTREME**\n"
        f"Max: 200x | Min margin: 0.5%\n"
        f"A 0.5% adverse move = total loss\n\n"
        "You are responsible for all losses."
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    logger.warning("High leverage mode enabled")


async def cmd_withdraw_profits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending profits for 60% withdrawal to external wallet."""
    pending_profits = await _run_in_thread(db_utils.get_unwithdrawn_profits)
    withdrawal_amount = pending_profits * 0.60  # 60% to external wallet
    
    if withdrawal_amount < 10:
        msg = f"💰 Pending profit withdrawal: ${withdrawal_amount:.2f} (threshold: $10 minimum)"
        await update.message.reply_text(msg)
        return
    
    msg = (
        f"💸 **Profit Withdrawal Ready**\n\n"
        f"Gross Profits: ${pending_profits:.2f}\n"
        f"To External Wallet (60%): ${withdrawal_amount:.2f}\n"
        f"Reinvested (40%): ${pending_profits * 0.4:.2f}\n\n"
        f"⚠️ Manually transfer from Bybit to your wallet:\n"
        f"Send ${withdrawal_amount:.2f} USDT to your address\n"
        f"(Feature coming: Auto-transfer via API)"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    logger.info(f"Profit withdrawal requested: ${withdrawal_amount:.2f}")


async def cmd_setbybit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set Bybit API key and secret via Telegram (OWNER only). Usage: /setbybit <api_key> <api_secret>"""
    user_id = update.effective_user.id
    owner = os.getenv('OWNER_TELEGRAM_ID')
    try:
        owner_id = int(owner) if owner else None
    except Exception:
        owner_id = None

    if owner_id is None or user_id != owner_id:
        await update.message.reply_text("❌ Unauthorized. Only the bot owner can set API keys.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /setbybit <API_KEY> <API_SECRET>")
        return

    api_key = context.args[0].strip()
    api_secret = context.args[1].strip()

    # Persist to .env
    dotenv_path = os.path.join(os.getcwd(), '.env')
    try:
        dotenv.set_key(dotenv_path, 'BYBIT_API_KEY', api_key)
        dotenv.set_key(dotenv_path, 'BYBIT_API_SECRET', api_secret)
        # Update process env
        os.environ['BYBIT_API_KEY'] = api_key
        os.environ['BYBIT_API_SECRET'] = api_secret
        await update.message.reply_text("✅ Bybit API keys saved to .env. Please restart the bot to apply changes.")
        logger.info("Bybit API keys updated via Telegram by owner")
    except Exception as e:
        logger.error(f"Failed to save Bybit keys: {e}")
        await update.message.reply_text(f"❌ Failed to save keys: {e}")


async def cmd_setgemini(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set Gemini API key via Telegram (OWNER only). Usage: /setgemini <api_key>"""
    user_id = update.effective_user.id
    owner = os.getenv('OWNER_TELEGRAM_ID')
    try:
        owner_id = int(owner) if owner else None
    except Exception:
        owner_id = None

    if owner_id is None or user_id != owner_id:
        await update.message.reply_text("❌ Unauthorized. Only the bot owner can set API keys.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /setgemini <API_KEY>")
        return

    api_key = context.args[0].strip()
    dotenv_path = os.path.join(os.getcwd(), '.env')
    try:
        dotenv.set_key(dotenv_path, 'GEMINI_API_KEY', api_key)
        os.environ['GEMINI_API_KEY'] = api_key
        await update.message.reply_text("✅ Gemini API key saved to .env. Restart or re-init to apply.")
        logger.info("Gemini API key updated via Telegram by owner")
    except Exception as e:
        logger.error(f"Failed to save Gemini key: {e}")
        await update.message.reply_text(f"❌ Failed to save Gemini key: {e}")


async def cmd_setgroq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set Groq API key via Telegram (OWNER only). Usage: /setgroq <api_key>"""
    user_id = update.effective_user.id
    owner = os.getenv('OWNER_TELEGRAM_ID')
    try:
        owner_id = int(owner) if owner else None
    except Exception:
        owner_id = None

    if owner_id is None or user_id != owner_id:
        await update.message.reply_text("❌ Unauthorized. Only the bot owner can set API keys.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /setgroq <API_KEY>")
        return

    api_key = context.args[0].strip()
    dotenv_path = os.path.join(os.getcwd(), '.env')
    try:
        dotenv.set_key(dotenv_path, 'GROQ_API_KEY', api_key)
        os.environ['GROQ_API_KEY'] = api_key
        await update.message.reply_text("✅ Groq API key saved to .env. Restart or re-init to apply.")
        logger.info("Groq API key updated via Telegram by owner")
    except Exception as e:
        logger.error(f"Failed to save Groq key: {e}")
        await update.message.reply_text(f"❌ Failed to save Groq key: {e}")


async def cmd_setcoingecko(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set CoinGecko API URL via Telegram (OWNER only). Usage: /setcoingecko <api_url>"""
    user_id = update.effective_user.id
    owner = os.getenv('OWNER_TELEGRAM_ID')
    try:
        owner_id = int(owner) if owner else None
    except Exception:
        owner_id = None

    if owner_id is None or user_id != owner_id:
        await update.message.reply_text("❌ Unauthorized. Only the bot owner can set this.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /setcoingecko <API_URL>")
        return

    api_url = context.args[0].strip()
    dotenv_path = os.path.join(os.getcwd(), '.env')
    try:
        dotenv.set_key(dotenv_path, 'COINGECKO_API_URL', api_url)
        os.environ['COINGECKO_API_URL'] = api_url
        await update.message.reply_text("✅ CoinGecko API URL saved to .env. Restart or re-init to apply.")
        logger.info("CoinGecko API URL updated via Telegram by owner")
    except Exception as e:
        logger.error(f"Failed to save CoinGecko URL: {e}")
        await update.message.reply_text(f"❌ Failed to save CoinGecko URL: {e}")


async def cmd_reinit_trader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Owner-only: Re-initialize the Bybit trader in-process so new keys apply without restart."""
    user_id = update.effective_user.id
    owner = os.getenv('OWNER_TELEGRAM_ID')
    try:
        owner_id = int(owner) if owner else None
    except Exception:
        owner_id = None

    if owner_id is None or user_id != owner_id:
        await update.message.reply_text("❌ Unauthorized. Only the bot owner can run this.")
        return

    # Expect commands.BOT_INSTANCE to be injected by main
    bot_instance = globals().get('BOT_INSTANCE')
    if not bot_instance:
        await update.message.reply_text("❌ Bot instance not available in this process.")
        return

    await update.message.reply_text("🔄 Re-initializing Bybit trader... Please wait.")
    try:
        success = await bot_instance.reinit_trader()
        if success:
            await update.message.reply_text("✅ Bybit trader re-initialized successfully.")
        else:
            await update.message.reply_text("❌ Re-init failed; check logs for details.")
    except Exception as e:
        logger.error(f"Re-init error: {e}")
        await update.message.reply_text(f"❌ Re-init raised exception: {e}")

# Callback handlers
async def button_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume callback."""
    query = update.callback_query
    await query.answer()
    await cmd_resume(query, context)


async def button_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pause callback."""
    query = update.callback_query
    await query.answer()
    await cmd_pause(query, context)


async def button_confirm_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm kill callback."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔴 Initiating shutdown sequence...\n_Bot will close all positions and stop._")
    context.application.stop()


async def button_cancel_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel kill callback."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Kill cancelled.")
