import tweepy
import requests
import os

client = tweepy.Client(
    consumer_key=os.environ['TWITTER_API_KEY'],
    consumer_secret=os.environ['TWITTER_API_SECRET'],
    access_token=os.environ['TWITTER_ACCESS_TOKEN'],
    access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET']
)

COINS = {
    'bitcoin':      ('BTC', '₿'),
    'ethereum':     ('ETH', 'Ξ'),
    'solana':       ('SOL', '◎'),
    'binancecoin':  ('BNB', '🔶'),
    'ripple':       ('XRP', '💧'),
}
COIN_NAMES = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binance',
    'XRP': 'ripple',
}

def get_prices():
    ids = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH',
        'solana': 'SOL',
        'binance-coin': 'BNB',
        'xrp': 'XRP',
    }
    result = {}
    try:
        url = 'https://api.coincap.io/v2/assets'
        params = {'ids': ','.join(ids.keys())}
        data = requests.get(url, params=params, timeout=10).json()
        for asset in data.get('data', []):
            coin_id = asset['id']
            if coin_id in ids:
                ticker = ids[coin_id]
                result[ticker] = {
                    'usd': float(asset.get('priceUsd', 0)),
                    'usd_24h_change': float(asset.get('changePercent24Hr', 0))
                }
    except Exception as e:
        print(f'Price fetch error: {e}')
    return result

def get_news(ticker):
    feeds = {
        'BTC': 'https://feeds.feedburner.com/CoinDesk',
        'ETH': 'https://feeds.feedburner.com/CoinDesk',
        'SOL': 'https://feeds.feedburner.com/CoinDesk',
        'BNB': 'https://feeds.feedburner.com/CoinDesk',
        'XRP': 'https://feeds.feedburner.com/CoinDesk',
    }
    try:
        import xml.etree.ElementTree as ET
        url = feeds.get(ticker, 'https://feeds.feedburner.com/CoinDesk')
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        for item in items:
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = (title + ' ' + item.findtext('description', '')).lower()
            if ticker.lower() in desc or COIN_NAMES.get(ticker, '').lower() in desc:
                return title, link
        if items:
            return items[0].findtext('title', ''), items[0].findtext('link', '')
    except:
        pass
    return '', ''

def format_change(change):
    if change is None:
        return '—'
    icon = '🟢' if change >= 0 else '🔴'
    return f'{icon} {change:+.1f}%'

def build_tweet(coin_id, ticker, emoji, price_data):
    price = price_data.get('usd', 0)
    change = price_data.get('usd_24h_change')
    price_str = f'${price:,.2f}' if price < 1000 else f'${price:,.0f}'

    headline, link = get_news(ticker)

    tweet = f'{emoji} #{ticker} — {price_str}\n24h: {format_change(change)}\n\n'

    if headline and link:
        max_len = 275 - len(tweet) - len(link) - 5
        if len(headline) > max_len:
            headline = headline[:max_len] + '...'
        tweet += f'📰 "{headline}"\n{link}'

    return tweet

def main():
    prices = get_prices()
    for coin_id, (ticker, emoji) in COINS.items():
        if coin_id in prices:
            tweet = build_tweet(coin_id, ticker, emoji, prices[coin_id])
            try:
                client.create_tweet(text=tweet)
                print(f'✅ Tweeted {ticker}')
            except Exception as e:
                print(f'❌ {ticker} failed: {e}')

if __name__ == '__main__':
    main()
