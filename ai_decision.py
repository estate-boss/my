"""
AI decision module: Gemini + Groq with CoinGecko news weighting.
"""
import os
import logging
import asyncio
import json
import re
from typing import Tuple, Optional, Dict, Any
import aiohttp
import google.generativeai as genai
from groq import AsyncGroq

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')

genai.configure(api_key=GEMINI_API_KEY)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)


async def fetch_crypto_news(symbol_base: str, limit: int = 5) -> str:
    """
    Fetch recent project status updates from CoinGecko for a symbol.
    symbol_base: e.g., 'BTC' from 'BTCUSDT'
    Returns: Summarized news string.
    """
    try:
        # Map symbol to CoinGecko coin id
        async with aiohttp.ClientSession() as session:
            list_url = f"{COINGECKO_API_URL}/coins/list"
            async with session.get(list_url, timeout=10) as r:
                if r.status != 200:
                    return "News unavailable (CoinGecko list fetch failed)"
                coins = await r.json()

            symbol_lower = symbol_base.lower()
            coin_id = None
            for c in coins:
                if c.get('symbol', '').lower() == symbol_lower:
                    coin_id = c.get('id')
                    break

            if not coin_id:
                return "No news found (coin id not mapped)"

            updates_url = f"{COINGECKO_API_URL}/coins/{coin_id}/status_updates"
            async with session.get(updates_url, timeout=10) as ur:
                if ur.status != 200:
                    return "No news found (status updates unavailable)"
                data = await ur.json()

            updates = data.get('status_updates', [])[:limit]
            summaries = []
            for u in updates:
                title = u.get('title') or u.get('description', '')[:120]
                category = u.get('category') or u.get('user', {}).get('name', 'CoinGecko')
                created = u.get('created_at', '')
                summaries.append(f"[{category}] {title} ({created})")

            if not summaries:
                return "No recent project updates"

            return '\n'.join(summaries)
    except Exception as e:
        logger.warning(f"CoinGecko news fetch failed for {symbol_base}: {e}")
        return f"News fetch error: {str(e)[:50]}"


async def get_ai_decision(
    symbol: str,
    current_price: float,
    change_24h: float,
    volume_24h: float,
    volatility_atr: float,
    min_confidence: str = 'medium'
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float], Optional[float], Optional[float]]:
    """
    Get aggressive trade decision from both Gemini and Groq.
    Returns: (decision, confidence, reason, suggested_leverage, tp_percent, sl_percent)
    Both must agree and meet confidence threshold.
    """
    symbol_base = symbol.replace('USDT', '').replace('BUSD', '')
    news = await fetch_crypto_news(symbol_base)
    
    prompt = f"""You are a RUTHLESS profit-maximizing trader operating on extreme leverage (50x-100x+).
    
Symbol: {symbol}
Current Price: ${current_price:.2f}
24h Change: {change_24h:+.2f}%
24h Volume: ${volume_24h:,.0f}
Volatility (ATR): {volatility_atr:.4f}

Recent News (HEAVILY WEIGHT THIS FOR DIRECTIONAL BIAS):
{news}

DECISION RULES:
1. Massively weight NEWS for directional bias (news breakouts = high confidence long/short)
2. If 24h change >5% + positive news → LONG with HIGH confidence
3. If 24h change <-5% + negative news → SHORT with HIGH confidence  
4. High volatility + news → consider max leverage
5. Low volume → reduce confidence to MEDIUM/LOW
6. No clear signal → NO_TRADE

RESPOND EXACTLY WITH:
DECISION: long/short/no_trade
CONFIDENCE: high/medium/low
REASON: [one line - news impact + price action]
SUGGESTED_LEVERAGE: [80-100 for majors, up to 200 for high-vol alts, or 1 for no_trade]
TARGET_TP_PCT: [{change_24h*2:.0f} to {min(100, change_24h*3):.0f}] (be aggressive: 40-100+%)
STOP_LOSS_PCT: [-15 to -30]"""

    try:
        # Gemini decision
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_response = await asyncio.to_thread(
            gemini_model.generate_content, prompt
        )
        gemini_text = gemini_response.text.strip()
        logger.info(f"Gemini decision ({symbol}): {gemini_text[:100]}...")
        
        # Groq decision (parallel)
        groq_response = await groq_client.chat.completions.create(
            model='mixtral-8x7b-32768',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=300,
            temperature=0.7
        )
        groq_text = groq_response.choices[0].message.content.strip()
        logger.info(f"Groq decision ({symbol}): {groq_text[:100]}...")
        
        # Parse both responses
        gemini_parsed = _parse_ai_response(gemini_text)
        groq_parsed = _parse_ai_response(groq_text)
        
        # Require agreement on decision (or one says no_trade)
        gemini_dec = gemini_parsed.get('decision', 'no_trade')
        groq_dec = groq_parsed.get('decision', 'no_trade')
        
        if gemini_dec != groq_dec and gemini_dec != 'no_trade' and groq_dec != 'no_trade':
            logger.warning(f"{symbol}: AI disagreement - Gemini {gemini_dec} vs Groq {groq_dec}. SKIP")
            return None, None, None, None, None, None
        
        # Use Groq if agreement, else use Gemini
        decision_data = groq_parsed if groq_dec == gemini_dec else gemini_parsed
        
        decision = decision_data.get('decision', 'no_trade')
        confidence = decision_data.get('confidence', 'low')
        leverage = decision_data.get('leverage', 1.0)
        tp = decision_data.get('tp', 50.0)
        sl = decision_data.get('sl', -20.0)
        reason = decision_data.get('reason', 'AI decision')
        
        # Enforce minimum confidence
        conf_levels = {'high': 3, 'medium': 2, 'low': 1}
        min_conf_level = conf_levels.get(min_confidence, 2)
        actual_conf_level = conf_levels.get(confidence, 1)
        
        if decision != 'no_trade' and actual_conf_level < min_conf_level:
            logger.info(f"{symbol}: Confidence {confidence} below threshold {min_confidence}. SKIP")
            return None, None, None, None, None, None
        
        return decision, confidence, reason, leverage, tp, sl
    
    except Exception as e:
        logger.error(f"AI decision error for {symbol}: {e}")
        return None, None, None, None, None, None


def _parse_ai_response(text: str) -> Dict[str, Any]:
    """Parse AI response into structured decision data."""
    data = {
        'decision': 'no_trade',
        'confidence': 'low',
        'leverage': 1.0,
        'tp': 50.0,
        'sl': -20.0,
        'reason': 'Parsing error'
    }
    
    try:
        # Extract DECISION
        decision_match = re.search(r'DECISION:\s*(long|short|no_trade)', text, re.IGNORECASE)
        if decision_match:
            data['decision'] = decision_match.group(1).lower()
        
        # Extract CONFIDENCE
        conf_match = re.search(r'CONFIDENCE:\s*(high|medium|low)', text, re.IGNORECASE)
        if conf_match:
            data['confidence'] = conf_match.group(1).lower()
        
        # Extract SUGGESTED_LEVERAGE
        lev_match = re.search(r'SUGGESTED_LEVERAGE:\s*([\d.]+)', text)
        if lev_match:
            data['leverage'] = float(lev_match.group(1))
        
        # Extract TARGET_TP_PCT
        tp_match = re.search(r'TARGET_TP_PCT:\s*\[?([0-9.]+)', text)
        if tp_match:
            data['tp'] = float(tp_match.group(1))
        
        # Extract STOP_LOSS_PCT
        sl_match = re.search(r'STOP_LOSS_PCT:\s*\[?(-?[0-9.]+)', text)
        if sl_match:
            data['sl'] = float(sl_match.group(1))
        
        # Extract REASON
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', text)
        if reason_match:
            data['reason'] = reason_match.group(1).strip()[:100]
    
    except Exception as e:
        logger.error(f"Parse error: {e}")
    
    return data


async def fallback_decision(
    symbol: str,
    change_24h: float,
    volume_24h: float
) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    """
    Fallback decision if AI fails: simple rule-based logic.
    Returns: (decision, confidence, leverage)
    """
    min_volume = 10_000_000  # $10M minimum
    
    if volume_24h < min_volume:
        logger.warning(f"{symbol}: Low volume ({volume_24h:,.0f}). SKIP")
        return None, 'low', None
    
    if change_24h > 5:
        logger.info(f"{symbol}: Fallback LONG (24h change {change_24h:.2f}%)")
        return 'long', 'medium', 50.0
    elif change_24h < -5:
        logger.info(f"{symbol}: Fallback SHORT (24h change {change_24h:.2f}%)")
        return 'short', 'medium', 50.0
    
    logger.info(f"{symbol}: Fallback NO_TRADE (change {change_24h:.2f}%, volume ok)")
    return None, 'low', None
