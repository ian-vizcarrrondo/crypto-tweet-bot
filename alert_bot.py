import os
import json
import time
import requests
from datetime import datetime, timezone

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
MAIN_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
MEME_CHAT_ID = os.environ['TELEGRAM_MEMECOIN_CHAT_ID']
THRESHOLD = 5.0
COOLDOWN_FILE = 'cooldown.json'
COOLDOWN_SECONDS = 3600  # 1 hour per coin

MAIN_COINS = [
    'bitcoin', 'ethereum', 'solana', 'binancecoin', 'ripple',
    'dogecoin', 'avalanche-2', 'chainlink', 'polkadot', 'matic-network'
]

MEME_COINS = [
    'dogecoin', 'shiba-inu', 'pepe', 'floki', 'dogwifcoin', 'bonk'
]

LABELS = {
    'bitcoin': '₿ #BTC', 'ethereum': 'Ξ #ETH', 'solana': '◎ #SOL',
    'binancecoin': '🔶 #BNB', 'ripple': '💧 #XRP', 'dogecoin': '🐶 #DOGE',
    'avalanche-2': '🔺 #AVAX', 'chainlink': '🔗 #LINK', 'polkadot': '⚫ #DOT',
    'matic-network': '🟣 #POL', 'shiba-inu': '🐕 #SHIB', 'pepe': '🐸 #PEPE',
    'floki': '⚡ #FLOKI', 'dogwifcoin': '🎩 #WIF', 'bonk': '🔨 #BONK'
}

def format_price(price):
    """Smart price formatting based on magnitude."""
    if price >= 1000:
        return f'${price:,.2f}'
    elif price >= 1:
        return f'${price:.4f}'
    elif price >= 0.01:
        return f'${price:.5f}'
    elif price >= 0.0001:
        return f'${price:.7f}'
    else:
        return f'${price:.10f}'

def get_with_retry(url, params, retries=4, backoff=5):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 429:
                wait = backoff * (2 ** attempt)
                print(f"Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            wait = backoff * (2 ** attempt)
            print(f"Request failed ({e}). Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"All {retries} retries failed for {url}")

def get_prices(coin_ids):
    return get_with_retry('https://api.coingecko.com/api/v3/coins/markets', {
        'vs_currency': 'usd',
        'ids': ','.join(coin_ids),
        'price_change_percentage': '1h,24h'
    })

def load_cooldown():
    try:
        with open(COOLDOWN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cooldown(cooldown):
    with open(COOLDOWN_FILE, 'w') as f:
        json.dump(cooldown, f)

def is_on_cooldown(coin_id, cooldown):
    last_fired = cooldown.get(coin_id, 0)
    return (time.time() - last_fired) < COOLDOWN_SECONDS

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': True
    })

def check_and_alert(coin_ids, chat_id, header, cooldown):
    data = get_prices(coin_ids)
    alerts = []
    fired_ids = []

    for coin in data:
        cid = coin['id']
        change_1h = coin.get('price_change_percentage_1h_in_currency') or 0
        change_24h = coin.get('price_change_percentage_24h_in_currency') or 0

        if abs(change_1h) >= THRESHOLD:
            if is_on_cooldown(cid, cooldown):
                print(f"Skipping {cid} — on cooldown.")
                continue

            label = LABELS.get(cid, cid)
            price = coin['current_price'] or 0
            arrow = '🚨🟢' if change_1h >= 0 else '🚨🔴'
            sign_1h = '+' if change_1h >= 0 else ''
            sign_24h = '+' if change_24h >= 0 else ''
            alerts.append(
                f"{arrow} {label} — {format_price(price)}\n"
                f"1h: {sign_1h}{change_1h:.1f}%  |  24h: {sign_24h}{change_24h:.1f}%"
            )
            fired_ids.append(cid)

    if alerts:
        message = f"{header}\n\n" + '\n\n'.join(alerts)
        send_message(chat_id, message)
        print(f"Alert sent to {chat_id} for: {', '.join(fired_ids)}")
        now = time.time()
        for cid in fired_ids:
            cooldown[cid] = now
    else:
        print("No alerts triggered (or all on cooldown).")

def main():
    cooldown = load_cooldown()
    check_and_alert(MAIN_COINS, MAIN_CHAT_ID, "⚡ PRICE ALERT ⚡", cooldown)
    check_and_alert(MEME_COINS, MEME_CHAT_ID, "🚀 MEME ALERT 🚀", cooldown)
    save_cooldown(cooldown)

if __name__ == '__main__':
    main()
