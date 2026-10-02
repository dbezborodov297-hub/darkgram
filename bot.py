import telebot
import sqlite3
import time
import json
import os
import threading
import re
from telebot import types

TOKEN = '8471116013:AAHY-XzbzkHWFd3DtsZoJJfejppnU6IrNrk'
ADMIN_IDS = [8907438590]  # ID админов через запятую: [123456789, 987654321]
CHANNEL_ID = None  # Куда публиковать одобренное (например: -1001234567890). None = не публиковать

bot = telebot.TeleBot(TOKEN)
DB = 'suggest.db'

# ============================================================
# ТЕМЫ
# ============================================================
TOPICS = {
    'news':     {'name': '📰 Новости',  'emoji': '📰'},
    'meme':     {'name': '😂 Мемы',     'emoji': '😂'},
    'question': {'name': '❓ Вопросы',  'emoji': '❓'},
    'ads':      {'name': '📢 Реклама',  'emoji': '📢'},
    'art':      {'name': '🎨 Арт',      'emoji': '🎨'},
    'idea':     {'name': '💡 Идеи',     'emoji': '💡'},
}


# ============================================================
# БД
# ============================================================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, name TEXT, topic TEXT, text TEXT,
        status TEXT DEFAULT 'pending',
        mod_uid INTEGER, mod_comment TEXT,
        created INTEGER, decided INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mods (
        uid INTEGER, topic TEXT,
        PRIMARY KEY (uid, topic)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        uid INTEGER PRIMARY KEY,
        until INTEGER,
        reason TEXT,
        by_uid INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mutes (
        uid INTEGER PRIMARY KEY,
        until INTEGER,
        reason TEXT,
        by_uid INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, reason TEXT, by_uid INTEGER, time INTEGER
    )''')
    conn.commit()
    conn.close()


init_db()


# ============================================================
# ХЕЛПЕРЫ
# ============================================================
def get_mod_topics(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT topic FROM mods WHERE uid=?', (uid,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def is_admin(uid):
    return uid in ADMIN_IDS


def is_mod(uid):
    return bool(get_mod_topics(uid)) or is_admin(uid)


def is_banned(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT until FROM bans WHERE uid=?', (uid,))
    row = c.fetchone()
    conn.close()
    if not row: return False
    until = row[0]
    if until == 0 or until > int(time.time()):
        return True
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (uid,))
    conn.commit()
    conn.close()
    return False


def is_muted(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
    row = c.fetchone()
    conn.close()
    if not row: return False
    until = row[0]
    if until == 0 or until > int(time.time()):
        return True
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (uid,))
    conn.commit()
    conn.close()
    return False


def parse_time(text):
    """Парсит время: 5m, 1h, 1d, forever, 0 = навсегда. Возвращает секунды или -1 для навсегда."""
    text = text.strip().lower()
    if text in ('forever', 'навсегда', '0', 'inf', 'infinity'):
        return 0
    m = re.match(r'^(\d+)\s*([smhd]?)$', text)
    if not m: return None
    num = int(m.group(1))
    unit = m.group(2) or 'm'
    mult = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return num * mult.get(unit, 60)


def fmt_time(seconds):
    if seconds == 0: return 'навсегда'
    if seconds < 60: return f'{seconds} сек'
    if seconds < 3600: return f'{seconds // 60} мин'
    if seconds < 86400: return f'{seconds // 3600} ч'
    return f'{seconds // 86400} д'


def time_until(until_ts):
    if until_ts == 0: return 'навсегда'
    left = until_ts - int(time.time())
    if left <= 0: return 'истёк'
    return fmt_time(left)


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add('📝 Предложить', '📋 Мои посты')
    if is_mod(uid):
        kb.add('🛡️ Модерация', '📊 Статистика')
    if is_admin(uid):
        kb.add('👑 Админ-панель')
    return kb


def topics_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, t in TOPICS.items():
        btns.append(types.InlineKeyboardButton(t['name'], callback_data=f'take_topic_{k}'))
    kb.add(*btns)
    return kb


def mod_actions_kb(post_id):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('✅ Одобрить', callback_data=f'mod_approve_{post_id}'),
        types.InlineKeyboardButton('❌ Отклонить', callback_data=f'mod_reject_{post_id}'),
    )
    kb.add(
        types.InlineKeyboardButton('💬 Комментарий', callback_data=f'mod_comment_{post_id}'),
        types.InlineKeyboardButton('🚫 Забанить', callback_data=f'mod_ban_{post_id}'),
    )
    return kb


def ban_duration_kb(action, uid):
    """action: ban / mute / unban / unmute"""
    kb = types.InlineKeyboardMarkup(row_width=3)
    times = [
        ('1м', '1m'), ('5м', '5m'), ('30м', '30m'),
        ('1ч', '1h'), ('6ч', '6h'), ('1д', '1d'),
        ('7д', '7d'), ('30д', '30d'), ('∞', 'forever'),
    ]
    btns = [types.InlineKeyboardButton(label, callback_data=f'{action}_dur_{uid}_{val}') for label, val in times]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('❌ Отмена', callback_data='cancel'))
    return kb


def admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('👤 Добавить модератора', callback_data='admin_addmod'),
        types.InlineKeyboardButton('📋 Список модераторов', callback_data='admin_listmods'),
        types.InlineKeyboardButton('🚫 Список банов', callback_data='admin_bans'),
        types.InlineKeyboardButton('🔇 Список мутов', callback_data='admin_mutes'),
    )
    return kb


def mods_topics_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for k, t in TOPICS.items():
        btns.append(types.InlineKeyboardButton(t['name'], callback_data=f'addmod_topic_{k}'))
    kb.add(*btns)
    return kb


# ============================================================
# START
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if is_banned(uid):
        bot.send_message(m.chat.id, '🚫 Ты забанен.')
        return
    text = (
        '👋 <b>Предложка</b>\n\n'
        'Присылай посты в наш канал!\n\n'
        '📝 <b>Предложить</b> — отправить пост\n'
        '📋 <b>Мои посты</b> — статус твоих заявок\n'
    )
    if is_mod(uid):
        text += '\n🛡️ <b>Модерация</b> — проверять посты\n'
    if is_admin(uid):
        text += '\n👑 <b>Админ-панель</b> — управление\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb(uid))


# ============================================================
# ПРЕДЛОЖКА
# ============================================================
user_states = {}  # uid -> {'action': ..., 'data': ...}


@bot.message_handler(func=lambda m: m.text == '📝 Предложить')
def cmd_suggest(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, '🚫 Ты забанен.')
    if is_muted(uid):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
        row = c.fetchone()
        conn.close()
        bot.send_message(m.chat.id, f'🔇 Ты в муте. Осталось: {time_until(row[0])}')
        return
    user_states[uid] = {'action': 'choose_topic'}
    bot.send_message(m.chat.id, '🗂️ Выбери тему:', reply_markup=topics_kb())


@bot.callback_query_handler(func=lambda c: c.data.startswith('take_topic_'))
def cb_take_topic(c):
    uid = c.from_user.id
    topic = c.data.replace('take_topic_', '')
    if topic not in TOPICS:
        return bot.answer_callback_query(c.id, 'Ошибка')
    user_states[uid] = {'action': 'write_post', 'topic': topic}
    bot.answer_callback_query(c.id)
    bot.edit_message_text(
        f'✍️ Тема: {TOPICS[topic]["name"]}\n\n'
        f'Напиши текст поста (от 5 до 2000 символов).',
        c.message.chat.id, c.message.message_id
    )
    bot.register_next_step_handler_by_chat_id(c.message.chat.id, handle_post_text, uid, topic)


def handle_post_text(m, uid, topic):
    if m.from_user.id != uid: return
    if not m.text: return
    text = m.text.strip()
    if len(text) < 5:
        bot.send_message(m.chat.id, '❌ Слишком коротко. Попробуй снова.')
        return
    if len(text) > 2000:
        text = text[:2000]

    # Сохраняем
    name = m.from_user.first_name or 'Аноним'
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''INSERT INTO posts (uid, name, topic, text, created) 
                 VALUES (?, ?, ?, ?, ?)''', (uid, name, topic, text, int(time.time())))
    post_id = c.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, '✅ Пост отправлен на модерацию!', reply_markup=main_kb(uid))
    user_states.pop(uid, None)

    # Отправляем модераторам темы
    send_to_mods(post_id, uid, name, topic, text)


def send_to_mods(post_id, author_uid, author_name, topic, text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT uid FROM mods WHERE topic=?', (topic,))
    mod_uids = [r[0] for r in c.fetchall()]
    conn.close()

    mod_uids.extend(ADMIN_IDS)
    mod_uids = list(set(mod_uids))

    topic_name = TOPICS[topic]['name']
    caption = (
        f'📬 <b>Новый пост #{post_id}</b>\n\n'
        f'👤 От: {author_name} (<code>{author_uid}</code>)\n'
        f'🗂️ Тема: {topic_name}\n\n'
        f'<b>Текст:</b>\n{escape_html(text)}'
    )

    for mod_uid in mod_uids:
        try:
            bot.send_message(mod_uid, caption, parse_mode='HTML', reply_markup=mod_actions_kb(post_id))
        except Exception as e:
            print(f'Не отправить {mod_uid}: {e}')


def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ============================================================
# МОДЕРАЦИЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🛡️ Модерация')
def cmd_mod(m):
    uid = m.from_user.id
    if not is_mod(uid):
        return bot.send_message(m.chat.id, '❌ Нет доступа')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if is_admin(uid) and not get_mod_topics(uid):
        c.execute('''SELECT id, uid, name, topic, text, created FROM posts 
                     WHERE status='pending' ORDER BY id ASC LIMIT 10''')
    else:
        topics = get_mod_topics(uid)
        placeholders = ','.join('?' * len(topics))
        c.execute(f'''SELECT id, uid, name, topic, text, created FROM posts 
                      WHERE status='pending' AND topic IN ({placeholders}) 
                      ORDER BY id ASC LIMIT 10''', topics)
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.send_message(m.chat.id, '📭 Очередь пуста', reply_markup=main_kb(uid))
        return

    for r in rows:
        post_id, author_uid, name, topic, text, created = r
        topic_name = TOPICS[topic]['name']
        caption = (
            f'📬 <b>Пост #{post_id}</b>\n\n'
            f'👤 От: {name} (<code>{author_uid}</code>)\n'
            f'🗂️ Тема: {topic_name}\n\n'
            f'<b>Текст:</b>\n{escape_html(text)}'
        )
        bot.send_message(m.chat.id, caption, parse_mode='HTML', reply_markup=mod_actions_kb(post_id))


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_approve_'))
def cb_approve(c):
    uid = c.from_user.id
    post_id = int(c.data.replace('mod_approve_', ''))
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid, name, topic, text FROM posts WHERE id=?', (post_id,))
    row = c2.fetchone()
    if not row:
        conn.close()
        return bot.answer_callback_query(c.id, 'Пост не найден')
    author_uid, author_name, topic, text = row

    # Проверка темы
    if not is_admin(uid) and topic not in get_mod_topics(uid):
        conn.close()
        return bot.answer_callback_query(c.id, 'Не твоя тема', show_alert=True)

    c2.execute('UPDATE posts SET status=?, mod_uid=?, decided=? WHERE id=?',
               ('approved', uid, int(time.time()), post_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(c.id, '✅ Одобрено')
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f'✅ Пост #{post_id} одобрен')

    # Уведомление автору
    try:
        bot.send_message(author_uid, f'✅ Твой пост одобрен!\n\nТема: {TOPICS[topic]["name"]}')
    except: pass

    # Публикация в канал
    if CHANNEL_ID:
        try:
            bot.send_message(CHANNEL_ID, f'{TOPICS[topic]["emoji"]} <b>{TOPICS[topic]["name"]}</b>\n\n{escape_html(text)}',
                             parse_mode='HTML')
        except Exception as e:
            print(f'Публикация: {e}')


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_reject_'))
def cb_reject(c):
    uid = c.from_user.id
    post_id = int(c.data.replace('mod_reject_', ''))
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid, topic FROM posts WHERE id=?', (post_id,))
    row = c2.fetchone()
    if not row:
        conn.close()
        return bot.answer_callback_query(c.id, 'Не найден')
    author_uid, topic = row
    if not is_admin(uid) and topic not in get_mod_topics(uid):
        conn.close()
        return bot.answer_callback_query(c.id, 'Не твоя тема', show_alert=True)

    c2.execute('UPDATE posts SET status=?, mod_uid=?, decided=? WHERE id=?',
               ('rejected', uid, int(time.time()), post_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(c.id, '❌ Отклонено')
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f'❌ Пост #{post_id} отклонён')

    try:
        bot.send_message(author_uid, f'❌ Твой пост отклонён.')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_comment_'))
def cb_comment(c):
    uid = c.from_user.id
    post_id = int(c.data.replace('mod_comment_', ''))
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)

    user_states[uid] = {'action': 'comment', 'post_id': post_id}
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id, f'💬 Напиши комментарий к посту #{post_id}:')
    bot.register_next_step_handler(msg, handle_comment, uid, post_id)


def handle_comment(m, uid, post_id):
    if not m.text: return
    comment = m.text.strip()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT uid, topic FROM posts WHERE id=?', (post_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return bot.send_message(m.chat.id, '❌ Пост не найден')
    author_uid, topic = row

    c.execute('''UPDATE posts SET status=?, mod_uid=?, mod_comment=?, decided=? WHERE id=?''',
              ('rejected', uid, comment, int(time.time()), post_id))
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, f'✅ Комментарий отправлен, пост #{post_id} отклонён')
    try:
        bot.send_message(author_uid, f'❌ Твой пост отклонён.\n\n💬 Причина: {escape_html(comment)}', parse_mode='HTML')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_ban_'))
def cb_ban_post(c):
    uid = c.from_user.id
    post_id = int(c.data.replace('mod_ban_', ''))
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid FROM posts WHERE id=?', (post_id,))
    row = c2.fetchone()
    conn.close()
    if not row:
        return bot.answer_callback_query(c.id, 'Не найден')
    target_uid = row[0]

    bot.answer_callback_query(c.id)
    bot.send_message(
        c.message.chat.id,
        f'🚫 На сколько забанить <code>{target_uid}</code>?',
        parse_mode='HTML',
        reply_markup=ban_duration_kb('ban', target_uid)
    )


# ============================================================
# BAN / MUTE
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('ban_dur_'))
def cb_ban_dur(c):
    uid = c.from_user.id
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    parts = c.data.split('_')
    target_uid = int(parts[2])
    duration_str = parts[3]
    seconds = parse_time(duration_str)
    if seconds is None:
        return bot.answer_callback_query(c.id, 'Ошибка времени')

    until = 0 if seconds == 0 else int(time.time()) + seconds

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
               (target_uid, until, 'Бан от модератора', uid))
    conn.commit()
    conn.close()

    bot.answer_callback_query(c.id, '✅ Забанен')
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f'🚫 <code>{target_uid}</code> забанен на {time_until(until)}', parse_mode='HTML')
    try:
        bot.send_message(target_uid, f'🚫 Ты забанен на {time_until(until)}')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mute_dur_'))
def cb_mute_dur(c):
    uid = c.from_user.id
    if not is_mod(uid):
        return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    parts = c.data.split('_')
    target_uid = int(parts[2])
    duration_str = parts[3]
    seconds = parse_time(duration_str)
    if seconds is None:
        return bot.answer_callback_query(c.id, 'Ошибка времени')
    until = 0 if seconds == 0 else int(time.time()) + seconds

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
               (target_uid, until, 'Мут', uid))
    conn.commit()
    conn.close()

    bot.answer_callback_query(c.id, '✅ Замучен')
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, f'🔇 <code>{target_uid}</code> замучен на {time_until(until)}', parse_mode='HTML')
    try:
        bot.send_message(target_uid, f'🔇 Ты замучен на {time_until(until)}')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cb_cancel(c):
    bot.answer_callback_query(c.id, 'Отменено')
    try:
        bot.delete_message(c.message.chat.id, c.message.message_id)
    except: pass


# ============================================================
# МОИ ПОСТЫ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📋 Мои посты')
def cmd_my_posts(m):
    uid = m.from_user.id
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''SELECT id, topic, text, status, mod_comment, created FROM posts 
                 WHERE uid=? ORDER BY id DESC LIMIT 20''', (uid,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return bot.send_message(m.chat.id, '📭 У тебя пока нет постов', reply_markup=main_kb(uid))

    text = '📋 <b>Твои посты</b>\n\n'
    for r in rows:
        post_id, topic, txt, status, comment, created = r
        icon = '⏳' if status == 'pending' else '✅' if status == 'approved' else '❌'
        text += f'{icon} <b>#{post_id}</b> · {TOPICS.get(topic, {}).get("name", "?")}\n'
        text += f'   {escape_html(txt[:50])}...\n'
        if comment:
            text += f'   💬 {escape_html(comment)}\n'
        text += '\n'
    bot.send_message(m.chat.id, text[:4000], parse_mode='HTML', reply_markup=main_kb(uid))


# ============================================================
# СТАТИСТИКА
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📊 Статистика')
def cmd_stats(m):
    uid = m.from_user.id
    if not is_mod(uid):
        return bot.send_message(m.chat.id, '❌ Нет доступа')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM posts WHERE mod_uid=? AND status="approved"', (uid,))
    approved = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM posts WHERE mod_uid=? AND status="rejected"', (uid,))
    rejected = c.fetchone()[0]
    if is_admin(uid) and not get_mod_topics(uid):
        c.execute('SELECT COUNT(*) FROM posts WHERE status="pending"')
    else:
        topics = get_mod_topics(uid)
        placeholders = ','.join('?' * len(topics))
        c.execute(f'SELECT COUNT(*) FROM posts WHERE status="pending" AND topic IN ({placeholders})', topics)
    pending = c.fetchone()[0]
    conn.close()

    text = (
        f'📊 <b>Твоя статистика</b>\n\n'
        f'✅ Одобрено: <b>{approved}</b>\n'
        f'❌ Отклонено: <b>{rejected}</b>\n'
        f'⏳ В очереди: <b>{pending}</b>\n'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb(uid))


# ============================================================
# АДМИН-ПАНЕЛЬ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '👑 Админ-панель')
def cmd_admin(m):
    uid = m.from_user.id
    if not is_admin(uid):
        return bot.send_message(m.chat.id, '❌ Нет доступа')
    bot.send_message(m.chat.id, '👑 <b>Админ-панель</b>', parse_mode='HTML', reply_markup=admin_kb())


@bot.callback_query_handler(func=lambda c: c.data == 'admin_addmod')
def cb_addmod(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, 'Нет доступа')
    user_states[c.from_user.id] = {'action': 'addmod_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '👤 Отправь <b>UID</b> пользователя:', parse_mode='HTML')


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('action') == 'addmod_uid')
def handle_addmod_uid(m):
    uid = m.from_user.id
    if not is_admin(uid): return
    try:
        target_uid = int(m.text.strip())
    except:
        return bot.send_message(m.chat.id, '❌ Некорректный UID')
    user_states[uid] = {'action': 'addmod_topic', 'target_uid': target_uid}
    bot.send_message(m.chat.id, f'🗂️ Выбери тему для <code>{target_uid}</code>:',
                     parse_mode='HTML', reply_markup=mods_topics_kb())


@bot.callback_query_handler(func=lambda c: c.data.startswith('addmod_topic_'))
def cb_addmod_topic(c):
    uid = c.from_user.id
    if not is_admin(uid): return
    state = user_states.get(uid, {})
    if state.get('action') != 'addmod_topic': return
    topic = c.data.replace('addmod_topic_', '')
    target_uid = state['target_uid']

    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('INSERT OR IGNORE INTO mods (uid, topic) VALUES (?, ?)', (target_uid, topic))
    conn.commit()
    conn.close()

    user_states.pop(uid, None)
    bot.answer_callback_query(c.id, '✅ Добавлен')
    bot.edit_message_text(f'✅ <code>{target_uid}</code> — модератор темы {TOPICS[topic]["name"]}',
                          c.message.chat.id, c.message.message_id, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'admin_listmods')
def cb_listmods(c):
    if not is_admin(c.from_user.id): return
    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid, topic FROM mods')
    rows = c2.fetchall()
    conn.close()
    if not rows:
        return bot.answer_callback_query(c.id, 'Пусто', show_alert=True)
    text = '📋 <b>Модераторы</b>\n\n'
    for r in rows:
        text += f'👤 <code>{r[0]}</code> — {TOPICS.get(r[1], {}).get("name", "?")}\n'
    bot.send_message(c.message.chat.id, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'admin_bans')
def cb_bans(c):
    if not is_admin(c.from_user.id): return
    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid, until FROM bans')
    rows = c2.fetchall()
    conn.close()
    if not rows:
        return bot.answer_callback_query(c.id, 'Пусто', show_alert=True)
    text = '🚫 <b>Баны</b>\n\n'
    for r in rows:
        text += f'<code>{r[0]}</code> — {time_until(r[1])}\n'
    bot.send_message(c.message.chat.id, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'admin_mutes')
def cb_mutes(c):
    if not is_admin(c.from_user.id): return
    conn = sqlite3.connect(DB)
    c2 = conn.cursor()
    c2.execute('SELECT uid, until FROM mutes')
    rows = c2.fetchall()
    conn.close()
    if not rows:
        return bot.answer_callback_query(c.id, 'Пусто', show_alert=True)
    text = '🔇 <b>Муты</b>\n\n'
    for r in rows:
        text += f'<code>{r[0]}</code> — {time_until(r[1])}\n'
    bot.send_message(c.message.chat.id, text, parse_mode='HTML')


# ============================================================
# КОМАНДЫ ДЛЯ БЫСТРОГО БАНА / МУТА
# ============================================================
@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    if not is_mod(m.from_user.id):
        return bot.send_message(m.chat.id, '❌ Нет доступа')
    parts = m.text.split()
    if len(parts) < 3:
        return bot.send_message(m.chat.id, 'Использование: /ban <uid> <время>\n\nВремя: 5m, 1h, 1d, forever')
    try:
        target_uid = int(parts[1])
    except:
        return bot.send_message(m.chat.id, '❌ Некорректный UID')
    seconds = parse_time(parts[2])
    if seconds is None:
        return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if seconds == 0 else int(time.time()) + seconds
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target_uid, until, 'Бан', m.from_user.id))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, f'🚫 <code>{target_uid}</code> забанен на {time_until(until)}', parse_mode='HTML')


@bot.message_handler(commands=['mute'])
def cmd_mute(m):
    if not is_mod(m.from_user.id):
        return bot.send_message(m.chat.id, '❌ Нет доступа')
    parts = m.text.split()
    if len(parts) < 3:
        return bot.send_message(m.chat.id, 'Использование: /mute <uid> <время>')
    try:
        target_uid = int(parts[1])
    except:
        return bot.send_message(m.chat.id, '❌ Некорректный UID')
    seconds = parse_time(parts[2])
    if seconds is None:
        return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if seconds == 0 else int(time.time()) + seconds
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target_uid, until, 'Мут', m.from_user.id))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, f'🔇 <code>{target_uid}</code> замучен на {time_until(until)}', parse_mode='HTML')


@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    if not is_mod(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 2: return
    try: target_uid = int(parts[1])
    except: return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (target_uid,))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target_uid}</code> разбанен', parse_mode='HTML')


@bot.message_handler(commands=['unmute'])
def cmd_unmute(m):
    if not is_mod(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 2: return
    try: target_uid = int(parts[1])
    except: return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (target_uid,))
    conn.commit()
    conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target_uid}</code> размучен', parse_mode='HTML')


@bot.message_handler(commands=['myid'])
def cmd_myid(m):
    bot.send_message(m.chat.id, f'👤 Твой ID: <code>{m.from_user.id}</code>', parse_mode='HTML')


if __name__ == '__main__':
    print('Suggest bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
