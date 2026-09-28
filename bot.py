import telebot
import os
import threading
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

TOKEN = '8514412667:AAE35Ujh2S4wgncDMe3t35Kv1POYEUEWPQI' # токен бота
WEBAPP_URL = 'https://darkgram-2.onrender.com'  # адрес Mini App
SERVER_URL = 'https://darkgram-2.onrender.com'  # для API запросов

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
        text='Открыть поиск',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    return kb


def tavily_search(query, max_results=10):
    try:
        r = requests.post(
            'https://api.tavily.com/search',
            json={'query': query, 'search_depth': 'advanced',
                  'max_results': max_results, 'include_answer': False},
            timeout=20
        )
        if r.status_code == 200:
            return r.json().get('results', [])
        return []
    except Exception as e:
        print('tavily err:', e)
        return []


def ai_answer(query, sources):
    try:
        context = ''
        for s in sources[:5]:
            context += f"{s.get('title', '')}\n{s.get('content', '')}\n\n"

        prompt = f"""Вопрос: {query}

Информация:
{context}

Дай полный ответ на русском.

ПРАВИЛА:
- НЕ упоминай источники, ссылки, сайты
- НЕ пиши "согласно источникам", "[1]"
- Просто ответь как знающий эксперт
- Оформляй HTML: <b>жирный</b>, <code>код</code>, <i>курсив</i>
- Без вводных фраз"""

        for attempt in range(3):
            try:
                r = requests.post(
                    'https://text.pollinations.ai/openai',
                    json={'model': 'openai', 'messages': [
                        {'role': 'system', 'content': 'Ты — умный AI-ассистент. Отвечай на русском, оформляй HTML.'},
                        {'role': 'user', 'content': prompt}
                    ]},
                    timeout=60
                )
                if r.status_code == 200:
                    data = r.json()
                    answer = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if answer and len(answer) > 10:
                        return answer
            except Exception as e:
                print(f'ai err {attempt+1}:', e)
                time.sleep(1)
        return None
    except Exception as e:
        print('ai err:', e)
        return None


def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = (
        'DeepSeek Darkgram\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Привет, ' + (m.from_user.first_name or 'друг') + '!\n\n'
        'AI-поиск с интернетом.\n'
        'Задай вопрос — найду ответ.\n\n'
        '/search &lt;запрос&gt; — искать\n'
        '/app — открыть Mini App\n'
        '/help — помощь'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        'DeepSeek Darkgram — помощь\n\n'
        '/search <запрос> — поиск в интернете\n'
        '/app — открыть Mini App\n'
        '/help — справка\n\n'
        'Просто пиши вопросы в личке — отвечу.',
        reply_markup=webapp_kb())


@bot.message_handler(commands=['app'])
def cmd_app(m):
    bot.send_message(m.chat.id, 'Открой Mini App:', reply_markup=webapp_kb())


# ============ SEARCH COMMAND ============
@bot.message_handler(commands=['search'])
def cmd_search(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, 'Использование: /search <запрос>\n\nНапример: /search что такое квантовый компьютер')
        return
    query = parts[1].strip()
    do_ai_search(m, query)


# ============ AI SEARCH WITH STREAMING ============
def do_ai_search(m, query):
    # Отправляем сообщение процесса
    msg = bot.send_message(
        m.chat.id,
        'Поиск в интернете...',
        parse_mode='HTML'
    )

    try:
        # Этап 1: поиск
        sources = tavily_search(query, 10)
        time.sleep(0.3)
        try:
            bot.edit_message_text(
                'AI обрабатывает запрос...',
                chat_id=m.chat.id,
                message_id=msg.message_id
            )
        except: pass

        # Этап 2: AI
        answer = ai_answer(query, sources)
        if not answer:
            bot.edit_message_text(
                'Не удалось получить ответ. Попробуй позже.',
                chat_id=m.chat.id,
                message_id=msg.message_id
            )
            return

        # Этап 3: стриминг текста
        # Разбиваем ответ на чанки по 3-5 слов
        words = answer.split(' ')
        chunk_size = 4
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            if i > 0: chunk = ' ' + chunk
            chunks.append(chunk)

        # Показываем постепенно
        current_text = ''
        last_edit_time = time.time()

        for i, chunk in enumerate(chunks):
            current_text += chunk

            # Редактируем каждые 1.2 сек (антифлуд Telegram)
            now = time.time()
            if now - last_edit_time >= 1.2 or i == len(chunks) - 1:
                try:
                    display_text = current_text
                    if i < len(chunks) - 1:
                        display_text += ' ▌'  # курсор

                    # Telegram лимит 4096
                    if len(display_text) > 4000:
                        display_text = display_text[:4000] + '...'

                    bot.edit_message_text(
                        display_text,
                        chat_id=m.chat.id,
                        message_id=msg.message_id,
                        parse_mode='HTML'
                    )
                    last_edit_time = now
                except telebot.apihelper.ApiTelegramException as e:
                    if 'message is not modified' not in str(e):
                        print('edit err:', e)
                except Exception as e:
                    print('edit err:', e)

        # Финальное сообщение (без курсора)
        try:
            bot.edit_message_text(
                answer,
                chat_id=m.chat.id,
                message_id=msg.message_id,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except: pass

    except Exception as e:
        print('search err:', e)
        try:
            bot.edit_message_text(
                'Ошибка. Попробуй позже.',
                chat_id=m.chat.id,
                message_id=msg.message_id
            )
        except: pass


# ============ TEXT IN PRIVATE ============
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text and not m.text.startswith('/'))
def handle_private_text(m):
    do_ai_search(m, m.text.strip())


# ============ TEXT IN GROUPS ============
@bot.message_handler(func=lambda m: m.chat.type in ('group', 'supergroup') and m.text and not m.text.startswith('/'))
def handle_group_text(m):
    text = m.text.strip()
    # В группах — только по упоминанию или реплаю
    bot_username = bot.get_me().username
    triggered = False

    if m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id:
        triggered = True
    elif f'@{bot_username}' in text:
        text = text.replace(f'@{bot_username}', '').strip()
        triggered = True

    if not triggered or not text:
        return

    do_ai_search(m, text)


if __name__ == '__main__':
    print('DeepSeek Darkgram bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
