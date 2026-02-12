#!/usr/bin/env python3
"""
Solana Token Price Alert with Pushover Notification
Monitors a meme token price and sends a LOUD siren alert when target is reached.
Deploy on Railway.app for 24/7 monitoring without your PC.
"""

import os
import time
import requests
from datetime import datetime

# ============ CONFIGURATION ============
# Option 1: Set via Environment Variables (recommended for deployment)
# Option 2: Replace directly here for local testing

PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "YOUR_PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "YOUR_PUSHOVER_API_TOKEN")

# Token settings (can also be set via env vars)
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS", "Cm6fNnMk7NfzStP9CZpsQA2v3jjzbcYGAxdJySmHpump")
TARGET_PRICE = float(os.getenv("TARGET_PRICE", "0.03"))  # USD
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # seconds between checks

# =========================================

def get_token_price():
    """Fetch current token price from DexScreener API (free, no API key needed)"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADDRESS}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("pairs") and len(data["pairs"]) > 0:
            # Get the first (most liquid) pair
            pair = data["pairs"][0]
            price_usd = float(pair.get("priceUsd", 0))
            token_name = pair.get("baseToken", {}).get("name", "Unknown")
            token_symbol = pair.get("baseToken", {}).get("symbol", "???")
            return {
                "price": price_usd,
                "name": token_name,
                "symbol": token_symbol
            }
        return None
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching price: {e}")
        return None


def send_pushover_alert(token_info):
    """Send emergency priority notification with SIREN sound"""
    url = "https://api.pushover.net/1/messages.json"
    
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": f"🚀 {token_info['symbol']} досягнув ${token_info['price']:.6f}!\n\nЦільова ціна: ${TARGET_PRICE}\nЧас: {datetime.now().strftime('%H:%M:%S')}",
        "title": f"🔥 PRICE ALERT: {token_info['symbol']}",
        "sound": "siren",  # SIREN sound for wake-up
        "priority": 2,  # Emergency priority - repeats until acknowledged
        "retry": 30,  # Retry every 30 seconds
        "expire": 3600,  # Keep retrying for 1 hour
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"[{datetime.now()}] ✅ ALERT SENT! Check your phone!")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error sending alert: {e}")
        return False


def main():
    print("=" * 50)
    print("🔍 Solana Token Price Monitor")
    print("=" * 50)
    print(f"Token: {TOKEN_ADDRESS[:20]}...{TOKEN_ADDRESS[-10:]}")
    print(f"Target Price: ${TARGET_PRICE}")
    print(f"Check Interval: {CHECK_INTERVAL}s")
    print("=" * 50)
    print()
    
    alert_sent = False
    
    while True:
        token_info = get_token_price()
        
        if token_info:
            current_price = token_info["price"]
            symbol = token_info["symbol"]
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol}: ${current_price:.6f} | Target: ${TARGET_PRICE}")
            
            # Check if price reached target and alert not sent yet
            if current_price >= TARGET_PRICE and not alert_sent:
                print()
                print("🚀" * 20)
                print(f"TARGET REACHED! ${current_price:.6f} >= ${TARGET_PRICE}")
                print("🚀" * 20)
                print()
                
                if send_pushover_alert(token_info):
                    alert_sent = True
                    print("Script completed. Alert sent successfully!")
                    break  # Exit after one-time alert
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Could not fetch price, retrying...")
        
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
