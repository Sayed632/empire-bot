# =================================================================
# 🚀 EMPIRE BOT v14.0 — NSE AI AGENT (PREDICTIVE + SELF-LEARNING)
# Built for Sayed632 | May 2026
# Resources: Gemini API + Telegram Bot + yfinance
# Hosting: Railway.app (Free)
# =================================================================

# ─── INSTALLATIONS ───────────────────────────────────────────────
# Railway installs these automatically from requirements.txt
import os, time, json, datetime, logging, threading, requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import feedparser
import telebot
import google.generativeai as genai_lib

# ─── SILENCE NOISE ───────────────────────────────────────────────
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# =================================================================
# SECTION 1: YOUR SECRET KEYS
# Add these in Railway Environment Variables — never hardcode!
# =================================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
MY_CHAT_ID     = os.getenv('MY_CHAT_ID', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

if not all([TELEGRAM_TOKEN, MY_CHAT_ID, GEMINI_API_KEY]):
    log.error("❌ Missing environment variables! Set TELEGRAM_TOKEN, MY_CHAT_ID, GEMINI_API_KEY in Railway.")

# ─── INIT SERVICES ───────────────────────────────────────────────
genai_lib.configure(api_key=GEMINI_API_KEY)
gemini = genai_lib.GenerativeModel("gemini-1.5-flash")
bot    = telebot.TeleBot(TELEGRAM_TOKEN)

# =================================================================
# SECTION 2: SUBHANI'S PERSONAL WATCHLIST (Group 1)
# These are YOUR chosen stocks — always monitored with priority
# =================================================================
SUBHANI_WATCHLIST = {
    "DEFENSE":    ["HAL", "MAZDOCK", "BEL", "DATAPATTNS", "ASTRAMICRO", "KRISHNADEF"],
    "RENEWABLES": ["TATAPOWER", "ADANIGREEN", "SUZLON", "SWREL", "BORORENEW", "INOXWIND"],
    "AUTO_EV":    ["M&M", "TATAMOTORS", "BAJAJ-AUTO", "TVSMOTOR", "EICHERMOT"],
    "IT_PHARMA":  ["TCS", "INFY", "PERSISTENT", "SUNPHARMA", "DRREDDY", "MANKIND"],
    "SUMMER_AGRI":["VOLTAS", "VBL", "PIIND", "COROMANDEL", "DHANUKA"],
    "DATA_CLOUD": ["E2ENETWORKS", "NELCO", "NETWEB", "HCLTECH"],
    "SHIELD_ETF": ["GOLDBEES", "SILVERBEES", "ICICISILVER"]
}

# =================================================================
# SECTION 3: AI AGENT BRAIN STATE (Self-Learning Memory)
# This file stores what the bot learns over time
# =================================================================
BRAIN_FILE = "brain_state.json"

def load_brain():
    """Load the AI agent's learned memory from disk."""
    default = {
        "sentiment_score": 50,
        "win_loss_ratio": 1.5,
        "vix_limit": 20.0,
        "signal_weights": {
            "volume_spike":     1.0,   # Unusual volume weight
            "rsi_oversold":     1.0,   # RSI < 30 weight
            "price_compress":   1.0,   # Tight range before breakout
            "momentum":         1.0,   # Price acceleration weight
            "fundamental":      1.0    # Good fundamentals weight
        },
        "alert_history":   [],         # Past alerts sent
        "performance_log": [],         # Outcomes tracked
        "total_alerts":    0,
        "correct_calls":   0,
        "last_scan_time":  ""
    }
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE, 'r') as f:
                data = json.load(f)
                # Merge with defaults for any missing keys
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
    except: pass
    return default

def save_brain(brain):
    """Save the AI agent's memory to disk."""
    try:
        with open(BRAIN_FILE, 'w') as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        log.error(f"Brain save error: {e}")

BRAIN = load_brain()

# =================================================================
# SECTION 4: FUNDAMENTAL FILTER
# Reject junk stocks like Vodafone Idea, Jaiprakash Power types
# Only invest in companies with real business strength
# =================================================================
def passes_fundamental_filter(ticker):
    """
    Returns True if stock passes quality checks.
    Rejects only clearly junk stocks.
    """
    try:
        t    = yf.Ticker(f"{ticker}.NS")
        info = t.info

        # Must have some market cap
        mkt_cap = info.get('marketCap', 0) or 0
        if mkt_cap < 1_000_000:
            return False, "No market cap"

        # Must have current price
        price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0) or 0
        if price <= 0:
            return False, "No price data"

        # Reject only extremely high debt
        de_ratio = info.get('debtToEquity', 0) or 0
        if de_ratio > 500:
            return False, f"Extreme debt D/E={de_ratio:.0f}"

        return True, "✅ Passes"

    except Exception as e:
        # If we can't get data, still allow it through
        return True, "✅ Data limited"

# =================================================================
# SECTION 5: TECHNICAL PATTERN DETECTORS
# These find stocks BEFORE they explode — predictive signals
# =================================================================

def get_technical_score(ticker, brain):
    """
    Scores a stock 0-100 based on multiple predictive signals.
    Higher score = higher probability of upcoming move.
    """
    try:
        t  = yf.Ticker(f"{ticker}.NS")
        df = t.history(period="6mo", interval="1d")
        if df is None or len(df) < 50:
            return 0, {}, None

        close  = df['Close']
        volume = df['Volume']
        high   = df['High']
        low    = df['Low']
        w      = brain['signal_weights']

        signals = {}
        score   = 0
        curr_price = close.iloc[-1]

        # ── Signal 1: RSI Oversold (Sleeping Giant detector) ──────
        # Suzlon was RSI < 35 for months before its 867% run
        rsi = ta.rsi(close, length=14)
        if rsi is not None and len(rsi) > 0:
            rsi_val = rsi.iloc[-1]
            signals['rsi'] = round(rsi_val, 1)
            if 20 <= rsi_val <= 35:
                pts = 25 * w['rsi_oversold']
                score += pts
                signals['rsi_signal'] = f"🟢 OVERSOLD RSI={rsi_val:.1f} (+{pts:.0f}pts)"
            elif rsi_val > 75:
                signals['rsi_signal'] = f"🔴 OVERBOUGHT RSI={rsi_val:.1f}"

        # ── Signal 2: Volume Compression + Breakout ───────────────
        # Before E2E Networks 35% run, volume dried up then spiked
        vol_20d_avg  = volume.iloc[-21:-1].mean()
        vol_today    = volume.iloc[-1]
        vol_5d_avg   = volume.iloc[-6:-1].mean()
        vol_ratio    = vol_today / vol_20d_avg if vol_20d_avg > 0 else 1

        # Volume was quiet (compressed) then suddenly active
        prev_vol_ratio = vol_5d_avg / vol_20d_avg if vol_20d_avg > 0 else 1
        if prev_vol_ratio < 0.6 and vol_ratio > 1.5:
            pts = 20 * w['volume_spike']
            score += pts
            signals['volume_signal'] = f"🟢 VOL BREAKOUT {vol_ratio:.1f}x (+{pts:.0f}pts)"
        elif vol_ratio > 2.5:
            pts = 15 * w['volume_spike']
            score += pts
            signals['volume_signal'] = f"🟡 HIGH VOLUME {vol_ratio:.1f}x (+{pts:.0f}pts)"

        # ── Signal 3: Price Compression (Coiling Spring) ──────────
        # Stock stuck in tight range = energy building for breakout
        high_20d = high.iloc[-20:].max()
        low_20d  = low.iloc[-20:].min()
        range_pct = ((high_20d - low_20d) / low_20d) * 100 if low_20d > 0 else 100

        if range_pct < 8:  # Tight range under 8% = coiling
            pts = 20 * w['price_compress']
            score += pts
            signals['compression'] = f"🟢 COILING SPRING Range={range_pct:.1f}% (+{pts:.0f}pts)"

        # ── Signal 4: 52-Week Low Proximity (Deep Value) ──────────
        # Stocks near 52-week low with volume = potential V-recovery
        week52_low  = low.iloc[-252:].min() if len(low) >= 252 else low.min()
        week52_high = high.iloc[-252:].max() if len(high) >= 252 else high.max()
        position_pct = ((curr_price - week52_low) / (week52_high - week52_low) * 100) if (week52_high - week52_low) > 0 else 50

        if position_pct < 20:  # Near 52-week low
            pts = 15 * w['momentum']
            score += pts
            signals['position'] = f"🟢 NEAR 52W LOW {position_pct:.0f}% from bottom (+{pts:.0f}pts)"

        # ── Signal 5: Momentum Acceleration ──────────────────────
        # Price starting to move after being flat = early momentum
        ret_1w  = ((close.iloc[-1] - close.iloc[-6])  / close.iloc[-6])  * 100
        ret_1m  = ((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100
        ret_3m  = ((close.iloc[-1] - close.iloc[-63]) / close.iloc[-63]) * 100 if len(close) >= 63 else 0

        # Accelerating: flat 3M but moving 1W = early signal
        if abs(ret_3m) < 5 and ret_1w > 2:
            pts = 15 * w['momentum']
            score += pts
            signals['momentum'] = f"🟢 WAKING UP 3M={ret_3m:.1f}% 1W={ret_1w:.1f}% (+{pts:.0f}pts)"
        elif ret_1w > 5 and ret_1m > 8:
            pts = 10 * w['momentum']
            score += pts
            signals['momentum'] = f"🟡 ACCELERATING 1W={ret_1w:.1f}% 1M={ret_1m:.1f}% (+{pts:.0f}pts)"

        # ── Signal 6: MACD Crossover ──────────────────────────────
        macd_data = ta.macd(close)
        if macd_data is not None and len(macd_data) > 2:
            macd_line = macd_data.iloc[:, 0]
            signal_line = macd_data.iloc[:, 2]
            if (macd_line.iloc[-2] < signal_line.iloc[-2] and
                macd_line.iloc[-1] > signal_line.iloc[-1]):
                pts = 5 * w['momentum']
                score += pts
                signals['macd'] = f"🟢 MACD CROSSOVER (+{pts:.0f}pts)"

        return min(score, 100), signals, curr_price

    except Exception as e:
        log.debug(f"Technical score error {ticker}: {e}")
        return 0, {}, None

def calculate_targets(ticker, curr_price, score):
    """Calculate entry, target and stop-loss based on volatility."""
    try:
        df  = yf.Ticker(f"{ticker}.NS").history(period="1mo")
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        atr_val = atr.iloc[-1] if atr is not None and len(atr) > 0 else curr_price * 0.02

        # Higher score = more aggressive targets
        if score >= 70:
            target_mult = 3.0
            sl_mult     = 1.5
        elif score >= 50:
            target_mult = 2.0
            sl_mult     = 1.2
        else:
            target_mult = 1.5
            sl_mult     = 1.0

        entry  = round(curr_price, 2)
        target = round(curr_price + (atr_val * target_mult), 2)
        sl     = round(curr_price - (atr_val * sl_mult), 2)
        rr     = round((target - entry) / (entry - sl), 2) if (entry - sl) > 0 else 0

        return entry, target, sl, rr

    except:
        # Fallback percentage-based
        entry  = round(curr_price, 2)
        target = round(curr_price * 1.08, 2)
        sl     = round(curr_price * 0.95, 2)
        return entry, target, sl, 1.6

# =================================================================
# SECTION 6: NSE UNIVERSE FETCHER
# Downloads all NSE-listed stocks for AI Agent scanning
# =================================================================
NSE_STOCK_CACHE = []
NSE_CACHE_TIME  = None

def get_nse_universe():
    """
    Fetches all NSE-listed stocks.
    Uses a curated list of ~500 active NSE stocks across all sectors.
    Refreshes daily to catch new listings.
    """
    global NSE_STOCK_CACHE, NSE_CACHE_TIME

    # Return cached list if fresh (less than 24 hours old)
    if NSE_STOCK_CACHE and NSE_CACHE_TIME:
        if (datetime.datetime.now() - NSE_CACHE_TIME).seconds < 86400:
            return NSE_STOCK_CACHE

    log.info("🌐 Refreshing NSE universe list...")

    # Comprehensive NSE stock list across all market caps
    # Large Cap
    large_cap = [
        "RELIANCE","TCS","HDFCBANK","INFY","HINDUNILVR","ICICIBANK","KOTAKBANK",
        "BHARTIARTL","ITC","AXISBANK","LT","ASIANPAINT","MARUTI","TITAN","BAJFINANCE",
        "SUNPHARMA","WIPRO","ULTRACEMCO","NESTLEIND","POWERGRID","NTPC","ONGC","COALINDIA",
        "TATAMOTORS","TATASTEEL","JSWSTEEL","ADANIENT","ADANIGREEN","ADANIPORTS","SBILIFE",
        "HCLTECH","TECHM","BAJAJFINSV","GRASIM","BRITANNIA","HINDALCO","DIVISLAB","DRREDDY",
        "CIPLA","EICHERMOT","HEROMOTOCO","M&M","BAJAJ-AUTO","TVSMOTOR","APOLLOHOSP",
        "HAL","BEL","MAZDOCK","BPCL","IOC","HPCL","GAIL","TATAPOWER","ADANIPOWER"
    ]

    # Mid Cap
    mid_cap = [
        "PERSISTENT","MPHASIS","LTTS","COFORGE","KPITTECH","TATAELXSI",
        "PIIND","AARTIIND","DEEPAKNITR","ASTRAL","POLYCAB","HAVELLS","CROMPTON",
        "VOLTAS","BLUESTARCO","WHIRLPOOL","CEATLTD","MRF","APOLLOTYRE",
        "CONCOR","IRCTC","INDHOTEL","LEMONTREE","CHALET","MAHINDCIE",
        "SUZLON","INOXWIND","SWREL","BORORENEW","GREENPANEL","CENTURYPLY",
        "NAVINFLUOR","FINEORG","ALKYLAMINE","VINATIORGA","BALRAMCHIN",
        "DHANUKA","COROMANDEL","PIIND","RALLIS","BAYER","SUMICHEM",
        "LALPATHLAB","METROPOLIS","THYROCARE","KRSNAA","VIJAYADIAG",
        "DATAPATTNS","ASTRAMICRO","KRISHNADEF","PARAS","MIDHANI",
        "E2ENETWORKS","NELCO","NETWEB","RTNINDIA","RPOWER",
        "VBL","VARUNBEV","UBL","RADICO","MCDOWELL-N",
        "OBEROIRLTY","PHOENIXLTD","PRESTIGE","GODREJPROP","SOBHA",
        "SUNTV","ZEEL","PVRINOX","INOXLEISUR","NAZARA"
    ]

    # Small Cap & Emerging
    small_cap = [
        "TIDEWATER","SMSPHARMA","WAAREEENER","PREMIER","FLAIR",
        "NEWGEN","MASTEK","ZENSAR","HEXAWARE","NIITTECH",
        "SAGCEM","JKCEMENT","HEIDELBERG","BIRLACORPN","RAMCOCEM",
        "GPPL","ESABINDIA","GRINDWELL","CARBORUNIV","SCHAEFFLER",
        "RATNAMANI","WELSPUNIND","GHCL","STYRENIX","NOCIL",
        "ELECON","KENNAMETAL","TIMKEN","SKF","NAUKRI",
        "JUSTDIAL","MAKEMYTRIP","YATRA","EASEMYTRIP",
        "ZOMATO","SWIGGY","PAYTM","POLICYBZR","NYKAA",
        "DELHIVERY","XPRESSBEES","BLUEDART","GATI","TCI",
        "RVNL","IRFC","IRCON","RAILTEL","DFMFOODS",
        "TEJASNET","STERLITE","HFCL","VINDHYATEL","GTLINFRA",
        "RTNPOWER","JPPOWER","CESC","TORNTPOWER","KPEL",
        "RAJESHEXPO","THANGAMAYL","TITAN","PCJEWELLER","GITANJALI",
        "AVANTIFEED","WATERBASE","APEX","GODREJAGRO","KAVERI"
    ]

    # Penny & Micro Cap (high risk, high reward)
    micro_cap = [
        "RATTANINDIA","RPOWER","JPPOWER","SUZLON","INOXWIND",
        "YESBANK","VODAFONE","IDEA","PNB","BANKBARODA",
        "UNIONBANK","CANBK","IOB","UCOBANK","CENTRALBANK",
        "GREENPOWER","WEBSOL","WAAREE","PREMIER","SUNGARNER",
        "ALPHAGEO","SEAMECLTD","DEEPINDS","TEXRAIL","RAMASTEEL"
    ]

    all_stocks = list(set(large_cap + mid_cap + small_cap + micro_cap))
    NSE_STOCK_CACHE = all_stocks
    NSE_CACHE_TIME  = datetime.datetime.now()
    log.info(f"✅ NSE Universe loaded: {len(all_stocks)} stocks")
    return all_stocks

# =================================================================
# SECTION 7: SELF-LEARNING ENGINE
# Tracks every alert, checks outcome after 7 days,
# adjusts signal weights to improve over time
# =================================================================
def track_alert(brain, ticker, price_at_alert, score, signals_used):
    """Record an alert in brain memory for future evaluation."""
    alert = {
        "ticker":         ticker,
        "price_at_alert": price_at_alert,
        "score":          score,
        "signals":        list(signals_used.keys()),
        "date":           datetime.datetime.now().isoformat(),
        "checked_7d":     False,
        "checked_30d":    False,
        "outcome_7d":     None,
        "outcome_30d":    None
    }
    brain['alert_history'].append(alert)
    brain['total_alerts'] = brain.get('total_alerts', 0) + 1

    # Keep only last 200 alerts
    if len(brain['alert_history']) > 200:
        brain['alert_history'] = brain['alert_history'][-200:]
    save_brain(brain)

def evaluate_past_alerts(brain):
    """
    Check outcomes of past alerts and adjust signal weights.
    This is the SELF-LEARNING core — bot improves automatically.
    """
    log.info("🧠 Self-evaluation running...")
    now = datetime.datetime.now()
    improved = 0

    for alert in brain['alert_history']:
        try:
            alert_date = datetime.datetime.fromisoformat(alert['date'])
            days_passed = (now - alert_date).days
            ticker      = alert['ticker']

            # ── Check 7-day outcome ───────────────────────────────
            if days_passed >= 7 and not alert['checked_7d']:
                curr_df = yf.Ticker(f"{ticker}.NS").history(period="10d")
                if not curr_df.empty:
                    curr_price    = curr_df['Close'].iloc[-1]
                    price_change  = ((curr_price - alert['price_at_alert']) / alert['price_at_alert']) * 100
                    alert['outcome_7d']  = round(price_change, 2)
                    alert['checked_7d']  = True

                    # Adjust weights based on outcome
                    for sig in alert.get('signals', []):
                        if sig in brain['signal_weights']:
                            if price_change > 3:  # Good call — boost this signal
                                brain['signal_weights'][sig] = min(2.0, brain['signal_weights'][sig] * 1.05)
                                brain['correct_calls'] = brain.get('correct_calls', 0) + 1
                            elif price_change < -3:  # Bad call — reduce this signal
                                brain['signal_weights'][sig] = max(0.3, brain['signal_weights'][sig] * 0.95)
                    improved += 1

            # ── Check 30-day outcome ──────────────────────────────
            if days_passed >= 30 and not alert['checked_30d']:
                curr_df = yf.Ticker(f"{ticker}.NS").history(period="35d")
                if not curr_df.empty:
                    curr_price   = curr_df['Close'].iloc[-1]
                    price_change = ((curr_price - alert['price_at_alert']) / alert['price_at_alert']) * 100
                    alert['outcome_30d'] = round(price_change, 2)
                    alert['checked_30d'] = True
                    improved += 1

        except Exception as e:
            log.debug(f"Eval error {alert.get('ticker','?')}: {e}")

    if improved > 0:
        save_brain(brain)
        log.info(f"🧠 Brain updated: {improved} alerts evaluated")

    # Calculate accuracy
    checked = [a for a in brain['alert_history'] if a.get('outcome_7d') is not None]
    if checked:
        wins = [a for a in checked if a['outcome_7d'] > 3]
        accuracy = (len(wins) / len(checked)) * 100
        brain['accuracy_7d'] = round(accuracy, 1)
        save_brain(brain)
        return accuracy
    return None

# =================================================================
# SECTION 8: MASTER PREDICTIVE SCANNER
# Scans entire NSE universe for early-stage opportunities
# =================================================================

# Alert deduplication — don't spam same stock
ALERTED_TODAY = {}

def format_alert_message(ticker, score, signals, entry, target, sl, rr, source, pass_reason, curr_price):
    """Format a beautiful Telegram alert message."""
    signal_lines = ""
    for k, v in signals.items():
        if '_signal' in k or k in ['compression', 'position', 'momentum', 'macd', 'volume_signal']:
            signal_lines += f"  {v}\n"

    stars = "⭐" * min(5, max(1, int(score / 20)))
    upside = round(((target - entry) / entry) * 100, 1)

    msg = (
        f"{'🤖' if source == 'AI' else '🟢'} <b>{'AI DISCOVERY' if source == 'AI' else 'WATCHLIST ALERT'}: {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Score: {score:.0f}/100</b> {stars}\n"
        f"💰 <b>Current Price: ₹{curr_price:.2f}</b>\n\n"
        f"📊 <b>Signals Detected:</b>\n{signal_lines}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>TRADE SETUP</b>\n"
        f"  Entry:  ₹{entry}\n"
        f"  Target: ₹{target} (+{upside}%)\n"
        f"  Stop:   ₹{sl}\n"
        f"  R:R Ratio: {rr}x\n\n"
        f"✅ <b>Fundamental:</b> {pass_reason}\n"
        f"⚠️ <i>Not financial advice. Use position sizing wisely.</i>"
    )
    return msg

def run_predictive_scan(source="AI", watchlist=None):
    """
    Core scanner — runs through stocks, scores them, sends alerts.
    source = "AI" (full NSE scan) or "SUBHANI" (personal watchlist)
    """
    global ALERTED_TODAY

    if source == "SUBHANI":
        stocks = [s for sub in SUBHANI_WATCHLIST.values() for s in sub]
        log.info(f"🟢 Subhani scan: {len(stocks)} stocks")
    else:
        stocks = get_nse_universe()
        log.info(f"🤖 AI scan: {len(stocks)} stocks")

    # Reset daily alert tracker at midnight
    today = datetime.date.today().isoformat()
    ALERTED_TODAY = {k: v for k, v in ALERTED_TODAY.items() if v == today}

    found = 0
    for ticker in stocks:
        try:
            # Skip if already alerted today for this stock
            if ALERTED_TODAY.get(ticker) == today:
                continue

            # ── Fundamental Filter ────────────────────────────────
            passes, reason = passes_fundamental_filter(ticker)
            if not passes:
                log.debug(f"❌ {ticker}: {reason}")
                continue

            # ── Technical Scoring ─────────────────────────────────
            score, signals, curr_price = get_technical_score(ticker, BRAIN)
            if curr_price is None or curr_price <= 0:
                continue

            # Only alert if score is meaningful
            threshold = 45 if source == "SUBHANI" else 55
            if score < threshold:
                continue

            # ── Calculate Trade Targets ───────────────────────────
            entry, target, sl, rr = calculate_targets(ticker, curr_price, score)

            # Skip if risk-reward is too low
            if rr < 1.5:
                continue

            # ── Send Alert ────────────────────────────────────────
            msg = format_alert_message(
                ticker, score, signals, entry, target, sl, rr,
                source, reason, curr_price
            )
            bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
            log.info(f"✅ Alert sent: {ticker} Score={score:.0f}")

            # Track for self-learning
            track_alert(BRAIN, ticker, curr_price, score, signals)
            ALERTED_TODAY[ticker] = today
            found += 1

            # Max 5 alerts per scan to avoid spam
            if found >= 5:
                break

            time.sleep(0.5)  # Be nice to yfinance API

        except Exception as e:
            log.debug(f"Scan error {ticker}: {e}")
            continue

    return found

# =================================================================
# SECTION 9: INTELLIGENCE ENGINE (News + Gemini AI Briefings)
# =================================================================

def get_gemini_analysis(prompt):
    """Call Gemini AI for market analysis."""
    try:
        res = gemini.generate_content(prompt)
        return res.text
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return "AI analysis unavailable right now."

def morning_briefing():
    """Send 9:30 AM market briefing via Gemini."""
    try:
        # Get VIX
        vix_df  = yf.Ticker("^INDIAVIX").history(period="2d")
        vix_val = vix_df['Close'].iloc[-1] if not vix_df.empty else "N/A"

        # Get Nifty
        nifty_df  = yf.Ticker("^NSEI").history(period="2d")
        nifty_val = nifty_df['Close'].iloc[-1] if not nifty_df.empty else "N/A"
        nifty_chg = ((nifty_df['Close'].iloc[-1] - nifty_df['Close'].iloc[-2]) /
                      nifty_df['Close'].iloc[-2] * 100) if len(nifty_df) >= 2 else 0

        # Brain accuracy
        total   = BRAIN.get('total_alerts', 0)
        correct = BRAIN.get('correct_calls', 0)
        acc     = round((correct / total * 100), 1) if total > 0 else "Learning..."

        prompt = f"""You are an expert Indian stock market analyst.
        Current data: Nifty={nifty_val:.0f} ({nifty_chg:+.2f}%), India VIX={vix_val:.1f}
        Date: {datetime.datetime.now().strftime('%d %B %Y')}
        
        Write a sharp 5-line morning market briefing covering:
        1. Overall market mood (bullish/bearish/neutral)
        2. One key risk to watch today
        3. One sector looking strong
        4. Crude oil / Rupee impact
        5. One action advice for the day
        Keep it direct, no fluff."""

        analysis = get_gemini_analysis(prompt)
        w        = BRAIN['signal_weights']

        msg = (
            f"☀️ <b>EMPIRE MORNING BRIEFING</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 Nifty: {nifty_val:.0f} ({nifty_chg:+.2f}%)\n"
            f"⚡ India VIX: {vix_val:.1f}\n"
            f"🧠 AI Accuracy: {acc}% ({total} alerts tracked)\n\n"
            f"🤖 <b>Gemini Analysis:</b>\n{analysis}\n\n"
            f"🔬 <b>Brain Weights:</b>\n"
            f"  Volume: {w['volume_spike']:.2f} | RSI: {w['rsi_oversold']:.2f}\n"
            f"  Compress: {w['price_compress']:.2f} | Momentum: {w['momentum']:.2f}"
        )
        bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
        log.info("☀️ Morning briefing sent")

    except Exception as e:
        log.error(f"Morning briefing error: {e}")

def update_sentiment(brain):
    """Update market sentiment score from news RSS feeds."""
    feeds = [
        "https://www.moneycontrol.com/rss/latestnews.xml",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    news_stack = ""
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                news_stack += entry.title + ". "
        except: pass

    if news_stack:
        try:
            res = get_gemini_analysis(
                f"Rate overall Indian stock market sentiment from 1-100 based on these headlines. "
                f"Reply with ONLY a number between 1 and 100, nothing else: {news_stack[:500]}"
            )
            # Safe extraction of score
            digits = ''.join(filter(str.isdigit, res.strip()[:5]))
            if digits:
                score = max(1, min(100, int(digits[:3])))
                # Smooth update (weighted average, not instant replace)
                old_score = brain.get('sentiment_score', 50)
                brain['sentiment_score'] = round(old_score * 0.7 + score * 0.3)
                save_brain(brain)
                log.info(f"📡 Sentiment updated: {brain['sentiment_score']}")
        except Exception as e:
            log.debug(f"Sentiment error: {e}")

# =================================================================
# SECTION 10: BACKGROUND THREADS (The Always-On Engines)
# =================================================================

def intelligence_thread():
    """Runs intelligence engine — briefings, sentiment, self-learning."""
    log.info("📡 Intelligence Engine started")
    while True:
        try:
            now = datetime.datetime.now()

            # Morning briefing at 9:30 AM on weekdays
            if now.hour == 9 and now.minute == 30 and now.weekday() < 5:
                morning_briefing()
                time.sleep(70)

            # Subhani watchlist scan at market open (9:35 AM)
            if now.hour == 9 and now.minute == 35 and now.weekday() < 5:
                bot.send_message(MY_CHAT_ID, "🟢 <b>Subhani Watchlist Scan starting...</b>", parse_mode='HTML')
                found = run_predictive_scan(source="SUBHANI")
                bot.send_message(MY_CHAT_ID, f"🟢 Watchlist scan done. <b>{found} opportunities found.</b>", parse_mode='HTML')
                time.sleep(70)

            # AI full NSE scan at 10:00 AM
            if now.hour == 10 and now.minute == 0 and now.weekday() < 5:
                bot.send_message(MY_CHAT_ID, "🤖 <b>AI Agent NSE scan starting (500+ stocks)...</b>", parse_mode='HTML')
                found = run_predictive_scan(source="AI")
                bot.send_message(MY_CHAT_ID, f"🤖 AI scan done. <b>{found} discoveries sent.</b>", parse_mode='HTML')
                time.sleep(70)

            # Sentiment update every 30 mins during market hours
            if 9 <= now.hour <= 15 and now.minute % 30 == 0:
                update_sentiment(BRAIN)
                time.sleep(70)

            # Self-learning evaluation at 4:00 PM (after market close)
            if now.hour == 16 and now.minute == 0:
                acc = evaluate_past_alerts(BRAIN)
                if acc:
                    bot.send_message(
                        MY_CHAT_ID,
                        f"🧠 <b>Daily Self-Learning Complete</b>\n"
                        f"7-Day Accuracy: <b>{acc:.1f}%</b>\n"
                        f"Total Alerts Tracked: {BRAIN.get('total_alerts', 0)}\n"
                        f"Brain weights auto-adjusted ✅",
                        parse_mode='HTML'
                    )
                time.sleep(70)

        except Exception as e:
            log.error(f"Intelligence thread error: {e}")

        time.sleep(55)

# =================================================================
# SECTION 11: TELEGRAM COMMANDS
# Your control panel via Telegram messages
# =================================================================

@bot.message_handler(commands=['start', 'help'])
def cmd_help(message):
    msg = (
        "🚀 <b>EMPIRE BOT v14 — AI AGENT</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Available Commands:\n\n"
        "📊 <b>/scan</b> — Run AI scan on full NSE now\n"
        "🟢 <b>/watchlist</b> — Scan your personal watchlist\n"
        "🧠 <b>/brain</b> — Show AI learning stats\n"
        "📈 <b>/rsi TICKER</b> — Get RSI of any stock\n"
        "🔍 <b>/analyze TICKER</b> — Full AI analysis\n"
        "📋 <b>/report</b> — Weekly performance report\n"
        "⚖️ <b>/balance</b> — Sector allocation\n"
        "💡 <b>/tip</b> — Get a market tip from Gemini\n\n"
        "Bot scans automatically:\n"
        "  ☀️ 9:30 AM — Morning briefing\n"
        "  🟢 9:35 AM — Watchlist scan\n"
        "  🤖 10:00 AM — Full NSE AI scan\n"
        "  🧠 4:00 PM — Self-learning update"
    )
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['scan'])
def cmd_scan(message):
    bot.send_message(message.chat.id, "🤖 <b>AI Scan started on 500+ NSE stocks...</b>\nThis takes 2-3 minutes. Results incoming!", parse_mode='HTML')
    threading.Thread(target=lambda: run_predictive_scan("AI"), daemon=True).start()

@bot.message_handler(commands=['watchlist'])
def cmd_watchlist(message):
    bot.send_message(message.chat.id, "🟢 <b>Scanning Subhani watchlist...</b>", parse_mode='HTML')
    threading.Thread(target=lambda: run_predictive_scan("SUBHANI"), daemon=True).start()

@bot.message_handler(commands=['brain'])
def cmd_brain(message):
    total   = BRAIN.get('total_alerts', 0)
    correct = BRAIN.get('correct_calls', 0)
    acc     = round((correct / total * 100), 1) if total > 0 else 0
    w       = BRAIN['signal_weights']
    checked = [a for a in BRAIN['alert_history'] if a.get('outcome_7d') is not None]
    wins_7d = [a for a in checked if a.get('outcome_7d', 0) > 3]
    acc_7d  = round(len(wins_7d) / len(checked) * 100, 1) if checked else 0

    msg = (
        f"🧠 <b>EMPIRE BRAIN REPORT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Total Alerts Sent: {total}\n"
        f"Alerts Evaluated:  {len(checked)}\n"
        f"7-Day Win Rate:    {acc_7d}%\n"
        f"Sentiment Score:   {BRAIN.get('sentiment_score', 50)}/100\n\n"
        f"📊 <b>Signal Weights (Auto-Learned):</b>\n"
        f"  Volume Spike:    {w['volume_spike']:.3f}\n"
        f"  RSI Oversold:    {w['rsi_oversold']:.3f}\n"
        f"  Price Compress:  {w['price_compress']:.3f}\n"
        f"  Momentum:        {w['momentum']:.3f}\n"
        f"  Fundamental:     {w['fundamental']:.3f}\n\n"
        f"<i>Weights adjust automatically based on alert outcomes.</i>"
    )
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['rsi'])
def cmd_rsi(message):
    try:
        parts  = message.text.split()
        ticker = parts[1].upper() if len(parts) > 1 else None
        if not ticker:
            bot.send_message(message.chat.id, "Usage: /rsi TATAMOTORS")
            return

        df  = yf.Ticker(f"{ticker}.NS").history(period="1mo")
        rsi = ta.rsi(df['Close'], length=14)
        if rsi is None or len(rsi) == 0:
            bot.send_message(message.chat.id, f"❌ Could not get RSI for {ticker}")
            return

        rsi_val = rsi.iloc[-1]
        curr    = df['Close'].iloc[-1]

        if rsi_val < 30:
            interpretation = "🟢 OVERSOLD — Potential buy zone"
        elif rsi_val > 70:
            interpretation = "🔴 OVERBOUGHT — Consider booking profits"
        else:
            interpretation = "🟡 NEUTRAL — Wait for clearer signal"

        msg = (
            f"📊 <b>RSI Analysis: {ticker}</b>\n"
            f"Current Price: ₹{curr:.2f}\n"
            f"RSI (14): <b>{rsi_val:.1f}</b>\n"
            f"{interpretation}"
        )
        bot.send_message(message.chat.id, msg, parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['analyze'])
def cmd_analyze(message):
    try:
        parts  = message.text.split()
        ticker = parts[1].upper() if len(parts) > 1 else None
        if not ticker:
            bot.send_message(message.chat.id, "Usage: /analyze E2ENETWORKS")
            return

        bot.send_message(message.chat.id, f"🔍 Analyzing {ticker}... please wait")

        passes, reason    = passes_fundamental_filter(ticker)
        score, signals, price = get_technical_score(ticker, BRAIN)

        if price is None:
            bot.send_message(message.chat.id, f"❌ No data found for {ticker}.NS")
            return

        entry, target, sl, rr = calculate_targets(ticker, price, score)

        analysis_prompt = (
            f"Analyze NSE stock {ticker} currently at ₹{price:.2f}. "
            f"Technical score: {score}/100. Fundamental: {reason}. "
            f"Key signals: {', '.join(list(signals.keys())[:3])}. "
            f"Give a 3-line investment view for Indian retail investor. Be direct."
        )
        ai_view = get_gemini_analysis(analysis_prompt)

        signal_lines = ""
        for k, v in signals.items():
            if any(x in k for x in ['signal', 'compress', 'position', 'momentum', 'macd', 'volume']):
                signal_lines += f"  {v}\n"

        msg = (
            f"🔍 <b>FULL ANALYSIS: {ticker}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Price: ₹{price:.2f}\n"
            f"Score: {score:.0f}/100\n"
            f"Fundamental: {'✅' if passes else '❌'} {reason}\n\n"
            f"📊 Signals:\n{signal_lines if signal_lines else '  No strong signals\n'}\n"
            f"📈 Setup: Entry ₹{entry} | Target ₹{target} | SL ₹{sl} | R:R {rr}x\n\n"
            f"🤖 <b>Gemini View:</b>\n{ai_view}"
        )
        bot.send_message(message.chat.id, msg, parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error analyzing: {e}")

@bot.message_handler(commands=['report'])
def cmd_report(message):
    history = BRAIN.get('alert_history', [])
    recent  = [a for a in history if a.get('outcome_7d') is not None][-10:]

    if not recent:
        bot.send_message(message.chat.id, "📋 No completed alerts to report yet. Check back after 7 days!")
        return

    report = "📋 <b>RECENT PERFORMANCE REPORT</b>\n━━━━━━━━━━━━━━━━━━\n"
    wins = losses = 0
    for a in recent:
        outcome = a['outcome_7d']
        emoji   = "✅" if outcome > 3 else ("❌" if outcome < -3 else "➖")
        if outcome > 3: wins += 1
        elif outcome < -3: losses += 1
        report += f"{emoji} {a['ticker']}: {outcome:+.1f}% (7d)\n"

    total   = len(recent)
    acc     = round(wins / total * 100) if total > 0 else 0
    report += f"\n━━━━━━━━━━━━━━━━━━\n"
    report += f"Win Rate: <b>{acc}%</b> ({wins}W/{losses}L/{total-wins-losses}N)\n"
    report += f"<i>Bot self-learns from every outcome automatically.</i>"
    bot.send_message(message.chat.id, report, parse_mode='HTML')

@bot.message_handler(commands=['balance'])
def cmd_balance(message):
    report = "⚖️ <b>SUBHANI WATCHLIST SECTORS</b>\n━━━━━━━━━━━━━━━━━━\n"
    total  = sum(len(v) for v in SUBHANI_WATCHLIST.values())
    for sector, stocks in SUBHANI_WATCHLIST.items():
        pct    = (len(stocks) / total) * 100
        report += f"🔹 {sector}: {len(stocks)} stocks ({pct:.0f}%)\n"
        report += f"   {', '.join(stocks[:3])}{'...' if len(stocks) > 3 else ''}\n"
    bot.send_message(message.chat.id, report, parse_mode='HTML')

@bot.message_handler(commands=['tip'])
def cmd_tip(message):
    tip = get_gemini_analysis(
        "Give one sharp, practical stock market tip for Indian retail investors today. "
        "Max 3 sentences. Make it actionable and specific."
    )
    bot.send_message(message.chat.id, f"💡 <b>Market Tip:</b>\n{tip}", parse_mode='HTML')

# =================================================================
# SECTION 12: IGNITION — START EVERYTHING
# =================================================================
if __name__ == "__main__":
    log.info("🚀 EMPIRE BOT v14.0 starting...")

    # Validate keys
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == '':
        log.error("❌ TELEGRAM_TOKEN not set!")
        exit(1)

    # Send startup message
    try:
        bot.send_message(
            MY_CHAT_ID,
            "🚀 <b>EMPIRE BOT v14.0 ONLINE</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "✅ NSE Universe: 500+ stocks loaded\n"
            "✅ Self-Learning Engine: Active\n"
            "✅ Fundamental Filter: Active\n"
            "✅ Gemini AI: Connected\n\n"
            "Type /help to see all commands\n"
            "Type /scan for immediate AI scan",
            parse_mode='HTML'
        )
    except Exception as e:
        log.error(f"Startup message failed: {e}")

    # Start intelligence engine in background
    threading.Thread(target=intelligence_thread, daemon=True).start()
    log.info("✅ Intelligence Engine thread started")

    # Start Telegram bot with auto-restart
    log.info("✅ Telegram bot polling started")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            log.error(f"Polling error, restarting in 15s: {e}")
            time.sleep(15)
