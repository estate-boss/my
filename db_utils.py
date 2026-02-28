"""
Database utilities for trade tracking, configs, watchlist, and streak management.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / 'trading_bot.db'


def init_database() -> None:
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Trades table
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            leverage REAL NOT NULL,
            quantity REAL NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            exit_time TIMESTAMP,
            pnl REAL,
            pnl_percent REAL,
            fee REAL,
            status TEXT DEFAULT 'open',
            ai_decision_gemini TEXT,
            ai_decision_groq TEXT,
            ai_confidence TEXT,
            target_tp_percent REAL,
            stop_loss_percent REAL,
            reason TEXT,
            duration_minutes INTEGER
        )
    ''')
    
    # Configs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Watchlist table
    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Streak table (loss tracking)
    c.execute('''
        CREATE TABLE IF NOT EXISTS streak (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loss_count INTEGER DEFAULT 0,
            last_loss_time TIMESTAMP,
            paused BOOLEAN DEFAULT 0,
            pause_reason TEXT,
            paused_at TIMESTAMP
        )
    ''')
    
    # Profits tracking (for 60% withdrawal feature)
    c.execute('''
        CREATE TABLE IF NOT EXISTS profits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            closed_trade_id INTEGER,
            profit_usd REAL NOT NULL,
            withdrawal_percent REAL DEFAULT 0.6,
            withdrawn_amount REAL DEFAULT 0,
            withdrawn_at TIMESTAMP,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def get_config(key: str, default: str = '') -> str:
    """Retrieve config value from database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT value FROM configs WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default


def set_config(key: str, value: str) -> None:
    """Store config value in database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO configs (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
        (key, value)
    )
    conn.commit()
    conn.close()
    logger.info(f"Config set: {key} = {value}")


def add_trade(
    symbol: str, side: str, entry_price: float, leverage: float,
    quantity: float, ai_gemini: str = '', ai_groq: str = '',
    confidence: str = '', tp: float = 0, sl: float = 0, reason: str = ''
) -> int:
    """Log trade entry to database. Returns trade ID."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (
            symbol, side, entry_price, leverage, quantity, entry_time,
            ai_decision_gemini, ai_decision_groq, ai_confidence,
            target_tp_percent, stop_loss_percent, reason, status
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, 'open')
    ''', (symbol, side, entry_price, leverage, quantity, ai_gemini, ai_groq, confidence, tp, sl, reason))
    trade_id = c.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Trade added: ID={trade_id} {symbol} {side} @ {entry_price}")
    return trade_id


def close_trade(
    trade_id: int, exit_price: float, pnl: float, pnl_percent: float, fee: float = 0
) -> None:
    """Close a trade and record P&L."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        UPDATE trades
        SET exit_price = ?, exit_time = CURRENT_TIMESTAMP, pnl = ?, pnl_percent = ?, fee = ?, status = 'closed'
        WHERE id = ?
    ''', (exit_price, pnl, pnl_percent, fee, trade_id))
    conn.commit()
    conn.close()
    logger.info(f"Trade closed: ID={trade_id} P&L={pnl_percent:.2f}%")


def get_open_trades() -> List[Dict]:
    """Retrieve all open trades."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM trades WHERE status = "open"')
    trades = [dict(row) for row in c.fetchall()]
    conn.close()
    return trades


def get_trade_history(limit: int = 50) -> List[Dict]:
    """Get recent closed trades."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM trades WHERE status = "closed" ORDER BY exit_time DESC LIMIT ?', (limit,))
    trades = [dict(row) for row in c.fetchall()]
    conn.close()
    return trades


def add_watchlist(symbol: str) -> None:
    """Add symbol to watchlist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)', (symbol,))
    conn.commit()
    conn.close()
    logger.info(f"Added to watchlist: {symbol}")


def remove_watchlist(symbol: str) -> None:
    """Remove symbol from watchlist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()
    logger.info(f"Removed from watchlist: {symbol}")


def get_watchlist() -> List[str]:
    """Get all watched symbols."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT symbol FROM watchlist ORDER BY added_at DESC')
    symbols = [row[0] for row in c.fetchall()]
    conn.close()
    return symbols


def get_loss_streak() -> Tuple[int, bool, str]:
    """Get current loss streak count and pause status. Returns (count, is_paused, reason)."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT loss_count, paused, pause_reason FROM streak LIMIT 1')
    result = c.fetchone()
    conn.close()
    if result:
        return result[0], bool(result[1]), result[2] or ''
    return 0, False, ''


def increment_loss_streak() -> int:
    """Increment loss streak count. Returns new count."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT loss_count FROM streak LIMIT 1')
    result = c.fetchone()
    
    if result:
        new_count = result[0] + 1
        c.execute(
            'UPDATE streak SET loss_count = ?, last_loss_time = CURRENT_TIMESTAMP',
            (new_count,)
        )
    else:
        c.execute('INSERT INTO streak (loss_count, last_loss_time) VALUES (1, CURRENT_TIMESTAMP)')
        new_count = 1
    
    conn.commit()
    conn.close()
    logger.warning(f"Loss streak incremented to {new_count}")
    return new_count


def reset_loss_streak() -> None:
    """Reset loss streak to 0 after a winning trade."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('UPDATE streak SET loss_count = 0')
    conn.commit()
    conn.close()
    logger.info("Loss streak reset to 0")


def set_pause_state(is_paused: bool, reason: str = '') -> None:
    """Set bot pause state."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    if c.execute('SELECT id FROM streak LIMIT 1').fetchone():
        c.execute(
            'UPDATE streak SET paused = ?, pause_reason = ?, paused_at = CURRENT_TIMESTAMP',
            (1 if is_paused else 0, reason)
        )
    else:
        c.execute(
            'INSERT INTO streak (paused, pause_reason, paused_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (1 if is_paused else 0, reason)
        )
    conn.commit()
    conn.close()
    status = "paused" if is_paused else "resumed"
    logger.warning(f"Bot {status}: {reason}")


def track_profit(trade_id: int, profit_usd: float) -> None:
    """Track profitable trade for 60% withdrawal."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    if profit_usd > 0:
        c.execute(
            'INSERT INTO profits (closed_trade_id, profit_usd) VALUES (?, ?)',
            (trade_id, profit_usd)
        )
        conn.commit()
    conn.close()


def get_unwithdrawn_profits() -> float:
    """Get total profits not yet withdrawn."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        'SELECT SUM(profit_usd * withdrawal_percent) FROM profits WHERE withdrawn_at IS NULL'
    )
    result = c.fetchone()
    conn.close()
    return float(result[0] or 0.0)


def mark_profits_withdrawn(amount: float) -> None:
    """Mark profits as withdrawn (60% to wallet)."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    # Mark as withdrawn
    c.execute(
        'UPDATE profits SET withdrawn_amount = ?, withdrawn_at = CURRENT_TIMESTAMP '
        'WHERE withdrawn_at IS NULL AND withdrawn_amount = 0 LIMIT 1',
        (amount,)
    )
    conn.commit()
    conn.close()
    logger.info(f"Marked ${amount:.2f} as withdrawn to profit wallet")
