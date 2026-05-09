#!/usr/bin/env python3
"""
stock_bot.py — Daily stock market digest for Telegram
Runs via GitHub Actions (or cron). No paid API keys required.
Uses: Yahoo Finance (unofficial) for prices, RSS feeds for news.
"""

import os
import sys
import requests
import feedparser
from datetime import datetime
import pytz

# ── CONFIG ──
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

WATCHLIST = [
    # Indices
    {"symbol": "SPY",   "name": "S&P 500",    "sector": "market"},
    {"symbol": "QQQ",   "name": "Nasdaq",      "sector": "market"},
    {"symbol": "DIA",   "name": "Dow Jones",   "sector": "market"},
    # Big Tech
    {"symbol": "AAPL",  "name": "Apple",       "sector": "tech"},
    {"symbol": "MSFT",  "name": "Microsoft",   "sector": "tech"},
    {"symbol": "NVDA",  "name": "NVIDIA",      "sector": "tech"},
    {"symbol": "GOOGL", "name": "Alphabet",    "sector": "tech"},
    {"symbol": "META",  "name": "Meta",        "sector": "tech"},
    {"symbol": "AMZN",  "name": "Amazon",      "sector": "tech"},
    # Finance
    {"symbol": "JPM",   "name": "JPMorgan",    "sector": "finance"},
    {"symbol": "GS",    "name": "Goldman Sachs","sector": "finance"},
    {"symbol": "BAC",   "name": "Bank of America","sector": "finance"},
    {"symbol": "BRK-B", "name": "Berkshire",   "sector": "finance"},
    # Energy
    {"symbol": "XOM",   "name": "ExxonMobil",  "sector": "energy"},
    {"symbol": "CVX",   "name": "Chevron",     "sector": "energy"},
]

NEWS_FEEDS = [
    ("https://finance.yahoo.com/rss/topstories",               "Yahoo Finance"),
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html",  "CNBC"),
    ("https://feeds.marketwatch.com/marketwatch/topstories/",  "MarketWatch"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0)"}


# ── PRICES ──
def get_prices():
    symbols = ",".join(t["symbol"] for t in WATCHLIST)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        results = r.json()["quoteResponse"]["result"]
        return {q["symbol"]: q for q in results}
    except Exception as e:
        print(f"⚠️  Price fetch failed: {e}", file=sys.stderr)
        return {}


def fmt_pct(pct):
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"

def fmt_price(p):
    return f"${p:,.2f}"

def arrow(pct):
    return "🟢" if pct > 0 else "🔴" if pct < 0 else "⚪"


# ── NEWS ──
def get_headlines(n=5):
    headlines = []
    for feed_url, source in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:4]:
                title = entry.get("title", "").strip()
                link  = entry.get("link", "").strip()
                if title and link:
                    headlines.append((title, link, source))
        except Exception as e:
            print(f"⚠️  Feed {source} failed: {e}", file=sys.stderr)
    # Deduplicate by title prefix
    seen = set()
    unique = []
    for h in headlines:
        key = h[0][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique[:n]


# ── FORMAT MESSAGE ──
def build_message(prices, headlines):
    et = pytz.timezone("America/New_York")
    now_et = datetime.now(et)
    date_str = now_et.strftime("%A, %B %d %Y • %I:%M %p ET")

    lines = [
        "📊 *Stock Market Daily Digest*",
        f"_{date_str}_",
        "",
    ]

    # ── INDICES ──
    index_syms = ["SPY", "QQQ", "DIA"]
    index_names = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones"}
    index_emojis = {"SPY": "🏛", "QQQ": "💻", "DIA": "📐"}
    lines.append("*📈 Market Indices*")
    for sym in index_syms:
        q = prices.get(sym)
        if q:
            pct = q.get("regularMarketChangePercent", 0)
            pr  = q.get("regularMarketPrice", 0)
            lines.append(f"{index_emojis[sym]} *{index_names[sym]}:* {fmt_price(pr)} {arrow(pct)} {fmt_pct(pct)}")
    lines.append("")

    # ── TOP MOVERS (excluding indices) ──
    movers = [
        (t, prices[t["symbol"]])
        for t in WATCHLIST
        if t["symbol"] in prices and t["sector"] != "market"
    ]
    movers.sort(key=lambda x: x[1].get("regularMarketChangePercent", 0), reverse=True)

    gainers = [(t, q) for t, q in movers if q.get("regularMarketChangePercent", 0) > 0][:3]
    losers  = [(t, q) for t, q in movers if q.get("regularMarketChangePercent", 0) < 0][-3:]

    if gainers:
        lines.append("*🚀 Top Gainers*")
        for t, q in gainers:
            pct = q.get("regularMarketChangePercent", 0)
            pr  = q.get("regularMarketPrice", 0)
            lines.append(f"• *{t['symbol']}* ({t['name']}) — {fmt_price(pr)} 🟢 {fmt_pct(pct)}")
        lines.append("")

    if losers:
        lines.append("*📉 Biggest Drops*")
        for t, q in reversed(losers):
            pct = q.get("regularMarketChangePercent", 0)
            pr  = q.get("regularMarketPrice", 0)
            lines.append(f"• *{t['symbol']}* ({t['name']}) — {fmt_price(pr)} 🔴 {fmt_pct(pct)}")
        lines.append("")

    # ── SECTOR SNAPSHOT ──
    sectors = {"tech": "💻 Tech", "finance": "🏦 Finance", "energy": "⛽ Energy"}
    lines.append("*Sector Snapshot*")
    for sec_key, sec_label in sectors.items():
        sec_stocks = [(t, prices[t["symbol"]]) for t in WATCHLIST if t["sector"] == sec_key and t["symbol"] in prices]
        if not sec_stocks:
            continue
        avg_pct = sum(q.get("regularMarketChangePercent", 0) for _, q in sec_stocks) / len(sec_stocks)
        lines.append(f"{sec_label}: avg {fmt_pct(avg_pct)} {arrow(avg_pct)}")
    lines.append("")

    # ── HEADLINES ──
    if headlines:
        lines.append("*📰 Top Headlines*")
        for title, link, source in headlines:
            lines.append(f"• [{title}]({link})")
        lines.append("")

    lines.append("_Powered by CryptoDoggy Stock Hub 📊_")

    return "\n".join(lines)


# ── SEND ──
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID", file=sys.stderr)
        sys.exit(1)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code == 200:
        print("✅ Stock digest sent to Telegram!")
    else:
        print(f"❌ Telegram error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


# ── MAIN ──
if __name__ == "__main__":
    print("📊 Fetching stock prices...")
    prices = get_prices()
    print(f"   Got {len(prices)} quotes")

    print("📰 Fetching headlines...")
    headlines = get_headlines(n=5)
    print(f"   Got {len(headlines)} headlines")

    if not prices and not headlines:
        print("❌ No data available — aborting", file=sys.stderr)
        sys.exit(1)

    msg = build_message(prices, headlines)
    print("\n── MESSAGE PREVIEW ──")
    print(msg)
    print("─────────────────────\n")

    send_telegram(msg)
