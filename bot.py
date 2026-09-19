import telebot
import json
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
MUTES_FILE = 'mutes.json'
DELETED_FILE = 'deleted.json'

ADMIN_IDS = [8907438590]

TOKEN = '8861049978:AAG3ORrCkxdCyjX2WHhNEZE18ZfZLE7-QK8'

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_mutes(): return load_json(MUTES_FILE, {})
def save_mutes(d): save_json(MUTES_FILE, d)
def load_deleted(): return load_json(DELETED_FILE, [])
def save_deleted(d): save_json(DELETED_FILE, d)

def is_muted(owner_id, user_id):
    mutes = load_mutes()
    return str(user_id) in mutes.get(str(owner_id), [])

def mute_user(owner_id, user_id):
    mutes = load_mutes()
    key = str(owner_id)
    if key not in mutes: mutes[key] = []
    uid = str(user_id)
    if uid not in mutes[key]:
        mutes[key].append(uid)
    save_mutes(mutes)

def unmute_user(owner_id, user_id):
    mutes = load_mutes()
    key = str(owner_id)
    if key not in mutes: return
    uid = str(user_id)
    if uid in mutes[key]:
        mutes[key].remove(uid)
    save_mutes(mutes)

def get_muted_list(owner_id):
    mutes = load_mutes()
    return mutes.get(str(owner_id), [])

bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Creator on Secretary Bot is running')

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

# ===== КОМАНДЫ В ЛИЧКЕ С БОТОМ =====

@bot.message_handler(commands=['start'])
def cmd_start(message):
    text = (
        f"👤 <b>CREATOR ON — SECRETARY</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Я помогаю управлять твоими ЛС.\n"
        f"Подключи меня через Telegram →\n"
        f"<b>Настройки → Автоматизация чатов</b>\n\n"
        f"<b>Команды (отвечай на сообщение юзера):</b>\n"
        f"🔇 <code>.myt</code> — заглушить юзера\n"
        f"🔊 <code>.unmyt</code> — размутить\n"
        f"📋 <code>.mytlist</code> — список мута\n"
        f"💬 <code>.спам слово</code> — 50 сообщений\n\n"
        f"<b>В чате с ботом:</b>\n"
        f"🗑 <code>/deleted</code> — удалённые сообщения"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['help'])
def cmd_help(message):
    cmd_start(message)

@bot.message_handler(commands=['deleted'])
def cmd_deleted(message):
    uid = str(message.from_user.id)
    if int(uid) not in ADMIN_IDS:
        return
    deleted = load_deleted()
    my_deleted = [d for d in deleted if d.get('owner_id') == uid]
    if not my_deleted:
        bot.send_message(message.chat.id, "🗑 Удалённых нет.")
        return
    text = "🗑 <b>Последние удалённые:</b>\n\n"
    for d in my_deleted[-20:]:
        uname = d.get('user_name', 'Аноним')
        utext = d.get('text', '')[:100]
        text += f"👤 <b>{uname}</b>: {utext}\n\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ===== BUSINESS-СООБЩЕНИЯ (Secretary Mode) =====

@bot.business_message_handler(content_types=['text'])
def handle_business_text(message):
    try:
        owner_id = str(message.chat.id)
        user = message.from_user
        user_id = str(user.id)
        text = message.text or ''

        if text.startswith('.'):
            handle_command(message, owner_id, user_id, text)
            return

        if is_muted(owner_id, user_id):
            try:
                bot.delete_business_messages(
                    business_connection_id=message.business_connection_id,
                    message_ids=[message.message_id]
                )
            except Exception as e:
                print('delete error:', e)
            try:
                bot.send_message(
                    int(user_id),
                    "🚫 <b>Ты в муте.</b>\nТвои сообщения не доходят.",
                    parse_mode='HTML'
                )
            except: pass
            save_deleted_msg(owner_id, user, text, 'muted')
            return

        save_deleted_msg(owner_id, user, text, 'received')

    except Exception as e:
        print('business text error:', e)

@bot.business_message_handler(content_types=['photo','video','document','voice','audio','sticker','animation'])
def handle_business_media(message):
    try:
        owner_id = str(message.chat.id)
        user = message.from_user
        user_id = str(user.id)
        if is_muted(owner_id, user_id):
            try:
                bot.delete_business_messages(
                    business_connection_id=message.business_connection_id,
                    message_ids=[message.message_id]
                )
            except: pass
            try:
                bot.send_message(int(user_id), "🚫 <b>Ты в муте.</b>", parse_mode='HTML')
            except: pass
    except Exception as e:
        print('business media error:', e)

def handle_command(message, owner_id, user_id, text):
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ''

    reply_to = message.reply_to_message
    if not reply_to:
        try:
            bot.send_message(
                int(owner_id),
                "❌ Ответь <b>на сообщение юзера</b>, а потом напиши команду.",
                parse_mode='HTML'
            )
        except: pass
        return

    target_user = reply_to.from_user
    target_id = str(target_user.id)
    target_name = target_user.first_name or 'юзер'

    if cmd == '.myt':
        mute_user(owner_id, target_id)
        try:
            bot.send_message(
                int(owner_id),
                f"🔇 <b>Заглушил</b> {target_name} (<code>{target_id}</code>).",
                parse_mode='HTML'
            )
        except: pass
        try:
            bot.send_message(
                int(target_id),
                "🚫 <b>Ты в муте.</b>\nТвои сообщения не доходят.",
                parse_mode='HTML'
            )
        except: pass
        return

    if cmd == '.unmyt':
        unmute_user(owner_id, target_id)
        try:
            bot.send_message(
                int(owner_id),
                f"🔊 <b>Размутил</b> {target_name}.",
                parse_mode='HTML'
            )
        except: pass
        try:
            bot.send_message(int(target_id), "✅ Тебя размутили.")
        except: pass
        return

    if cmd == '.mytlist':
        muted = get_muted_list(owner_id)
        if not muted:
            bot.send_message(int(owner_id), "📋 Список пуст.")
            return
        text_out = "📋 <b>Заглушённые:</b>\n\n"
        for i, uid in enumerate(muted, 1):
            text_out += f"{i}. <code>{uid}</code>\n"
        bot.send_message(int(owner_id), text_out, parse_mode='HTML')
        return

    if cmd == '.спам':
        word = arg.strip() if arg.strip() else 'привет'
        threading.Thread(
            target=send_spam,
            args=[target_id, word, 50, owner_id]
        ).start()
        try:
            bot.send_message(
                int(owner_id),
                f"💬 <b>Отправляю 50 сообщений</b> юзеру {target_name}.",
                parse_mode='HTML'
            )
        except: pass
        return

def send_spam(target_id, word, count, owner_id):
    sent = 0
    for i in range(count):
        try:
            bot.send_message(int(target_id), word)
            sent += 1
            time.sleep(1)
        except Exception as e:
            err = str(e).lower()
            if 'too many' in err or 'retry' in err:
                time.sleep(30)
                try:
                    bot.send_message(int(target_id), word)
                    sent += 1
                except: pass
            else:
                break
    try:
        bot.send_message(
            int(owner_id),
            f"✅ Спам завершён. Отправлено: <b>{sent}/{count}</b>.",
            parse_mode='HTML'
        )
    except: pass

def save_deleted_msg(owner_id, user, text, msg_type='received'):
    try:
        deleted = load_deleted()
        deleted.append({
            'owner_id': str(owner_id),
            'user_id': str(user.id),
            'user_name': user.first_name or 'Аноним',
            'text': text,
            'type': msg_type,
            'ts': int(time.time())
        })
        if len(deleted) > 500:
            deleted = deleted[-500:]
        save_deleted(deleted)
    except: pass

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start', '📖 Справка'),
            types.BotCommand('help', '💬 Помощь'),
            types.BotCommand('deleted', '🗑 Удалённые'),
        ])
    except: pass

set_commands()
print('Creator on Secretary Bot запущен')
bot.infinity_polling(
    allowed_updates=["message", "business_connection", "business_message",
                     "edited_business_message", "deleted_business_messages"],
    timeout=30
)
