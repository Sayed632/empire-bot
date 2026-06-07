import os
import time
import json
import datetime
import logging
import pandas as pd
import yfinance as yf
import feedparser
import telebot
import google.generativeai as genai
import matplotlib
# Force matplotlib to use a non-interactive backend for headless GitHub servers
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    debt_to_equity = info.get('debtToEquity', 100)
    if debt_to_equity is not None and debt_to_equity < 50: 
        score += 20
        reasons.append("Low leverage (Financial Strength)")
        
    # Secret 2: The 'Scaling' (E2E Networks Style)
    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth is not None and rev_growth > 0.25:
        score += 25
        reasons.append(f"Hyper-growth: +{rev_growth*100:.0f}% Rev")

    # Secret 3: The 'Accumulation' (RJ Style)
    vol_avg = df['Volume'].tail(20).mean()
    vol_today = df['Volume'].iloc[-1] if not df.empty else 0
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

# 3. SHAREHOLDING ENGINE (Generates & Saves Donut Chart Image)
def generate_shareholding_chart(ticker, info):
    """Parses structural shareholding metrics and renders a clean donut chart vector."""
    # Pull percentages from yfinance info dictionary
    promoter_held = info.get('heldPercentInsiders', 0.50) * 100
    inst_held = info.get('heldPercentInstitutions', 0.25) * 100
    
    # Fallback defaults if values are missing or zero
    if promoter_held == 0 and inst_held == 0:
        promoter_held, inst_held = 50.95, 32.31
        
    public_held = max(0, 100 - (promoter_held + inst_held))
    
    # Compile Summary Data Frame
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

    # Convert standard slice representation into a Donut Mask ring
    centre_circle = plt.Circle((0, 0), 0.65, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.legend(wedges, categories, title="Categories", loc="upper right", bbox_to_anchor=(1.2, 1))
    ax.set_title(f"{ticker} - Shareholding Structural Distribution", weight='bold', size=12)
    plt.tight_layout()

    # Export out raw image asset locally
    image_filename = f"{ticker}_shareholding.png"
    plt.savefig(image_filename, dpi=300, bbox_inches='tight')
    plt.close()
    return image_filename

# 4. THE AI AGENT SCANNER ENGINE
def hunt_multibaggers():
    print("🎯 Starting AI Hunter Agent market scan...")
    macro_context = get_macro_tailwind()
    
    # Prioritized processing list
    universe = ["SUZLON", "LAURUSLABS", "NELCO", "HINDALCO", "HINDZINC", "E2ENETWORKS", "TATAELXSI", "HAL"]
    
    hits_found = False
    for ticker in universe:
        try:
            t = yf.Ticker(f"{ticker}.NS")
            df = t.history(period="6mo")
            if df.empty: continue
            
            score, DNA_reasons = get_multibagger_dna(ticker, t.info, df)
            
            # Identify "Pre-Surge" (Score > 40)
            if score >= 40:
                hits_found = True
                
                # Render specialized donut chart visual asset on the fly
                chart_img = generate_shareholding_chart(ticker, t.info)
                
                # Format complete alert payload text block 
                msg = (
                    f"🚀 **POTENTIAL MULTIBAGGER ALERT: {ticker}**\n\n"
                    f"🏆 **DNA Match Score**: `{score}/100`\n"
                    f"💡 **Key Triggers**: {', '.join(DNA_reasons)}\n"
                    f"🌍 **Macro Context**: {macro_context}\n\n"
                    f"📊 *Visual Shareholding Summary attached below.*"
                )
                
                # Dispatch image containing textual caption via Telegram
                with open(chart_img, 'rb') as photo:
                    bot.send_photo(MY_CHAT_ID, photo, caption=msg, parse_mode='Markdown')
                print(f"✅ Alert sent for {ticker}")
                
                # Delete temporary disk image asset to optimize environment storage
                if os.path.exists(chart_img):
                    os.remove(chart_img)
                    
        except Exception as e:
            print(f"Error handling operations on ticker {ticker}: {str(e)}")
            continue

    if not hits_found:
        bot.send_message(MY_CHAT_ID, "No high-conviction pre-surge matches found today.")
        print("📁 Scan finished with 0 alerts sent.")

# 5. AUTOMATED EXECUTION ENTRY POINT
if __name__ == "__main__":
    print("🚀 Triggering automated market hunting sequence...")
    hunt_multibaggers()
    print("✅ Hunting complete. Powering down GitHub Action container smoothly.")
    
