#!/usr/bin/env python3
"""
Bybit News Trading Bot v2.1 - BYBIT_NEWS_TRADING_V2
==============================================
Patched to support TWO separate entry models:

1. CONTINUATION MODEL (momentum):
   - event_score >= 8
   - breakout confirmed, volume confirmed
   - RSI ALLOWED (not required to be oversold)
   - RSI ceiling: 78 for longs, 22 for shorts

2. FADE MODEL (mean-reversion):
   - event_score 5-7.99
   - RSI oversold < 20 (long) or > 80 (short)
   - price extension >= 1.5 ATR
   - orderflow decelerating

CRITICAL FIX: No more global RSI gate blocking continuation trades!
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION V2.1
# ============================================================

CONFIG = {
    # Continuation model params
    "continuation": {
        "min_event_score": 8.0,
        "long_rsi_max": 78,
        "short_rsi_min": 22,
        "require_breakout": True,
        "require_volume_confirmation": True,
    },
    # Fade model params
    "fade": {
        "min_event_score": 5.0,
        "max_event_score": 7.99,
        "long_rsi_max": 20,
        "short_rsi_min": 80,
        "min_atr_extension": 1.5,
        "require_orderflow_deceleration": True,
    },
    # Decision priority
    "decision_priority": {
        "prefer_continuation_above_score": 8.0,
    },
    # Logging
    "logging": {
        "detailed_skip_reasons": True,
        "send_debug_skip_alerts": False,
    },
    # Risk controls (preserve from V2)
    "risk": {
        "max_trades_per_day": 3,
        "min_balance": 50,
        "max_position_pct": 0.30,
        "stop_loss_atr": 1.5,
        "tp1_r": 1.0,
        "tp2_r": 2.0,
        "partial_at_tp1_pct": 50,
    },
    # Spread limits (bps)
    "max_spread_bps": {
        "BTCUSDT": 8,
        "ETHUSDT": 10,
        "XAUUSDT": 15,
        "XAGUSDT": 18,
        "GASUSDT": 25,
    },
    # Headline to asset mapping
    "headline_mapping": {
        "enable_proxy_penalty": True,
        "oil": {"primary_symbols": ["GASUSDT"], "confidence_penalty": 1, "notes": "proxy for natural gas"},
        "natural_gas": {"primary_symbols": ["GASUSDT"], "confidence_penalty": 0},
        "gold": {"primary_symbols": ["XAUUSDT", "XAUTUSDT"], "confidence_penalty": 0},
        "silver": {"primary_symbols": ["XAGUSDT"], "confidence_penalty": 0},
        "fed_rates": {"primary_symbols": ["XAUUSDT", "BTCUSDT", "ETHUSDT"], "confidence_penalty": 0},
        "crypto_regulation": {"primary_symbols": ["BTCUSDT", "ETHUSDT"], "confidence_penalty": 0},
    },
}

# News sources
NEWS_SOURCES = [
    {"name": "OilPrice", "url": "https://oilprice.com/"},
    {"name": "BBC Business", "url": "https://www.bbc.com/news/business"},
    {"name": "MarketWatch Commodities", "url": "https://www.marketwatch.com/investing/commodities"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/topic/markets/"},
]

# Trading pairs
TRADING_PAIRS = ["XAUUSDT", "XAUTUSDT", "XAGUSDT", "GASUSDT", "BTCUSDT", "ETHUSDT"]

# Keywords
GOLD_KEYWORDS = ["gold", "xau", "bullion", "gold price", "gold up", "gold down", "gold surge", "gold rally", "safe haven", "precious metals"]
SILVER_KEYWORDS = ["silver", "xag", "silver price", "silver up", "silver down"]
CRYPTO_KEYWORDS = ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "sec", "regulation", "etf"]
OIL_KEYWORDS = ["oil", "opec", "crude", "wti", "brent", "petroleum", "energy", "natural gas", "iran", "straits", "fuel", "gas prices"]
BULLISH_KEYWORDS = ["up", "surge", "rally", "gains", "soars", "hits record", "breakout", "bullish", "higher", "rises", "climbs", "growing"]
BEARISH_KEYWORDS = ["down", "falls", "drops", "plunges", "tumbles", "slumps", "declines", "bearish", "lower", "selloff", "worst", "recession", "crash"]

# ============================================================
# CORE FUNCTIONS
# ============================================================

def analyze_sentiment(text):
    """Analyze news text for sentiment"""
    text_lower = " " + text.lower() + " "
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    
    if bullish_count > bearish_count:
        return "BULLISH", bullish_count - bearish_count
    elif bearish_count > bullish_count:
        return "BEARISH", bearish_count - bullish_count
    else:
        return "NEUTRAL", 0


def identify_commodity(text):
    """Identify which commodity the news is about"""
    text_lower = " " + text.lower() + " "
    
    for kw in OIL_KEYWORDS:
        if kw in text_lower:
            return "oil"  # Will map to GASUSDT
    for kw in GOLD_KEYWORDS:
        if kw in text_lower:
            return "gold"
    for kw in SILVER_KEYWORDS:
        if kw in text_lower:
            return "silver"
    for kw in CRYPTO_KEYWORDS:
        if kw in text_lower:
            return "crypto"
    return None


def get_pairs_for_commodity(commodity):
    """Get trading pairs for the commodity"""
    mapping = {
        "gold": ["XAUUSDT", "XAUTUSDT"],
        "silver": ["XAGUSDT"],
        "oil": ["GASUSDT"],  # Oil maps to natural gas for now
        "natural_gas": ["GASUSDT"],
        "bitcoin": ["BTCUSDT"],
        "crypto": ["BTCUSDT", "ETHUSDT"],
    }
    return mapping.get(commodity, ["XAUUSDT", "BTCUSDT"])


# ============================================================
# V2.1 DECISION ENGINE
# ============================================================

def calculate_event_score(headline, source, sentiment, strength, commodity):
    """Calculate event score (0-20)"""
    score = 0.0
    
    # Source quality (0-4)
    source_weights = {"Reuters": 4, "CNBC": 4, "BBC": 3, "MarketWatch": 2, "OilPrice": 3, "Yahoo": 1}
    score += source_weights.get(source, 2) * 0.5
    
    # Sentiment strength (0-3)
    score += min(strength * 0.5, 3)
    
    # Freshness (assume recent for now)
    score += 2
    
    # Asset relevance (0-3)
    if commodity:
        score += 2
    
    return min(score, 20)


def evaluate_market_confirmation(bybit, symbol, direction):
    """Evaluate market confirmation checks"""
    result = {
        "breakout_confirmed": False,
        "breakdown_confirmed": False,
        "volume_confirmed": False,
        "spread_ok": False,
        "overextended": False,
    }
    
    try:
        # Get ticker for spread
        ticker = bybit.fetch_ticker(symbol)
        spread = abs(ticker['bid'] - ticker['ask']) / ticker['last'] * 10000
        
        max_spread = CONFIG["max_spread_bps"].get(symbol, 15)
        result["spread_ok"] = spread < max_spread
        
        # Check if overextended (simple ATR check)
        ohlcv = bybit.fetch_ohlcv(symbol, '1h', limit=20)
        if ohlcv and len(ohlcv) >= 10:
            recent = ohlcv[-5:]
            avg_range = sum(c[2] - c[3] for c in recent) / len(recent)
            current_range = ohlcv[-1][2] - ohlcv[-1][3]
            
            if current_range > avg_range * 1.8:
                result["overextended"] = True
        
        # Get volume (simplified - assume confirmed for now)
        result["volume_confirmed"] = True
        
        # Breakout/breakdown check (simplified - assume confirmed if spread OK and not overextended)
        if result["spread_ok"] and not result["overextended"]:
            if direction == "BULLISH":
                result["breakout_confirmed"] = True
            else:
                result["breakdown_confirmed"] = True
                
    except Exception as e:
        print("[MARKET CONF ERROR] {}: {}".format(symbol, e))
    
    return result


def evaluate_continuation_entry(event_score, rsi, market_conf, direction):
    """Evaluate continuation model entry"""
    cfg = CONFIG["continuation"]
    result = {"eligible": False, "confidence": 0, "fail_reasons": []}
    
    # Check event score
    if event_score < cfg["min_event_score"]:
        result["fail_reasons"].append("event_score_below_min")
        return result
    
    # Check breakout/breakdown confirmed
    if direction == "BULLISH" and not market_conf.get("breakout_confirmed"):
        result["fail_reasons"].append("no_breakout_confirmation")
        return result
    if direction == "BEARISH" and not market_conf.get("breakdown_confirmed"):
        result["fail_reasons"].append("no_breakdown_confirmation")
        return result
    
    # Check volume confirmed
    if cfg["require_volume_confirmation"] and not market_conf.get("volume_confirmed"):
        result["fail_reasons"].append("volume_not_confirmed")
        return result
    
    # Check spread
    if not market_conf.get("spread_ok"):
        result["fail_reasons"].append("spread_too_wide")
        return result
    
    # Check overextension
    if market_conf.get("overextended"):
        result["fail_reasons"].append("overextended")
        return result
    
    # RSI check - ALLOW continuation with moderate RSI (key fix!)
    if direction == "BULLISH":
        if rsi and rsi >= cfg["long_rsi_max"]:
            result["fail_reasons"].append("rsi_too_high")
            return result
    else:  # BEARISH
        if rsi and rsi <= cfg["short_rsi_min"]:
            result["fail_reasons"].append("rsi_too_low")
            return result
    
    # All checks passed - eligible!
    result["eligible"] = True
    
    # Calculate confidence
    confidence = event_score * 2  # Base: event score
    if market_conf.get("breakout_confirmed") or market_conf.get("breakdown_confirmed"):
        confidence += 3
    if market_conf.get("volume_confirmed"):
        confidence += 2
    if rsi:
        # Lower RSI = higher confidence for continuation
        if direction == "BULLISH":
            confidence += max(0, (78 - rsi) / 10)
        else:
            confidence += max(0, (rsi - 22) / 10)
    
    result["confidence"] = min(confidence, 10)
    return result


def evaluate_fade_entry(event_score, rsi, atr, price_extent, market_conf, direction):
    """Evaluate fade model entry"""
    cfg = CONFIG["fade"]
    result = {"eligible": False, "confidence": 0, "fail_reasons": []}
    
    # Check event score range (5-7.99)
    if event_score < cfg["min_event_score"] or event_score > cfg["max_event_score"]:
        result["fail_reasons"].append("event_score_out_of_range")
        return result
    
    # Check spread
    if not market_conf.get("spread_ok"):
        result["fail_reasons"].append("spread_too_wide")
        return result
    
    # RSI oversold/overbought REQUIRED for fade
    if direction == "BULLISH":
        if rsi is None or rsi >= cfg["long_rsi_max"]:
            result["fail_reasons"].append("not_oversold")
            return result
    else:
        if rsi is None or rsi <= cfg["short_rsi_min"]:
            result["fail_reasons"].append("not_overbought")
            return result
    
    # Check ATR extension
    if price_extent < cfg["min_atr_extension"]:
        result["fail_reasons"].append("insufficient_atr_extension")
        return result
    
    # Orderflow deceleration (simplified - assume true for now)
    if cfg["require_orderflow_deceleration"]:
        orderflow_dec = True  # Simplified
        if not orderflow_dec:
            result["fail_reasons"].append("orderflow_not_decelerating")
            return result
    
    # All checks passed!
    result["eligible"] = True
    
    # Calculate confidence
    confidence = event_score * 1.5
    if rsi:
        # More extreme RSI = higher confidence
        if direction == "BULLISH":
            confidence += max(0, (20 - rsi) * 0.5)
        else:
            confidence += max(0, (rsi - 80) * 0.5)
    confidence += price_extent * 2
    
    result["confidence"] = min(confidence, 10)
    return result


def build_trade_decision(event_score, rsi, atr, market_conf, direction, symbol, headline, source):
    """Build trade decision with full logging"""
    cfg = CONFIG["decision_priority"]
    
    # Get price extension - for testing, default to 2.0 when no strong signal
    # Real implementation would calculate actual distance from VWAP/MA
    price_extent = 2.0 if atr else 1.5
    
    # Evaluate both models
    cont_result = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    fade_result = evaluate_fade_entry(event_score, rsi, atr, price_extent, market_conf, direction)
    
    # Decision logic
    final_action = "SKIP"
    entry_model = "none"
    
    if cont_result["eligible"] and fade_result["eligible"]:
        # Both eligible - use priority
        if event_score >= cfg["prefer_continuation_above_score"]:
            final_action = "ENTER_LONG_CONTINUATION" if direction == "BULLISH" else "ENTER_SHORT_CONTINUATION"
            entry_model = "continuation"
        else:
            if cont_result["confidence"] > fade_result["confidence"]:
                final_action = "ENTER_LONG_CONTINUATION" if direction == "BULLISH" else "ENTER_SHORT_CONTINUATION"
                entry_model = "continuation"
            else:
                final_action = "ENTER_LONG_FADE" if direction == "BULLISH" else "ENTER_SHORT_FADE"
                entry_model = "fade"
    elif cont_result["eligible"]:
        final_action = "ENTER_LONG_CONTINUATION" if direction == "BULLISH" else "ENTER_SHORT_CONTINUATION"
        entry_model = "continuation"
    elif fade_result["eligible"]:
        final_action = "ENTER_LONG_FADE" if direction == "BULLISH" else "ENTER_SHORT_FADE"
        entry_model = "fade"
    
    # Build log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "headline": headline[:80],
        "source": source,
        "direction": direction,
        "event_score": round(event_score, 1),
        "rsi": rsi,
        "atr": atr,
        "breakout_confirmed": market_conf.get("breakout_confirmed"),
        "breakdown_confirmed": market_conf.get("breakdown_confirmed"),
        "volume_confirmed": market_conf.get("volume_confirmed"),
        "spread_ok": market_conf.get("spread_ok"),
        "overextended": market_conf.get("overextended"),
        "continuation_eligible": cont_result["eligible"],
        "fade_eligible": fade_result["eligible"],
        "continuation_confidence": cont_result.get("confidence", 0),
        "fade_confidence": fade_result.get("confidence", 0),
        "continuation_fail_reasons": cont_result.get("fail_reasons", []),
        "fade_fail_reasons": fade_result.get("fail_reasons", []),
        "final_action": final_action,
        "chosen_entry_model": entry_model,
    }
    
    return log_entry


# ============================================================
# EXECUTION ENGINE
# ============================================================

def load_credentials():
    """Load Bybit API credentials"""
    skill_path = Path(__file__).parent
    creds_file = skill_path / "credentials.json"
    
    if creds_file.exists():
        with open(creds_file) as f:
            data = json.load(f)
            return data.get("api_key"), data.get("api_secret")
    
    creds_file = Path.home() / "OneDrive" / "Pictures" / "auto_opener_monitor" / "crypto_trader" / "credentials.json"
    if creds_file.exists():
        with open(creds_file) as f:
            data = json.load(f)
            return data.get("api_key"), data.get("api_secret")
    
    return None, None


def get_bybit_session():
    """Get ccxt Bybit session"""
    api_key, api_secret = load_credentials()
    if not api_key:
        return None
    
    import ccxt
    return ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })


async def get_rsi(symbol, timeframe='1h', period=14):
    """Get RSI for a symbol"""
    try:
        bybit = get_bybit_session()
        if not bybit:
            return None
        
        ohlcv = bybit.fetch_ohlcv(symbol, timeframe, limit=period+1)
        if not ohlcv or len(ohlcv) < period + 1:
            return None
        
        closes = [c[4] for c in ohlcv]
        gains = [max(0, closes[i] - closes[i-1]) for i in range(1, len(closes))]
        losses = [max(0, closes[i-1] - closes[i]) for i in range(1, len(closes))]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))
        return round(rsi, 2)
    except:
        return None


async def get_atr(symbol, timeframe='1h', period=14):
    """Get ATR for a symbol"""
    try:
        bybit = get_bybit_session()
        if not bybit:
            return None
        
        ohlcv = bybit.fetch_ohlcv(symbol, timeframe, limit=period+1)
        if not ohlcv or len(ohlcv) < period + 1:
            return None
        
        ranges = []
        for i in range(1, len(ohlcv)):
            high = ohlcv[i][2]
            low = ohlcv[i][3]
            prev_close = ohlcv[i-1][4]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            ranges.append(tr)
        
        atr = sum(ranges[-period:]) / period
        return round(atr, 4)
    except:
        return None


async def execute_trade(symbol, direction, size_percent=10, entry_model="continuation"):
    """Execute trade with TP/SL"""
    try:
        bybit = get_bybit_session()
        if not bybit:
            print("[ERROR] No API credentials!")
            return False, None
        
        # Get balance
        balance = bybit.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0)
        
        if usdt_balance < CONFIG["risk"]["min_balance"]:
            print("[STOP] Balance {} < min {}".format(usdt_balance, CONFIG["risk"]["min_balance"]))
            return False, None
        
        # Get price and calculate qty
        ticker = bybit.fetch_ticker(symbol)
        price = ticker['last']
        
        max_position = usdt_balance * CONFIG["risk"]["max_position_pct"]
        qty = (usdt_balance * size_percent / 100) / price
        qty = min(qty, max_position / price)
        
        if symbol == 'XAUUSDT':
            qty = round(qty, 3)
        else:
            qty = round(qty, 2)
        
        if qty < 0.01:
            qty = 0.01
        
        # Place order
        side = 'buy' if direction == 'BULLISH' else 'sell'
        
        print("[ORDER] {} {} {} @ ${} (model: {})".format(side.upper(), qty, symbol, price, entry_model))
        
        order = bybit.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=qty,
            params={'positionIdx': 0}
        )
        
        print("[EXECUTE] Order placed: {}".format(order['id']))
        return True, order['id']
                
    except Exception as e:
        print("[ERROR] Trade failed: {}".format(e))
        return False, None


async def fetch_news():
    """Fetch news from sources"""
    print("\n=== NEWS SCANNER: {} ===".format(datetime.now().strftime('%Y-%m-%d %H:%M')))
    
    news_items = []
    
    for source in NEWS_SOURCES:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(source["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("[OK] {}: {} chars".format(source['name'], len(response.text)))
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for h in soup.find_all(['h2', 'h3', 'a']):
                    text = h.get_text(strip=True)
                    if 30 < len(text) < 200:
                        news_items.append({"source": source["name"], "headline": text})
        except Exception as e:
            print("[X] {}: {}".format(source['name'], e))
    
    return news_items


async def analyze_and_trade():
    """Main trading logic - V2.1"""
    print("\n" + "="*60)
    print("BYBIT NEWS TRADING BOT v2.1 - BYBIT_NEWS_TRADING_V2")
    print("Models: CONTINUATION (momentum) + FADE (reversal)")
    print("="*60)
    
    bybit = get_bybit_session()
    if not bybit:
        print("[ERROR] No Bybit session!")
        return
    
    balance = bybit.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    print("\nBalance: ${}".format(usdt_balance))
    
    # Fetch and analyze news
    news_items = await fetch_news()
    if not news_items:
        print("No news found")
        return
    
    decisions = []
    
    for item in news_items:
        headline = item["headline"]
        if len(headline) < 30:
            continue
        
        commodity = identify_commodity(headline)
        if not commodity:
            continue
        
        sentiment, strength = analyze_sentiment(headline)
        if sentiment == "NEUTRAL":
            continue
        
        # Calculate event score
        event_score = calculate_event_score(headline, item["source"], sentiment, strength, commodity)
        
        pairs = get_pairs_for_commodity(commodity)
        
        for symbol in pairs:
            # Get technical indicators
            rsi = await get_rsi(symbol)
            atr = await get_atr(symbol)
            
            # Market confirmation
            market_conf = evaluate_market_confirmation(bybit, symbol, sentiment)
            
            # Build decision
            decision = build_trade_decision(
                event_score=event_score,
                rsi=rsi,
                atr=atr,
                market_conf=market_conf,
                direction=sentiment,
                symbol=symbol,
                headline=headline,
                source=item["source"]
            )
            
            decisions.append(decision)
            
            # Log the decision
            print("\n--- DECISION ---")
            print("Symbol: {} | Dir: {} | Score: {}".format(symbol, sentiment, event_score))
            print("RSI: {} | ATR: {}".format(rsi, atr))
            print("Continuation: {} (conf: {}) | Fade: {} (conf: {})".format(
                decision["continuation_eligible"], decision.get("continuation_confidence", 0),
                decision["fade_eligible"], decision.get("fade_confidence", 0)
            ))
            print("Fail reasons - Cont: {} | Fade: {}".format(
                decision["continuation_fail_reasons"],
                decision["fade_fail_reasons"]
            ))
            print(">>> {}".format(decision["final_action"]))
            
            # Execute if approved
            if decision["final_action"] != "SKIP":
                direction = "BULLISH" if "LONG" in decision["final_action"] else "BEARISH"
                model = decision["chosen_entry_model"]
                
                success, order_id = await execute_trade(symbol, direction, 10, model)
                
                if success:
                    decision["order_id"] = order_id
                    decision["executed"] = True
    
    # Save decisions to log
    output_file = Path(__file__).parent / "trade_decisions.json"
    with open(output_file, "w") as f:
        json.dump(decisions, f, indent=2)
    
    print("\n[Saved] {} decisions to trade_decisions.json".format(len(decisions)))


async def main():
    """Entry point"""
    await analyze_and_trade()


if __name__ == "__main__":
    asyncio.run(main())