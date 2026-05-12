#!/usr/bin/env python3
"""
📋 CryptoDoggy Weekly Digest Bot
Runs every Sunday at 9:00 AM UTC via GitHub Actions.
Sends a Telegram summary covering:
  • Top 3 gainers & losers (7-day)
  • Biggest volume spike of the week
  • DeFi TVL snapshot (DeFiLlama)
  • Upcoming calendar events for the week ahead

Required GitHub Secrets:
  TELEGRAM_TOKEN  — from @BotFather
  TELEGRAM_CHAT_ID    — your chat/channel ID
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.environ["TELEGRAM_TOKEN"]
CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]
PARSE_MODE = "HTML"

COINGECKO_MARKETS = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    "&sparkline=false&price_change_percentage=7d"
)

DEFILLAMA_PROTOCOLS = "https://api.llama.fi/protocols"
DEFILLAMA_CHAINS    = "https://api.llama.fi/v2/chains"

# ── Upcoming events (mirrors calendar.html — keep in sync) ───────────────────
EVENTS = [
    # Format: (date_str, title, category, importance)
    ("2026-06-10", "US CPI Report — May Data",         "Macro",      "high"),
    ("2026-06-17", "FOMC Meeting — Day 1",              "Macro",      "medium"),
    ("2026-06-18", "FOMC Rate Decision",                "Macro",      "high"),
    ("2026-06-27", "ETH Options Expiry — June",         "Crypto",     "medium"),
    ("2026-07-03", "BTC Options Expiry — July",         "Crypto",     "high"),
    ("2026-07-14", "US CPI Report — Jun Data",          "Macro",      "high"),
    ("2026-07-15", "Aave v4 Launch Window (Est.)",      "DeFi",       "high"),
    ("2026-07-20", "APT Token Unlock — Aptos",          "Tokenomics", "medium"),
    ("2026-07-28", "FOMC Meeting — Day 1",              "Macro",      "medium"),
    ("2026-07-29", "FOMC Rate Decision",                "Macro",      "high"),
    ("2026-08-01", "SUI Token Unlock",                  "Tokenomics", "medium"),
    ("2026-08-07", "BTC Options Expiry — August",       "Crypto",     "high"),
    ("2026-08-12", "US CPI Report — Jul Data",          "Macro",      "high"),
    ("2026-08-20", "Curve Gauge Vote — Monthly",        "DeFi",       "low"),
    ("2026-09-01", "OP Token Unlock — Optimism",        "Tokenomics", "high"),
    ("2026-09-11", "US CPI Report — Aug Data",          "Macro",      "high"),
    ("2026-09-15", "FOMC Meeting — Day 1",              "Macro",      "medium"),
    ("2026-09-16", "FOMC Rate Decision",                "Macro",      "high"),
    ("2026-09-25", "BTC Options Expiry — September",    "Crypto",     "high"),
    ("2026-09-26", "Ethereum Devcon 2026 (Est.)",       "Crypto",     "medium"),
    ("2026-10-13", "US CPI Report — Sep Data",          "Macro",      "high"),
    ("2026-11-03", "FOMC Meeting — Day 1",              "Macro",      "medium"),
    ("2026-11-04", "FOMC Rate Decision",                "Macro",      "high"),
    ("2026-11-12", "US CPI Report — Oct Data",          "Macro",      "high"),
    ("2026-12-10", "US CPI Report — Nov Data",          "Macro",      "high"),
    ("2026-12-15", "FOMC Meeting — Day 1",              "Macro",      "medium"),
    ("2026-12-16", "FOMC Rate Decision",                "Macro",      "high"),
    ("2026-12-25", "BTC Options Expiry — December",     "Crypto",     "high"),
]

CAT_EMOJI = {
    "Macro":      "🏛",
    "Crypto":     "₿",
    "Tokenomics": "🔓",
    "DeFi":       "🌊",
}
IMP_DOT = {"high": "🔴", "medium": "🟡", "low": "⚪"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_json(url, via_allorigins=False):
    """Fetch JSON with simple retry."""
    urls = [url]
    if via_allorigins:
        urls.append(f"https://api.allorigins.win/get?url={requests.utils.quote(url)}")

    for u in urls:
        try:
            r = requests.get(u, timeout=15, headers={"Accept": "application/json"})
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and "contents" in data:
                data = json.loads(data["contents"])
            return data
        except Exception as e:
            print(f"[fetch] {u[:70]} → {e}")
            time.sleep(2)
    return None


def fmt_price(p):
    if p is None:
        return "N/A"
    if p >= 1000:
        return f"${p:,.0f}"
    if p >= 1:
        return f"${p:.2f}"
    return f"${p:.6f}"


def fmt_pct(p, decimals=1):
    if p is None:
        return "?"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.{decimals}f}%"


def fmt_tvl(t):
    if t >= 1e9:
        return f"${t/1e9:.2f}B"
    if t >= 1e6:
        return f"${t/1e6:.0f}M"
    return f"${t:,.0f}"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     text,
        "parse_mode":               PARSE_MODE,
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    print("✅ Telegram message sent")


# ── Sections ──────────────────────────────────────────────────────────────────
def section_movers(coins):
    """Top 3 gainers and losers by 7d %."""
    valid = [c for c in coins if c.get("price_change_percentage_7d_in_currency") is not None]
    valid.sort(key=lambda c: c["price_change_percentage_7d_in_currency"], reverse=True)

    gainers = valid[:3]
    losers  = valid[-3:][::-1]

    lines = ["<b>📈 Top Gainers (7d)</b>"]
    for c in gainers:
        pct = c["price_change_percentage_7d_in_currency"]
        lines.append(f"  🟢 <b>{c['symbol'].upper()}</b>  {fmt_pct(pct)}  ·  {fmt_price(c['current_price'])}")

    lines += ["", "<b>📉 Top Losers (7d)</b>"]
    for c in losers:
        pct = c["price_change_percentage_7d_in_currency"]
        lines.append(f"  🔴 <b>{c['symbol'].upper()}</b>  {fmt_pct(pct)}  ·  {fmt_price(c['current_price'])}")

    return "\n".join(lines)


def section_volume_spike(coins):
    """Coin with highest volume intensity (vol/mcap)."""
    best = None
    best_intensity = 0
    for c in coins:
        mc  = c.get("market_cap") or 0
        vol = c.get("total_volume") or 0
        if mc < 50_000_000:
            continue
        intensity = vol / mc if mc > 0 else 0
        if intensity > best_intensity:
            best_intensity = intensity
            best = c

    if not best:
        return "<b>🐋 Volume Spike</b>\nNo significant spikes this week."

    vol_b = best["total_volume"] / 1e9
    mc_b  = best["market_cap"] / 1e9
    chg   = best.get("price_change_percentage_7d_in_currency") or 0
    direction = "🟢" if chg >= 0 else "🔴"

    tier = "🚨 EXTREME" if best_intensity > 0.25 else "🐋 WHALE" if best_intensity > 0.12 else "📈 ELEVATED"

    return (
        f"<b>🐋 Biggest Volume Spike</b>\n"
        f"  {tier} — <b>{best['name']}</b> ({best['symbol'].upper()})\n"
        f"  {direction} 7d: {fmt_pct(chg)}  ·  {fmt_price(best['current_price'])}\n"
        f"  Vol ${vol_b:.2f}B  vs  MCap ${mc_b:.2f}B  ({best_intensity*100:.0f}% intensity)"
    )


def section_defi(protocols, chains):
    """Total TVL and top 3 protocols."""
    if not protocols:
        return "<b>🌊 DeFi TVL</b>\nData unavailable."

    # Total TVL from chains
    total_tvl = sum(c.get("tvl", 0) for c in (chains or [])) if chains else 0
    if total_tvl == 0:
        total_tvl = sum(p.get("tvl", 0) for p in protocols)

    # Top 3 by TVL
    top = sorted(protocols, key=lambda p: p.get("tvl") or 0, reverse=True)[:3]

    lines = [
        f"<b>🌊 DeFi TVL Snapshot</b>",
        f"  Total: <b>{fmt_tvl(total_tvl)}</b>",
        "",
    ]
    for i, p in enumerate(top, 1):
        tvl   = p.get("tvl") or 0
        chg1d = p.get("change_1d") or 0
        chg7d = p.get("change_7d") or 0
        d = "🟢" if chg1d >= 0 else "🔴"
        lines.append(
            f"  {i}. <b>{p['name']}</b>  {fmt_tvl(tvl)}\n"
            f"     {d} 24h {fmt_pct(chg1d)}  ·  7d {fmt_pct(chg7d)}"
        )

    return "\n".join(lines)


def section_calendar():
    """Events in the next 7 days."""
    today    = datetime.now(timezone.utc).date()
    week_end = today + timedelta(days=7)

    upcoming = []
    for date_str, title, cat, imp in EVENTS:
        ev_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if today <= ev_date <= week_end:
            upcoming.append((ev_date, title, cat, imp))

    upcoming.sort(key=lambda x: x[0])

    if not upcoming:
        return "<b>📅 This Week's Events</b>\nNo major events this week — quiet week ahead."

    lines = ["<b>📅 This Week's Events</b>"]
    for ev_date, title, cat, imp in upcoming:
        day  = ev_date.strftime("%a %b %d")
        icon = CAT_EMOJI.get(cat, "📌")
        dot  = IMP_DOT.get(imp, "⚪")
        lines.append(f"  {dot} {icon} <b>{day}</b> — {title}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
    print(f"📋 Weekly Digest running — {now_str}")

    # Fetch data
    print("Fetching CoinGecko markets...")
    coins = fetch_json(COINGECKO_MARKETS, via_allorigins=True)
    if not coins:
        print("❌ CoinGecko fetch failed — aborting")
        sys.exit(1)
    print(f"  Got {len(coins)} coins")

    print("Fetching DeFiLlama...")
    protocols = fetch_json(DEFILLAMA_PROTOCOLS)
    chains    = fetch_json(DEFILLAMA_CHAINS)
    print(f"  Got {len(protocols or [])} protocols, {len(chains or [])} chains")

    # Build message
    sep = "\n─────────────────────\n"
    week_label = datetime.now(timezone.utc).strftime("Week of %b %d, %Y")

    message = "\n".join([
        f"<b>🐕 CryptoDoggy Weekly Digest</b>",
        f"<i>{week_label}</i>",
        sep,
        section_movers(coins),
        sep,
        section_volume_spike(coins),
        sep,
        section_defi(protocols, chains),
        sep,
        section_calendar(),
        sep,
        "📊 <a href='https://cryptodoggy.github.io/'>Open Dashboard</a>  ·  "
        "📅 <a href='https://cryptodoggy.github.io/calendar.html'>Full Calendar</a>",
    ])

    print("\n── MESSAGE PREVIEW ──")
    print(message)
    print("─────────────────────\n")

    send_telegram(message)


if __name__ == "__main__":
    main()
