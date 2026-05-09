import os
import time
import requests
import feedparser
from datetime import datetime, timezone

TELEGRAM_TOKEN   = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

ALL_COINS = [
    {'id': 'bitcoin',          'ticker': 'BTC',  'name': 'bitcoin',   'emoji': '₿'},
    {'id': 'ethereum',         'ticker': 'ETH',  'name': 'ethereum',  'emoji': 'Ξ'},
    {'id': 'solana',           'ticker': 'SOL',  'name': 'solana',    'emoji': '◎'},
    {'id': 'binancecoin',      'ticker': 'BNB',  'name': 'BNB',       'emoji': '🔶'},
    {'id': 'ripple',           'ticker': 'XRP',  'name': 'XRP',       'emoji': '💧'},
    {'id': 'dogecoin',         'ticker': 'DOGE', 'name': 'dogecoin',  'emoji': '🐶'},
    {'id': 'avalanche-2',      'ticker': 'AVAX', 'name': 'avalanche', 'emoji': '🔺'},
    {'id': 'chainlink',        'ticker': 'LINK', 'name': 'chainlink', 'emoji': '🔗'},
    {'id': 'polkadot',         'ticker': 'DOT',  'name': 'polkadot',  'emoji': '⚫'},
    {'id': 'matic-network',    'ticker': 'POL',  'name': 'polygon',   'emoji': '🟣'},
    {'id': 'sui',              'ticker': 'SUI',  'name': 'sui',       'emoji': '💧'},
    {'id': 'the-open-network', 'ticker': 'TON',  'name': 'toncoin',   'emoji': '💎'},
    {'id': 'near',             'ticker': 'NEAR', 'name': 'near',      'emoji': '🌐'},
    {'id': 'shiba-inu',        'ticker': 'SHIB', 'name': 'shiba',     'emoji': '🐕'},
    {'id': 'pepe',             'ticker': 'PEPE', 'name': 'pepe',      'emoji': '🐸'},
    {'id': 'floki',            'ticker': 'FLOKI','name': 'floki',     'emoji': '⚡'},
    {'id': 'dogwifcoin',       'ticker': 'WIF',  'name': 'dogwifhat', 'emoji': '🎩'},
    {'id': 'bonk',             'ticker': 'BONK', 'name': 'bonk',      'emoji': '🔨'},
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
    ids = ','.join(c['id'] for c in ALL_COINS)
    return get_with_retry('https://api.coingecko.com/api/v3/coins/markets', {
        'vs_currency': 'usd', 'ids': ids,
        'price_change_percentage': '7d', 'sparkline': 'false'
    })

def get_fear_greed():
    try:
        r = requests.get('https://api.alternative.me/fng/?limit=7', timeout=10)
        return r.json()['data']   # list of 7 days, index 0 = today
    except Exception as e:
        print(f"Fear & Greed fetch failed: {e}")
        return []

def get_top_news(count=3):
    try:
        feed = feedparser.parse('https://www.coindesk.com/arc/outboundfeeds/rss/')
        return [{'title': e.title, 'link': e.link} for e in feed.entries[:count]]
    except:
        return []

def send_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    r = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'disable_web_page_preview': True})
    print(f"Telegram: {r.status_code}")

def main():
    data = get_prices()
    fng_week = get_fear_greed()
    news     = get_top_news()

    # Map coin id → market data
    info_map = {c['id']: c for c in ALL_COINS}
    enriched = []
    for coin in data:
        chg7 = float(coin.get('price_change_percentage_7d_in_currency') or 0)
        enriched.append({
            'id':     coin['id'],
            'ticker': info_map.get(coin['id'], {}).get('ticker', coin['symbol'].upper()),
            'emoji':  info_map.get(coin['id'], {}).get('emoji', '🪙'),
            'price':  coin['current_price'] or 0,
            'chg7':   chg7,
            'mcap':   coin['market_cap'] or 0,
            'vol':    coin['total_volume'] or 0,
        })

    enriched.sort(key=lambda x: x['chg7'], reverse=True)
    top     = enriched[0]
    worst   = enriched[-1]
    # Most volatile = largest absolute 7d change
    most_vol = max(enriched, key=lambda x: abs(x['chg7']))

    def arrow(v): return '🟢' if v >= 0 else '🔴'
    def sign(v):  return '+' if v >= 0 else ''

    week_str = datetime.now(timezone.utc).strftime('Week of %b %d, %Y')

    # Fear & Greed summary
    if fng_week:
        today_fng  = fng_week[0]
        fng_val    = int(today_fng['value'])
        fng_cls    = today_fng['value_classification']
        fng_emoji  = '😱' if fng_val < 25 else '😨' if fng_val < 45 else '😐' if fng_val < 55 else '😏' if fng_val < 75 else '🤑'
        fng_line   = f"\n{fng_emoji} Fear & Greed: {fng_val} — {fng_cls}"
        if len(fng_week) >= 7:
            week_avg = sum(int(d['value']) for d in fng_week) / len(fng_week)
            fng_line += f" (7d avg: {week_avg:.0f})"
    else:
        fng_line = ""

    # Top movers block
    top5_gainers = enriched[:5]
    top5_losers  = enriched[-5:][::-1]

    gainers_block = '\n'.join(
        f"  {c['emoji']} #{c['ticker']} {sign(c['chg7'])}{c['chg7']:.1f}%" for c in top5_gainers
    )
    losers_block = '\n'.join(
        f"  {c['emoji']} #{c['ticker']} {sign(c['chg7'])}{c['chg7']:.1f}%" for c in top5_losers
    )

    # News block
    news_block = '\n'.join(f"  📰 {n['title']}\n     {n['link']}" for n in news)

    message = (
        f"📅 WEEKLY CRYPTO RECAP — {week_str}\n"
        f"{'─'*40}\n\n"
        f"🏆 Top Gainer: {top['emoji']} #{top['ticker']} {sign(top['chg7'])}{top['chg7']:.1f}%\n"
        f"💀 Worst Performer: {worst['emoji']} #{worst['ticker']} {sign(worst['chg7'])}{worst['chg7']:.1f}%\n"
        f"🎢 Most Volatile: {most_vol['emoji']} #{most_vol['ticker']} {sign(most_vol['chg7'])}{most_vol['chg7']:.1f}%"
        f"{fng_line}\n\n"
        f"📈 Top 5 This Week:\n{gainers_block}\n\n"
        f"📉 Bottom 5 This Week:\n{losers_block}\n\n"
        f"📰 Top Stories:\n{news_block}\n\n"
        f"👉 Full dashboard: https://ian-vizcarrrondo.github.io/crypto-tweet-bot/"
    )

    send_message(message)

if __name__ == '__main__':
    main()
