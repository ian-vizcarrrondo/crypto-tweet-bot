#!/usr/bin/env python3
"""
stock_alert_bot.py — Real-time breaking stock news alerts for Telegram.

Runs every 30 min via GitHub Actions during market hours (weekdays 9:30 AM–5 PM ET).
Deduplication is time-based: only articles published in the last 35 minutes are sent,
so no state file or database is needed.
"""

import os
import sys
import time
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ── CONFIG ──
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# Only alert on articles published within this window (slightly > cron interval)
LOOKBACK_MINUTES = 35

# Minimum articles needed to send an alert (avoid pinging for 1 minor story)
MIN_ARTICLES = 1
MAX_ARTICLES = 6  # cap per alert so the message isn't a wall

# ── NEWS SOURCES ──
FEEDS = [
    ("https://finance.yahoo.com/rss/topstories",               "Yahoo Finance"),
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html",  "CNBC"),
    ("https://feeds.marketwatch.com/marketwatch/topstories/",  "MarketWatch"),
    ("https://www.cnbc.com/id/10001147/device/rss/rss.html",   "CNBC Markets"),
]

# ── SIGNIFICANCE FILTER ──
# Only alert on stories mentioning these keywords or tickers
# (prevents noise from unrelated business stories)
MUST_MATCH = [
    # Major tickers
    "aapl","apple","msft","microsoft","nvda","nvidia","googl","alphabet","google",
    "meta","amazon","amzn","jpmorgan","jpm","goldman","sachs","berkshire","brk",
    "exxon","xom","chevron","cvx","tesla","tsla","sp500","s&p","nasdaq","dow jones",
    # Market-moving topics
    "fed","federal reserve","rate","inflation","cpi","gdp","recession","earnings",
    "quarterly","guidance","revenue","profit","loss","beat","miss","merger","acquisition",
    "ipo","bankruptcy","layoff","jobs report","unemployment","rate cut","rate hike",
    "market rally","market crash","market selloff","bull","bear","correction",
    "tariff","trade war","sanctions",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockAlertBot/1.0)"}


def parse_pub_date(entry):
    """Return UTC datetime from a feedparser entry, or None."""
    try:
        if hasattr(entry, "published"):
            return parsedate_to_datetime(entry.published).astimezone(timezone.utc)
        if hasattr(entry, "updated"):
            return parsedate_to_datetime(entry.updated).astimezone(timezone.utc)
    except Exception:
        pass
    return None


def is_significant(title, summary=""):
    """Return True if the article is worth alerting on."""
    text = (title + " " + summary).lower()
    return any(kw in text for kw in MUST_MATCH)


def fetch_breaking_news():
    """Fetch all feeds, return articles published within LOOKBACK_MINUTES."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    breaking = []
    seen_titles = set()

    for feed_url, source in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                pub = parse_pub_date(entry)
                if pub is None or pub < cutoff:
                    continue  # too old or unparseable

                title   = entry.get("title", "").strip()
                link    = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()

                if not title or not link:
                    continue

                # Deduplicate by title prefix
                key = title[:55].lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                if not is_significant(title, summary):
                    continue

                age_min = int((datetime.now(timezone.utc) - pub).total_seconds() / 60)
                breaking.append({
                    "title":   title,
                    "link":    link,
                    "source":  source,
                    "age_min": age_min,
                    "pub":     pub,
                })

        except Exception as e:
            print(f"⚠️  Feed error ({source}): {e}", file=sys.stderr)

    # Sort newest first
    breaking.sort(key=lambda x: x["pub"], reverse=True)
    return breaking[:MAX_ARTICLES]


def build_alert(articles):
    """Format a concise Telegram message for breaking news."""
    now_et = datetime.now(timezone.utc) - timedelta(hours=4)  # approximate EDT
    time_str = now_et.strftime("%I:%M %p ET")

    lines = [
        f"📊 *Breaking Stock News* — {time_str}",
        "─────────────────────────",
    ]

    for a in articles:
        age = f"{a['age_min']}m ago" if a['age_min'] > 0 else "just now"
        # Escape Markdown special chars in title
        safe_title = a['title'].replace('[','(').replace(']',')')
        lines.append(f"📰 [{safe_title}]({a['link']})")
        lines.append(f"_🔹 {a['source']} · {age}_")
        lines.append("")

    lines.append("_Powered by CryptoDoggy Stock Hub 📊_")
    return "\n".join(lines)


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     message,
        "parse_mode":               "Markdown",
        "disable_web_page_preview": False,  # show preview for top article
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code == 200:
        print(f"✅ Alert sent with {len(message)} chars")
    else:
        print(f"❌ Telegram error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print(f"🔍 Checking for breaking stock news (last {LOOKBACK_MINUTES} min)…")
    articles = fetch_breaking_news()

    if len(articles) < MIN_ARTICLES:
        print(f"✅ No breaking stories in the last {LOOKBACK_MINUTES} min — nothing to send.")
        sys.exit(0)

    print(f"🚨 Found {len(articles)} breaking article(s):")
    for a in articles:
        print(f"   • [{a['age_min']}m] {a['title'][:80]} ({a['source']})")

    msg = build_alert(articles)
    print("\n── MESSAGE PREVIEW ──")
    print(msg)
    print("─────────────────────\n")

    send_telegram(msg)
