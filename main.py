import telebot
import sqlite3
import os
from datetime import datetime
from flask import Flask, request
from threading import Thread
from telebot.types import ReplyKeyboardMarkup

# --- Переменные окружения ---
TOKEN = os.getenv("TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS").split(",")))

bot = telebot.TeleBot(TOKEN)

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

# --- Обработчики ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    if message.chat.id not in ALLOWED_USERS:
        bot.send_message(message.chat.id, "⛔ Нет доступа.")
        return
    bot.send_message(message.chat.id, "👋 Добро пожаловать в Логопед-Бота!", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "▶️ Главное меню")
def restart_interface(message):
    bot.send_message(message.chat.id, "🔁 Главное меню обновлено.", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить клиента")
def ask_client_name(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, save_client_name)

def save_client_name(message):
    try:
        c.execute("INSERT INTO clients (name) VALUES (?)", (message.text,))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Клиент {message.text} добавлен.")
    except:
        bot.send_message(message.chat.id, "⚠️ Клиент уже существует.")

@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def list_clients(message):
    c.execute("SELECT name FROM clients")
    clients = c.fetchall()
    msg = "\n".join([f"• {name[0]}" for name in clients]) if clients else "❌ Клиентов пока нет."
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda msg: msg.text == "📅 Записать клиента")
def ask_who_to_schedule(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, ask_date)

def ask_date(message):
    name = message.text
    c.execute("SELECT id FROM clients WHERE name = ?", (name,))
    result = c.fetchone()
    if result:
        client_id = result[0]
        msg = bot.send_message(message.chat.id, "Введите дату занятия (ГГГГ-ММ-ДД):")
        bot.register_next_step_handler(msg, lambda m: save_session(m, client_id))
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

def save_session(message, client_id):
    try:
        date = datetime.strptime(message.text, "%Y-%m-%d").date()
        c.execute("INSERT INTO sessions (client_id, date) VALUES (?, ?)", (client_id, str(date)))
        conn.commit()
        bot.send_message(message.chat.id, "📅 Занятие записано.")
    except:
        bot.send_message(message.chat.id, "⚠️ Неверный формат даты.")

@bot.message_handler(func=lambda msg: msg.text == "✅ Отметить посещение")
def ask_attendance_name(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, mark_attended)

def mark_attended(message):
    name = message.text
    today = datetime.now().date()
    c.execute("SELECT id FROM clients WHERE name = ?", (name,))
    client = c.fetchone()
    if client:
        client_id = client[0]
        c.execute("UPDATE sessions SET attended = 1 WHERE client_id = ? AND date = ?", (client_id, str(today)))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Посещение отмечено.")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

@bot.message_handler(func=lambda msg: msg.text == "💰 Внести оплату")
def ask_payment_name(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, ask_amount)

def ask_amount(message):
    name = message.text
    c.execute("SELECT id FROM clients WHERE name = ?", (name,))
    client = c.fetchone()
    if client:
        client_id = client[0]
        msg = bot.send_message(message.chat.id, "Введите сумму оплаты:")
        bot.register_next_step_handler(msg, lambda m: save_payment(m, client_id))
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

def save_payment(message, client_id):
    try:
        amount = int(message.text)
        c.execute("UPDATE clients SET balance = balance + ? WHERE id = ?", (amount, client_id))
        conn.commit()
        bot.send_message(message.chat.id, f"💰 Оплата {amount}₽ учтена.")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка суммы.")

@bot.message_handler(func=lambda msg: msg.text == "📊 Баланс клиента")
def ask_balance_name(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, show_balance)

def show_balance(message):
    name = message.text
    c.execute("SELECT balance FROM clients WHERE name = ?", (name,))
    result = c.fetchone()
    if result:
        bot.send_message(message.chat.id, f"💸 Баланс {name}: {result[0]}₽")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

@bot.message_handler(func=lambda msg: msg.text == "🧾 История клиента")
def ask_history_name(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, show_history)

def show_history(message):
    name = message.text
    c.execute("SELECT id, balance FROM clients WHERE name = ?", (name,))
    client = c.fetchone()
    if not client:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
        return

    client_id, balance = client
    c.execute("SELECT date, attended FROM sessions WHERE client_id = ? ORDER BY date", (client_id,))
    sessions = c.fetchall()

    if not sessions:
        bot.send_message(message.chat.id, f"📭 У клиента {name} пока нет занятий.")
        return

    text = f"📘 История для {name}:\nБаланс: {balance}₽\n\n"
    for date, attended in sessions:
        status = "✅ Был" if attended else "❌ Не был"
        text += f"{date}: {status}\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text == "🗓️ Отчёт на неделю")
def weekly_report(message):
    today = datetime.now().date()
    end = today.replace(day=min(today.day + 6, 28))
    c.execute("""SELECT clients.name, sessions.date, sessions.attended
                 FROM sessions
                 JOIN clients ON clients.id = sessions.client_id
                 WHERE date BETWEEN ? AND ?
                 ORDER BY date""", (str(today), str(end)))
    rows = c.fetchall()
    if rows:
        text = ""
        for name, date, attended in rows:
            status = "✅" if attended else "❌"
            text += f"{date}: {name} — {status}\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "🕒 Записей на неделю нет.")

# --- Flask сервер для webhook ---
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Я жив!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
