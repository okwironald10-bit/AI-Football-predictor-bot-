import requests, math, os, threading
from flask import Flask
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot is alive!"

API_FOOTBALL_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
HEADERS = {'x-apisports-key': API_FOOTBALL_KEY}

def poisson(lam, k):
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def predict(home_exp, away_exp):
    total = home_exp + away_exp
    p0 = poisson(total, 0); p1 = poisson(total, 1); p2 = poisson(total, 2)
    over15 = (1 - p0 - p1) * 100
    over25 = (1 - p0 - p1 - p2) * 100
    hw=d=aw=0
    for i in range(6):
        for j in range(6):
            p = poisson(home_exp, i) * poisson(away_exp, j)
            if i>j: hw+=p
            elif i==j: d+=p
            else: aw+=p
    btts = (1-poisson(home_exp,0))*(1-poisson(away_exp,0))*100
    return over15, over25, hw*100, d*100, aw*100, btts

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching all leagues...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={date_str}"
    try:
        games = requests.get(url, headers=HEADERS, timeout=15).json().get('response', [])[:80]
    except:
        games = []
    if not games:
        await update.message.reply_text("No games today or API limit reached")
        return
    msg = f"PREDICTIONS {date_str}\n\n"
    for f in games[:30]:
        league = f['league']['name']; home = f['teams']['home']['name']; away = f['teams']['away']['name']
        avg = 3.4 if "U19" in league or "U20" in league or "U23" in league else 2.8
        o15, o25, hw, dr, aw, btts = predict(avg*0.63, avg*0.51)
        dc = "1X" if hw+dr > aw+dr else "X2"
        msg += f"{league}\n{home} vs {away}\nOver 1.5: {o15:.0f}% | Over 2.5: {o25:.0f}%\nDouble: {dc} | BTTS {btts:.0f}%\n\n"
        if len(msg) > 3500:
            await update.message.reply_text(msg); msg=""
    if msg: await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Live! /today for predictions")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
import threading
threading.Thread(target=run_flask).start()
app.run_polling()
