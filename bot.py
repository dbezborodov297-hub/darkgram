import telebot
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

TOKEN = '8514412667:AAE3rjZDJqpHDEi5x2qNwlNYPBoFlFJcevQ'
WEBAPP_URL = 'https://darkgram-2.onrender.com'

bot = telebot.TeleBot(TOKEN)

try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Webhook deleted')
except Exception as e:
    print('webhook err:', e)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot running')


def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


threading.Thread(target=run_http, daemon=True).start()


def webapp_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🌺 Открыть Флориссант',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    return kb


@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = (
        '🌸 ФЛОРИССАНТ\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Привет, ' + (m.from_user.first_name or 'друг') + '!\n\n'
        'Это платформа конкурсов и творчества.\n\n'
        '🎨 Участвуй в конкурсах\n'
        '📸 Отправляй свои работы\n'
        '🏆 Побеждай\n\n'
        '👇 Открой приложение:'
    )
    bot.send_message(m.chat.id, text, reply_markup=webapp_kb())


@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        '🌸 ФЛОРИССАНТ — помощь\n\n'
        '• Открой приложение кнопкой ниже\n'
        '• Выбери конкурс и участвуй\n'
        '• Следи за своими заявками\n\n'
        'Разработка: Флориссант',
        reply_markup=webapp_kb())


@bot.message_handler(commands=['app'])
def cmd_app(m):
    bot.send_message(m.chat.id, '🌸 Открой Флориссант:', reply_markup=webapp_kb())


if __name__ == '__main__':
    print('Florissant bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
