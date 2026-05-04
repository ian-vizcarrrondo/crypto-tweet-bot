import os
import requests
import feedparser

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

COINS = {
    'bitcoin':      '₿ #BTC',
    'ethereum':     'Ξ #ETH',
    'solana':       '◎ #SOL',
    'binancecoin':  '🔶 #BNB',
    'ripple':       '💧 #XRP'
}

def get_prices():
    ids = ','.join(COINS.keys())
    url = 'https://api.coingecko.com/api/v3/simple/price'
    r = requests.get(url, params={
        'ids': ids,
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    })
    return r.json()

def get_news():
    feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
    entry = feed.entries[0]
    return entry.title, entry.link

def send_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'disable_web_page_preview': True
    })

def main():
    prices = get_prices()
    lines = []
    for coin_id, label in COINS.items():
        data = prices[coin_id]
        price = data['usd']
        change = data['usd_24h_change']
        arrow = '🟢' if change >= 0 else '🔴'
        sign = '+' if change >= 0 else ''
        lines.append(f"{label} — ${price:,.2f}\n24h: {arrow} {sign}{change:.1f}%")

    title, link = get_news()
    news_line = f"\n📰 {title}\n{link}"

    message = '\n\n'.join(lines) + '\n' + news_line
    send_message(message)

if __name__ == '__main__':
    main()
