# 🐶 CryptoDoggy

> **Live crypto intelligence. Automated alerts. One slick dashboard.**

[![Automated](https://img.shields.io/badge/Automated-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Dashboard](https://img.shields.io/badge/Live-GitHub_Pages-222?style=flat-square&logo=github&logoColor=white)](https://ian-vizcarrrondo.github.io/crypto-tweet-bot/)
[![Data](https://img.shields.io/badge/Data-CoinGecko-8DC647?style=flat-square)](https://www.coingecko.com/)
[![Alerts](https://img.shields.io/badge/Alerts-Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://telegram.org/)

---

## What Is CryptoDoggy?

CryptoDoggy is a fully automated crypto market tracker with four GitHub Actions bots running on separate schedules. It pulls live price data, monitors major coins and memecoins, sends Telegram alerts, and serves everything through a live multi-page web dashboard — zero manual work required.

**[→ View the live dashboard](https://ian-vizcarrrondo.github.io/crypto-tweet-bot/)**

---

## ⚡ Features

| Feature | Details |
|---|---|
| 📊 **Live Price Tracking** | Prices, 1h/24h/7d % changes, sparklines, market cap, volume |
| 🔔 **Price Alerts** | Fires when any coin moves ±5% in 1 hour, with 1-hour cooldown per coin |
| 🐸 **Memecoin Updates** | Dedicated bot + Telegram channel just for memecoins |
| 📅 **Weekly Digest** | Every Sunday — top gainers/losers, 7d recap, Fear & Greed, top news |
| 😱 **Fear & Greed Index** | Live sentiment from Alternative.me, reflected in dashboard mood bar |
| 📰 **Crypto News** | Latest headlines pulled from CoinDesk RSS |
| 💼 **Portfolio Tracker** | Local-only holdings tracker with P&L, cost basis, and allocation chart |
| 🎮 **Prediction Game** | Bet UP or DOWN on live prices — 60 second results, streak tracker |
| 🌐 **Live Dashboard** | Static site hosted on GitHub Pages, auto-updated every hour |

---

## 🪙 Coins Tracked

**Major Markets** (13 coins)

`BTC` · `ETH` · `XRP` · `BNB` · `SOL` · `DOGE` · `AVAX` · `LINK` · `DOT` · `SUI` · `TON` · `NEAR` · `POL`

**Memecoins** (6 coins)

`DOGE` · `SHIB` · `PEPE` · `FLOKI` · `WIF` · `BONK`

---

## ⚙️ Automation Schedule

Four bots run independently on their own schedules:

| Workflow | Script | Schedule | Does |
|---|---|---|---|
| `bot.yml` | `bot.py` | Every hour | Fetches all prices, updates `prices.json`, sends market update to Telegram |
| `run_alerts.yml` | `alert_bot.py` | Every 15 minutes | Checks for ±5% 1h moves, fires alerts with 1hr cooldown, saves `cooldown.json` |
| `run_memecoin.yml` | `memecoin_bot.py` | Every 6 hours | Sends memecoin update to the meme Telegram channel |
| `run_weekly.yml` | `weekly_bot.py` | Sundays at 10:00 UTC | Sends weekly digest — top 5 gainers/losers, F&G avg, top news |

---

## 🖥️ Dashboard Pages

| Page | File | Description |
|---|---|---|
| 📊 Dashboard | `index.html` | Market table, heatmap, ticker tape, volume chart, news feed |
| 🎮 Predict | `game.html` | 60-second UP/DOWN game with streak tracking |
| 🐸 Meme Zone | `meme.html` | Degen Score, Rug Pull-O-Meter, meme awards |
| 💼 Portfolio | `portfolio.html` | Holdings tracker with P&L, cost basis, pie chart |

All pages load data from `prices.json`, which is committed to the repo and served via GitHub Pages.

---

## 🛠️ How It Works

```
Every 15 min ─── run_alerts.yml ───► alert_bot.py   ──► Telegram (price alerts)
Every hour   ─── bot.yml        ───► bot.py          ──► prices.json + Telegram
Every 6 hrs  ─── run_memecoin.yml ► memecoin_bot.py ──► Telegram (meme update)
Every Sunday ─── run_weekly.yml ───► weekly_bot.py   ──► Telegram (weekly digest)
                                                           │
                                                           ▼
                                                  GitHub Pages serves
                                                  dashboard from prices.json
```

**Data sources:**
- Prices & sparklines → [CoinGecko](https://www.coingecko.com/)
- News headlines → [CoinDesk RSS](https://www.coindesk.com/arc/outboundfeeds/rss/)
- Fear & Greed Index → [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/)

---

## 📁 Project Structure

```
crypto-tweet-bot/
├── .github/
│   └── workflows/
│       ├── bot.yml              # Hourly price bot
│       ├── run.yml              # Legacy run workflow
│       ├── run_alerts.yml       # 15-min price alert bot
│       ├── run_memecoin.yml     # 6hr memecoin bot
│       └── run_weekly.yml       # Sunday weekly digest
├── bot.py                       # Main price bot + prices.json writer
├── alert_bot.py                 # Price movement alert bot
├── memecoin_bot.py              # Memecoin Telegram bot
├── weekly_bot.py                # Weekly digest bot
├── prices.json                  # Auto-updated market data (dashboard reads this)
├── cooldown.json                # Alert cooldown state (auto-managed)
├── index.html                   # Main dashboard
├── game.html                    # Prediction game
├── meme.html                    # Meme Zone
└── portfolio.html               # Portfolio tracker
```

---

## 🚀 Setup

### 1. Fork or clone the repo
```bash
git clone https://github.com/ian-vizcarrrondo/crypto-tweet-bot.git
cd crypto-tweet-bot
```

### 2. Create a Telegram bot
Go to [@BotFather](https://t.me/botfather) on Telegram. Create two bots — one for main alerts, one for memecoins. Get your chat IDs from [@userinfobot](https://t.me/userinfobot).

### 3. Add GitHub Secrets
**Settings → Secrets → Actions**, add all three:

| Secret | What it is |
|---|---|
| `TELEGRAM_TOKEN` | Your bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Chat ID for main market alerts |
| `TELEGRAM_MEMECOIN_CHAT_ID` | Chat ID for memecoin alerts |

### 4. Enable GitHub Actions
Push to `main` — all four workflows activate automatically on their schedules.

### 5. Enable GitHub Pages
**Settings → Pages** → set source to the root of your `main` branch. Dashboard goes live at `https://username.github.io/crypto-tweet-bot/`.

---

## 📱 Telegram Channels

| Channel | What you get |
|---|---|
| [📈 CryptoDoggyAlerts](https://t.me/CryptoDoggyAlerts) | Hourly market updates + price movement alerts |
| [🐸 CryptoDoggyMemes](https://t.me/CryptoDoggyMemes) | Memecoin updates + meme alerts |

---

## 📄 License

MIT — do whatever you want with it.

---

<p align="center">
  Built with 🐶 energy · Powered by automation · No sleep required
</p>
