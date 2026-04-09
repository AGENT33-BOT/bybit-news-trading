"""
Telegram notifier for cron reports - uses direct API calls
"""
import sys
import urllib.parse

BOT_TOKEN = "8586893914:AAE97US-4TwphcZeXVbk8GNkIYowHb_JLYw"
CHAT_ID = "5804173449"

def send_message(text):
    """Send message via Telegram API"""
    import urllib.request
    import json
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='POST')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Test message"
    result = send_message(message)
    if result and result.get("ok"):
        print("Message sent!")
    else:
        print("Failed to send")
