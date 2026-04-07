# BYBIT NEWS TRADING SKILL v1.0

**Day trading based on news events, social media & market sentiment**

## Overview

This skill monitors news sources and social media to identify market-moving events, then analyzes which crypto pairs will be affected and finds optimal entry points.

## News Categories & Market Impact

| Category | Direction | Examples | Affected Pairs |
|----------|-----------|----------|----------------|
| Fed/Interest Rates | Bearish | Fed raises rates, inflation news | BTC, ETH, GOLD |
| President/Political | Volatile | Trump speeches, China news | BTC, GOLD, USDT pairs |
| ETF/Crypto Regulation | Bullish | BTC ETF approval, SEC news | BTC, ETH |
| Tech/AI News | Bullish | Nvidia earnings, AI breakthroughs | SOL, AVAX, AI tokens |
| Elon Musk | Bullish | Dogecoin tweets | DOGE, BTC |
| China/Crypto Ban | Bearish | China crackdown, restrictions | BTC, ETH, Tether |
| Economic Data | Mixed | Jobs report, GDP, CPI | BTC, GOLD, USD |

## Data Sources

### Web Fetch (No API Needed)
- **Reuters:** https://www.reuters.com/markets/us
- **CoinDesk:** https://www.coindesk.com
- **Bloomberg:** https://www.bloomberg.com/markets
- **Yahoo Finance:** https://finance.yahoo.com/crypto

### Social Media (Monitor)
- **X/Twitter:** @realDonaldTrump, @POTUS, @elonmusk, @CryptoTwitter
- **Reddit:** r/cryptocurrency, r/Bitcoin

## Trading Workflow

### STEP 1: SCAN NEWS (Every 2 hours)
Fetch latest news from sources above. Look for:
- Federal Reserve statements
- President/Political announcements  
- Crypto regulation news
- Major tech/AI developments
- Market-moving tweets

### STEP 2: ANALYZE IMPACT
Determine sentiment:
- **BULLISH** = Buy momentum expected
- **BEARISH** = Sell pressure expected
- **NEUTRAL** = No clear direction

Identify affected pairs based on category table.

### STEP 3: FIND ENTRY
For affected pairs:
1. Check current trend (RSI, Moving Averages)
2. Wait for pullback/retracement
3. Enter on 15min-1hr timeframe
4. Set tight TP/SL

### STEP 4: EXECUTE
- Position size: 5-10% max per trade
- TP: 2-3% (quick day trades)
- SL: 1.5%
- Trailing stop: 1%

## Example Workflow

```
NEWS: "Fed signals rates to stay higher for longer"
→ SENTIMENT: BEARISH
→ AFFECTED: BTC, ETH, GOLD
→ ACTION: Look for shorts or sell spot

NEWS: "Trump announces crypto-friendly policy"
→ SENTIMENT: BULLISH  
→ AFFECTED: BTC, ETH, SOL
→ ACTION: Look for long entries

NEWS: "Elon tweets about Dogecoin"
→ SENTIMENT: BULLISH
→ AFFECTED: DOGE
→ ACTION: Quick pump expected - sell quick!
```

## Bybit Commands

```bash
# Check prices
bybit-trading --symbol BTCUSDT price

# Open long
bybit-trading --symbol BTCUSDT --side Buy --qty 0.01 market

# Open short
bybit-trading --symbol BTCUSDT --side Sell --qty 0.01 market

# Set TP/SL
python tpsl_monitor_check.py

# Check positions
python check_bots.py
```

## Key Rules

1. **Never fight the news direction** - If bearish news, don't go long
2. **Quick trades** - News moves fade fast, exit within hours
3. **Small positions** - News is high risk, max 10% portfolio
4. **Stop at $10** - Stop trading when available balance reaches $10
5. **Only major pairs** - BTC, ETH, SOL, DOGE, XRP (high liquidity)

## Cron Jobs

- **Every 2 hours:** Scan news + analyze sentiment
- **Every 1 min:** Check TP/SL on open positions

## Files

- `bybit-news-bot.py` - Main news scanner
- `sentiment-analyzer.py` - Analyze news sentiment
- `tpsl_monitor_check.py` - Auto TP/SL

## Risk Management

- Max 3 news-based trades per day
- Never risk more than 1.5% per trade
- Exit all positions before major news events
- Stop at $10 available balance

---

**Remember:** News trading is high-risk! Quick profits = quick losses. Be fast, be small, be out.
