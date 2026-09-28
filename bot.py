import telebot
import os
import threading
import requests
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

TOKEN = '8514412667:AAFR0fwoa0CTvTdFJZSK65-4isUDJB7_o50'  # токен бота от @BotFather
WEBAPP_URL = 'https://darkgram-2.onrender.com'  # адрес Mini App
API_URL = 'https://darkgram-2.onrender.com'  # для API запросов

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
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='Открыть Mini App',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    return kb


def do_search(query, uid, name):
    """Вызов API сервера."""
    try:
        r = requests.post(
            f'{API_URL}/api/search',
            json={'uid': uid, 'name': name, 'query': query},
            timeout=60
        )
        if r.status_code == 200:
            return r.json()
        try:
            return r.json()
        except:
            return {'error': 'Ошибка сервера'}
    except Exception as e:
        print('api err:', e)
        return {'error': 'Не удалось связаться с сервером'}


# ==================== /start ====================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='Открыть Mini App',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))

    text = (
        'DeepSeek Darkgram\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Привет, ' + (m.from_user.first_name or 'друг') + '!\n\n'
        'AI-поиск с интернетом.\n\n'
        'Просто напиши вопрос — отвечу.\n'
        'Или открой Mini App кнопкой ниже.\n\n'
        '/help — подробнее'
    )
    bot.send_message(m.chat.id, text, reply_markup=kb)


# ==================== /help ====================
@bot.message_handler(commands=['help'])
def cmd_help(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='Открыть Mini App',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))

    text = (
        'DeepSeek Darkgram\n'
        '━━━━━━━━━━━━━━━\n\n'
        '<b>ЧТО ЭТО</b>\n\n'
        'AI-поисковик с интернетом.\n'
        'Задаёшь вопрос → ищет в интернете → '
        'даёт умный ответ через нейросеть.\n\n'
        '<b>ВОЗМОЖНОСТИ AI</b>\n\n'
        '• Ищет в интернете\n'
        '• Отвечает через нейросеть\n'
        '• Оформляет ответ: <b>жирный</b>, <code>код</code>\n'
        '• Не упоминает источники — просто ответ\n'
        '• 10 источников за запрос\n\n'
        '<b>КАК ПОЛЬЗОВАТЬСЯ</b>\n\n'
        '<b>В боте:</b>\n'
        '• Напиши вопрос в личке\n'
        '• Или упомяни @бот в группе\n'
        '• Или ответь на моё сообщение\n\n'
        '<b>В Mini App:</b>\n'
        '• Открой кнопкой ниже\n'
        '• Больше функций: топ, профиль, графики\n\n'
        '<b>КОМАНДЫ</b>\n\n'
        '/start — начать\n'
        '/help — эта справка\n'
        '/app — открыть Mini App\n\n'
        '<b>ТОКЕНЫ</b>\n\n'
        '• 1000 при старте\n'
        '• +50 каждый день\n'
        '• 1 токен = 1 запрос'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)


# ==================== /app ====================
@bot.message_handler(commands=['app'])
def cmd_app(m):
    bot.send_message(m.chat.id, 'Открой Mini App:', reply_markup=webapp_kb())


# ==================== ПОИСК ====================
def handle_query(m, query):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Гость'

    msg = bot.send_message(m.chat.id, 'Поиск в интернете...')

    data = do_search(query, uid, name)

    if data.get('error') == 'tokens':
        try:
            bot.edit_message_text(
                'Недостаточно токенов.\n\nОткрой Mini App — там +50 каждый день.',
                chat_id=m.chat.id, message_id=msg.message_id,
                reply_markup=webapp_kb()
            )
        except: pass
        return

    if data.get('error'):
        try:
            bot.edit_message_text(
                data.get('message', data['error']),
                chat_id=m.chat.id, message_id=msg.message_id
            )
        except: pass
        return

    answer = data.get('answer', '')

    try:
        bot.edit_message_text(
            answer,
            chat_id=m.chat.id,
            message_id=msg.message_id,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except Exception as e:
        print('html err:', e)
        try:
            clean = re.sub(r'<[^>]+>', '', answer)
            bot.edit_message_text(
                clean,
                chat_id=m.chat.id,
                message_id=msg.message_id,
                disable_web_page_preview=True
            )
        except Exception as e2:
            print('text err:', e2)


@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text and not m.text.startswith('/'))
def handle_private(m):
    handle_query(m, m.text.strip())


@bot.message_handler(func=lambda m: m.chat.type in ('group', 'supergroup') and m.text and not m.text.startswith('/'))
def handle_group(m):
    text = m.text.strip()
    bot_username = bot.get_me().username
    triggered = False

    if m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id:
        triggered = True
    elif f'@{bot_username}' in text:
        text = text.replace(f'@{bot_username}', '').strip()
        triggered = True

    if not triggered or not text:
        return

    handle_query(m, text)


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('DeepSeek Darkgram bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
