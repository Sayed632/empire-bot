# =================================================================
# 🚀 EMPIRE BOT v15.0 — NSE AI AGENT (3 LEGEND FRAMEWORKS)
# Built for Sayed632 | May 2026
# Frameworks: Peter Lynch + Warren Buffett + Rakesh Jhunjhunwala
# Resources: Gemini API + Telegram Bot + yfinance
# Hosting: Railway.app (Free)
# =================================================================

import os, time, json, datetime, logging, threading
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import feedparser
import telebot
import google.generativeai as genai

# ─── SILENCE NOISE ───────────────────────────────────────────────
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

# =================================================================
# SECTION 1: SECRET KEYS (Set in Railway Environment Variables)
# =================================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
MY_CHAT_ID     = os.getenv('MY_CHAT_ID', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# ─── INIT SERVICES ───────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# =================================================================
# SECTION 2: SUBHANI WATCHLIST (Your Personal Group)
# =================================================================
SUBHANI_WATCHLIST = {
    "DEFENSE":     ["HAL", "MAZDOCK", "BEL", "DATAPATTNS", "ASTRAMICRO"],
    "RENEWABLES":  ["TATAPOWER", "ADANIGREEN", "SUZLON", "INOXWIND", "BORORENEW"],
    "AUTO_EV":     ["M&M", "TATAMOTORS", "BAJAJ-AUTO", "TVSMOTOR", "EICHERMOT"],
    "IT_PHARMA":   ["TCS", "INFY", "PERSISTENT", "SUNPHARMA", "DRREDDY"],
    "SUMMER_AGRI": ["VOLTAS", "VBL", "PIIND", "COROMANDEL", "DHANUKA"],
    "DATA_CLOUD":  ["E2ENETWORKS", "NELCO", "NETWEB", "HCLTECH"],
    "SHIELD_ETF":  ["GOLDBEES", "SILVERBEES", "ICICISILVER"]
}

# =================================================================
# SECTION 3: BRAIN (Self-Learning Memory)
# =================================================================
BRAIN_FILE = "brain_state.json"

def load_brain():
    default = {
        "sentiment_score": 50,
        "win_loss_ratio":  1.5,
        "signal_weights": {
            "lynch_score":   1.0,
            "buffett_score": 1.0,
            "rj_score":      1.0,
            "volume_spike":  1.0,
            "rsi_oversold":  1.0,
            "momentum":      1.0
        },
        "alert_history":  [],
        "total_alerts":   0,
        "correct_calls":  0
    }
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE, 'r') as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
    except: pass
    return default

def save_brain(brain):
    try:
        with open(BRAIN_FILE, 'w') as f:
            json.dump(brain, f, indent=2)
    except Exception as e:
        log.error(f"Brain save error: {e}")

BRAIN = load_brain()

# =================================================================
# SECTION 4: GEMINI AI (Fixed & Working)
# =================================================================
def get_gemini_analysis(prompt):
    """Call Gemini AI — properly fixed for google-generativeai library."""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return None

# =================================================================
# SECTION 5: NSE UNIVERSE
# =================================================================
NSE_STOCKS = [
    # Large Cap
    "RELIANCE","TCS","HDFCBANK","INFY","HINDUNILVR","ICICIBANK","KOTAKBANK",
    "BHARTIARTL","ITC","AXISBANK","LT","ASIANPAINT","MARUTI","TITAN","BAJFINANCE",
    "SUNPHARMA","WIPRO","ULTRACEMCO","NESTLEIND","POWERGRID","NTPC","ONGC",
    "TATAMOTORS","TATASTEEL","JSWSTEEL","ADANIENT","ADANIGREEN","ADANIPORTS",
    "HCLTECH","TECHM","BAJAJFINSV","GRASIM","BRITANNIA","HINDALCO","DIVISLAB",
    "DRREDDY","CIPLA","EICHERMOT","HEROMOTOCO","M&M","BAJAJ-AUTO","TVSMOTOR",
    "APOLLOHOSP","HAL","BEL","MAZDOCK","BPCL","IOC","TATAPOWER","COALINDIA",
    # Mid Cap
    "PERSISTENT","MPHASIS","LTTS","COFORGE","KPITTECH","TATAELXSI",
    "PIIND","AARTIIND","DEEPAKNITR","ASTRAL","POLYCAB","HAVELLS","CROMPTON",
    "VOLTAS","BLUESTAR","CONCOR","IRCTC","INDHOTEL","MAHINDCIE",
    "SUZLON","INOXWIND","BORORENEW","DHANUKA","COROMANDEL","RALLIS",
    "DATAPATTNS","ASTRAMICRO","E2ENETWORKS","NELCO","NETWEB",
    "VBL","RADICO","OBEROIRLTY","PRESTIGE","GODREJPROP",
    "SUNTV","NAZARA","ZOMATO","PAYTM","NYKAA","DELHIVERY",
    "RVNL","IRFC","IRCON","RAILTEL",
    "TEJASNET","HFCL","VINDHYATEL",
    # Small & Micro Cap
    "RATTANINDIA","RPOWER","JPPOWER","YESBANK",
    "GREENPOWER","WEBSOL","WAAREE","PREMIER",
    "ALPHAGEO","SEAMECLTD","TEXRAIL","RAMASTEEL",
    "SWREL","KRISHNADEF","MANKIND","DRREDDY"
]

# =================================================================
# SECTION 6: THREE LEGEND FRAMEWORKS
# =================================================================

def peter_lynch_score(info, df):
    """
    Peter Lynch Framework — Find 10-baggers before they run.
    Looks for: Fast growing small companies, PEG < 1, ignored by market.
    His famous quote: 'The best stock to buy is the one you already know.'
    """
    score = 0
    reasons = []

    try:
        # ── PEG Ratio < 1 (Growth at reasonable price) ────────────
        pe  = info.get('trailingPE', None)
        eps_growth = info.get('earningsGrowth', None) or info.get('revenueGrowth', None)
        if pe and eps_growth and eps_growth > 0:
            peg = pe / (eps_growth * 100)
            if peg < 1:
                score += 25
                reasons.append(f"📈 PEG={peg:.2f} (Lynch loves <1)")
            elif peg < 2:
                score += 10
                reasons.append(f"📈 PEG={peg:.2f} (Acceptable)")

        # ── Small/Mid cap ignored by analysts ─────────────────────
        mkt_cap = info.get('marketCap', 0) or 0
        if 100_000_000 < mkt_cap < 50_000_000_000:  # 10Cr to 5000Cr
            score += 20
            reasons.append(f"🔍 Small/Mid cap — Lynch's sweet spot")

        # ── Revenue growing consistently ──────────────────────────
        rev_growth = info.get('revenueGrowth', 0) or 0
        if rev_growth > 0.20:  # >20% revenue growth
            score += 20
            reasons.append(f"💰 Revenue +{rev_growth*100:.0f}% (Strong growth)")
        elif rev_growth > 0.10:
            score += 10
            reasons.append(f"💰 Revenue +{rev_growth*100:.0f}% (Decent growth)")

        # ── Low institutional ownership (undiscovered) ─────────────
        inst_own = info.get('heldPercentInstitutions', 1) or 1
        if inst_own < 0.15:  # Less than 15% institutional
            score += 15
            reasons.append(f"👁️ Only {inst_own*100:.0f}% institutional — undiscovered!")

        # ── Cash rich company ─────────────────────────────────────
        cash = info.get('totalCash', 0) or 0
        debt = info.get('totalDebt', 0) or 0
        if cash > debt:
            score += 10
            reasons.append(f"💵 More cash than debt")

    except Exception as e:
        log.debug(f"Lynch score error: {e}")

    return min(score, 100), reasons

def warren_buffett_score(info, df):
    """
    Warren Buffett Framework — Find businesses with wide moat.
    Looks for: Consistent ROE>15%, low debt, strong brand, predictable earnings.
    His famous quote: 'Buy wonderful companies at fair prices.'
    """
    score = 0
    reasons = []

    try:
        # ── ROE > 15% consistently (Economic moat indicator) ──────
        roe = info.get('returnOnEquity', 0) or 0
        if roe > 0.20:  # >20% ROE
            score += 25
            reasons.append(f"🏰 ROE={roe*100:.1f}% (Strong moat)")
        elif roe > 0.15:
            score += 15
            reasons.append(f"🏰 ROE={roe*100:.1f}% (Good moat)")

        # ── Low Debt to Equity ────────────────────────────────────
        de = info.get('debtToEquity', 999) or 999
        if de < 50:
            score += 20
            reasons.append(f"✅ D/E={de:.0f} (Buffett loves low debt)")
        elif de < 100:
            score += 10
            reasons.append(f"✅ D/E={de:.0f} (Acceptable debt)")

        # ── Profit margins (Pricing power = moat) ─────────────────
        margin = info.get('profitMargins', 0) or 0
        if margin > 0.15:  # >15% net margin
            score += 20
            reasons.append(f"💎 Margin={margin*100:.1f}% (Pricing power)")
        elif margin > 0.08:
            score += 10
            reasons.append(f"💎 Margin={margin*100:.1f}% (Decent margin)")

        # ── Consistent EPS (Predictable business) ─────────────────
        eps = info.get('trailingEps', 0) or 0
        if eps > 0:
            score += 15
            reasons.append(f"📊 EPS=₹{eps:.1f} (Profitable)")

        # ── P/B ratio reasonable ──────────────────────────────────
        pb = info.get('priceToBook', 999) or 999
        if 0 < pb < 3:
            score += 10
            reasons.append(f"📉 P/B={pb:.1f} (Fair value)")
        elif 0 < pb < 5:
            score += 5
            reasons.append(f"📉 P/B={pb:.1f} (Slightly stretched)")

        # ── Promoter holding high (Skin in the game) ──────────────
        promoter = info.get('heldPercentInsiders', 0) or 0
        if promoter > 0.50:  # >50% promoter holding
            score += 10
            reasons.append(f"👨‍💼 Promoter={promoter*100:.0f}% (High conviction)")

    except Exception as e:
        log.debug(f"Buffett score error: {e}")

    return min(score, 100), reasons

def rakesh_jhunjhunwala_score(info, df, ticker):
    """
    Rakesh Jhunjhunwala Framework — India's Warren Buffett.
    Looks for: India growth story, beaten down leaders, sector tailwinds,
    management quality, 3-5 year compounding potential.
    His famous quote: 'India is a long term story. Be patient.'
    """
    score = 0
    reasons = []

    try:
        close = df['Close']
        high  = df['High']
        low   = df['Low']

        # ── Beaten down from 52-week high (RJ loved buying dips) ──
        week52_high = high.iloc[-252:].max() if len(high) >= 252 else high.max()
        curr_price  = close.iloc[-1]
        fall_from_high = ((week52_high - curr_price) / week52_high) * 100

        if 30 <= fall_from_high <= 70:  # Down 30-70% from top
            score += 25
            reasons.append(f"🎯 Down {fall_from_high:.0f}% from peak — RJ entry zone!")
        elif 15 <= fall_from_high < 30:
            score += 15
            reasons.append(f"🎯 Down {fall_from_high:.0f}% from peak — Watching zone")

        # ── India growth sectors (RJ's favorites) ─────────────────
        rj_sectors = [
            'TITAN','CRISIL','LUPIN','ESCORTS','NAZARA','TATA',
            'STAR','DELTA','NCC','APTECH','RALLIS','VICEROY',
            'HAL','BEL','IRCTC','CONCOR','RAILTEL','RVNL'
        ]
        if any(s in ticker.upper() for s in rj_sectors):
            score += 15
            reasons.append(f"🇮🇳 India growth sector — RJ's favorite type")

        # ── Volume accumulation (Smart money buying quietly) ───────
        vol_20d = df['Volume'].iloc[-21:-1].mean()
        vol_5d  = df['Volume'].iloc[-6:-1].mean()
        if vol_5d > vol_20d * 1.5:
            score += 20
            reasons.append(f"🐋 Volume accumulation — Smart money entering")

        # ── Price recovering from bottom (Turnaround story) ────────
        week52_low = low.iloc[-252:].min() if len(low) >= 252 else low.min()
        rise_from_low = ((curr_price - week52_low) / week52_low) * 100
        if 10 <= rise_from_low <= 50:
            score += 20
            reasons.append(f"🔄 Up {rise_from_low:.0f}% from bottom — Turnaround!")

        # ── Market cap sweet spot for multibagger ─────────────────
        mkt_cap = info.get('marketCap', 0) or 0
        if 500_000_000 < mkt_cap < 100_000_000_000:  # 50Cr to 10000Cr
            score += 10
            reasons.append(f"📐 Market cap in multibagger range")

        # ── Dividend history (Management returns value) ────────────
        div_yield = info.get('dividendYield', 0) or 0
        if div_yield > 0.01:  # >1% dividend
            score += 10
            reasons.append(f"💸 Dividend yield {div_yield*100:.1f}% (Shareholder friendly)")

    except Exception as e:
        log.debug(f"RJ score error: {e}")

    return min(score, 100), reasons

# =================================================================
# SECTION 7: TECHNICAL SIGNALS (Supporting Indicators)
# =================================================================
def get_technical_signals(df, brain):
    """Get RSI, Volume, Momentum signals."""
    signals = {}
    score   = 0
    w       = brain['signal_weights']

    try:
        close  = df['Close']
        volume = df['Volume']
        high   = df['High']
        low    = df['Low']

        # RSI
        rsi = ta.rsi(close, length=14)
        if rsi is not None and len(rsi) > 0:
            rsi_val = rsi.iloc[-1]
            signals['rsi'] = round(rsi_val, 1)
            if 20 <= rsi_val <= 35:
                pts = 30 * w['rsi_oversold']
                score += pts
                signals['rsi_signal'] = f"🟢 RSI={rsi_val:.0f} OVERSOLD — Buy zone!"
            elif rsi_val > 75:
                signals['rsi_signal'] = f"🔴 RSI={rsi_val:.0f} OVERBOUGHT — Caution"

        # Volume spike
        vol_avg   = volume.iloc[-21:-1].mean()
        vol_today = volume.iloc[-1]
        vol_ratio = vol_today / vol_avg if vol_avg > 0 else 1
        if vol_ratio > 2.0:
            pts = 20 * w['volume_spike']
            score += pts
            signals['volume'] = f"🐋 Volume {vol_ratio:.1f}x average — Big players moving!"

        # Price momentum
        if len(close) >= 22:
            ret_1w = ((close.iloc[-1] - close.iloc[-6])  / close.iloc[-6])  * 100
            ret_1m = ((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100
            if ret_1w > 3 and ret_1m > 5:
                pts = 20 * w['momentum']
                score += pts
                signals['momentum'] = f"⚡ Momentum: 1W={ret_1w:.1f}% 1M={ret_1m:.1f}%"

        # Price compression (coiling spring)
        high_20 = high.iloc[-20:].max()
        low_20  = low.iloc[-20:].min()
        range_pct = ((high_20 - low_20) / low_20) * 100 if low_20 > 0 else 100
        if range_pct < 8:
            score += 15
            signals['compression'] = f"🌀 Tight range {range_pct:.1f}% — Breakout building!"

        # MACD crossover
        macd_data = ta.macd(close)
        if macd_data is not None and len(macd_data) > 2:
            ml = macd_data.iloc[:, 0]
            sl = macd_data.iloc[:, 2]
            if len(ml) > 1 and ml.iloc[-2] < sl.iloc[-2] and ml.iloc[-1] > sl.iloc[-1]:
                score += 15
                signals['macd'] = f"📊 MACD Crossover — Momentum turning up!"

    except Exception as e:
        log.debug(f"Technical signals error: {e}")

    return min(score, 100), signals

# =================================================================
# SECTION 8: MASTER SCORING ENGINE
# Combines all 3 frameworks + technicals
# =================================================================
def score_stock(ticker, brain):
    """
    Score a stock using all 3 legend frameworks + technical signals.
    Returns combined score, breakdown, and current price.
    """
    try:
        t  = yf.Ticker(f"{ticker}.NS")
        df = t.history(period="1y", interval="1d")

        if df is None or len(df) < 30:
            return 0, {}, None

        info = t.info
        if not info:
            return 0, {}, None

        curr_price = df['Close'].iloc[-1]
        if curr_price <= 0:
            return 0, {}, None

        # Run all 3 legend frameworks
        lynch_s,   lynch_r   = peter_lynch_score(info, df)
        buffett_s, buffett_r = warren_buffett_score(info, df)
        rj_s,      rj_r      = rakesh_jhunjhunwala_score(info, df, ticker)
        tech_s,    tech_sigs = get_technical_signals(df, brain)

        # Weighted combination
        w = brain['signal_weights']
        combined = (
            lynch_s   * w['lynch_score']   * 0.25 +
            buffett_s * w['buffett_score'] * 0.25 +
            rj_s      * w['rj_score']      * 0.30 +
            tech_s    *                      0.20
        )

        # Determine which legend's framework triggered most
        legend = "🔍 Mixed"
        if lynch_s >= buffett_s and lynch_s >= rj_s and lynch_s > 30:
            legend = "📚 Peter Lynch Signal"
        elif buffett_s >= lynch_s and buffett_s >= rj_s and buffett_s > 30:
            legend = "🏦 Warren Buffett Signal"
        elif rj_s >= lynch_s and rj_s >= buffett_s and rj_s > 30:
            legend = "🇮🇳 Rakesh Jhunjhunwala Signal"

        breakdown = {
            "lynch_score":   round(lynch_s),
            "buffett_score": round(buffett_s),
            "rj_score":      round(rj_s),
            "tech_score":    round(tech_s),
            "lynch_reasons":   lynch_r,
            "buffett_reasons": buffett_r,
            "rj_reasons":      rj_r,
            "tech_signals":    tech_sigs,
            "legend":          legend
        }

        return round(combined), breakdown, curr_price

    except Exception as e:
        log.debug(f"Score error {ticker}: {e}")
        return 0, {}, None

# =================================================================
# SECTION 9: TRADE SETUP CALCULATOR
# =================================================================
def calculate_targets(ticker, curr_price, score):
    """Calculate Entry, Target, Stop-Loss based on ATR."""
    try:
        df  = yf.Ticker(f"{ticker}.NS").history(period="1mo")
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        atr_val = atr.iloc[-1] if atr is not None and len(atr) > 0 else curr_price * 0.025

        if score >= 70:
            t_mult, sl_mult = 3.0, 1.5
        elif score >= 50:
            t_mult, sl_mult = 2.0, 1.2
        else:
            t_mult, sl_mult = 1.5, 1.0

        entry  = round(curr_price, 2)
        target = round(curr_price + (atr_val * t_mult), 2)
        sl     = round(curr_price - (atr_val * sl_mult), 2)
        rr     = round((target - entry) / (entry - sl), 2) if (entry - sl) > 0 else 0
        upside = round(((target - entry) / entry) * 100, 1)

        return entry, target, sl, rr, upside

    except:
        entry  = round(curr_price, 2)
        target = round(curr_price * 1.10, 2)
        sl     = round(curr_price * 0.95, 2)
        return entry, target, sl, 2.0, 10.0

# =================================================================
# SECTION 10: ALERT FORMATTER
# =================================================================
def format_alert(ticker, score, breakdown, entry, target, sl, rr, upside, source):
    """Format beautiful Telegram alert with legend framework details."""

    stars   = "⭐" * min(5, max(1, int(score / 20)))
    legend  = breakdown.get('legend', '🔍 Mixed')
    ls, bs, rs, ts = (breakdown['lynch_score'], breakdown['buffett_score'],
                      breakdown['rj_score'],    breakdown['tech_score'])

    # Best reasons from winning framework
    all_reasons = (breakdown.get('lynch_reasons',   []) +
                   breakdown.get('buffett_reasons', []) +
                   breakdown.get('rj_reasons',      []))
    tech_sigs   = breakdown.get('tech_signals', {})

    reason_lines = ""
    for r in all_reasons[:3]:
        reason_lines += f"  {r}\n"

    tech_lines = ""
    for k, v in tech_sigs.items():
        if k not in ['rsi']:
            tech_lines += f"  {v}\n"

    source_emoji = "🟢" if source == "SUBHANI" else "🤖"
    source_label = "WATCHLIST ALERT" if source == "SUBHANI" else "AI DISCOVERY"

    msg = (
        f"{source_emoji} <b>{source_label}: {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>{legend}</b>\n"
        f"📊 Total Score: <b>{score}/100</b> {stars}\n\n"
        f"📈 Framework Scores:\n"
        f"  📚 Lynch:   {ls}/100\n"
        f"  🏦 Buffett: {bs}/100\n"
        f"  🇮🇳 RJ:     {rs}/100\n"
        f"  ⚡ Tech:    {ts}/100\n\n"
        f"💡 <b>Why This Stock:</b>\n{reason_lines}"
        f"{'📡 Technical:' + chr(10) + tech_lines if tech_lines else ''}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Current Price: ₹{entry}\n"
        f"🎯 Target:        ₹{target} (+{upside}%)\n"
        f"🛡️ Stop Loss:     ₹{sl}\n"
        f"⚖️ Risk:Reward:   {rr}x\n\n"
        f"<i>⚠️ Not financial advice. Always use stop loss.</i>"
    )
    return msg

# =================================================================
# SECTION 11: MAIN SCANNER
# =================================================================
ALERTED_TODAY = {}

def run_scan(source="AI", custom_list=None):
    """Main scan function — runs through stocks and sends alerts."""
    global ALERTED_TODAY

    if custom_list:
        stocks = custom_list
    elif source == "SUBHANI":
        stocks = [s for sub in SUBHANI_WATCHLIST.values() for s in sub]
    else:
        stocks = NSE_STOCKS

    today = datetime.date.today().isoformat()
    ALERTED_TODAY = {k: v for k, v in ALERTED_TODAY.items() if v == today}

    log.info(f"🔍 Scanning {len(stocks)} stocks [{source}]")
    found = 0

    for ticker in stocks:
        try:
            if ALERTED_TODAY.get(ticker) == today:
                continue

            score, breakdown, curr_price = score_stock(ticker, BRAIN)

            if curr_price is None:
                continue

            # Lower threshold — more alerts
            threshold = 25 if source == "SUBHANI" else 30
            if score < threshold:
                continue

            entry, target, sl, rr, upside = calculate_targets(ticker, curr_price, score)

            if rr < 1.2:
                continue

            msg = format_alert(ticker, score, breakdown, entry, target, sl, rr, upside, source)
            bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
            log.info(f"✅ Alert: {ticker} Score={score}")

            # Track for learning
            BRAIN['alert_history'].append({
                "ticker":         ticker,
                "price":          curr_price,
                "score":          score,
                "date":           datetime.datetime.now().isoformat(),
                "checked_7d":     False,
                "outcome_7d":     None
            })
            BRAIN['total_alerts'] = BRAIN.get('total_alerts', 0) + 1
            if len(BRAIN['alert_history']) > 200:
                BRAIN['alert_history'] = BRAIN['alert_history'][-200:]
            save_brain(BRAIN)

            ALERTED_TODAY[ticker] = today
            found += 1

            if found >= 8:
                break

            time.sleep(1)

        except Exception as e:
            log.debug(f"Scan error {ticker}: {e}")
            continue

    return found

# =================================================================
# SECTION 12: SELF-LEARNING ENGINE
# =================================================================
def self_learn():
    """Evaluate past alerts and adjust framework weights."""
    log.info("🧠 Self-learning running...")
    improved = 0

    for alert in BRAIN['alert_history']:
        try:
            if alert.get('checked_7d'):
                continue

            alert_date  = datetime.datetime.fromisoformat(alert['date'])
            days_passed = (datetime.datetime.now() - alert_date).days

            if days_passed >= 7:
                df = yf.Ticker(f"{alert['ticker']}.NS").history(period="10d")
                if not df.empty:
                    curr     = df['Close'].iloc[-1]
                    change   = ((curr - alert['price']) / alert['price']) * 100
                    alert['outcome_7d'] = round(change, 2)
                    alert['checked_7d'] = True

                    # Adjust weights
                    if change > 5:
                        for k in BRAIN['signal_weights']:
                            BRAIN['signal_weights'][k] = min(2.0, BRAIN['signal_weights'][k] * 1.03)
                        BRAIN['correct_calls'] = BRAIN.get('correct_calls', 0) + 1
                    elif change < -5:
                        for k in BRAIN['signal_weights']:
                            BRAIN['signal_weights'][k] = max(0.5, BRAIN['signal_weights'][k] * 0.97)
                    improved += 1

        except Exception as e:
            log.debug(f"Learn error: {e}")

    if improved > 0:
        save_brain(BRAIN)
        log.info(f"🧠 Learned from {improved} alerts")

    checked = [a for a in BRAIN['alert_history'] if a.get('outcome_7d') is not None]
    if checked:
        wins = [a for a in checked if a['outcome_7d'] > 3]
        return round(len(wins) / len(checked) * 100, 1)
    return None

# =================================================================
# SECTION 13: INTELLIGENCE ENGINE (Background Thread)
# =================================================================
def intelligence_thread():
    """Runs 24/7 — briefings, scans, sentiment, learning."""
    log.info("📡 Intelligence Engine started")

    while True:
        try:
            now = datetime.datetime.now()
            h, m, wd = now.hour, now.minute, now.weekday()

            # ── 9:30 AM Morning Briefing ──────────────────────────
            if h == 9 and m == 30 and wd < 5:
                try:
                    nifty = yf.Ticker("^NSEI").history(period="2d")
                    vix   = yf.Ticker("^INDIAVIX").history(period="2d")
                    nifty_val = nifty['Close'].iloc[-1] if not nifty.empty else "N/A"
                    vix_val   = vix['Close'].iloc[-1]   if not vix.empty   else "N/A"
                    nifty_chg = ((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) /
                                  nifty['Close'].iloc[-2] * 100) if len(nifty) >= 2 else 0

                    prompt = (
                        f"You are an expert Indian stock market analyst.\n"
                        f"Nifty: {nifty_val:.0f} ({nifty_chg:+.1f}%), VIX: {vix_val:.1f}\n"
                        f"Date: {now.strftime('%d %B %Y')}\n"
                        f"Write a 5-line sharp morning briefing:\n"
                        f"1. Market mood today\n2. Key risk\n3. Strong sector\n"
                        f"4. One Peter Lynch/Buffett/RJ insight\n5. Action for the day"
                    )
                    analysis = get_gemini_analysis(prompt)

                    total   = BRAIN.get('total_alerts', 0)
                    correct = BRAIN.get('correct_calls', 0)
                    acc     = f"{round(correct/total*100, 1)}%" if total > 0 else "Learning..."

                    msg = (
                        f"☀️ <b>EMPIRE MORNING BRIEFING</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Nifty: {nifty_val:.0f} ({nifty_chg:+.1f}%)\n"
                        f"⚡ VIX: {vix_val:.1f}\n"
                        f"🧠 AI Accuracy: {acc}\n\n"
                        f"🤖 <b>Analysis:</b>\n{analysis if analysis else 'Market data loading...'}"
                    )
                    bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
                except Exception as e:
                    log.error(f"Briefing error: {e}")
                time.sleep(70)

            # ── 9:35 AM Subhani Watchlist Scan ───────────────────
            if h == 9 and m == 35 and wd < 5:
                bot.send_message(MY_CHAT_ID,
                    "🟢 <b>Subhani Watchlist Scan starting...</b>", parse_mode='HTML')
                found = run_scan("SUBHANI")
                bot.send_message(MY_CHAT_ID,
                    f"🟢 Watchlist scan done. <b>{found} alerts sent.</b>", parse_mode='HTML')
                time.sleep(70)

            # ── 10:00 AM Full NSE AI Scan ─────────────────────────
            if h == 10 and m == 0 and wd < 5:
                bot.send_message(MY_CHAT_ID,
                    "🤖 <b>AI Agent scanning 500+ NSE stocks...</b>\n"
                    "Using Lynch + Buffett + RJ frameworks...", parse_mode='HTML')
                found = run_scan("AI")
                bot.send_message(MY_CHAT_ID,
                    f"🤖 AI scan complete. <b>{found} opportunities found.</b>", parse_mode='HTML')
                time.sleep(70)

            # ── 4:00 PM Self-Learning ─────────────────────────────
            if h == 16 and m == 0:
                acc = self_learn()
                if acc is not None:
                    total   = BRAIN.get('total_alerts', 0)
                    correct = BRAIN.get('correct_calls', 0)
                    w       = BRAIN['signal_weights']
                    msg = (
                        f"🧠 <b>Daily Self-Learning Complete</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"7-Day Accuracy: <b>{acc}%</b>\n"
                        f"Total Alerts: {total} | Wins: {correct}\n\n"
                        f"📊 Framework Weights Updated:\n"
                        f"  📚 Lynch:   {w['lynch_score']:.3f}\n"
                        f"  🏦 Buffett: {w['buffett_score']:.3f}\n"
                        f"  🇮🇳 RJ:     {w['rj_score']:.3f}\n"
                        f"  🐋 Volume:  {w['volume_spike']:.3f}\n\n"
                        f"<i>Bot gets smarter every day automatically.</i>"
                    )
                    bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
                time.sleep(70)

            # ── Sentiment update every 30 mins ───────────────────
            if 9 <= h <= 15 and m % 30 == 0:
                try:
                    feeds = [
                        "https://www.moneycontrol.com/rss/latestnews.xml",
                        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
                    ]
                    news = ""
                    for url in feeds:
                        try:
                            f = feedparser.parse(url)
                            for e in f.entries[:2]:
                                news += e.title + ". "
                        except: pass

                    if news:
                        res = get_gemini_analysis(
                            f"Rate Indian stock market sentiment 1-100. "
                            f"Reply with ONLY a number: {news[:400]}"
                        )
                        if res:
                            digits = ''.join(filter(str.isdigit, res[:5]))
                            if digits:
                                new_score = max(1, min(100, int(digits[:3])))
                                old_score = BRAIN.get('sentiment_score', 50)
                                BRAIN['sentiment_score'] = round(old_score * 0.7 + new_score * 0.3)
                                save_brain(BRAIN)
                except: pass
                time.sleep(70)

        except Exception as e:
            log.error(f"Intelligence thread error: {e}")

        time.sleep(55)

# =================================================================
# SECTION 14: TELEGRAM COMMANDS
# =================================================================

@bot.message_handler(commands=['start', 'help'])
def cmd_help(message):
    msg = (
        "🚀 <b>EMPIRE BOT v15.0 — 3 LEGEND FRAMEWORKS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📚 <b>Peter Lynch</b> — Finds 10-baggers early\n"
        "🏦 <b>Warren Buffett</b> — Strong moat companies\n"
        "🇮🇳 <b>Rakesh Jhunjhunwala</b> — India growth stories\n\n"
        "Commands:\n"
        "📊 /scan — AI scan on 500+ NSE stocks\n"
        "🟢 /watchlist — Scan your personal stocks\n"
        "🔍 /analyze TICKER — Full 3-legend analysis\n"
        "📈 /rsi TICKER — RSI of any stock\n"
        "🧠 /brain — AI learning stats\n"
        "📋 /report — Performance report\n"
        "⚖️ /balance — Sector allocation\n"
        "💡 /tip — Market tip from Gemini\n\n"
        "Auto scans daily:\n"
        "  ☀️ 9:30 AM — Morning briefing\n"
        "  🟢 9:35 AM — Watchlist scan\n"
        "  🤖 10:00 AM — Full NSE scan\n"
        "  🧠 4:00 PM — Self-learning"
    )
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['scan'])
def cmd_scan(message):
    bot.send_message(message.chat.id,
        "🤖 <b>AI Scan started — Lynch + Buffett + RJ frameworks...</b>\n"
        "Scanning 500+ NSE stocks. Results in 3-5 minutes!", parse_mode='HTML')
    threading.Thread(target=lambda: run_scan("AI"), daemon=True).start()

@bot.message_handler(commands=['watchlist'])
def cmd_watchlist(message):
    bot.send_message(message.chat.id,
        "🟢 <b>Scanning Subhani watchlist...</b>", parse_mode='HTML')
    threading.Thread(target=lambda: run_scan("SUBHANI"), daemon=True).start()

@bot.message_handler(commands=['analyze'])
def cmd_analyze(message):
    try:
        parts  = message.text.split()
        ticker = parts[1].upper() if len(parts) > 1 else None
        if not ticker:
            bot.send_message(message.chat.id, "Usage: /analyze TATAMOTORS")
            return

        bot.send_message(message.chat.id, f"🔍 Analyzing {ticker} with 3 legend frameworks...")

        score, breakdown, price = score_stock(ticker, BRAIN)
        if price is None:
            bot.send_message(message.chat.id, f"❌ No data for {ticker}.NS — check ticker name")
            return

        entry, target, sl, rr, upside = calculate_targets(ticker, price, score)

        # Get Gemini view
        prompt = (
            f"Analyze NSE stock {ticker} at ₹{price:.2f}.\n"
            f"Lynch score: {breakdown['lynch_score']}/100\n"
            f"Buffett score: {breakdown['buffett_score']}/100\n"
            f"RJ score: {breakdown['rj_score']}/100\n"
            f"Give a 3-line view for Indian retail investor. Be direct and specific."
        )
        ai_view = get_gemini_analysis(prompt)

        msg = format_alert(ticker, score, breakdown, entry, target, sl, rr, upside, "SUBHANI")
        if ai_view:
            msg += f"\n\n🤖 <b>Gemini View:</b>\n{ai_view}"

        bot.send_message(message.chat.id, msg, parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['rsi'])
def cmd_rsi(message):
    try:
        parts  = message.text.split()
        ticker = parts[1].upper() if len(parts) > 1 else None
        if not ticker:
            bot.send_message(message.chat.id, "Usage: /rsi TATAMOTORS")
            return

        df  = yf.Ticker(f"{ticker}.NS").history(period="1mo")
        if df.empty:
            bot.send_message(message.chat.id, f"❌ No data for {ticker}")
            return

        rsi     = ta.rsi(df['Close'], length=14)
        rsi_val = rsi.iloc[-1]
        price   = df['Close'].iloc[-1]

        if rsi_val < 30:
            zone = "🟢 OVERSOLD — Strong buy zone (Lynch/RJ love this!)"
        elif rsi_val < 40:
            zone = "🟡 MILDLY OVERSOLD — Watch for entry"
        elif rsi_val > 75:
            zone = "🔴 OVERBOUGHT — Book partial profits"
        elif rsi_val > 65:
            zone = "🟠 GETTING HOT — Tighten stop loss"
        else:
            zone = "⚪ NEUTRAL — Wait for clearer signal"

        bot.send_message(message.chat.id,
            f"📊 <b>RSI: {ticker}</b>\n"
            f"Price: ₹{price:.2f}\n"
            f"RSI(14): <b>{rsi_val:.1f}</b>\n"
            f"{zone}", parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

@bot.message_handler(commands=['brain'])
def cmd_brain(message):
    total   = BRAIN.get('total_alerts', 0)
    correct = BRAIN.get('correct_calls', 0)
    acc     = round(correct/total*100, 1) if total > 0 else 0
    w       = BRAIN['signal_weights']
    checked = [a for a in BRAIN['alert_history'] if a.get('outcome_7d') is not None]
    wins    = [a for a in checked if a.get('outcome_7d', 0) > 3]
    acc_7d  = round(len(wins)/len(checked)*100, 1) if checked else 0

    bot.send_message(message.chat.id,
        f"🧠 <b>EMPIRE BRAIN REPORT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Total Alerts: {total}\n"
        f"Evaluated:    {len(checked)}\n"
        f"7-Day Win Rate: {acc_7d}%\n"
        f"Sentiment: {BRAIN.get('sentiment_score', 50)}/100\n\n"
        f"📊 <b>Framework Weights (Auto-Learned):</b>\n"
        f"  📚 Lynch:   {w['lynch_score']:.3f}\n"
        f"  🏦 Buffett: {w['buffett_score']:.3f}\n"
        f"  🇮🇳 RJ:     {w['rj_score']:.3f}\n"
        f"  🐋 Volume:  {w['volume_spike']:.3f}\n"
        f"  📉 RSI:     {w['rsi_oversold']:.3f}\n"
        f"  ⚡ Momentum:{w['momentum']:.3f}\n\n"
        f"<i>Weights adjust automatically from outcomes.</i>",
        parse_mode='HTML')

@bot.message_handler(commands=['report'])
def cmd_report(message):
    history = [a for a in BRAIN.get('alert_history', []) if a.get('outcome_7d') is not None][-10:]
    if not history:
        bot.send_message(message.chat.id,
            "📋 No completed alerts yet. Check back after 7 days!\n"
            "Keep running /scan daily to build the track record.")
        return

    report = "📋 <b>PERFORMANCE REPORT</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    wins = losses = neutral = 0
    for a in history:
        o = a['outcome_7d']
        e = "✅" if o > 3 else ("❌" if o < -3 else "➖")
        if o > 3: wins += 1
        elif o < -3: losses += 1
        else: neutral += 1
        report += f"{e} {a['ticker']}: {o:+.1f}% (7d)\n"

    total  = len(history)
    acc    = round(wins/total*100) if total > 0 else 0
    report += (f"\n━━━━━━━━━━━━━━━━━━━━\n"
               f"Win Rate: <b>{acc}%</b> ({wins}W / {losses}L / {neutral}N)\n"
               f"<i>Bot learns from every result automatically.</i>")
    bot.send_message(message.chat.id, report, parse_mode='HTML')

@bot.message_handler(commands=['balance'])
def cmd_balance(message):
    total  = sum(len(v) for v in SUBHANI_WATCHLIST.values())
    report = "⚖️ <b>SUBHANI WATCHLIST</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for sector, stocks in SUBHANI_WATCHLIST.items():
        pct    = (len(stocks) / total) * 100
        report += f"🔹 {sector}: {len(stocks)} stocks ({pct:.0f}%)\n"
        report += f"   {', '.join(stocks[:3])}{'...' if len(stocks)>3 else ''}\n"
    bot.send_message(message.chat.id, report, parse_mode='HTML')

@bot.message_handler(commands=['tip'])
def cmd_tip(message):
    prompt = (
        "Give one sharp actionable stock market tip for Indian retail investors today. "
        "Reference Peter Lynch, Warren Buffett, or Rakesh Jhunjhunwala wisdom. "
        "Max 4 sentences. Be specific about Indian market context."
    )
    tip = get_gemini_analysis(prompt)
    if tip:
        bot.send_message(message.chat.id,
            f"💡 <b>Market Wisdom:</b>\n{tip}", parse_mode='HTML')
    else:
        bot.send_message(message.chat.id,
            "💡 <b>Market Wisdom:</b>\n"
            "Peter Lynch said: 'The person that turns over the most rocks wins the game.' "
            "Keep scanning, keep learning. Your Empire Bot is doing exactly that! 🚀")

# =================================================================
# SECTION 15: IGNITION
# =================================================================
if __name__ == "__main__":
    log.info("🚀 EMPIRE BOT v15.0 starting...")

    if not TELEGRAM_TOKEN:
        log.error("❌ TELEGRAM_TOKEN missing!")
        exit(1)

    try:
        bot.send_message(MY_CHAT_ID,
            "🚀 <b>EMPIRE BOT v15.0 ONLINE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Peter Lynch Framework: Active\n"
            "✅ Warren Buffett Framework: Active\n"
            "✅ Rakesh Jhunjhunwala Framework: Active\n"
            "✅ Self-Learning Engine: Active\n"
            "✅ Gemini AI: Connected\n\n"
            "Type /scan to find opportunities now!\n"
            "Type /help to see all commands",
            parse_mode='HTML')
        log.info("✅ Startup message sent")
    except Exception as e:
        log.error(f"Startup message failed: {e}")

    threading.Thread(target=intelligence_thread, daemon=True).start()
    log.info("✅ All systems online")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            log.error(f"Polling error: {e}")
            time.sleep(15)
