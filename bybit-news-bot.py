#!/usr/bin/env python3
"""
Bybit News Trading Bot v1.0
Scans news sources to find market-moving events and identifies trading opportunities
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# News sources to scan
NEWS_SOURCES = [
    {"name": "Reuters Markets", "url": "https://www.reuters.com/markets/us"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com"},
    {"name": "Yahoo Finance Crypto", "url": "https://finance.yahoo.com/crypto"},
    {"name": "BBC Business", "url": "https://www.bbc.com/news/business"},
]

# Keywords by sentiment
BULLISH_KEYWORDS = [
    "etf approval", "bullish", "all-time high", "record high", 
    "cryptocurrency friendly", "rate cut", "stimulus",
    "innovation", "adoption", "institutional", "breakout"
]

BEARISH_KEYWORDS = [
    "rate hike", "inflation", "recession", "crackdown", "ban",
    "bearish", "all-time low", "selloff", "regulation", 
    "restrictions", "china ban", "sec lawsuit"
]

# News category to trading pairs mapping
CATEGORY_PAIRS = {
    "fed_rates": ["BTCUSDT", "ETHUSDT", "XAUUSDT"],
    "president_political": ["BTCUSDT", "ETHUSDT", "USDTUSDC"],
    "crypto_regulation": ["BTCUSDT", "ETHUSDT", "USDCUSDT"],
    "tech_ai": ["SOLUSDT", "AVAXUSDT", "BTCUSDT"],
    "elon_musk": ["DOGEUSDT", "BTCUSDT"],
    "china_ban": ["BTCUSDT", "ETHUSDT", "USDTUSDC"],
    "economic": ["BTCUSDT", "XAUUSDT", "USDTUSDC"],
}


def analyze_sentiment(text):
    """Analyze news text for sentiment"""
    text_lower = text.lower()
    
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    
    if bullish_count > bearish_count:
        return "BULLISH", bullish_count - bearish_count
    elif bearish_count > bullish_count:
        return "BEARISH", bearish_count - bullish_count
    else:
        return "NEUTRAL", 0


def identify_category(text):
    """Identify which category the news falls into"""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["fed", "federal reserve", "interest rate", "fomc", "powell"]):
        return "fed_rates"
    if any(w in text_lower for w in ["trump", "president", "white house", "congress"]):
        return "president_political"
    if any(w in text_lower for w in ["sec", "etf", "approval", "regulation", "crypto law"]):
        return "crypto_regulation"
    if any(w in text_lower for w in ["nvidia", "ai", "tech", "earnings", "breakthrough"]):
        return "tech_ai"
    if any(w in text_lower for w in ["elon", "musk", "doge"]):
        return "elon_musk"
    if any(w in text_lower for w in ["china", "ban", "crackdown"]):
        return "china_ban"
    if any(w in text_lower for w in ["gdp", "cpi", "jobs", "unemployment", "economy"]):
        return "economic"
    
    return "general"


def get_affected_pairs(category):
    """Get trading pairs affected by this news category"""
    return CATEGORY_PAIRS.get(category, ["BTCUSDT", "ETHUSDT"])


def load_env():
    """Load Bybit API credentials from environment or file"""
    # Try environment first
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if api_key and api_secret:
        return api_key, api_secret
    
    # Try to load from credentials file
    creds_file = Path.home() / "OneDrive" / "Pictures" / "auto_opener_monitor" / "crypto_trader" / "credentials.json"
    
    if creds_file.exists():
        with open(creds_file) as f:
            data = json.load(f)
            return data.get("api_key"), data.get("api_secret")
    
    return None, None


async def fetch_news():
    """Fetch news from all sources"""
    print(f"\n=== NEWS SCANNER: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
    
    news_items = []
    
    for source in NEWS_SOURCES:
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(source["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ {source['name']}: Fetched {len(response.text)} chars")
                
                # Extract headlines (simple approach)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for headlines
                headlines = []
                for h in soup.find_all(['h2', 'h3', 'a']):
                    text = h.get_text(strip=True)
                    if 20 < len(text) < 200:  # Reasonable headline length
                        headlines.append(text)
                
                # Take first 5
                for headline in headlines[:5]:
                    news_items.append({
                        "source": source["name"],
                        "headline": headline,
                        "url": source["url"]
                    })
                    
        except Exception as e:
            print(f"✗ {source['name']}: {e}")
    
    return news_items


def analyze_news(news_items):
    """Analyze news for sentiment and trading opportunities"""
    print("\n=== SENTIMENT ANALYSIS ===\n")
    
    opportunities = []
    
    for item in news_items:
        headline = item["headline"]
        
        # Analyze
        sentiment, strength = analyze_sentiment(headline)
        category = identify_category(headline)
        pairs = get_affected_pairs(category)
        
        if sentiment != "NEUTRAL":
            opportunities.append({
                "source": item["source"],
                "headline": headline,
                "sentiment": sentiment,
                "strength": strength,
                "category": category,
                "affected_pairs": pairs
            })
            
            print(f"[{sentiment}] {item['source']}")
            print(f"  {headline[:100]}...")
            print(f"  → {', '.join(pairs)}\n")
    
    return opportunities


async def get_market_prices(pairs):
    """Get current prices for affected pairs"""
    api_key, api_secret = load_env()
    
    if not api_key:
        print("⚠ No API credentials found")
        return {}
    
    try:
        import requests
        
        url = "https://api.bybit.com/v5/market/tickers"
        params = {"category": "spot", "symbol": ",".join(pairs[:5])}  # Limit to 5
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("retCode") == 0:
                prices = {}
                for item in data.get("result", {}).get("list", []):
                    prices[item["symbol"]] = float(item["lastPrice"])
                return prices
                
    except Exception as e:
        print(f"⚠ Error fetching prices: {e}")
    
    return {}


def generate_recommendations(opportunities, prices):
    """Generate trading recommendations based on news and prices"""
    print("\n=== TRADING RECOMMENDATIONS ===\n")
    
    recommendations = []
    
    for opp in opportunities:
        for pair in opp["affected_pairs"]:
            price = prices.get(pair, "N/A")
            
            rec = {
                "pair": pair,
                "action": "BUY" if opp["sentiment"] == "BULLISH" else "SELL",
                "reason": f"News: {opp['headline'][:50]}...",
                "sentiment": opp["sentiment"],
                "price": price
            }
            recommendations.append(rec)
            
            direction = "🟢 LONG" if opp["sentiment"] == "BULLISH" else "🔴 SHORT"
            print(f"{direction} {pair} @ {price}")
            print(f"  Reason: {opp['headline'][:80]}")
            print()
    
    return recommendations


async def main():
    """Main news trading bot"""
    print("🔍 BYBIT NEWS TRADING BOT v1.0\n")
    
    # Step 1: Fetch news
    news_items = await fetch_news()
    
    if not news_items:
        print("No news found, checking again later...")
        return
    
    # Step 2: Analyze sentiment
    opportunities = analyze_news(news_items)
    
    if not opportunities:
        print("No significant news found")
        return
    
    # Step 3: Get affected pairs
    all_pairs = []
    for opp in opportunities:
        all_pairs.extend(opp["affected_pairs"])
    all_pairs = list(set(all_pairs))[:10]  # Dedupe, max 10
    
    # Step 4: Get current prices
    prices = await get_market_prices(all_pairs)
    
    # Step 5: Generate recommendations
    recommendations = generate_recommendations(opportunities, prices)
    
    # Save to file for cron job
    output = {
        "timestamp": datetime.now().isoformat(),
        "opportunities": opportunities,
        "recommendations": recommendations,
        "prices": prices
    }
    
    output_file = Path(__file__).parent / "news_signals.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Saved {len(recommendations)} recommendations to news_signals.json")
    
    # Summary
    bullish_count = sum(1 for r in recommendations if r["action"] == "BUY")
    bearish_count = sum(1 for r in recommendations if r["action"] == "SELL")
    
    print(f"\n📊 Summary: {bullish_count} bullish, {bearish_count} bearish opportunities")


if __name__ == "__main__":
    asyncio.run(main())
