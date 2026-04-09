"""
Hourly report script - sends status to Telegram directly
"""
import json
from pathlib import Path
import urllib.request
import urllib.parse
import ccxt

BOT_TOKEN = "8586893914:AAE97US-4TwphcZeXVbk8GNkIYowHb_JLYw"
CHAT_ID = "5804173449"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def get_status():
    try:
        skill_path = Path('C:/Users/digim/.openclaw/workspace/skills/bybit-news-trading')
        with open(skill_path / 'credentials.json') as f:
            creds = json.load(f)
        
        bybit_new = ccxt.bybit({'apiKey': creds['api_key'], 'secret': creds['api_secret']})
        bybit_old = ccxt.bybit({'apiKey': 'bsK06QDhsagOWwFsXQ', 'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'})
        
        bal_new = round(bybit_new.fetch_balance()['total'].get('USDT', 0), 2)
        bal_old = round(bybit_old.fetch_balance()['total'].get('USDT', 0), 2)
        
        return f"Bybit: New ${bal_new} | Old ${bal_old} | Total ${bal_new + bal_old}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    status = get_status()
    message = f"Hourly Report\n\n{status}"
    send_telegram(message)
    print(message)
