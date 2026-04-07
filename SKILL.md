# BYBIT NEWS TRADING SKILL v1.1

**Day trading based on news events - GOLD, OIL, CRYPTO, POLITICAL**

## Overview

This skill monitors major news sources to identify market-moving events, then analyzes which crypto pairs will be affected and executes trades autonomously.

## Available Trading Pairs

| Asset | Bybit Symbol | Type |
|-------|--------------|------|
| Gold | XAUUSDT | Linear perpetual |
| Gold | XAUTUSDT | Spot |
| Silver | XAGUSDT | Linear |
| Gold Futures | XAUTUSDT-10APR26 | Futures |

## News Categories & Market Impact

| Category | Direction | Examples | Affected Pairs |
|----------|-----------|----------|----------------|
| Gold/Commodities | Bullish | Gold surge, mine news, inflation | XAUUSDT, XAGUSDT |
| Oil/Energy | Bullish | Oil spike, OPEC, supply | DAOUSDT, related |
| Fed/Interest Rates | Bearish | Fed raises rates, inflation | XAUUSDT, BTC, ETH |
| President/Political | Volatile | Trump speeches, China news | BTC, ETH, XAUUSDT |
| Crypto Regulation | Bullish | BTC ETF approval, SEC | BTC, ETH |
| Tech/AI News | Bullish | Nvidia earnings, AI breakthroughs | SOL, AVAX, AI tokens |
| Elon Musk | Bullish | Dogecoin tweets | DOGE, BTC |
| Economic Data | Mixed | Jobs report, GDP, CPI | XAUUSDT, BTC |

## Data Sources

### Major News (Web Fetch)
- **Reuters Markets:** https://www.reuters.com/markets/us
- **Reuters Commodities:** https://www.reuters.com/markets/commodities
- **BBC Business:** https://www.bbc.com/news/business
- **CNBC:** https://www.cnbc.com
- **CoinDesk:** https://www.coindesk.com

### Key Keywords to Watch

**BULLISH (Buy signals):**
- Gold up, gold surge, gold hits record
- Oil up, oil spikes, OPEC extends
- Fed rate cut, stimulus, inflation cools
- ETF approval, crypto friendly
- Breakout, all-time high, rally

**BEARISH (Sell signals):**
- Gold down, gold falls
- Oil drops, oil plunges
- Fed rate hike, inflation rises
- Recession fears, selloff
- All-time low, crash

## Trading Workflow

### STEP 1: SCAN NEWS (Every 2 hours via cron)
Fetch headlines from major news sources. Focus on:
- Commodities (Gold, Silver, Oil)
- Federal Reserve / Interest Rates
- Political announcements
- Economic data
- Crypto regulation

### STEP 2: ANALYZE IMPACT
Determine sentiment:
- **BULLISH** = Go long
- **BEARISH** = Go short
- **NEUTRAL** = No trade

### STEP 3: FIND PAIRS
Map news to affected pairs:
- Gold news -> XAUUSDT
- Oil/Energy -> Check for energy tokens
- Crypto news -> BTC, ETH
- Tech -> SOL, AVAX
- Political -> XAUUSDT, BTC

### STEP 4: EXECUTE AUTONOMOUSLY
- Position size: 5-10% max per trade
- TP: 2-3% (quick day trades)
- SL: 1.5%
- Trailing stop: 1%
- Exit within 4-24 hours max

## Bybit Trading Commands

```bash
# Buy XAUUSDT (Gold)
bybit order --symbol XAUUSDT --side Buy --qty 0.01 --price spot

# Sell XAUUSDT
bybit order --symbol XAUUSDT --side Sell --qty 0.01 --price spot

# Check positions
python check_bots.py
```

## Key Rules

1. **MAJOR NEWS ONLY** - Skip minor news, focus on market movers
2. **QUICK TRADES** - News moves fade fast, exit within 24h
3. **SMALL POSITIONS** - Max 10% portfolio per trade
4. **STOP AT $10** - Stop when available balance reaches $10
5. **ALWAYS TP/SL** - Never trade without protection
6. **MAX 3/day** - Quality over quantity

## Cron Jobs

- **Every 2 hours:** Scan news + execute trades
- **Every 1 min:** Check TP/SL on open positions

## Risk Management

- Never risk more than 1.5% per trade
- Exit all positions before major news events
- Stop at $10 available balance
- Max 3 news trades per day

---

**Remember:** News trading is high-risk! Be fast, be small, be out.
