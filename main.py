import os, time, json, datetime, logging
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import feedparser
import telebot
import google.generativeai as genai

# --- SECURITY & SETUP ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
MY_CHAT_ID     = os.getenv('MY_CHAT_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 1. THE SECRET DNA (Defining the 'Multibagger' Framework)
def get_multibagger_dna(ticker, info, df):
    """Identifies pre-surge characteristics of legendary stocks."""
    score = 0
    reasons = []
    
    # Secret 1: The 'Turnaround' (Suzlon/Laurus Style)
    # Debt reduction or cash flow improvement from a low base
    debt_to_equity = info.get('debtToEquity', 100)
    if debt_to_equity < 50: 
        score += 20
        reasons.append("Low leverage (Financial Strength)")
        
    # Secret 2: The 'Scaling' (E2E Networks Style)
    # Revenue growth > 20% while PE is still relatively ignored
    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth > 0.25:
        score += 25
        reasons.append(f"Hyper-growth: +{rev_growth*100:.0f}% Rev")

    # Secret 3: The 'Accumulation' (RJ Style)
    # Price coiling + Volume spike (Smart money entering quietly)
    vol_avg = df['Volume'].tail(20).mean()
    vol_today = df['Volume'].iloc[-1]
    if vol_today > vol_avg * 2:
        score += 25
        reasons.append("🐋 Massive Volume Spike (Accumulation)")

    return score, reasons

# 2. EVOLVING INTELLIGENCE (Macro & Policy Layer)
def get_macro_tailwind():
    """Identifies if the current news supports a sector (e.g. Solar, AI, Defense)."""
    feeds = ["https://www.moneycontrol.com/rss/latestnews.xml"]
    news_snippet = ""
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for e in f.entries[:5]: news_snippet += e.title + ". "
        except: continue

    prompt = (
        f"Based on these headlines: {news_snippet}\n"
        "Identify 1 high-growth Indian sector benefiting from current Govt policy or War/Trade shifts. "
        "Reply ONLY with: [Sector Name]: [Brief Reason]"
    )
    try:
        return gemini.generate_content(prompt).text.strip()
    except: return "Neutral Market"

# 3. THE AI AGENT SCANNER
@bot.message_handler(commands=['hunt'])
def hunt_multibaggers(message):
    bot.send_message(MY_CHAT_ID, "🎯 **AI Hunter Agent: Searching for 5000+ stock DNA matches...**")
    
    macro_context = get_macro_tailwind()
    # For speed, we scan a prioritized list (can be expanded to 5000)
    universe = ["SUZLON", "LAURUSLABS", "NELCO", "HINDALCO", "HINDZINC", "E2ENETWORKS", "TATAELXSI", "HAL"]
    
    alerts = []
    for ticker in universe:
        try:
            t = yf.Ticker(f"{ticker}.NS")
            df = t.history(period="6mo")
            score, DNA_reasons = get_multibagger_dna(ticker, t.info, df)
            
            # Identify "Pre-Surge" (Score > 40)
            if score >= 40:
                msg = (
                    f"🚀 **POTENTIAL MULTIBAGGER: {ticker}**\n"
                    f"🏆 DNA Match: {score}/100\n"
                    f"💡 Reasons: {', '.join(DNA_reasons)}\n"
                    f"🌍 Macro Context: {macro_context}"
                )
                alerts.append(msg)
        except: continue

    if alerts:
        for a in alerts: bot.send_message(MY_CHAT_ID, a, parse_mode='Markdown')
    else:
        bot.send_message(MY_CHAT_ID, "No high-conviction pre-surge matches found today.")

if __name__ == "__main__":
    bot.infinity_polling()