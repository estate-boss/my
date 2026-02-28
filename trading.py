"""
Trading module: Order execution, position management on Bybit.
"""
import logging
from typing import Dict, Optional, List, Tuple
import ccxt.async_support as ccxt
from decimal import Decimal

logger = logging.getLogger(__name__)


class BybitTrader:
    """
    Handles all trading operations on Bybit futures.
    """
    
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool = False):
        """
        Initialize Bybit exchange connector.
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            paper_mode: If True, simulate orders without actual execution
        """
        self.paper_mode = paper_mode
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {
                'defaultType': 'future',
                'defaultNetwork': 'Bybit',
                'enableRateLimit': True
            }
        })
        self.open_orders: Dict[str, Dict] = {}  # symbol -> order data
    
    async def init_markets(self) -> bool:
        """Load market data to get max leverage and fee info."""
        try:
            await self.exchange.load_markets()
            logger.info("Markets loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            return False
    
    async def get_max_leverage(self, symbol: str) -> float:
        """
        Fetch maximum allowed leverage for a symbol.
        """
        try:
            if symbol not in self.exchange.symbols:
                logger.warning(f"Symbol {symbol} not found in market data")
                return 10.0  # Safe fallback
            
            market = self.exchange.markets.get(symbol, {})
            max_lev = market.get('limits', {}).get('leverage', {}).get('max', 10.0)
            logger.info(f"{symbol}: Max leverage {max_lev:.0f}x")
            return float(max_lev)
        except Exception as e:
            logger.warning(f"Leverage fetch failed for {symbol}: {e}")
            return 10.0
    
    async def get_balance(self) -> float:
        """Fetch current USDT balance."""
        try:
            balance = await self.exchange.fetch_balance(params={'type': 'future'})
            usdt = balance.get('USDT', {}).get('free', 0.0)
            logger.info(f"Balance: ${usdt:,.2f}")
            return float(usdt)
        except Exception as e:
            logger.error(f"Balance fetch failed: {e}")
            return 0.0
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch current ticker for symbol."""
        try:
            if not self.paper_mode:
                ticker = await self.exchange.fetch_ticker(symbol)
                return {
                    'symbol': symbol,
                    'last': ticker['last'],
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'high': ticker.get('high', ticker['last']),
                    'low': ticker.get('low', ticker['last']),
                    'volume': ticker.get('quoteVolume', 0),
                    'timestamp': ticker['timestamp']
                }
        except Exception as e:
            logger.error(f"Ticker fetch failed for {symbol}: {e}")
        
        return None
    
    async def get_ohlcv(
        self, symbol: str, timeframe: str = '1h', limit: int = 20
    ) -> List[List]:
        """
        Fetch OHLCV candles for volatility/swing analysis.
        """
        try:
            if not self.paper_mode:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                return ohlcv
        except Exception as e:
            logger.error(f"OHLCV fetch failed for {symbol}@{timeframe}: {e}")
        
        return []
    
    async def open_position(
        self, symbol: str, side: str, quantity: float, leverage: float,
        tp_percent: Optional[float] = None, sl_percent: Optional[float] = None
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Open a long/short leveraged position.
        
        Args:
            symbol: e.g., 'BTCUSDT'
            side: 'long' or 'short'
            quantity: Size in USDT
            leverage: Leverage multiplier (e.g., 50x)
            tp_percent: Take profit percent above entry
            sl_percent: Stop loss percent below entry (negative)
        
        Returns:
            (success, order_id, entry_price)
        """
        try:
            if self.paper_mode:
                ticker = await self.exchange.fetch_ticker(symbol)
                entry = ticker['last']
                order_id = f"PAPER_{symbol}_{int(entry)}"
                logger.info(f"PAPER: {side.upper()} {quantity:.2f} USDT @ {entry:.2f}x{leverage:.0f}x")
                self.open_orders[symbol] = {
                    'id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'entry': entry,
                    'quantity': quantity,
                    'leverage': leverage,
                    'tp': entry * (1 + tp_percent/100) if tp_percent else None,
                    'sl': entry * (1 + sl_percent/100) if sl_percent else None
                }
                return True, order_id, entry
            
            # Set leverage
            try:
                _params = {
                    'leverage': int(leverage),
                    'reduceOnly': False
                }
                await self.exchange.set_leverage(int(leverage), symbol, _params)
            except Exception as lev_error:
                logger.warning(f"Leverage set warning: {lev_error}")
            
            # Calculate amount from USDT quantity
            ticker = await self.exchange.fetch_ticker(symbol)
            amount = quantity / ticker['last']
            
            # Adjust side for CCXT
            ccxt_side = 'buy' if side == 'long' else 'sell'
            
            # Create market order
            order = await self.exchange.create_market_order(
                symbol, ccxt_side, amount,
                params={
                    'leverage': int(leverage),
                    'reduceOnly': False
                }
            )
            
            order_id = order['id']
            entry = ticker['last']
            
            logger.info(f"Position opened: {symbol} {side.upper()} "
                       f"qty {amount:.4f} @ {entry:.2f}x{leverage:.0f}x | Order {order_id}")
            
            self.open_orders[symbol] = {
                'id': order_id,
                'symbol': symbol,
                'side': side,
                'entry': entry,
                'quantity': amount,
                'leverage': leverage,
                'tp': entry * (1 + tp_percent/100) if tp_percent else None,
                'sl': entry * (1 + sl_percent/100) if sl_percent else None
            }
            
            return True, order_id, entry
        
        except Exception as e:
            logger.error(f"Open position failed for {symbol}: {e}")
            return False, None, None
    
    async def close_position(self, symbol: str) -> Tuple[bool, Optional[float], Optional[float]]:
        """
        Close open position on symbol.
        
        Returns:
            (success, exit_price, pnl_usdt)
        """
        try:
            if symbol not in self.open_orders:
                logger.warning(f"No open order for {symbol}")
                return False, None, None
            
            order = self.open_orders[symbol]
            
            if self.paper_mode:
                ticker = await self.exchange.fetch_ticker(symbol)
                exit_price = ticker['last']
                pnl = self._calculate_pnl(
                    order['side'], order['entry'], exit_price, order['quantity']
                )
                del self.open_orders[symbol]
                logger.info(f"PAPER: Closed {symbol} @ {exit_price:.2f} P&L ${pnl:.2f}")
                return True, exit_price, pnl
            
            # Fetch current position
            positions = await self.exchange.fetch_positions(symbols=[symbol])
            if not positions or positions[0]['contracts'] == 0:
                logger.warning(f"No active position for {symbol}")
                return False, None, None
            
            # Close position
            ticker = await self.exchange.fetch_ticker(symbol)
            exit_price = ticker['last']
            ccxt_side = 'sell' if order['side'] == 'long' else 'buy'
            amount = order['quantity']
            
            close_order = await self.exchange.create_market_order(
                symbol, ccxt_side, amount,
                params={'reduceOnly': True}
            )
            
            pnl = self._calculate_pnl(
                order['side'], order['entry'], exit_price, amount
            )
            
            del self.open_orders[symbol]
            logger.info(f"Position closed: {symbol} @ {exit_price:.2f} "
                       f"P&L ${pnl:.2f} | Order {close_order['id']}")
            
            return True, exit_price, pnl
        
        except Exception as e:
            logger.error(f"Close position failed for {symbol}: {e}")
            return False, None, None
    
    def _calculate_pnl(
        self, side: str, entry: float, exit: float, quantity: float
    ) -> float:
        """Calculate P&L in USDT."""
        if side.lower() == 'long':
            return quantity * (exit - entry)
        else:  # short
            return quantity * (entry - exit)
    
    async def get_open_positions(self) -> List[Dict]:
        """Fetch all open positions from Bybit."""
        try:
            if self.paper_mode:
                return [
                    {
                        'symbol': sym,
                        'side': order['side'],
                        'contracts': order['quantity'],
                        'contractSize': 1,
                        'percentage': 0,
                        'markPrice': order['entry'],
                        'liquidationPrice': order['entry'] * 0.8
                    }
                    for sym, order in self.open_orders.items()
                ]
            
            positions = await self.exchange.fetch_positions()
            open_pos = [p for p in positions if p.get('contracts', 0) > 0]
            return open_pos
        except Exception as e:
            logger.error(f"Fetch positions failed: {e}")
            return []
    
    async def close(self) -> None:
        """Close exchange connection."""
        await self.exchange.close()
        logger.info("Exchange connection closed")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            if self.paper_mode:
                logger.info(f"PAPER: Cancelled order {order_id} for {symbol}")
                return True
            
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {symbol} {order_id}")
            return True
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
