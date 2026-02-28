"""
Reporter module: Trade reports, summaries, P&L calculations, tax estimation.
"""
import logging
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional, Tuple
import requests
from db_utils import get_trade_history, get_config, set_config

logger = logging.getLogger(__name__)

WAT = pytz.timezone('Africa/Lagos')


class Reporter:
    """Generates detailed trade reports, P&L summaries, and tax estimates."""
    
    @staticmethod
    def format_trade_open_report(
        symbol: str, side: str, entry_price: float, leverage: float,
        position_size_usdt: float, reason: str, tp_percent: float,
        sl_percent: float, current_balance: float
    ) -> str:
        """Format opening trade Telegram report."""
        side_emoji = '🔵' if side == 'long' else '🔴'
        tp_str = f"+{tp_percent:.0f}%" if tp_percent > 0 else f"{tp_percent:.0f}%"
        sl_str = f"{sl_percent:.0f}%"
        
        report = (
            f"{side_emoji} **{side.upper()} {symbol}** Opened\n"
            f"Entry: ${entry_price:,.2f}\n"
            f"Leverage: {leverage:.0f}x\n"
            f"Position: {position_size_usdt:.2f} USDT (~{(position_size_usdt/current_balance)*100:.1f}%)\n"
            f"AI Reason: {reason}\n"
            f"TP: {tp_str} | SL: {sl_str}\n"
            f"Balance: ${current_balance:,.2f}"
        )
        return report
    
    @staticmethod
    def format_trade_close_report(
        symbol: str, side: str, entry_price: float, exit_price: float,
        pnl_usdt: float, pnl_percent: float, fees_usdt: float,
        leverage: float, duration_minutes: int, current_balance: float,
        win_streak: int, weekly_estimate: float
    ) -> str:
        """Format closing trade Telegram report."""
        pnl_emoji = '✅' if pnl_percent >= 0 else '❌'
        side_emoji = '🔵' if side == 'long' else '🔴'
        duration_str = f"{duration_minutes}m" if duration_minutes < 60 else f"{duration_minutes//60}h {duration_minutes%60}m"
        
        report = (
            f"{pnl_emoji} **{side.upper()} {symbol}** Closed\n"
            f"Entry: ${entry_price:,.2f} → Exit: ${exit_price:,.2f}\n"
            f"P&L: {pnl_percent:+.2f}% (${pnl_usdt:+,.2f})\n"
            f"Leverage: {leverage:.0f}x | Fees: ${fees_usdt:.2f}\n"
            f"Duration: {duration_str}\n"
            f"Win Streak: {win_streak} | Weekly Est: ${weekly_estimate:,.2f}\n"
            f"Balance: ${current_balance:,.2f}"
        )
        return report
    
    @staticmethod
    def calculate_daily_summary(
        trades: List[Dict], start_date: datetime
    ) -> Dict[str, any]:
        """Calculate daily P&L summary from closed trades."""
        daily_trades = [
            t for t in trades
            if t.get('exit_time') and
            datetime.fromisoformat(t['exit_time']).date() == start_date.date()
        ]
        
        total_pnl = sum(t.get('pnl', 0) for t in daily_trades)
        total_fees = sum(t.get('fee', 0) for t in daily_trades)
        win_count = len([t for t in daily_trades if t.get('pnl', 0) > 0])
        loss_count = len([t for t in daily_trades if t.get('pnl', 0) < 0])
        
        return {
            'date': start_date.strftime('%Y-%m-%d'),
            'count': len(daily_trades),
            'wins': win_count,
            'losses': loss_count,
            'win_rate': (win_count / len(daily_trades) * 100) if daily_trades else 0,
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'net_pnl': total_pnl - total_fees
        }
    
    @staticmethod
    def format_daily_report(summary: Dict) -> str:
        """Format daily summary for Telegram."""
        report = (
            f"📊 **Daily Report** - {summary['date']}\n"
            f"Trades: {summary['count']} (Win {summary['wins']} | Loss {summary['losses']})\n"
            f"Win Rate: {summary['win_rate']:.1f}%\n"
            f"P&L: ${summary['total_pnl']:+,.2f}\n"
            f"Fees: ${summary['total_fees']:.2f}\n"
            f"Net: ${summary['net_pnl']:+,.2f}"
        )
        return report
    
    @staticmethod
    def calculate_weekly_summary(trades: List[Dict]) -> Dict[str, any]:
        """Calculate weekly P&L summary."""
        now = datetime.now(WAT)
        week_ago = now - timedelta(days=7)
        
        weekly_trades = [
            t for t in trades
            if t.get('exit_time') and
            datetime.fromisoformat(t['exit_time']).replace(tzinfo=WAT) >= week_ago
        ]
        
        total_pnl = sum(t.get('pnl', 0) for t in weekly_trades)
        total_fees = sum(t.get('fee', 0) for t in weekly_trades)
        win_count = len([t for t in weekly_trades if t.get('pnl', 0) > 0])
        loss_count = len([t for t in weekly_trades if t.get('pnl', 0) < 0])
        
        return {
            'period': f"{week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            'count': len(weekly_trades),
            'wins': win_count,
            'losses': loss_count,
            'win_rate': (win_count / len(weekly_trades) * 100) if weekly_trades else 0,
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'net_pnl': total_pnl - total_fees
        }
    
    @staticmethod
    def format_weekly_report(summary: Dict) -> str:
        """Format weekly summary for Telegram."""
        report = (
            f"📈 **Weekly Report** - {summary['period']}\n"
            f"Trades: {summary['count']} (Win {summary['wins']} | Loss {summary['losses']})\n"
            f"Win Rate: {summary['win_rate']:.1f}%\n"
            f"P&L: ${summary['total_pnl']:+,.2f}\n"
            f"Fees: ${summary['total_fees']:.2f}\n"
            f"Net: ${summary['net_pnl']:+,.2f}"
        )
        return report
    
    @staticmethod
    def get_usd_to_ngn_rate() -> float:
        """Fetch current USD to NGN exchange rate."""
        try:
            resp = requests.get(
                'https://api.exchangerate-api.com/v4/latest/USD',
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get('rates', {}).get('NGN', 1650.0)
        except Exception as e:
            logger.warning(f"Exchange rate fetch failed: {e}")
        return 1650.0  # Fallback
    
    @staticmethod
    def estimate_tax_fifo(trades: List[Dict]) -> Tuple[float, float, str]:
        """
        Estimate Nigerian taxes on crypto gains using FIFO method.
        Returns: (tax_usd, tax_ngn, detailed_breakdown)
        
        Nigeria rules (simplified):
        - Capital gains tax: 10% for STT holdings (< 1 year) or deemed trading
        - No CGT for >1 year hold
        - Exemption: First ₦800,000 (~$500) per annum
        - Progressive rates apply to deemed income
        """
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        if not closed_trades:
            return 0.0, 0.0, "No closed trades"
        
        # Simple FIFO: sum realized gains
        total_gain_usd = sum(max(0, t.get('pnl', 0)) for t in closed_trades)
        
        # Tax at 10% CGT
        taxable_usd = max(0, total_gain_usd - 500)  # Exemption
        tax_usd = taxable_usd * 0.10
        
        rate = Reporter.get_usd_to_ngn_rate()
        tax_ngn = tax_usd * rate
        
        breakdown = (
            f"FIFO Gains (USD): ${total_gain_usd:,.2f}\n"
            f"Exemption: $500\n"
            f"Taxable: ${taxable_usd:,.2f}\n"
            f"Tax Rate: 10%\n"
            f"Tax Due (USD): ${tax_usd:,.2f}\n"
            f"Tax Due (NGN): ₦{tax_ngn:,.0f}\n"
            f"Note: Consult tax professional. Rates approximate."
        )
        
        return tax_usd, tax_ngn, breakdown
    
    @staticmethod
    def format_tax_report(tax_usd: float, tax_ngn: float, breakdown: str) -> str:
        """Format tax estimate for Telegram."""
        return (
            f"💰 **Tax Estimate** (FIFO, Nigeria)\n"
            f"{breakdown}"
        )
    
    @staticmethod
    def format_status_report(
        current_balance: float, starting_balance: float,
        open_positions: int, total_trades: int, win_rate: float,
        is_paused: bool, pause_reason: str = ''
    ) -> str:
        """Format bot status for Telegram."""
        return_pct = ((current_balance - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0
        pause_status = f"🔘 PAUSED: {pause_reason}" if is_paused else "🟢 RUNNING"
        
        report = (
            f"📱 **Bot Status**\n"
            f"{pause_status}\n"
            f"Balance: ${current_balance:,.2f}\n"
            f"Return: {return_pct:+.2f}%\n"
            f"Open: {open_positions} pos | Total: {total_trades} trades\n"
            f"Win Rate: {win_rate:.1f}%"
        )
        return report
