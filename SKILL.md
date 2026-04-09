# SKILL: bybit-news-trading v2.0

**News-based trading on Bybit - MACRO, COMMODITY, CRYPTO**

## Strategy: BYBIT_NEWS_TRADING_V2

---

## Modes
- **macro_shock** - Fed rates, economic data, political news
- **commodity_shock** - Oil, gold, silver news
- **crypto_specific** - Bitcoin, Ethereum specific news

---

## Trading Pairs

| Priority | Symbols |
|----------|---------|
| **Core** | BTCUSDT, ETHUSDT, XAUUSDT, XAGUSDT, GASUSDT |
| **High Risk** | DOGEUSDT, XAUTUSDT |

---

## News Sources

### Tier 1 (Major)
- Reuters Markets
- CNBC
- BBC Business

### Tier 2 (Secondary)
- MarketWatch
- OilPrice

### Confirmation Rules
- **Medium events:** Require 2-source confirmation
- **Major breaking news:** 1 source allowed

---

## Event Scoring

**Minimum score to trade: 7/20**

| Factor | Weight | Description |
|--------|--------|-------------|
| Source quality | 0-4 | Reliability of source |
| Freshness | 0-3 | How recent (0=stale, 3=very fresh) |
| Surprise level | 0-4 | Unexpected vs expected |
| Asset relevance | 0-3 | How relevant to pair |
| Multi-source confirmation | 0-2 | 0=none, 2=multiple sources |
| Market confirmation | 0-4 | Technical confirmation |

### Market Confirmation (need 3 of 5)
- Breakout of pre-news range
- Volume spike vs 20-bar average
- Orderbook imbalance
- Open interest confirms move
- Mark index alignment

---

## Entry Models

### Continuation (Trend Following)
**Conditions:**
- Event score ≥ 8
- Breakout confirmed
- Spread acceptable
- Slippage acceptable

### Fade (Counter-trend)
**Conditions:**
- Event score 5-7
- RSI > 80 (for short) OR RSI < 20 (for long)
- Price extended ≥ 1.5 ATR
- Orderflow decelerating

---

## Position Sizing

| Parameter | Value |
|-----------|-------|
| Risk per trade | 0.75% |
| Max notional | 20% of balance |
| Max daily trades | 3 |
| Max daily loss | 3R |
| Max correlated positions | 2 |

**Example:** If balance = $374, max position = $74.80 (20%)

---

## Exit Rules

### Stop Loss
- **Type:** ATR-based
- **ATR Multiple:** 1.5

### Take Profit
| Level | Exit % | Target |
|-------|--------|--------|
| TP1 | 50% | 1R |
| TP2 | 50% | 2R |

### Trailing Stop
- **Enabled:** After TP1 hit
- **Method:** ATR or structure

### Time Stop
| Setup Type | Duration |
|------------|-----------|
| Fast (quick news) | 60 minutes |
| Slow (major event) | 6 hours |

---

## Safety Filters

### Minimum Balance
- **$50** - Stop trading below this

### Max Spread (bps)
| Symbol | Max Spread |
|--------|------------|
| BTCUSDT | 8 |
| ETHUSDT | 10 |
| XAUUSDT | 15 |
| XAGUSDT | 18 |
| GASUSDT | 25 |

### Block Trades If:
- Source unconfirmed
- Spread too wide
- Slippage too high
- Move already extended >1.8 ATR
- Contradictory headlines
- API latency abnormal

---

## Cron Jobs

- **News scan:** Every 3 minutes
- **Position monitor:** Every 15 seconds
- **TP/SL check:** Every 1 hour
- **Signal expiry:** 20 minutes

---

## Current Status

**Watching for:**
- RSI signals (oversold <35, overbought >65)
- News events with score ≥7
- Market confirmation (breakout, volume spike)

**Active pairs:** BTC, ETH, XAU, XAG, GAS

---

**Remember:** News trading is high-risk! Wait for confirmation, respect the rules.