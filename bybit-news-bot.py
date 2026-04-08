#!/usr/bin/env python3
"""
Bybit News Trading Bot v1.6 - COMMODITY + CRYPTO FOCUS
Scans major news sources for gold, oil, and commodity news, then trades XAUUSDT, XAGUSDT, GASUSDT autonomously

UPDATES v1.4:
- MAX 30% POSITION SIZE per trade
- RSI FILTER (only enter when RSI < 35 or > 65)
- Position size limits based on account balance
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# News sources - OPTIMIZED for OIL & GOLD
NEWS_SOURCES = [
    {"name": "OilPrice", "url": "https://oilprice.com/"},
    {"name": "BBC Business", "url": "https://www.bbc.com/news/business"},
    {"name": "MarketWatch Commodities", "url": "https://www.marketwatch.com/investing/commodities"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/topic/markets/"},
]

# Focus pairs - EXPANDED for OIL & GOLD & COMMODITIES
TRADING_PAIRS = [
    # Gold
    "XAUUSDT",   # Gold/USDT
    "XAUTUSDT",  # Gold Tether
    # Silver
    "XAGUSDT",   # Silver/USDT
    # Oil/Natural Gas
    "GASUSDT",   # Natural Gas
    # Energy/Crypto related
    "BTCUSDT",   # Bitcoin (gold of crypto)
    "ETHUSDT",   # Ethereum
]

# Commodity to pair mapping
COMMODITY_PAIRS = {
    "gold": ["XAUUSDT", "XAUTUSDT"],
    "silver": ["XAGUSDT"],
    "oil": ["GASUSDT"],
    "natural gas": ["GASUSDT"],
    "bitcoin": ["BTCUSDT"],
    "crypto": ["BTCUSDT", "ETHUSDT"],
}

# Keywords - EXPANDED for OIL & GOLD
GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "goldman sachs gold", "gold price", "gold up", "gold down",
    "gold surge", "gold falls", "gold rally", "gold gains", "gold losses",
    "safe haven", "gold etf", "gold futures", "gold mining", "gold stocks",
    "gold ounces", "gold bars", "gold coin", "spot gold", "gold market",
    "inflation hedge", "gold demand", "gold supply", "central bank gold",
    "palladium", "platinum", "precious metals"
]

SILVER_KEYWORDS = [
    "silver", "xag", "silver price", "silver up", "silver down", "silver surge",
    "silver rally", "silver futures", "silver mining", "silver demand"
]

OIL_KEYWORDS = [
    # Basic
    "oil", "opec", "crude", "wti", "brent", "petroleum", "energy", "natural gas",
    "iran", "straits", "hormuz", "oil price", "oil up", "oil down",
    "oil surge", "oil plunges", "oil spike", "fuel",
    # Expanded
    "opec+", "opec plus", "saudi", "russia oil", "oil production", "oil supply",
    "oil demand", "oil inventory", "oil reserves", "oil exports",
    "gasoline", "diesel", "jet fuel", "heating oil", "refining",
    "pipeline", "oil tanker", "oil rig", "shale", "fracking",
    "national average gas", "gas prices", "pump price", "fuel prices",
    "electric vehicle", "ev demand", "battery", "lithium",
    "energy crisis", "energy prices", "power crisis", "electricity prices"
]

BULLISH_KEYWORDS = [
    "up", "surge", "rally", "gains", "soars", "hits record", "breakout", 
    "bullish", "higher", "rises", "climbs", "best", "growing", "growth"
]

BEARISH_KEYWORDS = [
    "down", "falls", "drops", "plunges", "tumbles", "slumps", "declines",
    "bearish", "lower", "selloff", "worst", "recession", "fears", "crash"
]


def analyze_sentiment(text):
    """Analyze news text for sentiment"""
    text_lower = " " + text.lower() + " "
    
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    
    if bullish_count > bearish_count:
        return "BULLISH", bullish_count - bearish_count
    elif bearish_count > bullish_count:
        return "BEARISH", bearish_count - bearish_count
    else:
        return "NEUTRAL", 0


def identify_commodity(text):
    """Identify which commodity the news is about"""
    text_lower = " " + text.lower() + " "
    
    for kw in OIL_KEYWORDS:
        if kw in text_lower:
            return "oil"
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
        "oil": ["GASUSDT"],
        "natural gas": ["GASUSDT"],
        "bitcoin": ["BTCUSDT"],
        "crypto": ["BTCUSDT", "ETHUSDT"],
    }
    return mapping.get(commodity, ["XAUUSDT", "BTCUSDT"])


def load_credentials():
    """Load Bybit API credentials"""
    # First check skill folder
    skill_path = Path(__file__).parent
    creds_file = skill_path / "credentials.json"
    
    if creds_file.exists():
        with open(creds_file) as f:
            data = json.load(f)
            return data.get("api_key"), data.get("api_secret")
    
    # Then check OneDrive folder
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


async def fetch_news():
    """Fetch news from sources"""
    print("\n=== NEWS SCANNER: {} ===".format(datetime.now().strftime('%Y-%m-%d %H:%M')))
    
    news_items = []
    
    for source in NEWS_SOURCES:
        try:
            import requests
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(source["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("[OK] {}: {} chars".format(source['name'], len(response.text)))
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                headlines = []
                for h in soup.find_all(['h2', 'h3', 'a']):
                    text = h.get_text(strip=True)
                    if 30 < len(text) < 200:
                        headlines.append(text)
                
                for headline in headlines[:10]:
                    news_items.append({
                        "source": source["name"],
                        "headline": headline
                    })
                    
        except Exception as e:
            print("[X] {}: {}".format(source['name'], e))
    
    return news_items


def analyze_news(news_items):
    """Analyze news for commodity sentiment"""
    print("\n=== COMMODITY ANALYSIS ===")
    
    opportunities = []
    
    for item in news_items:
        headline = item["headline"]
        
        # Skip if too short
        if len(headline) < 30:
            continue
        
        commodity = identify_commodity(headline)
        if not commodity:
            continue
            
        sentiment, strength = analyze_sentiment(headline)
        
        if sentiment != "NEUTRAL":
            pairs = get_pairs_for_commodity(commodity)
            
            opportunities.append({
                "source": item["source"],
                "headline": headline,
                "sentiment": sentiment,
                "strength": strength,
                "commodity": commodity,
                "pairs": pairs
            })
            
            direction = ">>> BUY" if sentiment == "BULLISH" else "<<< SELL"
            print("\n[{}] {} - {}".format(sentiment, commodity.upper(), direction))
            print("  {}".format(headline[:100]))
            print("  -> Trade: {}".format(", ".join(pairs)))
    
    return opportunities


async def get_prices(pairs):
    """Get current prices for pairs using ccxt"""
    prices = {}
    
    try:
        bybit = get_bybit_session()
        
        for pair in pairs:
            try:
                ticker = bybit.fetch_ticker(pair)
                prices[pair] = {
                    "price": ticker['last'],
                    "24h_change": ticker['percentage']
                }
            except Exception as e:
                print("[ERROR] {}: {}".format(pair, e))
                
    except Exception as e:
        print("Price error: {}".format(e))
    
    return prices


async def execute_trade(pair, direction, size_percent=10):
    """Execute a trade on Bybit using ccxt - v1.4 with position limits"""
    try:
        bybit = get_bybit_session()
        
        if not bybit:
            print("[ERROR] No API credentials!")
            return False
        
        # Get current price and calculate qty
        ticker = bybit.fetch_ticker(pair)
        price = ticker['last']
        
        # Get balance
        try:
            balance = bybit.fetch_balance()
            usdt_balance = balance['total'].get('USDT', 0)
        except:
            usdt_balance = 450  # Default
        
        # v1.4: MAX 30% per trade
        max_position = usdt_balance * 0.30  # 30% max
        
        # Calculate qty (default 10%, but capped at 30%)
        qty = (usdt_balance * size_percent / 100) / price
        
        # Ensure we don't exceed 30%
        max_qty = max_position / price
        qty = min(qty, max_qty)
        
        # Round appropriately for each pair
        if pair == 'XAUUSDT':
            qty = round(qty, 3)  # Gold uses 3 decimals
        else:
            qty = round(qty, 2)
        
        if qty < 0.01:
            qty = 0.01
        
        # v1.4: Check RSI before trading
        try:
            rsi = await get_rsi(pair)
            print("[RSI CHECK] {} RSI: {}".format(pair, rsi))
            
            if direction == 'BULLISH' and rsi and rsi > 35:
                print("[SKIP] {} not oversold (RSI={}). Wait for dip.".format(pair, rsi))
                return False
            elif direction == 'BEARISH' and rsi and rsi < 65:
                print("[SKIP] {} not overbought (RSI={}). Wait for rally.".format(pair, rsi))
                return False
        except:
            pass  # Continue if RSI check fails
        
        # Place order
        side = 'buy' if direction == 'BULLISH' else 'sell'
        
        print("[ORDER] {} {} {} @ ${} (${} of ${})".format(side.upper(), qty, pair, price, qty*price, usdt_balance))
        
        try:
            order = bybit.create_order(
                symbol=pair,
                type='market',
                side=side,
                amount=qty,
                params={
                    'positionIdx': 0,  # One-way mode
                }
            )
            print("[EXECUTE] Order placed: {}".format(order['id']))
            return True
        except Exception as e:
            print("[ERROR] Order failed: {}".format(str(e)[:100]))
            return False
                
    except Exception as e:
        print("[ERROR] Trade failed: {}".format(e))
        return False


async def get_rsi(symbol, timeframe='1h', period=14):
    """Get RSI for a symbol using ccxt"""
    try:
        bybit = get_bybit_session()
        ohlcv = bybit.fetch_ohlcv(symbol, timeframe, limit=period+1)
        
        if not ohlcv or len(ohlcv) < period + 1:
            return None
        
        # Calculate RSI
        gains = []
        losses = []
        
        for i in range(1, len(ohlcv)):
            change = ohlcv[i][4] - ohlcv[i-1][4]  # close - open
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    except Exception as e:
        print("[RSI ERROR] {}: {}".format(symbol, e))
        return None


async def main():
    """Main news trading bot"""
    print("\n" + "="*50)
    print("BYBIT NEWS TRADING BOT v1.3 - COMMODITY FOCUS")
    print("Pairs: XAUUSDT, XAGUSDT, GASUSDT")
    print("="*50)
    
    # Step 1: Fetch news
    news_items = await fetch_news()
    
    if not news_items:
        print("No news found")
        return
    
    # Step 2: Analyze for commodities
    opportunities = analyze_news(news_items)
    
    if not opportunities:
        print("\n[INFO] No significant commodity news found")
        return
    
    # Step 3: Get prices
    prices = await get_prices(TRADING_PAIRS)
    
    print("\n=== CURRENT PRICES ===")
    for pair in TRADING_PAIRS:
        if pair in prices:
            change = prices[pair].get("24h_change", 0)
            print("{}: ${} ({}%)".format(pair, prices[pair]["price"], round(change, 2)))
        else:
            print("{}: Not available".format(pair))
    
    # Step 4: Execute trades
    print("\n=== EXECUTING TRADES ===")
    
    trades = []
    for opp in opportunities:
        for pair in opp["pairs"]:
            if pair in prices:
                trades.append({
                    "pair": pair,
                    "direction": opp["sentiment"],
                    "price": prices[pair]["price"],
                    "commodity": opp["commodity"],
                    "reason": opp["headline"][:60]
                })
                
                action = "LONG" if opp["sentiment"] == "BULLISH" else "SHORT"
                print("\n{} {} @ ${}".format(action, pair, prices[pair]["price"]))
                print("  Reason: {}...".format(opp["headline"][:60]))
                
                # Execute trade
                await execute_trade(pair, opp["sentiment"], size_percent=10)
    
    # Save signals
    output = {
        "timestamp": datetime.now().isoformat(),
        "trades": trades,
        "prices": {k: v["price"] for k, v in prices.items()}
    }
    
    output_file = Path(__file__).parent / "news_signals.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n[Saved] {} trade opportunities to news_signals.json".format(len(trades)))


if __name__ == "__main__":
    asyncio.run(main())
