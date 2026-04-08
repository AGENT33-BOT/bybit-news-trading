# BYBIT NEWS TRADING SKILL v1.2

**Day trading based on news events - GOLD, OIL, CRYPTO, POLITICAL**

## Overview

This skill monitors major news sources to identify market-moving events, then analyzes which crypto pairs will be affected and executes trades autonomously.

## IMPROVED - v1.2 Changes

- **MAX 30% POSITION SIZE** - Never more than 30% of balance per trade
- **RSI FILTER** - Only enter when RSI < 35 (oversold) or > 65 (overbought)
- **IN-PLAY KLASHI** - Only trade after game starts
- **Smaller trades** - 5-15% per trade instead of 10%

## Available Trading Pairs

| Asset | Bybit Symbol | Type |
|-------|--------------|------|
| Gold | XAUUSDT | Linear perpetual |
| Silver | XAGUSDT | Linear |
| Natural Gas | GASUSDT | Linear |
| BTC | BTCUSDT | Linear |
| ETH | ETHUSDT | Linear |

## News Categories & Market Impact

| Category | Direction | Examples | Affected Pairs |
|----------|-----------|----------|----------------|
| Gold/Commodities | Bullish | Gold surge, mine news, inflation | XAUUSDT, XAGUSDT |
| Oil/Energy | Bullish | Oil spike, OPEC, supply | GASUSDT |
| Fed/Interest Rates | Bearish | Fed raises rates, inflation | XAUUSDT, BTC |
| President/Political | Volatile | Trump speeches, China news | BTC, ETH, XAUUSDT |
| Crypto Regulation | Bullish | BTC ETF approval, SEC | BTC, ETH |
| Tech/AI News | Bullish | Nvidia earnings, AI breakthroughs | SOL, AVAX |
| Elon Musk | Bullish | Dogecoin tweets | DOGE |

## Data Sources

- **Reuters Markets:** https://www.reuters.com/markets/us
- **BBC Business:** https://www.bbc.com/news/business
- **CNBC:** https://www.cnbc.com

## Key Keywords

**BULLISH:** gold up, oil spikes, Fed rate cut, breakout, rally
**BEARISH:** gold down, oil drops, Fed rate hike, selloff, crash

## Trading Rules (v1.2)

1. **MAX 30% PER TRADE** - Never exceed 30% of account balance
2. **RSI FILTER** - Enter only when:
   - RSI < 35 (oversold) for long
   - RSI > 65 (overbought) for short
3. **QUICK TRADES** - Exit within 4-24 hours
4. **ALWAYS TP/SL** - 2.5% TP, 2% SL, 1% trailing
5. **STOP AT $50** - Stop trading when balance reaches $50
6. **MAX 3 TRADES/DAY** - Quality over quantity

## Position Sizing

| Balance | Max Position |
|---------|-------------|
| $500 | $150 (30%) |
| $400 | $120 (30%) |
| $300 | $90 (30%) |
| $200 | $60 (30%) |

## Cron Jobs

- **Every 2 hours:** Scan news + execute trades
- **Every 1 min:** Check TP/SL on open positions
- **Every 1 hour:** TP/SL monitor cron

## Risk Management

- Never risk more than 2% per trade
- Exit all positions within 24h
- Stop at $50 balance
- Max 3 trades per day

---

**Remember:** News trading is high-risk! Be fast, be small, be out.
