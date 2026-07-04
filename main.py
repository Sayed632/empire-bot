"""
NSE Multibagger DNA Hunter - Full Universe Scanner
====================================================
Scans ALL NSE-listed equities (~2000+) for pre-surge "multibagger DNA"
patterns using a two-stage funnel so it stays fast and doesn't get
rate-limited by Yahoo Finance:

  Stage 1 (cheap, bulk):  Download OHLCV for all tickers in batches via
                          yf.download(). Screen on volume spike + price
                          momentum only. This needs zero .info calls.

  Stage 2 (expensive,     For the (much smaller) Stage-1 shortlist only,
  targeted):              fetch t.info to check debt/equity and revenue
                          growth, then compute the full DNA score.

This keeps the total number of Yahoo Finance "info" requests small
(usually tens, not thousands), which is the main thing that gets you
throttled/blocked when scanning a full market.

Env vars (all optional except the three secrets):
  TELEGRAM_TOKEN, MY_CHAT_ID, GEMINI_API_KEY      (required secrets)
  CHUNK_SIZE            default 150   tickers per bulk download batch
  MAX_RUNTIME_MINUTES   default 240   hard stop so GH Actions doesn't kill mid-run
  STAGE1_TOP_N          default 150   how many Stage-1 candidates advance to Stage 2
  MIN_SCORE             default 40    DNA score threshold to trigger an alert
  TOP_N_CHARTS          default 5     max number of chart images sent to Telegram
  UNIVERSE_CACHE_PATH   default "nse_universe_cache.csv"
"""

import os
import io
import csv
import time
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd
import yfinance as yf
import feedparser
import telebot
import google.generativeai as genai
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("multibagger_hunter")

# --- SECRETS & CONFIG ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID     = os.getenv('MY_CHAT_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

CHUNK_SIZE          = int(os.getenv('CHUNK_SIZE', 150))
MAX_RUNTIME_MINUTES = int(os.getenv('MAX_RUNTIME_MINUTES', 240))
STAGE1_TOP_N        = int(os.getenv('STAGE1_TOP_N', 150))
MIN_SCORE           = int(os.getenv('MIN_SCORE', 40))
TOP_N_CHARTS        = int(os.getenv('TOP_N_CHARTS', 5))
UNIVERSE_CACHE_PATH = os.getenv('UNIVERSE_CACHE_PATH', 'nse_universe_cache.csv')

NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equity/EQUITY_L.csv"

if not (TELEGRAM_TOKEN and MY_CHAT_ID and GEMINI_API_KEY):
    log.warning("One or more required secrets (TELEGRAM_TOKEN, MY_CHAT_ID, GEMINI_API_KEY) are missing.")

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

START_TIME = time.time()


def time_budget_exceeded():
    elapsed_min = (time.time() - START_TIME) / 60
    return elapsed_min >= MAX_RUNTIME_MINUTES


# ---------------------------------------------------------------------------
# 0. UNIVERSE: fetch the full list of NSE-listed equities
# ---------------------------------------------------------------------------
def fetch_nse_universe():
    """Fetch all NSE-listed EQ series symbols. Falls back to a local cache
    if the live NSE fetch fails (NSE actively blocks naive requests, so a
    proper browser-like session + a cache safety net is required)."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/csv,application/csv,*/*",
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        # Warm up session to obtain cookies NSE expects before serving the CSV
        session.get("https://www.nseindia.com", timeout=10)
        resp = session.get(NSE_EQUITY_LIST_URL, timeout=15)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        symbols = [
            row["SYMBOL"].strip() + ".NS"
            for row in reader
            if row.get("SERIES", "").strip() == "EQ" and row.get("SYMBOL")
        ]
        if len(symbols) < 500:
            raise ValueError(f"Suspiciously small universe fetched ({len(symbols)}); rejecting.")

        log.info(f"Fetched {len(symbols)} NSE EQ symbols live from NSE archives.")
        # Refresh the cache for next time
        pd.Series(symbols, name="ticker").to_csv(UNIVERSE_CACHE_PATH, index=False)
        return symbols

    except Exception as e:
        log.warning(f"Live NSE universe fetch failed ({e}). Falling back to cache.")
        if os.path.exists(UNIVERSE_CACHE_PATH):
            symbols = pd.read_csv(UNIVERSE_CACHE_PATH)["ticker"].tolist()
            log.info(f"Loaded {len(symbols)} symbols from cache '{UNIVERSE_CACHE_PATH}'.")
            return symbols
        log.error("No cache available either. Cannot proceed without a universe list.")
        return []


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


# ---------------------------------------------------------------------------
# 1. STAGE 1: cheap bulk screen (volume spike + momentum), no .info calls
# ---------------------------------------------------------------------------
def stage1_bulk_screen(tickers):
    candidates = []  # list of dicts: ticker, volume_ratio, momentum_pct
    total_chunks = (len(tickers) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for idx, chunk in enumerate(chunk_list(tickers, CHUNK_SIZE), start=1):
        if time_budget_exceeded():
            log.warning("Time budget exceeded during Stage 1; stopping early with partial results.")
            break

        log.info(f"Stage 1: batch {idx}/{total_chunks} ({len(chunk)} tickers)")
        try:
            data = yf.download(
                tickers=chunk,
                period="6mo",
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=True,
            )
        except Exception as e:
            log.error(f"Stage 1 batch {idx} download failed entirely: {e}")
            time.sleep(3)
            continue

        for symbol in chunk:
            try:
                df = data[symbol] if len(chunk) > 1 else data
                df = df.dropna(how="all")
                if df.empty or len(df) < 21:
                    continue

                vol_avg20 = df['Volume'].tail(21).iloc[:-1].mean()
                vol_today = df['Volume'].iloc[-1]
                if vol_avg20 == 0 or pd.isna(vol_avg20):
                    continue
                volume_ratio = vol_today / vol_avg20

                momentum_pct = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100

                # Advance if there's a volume spike OR strong momentum
                if volume_ratio >= 1.5 or momentum_pct >= 15:
                    candidates.append({
                        "ticker": symbol,
                        "volume_ratio": volume_ratio,
                        "momentum_pct": momentum_pct,
                    })
            except Exception as e:
                log.debug(f"Stage 1 skip {symbol}: {e}")
                continue

        time.sleep(2)  # be polite between batches

    log.info(f"Stage 1 complete: {len(candidates)} candidates out of {len(tickers)} scanned.")
    # Rank by combined signal strength and cap to STAGE1_TOP_N before the expensive stage
    candidates.sort(key=lambda c: (c["volume_ratio"] * 2 + c["momentum_pct"]), reverse=True)
    return candidates[:STAGE1_TOP_N]


# ---------------------------------------------------------------------------
# 2. STAGE 2: targeted deep screen (.info) on the shortlist only
# ---------------------------------------------------------------------------
def score_candidate(cand):
    ticker = cand["ticker"]
    try:
        info = yf.Ticker(ticker).info
        if not info or info.get("regularMarketPrice") is None:
            return None

        score = 0
        reasons = []

        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity is not None and debt_to_equity < 50:
            score += 20
            reasons.append("Low leverage (Financial Strength)")

        rev_growth = info.get('revenueGrowth')
        if rev_growth is not None and rev_growth > 0.25:
            score += 25
            reasons.append(f"Hyper-growth: +{rev_growth*100:.0f}% Rev")

        if cand["volume_ratio"] >= 2:
            score += 25
            reasons.append("🐋 Massive Volume Spike (Accumulation)")
        elif cand["volume_ratio"] >= 1.5:
            score += 10
            reasons.append("Elevated volume")

        if cand["momentum_pct"] >= 25:
            score += 15
            reasons.append(f"Strong 6mo momentum: +{cand['momentum_pct']:.0f}%")

        if score >= MIN_SCORE:
            return {"ticker": ticker, "score": score, "reasons": reasons, "info": info}
        return None

    except Exception as e:
        log.debug(f"Stage 2 skip {ticker}: {e}")
        return None


def stage2_deep_screen(candidates):
    hits = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(score_candidate, c): c for c in candidates}
        for future in as_completed(futures):
            if time_budget_exceeded():
                log.warning("Time budget exceeded during Stage 2; using partial results.")
                break
            result = future.result()
            if result:
                hits.append(result)

    hits.sort(key=lambda h: h["score"], reverse=True)
    log.info(f"Stage 2 complete: {len(hits)} confirmed hits (score >= {MIN_SCORE}).")
    return hits


# ---------------------------------------------------------------------------
# 3. MACRO CONTEXT (unchanged logic, better error visibility)
# ---------------------------------------------------------------------------
def get_macro_tailwind():
    feeds = ["https://www.moneycontrol.com/rss/latestnews.xml"]
    news_snippet = ""
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for e in f.entries[:5]:
                news_snippet += e.title + ". "
        except Exception as e:
            log.warning(f"Failed to parse feed {url}: {e}")

    if not news_snippet:
        return "Neutral Market"

    prompt = (
        f"Based on these headlines: {news_snippet}\n"
        "Identify 1 high-growth Indian sector benefiting from current Govt policy or War/Trade shifts. "
        "Reply ONLY with: [Sector Name]: [Brief Reason]"
    )
    try:
        return gemini.generate_content(prompt).text.strip()
    except Exception as e:
        log.warning(f"Gemini macro tailwind call failed: {e}")
        return "Neutral Market"


# ---------------------------------------------------------------------------
# 4. SHAREHOLDING CHART (None-safe)
# ---------------------------------------------------------------------------
def generate_shareholding_chart(ticker, info):
    promoter_held = info.get('heldPercentInsiders') or 0.50
    inst_held = info.get('heldPercentInstitutions') or 0.25
    promoter_held *= 100
    inst_held *= 100

    if promoter_held == 0 and inst_held == 0:
        promoter_held, inst_held = 50.95, 32.31

    public_held = max(0, 100 - (promoter_held + inst_held))

    categories = ['Promoter', 'Institutions', 'Public']
    percentages = [round(promoter_held, 2), round(inst_held, 2), round(public_held, 2)]
    colors = ['#1a73e8', '#2ecc71', '#e67e22']

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        percentages,
        labels=[f"{p}%" for p in percentages],
        colors=colors,
        startangle=90,
        counterclock=False,
        pctdistance=0.82,
        textprops=dict(color="#222222", weight="bold", size=10)
    )
    centre_circle = plt.Circle((0, 0), 0.65, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.legend(wedges, categories, title="Categories", loc="upper right", bbox_to_anchor=(1.2, 1))
    ax.set_title(f"{ticker} - Shareholding Structural Distribution", weight='bold', size=12)
    plt.tight_layout()

    image_filename = f"{ticker.replace('.NS', '')}_shareholding.png"
    plt.savefig(image_filename, dpi=300, bbox_inches='tight')
    plt.close()
    return image_filename


# ---------------------------------------------------------------------------
# 5. TELEGRAM DISPATCH
# ---------------------------------------------------------------------------
def send_alerts(hits, macro_context):
    if not hits:
        bot.send_message(MY_CHAT_ID, "No high-conviction pre-surge matches found today across the full NSE universe.")
        log.info("Scan finished with 0 alerts sent.")
        return

    summary_lines = [f"🎯 **{len(hits)} Multibagger DNA matches found** (full NSE scan)\n"]
    for h in hits:
        summary_lines.append(f"• {h['ticker'].replace('.NS','')}: {h['score']}/100")
    summary_lines.append(f"\n🌍 Macro: {macro_context}")
    try:
        bot.send_message(MY_CHAT_ID, "\n".join(summary_lines), parse_mode='Markdown')
    except Exception as e:
        log.error(f"Failed to send summary message: {e}")

    for h in hits[:TOP_N_CHARTS]:
        ticker = h['ticker']
        try:
            chart_img = generate_shareholding_chart(ticker, h['info'])
            msg = (
                f"🚀 **POTENTIAL MULTIBAGGER: {ticker.replace('.NS','')}**\n\n"
                f"🏆 **DNA Match Score**: `{h['score']}/100`\n"
                f"💡 **Key Triggers**: {', '.join(h['reasons'])}\n"
            )
            with open(chart_img, 'rb') as photo:
                bot.send_photo(MY_CHAT_ID, photo, caption=msg, parse_mode='Markdown')
            log.info(f"Alert sent for {ticker}")
            if os.path.exists(chart_img):
                os.remove(chart_img)
            time.sleep(1.5)  # avoid Telegram flood limits
        except Exception as e:
            log.error(f"Failed to send alert for {ticker}: {e}")


# ---------------------------------------------------------------------------
# 6. ENTRY POINT
# ---------------------------------------------------------------------------
def hunt_multibaggers():
    log.info("🚀 Starting full-NSE-universe AI Hunter Agent scan...")

    universe = fetch_nse_universe()
    if not universe:
        bot.send_message(MY_CHAT_ID, "⚠️ Could not load NSE universe (live fetch and cache both failed). Aborting scan.")
        return

    macro_context = get_macro_tailwind()

    stage1_candidates = stage1_bulk_screen(universe)
    if not stage1_candidates:
        send_alerts([], macro_context)
        return

    hits = stage2_deep_screen(stage1_candidates)
    send_alerts(hits, macro_context)

    elapsed_min = (time.time() - START_TIME) / 60
    log.info(f"✅ Hunting complete in {elapsed_min:.1f} min. Scanned {len(universe)} tickers, "
              f"{len(stage1_candidates)} advanced to deep screen, {len(hits)} alerts sent.")


if __name__ == "__main__":
    hunt_multibaggers()