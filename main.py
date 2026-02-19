import telebot
from telebot import types
import google.generativeai as genai
import sqlite3
import secrets
import string
from flask import Flask
from threading import Thread

# --- ТАНЗИМОТ ---
TOKEN = '8126192450:AAHjRkWshwnvbKXU5saAF_ChNU6X4JVC6aU'
GEMINI_KEY = 'AIzaSyBMtb30V4UkMw_XbDyytHdthDGic7AWP_8'
ADMIN_ID = 8014656470 # ID-и дурусти ту ✅
DC_NUMBER = "+992904104860"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# Танзими Gemini AI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- БАЗАИ МАЪЛУМОТ ---
conn = sqlite3.connect('empire_final.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, img_count INTEGER DEFAULT 0, status TEXT DEFAULT "free")')
cursor.execute('CREATE TABLE IF NOT EXISTS promo_codes (code TEXT PRIMARY KEY, used INTEGER DEFAULT 0)')
conn.commit()

@app.route('/')
def home(): return "Empire AI is Online ⚡"

def run_web(): app.run(host='0.0.0.0', port=8080)

# --- МЕНЮ ---
def get_main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add("🧠 Пурсиш аз AI", "🖼 Сохтани Сурат (AI)")
    m.add("🔑 Фаъолсозии VIP", "📊 Профил ва Лимит")
    m.add("💳 Харидани Код", "📢 Реклама")
    return m

@bot.message_handler(commands=['start'])
def start(m):
    cursor.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (m.chat.id,))
    conn.commit()
    bot.send_message(m.chat.id, "💎 **Хуш омадед ба Империяи AI!**\n\nБо ёрии ин бот шумо метавонед сурат созед ва ба саволҳои худ ҷавоб гиред.", reply_markup=get_main_menu())

# СОХТАНИ СУРАТ
@bot.message_handler(func=lambda m: m.text == "🖼 Сохтани Сурат (AI)")
def img_ask(m):
    user = cursor.execute('SELECT img_count, status FROM users WHERE id = ?', (m.chat.id,)).fetchone()
    if user and user[1] == "free" and user[0] >= 10:
        bot.send_message(m.chat.id, "🚫 Лимити ройгони шумо тамом шуд. Лутфан коди VIP харед.")
        return
    msg = bot.send_message(m.chat.id, "🎨 Чиро расм кашам? (Масалан: A lion wearing a crown)")
    bot.register_next_step_handler(msg, process_image)

def process_image(m):
    try:
        status = bot.send_message(m.chat.id, "⏳ AI дар ҳоли сохтан...")
        url = f"https://pollinations.ai/p/{m.text.replace(' ', '%20')}?width=1024&height=1024"
        bot.send_photo(m.chat.id, url, caption=f"✨ {m.text}\n💎 @Empire_Bot")
        cursor.execute('UPDATE users SET img_count = img_count + 1 WHERE id = ?', (m.chat.id,))
        conn.commit()
        bot.delete_message(m.chat.id, status.message_id)
    except:
        bot.send_message(m.chat.id, "❌ Хатогӣ дар сервер. Баъдтар кӯшиш кунед.")

# ПУРСИШ АЗ AI
@bot.message_handler(func=lambda m: m.text == "🧠 Пурсиш аз AI")
def ai_ask(m):
    msg = bot.send_message(m.chat.id, "🤖 Саволи худро нависед:")
    bot.register_next_step_handler(msg, lambda ms: bot.reply_to(ms, model.generate_content(ms.text).text))

# ФАЪОЛСОЗИИ КОД
@bot.message_handler(func=lambda m: m.text == "🔑 Фаъолсозии VIP")
def ask_v(m):
    msg = bot.send_message(m.chat.id, "🔑 Коди VIP-и худро ворид кунед:")
    bot.register_next_step_handler(msg, use_v)

def use_v(m):
    code = m.text.strip()
    cursor.execute('SELECT used FROM promo_codes WHERE code = ?', (code,))
    res = cursor.fetchone()
    if res and res[0] == 0:
        cursor.execute('UPDATE promo_codes SET used = 1 WHERE code = ?', (code,))
        cursor.execute('UPDATE users SET img_count = 0, status = "vip" WHERE id = ?', (m.chat.id,))
        conn.commit()
        bot.send_message(m.chat.id, "🎉 VIP бо муваффақият фаъол шуд! Лимитҳои шумо нав шуданд.")
        bot.send_message(ADMIN_ID, f"🔔 Юзер {m.chat.id} кодро истифода бурд: `{code}`")
    else:
        bot.send_message(m.chat.id, "❌ Код хато аст ё аллакай истифода шудааст.")

# ГЕНЕРАТСИЯИ КОД (ТАНҲО БАРОИ ТУ)
@bot.message_handler(commands=['gen'])
def cmd_gen(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        num = int(m.text.split()[1])
        codes = []
        for _ in range(num):
            code = "VIP-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            cursor.execute('INSERT INTO promo_codes (code) VALUES (?)', (code,))
            codes.append(f"`{code}`")
        conn.commit()
        bot.send_message(m.chat.id, f"✅ {num} коди нав сохта шуд:\n\n" + "\n".join(codes), parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "Мисол: `/gen 5`")

@bot.message_handler(func=lambda m: m.text == "📊 Профил ва Лимит")
def stats(m):
    u = cursor.execute('SELECT img_count, status FROM users WHERE id = ?', (m.chat.id,)).fetchone()
    bot.send_message(m.chat.id, f"👤 **Профили шумо:**\nСтатус: {u[1].upper()}\nРасмҳои сохташуда: {u[0]}/10")

@bot.message_handler(func=lambda m: m.text == "💳 Харидани Код")
def pay(m):
    bot.send_message(m.chat.id, f"💳 Барои харидани код ба DC Wallet маблағ гузаронед:\n\nҲамён: `{DC_NUMBER}`\nМаблағ: **30 сомон**\n\nЧекро ба @Bot_creator_tj фиристед.")

if __name__ == "__main__":
    bot.remove_webhook() # Муҳим барои пешгирии хатогии 409
    Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
