import os
import requests

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
MAIN_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
MEME_CHAT_ID = os.environ['TELEGRAM_MEMECOIN_CHAT_ID']
THRESHOLD = 5.0

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

def get_prices(coin_ids):
    ids = ','.join(coin_ids)
    r = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
        'vs_currency': 'usd',
        'ids': ids,
        'price_change_percentage': '1h'
    })
    return r.json()

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={
        'chat_id': chat_id,
        'text': text,
        'disable_web_page_preview': True
    })

def check_and_alert(coin_ids, chat_id, header):
    data = get_prices(coin_ids)
    alerts = []
    for coin in data:
        change_1h = coin.get('price_change_percentage_1h_in_currency') or 0
        if abs(change_1h) >= THRESHOLD:
            label = LABELS.get(coin['id'], coin['id'])
            price = coin['current_price']
            arrow = '🚨🟢' if change_1h >= 0 else '🚨🔴'
            sign = '+' if change_1h >= 0 else ''
            alerts.append(f"{arrow} {label} — ${price:,.4f}\n1h move: {sign}{change_1h:.1f}%")

    if alerts:
        message = f"{header}\n\n" + '\n\n'.join(alerts)
        send_message(chat_id, message)
        print(f"Alert sent to {chat_id}")
    else:
        print("No drastic moves detected.")

def main():
    check_and_alert(MAIN_COINS, MAIN_CHAT_ID, "⚡ PRICE ALERT ⚡")
    check_and_alert(MEME_COINS, MEME_CHAT_ID, "🚀 MEME ALERT 🚀")

if __name__ == '__main__':
    main()
