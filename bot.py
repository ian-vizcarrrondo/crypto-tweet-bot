import os
import json
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
    {'id': 'matic-network', 'label': '🟣 #POL',  'ticker': 'POL',  'name': 'polygon',   'emoji': '🟣'},
]

MEME_COINS = [
    {'id': 'dogecoin',   'label': '🐶 #DOGE',  'ticker': 'DOGE', 'name': 'dogecoin',  'emoji': '🐶'},
    {'id': 'shiba-inu',  'label': '🐕 #SHIB',  'ticker': 'SHIB', 'name': 'shiba',     'emoji': '🐕'},
    {'id': 'pepe',       'label': '🐸 #PEPE',  'ticker': 'PEPE', 'name': 'pepe',      'emoji': '🐸'},
    {'id': 'floki',      'label': '⚡ #FLOKI', 'ticker': 'FLOKI','name': 'floki',     'emoji': '⚡'},
    {'id': 'dogwifcoin', 'label': '🎩 #WIF',   'ticker': 'WIF',  'name': 'dogwifhat', 'emoji': '🎩'},
    {'id': 'bonk',       'label': '🔨 #BONK',  'ticker': 'BONK', 'name': 'bonk',      'emoji': '🔨'},
]

COIN_CONTEXT = {
    'bitcoin': {
        'description': 'Bitcoin is the original decentralized digital asset, often tracked as a macro-sensitive store-of-value proxy and the liquidity anchor for crypto markets.',
        'bull_case': [
            'Deep liquidity and broad institutional awareness can make BTC the first stop when new capital enters crypto.',
            'Fixed issuance and recurring halving cycles keep supply dynamics central to the long-term narrative.',
            'Spot ETF flows, treasury adoption, and macro liquidity shifts can quickly change demand expectations.'
        ],
        'risk_notes': [
            'BTC can still trade like a high-volatility risk asset during leverage unwinds or macro shocks.',
            'Fee-market sustainability, regulatory headlines, and concentration of large holders remain watch items.'
        ],
        'catalysts': ['Spot ETF flow trends', 'Macro rate and liquidity expectations', 'Exchange reserve movements', 'Network fee activity'],
        'links': [
            {'label': 'Bitcoin.org', 'url': 'https://bitcoin.org/'},
            {'label': 'CoinGecko BTC', 'url': 'https://www.coingecko.com/en/coins/bitcoin'}
        ],
        'aliases': ['btc', 'bitcoin', 'satoshi', 'digital gold']
    },
    'ethereum': {
        'description': 'Ethereum is a smart-contract network used for DeFi, NFTs, stablecoins, tokenization, and many layer-2 ecosystems.',
        'bull_case': [
            'Application activity, stablecoin settlement, and layer-2 growth can support demand for blockspace.',
            'Protocol upgrades and scaling improvements may improve the user experience over time.',
            'ETH is watched for staking yield, ETF demand, and its role as collateral across DeFi.'
        ],
        'risk_notes': [
            'Competition from faster or cheaper chains can pressure activity and fees.',
            'Regulatory treatment, staking concentration, and bridge/security incidents can affect sentiment.'
        ],
        'catalysts': ['Layer-2 activity', 'Protocol upgrade milestones', 'ETF/staking headlines', 'DeFi total value locked'],
        'links': [
            {'label': 'Ethereum.org', 'url': 'https://ethereum.org/'},
            {'label': 'CoinGecko ETH', 'url': 'https://www.coingecko.com/en/coins/ethereum'}
        ],
        'aliases': ['eth', 'ethereum', 'ether', 'layer 2', 'layer-2']
    },
    'solana': {
        'description': 'Solana is a high-throughput smart-contract network known for low fees, consumer apps, DeFi, NFTs, and memecoin trading.',
        'bull_case': [
            'Fast settlement and low fees make Solana attractive for consumer-scale crypto applications.',
            'Developer and user activity can reinforce liquidity across DeFi, NFTs, and token launches.',
            'Mobile, payments, and DePIN experiments provide differentiated growth narratives.'
        ],
        'risk_notes': [
            'Network reliability, validator economics, and congestion events remain important risks to monitor.',
            'High memecoin activity can boost attention but can also reverse sharply when risk appetite fades.'
        ],
        'catalysts': ['Network uptime metrics', 'DEX volume', 'Mobile and payments adoption', 'Major ecosystem launches'],
        'links': [
            {'label': 'Solana.com', 'url': 'https://solana.com/'},
            {'label': 'CoinGecko SOL', 'url': 'https://www.coingecko.com/en/coins/solana'}
        ],
        'aliases': ['sol', 'solana']
    },
    'binancecoin': {
        'description': 'BNB is the native asset tied to the BNB Chain ecosystem and Binance-related utility, including fees and on-chain applications.',
        'bull_case': [
            'Large exchange distribution and active on-chain usage can keep BNB in focus for traders.',
            'Token burns and ecosystem incentives are common demand narratives.',
            'BNB Chain app launches can create bursts of network activity.'
        ],
        'risk_notes': [
            'Exchange-specific regulatory or operational headlines can affect sentiment quickly.',
            'Centralization concerns and smart-contract security incidents are recurring watch items.'
        ],
        'catalysts': ['BNB burn updates', 'Binance regulatory news', 'BNB Chain activity', 'Launchpool or ecosystem campaigns'],
        'links': [
            {'label': 'BNB Chain', 'url': 'https://www.bnbchain.org/'},
            {'label': 'CoinGecko BNB', 'url': 'https://www.coingecko.com/en/coins/bnb'}
        ],
        'aliases': ['bnb', 'binance', 'binance coin', 'bnb chain']
    },
    'ripple': {
        'description': 'XRP is associated with the XRP Ledger, a network often discussed around payments, liquidity, and cross-border settlement.',
        'bull_case': [
            'Payments and institutional settlement narratives can attract attention when partnerships or legal clarity improve.',
            'Fast settlement and low transaction costs are central to XRP Ledger positioning.',
            'Regulatory developments can materially change market expectations.'
        ],
        'risk_notes': [
            'Legal and regulatory headlines can dominate price action.',
            'Adoption claims should be separated from measurable on-chain usage and liquidity.'
        ],
        'catalysts': ['Ripple legal updates', 'Payments partnership news', 'XRPL activity', 'Liquidity and exchange listing changes'],
        'links': [
            {'label': 'XRPL.org', 'url': 'https://xrpl.org/'},
            {'label': 'CoinGecko XRP', 'url': 'https://www.coingecko.com/en/coins/xrp'}
        ],
        'aliases': ['xrp', 'ripple', 'xrpl', 'xrp ledger']
    },
    'dogecoin': {
        'description': 'Dogecoin is the original meme coin, followed for community momentum, payments experiments, and social-media-driven attention.',
        'bull_case': [
            'Large brand recognition and deep exchange support can make DOGE a high-beta sentiment gauge.',
            'Community activity and payment integrations can renew attention quickly.',
            'Meme cycles can create strong momentum when retail risk appetite is high.'
        ],
        'risk_notes': [
            'Meme-led rallies can reverse abruptly and may not be tied to fundamentals.',
            'Concentrated holders and social-media narratives can increase volatility.'
        ],
        'catalysts': ['Social trend spikes', 'Payments integration headlines', 'Meme-sector rotation', 'Large wallet movement'],
        'links': [
            {'label': 'Dogecoin.com', 'url': 'https://dogecoin.com/'},
            {'label': 'CoinGecko DOGE', 'url': 'https://www.coingecko.com/en/coins/dogecoin'}
        ],
        'aliases': ['doge', 'dogecoin', 'meme coin', 'memecoin']
    },
    'avalanche-2': {
        'description': 'Avalanche is a smart-contract platform focused on subnets, app-specific chains, DeFi, gaming, and institutional tokenization pilots.',
        'bull_case': [
            'Subnet architecture can appeal to teams that need customized execution environments.',
            'Enterprise, gaming, and tokenization pilots can broaden the ecosystem narrative.',
            'DeFi liquidity rebounds can support network usage and attention.'
        ],
        'risk_notes': [
            'Competition among layer-1 networks is intense and liquidity can be fragmented.',
            'Token unlocks, incentive changes, and bridge risks can affect market sentiment.'
        ],
        'catalysts': ['Subnet launches', 'Tokenization pilots', 'DeFi liquidity trends', 'Ecosystem incentive updates'],
        'links': [
            {'label': 'Avalanche', 'url': 'https://www.avax.network/'},
            {'label': 'CoinGecko AVAX', 'url': 'https://www.coingecko.com/en/coins/avalanche'}
        ],
        'aliases': ['avax', 'avalanche', 'subnet', 'subnets']
    },
    'chainlink': {
        'description': 'Chainlink provides oracle and interoperability infrastructure used by DeFi protocols and institutions that need external data or cross-chain messaging.',
        'bull_case': [
            'Oracles remain critical infrastructure for lending, derivatives, and tokenized assets.',
            'CCIP and institutional integrations can expand Chainlink beyond price feeds.',
            'Staking and service-fee narratives can improve perceived token utility.'
        ],
        'risk_notes': [
            'Token value capture depends on adoption, fee design, and staking economics.',
            'Oracle competition or protocol-specific failures could pressure confidence.'
        ],
        'catalysts': ['CCIP integrations', 'Oracle feed adoption', 'Staking updates', 'Tokenization partnership news'],
        'links': [
            {'label': 'Chain.link', 'url': 'https://chain.link/'},
            {'label': 'CoinGecko LINK', 'url': 'https://www.coingecko.com/en/coins/chainlink'}
        ],
        'aliases': ['link', 'chainlink', 'oracle', 'ccip']
    },
    'polkadot': {
        'description': 'Polkadot is a multi-chain network built around shared security, interoperability, and application-specific parachain ecosystems.',
        'bull_case': [
            'Shared security and cross-chain messaging can help specialized chains coordinate liquidity and users.',
            'Governance and treasury activity may fund ecosystem development over time.',
            'Technical upgrades can improve scalability and developer flexibility.'
        ],
        'risk_notes': [
            'Complex architecture can make user adoption and messaging harder versus simpler networks.',
            'Ecosystem liquidity and app traction need to remain visible to sustain attention.'
        ],
        'catalysts': ['Protocol upgrade progress', 'Parachain activity', 'Treasury proposals', 'Cross-chain app launches'],
        'links': [
            {'label': 'Polkadot.network', 'url': 'https://polkadot.network/'},
            {'label': 'CoinGecko DOT', 'url': 'https://www.coingecko.com/en/coins/polkadot'}
        ],
        'aliases': ['dot', 'polkadot', 'parachain', 'parachains']
    },
    'matic-network': {
        'description': 'Polygon focuses on Ethereum scaling, including Polygon PoS, zk technology, and the POL token migration narrative.',
        'bull_case': [
            'Ethereum scaling demand can support Polygon usage when apps need lower fees.',
            'zk and aggregation roadmap milestones can renew developer and investor interest.',
            'Brand partnerships and tokenization pilots can drive mainstream visibility.'
        ],
        'risk_notes': [
            'Scaling competition is crowded, especially among Ethereum layer-2 networks.',
            'Token migration details, incentives, and bridge assumptions can create confusion or volatility.'
        ],
        'catalysts': ['POL migration updates', 'zk roadmap milestones', 'Enterprise partnership news', 'Polygon PoS activity'],
        'links': [
            {'label': 'Polygon.technology', 'url': 'https://polygon.technology/'},
            {'label': 'CoinGecko POL', 'url': 'https://www.coingecko.com/en/coins/polygon-ecosystem-token'}
        ],
        'aliases': ['pol', 'polygon', 'matic', 'polygon pos']
    },
    'shiba-inu': {
        'description': 'Shiba Inu is a meme-coin ecosystem watched for community activity, Shibarium developments, burns, and retail risk appetite.',
        'bull_case': [
            'Large community recognition can amplify market attention during meme rotations.',
            'Shibarium and ecosystem products may add narratives beyond pure meme exposure.',
            'Burn headlines and exchange liquidity can influence short-term sentiment.'
        ],
        'risk_notes': [
            'Supply size, speculative positioning, and social momentum can produce sharp reversals.',
            'Ecosystem utility should be evaluated with on-chain usage rather than headlines alone.'
        ],
        'catalysts': ['Shibarium activity', 'Token burn updates', 'Meme-sector rotation', 'Community campaign momentum'],
        'links': [
            {'label': 'ShibaToken.com', 'url': 'https://www.shibatoken.com/'},
            {'label': 'CoinGecko SHIB', 'url': 'https://www.coingecko.com/en/coins/shiba-inu'}
        ],
        'aliases': ['shib', 'shiba', 'shiba inu', 'shibarium']
    },
    'pepe': {
        'description': 'PEPE is a meme coin driven primarily by internet-culture momentum, exchange liquidity, and broader meme-sector risk appetite.',
        'bull_case': [
            'Recognizable meme branding can attract rapid retail attention during speculative cycles.',
            'Deepening liquidity and listings can make it easier for traders to express meme-sector views.',
            'High beta to market sentiment can produce outsized moves during risk-on periods.'
        ],
        'risk_notes': [
            'Limited fundamental anchors mean price can depend heavily on attention and liquidity.',
            'Whale movement, copycat tokens, and broader meme fatigue can pressure momentum.'
        ],
        'catalysts': ['Meme-sector trend spikes', 'Exchange/liquidity changes', 'Large wallet movement', 'Social-media velocity'],
        'links': [
            {'label': 'CoinGecko PEPE', 'url': 'https://www.coingecko.com/en/coins/pepe'}
        ],
        'aliases': ['pepe', 'frog coin', 'meme coin', 'memecoin']
    },
    'floki': {
        'description': 'FLOKI is a meme and utility-branded token watched for community marketing, gaming/metaverse products, and exchange-driven liquidity.',
        'bull_case': [
            'Strong community marketing can keep FLOKI visible during meme rotations.',
            'Product and gaming narratives may provide more context than meme attention alone.',
            'Listings, campaigns, and sector momentum can create bursts of liquidity.'
        ],
        'risk_notes': [
            'Marketing-led narratives can cool quickly if participation fades.',
            'Utility claims should be checked against actual users, revenue, and on-chain activity.'
        ],
        'catalysts': ['Valhalla/game updates', 'Marketing campaign launches', 'Exchange liquidity', 'Meme-sector flows'],
        'links': [
            {'label': 'Floki.com', 'url': 'https://floki.com/'},
            {'label': 'CoinGecko FLOKI', 'url': 'https://www.coingecko.com/en/coins/floki'}
        ],
        'aliases': ['floki', 'valhalla', 'meme coin', 'memecoin']
    },
    'dogwifcoin': {
        'description': 'Dogwifhat is a Solana-based meme coin that trades heavily on community identity, social momentum, and Solana ecosystem liquidity.',
        'bull_case': [
            'Simple, recognizable meme identity can travel quickly across crypto-native communities.',
            'Solana DEX and exchange liquidity can support active trading during meme cycles.',
            'Community-led campaigns can amplify attention when broader market conditions are risk-on.'
        ],
        'risk_notes': [
            'Narrative durability is uncertain and can depend on social attention staying high.',
            'Meme-coin liquidity can thin quickly during market stress.'
        ],
        'catalysts': ['Solana meme rotation', 'Community campaign activity', 'Exchange liquidity changes', 'Social trend acceleration'],
        'links': [
            {'label': 'CoinGecko WIF', 'url': 'https://www.coingecko.com/en/coins/dogwifhat'}
        ],
        'aliases': ['wif', 'dogwifhat', 'dogwifcoin', 'solana meme']
    },
    'bonk': {
        'description': 'BONK is a Solana meme coin watched as a sentiment gauge for Solana retail activity, community campaigns, and ecosystem integrations.',
        'bull_case': [
            'Solana-native distribution and integrations can keep BONK visible inside the ecosystem.',
            'Meme rotations and retail participation can create high-beta upside periods.',
            'Community-led products and campaigns may broaden awareness.'
        ],
        'risk_notes': [
            'Meme-sector drawdowns can be severe when liquidity leaves high-beta assets.',
            'Token unlocks, holder concentration, and speculative leverage should be monitored.'
        ],
        'catalysts': ['Solana activity', 'Community product updates', 'Exchange/liquidity changes', 'Meme-sector trend strength'],
        'links': [
            {'label': 'BonkCoin.com', 'url': 'https://www.bonkcoin.com/'},
            {'label': 'CoinGecko BONK', 'url': 'https://www.coingecko.com/en/coins/bonk'}
        ],
        'aliases': ['bonk', 'solana meme', 'meme coin', 'memecoin']
    }
}


def get_prices(coins):
    ids = ','.join(c['id'] for c in coins)
    r = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
        'vs_currency': 'usd', 'ids': ids,
        'price_change_percentage': '1h,24h,7d', 'sparkline': 'true'
    })
    return r.json()

def get_fear_greed():
    try:
        r = requests.get('https://api.alternative.me/fng/')
        return r.json()['data'][0]
    except:
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
        context = COIN_CONTEXT.get(coin['id'], {})
        return {
            'id': coin['id'],
            'name': coin['name'],
            'symbol': coin['symbol'].upper(),
            'emoji': info['emoji'],
            'price': coin['current_price'] or 0,
            'change_1h':  float(coin.get('price_change_percentage_1h_in_currency') or 0),
            'change_24h': float(coin.get('price_change_percentage_24h_in_currency') or 0),
            'change_7d':  float(coin.get('price_change_percentage_7d_in_currency') or 0),
            'market_cap': coin['market_cap'] or 0,
            'volume_24h': coin['total_volume'] or 0,
            'sparkline':  coin.get('sparkline_in_7d', {}).get('price', []),
            'related_news': context.get('related_news', []),
            **context
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
        json.dump(output, f, indent=2)
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
