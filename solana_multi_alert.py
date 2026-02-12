#!/usr/bin/env python3
"""
Solana Multi-Token Price Alert with Pushover Notification
Monitors multiple meme tokens and sends SIREN alerts when targets are reached.
Easy to add/remove/edit tokens!
"""

import os
import time
import requests
from datetime import datetime

# ============ PUSHOVER CONFIGURATION ============
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "YOUR_PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "YOUR_PUSHOVER_API_TOKEN")

# ============ TOKENS TO MONITOR ============
# Format: "TOKEN_ADDRESS": {"target": TARGET_PRICE, "direction": "above" or "below", "name": "optional nickname"}
#
# direction:
#   "above" - alert when price >= target (for moon alerts 🚀)
#   "below" - alert when price <= target (for buy-the-dip alerts 📉)
#
# Додавай/видаляй/редагуй токени тут:

TOKENS = {
    # Приклад 1: Alert коли ціна вище $0.03
    "Cm6fNnMk7NfzStP9CZpsQA2v3jjzbcYGAxdJySmHpump": {
        "target": 0.027,
        "direction": "above",
        "name": "MyMemeCoin"  # опціонально, для зручності
    },
    
    # Приклад 2: Розкоментуй і додай інший токен
    # "ANOTHER_TOKEN_ADDRESS_HERE": {
    #     "target": 0.001,
    #     "direction": "above",
    #     "name": "AnotherCoin"
    # },
    
    # Приклад 3: Alert коли ціна падає нижче (для купівлі діпа)
    # "DIP_TOKEN_ADDRESS_HERE": {
    #     "target": 0.05,
    #     "direction": "below",
    #     "name": "BuyTheDip"
    # },
}

# ============ SETTINGS ============
CHECK_INTERVAL = 30  # seconds between checks

# =========================================

# Track which alerts have been sent (to avoid spam)
alerts_sent = set()


def get_token_price(token_address):
    """Fetch current token price from DexScreener API"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("pairs") and len(data["pairs"]) > 0:
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
        print(f"  ⚠️ Error fetching {token_address[:10]}...: {e}")
        return None


def send_pushover_alert(token_info, config, direction_text):
    """Send emergency priority notification with SIREN sound"""
    url = "https://api.pushover.net/1/messages.json"
    
    emoji = "🚀" if config["direction"] == "above" else "📉"
    
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": f"{emoji} {token_info['symbol']} {direction_text} ${config['target']}!\n\nПоточна ціна: ${token_info['price']:.6f}\nЧас: {datetime.now().strftime('%H:%M:%S')}",
        "title": f"{emoji} PRICE ALERT: {token_info['symbol']}",
        "sound": "siren",
        "priority": 2,  # Emergency - repeats until acknowledged
        "retry": 30,
        "expire": 3600,
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"  ✅ ALERT SENT for {token_info['symbol']}!")
        return True
    except Exception as e:
        print(f"  ❌ Error sending alert: {e}")
        return False


def check_price_condition(price, config):
    """Check if price meets the target condition"""
    if config["direction"] == "above":
        return price >= config["target"]
    else:  # below
        return price <= config["target"]


def main():
    print("=" * 60)
    print("🔍 Solana Multi-Token Price Monitor")
    print("=" * 60)
    print(f"Monitoring {len(TOKENS)} token(s)")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print("-" * 60)
    
    for addr, config in TOKENS.items():
        name = config.get("name", addr[:10] + "...")
        direction = "≥" if config["direction"] == "above" else "≤"
        print(f"  • {name}: {direction} ${config['target']}")
    
    print("=" * 60)
    print()
    
    while True:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] Checking prices...")
        
        all_alerted = True
        
        for token_address, config in TOKENS.items():
            # Skip if alert already sent for this token
            if token_address in alerts_sent:
                continue
            
            all_alerted = False
            token_info = get_token_price(token_address)
            
            if token_info:
                name = config.get("name", token_info["symbol"])
                current_price = token_info["price"]
                target = config["target"]
                direction = config["direction"]
                
                # Show current status
                if direction == "above":
                    progress = (current_price / target) * 100 if target > 0 else 0
                    print(f"  {name}: ${current_price:.6f} | Target: ≥${target} ({progress:.1f}%)")
                else:
                    print(f"  {name}: ${current_price:.6f} | Target: ≤${target}")
                
                # Check if condition is met
                if check_price_condition(current_price, config):
                    print()
                    print("🚨" * 20)
                    direction_text = "досягнув" if direction == "above" else "впав до"
                    print(f"  TARGET REACHED: {name} {direction_text} ${target}!")
                    print("🚨" * 20)
                    print()
                    
                    if send_pushover_alert(token_info, config, direction_text):
                        alerts_sent.add(token_address)
        
        # If all tokens have been alerted, exit
        if all_alerted and len(TOKENS) > 0:
            print()
            print("✅ All alerts have been sent! Exiting...")
            break
        
        print()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
