# 🚀 Next Session Game Plan — New Product Launch

**Session goal:** Build and ship a new page to the CryptoDoggy site.

---

## What we have now

| Page | Color | What it does |
|------|-------|-------------|
| `index.html` | 🟡 Gold | Main dashboard — prices, F&G, alerts |
| `game.html` | 🟢 Teal | Price prediction game |
| `meme.html` | 🟣 Purple | Meme zone, degen awards |
| `portfolio.html` | 🔵 Blue | Portfolio P&L tracker |

---

## New Product Options (pick one at session start)

### Option A — 📰 News Hub (`news.html`)
**Color:** Red/Orange  
A dedicated live news feed page. Filter by coin (BTC, ETH, etc.), category (DeFi, NFT, regulation), and sentiment. Cards show headline, source, time, and a sentiment badge (🟢 bullish / 🔴 bearish / ⚪ neutral). Uses CryptoCompare or CoinGecko news API.

**Why it's great:** Fills a real gap — right now news is buried in the dashboard. Makes the site feel like a full platform.

---

### Option B — 📡 Signals Page (`signals.html`)
**Color:** Cyan  
Technical signal scanner across all tracked coins. Shows RSI (overbought/oversold), 7d momentum direction, volume spike alerts, and an overall BUY / HOLD / SELL signal badge. All computed client-side from CoinGecko OHLC data.

**Why it's great:** Gives the site actual trading utility. Feels like a mini Bloomberg terminal.

---

### Option C — 🏆 Leaderboard (`leaderboard.html`)
**Color:** Yellow/Gold  
Persistent leaderboard for the prediction game. Players enter a username, predictions are tracked, and a scoreboard shows win rate, streak, total calls, and rank. Data stored in localStorage (could later be a shared backend).

**Why it's great:** Adds social/competitive layer to the game — makes people want to come back.

---

### Option D — 🐋 Whale Watch (`whales.html`)
**Color:** Deep blue  
Track unusual moves — coins with biggest volume spikes vs 7d average, biggest 24h movers, and a "whale alert" feed of notable on-chain style events (simulated from CoinGecko exchange volume data). Auto-refreshes every 60s.

**Why it's great:** High drama, very shareable content. "Something is moving" is crypto catnip.

---

## Recommended pick: **Option A (News Hub)** or **Option B (Signals)**

These have the most real utility and are fully buildable with free APIs. News Hub is flashier; Signals is more impressive technically.

---

## Session execution plan (once we pick)

1. **Scaffold the new HTML page** — nav, header, mood bar matching existing design system
2. **Wire up the API** — fetch and parse live data on load
3. **Build the main UI component** — cards, filters, badges
4. **Add to nav** on all 4 existing pages (index, game, meme, portfolio)
5. **Test + polish** — loading states, error handling, mobile layout
6. **Git commit command** — paste to clipboard for Ian to push

Estimated time: 1 session (~45–60 min of build time)

---

## Also queued (smaller wins if time allows)

- **Game leaderboard persistence** — save prediction history to localStorage so streaks survive page refresh
- **Alert configurator UI** — simple form on index.html to set custom price alert thresholds (writes to a config the bot reads)
- **Share button** on meme.html — generate a tweet-ready image of the degen/moon/rug awards

---

*Saved: 2026-05-09 — resume from here next session*
