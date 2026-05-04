import requests
import feedparser

TELEGRAM_TOKEN = __import__('os').environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = __import__('os').environ['TELEGRAM_CHAT_ID']

COINS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
SYMBOLS = {'BTCUSDT': '₿ #BTC', 'ETHUSDT': 'Ξ #ETH', 'SOLUSDT': '◎ #SOL', 'BNBUSDT': '🔶 #BNB', 'XRPUSDT': '💧 #XRP'}

def get_prices():
    results = []
    for coin in COINS:
        url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={coin}'
        r = requests.get(url)
        results.append(r.json())
    return results

def get_news():
    feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
    entry = feed.entries[0]
    return entry.title, entry.link

def send_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'disable_web_page_preview': True})

def main():
    prices = get_prices()
    lines = []
    for coin in prices:
        symbol = SYMBOLS[coin['symbol']]
        price = float(coin['lastPrice'])
        change = float(coin['priceChangePercent'])
        arrow = '🟢' if change >= 0 else '🔴'
        sign = '+' if change >= 0 else ''
        lines.append(f"{symbol} — ${price:,.2f}\n24h: {arrow} {sign}{change:.1f}%")
    
    title, link = get_news()
    news_line = f"\n📰 {title}\n{link}"
    
    message = '\n\n'.join(lines) + '\n' + news_line
    send_message(message)

if __name__ == '__main__':
    main()
