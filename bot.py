import os
import json
import time
import requests
import feedparser
from datetime import datetime, timezone

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

MAIN_COINS = [
    {'id': 'bitcoin',       'label': '₿ #BTC',   'ticker': 'BTC',  'name': 'bitcoin',   'emoji': '₿'},
    {'id': 'ethereum',      'label': 'Ξ #ETH',   'ticker': 'ETH',  'name': 'ethereum',  'emoji': 'Ξ'},
    {'id': 'solana',        'label': '◎ #SOL',   'ticker': 'SOL',  'name': 'solana',    'emoji': '◎'},
    {'id': 'binancecoin',   'label': '🔶 #BNB',  'ticker': 'BNB',  'name': 'BNB',       'emoji': '🔶'},
    {'id': 'ripple',        'label': '💧 #XRP',  'ticker': 'XRP',  'name': 'XRP',       'emoji': '💧'},
    {'id': 'dogecoin',      'label': '🐶 #DOGE', 'ticker': 'DOGE', 'name': 'dogecoin',  'emoji': '🐶'},
    {'id': 'avalanche-2',   'label': '🔺 #AVAX', 'ticker': 'AVAX', 'name': 'avalanche', 'emoji': '🔺'},
    {'id': 'chainlink',     'label': '🔗 #LINK', 'ticker': 'LINK', 'name': 'chainlink', 'emoji': '🔗'},
    {'id': 'polkadot',      'label': '⚫ #DOT',  'ticker': 'DOT',  'name': 'polkadot',  'emoji': '⚫'},
    {'id': 'render-token',     'label': '🎨 #RNDR', 'ticker': 'RNDR', 'name': 'render',    'emoji': '🎨'},
    {'id': 'sui',              'label': '💧 #SUI',  'ticker': 'SUI',  'name': 'sui',       'emoji': '💧'},
    {'id': 'the-open-network', 'label': '💎 #TON',  'ticker': 'TON',  'name': 'toncoin',   'emoji': '💎'},
    {'id': 'near',             'label': '🌐 #NEAR', 'ticker': 'NEAR', 'name': 'near',      'emoji': '🌐'},
]

MEME_COINS = [
    {'id': 'dogecoin',   'label': '🐶 #DOGE',  'ticker': 'DOGE', 'name': 'dogecoin',  'emoji': '🐶'},
    {'id': 'shiba-inu',  'label': '🐕 #SHIB',  'ticker': 'SHIB', 'name': 'shiba',     'emoji': '🐕'},
    {'id': 'pepe',       'label': '🐸 #PEPE',  'ticker': 'PEPE', 'name': 'pepe',      'emoji': '🐸'},
    {'id': 'floki',      'label': '⚡ #FLOKI', 'ticker': 'FLOKI','name': 'floki',     'emoji': '⚡'},
    {'id': 'dogwifcoin', 'label': '🎩 #WIF',   'ticker': 'WIF',  'name': 'dogwifhat', 'emoji': '🎩'},
    {'id': 'bonk',       'label': '🔨 #BONK',  'ticker': 'BONK', 'name': 'bonk',      'emoji': '🔨'},
]

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

def get_prices(coins):
    ids = ','.join(c['id'] for c in coins)
    return get_with_retry('https://api.coingecko.com/api/v3/coins/markets', {
        'vs_currency': 'usd', 'ids': ids,
        'price_change_percentage': '1h,24h,7d', 'sparkline': 'true'
    })

def get_fear_greed():
    try:
        r = requests.get('https://api.alternative.me/fng/', timeout=10)
        return r.json()['data'][0]
    except Exception as e:
        print(f"Fear & Greed fetch failed: {e}")
        return None

def get_news(count=6):
    try:
        feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
        news = []
        for entry in feed.entries[:count]:
            news.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', '')
            })
        return news
    except:
        return []

def get_news_for_coin(ticker, name):
    feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
    for entry in feed.entries[:20]:
        if ticker.lower() in entry.title.lower() or name.lower() in entry.title.lower():
            return entry.title, entry.link
    return feed.entries[0].title, feed.entries[0].link

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    r = requests.post(url, data={'chat_id': chat_id, 'text': text, 'disable_web_page_preview': True})
    print(f"Telegram: {r.status_code}")

def write_json(main_data, meme_data, fng, news):
    def format_coin(coin, info):
        return {
            'id': coin['id'],
            'name': coin['name'],
            'symbol': coin['symbol'].upper(),
            'emoji': info['emoji'],
            'price': coin['current_price'] or 0,
            'change_1h':  float(coin.get('price_change_percentage_1h_in_currency') or 0),
            'change_24h': float(coin.get('price_change_percentage_24h_in_currency') or 0),
            'change_7d':  float(coin.get('price_change_percentage_7d_in_currency') or 0),
            'ath_change_pct': float(coin.get('ath_change_percentage') or 0),
            'market_cap': coin['market_cap'] or 0,
            'volume_24h': coin['total_volume'] or 0,
            'sparkline':  coin.get('sparkline_in_7d', {}).get('price', [])
        }

    info_map = {c['id']: c for c in MAIN_COINS + MEME_COINS}
    output = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'fear_greed': fng,
        'news': news,
        'main_coins': [format_coin(c, info_map[c['id']]) for c in main_data if c['id'] in info_map],
        'meme_coins': [format_coin(c, info_map[c['id']]) for c in meme_data if c['id'] in info_map],
    }
    with open('prices.json', 'w') as f:
        json.dump(output, f)
    print("prices.json written")

def main():
    main_data = get_prices(MAIN_COINS)
    meme_data = get_prices(MEME_COINS)
    fng = get_fear_greed()
    news = get_news()

    write_json(main_data, meme_data, fng, news)

    top = max(main_data, key=lambda x: float(x.get('price_change_percentage_24h_in_currency') or 0))
    top_info = next(c for c in MAIN_COINS if c['id'] == top['id'])

    lines = []
    for info in MAIN_COINS:
        coin = next((c for c in main_data if c['id'] == info['id']), None)
        if not coin: continue
        price  = coin['current_price'] or 0
        change = float(coin.get('price_change_percentage_24h_in_currency') or 0)
        arrow  = '🟢' if change >= 0 else '🔴'
        sign   = '+' if change >= 0 else ''
        lines.append(f"{info['label']} — ${price:,.2f}\n24h: {arrow} {sign}{change:.1f}%")

    title, link = get_news_for_coin(top_info['ticker'], top_info['name'])
    top_change = float(top.get('price_change_percentage_24h_in_currency') or 0)
    sign = '+' if top_change >= 0 else ''
    news_line = f"\n📰 Top mover: {top_info['label']} ({sign}{top_change:.1f}%)\n{title}\n{link}"

    send_message(TELEGRAM_CHAT_ID, '\n\n'.join(lines) + '\n' + news_line)

if __name__ == '__main__':
    main()
