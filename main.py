import telebot
import sqlite3
from datetime import datetime, timedelta

# Вставь сюда свой токен Telegram
TOKEN = '7544395313:AAF5Q52CV4_G2dEk5yU8RF-ipUodBJEBojQ'
# Вставь сюда Telegram ID мамы
ALLOWED_USERS = [slepenchuk99]

bot = telebot.TeleBot(TOKEN)

# Подключаемся к базе данных SQLite
conn = sqlite3.connect('logoped_bot.db', check_same_thread=False)
c = conn.cursor()

# Создаём таблицы для хранения клиентов и занятий
c.execute('''CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY,
                name TEXT,
                balance INTEGER DEFAULT 0
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                datetime TEXT,
                attended INTEGER DEFAULT 0,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )''')

# Проверка доступа пользователя
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id not in ALLOWED_USERS:
        bot.reply_to(message, '⛔ Нет доступа.')
        return
    bot.reply_to(message, '🌟 Добро пожаловать в ЛогоБота!')

# Здесь далее будет код с кнопками, логикой записи, оплаты, баланса и т.д.

bot.polling()
