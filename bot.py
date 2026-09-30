import telebot
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

TOKEN = '8514412667:AAEL2Iy4ImjPNd0qhapit-Ge6k3fkfFj37I'
WEBAPP_URL = 'https://ТВОЙ_СЕРВЕР.onrender.com'

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


@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🏛️ Открыть игру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    text = (
        '🏛️ <b>RP Countries</b>\n\n'
        'Игра про управление страной.\n\n'
        'Выбери страну и развивай её:\n'
        'экономика, армия, города.\n\n'
        'Жми кнопку ниже 👇'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)


@bot.message_handler(commands=['play'])
def cmd_play(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🏛️ Открыть игру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(m.chat.id, 'Открой игру:', reply_markup=kb)


if __name__ == '__main__':
    print('RP bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
