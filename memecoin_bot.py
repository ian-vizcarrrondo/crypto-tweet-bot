import os
import time
import requests
import feedparser

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_MEMECOIN_CHAT_ID']

COINS = [
    {'id': 'dogecoin',      'label': '🐶 #DOGE',  'ticker': 'DOGE', 'name': 'dogecoin'},
    {'id': 'shiba-inu',     'label': '🐕 #SHIB',  'ticker': 'SHIB', 'name': 'shiba'},
    {'id': 'pepe',          'label': '🐸 #PEPE',  'ticker': 'PEPE', 'name': 'pepe'},
    {'id': 'floki',         'label': '⚡ #FLOKI', 'ticker': 'FLOKI','name': 'floki'},
    {'id': 'dogwifcoin',    'label': '🎩 #WIF',   'ticker': 'WIF',  'name': 'dogwifhat'},
    {'id': 'bonk',          'label': '🔨 #BONK',  'ticker': 'BONK', 'name': 'bonk'},
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

def get_prices():
    ids = ','.join(c['id'] for c in COINS)
    return get_with_retry('https://api.coingecko.com/api/v3/simple/price', {
        'ids': ids,
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    })

def get_news_for_coin(ticker, name):
    feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
    search_terms = [ticker.lower(), name.lower(), 'meme', 'memecoin']
    for entry in feed.entries[:20]:
        title_lower = entry.title.lower()
        if any(term in title_lower for term in search_terms):
            return entry.title, entry.link
    return feed.entries[0].title, feed.entries[0].link

def send_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    r = requests.post(url, data={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'disable_web_page_preview': True
    })
    print(f"Telegram response: {r.status_code} — {r.text}")

def main():
    prices = get_prices()
    lines = []
    top_gainer = None
    top_change = -999

    for coin in COINS:
        data = prices.get(coin['id'], {})
        price = data.get('usd', 0)
        change = data.get('usd_24h_change', 0)
        arrow = '🟢' if change >= 0 else '🔴'
        sign = '+' if change >= 0 else ''
        lines.append(f"{coin['label']} — ${price:,.6f}\n24h: {arrow} {sign}{change:.1f}%")
        if change > top_change:
            top_change = change
            top_gainer = coin

    title, link = get_news_for_coin(top_gainer['ticker'], top_gainer['name'])
    sign = '+' if top_change >= 0 else ''
    news_line = f"\n🚀 Hot meme: {top_gainer['label']} ({sign}{top_change:.1f}%)\n{title}\n{link}"

    message = '🐸 MEME MARKET UPDATE 🐸\n\n' + '\n\n'.join(lines) + '\n' + news_line
    send_message(message)

if __name__ == '__main__':
    main()
