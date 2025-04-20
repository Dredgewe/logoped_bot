import os
import sqlite3
import telebot
from datetime import datetime
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup
# --- Переменные окружения ---
TOKEN = os.getenv("TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))
VERCEL_URL = os.getenv("https://logoped-bot.vercel.app")  # например, 'https://logoped-bot.vercel.app'

bot = telebot.TeleBot(TOKEN)

# --- Flask сервер для Webhook ---
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# --- База данных ---
conn = sqlite3.connect("logoped_bot.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    balance INTEGER DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    date TEXT,
    attended INTEGER DEFAULT 0,
    FOREIGN KEY(client_id) REFERENCES clients(id)
)''')
conn.commit()

# --- Главное меню ---
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить клиента", "📋 Список клиентов")
    markup.add("📅 Записать клиента", "✅ Отметить посещение")
    markup.add("💰 Внести оплату", "📊 Баланс клиента")
    markup.add("🧾 История клиента", "🗓️ Отчёт на неделю")
    markup.add("▶️ Главное меню")
    return markup

# --- Обработчики команд и кнопок ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    if message.chat.id not in ALLOWED_USERS:
        bot.send_message(message.chat.id, "⛔ Нет доступа.")
        return
    bot.send_message(message.chat.id, "👋 Добро пожаловать в Логопед-Бота!", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "▶️ Главное меню")
def restart_interface(message):
    bot.send_message(message.chat.id, "🔁 Главное меню обновлено.", reply_markup=main_menu())

# --- Установка webhook ---
webhook_url = f"{VERCEL_URL}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=webhook_url)

# --- Запуск приложения (для Vercel используется wsgi.py) ---
application = app
