#!/usr/bin/env python3
"""
🔔 CryptoDoggy Price Alert Bot
Runs every 15 minutes via GitHub Actions.
Sends a Telegram alert when any tracked coin crosses a predefined threshold.

Alert types:
  • % move in 24h  (e.g. BTC up >5% or down >5%)
  • Price crossing a round-number level (e.g. BTC ≥ $100,000)
  • Extreme RSI-proxy: 7d change >20% (overbought) or <-20% (oversold)
  • Volume spike: 24h volume > 40% of market cap

Required GitHub Secrets:
  TELEGRAM_TOKEN   — from @BotFather
  TELEGRAM_CHAT_ID — your chat/channel ID
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

# Coins to track (CoinGecko IDs)
TRACKED = [
    "bitcoin", "ethereum", "solana", "binancecoin", "ripple",
    "render-token", "dogecoin", "avalanche-2", "chainlink", "polkadot",
]

# Alert thresholds
MOVE_24H_PCT   = 5.0   # alert if |24h change| >= this %
MOVE_7D_PCT    = 20.0  # RSI-proxy: alert if |7d change| >= this %
VOL_INTENSITY  = 0.40  # alert if volume/mcap >= this ratio

# Round-number price levels to watch {coin_id: [levels]}
ROUND_LEVELS = {
    "bitcoin":  [70_000, 80_000, 90_000, 100_000, 110_000, 120_000],
    "ethereum": [2_000, 2_500, 3_000, 3_500, 4_000, 5_000],
    "solana":   [100, 150, 200, 250, 300],
    "ripple":   [1.0, 1.5, 2.0, 3.0, 5.0],
}

# State file — tracks which alerts already fired this run cycle
STATE_FILE = "/tmp/price_alert_state.json"

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd"
    f"&ids={'%2C'.join(TRACKED)}"
    "&order=market_cap_desc"
    "&per_page=50&page=1"
    "&sparkline=false"
    "&price_change_percentage=24h,7d"
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def fetch_json(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=20, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[fetch attempt {attempt+1}] {e}")
            time.sleep(3)
    return None


def fmt_price(p):
    if p is None:
        return "N/A"
    if p >= 1_000:
        return f"${p:,.0f}"
    if p >= 1:
        return f"${p:.3f}"
    return f"${p:.6f}"


def fmt_pct(p):
    if p is None:
        return "?"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.2f}%"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    print(f"✅ Sent: {text[:60]}...")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ── Alert builders ─────────────────────────────────────────────────────────────
def check_move_24h(coin, state, alerts):
    pct = coin.get("price_change_percentage_24h")
    if pct is None:
        return
    if abs(pct) < MOVE_24H_PCT:
        return

    key = f"move24h_{coin['id']}_{int(pct // MOVE_24H_PCT)}"
    if state.get(key):
        return
    state[key] = True

    direction = "🚀 SURGING" if pct > 0 else "🔻 DUMPING"
    emoji     = "🟢" if pct > 0 else "🔴"
    alerts.append(
        f"{emoji} <b>{coin['name']} ({coin['symbol'].upper()}) — 24h {direction}</b>\n"
        f"   Price: {fmt_price(coin['current_price'])}  ·  24h: {fmt_pct(pct)}"
    )


def check_move_7d(coin, state, alerts):
    pct = coin.get("price_change_percentage_7d_in_currency")
    if pct is None:
        return
    if abs(pct) < MOVE_7D_PCT:
        return

    key = f"move7d_{coin['id']}_{int(pct // MOVE_7D_PCT)}"
    if state.get(key):
        return
    state[key] = True

    if pct > 0:
        label = "⚠️ OVERBOUGHT SIGNAL"
        emoji = "🔥"
    else:
        label = "⚠️ OVERSOLD SIGNAL"
        emoji = "🧊"

    alerts.append(
        f"{emoji} <b>{coin['name']} ({coin['symbol'].upper()}) — {label}</b>\n"
        f"   Price: {fmt_price(coin['current_price'])}  ·  7d: {fmt_pct(pct)}"
    )


def check_round_levels(coin, state, alerts):
    levels = ROUND_LEVELS.get(coin["id"], [])
    price  = coin.get("current_price") or 0
    pct24  = coin.get("price_change_percentage_24h") or 0

    for level in levels:
        # Check if price is within 1% of level (just crossed or sitting on it)
        proximity = abs(price - level) / level
        if proximity > 0.01:
            continue

        direction = "above" if price >= level else "below"
        key = f"level_{coin['id']}_{level}_{direction}"
        if state.get(key):
            continue
        state[key] = True

        emoji = "🎯"
        alerts.append(
            f"{emoji} <b>{coin['name']} ({coin['symbol'].upper()}) — KEY LEVEL</b>\n"
            f"   Price {fmt_price(price)} is near <b>{fmt_price(float(level))}</b>\n"
            f"   24h: {fmt_pct(pct24)}"
        )


def check_volume_spike(coin, state, alerts):
    mc  = coin.get("market_cap") or 0
    vol = coin.get("total_volume") or 0
    if mc < 100_000_000:
        return
    intensity = vol / mc if mc > 0 else 0
    if intensity < VOL_INTENSITY:
        return

    key = f"volspike_{coin['id']}_{int(intensity * 10)}"
    if state.get(key):
        return
    state[key] = True

    pct24 = coin.get("price_change_percentage_24h") or 0
    emoji = "🟢" if pct24 >= 0 else "🔴"
    tier  = "🚨 EXTREME" if intensity > 0.70 else "🐋 HIGH"

    alerts.append(
        f"🐳 <b>{coin['name']} ({coin['symbol'].upper()}) — {tier} VOLUME</b>\n"
        f"   {emoji} Price: {fmt_price(coin['current_price'])}  ·  24h: {fmt_pct(pct24)}\n"
        f"   Vol/MCap ratio: {intensity*100:.0f}%"
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"🔔 Price Alert Bot running — {now_str}")

    data = fetch_json(COINGECKO_URL)
    if not data:
        print("❌ CoinGecko fetch failed — aborting")
        sys.exit(1)
    print(f"  Got {len(data)} coins")

    state  = load_state()
    alerts = []

    for coin in data:
        check_move_24h(coin, state, alerts)
        check_move_7d(coin, state, alerts)
        check_round_levels(coin, state, alerts)
        check_volume_spike(coin, state, alerts)

    save_state(state)

    if not alerts:
        print("✅ No new alerts to send.")
        return

    header = f"<b>🔔 CryptoDoggy Price Alerts</b>  <i>{now_str}</i>\n"
    sep    = "\n─────────────────────\n"

    # Send each alert as a separate message (avoids Telegram's 4096-char limit)
    for alert in alerts:
        msg = header + sep + alert + sep + (
            "📊 <a href='https://cryptodoggy.github.io/'>Dashboard</a>"
        )
        send_telegram(msg)
        time.sleep(0.5)   # rate-limit: avoid Telegram 429

    print(f"🔔 Sent {len(alerts)} alert(s).")


if __name__ == "__main__":
    main()
