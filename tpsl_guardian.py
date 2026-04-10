#!/usr/bin/env python3
"""
TP/SL Guardian - Check both accounts every 5 minutes
"""
import json
import ccxt
from pathlib import Path
from datetime import datetime

def load_creds(path):
    with open(path) as f:
        return json.load(f)

def check_account(creds, name):
    """Check single account for positions and TP/SL"""
    print(f"\n=== {name} ===")
    
    bybit = ccxt.bybit({
        'apiKey': creds['api_key'],
        'secret': creds['api_secret'],
        'options': {'defaultType': 'linear'}
    })
    
    try:
        bal = bybit.fetch_balance()
        usdt = round(bal['total'].get('USDT', 0), 2)
        print(f"Balance: ${usdt}")
    except Exception as e:
        print(f"Balance error: {e}")
        return
    
    # Check positions
    try:
        positions = bybit.fetch_positions({'category': 'linear'})
        open_pos = [p for p in positions if p.get('size', 0) != 0]
        
        if not open_pos:
            print("No open positions")
            return
        
        for pos in open_pos:
            sym = pos['symbol']
            side = pos['side']
            size = pos['size']
            entry = pos['entryPrice']
            pnl = pos.get('unrealizedPnl', 0)
            
            print(f"{sym} | {side} {size} | Entry:{entry} | PNL:{pnl}")
            
            # Check for TP/SL - try to get open orders
            try:
                orders = bybit.fetch_open_orders(sym)
                has_tp = any('takeProfit' in str(o.get('params', {})).lower() for o in orders)
                has_sl = any('stopLoss' in str(o.get('params', {})).lower() for o in orders)
                
                if has_tp or has_sl:
                    print(f"  ✅ TP/SL: OK")
                else:
                    print(f"  ⚠️ NO TP/SL!")
                    
                    # Try to set TP/SL
                    try:
                        # Simple 2.5% TP/SL
                        if side == 'buy':
                            tp = entry * 1.025
                            sl = entry * 0.975
                        else:
                            tp = entry * 0.975
                            sl = entry * 1.025
                        
                        bybit.set_margin_mode(symbol=sym, margin_mode='isolated')
                        bybit.set_leverage(symbol=sym, leverage=10)
                        
                        bybit.create_order(
                            symbol=sym,
                            type='limit',
                            side='sell' if side=='buy' else 'buy',
                            amount=size,
                            price=tp if side=='buy' else sl,
                            params={
                                'takeProfit': {'price': tp},
                                'stopLoss': {'price': sl},
                                'positionIdx': 0
                            }
                        )
                        print(f"  ✅ Set TP:{tp} SL:{sl}")
                    except Exception as e:
                        print(f"  ❌ Error: {str(e)[:50]}")
                        
            except Exception as e:
                print(f"  Error checking orders: {e}")
                
    except Exception as e:
        print(f"Position error: {e}")

def main():
    print("="*50)
    print("TP/SL GUARDIAN - Both Accounts")
    print("="*50)
    
    # New sub-account (llXHLn...)
    new_creds = Path(__file__).parent / "credentials.json"
    if new_creds.exists():
        c = load_creds(new_creds)
        check_account(c, "NEW ACCOUNT (llXHLn...)")
    
    # Old account (bsK06...)
    old_creds = Path(__file__).parent.parent / "crypto_trader" / "credentials.json"
    if old_creds.exists():
        c = load_creds(old_creds)
        check_account(c, "OLD ACCOUNT (bsK06...)")
    
    print("\nDone")

if __name__ == "__main__":
    main()