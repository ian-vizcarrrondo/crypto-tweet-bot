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

def get_prices():
    ids = ','.join(COINS.keys())
    url = (
        f'https://api.coingecko.com/api/v3/simple/price'
        f'?ids={ids}&vs_currencies=usd&include_24hr_change=true'
    )
    return requests.get(url).json()

def get_news(ticker):
    token = os.environ['CRYPTOPANIC_TOKEN']
    url = (
        f'https://cryptopanic.com/api/v1/posts/'
        f'?auth_token={token}&currencies={ticker}&filter=hot&limit=1'
    )
    data = requests.get(url).json()
    results = data.get('results', [])
    if results:
        return results[0].get('title', ''), results[0].get('url', '')
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
