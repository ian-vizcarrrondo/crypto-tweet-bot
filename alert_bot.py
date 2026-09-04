import os
import json
import time
import requests

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
MAIN_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
MEME_CHAT_ID = os.environ['TELEGRAM_MEMECOIN_CHAT_ID']
TRIGGER_THRESHOLD = 5.0
RESET_THRESHOLD = 4.0
STATE_FILE = 'cooldown.json'

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
    if price >= 1000:
        return f'${price:,.2f}'
    if price >= 1:
        return f'${price:.4f}'
    if price >= 0.01:
        return f'${price:.5f}'
    if price >= 0.0001:
        return f'${price:.7f}'
    return f'${price:.10f}'


def get_with_retry(url, params, retries=4, backoff=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 429:
                wait = backoff * (2 ** attempt)
                print(f"Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = backoff * (2 ** attempt)
            print(f"Request failed ({exc}). Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"All {retries} retries failed for {url}")


def get_prices(coin_ids):
    return get_with_retry('https://api.coingecko.com/api/v3/coins/markets', {
        'vs_currency': 'usd',
        'ids': ','.join(coin_ids),
        'price_change_percentage': '1h,24h'
    })


def load_state():
    try:
        with open(STATE_FILE) as state_file:
            state = json.load(state_file)
            return state if isinstance(state, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    with open(STATE_FILE, 'w') as state_file:
        json.dump(state, state_file, indent=2, sort_keys=True)
        state_file.write('\n')


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    response = requests.post(url, data={
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': True
    }, timeout=15)
    response.raise_for_status()
    print(f"Telegram accepted alert: {response.status_code}")


def check_and_alert(coin_ids, chat_id, header, state, channel_key):
    data = get_prices(coin_ids)
    alerts = []
    pending_state = {}

    for coin in data:
        coin_id = coin['id']
        state_key = f'{channel_key}:{coin_id}'
        change_1h = float(coin.get('price_change_percentage_1h_in_currency') or 0)
        change_24h = float(coin.get('price_change_percentage_24h_in_currency') or 0)

        # Re-arm only after the move settles below the reset threshold.
        if abs(change_1h) < RESET_THRESHOLD:
            state.pop(state_key, None)
            continue

        if abs(change_1h) < TRIGGER_THRESHOLD:
            continue

        direction = 'up' if change_1h > 0 else 'down'
        previous = state.get(state_key)
        if isinstance(previous, dict) and previous.get('direction') == direction:
            print(f"Skipping {coin_id} — continuous {direction} move already alerted.")
            continue

        label = LABELS.get(coin_id, coin_id)
        price = coin['current_price'] or 0
        arrow = '🚨🟢' if change_1h >= 0 else '🚨🔴'
        sign_1h = '+' if change_1h >= 0 else ''
        sign_24h = '+' if change_24h >= 0 else ''
        alerts.append(
            f"{arrow} {label} — {format_price(price)}\n"
            f"1h: {sign_1h}{change_1h:.1f}%  |  24h: {sign_24h}{change_24h:.1f}%"
        )
        pending_state[state_key] = {
            'direction': direction,
            'triggered_at': int(time.time())
        }

    if not alerts:
        print(f"No new {channel_key} alerts triggered.")
        return

    send_message(chat_id, f"{header}\n\n" + '\n\n'.join(alerts))
    state.update(pending_state)
    print(f"Alert sent for {len(alerts)} coin(s).")


def main():
    state = load_state()
    check_and_alert(MAIN_COINS, MAIN_CHAT_ID, "⚡ PRICE ALERT ⚡", state, 'main')

    meme_coins = MEME_COINS
    if MEME_CHAT_ID == MAIN_CHAT_ID:
        meme_coins = [coin for coin in MEME_COINS if coin not in MAIN_COINS]
    check_and_alert(meme_coins, MEME_CHAT_ID, "🚀 MEME ALERT 🚀", state, 'meme')

    save_state(state)


if __name__ == '__main__':
    main()
