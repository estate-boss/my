"""
Risk management: circuit breakers, loss tracking, balance protection, dynamic sizing.
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

WAT = pytz.timezone('Africa/Lagos')


class RiskManager:
    """
    Manages trading risk: symbols paused due to swings, balance protection,
    consecutive loss tracking, and dynamic position sizing.
    """
    
    def __init__(self):
        self.paused_symbols: dict[str, Tuple[datetime, str]] = {}  # symbol -> (pause_time, reason)
        self.daily_loss_percent = 0.0
        self.session_loss_percent = 0.0
    
    def check_swing_breaker(
        self, symbol: str, open_price: float, high: float, low: float,
        threshold_percent: float = 12.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if 1h swing exceeded threshold.
        Returns: (is_breaker_hit, reason)
        """
        h_swing = ((high - low) / open_price) * 100 if open_price > 0 else 0
        
        if h_swing > threshold_percent:
            reason = f"{h_swing:.1f}% 1h swing > {threshold_percent}%"
            logger.warning(f"⚠️ Breaker {symbol}: {reason}")
            self.pause_symbol(symbol, reason, hours=1)
            return True, reason
        
        return False, None
    
    def check_flash_crash(
        self, symbol: str, previous_price: float, current_price: float,
        threshold_percent: float = 8.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect rapid price drop (flash crash).
        Returns: (is_crashed, reason)
        """
        if previous_price <= 0:
            return False, None
        
        drop = ((previous_price - current_price) / previous_price) * 100
        
        if drop > threshold_percent:
            reason = f"{drop:.1f}% flash drop > {threshold_percent}%"
            logger.warning(f"🚨 Flash crash {symbol}: {reason}")
            self.pause_symbol(symbol, reason, hours=30)  # Long pause
            return True, reason
        
        return False, None
    
    def pause_symbol(
        self, symbol: str, reason: str, hours: float = 1.0
    ) -> None:
        """Pause trading on a symbol for N hours."""
        pause_until = datetime.now(WAT).timestamp() + (hours * 3600)
        self.paused_symbols[symbol] = (pause_until, reason)
        logger.warning(f"⏸️ Paused {symbol}: {reason} ({hours}h)")
    
    def is_symbol_paused(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """Check if symbol is currently paused. Returns (is_paused, reason)."""
        if symbol not in self.paused_symbols:
            return False, None
        
        pause_until, reason = self.paused_symbols[symbol]
        now = datetime.now(WAT).timestamp()
        
        if now < pause_until:
            hrs_left = (pause_until - now) / 3600
            return True, f"{reason} ({hrs_left:.1f}h left)"
        else:
            del self.paused_symbols[symbol]
            return False, None
    
    def check_balance_protection(
        self, current_balance: float, starting_balance: float,
        min_balance: float, daily_drawdown_limit: float = 20.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check balance against minimum and daily drawdown.
        Returns: (is_violated, reason)
        """
        # Check absolute minimum
        if current_balance < min_balance:
            reason = f"Balance ${current_balance:.2f} < min ${min_balance:.2f}"
            logger.error(f"🚨 Balance protection: {reason}")
            return True, reason
        
        # Check daily drawdown
        if starting_balance > 0:
            daily_loss = ((starting_balance - current_balance) / starting_balance) * 100
            if daily_loss > daily_drawdown_limit:
                reason = f"Daily drawdown {daily_loss:.1f}% > {daily_drawdown_limit}%"
                logger.error(f"🚨 Drawdown alert: {reason}")
                return True, reason
        
        self.daily_loss_percent = max(0, ((starting_balance - current_balance) / starting_balance) * 100)
        return False, None
    
    def calculate_position_size(
        self,
        account_balance: float,
        base_percent: float = 2.0,
        confidence_level: str = 'medium',
        volatility_factor: float = 1.0,
        recent_loss_streak: int = 0
    ) -> float:
        """
        Calculate dynamic position size based on confidence, volatility, and loss streak.
        REDUCED defaults for main coins + volatility accommodation.
        
        Args:
            account_balance: Current account balance in USDT
            base_percent: Base position size % (reduced to 2% for safety, was 3%)
            confidence_level: 'high', 'medium', 'low'
            volatility_factor: 1.0 (normal) to 0.5 (high volatility = reduce)
            recent_loss_streak: Count of recent losses
        
        Returns:
            Position size in USDT
        """
        # Confidence multiplier (reduced)
        conf_mult = {
            'high': 1.1,    # was 1.2
            'medium': 1.0,
            'low': 0.7      # was 0.6
        }.get(confidence_level, 1.0)
        
        # Loss streak multiplier (reduce after losses, more aggressive reduction)
        loss_mult = max(0.2, 1.0 - (recent_loss_streak * 0.33))
        
        # Volatility reduces size more aggressively
        size_percent = base_percent * conf_mult * volatility_factor * loss_mult
        size_usdt = (account_balance * size_percent) / 100
        
        logger.info(
            f"Position size: {size_usdt:.2f} USDT ({size_percent:.2f}%) "
            f"[base {base_percent}% × conf {conf_mult} × vol {volatility_factor} × loss {loss_mult:.2f}]"
        )
        return size_usdt
    
    def validate_leverage(
        self, requested_leverage: float, max_leverage: float
    ) -> float:
        """
        Ensure leverage doesn't exceed symbol max and applies sensible caps.
        Returns: Safe leverage to use.
        """
        # Cap at 95% of max to avoid liquidation at extreme prices
        safe_leverage = min(requested_leverage, max_leverage * 0.95)
        
        if safe_leverage < requested_leverage:
            logger.warning(
                f"Leverage capped: {requested_leverage}x → {safe_leverage:.1f}x "
                f"(symbol max {max_leverage:.0f}x)"
            )
        
        return max(1.0, safe_leverage)  # Never go below 1x
    
    def estimate_liquidation_price(
        self,
        entry_price: float,
        leverage: float,
        side: str,
        maintenance_margin: float = 0.005
    ) -> float:
        """
        Rough estimate of liquidation price (maintenance margin ~0.5% on Bybit).
        side: 'long' or 'short'
        """
        if side.lower() == 'long':
            liquidation = entry_price * (1 - (1 / leverage) + maintenance_margin)
        else:  # short
            liquidation = entry_price * (1 + (1 / leverage) - maintenance_margin)
        
        return max(0, liquidation)
