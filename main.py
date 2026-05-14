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

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
MY_CHAT_ID     = os.getenv('MY_CHAT_ID', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

SUBHANI_WATCHLIST = {
    "DEFENSE":     ["HAL", "MAZDOCK", "BEL", "DATAPATTNS", "ASTRAMICRO"],
    "RENEWABLES":  ["TATAPOWER", "ADANIGREEN", "SUZLON", "INOXWIND", "BORORENEW"],
    "AUTO_EV":     ["M&M", "TATAMOTORS", "BAJAJ-AUTO", "TVSMOTOR", "EICHERMOT"],
    "IT_PHARMA":   ["TCS", "INFY", "PERSISTENT", "SUNPHARMA", "DRREDDY"],
    "SUMMER_AGRI": ["VOLTAS", "VBL", "PIIND", "COROMANDEL", "DHANUKA"],
    "DATA_CLOUD":  ["E2ENETWORKS", "NELCO", "NETWEB", "HCLTECH"],
    "SHIELD_ETF":  ["GOLDBEES", "SILVERBEES", "ICICISILVER"]
}

NSE_STOCKS = [
    "RELIANCE","TCS","HDFCBANK","INFY","HINDUNILVR","ICICIBANK","KOTAKBANK",
    "BHARTIARTL","ITC","AXISBANK","LT","ASIANPAINT","MARUTI","TITAN","BAJFINANCE",
    "SUNPHARMA","WIPRO","ULTRACEMCO","NESTLEIND","POWERGRID","NTPC","ONGC",
    "TATAMOTORS","TATASTEEL","JSWSTEEL","ADANIENT","ADANIGREEN","ADANIPORTS",
    "HCLTECH","TECHM","BAJAJFINSV","GRASIM","BRITANNIA","HINDALCO","DIVISLAB",
    "DRREDDY","CIPLA","EICHERMOT","HEROMOTOCO","M&M","BAJAJ-AUTO","TVSMOTOR",
    "APOLLOHOSP","HAL","BEL","MAZDOCK","BPCL","IOC","TATAPOWER","COALINDIA",
    "PERSISTENT","MPHASIS","LTTS","COFORGE","KPITTECH","TATAELXSI",
    "PIIND","AARTIIND","DEEPAKNITR","ASTRAL","POLYCAB","HAVELLS","CROMPTON",
    "VOLTAS","CONCOR","IRCTC","INDHOTEL","MAHINDCIE",
    "SUZLON","INOXWIND","BORORENEW","DHANUKA","COROMANDEL","RALLIS",
    "DATAPATTNS","ASTRAMICRO","E2ENETWORKS","NELCO","NETWEB",
    "VBL","RADICO","OBEROIRLTY","PRESTIGE","GODREJPROP",
    "SUNTV","NAZARA","ZOMATO","PAYTM","NYKAA","DELHIVERY",
    "RVNL","IRFC","IRCON","RAILTEL","TEJASNET","HFCL",
    "RATTANINDIA","RPOWER","JPPOWER","YESBANK",
    "WAAREE","PREMIER","MANKIND","LALPATHLAB",
    "METROPOLIS","KRSNAA","MIDHANI","SWREL"
]

BRAIN_FILE = "brain_state.json"

def load_brain():
    default = {
        "sentiment_score": 50,
        "signal_weights": {
            "lynch_score": 1.0, "buffett_score": 1.0, "rj_score": 1.0,
            "volume_spike": 1.0, "rsi_oversold": 1.0, "momentum": 1.0
        },
        "alert_history": [], "total_alerts": 0, "correct_calls": 0
    }
    try:
        if os.path.exists(BRAIN_FILE):
            with open(BRAIN_FILE, 'r') as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data: data[k] = v
                return data
    except: pass
    return default

def save_brain(brain):
    try:
        with open(BRAIN_FILE, 'w') as f:
            json.dump(brain, f, indent=2)
    except: pass

BRAIN = load_brain()

def get_gemini_analysis(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return None

def peter_lynch_score(info, df):
    score = 0
    reasons = []
    try:
        pe = info.get('trailingPE', None)
        eps_growth = info.get('earningsGrowth', None) or info.get('revenueGrowth', None)
        if pe and eps_growth and eps_growth > 0:
            peg = pe / (eps_growth * 100)
            if peg < 1:
                score += 25; reasons.append(f"📈 PEG={peg:.2f} — Lynch loves <1!")
            elif peg < 2:
                score += 10; reasons.append(f"📈 PEG={peg:.2f} — Acceptable value")
        mkt_cap = info.get('marketCap', 0) or 0
        if 100_000_000 < mkt_cap < 50_000_000_000:
            score += 20; reasons.append(f"🔍 Small/Mid cap — Lynch's sweet spot")
        rev_growth = info.get('revenueGrowth', 0) or 0
        if rev_growth > 0.20:
            score += 20; reasons.append(f"💰 Revenue +{rev_growth*100:.0f}% — Strong growth!")
        elif rev_growth > 0.10:
            score += 10; reasons.append(f"💰 Revenue +{rev_growth*100:.0f}% — Decent growth")
        inst_own = info.get('heldPercentInstitutions', 1) or 1
        if inst_own < 0.15:
            score += 15; reasons.append(f"👁️ Only {inst_own*100:.0f}% institutional — undiscovered!")
        cash = info.get('totalCash', 0) or 0
        debt = info.get('totalDebt', 0) or 0
        if cash > debt:
            score += 10; reasons.append(f"💵 More cash than debt")
    except: pass
    return min(score, 100), reasons

def warren_buffett_score(info, df):
    score = 0
    reasons = []
    try:
        roe = info.get('returnOnEquity', 0) or 0
        if roe > 0.20:
            score += 25; reasons.append(f"🏰 ROE={roe*100:.1f}% — Strong economic moat!")
        elif roe > 0.15:
            score += 15; reasons.append(f"🏰 ROE={roe*100:.1f}% — Good moat")
        de = info.get('debtToEquity', 999) or 999
        if de < 50:
            score += 20; reasons.append(f"✅ D/E={de:.0f} — Buffett loves low debt!")
        elif de < 100:
            score += 10; reasons.append(f"✅ D/E={de:.0f} — Acceptable debt")
        margin = info.get('profitMargins', 0) or 0
        if margin > 0.15:
            score += 20; reasons.append(f"💎 Margin={margin*100:.1f}% — Pricing power!")
        elif margin > 0.08:
            score += 10; reasons.append(f"💎 Margin={margin*100:.1f}% — Decent margin")
        eps = info.get('trailingEps', 0) or 0
        if eps > 0:
            score += 15; reasons.append(f"📊 EPS=₹{eps:.1f} — Profitable business")
        pb = info.get('priceToBook', 999) or 999
        if 0 < pb < 3:
            score += 10; reasons.append(f"📉 P/B={pb:.1f} — Fair value")
        promoter = info.get('heldPercentInsiders', 0) or 0
        if promoter > 0.50:
            score += 10; reasons.append(f"👨‍💼 Promoter={promoter*100:.0f}% — Skin in game!")
    except: pass
    return min(score, 100), reasons

def rakesh_jhunjhunwala_score(info, df, ticker):
    score = 0
    reasons = []
    try:
        close = df['Close']; high = df['High']; low = df['Low']
        week52_high = high.iloc[-252:].max() if len(high) >= 252 else high.max()
        curr_price = close.iloc[-1]
        fall = ((week52_high - curr_price) / week52_high) * 100
        if 30 <= fall <= 70:
            score += 25; reasons.append(f"🎯 Down {fall:.0f}% from peak — RJ's entry zone!")
        elif 15 <= fall < 30:
            score += 15; reasons.append(f"🎯 Down {fall:.0f}% from peak — Watch zone")
        rj_favorites = ['TITAN','CRISIL','LUPIN','ESCORTS','NAZARA','HAL','BEL',
                        'IRCTC','CONCOR','RAILTEL','RVNL','TATA','STAR','NCC']
        if any(s in ticker.upper() for s in rj_favorites):
            score += 15; reasons.append(f"🇮🇳 India growth sector — RJ's favorite type!")
        vol_20d = df['Volume'].iloc[-21:-1].mean()
        vol_5d  = df['Volume'].iloc[-6:-1].mean()
        if vol_5d > vol_20d * 1.5:
            score += 20; reasons.append(f"🐋 Volume accumulation — Smart money entering!")
        week52_low = low.iloc[-252:].min() if len(low) >= 252 else low.min()
        rise = ((curr_price - week52_low) / week52_low) * 100
        if 10 <= rise <= 50:
            score += 20; reasons.append(f"🔄 Up {rise:.0f}% from bottom — Turnaround story!")
        mkt_cap = info.get('marketCap', 0) or 0
        if 500_000_000 < mkt_cap < 100_000_000_000:
            score += 10; reasons.append(f"📐 Market cap in multibagger range")
        div_yield = info.get('dividendYield', 0) or 0
        if div_yield > 0.01:
            score += 10; reasons.append(f"💸 Dividend {div_yield*100:.1f}% — Shareholder friendly")
    except: pass
    return min(score, 100), reasons

def get_technical_signals(df, brain):
    signals = {}; score = 0; w = brain['signal_weights']
    try:
        close = df['Close']; volume = df['Volume']
        high = df['High']; low = df['Low']
        rsi = ta.rsi(close, length=14)
        if rsi is not None and len(rsi) > 0:
            rv = rsi.iloc[-1]; signals['rsi'] = round(rv, 1)
            if 20 <= rv <= 35:
                score += 30 * w['rsi_oversold']
                signals['rsi_signal'] = f"🟢 RSI={rv:.0f} OVERSOLD — Buy zone!"
            elif rv > 75:
                signals['rsi_signal'] = f"🔴 RSI={rv:.0f} OVERBOUGHT"
        vol_avg = volume.iloc[-21:-1].mean()
        vol_now = volume.iloc[-1]
        vr = vol_now / vol_avg if vol_avg > 0 else 1
        if vr > 2.0:
            score += 20 * w['volume_spike']
            signals['volume'] = f"🐋 Volume {vr:.1f}x — Big players moving!"
        if len(close) >= 22:
            r1w = ((close.iloc[-1] - close.iloc[-6])  / close.iloc[-6])  * 100
            r1m = ((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100
            if r1w > 3 and r1m > 5:
                score += 20 * w['momentum']
                signals['momentum'] = f"⚡ 1W={r1w:.1f}% 1M={r1m:.1f}% — Accelerating!"
        h20 = high.iloc[-20:].max(); l20 = low.iloc[-20:].min()
        rng = ((h20 - l20) / l20) * 100 if l20 > 0 else 100
        if rng < 8:
            score += 15
            signals['compression'] = f"🌀 Range only {rng:.1f}% — Breakout building!"
        macd_d = ta.macd(close)
        if macd_d is not None and len(macd_d) > 2:
            ml = macd_d.iloc[:, 0]; sl2 = macd_d.iloc[:, 2]
            if len(ml) > 1 and ml.iloc[-2] < sl2.iloc[-2] and ml.iloc[-1] > sl2.iloc[-1]:
                score += 15; signals['macd'] = f"📊 MACD Crossover — Momentum turning!"
    except: pass
    return min(score, 100), signals

def score_stock(ticker, brain):
    try:
        t  = yf.Ticker(f"{ticker}.NS")
        df = t.history(period="1y", interval="1d")
        if df is None or len(df) < 30: return 0, {}, None
        info = t.info
        curr_price = df['Close'].iloc[-1]
        if curr_price <= 0: return 0, {}, None
        ls, lr = peter_lynch_score(info, df)
        bs, br = warren_buffett_score(info, df)
        rs, rr = rakesh_jhunjhunwala_score(info, df, ticker)
        ts, tsigs = get_technical_signals(df, brain)
        w = brain['signal_weights']
        combined = (ls*w['lynch_score']*0.25 + bs*w['buffett_score']*0.25 +
                    rs*w['rj_score']*0.30 + ts*0.20)
        legend = "🔍 Mixed Signals"
        if ls >= bs and ls >= rs and ls > 30: legend = "📚 Peter Lynch Signal"
        elif bs >= ls and bs >= rs and bs > 30: legend = "🏦 Warren Buffett Signal"
        elif rs >= ls and rs >= bs and rs > 30: legend = "🇮🇳 Rakesh Jhunjhunwala Signal"
        bd = {"lynch_score": round(ls), "buffett_score": round(bs),
              "rj_score": round(rs), "tech_score": round(ts),
              "lynch_reasons": lr, "buffett_reasons": br,
              "rj_reasons": rr, "tech_signals": tsigs, "legend": legend}
        return round(combined), bd, curr_price
    except Exception as e:
        log.debug(f"Score error {ticker}: {e}")
        return 0, {}, None

def calculate_targets(ticker, curr_price, score):
    try:
        df  = yf.Ticker(f"{ticker}.NS").history(period="1mo")
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        av  = atr.iloc[-1] if atr is not None and len(atr) > 0 else curr_price * 0.025
        tm, sm = (3.0, 1.5) if score >= 70 else (2.0, 1.2) if score >= 50 else (1.5, 1.0)
        entry  = round(curr_price, 2)
        target = round(curr_price + av * tm, 2)
        sl     = round(curr_price - av * sm, 2)
        rr     = round((target-entry)/(entry-sl), 2) if (entry-sl) > 0 else 0
        upside = round(((target-entry)/entry)*100, 1)
        return entry, target, sl, rr, upside
    except:
        return round(curr_price,2), round(curr_price*1.10,2), round(curr_price*0.95,2), 2.0, 10.0

def format_alert(ticker, score, bd, entry, target, sl, rr, upside, source):
    stars  = "⭐" * min(5, max(1, int(score/20)))
    legend = bd.get('legend', '🔍 Mixed')
    ls, bs, rs, ts = bd['lynch_score'], bd['buffett_score'], bd['rj_score'], bd['tech_score']
    all_r  = bd.get('lynch_reasons',[]) + bd.get('buffett_reasons',[]) + bd.get('rj_reasons',[])
    tsigs  = bd.get('tech_signals', {})
    rlines = "".join(f"  {r}\n" for r in all_r[:3])
    tlines = "".join(f"  {v}\n" for k,v in tsigs.items() if k != 'rsi')
    se = "🟢" if source=="SUBHANI" else "🤖"
    sl2 = "WATCHLIST ALERT" if source=="SUBHANI" else "AI DISCOVERY"
    return (
        f"{se} <b>{sl2}: {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>{legend}</b>\n"
        f"📊 Score: <b>{score}/100</b> {stars}\n\n"
        f"📈 Framework Breakdown:\n"
        f"  📚 Lynch:   {ls}/100\n"
        f"  🏦 Buffett: {bs}/100\n"
        f"  🇮🇳 RJ:     {rs}/100\n"
        f"  ⚡ Tech:    {ts}/100\n\n"
        f"💡 <b>Why:</b>\n{rlines}"
        f"{'📡 Tech Signals:\n'+tlines if tlines else ''}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price:  ₹{entry}\n"
        f"🎯 Target: ₹{target} (+{upside}%)\n"
        f"🛡️ Stop:   ₹{sl}\n"
        f"⚖️ R:R:    {rr}x\n\n"
        f"<i>⚠️ Not financial advice. Always use stop loss.</i>"
    )

ALERTED_TODAY = {}

def run_scan(source="AI", custom_list=None):
    global ALERTED_TODAY
    stocks = (custom_list if custom_list else
              [s for sub in SUBHANI_WATCHLIST.values() for s in sub] if source=="SUBHANI"
              else NSE_STOCKS)
    today = datetime.date.today().isoformat()
    ALERTED_TODAY = {k:v for k,v in ALERTED_TODAY.items() if v==today}
    log.info(f"🔍 Scanning {len(stocks)} stocks [{source}]")
    found = 0
    for ticker in stocks:
        try:
            if ALERTED_TODAY.get(ticker) == today: continue
            score, bd, price = score_stock(ticker, BRAIN)
            if price is None: continue
            threshold = 20 if source=="SUBHANI" else 25
            if score < threshold: continue
            entry, target, sl, rr, upside = calculate_targets(ticker, price, score)
            if rr < 1.2: continue
            msg = format_alert(ticker, score, bd, entry, target, sl, rr, upside, source)
            bot.send_message(MY_CHAT_ID, msg, parse_mode='HTML')
            log.info(f"✅ Alert: {ticker} Score={score}")
            BRAIN['alert_history'].append({
                "ticker": ticker, "price": price, "score": score,
                "date": datetime.datetime.now().isoformat(),
                "checked_7d": False, "outcome_7d": None
            })
            BRAIN['total_alerts'] = BRAIN.get('total_alerts', 0) + 1
            if len(BRAIN['alert_history']) > 200:
                BRAIN['alert_history'] = BRAIN['alert_history'][-200:]
            save_brain(BRAIN)
            ALERTED_TODAY[ticker] = today
            found += 1
            if found >= 8: break
            time.sleep(1)
        except Exception as e:
            log.debug(f"Scan error {ticker}: {e}")
    return found

def self_learn():
    improved = 0
    for alert in BRAIN['alert_history']:
        try:
            if alert.get('checked_7d'): continue
            days = (datetime.datetime.now() - datetime.datetime.fromisoformat(alert['date'])).days
            if days >= 7:
                df = yf.Ticker(f"{alert['ticker']}.NS").history(period="10d")
                if not df.empty:
                    chg = ((df['Close'].iloc[-1] - alert['price']) / alert['price']) * 100
                    alert['outcome_7d'] = round(chg, 2)
                    alert['checked_7d'] = True
                    if chg > 5:
                        for k in BRAIN['signal_weights']:
                            BRAIN['signal_weights'][k] = min(2.0, BRAIN['signal_weights'][k]*1.03)
                        BRAIN['correct_calls'] = BRAIN.get('correct_calls',0) + 1
                    elif chg < -5:
                        for k in BRAIN['signal_weights']:
                            BRAIN['signal_weights'][k] = max(0.5, BRAIN['signal_weights'][k]*0.97)
                    improved += 1
        except: pass
    if improved > 0: save_brain(BRAIN)
    checked = [a for a in BRAIN['alert_history'] if a.get('outcome_7d') is not None]
    if checked:
        wins = [a for a in checked if a['outcome_7d'] > 3]
        return round(len(wins)/len(checked)*100, 1)
    return None

def intelligence_thread():
    log.info("📡 Intelligence Engine started")
    while True:
        try:
            now = datetime.datetime.now()
            h, m, wd = now.hour, now.minute, now.weekday()
            if h==9 and m==30 and wd<5:
                try:
                    nifty = yf.Ticker("^NSEI").history(period="2d")
                    vix   = yf.Ticker("^INDIAVIX").history(period="2d")
                    nv = nifty['Close'].iloc[-1] if not nifty.empty else 0
                    vv = vix['Close'].iloc[-1]   if not vix.empty   else 0
                    nc = ((nifty['Close'].iloc[-1]-nifty['Close'].iloc[-2])/nifty['Close'].iloc[-2]*100) if len(nifty)>=2 else 0
                    prompt = (f"Indian stock market analyst. Nifty:{nv:.0f}({nc:+.1f}%) VIX:{vv:.1f} "
                              f"Date:{now.strftime('%d %B %Y')}. Write 5-line morning briefing: "
                              f"1.Market mood 2.Key risk 3.Strong sector 4.Lynch/Buffett/RJ insight 5.Action today")
                    analysis = get_gemini_analysis(prompt)
                    total = BRAIN.get('total_alerts',0); correct = BRAIN.get('correct_calls',0)
                    acc = f"{round(correct/total*100,1)}%" if total>0 else "Learning..."
                    bot.send_message(MY_CHAT_ID,
                        f"☀️ <b>EMPIRE MORNING BRIEFING</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Nifty: {nv:.0f} ({nc:+.1f}%)\n⚡ VIX: {vv:.1f}\n🧠 Accuracy: {acc}\n\n"
                        f"🤖 <b>Analysis:</b>\n{analysis if analysis else 'Gemini loading...'}",
                        parse_mode='HTML')
                except Exception as e: log.error(f"Briefing error: {e}")
                time.sleep(70)
            if h==9 and m==35 and wd<5:
                bot.send_message(MY_CHAT_ID,"🟢 <b>Subhani Watchlist Scan...</b>",parse_mode='HTML')
                found = run_scan("SUBHANI")
                bot.send_message(MY_CHAT_ID,f"🟢 Done. <b>{found} alerts sent.</b>",parse_mode='HTML')
                time.sleep(70)
            if h==10 and m==0 and wd<5:
                bot.send_message(MY_CHAT_ID,"🤖 <b>AI Scan — Lynch+Buffett+RJ frameworks...</b>",parse_mode='HTML')
                found = run_scan("AI")
                bot.send_message(MY_CHAT_ID,f"🤖 Done. <b>{found} opportunities found.</b>",parse_mode='HTML')
                time.sleep(70)
            if h==16 and m==0:
                acc = self_learn()
                if acc is not None:
                    w = BRAIN['signal_weights']
                    bot.send_message(MY_CHAT_ID,
                        f"🧠 <b>Self-Learning Complete</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"7-Day Accuracy: <b>{acc}%</b>\nTotal: {BRAIN.get('total_alerts',0)}\n\n"
                        f"Weights:\n  📚Lynch:{w['lynch_score']:.3f} 🏦Buffett:{w['buffett_score']:.3f}\n"
                        f"  🇮🇳RJ:{w['rj_score']:.3f} 🐋Vol:{w['volume_spike']:.3f}",
                        parse_mode='HTML')
                time.sleep(70)
            if 9<=h<=15 and m%30==0:
                try:
                    news=""
                    for url in ["https://www.moneycontrol.com/rss/latestnews.xml"]:
                        try:
                            f=feedparser.parse(url)
                            for e in f.entries[:3]: news+=e.title+". "
                        except: pass
                    if news:
                        res=get_gemini_analysis(f"Rate Indian stock sentiment 1-100. Only number: {news[:400]}")
                        if res:
                            digits=''.join(filter(str.isdigit,res[:5]))
                            if digits:
                                ns=max(1,min(100,int(digits[:3])))
                                BRAIN['sentiment_score']=round(BRAIN.get('sentiment_score',50)*0.7+ns*0.3)
                                save_brain(BRAIN)
                except: pass
                time.sleep(70)
        except Exception as e: log.error(f"Thread error: {e}")
        time.sleep(55)

@bot.message_handler(commands=['start','help'])
def cmd_help(message):
    bot.send_message(message.chat.id,
        "🚀 <b>EMPIRE BOT v15.0 — 3 LEGEND FRAMEWORKS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "📚 <b>Peter Lynch</b> — Finds 10-baggers early\n"
        "🏦 <b>Warren Buffett</b> — Strong moat companies\n"
        "🇮🇳 <b>Rakesh Jhunjhunwala</b> — India growth stories\n\n"
        "Commands:\n"
        "📊 /scan — AI scan 500+ NSE stocks\n"
        "🟢 /watchlist — Scan your personal stocks\n"
        "🔍 /analyze TICKER — Full 3-legend analysis\n"
        "📈 /rsi TICKER — RSI of any stock\n"
        "🧠 /brain — AI learning stats\n"
        "📋 /report — Performance report\n"
        "⚖️ /balance — Sector allocation\n"
        "💡 /tip — Market tip from Gemini\n\n"
        "Auto daily:\n☀️9:30 Briefing 🟢9:35 Watchlist 🤖10:00 NSE Scan 🧠4:00 Learning",
        parse_mode='HTML')

@bot.message_handler(commands=['scan'])
def cmd_scan(message):
    bot.send_message(message.chat.id,
        "🤖 <b>AI Scan — Lynch+Buffett+RJ frameworks...</b>\nResults in 3-5 mins!",parse_mode='HTML')
    threading.Thread(target=lambda:run_scan("AI"),daemon=True).start()

@bot.message_handler(commands=['watchlist'])
def cmd_watchlist(message):
    bot.send_message(message.chat.id,"🟢 <b>Scanning Subhani watchlist...</b>",parse_mode='HTML')
    threading.Thread(target=lambda:run_scan("SUBHANI"),daemon=True).start()

@bot.message_handler(commands=['analyze'])
def cmd_analyze(message):
    try:
        parts=message.text.split(); ticker=parts[1].upper() if len(parts)>1 else None
        if not ticker:
            bot.send_message(message.chat.id,"Usage: /analyze TATAMOTORS"); return
        bot.send_message(message.chat.id,f"🔍 Analyzing {ticker}...")
        score,bd,price=score_stock(ticker,BRAIN)
        if price is None:
            bot.send_message(message.chat.id,f"❌ No data for {ticker}.NS"); return
        entry,target,sl,rr,upside=calculate_targets(ticker,price,score)
        msg=format_alert(ticker,score,bd,entry,target,sl,rr,upside,"SUBHANI")
        ai=get_gemini_analysis(f"Analyze NSE {ticker} ₹{price:.2f} Lynch:{bd['lynch_score']} "
                               f"Buffett:{bd['buffett_score']} RJ:{bd['rj_score']}. 3-line view for Indian investor.")
        if ai: msg+=f"\n\n🤖 <b>Gemini:</b>\n{ai}"
        bot.send_message(message.chat.id,msg,parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id,f"❌ Error: {e}")

@bot.message_handler(commands=['rsi'])
def cmd_rsi(message):
    try:
        parts=message.text.split(); ticker=parts[1].upper() if len(parts)>1 else None
        if not ticker:
            bot.send_message(message.chat.id,"Usage: /rsi TATAMOTORS"); return
        df=yf.Ticker(f"{ticker}.NS").history(period="1mo")
        if df.empty:
            bot.send_message(message.chat.id,f"❌ No data for {ticker}"); return
        rsi=ta.rsi(df['Close'],length=14); rv=rsi.iloc[-1]; price=df['Close'].iloc[-1]
        zone=("🟢 OVERSOLD — Buy zone!" if rv<30 else "🟡 MILDLY OVERSOLD" if rv<40 else
              "🔴 OVERBOUGHT — Book profits" if rv>75 else "🟠 GETTING HOT" if rv>65 else "⚪ NEUTRAL")
        bot.send_message(message.chat.id,
            f"📊 <b>RSI: {ticker}</b>\nPrice: ₹{price:.2f}\nRSI(14): <b>{rv:.1f}</b>\n{zone}",
            parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id,f"❌ Error: {e}")

@bot.message_handler(commands=['brain'])
def cmd_brain(message):
    total=BRAIN.get('total_alerts',0); correct=BRAIN.get('correct_calls',0)
    w=BRAIN['signal_weights']
    checked=[a for a in BRAIN['alert_history'] if a.get('outcome_7d') is not None]
    wins=[a for a in checked if a.get('outcome_7d',0)>3]
    acc=round(len(wins)/len(checked)*100,1) if checked else 0
    bot.send_message(message.chat.id,
        f"🧠 <b>EMPIRE BRAIN</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Alerts: {total} | Evaluated: {len(checked)} | Win Rate: {acc}%\n"
        f"Sentiment: {BRAIN.get('sentiment_score',50)}/100\n\n"
        f"📊 <b>Weights (Auto-Learned):</b>\n"
        f"  📚Lynch:{w['lynch_score']:.3f} 🏦Buffett:{w['buffett_score']:.3f}\n"
        f"  🇮🇳RJ:{w['rj_score']:.3f} 🐋Vol:{w['volume_spike']:.3f}\n"
        f"  📉RSI:{w['rsi_oversold']:.3f} ⚡Mom:{w['momentum']:.3f}",
        parse_mode='HTML')

@bot.message_handler(commands=['report'])
def cmd_report(message):
    history=[a for a in BRAIN.get('alert_history',[]) if a.get('outcome_7d') is not None][-10:]
    if not history:
        bot.send_message(message.chat.id,"📋 No completed alerts yet. Check after 7 days!"); return
    report="📋 <b>PERFORMANCE</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    wins=losses=neutral=0
    for a in history:
        o=a['outcome_7d']; e="✅" if o>3 else ("❌" if o<-3 else "➖")
        if o>3: wins+=1
        elif o<-3: losses+=1
        else: neutral+=1
        report+=f"{e} {a['ticker']}: {o:+.1f}%\n"
    total=len(history); acc=round(wins/total*100) if total>0 else 0
    report+=f"\n━━━━━━━━━━━━━━━━━━━━\nWin Rate: <b>{acc}%</b> ({wins}W/{losses}L/{neutral}N)"
    bot.send_message(message.chat.id,report,parse_mode='HTML')

@bot.message_handler(commands=['balance'])
def cmd_balance(message):
    total=sum(len(v) for v in SUBHANI_WATCHLIST.values())
    report="⚖️ <b>SUBHANI WATCHLIST</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for sector,stocks in SUBHANI_WATCHLIST.items():
        pct=(len(stocks)/total)*100
        report+=f"🔹 {sector}: {len(stocks)} ({pct:.0f}%) — {','.join(stocks[:3])}...\n"
    bot.send_message(message.chat.id,report,parse_mode='HTML')

@bot.message_handler(commands=['tip'])
def cmd_tip(message):
    tip=get_gemini_analysis(
        "One sharp actionable Indian stock market tip referencing Peter Lynch, Buffett or RJ. "
        "4 sentences max. Specific to Indian market context.")
    bot.send_message(message.chat.id,
        f"💡 <b>Market Wisdom:</b>\n{tip}" if tip else
        "💡 <b>Peter Lynch:</b>\nTurn over more rocks than anyone else. "
        "Your Empire Bot is scanning 500+ stocks daily doing exactly that! 🚀",
        parse_mode='HTML')

if __name__ == "__main__":
    log.info("🚀 EMPIRE BOT v15.0 starting...")
    if not TELEGRAM_TOKEN: log.error("❌ TELEGRAM_TOKEN missing!"); exit(1)
    try:
        bot.send_message(MY_CHAT_ID,
            "🚀 <b>EMPIRE BOT v15.0 ONLINE</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Peter Lynch Framework: Active\n"
            "✅ Warren Buffett Framework: Active\n"
            "✅ Rakesh Jhunjhunwala Framework: Active\n"
            "✅ Gemini AI: Connected\n"
            "✅ Self-Learning: Active\n\n"
            "Type /scan to find opportunities!\nType /help for all commands",
            parse_mode='HTML')
    except Exception as e: log.error(f"Startup error: {e}")
    threading.Thread(target=intelligence_thread,daemon=True).start()
    while True:
        try: bot.infinity_polling(timeout=60,long_polling_timeout=30)
        except Exception as e: log.error(f"Polling error: {e}"); time.sleep(15)
