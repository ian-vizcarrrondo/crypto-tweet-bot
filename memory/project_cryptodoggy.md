---
name: CryptoDoggy Project State
description: Full context of the BridgeSpace / CryptoDoggy crypto dashboard site and bots
type: project
---

BridgeSpace is a GitHub Pages crypto dashboard site called "CryptoDoggy" with 4 live pages and a backend bot system.

**Site pages (all live at GitHub Pages):**
- `index.html` — main dashboard: live prices, Fear & Greed index, mood bar, 30-day chart modal, alert banner, dark/light toggle
- `game.html` — price prediction game ("Predict") — users call up/down on coins
- `meme.html` — Meme Zone with degen/rug/moon awards and coin cards
- `portfolio.html` — portfolio tracker: enter holdings, see live P&L, allocation pie chart, data saved to localStorage

**Backend bots (Python):**
- `bot.py` — main price/news Twitter bot; tracks BTC, ETH, SUI, TON, NEAR + more
- `alert_bot.py` — Telegram price alert bot with cooldown system (`cooldown.json`)
- `weekly_bot.py` — weekly digest every Sunday 10am UTC: top 5 gainers, worst 5, most volatile, F&G 7d avg, top 3 news
- `memecoin_bot.py` — memecoin-specific bot
- `prices.json` — cached price data

**Stack:** Pure HTML/CSS/JS frontend; CoinGecko API for prices; Telegram for alerts; Twitter/X for bot posts; GitHub Actions for scheduling.

**Last built (session "Update bot and GitHub Pages website"):**
- portfolio.html with live P&L and pie chart
- Dark/light mode across all pages
- 30d price history in coin modal
- SUI, TON, NEAR added to bot.py coin list
- weekly_bot.py + GitHub Actions workflow

**Why:** Ian is building this as a personal crypto tracking platform and exploring expanding it with new products/pages.

**How to apply:** When building new pages, match the existing dark design system (bg #0a0a14, nav #06060f), reuse the shared nav with color-coded active states, and use CoinGecko's free API for data.
