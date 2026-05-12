#!/usr/bin/env python3
"""
🐋 CryptoDoggy Whale Alert Bot
Runs hourly via GitHub Actions.
Fetches top 50 coins from CoinGecko, flags unusual volume spikes,
and sends a Telegram message when thresholds are exceeded.

Required GitHub Secrets:
  TELEGRAM_TOKEN  — from @BotFather
  TELEGRAM_CHAT_ID    — your chat/channel ID
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID     = os.environ["TELEGRAM_CHAT_ID"]
PARSE_MODE  = "HTML"

# Volume intensity = total_volume / market_cap
# This ratio tells you how "active" a coin is relative to its size
SPIKE_EXTREME  = 0.25   # 🚨 Extreme — massive unusual activity
SPIKE_WHALE    = 0.12   # 🐋 Whale   — significant spike
SPIKE_ELEVATED = 0.06   # 📈 Elevated — worth noting

# Minimum market cap to avoid tiny coins triggering alerts ($50M)
MIN_MARKET_CAP = 50_000_000

# Only alert if price also moved meaningfully (avoids false positives)
MIN_PRICE_CHANGE_ABS = 3.0  # % absolute 24h change

# Don't spam — only send a message if at least this many spikes detected
MIN_SPIKES_TO_ALERT = 1

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    "&sparkline=false&price_change_percentage=24h"
)

PROXIES = [
    lambda u: u,
    lambda u: f"https://corsproxy.io/?{requests.utils.quote(u)}",
    lambda u: f"https://api.allorigins.win/get?url={requests.utils.quote(u)}",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_coingecko():
    """Fetch market data with proxy fallback."""
    for proxy in PROXIES:
        url = proxy(COINGECKO_URL)
        try:
            r = requests.get(url, timeout=15, headers={"Accept": "application/json"})
            r.raise_for_status()
            data = r.json()
            # allorigins wraps in {"contents": "..."}
            if isinstance(data, dict) and "contents" in data:
                data = json.loads(data["contents"])
            if isinstance(data, list) and len(data) > 0:
                return data
        except Exception as e:
            print(f"[proxy] {url[:60]}... → {e}")
            time.sleep(1)
    raise RuntimeError("All proxies failed — CoinGecko unavailable")


def spike_tier(intensity):
    if intensity >= SPIKE_EXTREME:
        return ("🚨", "EXTREME", intensity)
    if intensity >= SPIKE_WHALE:
        return ("🐋", "WHALE", intensity)
    if intensity >= SPIKE_ELEVATED:
        return ("📈", "ELEVATED", intensity)
    return None


def fmt_price(p):
    if p is None:
        return "N/A"
    if p >= 1000:
        return f"${p:,.0f}"
    if p >= 1:
        return f"${p:.2f}"
    return f"${p:.6f}"


def fmt_pct(p):
    if p is None:
        return "?"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.1f}%"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": PARSE_MODE,
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    print("✅ Telegram message sent")
    return r.json()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"🐋 Whale Alert running at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    coins = fetch_coingecko()
    print(f"Fetched {len(coins)} coins")

    spikes = []
    for coin in coins:
        mc   = coin.get("market_cap") or 0
        vol  = coin.get("total_volume") or 0
        chg  = coin.get("price_change_percentage_24h") or 0

        if mc < MIN_MARKET_CAP:
            continue
        if abs(chg) < MIN_PRICE_CHANGE_ABS:
            continue

        intensity = vol / mc if mc > 0 else 0
        tier = spike_tier(intensity)
        if tier:
            spikes.append({
                "emoji":      tier[0],
                "tier":       tier[1],
                "intensity":  tier[2],
                "name":       coin.get("name", "?"),
                "symbol":     coin.get("symbol", "?").upper(),
                "price":      coin.get("current_price"),
                "change_24h": chg,
                "volume":     vol,
                "market_cap": mc,
            })

    # Sort: biggest intensity first
    spikes.sort(key=lambda x: x["intensity"], reverse=True)

    if len(spikes) < MIN_SPIKES_TO_ALERT:
        print(f"No significant spikes detected ({len(spikes)} below threshold). No message sent.")
        return

    # Build Telegram message
    now_str = datetime.now(timezone.utc).strftime("%H:%M UTC · %b %d")
    lines = [
        f"<b>🐋 CryptoDoggy Whale Alert</b>",
        f"<i>{now_str} · {len(spikes)} spike{'s' if len(spikes)>1 else ''} detected</i>",
        "",
    ]

    for s in spikes[:8]:  # cap at 8 to keep message readable
        vol_b  = s["volume"] / 1e9
        mc_b   = s["market_cap"] / 1e9
        intens = s["intensity"] * 100  # as %

        direction = "🟢" if s["change_24h"] >= 0 else "🔴"
        lines.append(
            f"{s['emoji']} <b>{s['name']}</b> ({s['symbol']})\n"
            f"   {direction} {fmt_pct(s['change_24h'])} · {fmt_price(s['price'])}\n"
            f"   Vol <b>${vol_b:.2f}B</b> vs MCap ${mc_b:.2f}B  "
            f"<b>({intens:.0f}% intensity)</b>\n"
            f"   Tier: <b>{s['tier']}</b>"
        )

    lines += [
        "",
        f"<a href='https://cryptodoggy.github.io/whales.html'>🌊 Open Whale Watch</a>",
    ]

    message = "\n".join(lines)
    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()
