#!/usr/bin/env python3
"""
Bybit News Trading Bot v1.2 - COMMODITY FOCUS
Scans major news sources for gold, oil, and commodity news, then trades XAUUSDT, XAGUSDT, GASUSDT autonomously
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# News sources
NEWS_SOURCES = [
    {"name": "BBC Business", "url": "https://www.bbc.com/news/business"},
    {"name": "CNBC", "url": "https://www.cnbc.com/investing/"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/topic/markets/"},
]

# Focus pairs
TRADING_PAIRS = ["XAUUSDT", "XAGUSDT", "GASUSDT"]

# Keywords - use word boundaries for accuracy
GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "goldman sachs gold", "gold price", "gold up", "gold down",
    "gold surge", "gold falls", "gold rally", "gold gains", "gold losses",
    "safe haven", "gold etf"
]

SILVER_KEYWORDS = [
    "silver", "xag", "silver price", "silver up", "silver down", "silver surge"
]

OIL_KEYWORDS = [
    "oil", "opec", "crude", "wti", "brent", "petroleum", "energy", "natural gas",
    "iran", "straits", "hormuz", "oil price", "oil up", "oil down",
    "oil surge", "oil plunges", "oil spike", "fuel"
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
        return "BEARISH", bearish_count - bullish_count
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
    
    return None


def get_pairs_for_commodity(commodity):
    """Get trading pairs for the commodity"""
    mapping = {
        "gold": ["XAUUSDT"],
        "silver": ["XAGUSDT"],
        "oil": ["GASUSDT"],
    }
    return mapping.get(commodity, ["XAUUSDT"])


def load_credentials():
    """Load Bybit API credentials"""
    creds_file = Path.home() / "OneDrive" / "Pictures" / "auto_opener_monitor" / "crypto_trader" / "credentials.json"
    
    if creds_file.exists():
        with open(creds_file) as f:
            data = json.load(f)
            return data.get("api_key"), data.get("api_secret")
    
    return None, None


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
    """Get current prices for pairs"""
    try:
        import requests
        
        prices = {}
        
        # Get each pair individually
        for pair in pairs:
            url = "https://api.bybit.com/v5/market/tickers"
            params = {"category": "linear", "symbol": pair}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                item = data["result"]["list"][0]
                prices[item["symbol"]] = {
                    "price": float(item["lastPrice"]),
                    "24h_change": float(item.get("price24hPcnt", 0)) * 100
                }
    except Exception as e:
        print("Price error: {}".format(e))
    
    return prices


async def execute_trade(pair, direction, size_percent=10):
    """Execute a trade on Bybit"""
    api_key, api_secret = load_credentials()
    
    if not api_key:
        print("[ERROR] No API credentials!")
        return False
    
    try:
        import requests
        import time
        import hmac
        import hashlib
        
        # Get current price
        r = requests.get("https://api.bybit.com/v5/market/tickers", 
                        params={"category": "linear", "symbol": pair}, timeout=10)
        data = r.json()
        
        if data.get("retCode") != 0:
            print("[ERROR] Could not get price for {}".format(pair))
            return False
        
        price = float(data["result"]["list"][0]["lastPrice"])
        
        # Calculate position size (percentage of balance)
        balance = 450  # Assume ~$450 USDT
        qty = (balance * size_percent / 100) / price
        qty = round(qty, 2)
        
        if qty < 0.01:
            qty = 0.01
        
        # Prepare order
        side = "Buy" if direction == "BULLISH" else "Sell"
        
        # Sign request
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        params_str = "category=linear&symbol={}&side={}&orderType=Market&qty={}".format(
            pair, side, qty)
        
        signature = hmac.new(
            api_secret.encode(),
            (timestamp + api_key + recv_window + params_str).encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }
        
        # Place order
        order_url = "https://api.bybit.com/v5/order/create"
        order_data = {
            "category": "linear",
            "symbol": pair,
            "side": side,
            "orderType": "Market",
            "qty": str(qty)
        }
        
        response = requests.post(order_url, json=order_data, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("retCode") == 0:
            print("[EXECUTE] {} {} {} at ${}".format(side, qty, pair, price))
            return True
        else:
            print("[ERROR] Order failed: {}".format(result.get("retMsg")))
            return False
                
    except Exception as e:
        print("[ERROR] Trade failed: {}".format(e))
        return False


async def main():
    """Main news trading bot"""
    print("\n" + "="*50)
    print("BYBIT NEWS TRADING BOT v1.2 - COMMODITY FOCUS")
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
            print("{}: ${} ({}%)".format(pair, prices[pair]["price"], change))
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
