import tweepy
import requests
import os
import xml.etree.ElementTree as ET

client = tweepy.Client(
    consumer_key=os.environ['TWITTER_API_KEY'],
    consumer_secret=os.environ['TWITTER_API_SECRET'],
    access_token=os.environ['TWITTER_ACCESS_TOKEN'],
    access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET']
)

COINS = [
    ('BTC', '₿'),
    ('ETH', 'Ξ'),
    ('SOL', '◎'),
    ('BNB', '🔶'),
    ('XRP', '💧'),
]

BINANCE_SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'SOL': 'SOLUSDT',
    'BNB': 'BNBUSDT',
    'XRP': 'XRPUSDT',
}

COIN_NAMES = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binance',
    'XRP': 'ripple',
}

def get_price(ticker):
    try:
        symbol = BINANCE_SYMBOLS.get(ticker)
        url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
        data = requests.get(url, timeout=10).json()
        return {
            'usd': float(data.get('lastPrice', 0)),
            'usd_24h_change': float(data.get('priceChangePercent', 0))
        }
    except Exception as e:
        print(f'Price error for {ticker}: {e}')
        return None

def get_news(ticker):
    try:
        url = 'https://feeds.feedburner.com/CoinDesk'
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        keyword = COIN_NAMES.get(ticker, ticker).lower()
        for item in items:
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            if keyword in title.lower() or ticker.lower() in title.lower():
                return title, link
        if items:
            return items[0].findtext('title', ''), items[0].findtext('link', '')
    except Exception as e:
        print(f'News error: {e}')
    return '', ''

def format_change(change):
    if change is None:
        return '—'
    icon = '🟢' if change >= 0 else '🔴'
    return f'{icon} {change:+.1f}%'

def main():
    for ticker, emoji in COINS:
        print(f'Processing {ticker}...')
        price_data = get_price(ticker)
        if not price_data:
            print(f'⚠️ No price data for {ticker}')
            continue

        price = price_data['usd']
        change = price_data['usd_24h_change']
        price_str = f'${price:,.2f}' if price < 1000 else f'${price:,.0f}'

        headline, link = get_news(ticker)

        tweet = f'{emoji} #{ticker} — {price_str}\n24h: {format_change(change)}\n\n'

        if headline and link:
            max_len = 275 - len(tweet) - len(link) - 5
            if len(headline) > max_len:
                headline = headline[:max_len] + '...'
            tweet += f'📰 "{headline}"\n{link}'

        print(f'Tweet preview: {tweet[:60]}...')

        try:
            client.create_tweet(text=tweet)
            print(f'✅ Tweeted {ticker}')
        except Exception as e:
            print(f'❌ {ticker} failed: {e}')

if __name__ == '__main__':
    main()
