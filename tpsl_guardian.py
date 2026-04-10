#!/usr/bin/env python3
"""
TP/SL Guardian v3 - With trailing stop support
"""
import json
import ccxt
from pathlib import Path

# TP/SL settings
TP_PCT = 0.025  # 2.5%
SL_PCT = 0.025  # 2.5%
TRAIL_PCT = 0.01  # 1% trailing (activates after profit)

def check_account(creds, name):
    print(f"\n=== {name} ===")
    bybit = ccxt.bybit({'apiKey': creds['api_key'], 'secret': creds['secret'], 'options': {'defaultType': 'linear'}})
    
    try:
        positions = bybit.fetch_positions()
        open_pos = [p for p in positions if p.get('size', 0) != 0]
        
        if not open_pos:
            print("No open positions")
            return
        
        for pos in open_pos:
            sym = pos['symbol']
            side = pos['side']
            size = pos['size']
            entry = float(pos['entryPrice'])
            pnl = pos.get('unrealizedPnl', 0)
            
            # Calculate TP/SL
            if side == 'buy':
                tp = entry * (1 + TP_PCT)
                sl = entry * (1 - SL_PCT)
            else:
                tp = entry * (1 - TP_PCT)
                sl = entry * (1 + SL_PCT)
            
            print(f"{sym} | {side} {size} | Entry:{entry} | TP:{tp:.4f} SL:{sl:.4f}")
            print(f"  PNL: {pnl}")
            
    except Exception as e:
        print(f"Error: {str(e)[:50]}")

def main():
    print("="*50)
    print("TP/SL GUARDIAN v3")
    print("Rules: TP 2.5% | SL 2.5% | Trailing 1%")
    print("="*50)
    
    # New sub
    p = Path(__file__).parent / "credentials.json"
    if p.exists():
        check_account(json.load(open(p)), "NEW (llXHLn...)"
    
    # Old
    o = Path(__file__).parent.parent / "crypto_trader" / "credentials.json"
    if o.exists():
        check_account(json.load(open(o)), "OLD (bsK06...)"

if __name__ == "__main__":
    main()