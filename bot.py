import telebot
import sqlite3
import time
import re
from telebot import types

TOKEN = '8471116013:AAE7-_Fhkoyjqpl9lJ_CPQdwgM-nZTndhx4'
ADMIN_IDS = [8907438590]  # [123456789] — сюда свой ID
CHANNEL_ID = None  # ID канала, если нужно

# ============================================================
# ВАРНЫ: настройки автонаказаний
# ============================================================
WARN_MUTE = 3          # 3 варна = автомут
WARN_BAN = 5           # 5 варнов = автобан
WARN_MUTE_TIME = 3600  # мут на 1 час
WARN_BAN_TIME = 86400  # бан на 1 день

TOPICS = {
    'news':     {'name': '📰 Новости'},
    'meme':     {'name': '😂 Мемы'},
    'question': {'name': '❓ Вопросы'},
    'ads':      {'name': '📢 Реклама'},
    'art':      {'name': '🎨 Арт'},
    'idea':     {'name': '💡 Идеи'},
}

bot = telebot.TeleBot(TOKEN)
DB = 'suggest.db'


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
        uid INTEGER, topic TEXT, PRIMARY KEY (uid, topic)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        uid INTEGER PRIMARY KEY, until INTEGER, reason TEXT, by_uid INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mutes (
        uid INTEGER PRIMARY KEY, until INTEGER, reason TEXT, by_uid INTEGER
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

def is_admin(uid): return uid in ADMIN_IDS
def is_mod(uid): return bool(get_mod_topics(uid)) or is_admin(uid)

def get_warns(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (uid,))
    n = c.fetchone()[0]
    conn.close()
    return n

def is_banned(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT until FROM bans WHERE uid=?', (uid,))
    row = c.fetchone()
    conn.close()
    if not row: return False
    if row[0] == 0 or row[0] > int(time.time()): return True
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (uid,))
    conn.commit(); conn.close()
    return False

def is_muted(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
    row = c.fetchone()
    conn.close()
    if not row: return False
    if row[0] == 0 or row[0] > int(time.time()): return True
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (uid,))
    conn.commit(); conn.close()
    return False

def get_ban_until(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT until FROM bans WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
    return row[0] if row else None

def get_mute_until(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
    return row[0] if row else None

def parse_time(text):
    text = text.strip().lower()
    if text in ('forever', 'навсегда', '0', 'inf'): return 0
    m = re.match(r'^(\d+)\s*([smhd]?)$', text)
    if not m: return None
    num = int(m.group(1))
    mult = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return num * mult.get(m.group(2) or 'm', 60)

def fmt_time(seconds):
    if seconds == 0: return 'навсегда'
    if seconds < 60: return f'{seconds} сек'
    if seconds < 3600: return f'{seconds // 60} мин'
    if seconds < 86400: return f'{seconds // 3600} ч'
    return f'{seconds // 86400} д'

def time_until(until_ts):
    if until_ts is None: return '—'
    if until_ts == 0: return 'навсегда'
    left = until_ts - int(time.time())
    if left <= 0: return 'истёк'
    return fmt_time(left)

def escape_html(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ============================================================
# КЛАВИАТУРЫ (с цветными кнопками style)
# ============================================================
def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add('📝 Предложить', '📋 Мои посты')
    if is_mod(uid):
        kb.add('🟢 Модерация', '🟡 Статистика')
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

def mod_actions_kb(post_id, author_uid):
    """Кнопки модерации с ЦВЕТАМИ"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Одобрить', callback_data=f'mod_ok_{post_id}', style='success'),
        types.InlineKeyboardButton('❌ Отклонить', callback_data=f'mod_no_{post_id}', style='danger'),
    )
    kb.add(
        types.InlineKeyboardButton('🟡 Варн', callback_data=f'warn_{author_uid}'),
        types.InlineKeyboardButton('🟠 Мут', callback_data=f'menu_mute_{author_uid}'),
    )
    kb.add(
        types.InlineKeyboardButton('🔴 Бан', callback_data=f'menu_ban_{author_uid}', style='danger'),
        types.InlineKeyboardButton('💬 Комментарий', callback_data=f'mod_cmt_{post_id}'),
    )
    return kb

def ban_duration_kb(action, uid):
    kb = types.InlineKeyboardMarkup(row_width=3)
    times = [
        ('1м', '1m'), ('5м', '5m'), ('30м', '30m'),
        ('1ч', '1h'), ('6ч', '6h'), ('1д', '1d'),
        ('7д', '7d'), ('30д', '30d'), ('🔴∞', 'forever'),
    ]
    btns = [types.InlineKeyboardButton(label, callback_data=f'{action}_dur_{uid}_{val}') for label, val in times]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('❌ Отмена', callback_data='cancel', style='danger'))
    return kb

def admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('👤 Добавить модератора', callback_data='admin_addmod'),
        types.InlineKeyboardButton('📋 Модераторы', callback_data='admin_listmods'),
        types.InlineKeyboardButton('🔴 Баны', callback_data='admin_bans', style='danger'),
        types.InlineKeyboardButton('🟠 Муты', callback_data='admin_mutes'),
        types.InlineKeyboardButton('🟡 Варны', callback_data='admin_warns'),
    )
    return kb

def mods_topics_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(t['name'], callback_data=f'addmod_topic_{k}')
            for k, t in TOPICS.items()]
    kb.add(*btns)
    return kb


# ============================================================
# START
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🔴 Ты забанен.\nОсталось: {time_until(get_ban_until(uid))}')
    text = (
        '👋 <b>Предложка</b>\n\n'
        '📝 <b>Предложить</b> — отправить пост\n'
        '📋 <b>Мои посты</b> — статус заявок\n'
    )
    if is_mod(uid):
        text += '\n🟢 <b>Модерация</b> — очередь\n🟡 <b>Статистика</b>\n'
    if is_admin(uid):
        text += '\n👑 <b>Админ-панель</b>\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb(uid))


@bot.message_handler(commands=['myid'])
def cmd_myid(m):
    warns = get_warns(m.from_user.id)
    text = f'👤 ID: <code>{m.from_user.id}</code>\n'
    text += f'🟡 Варнов: <b>{warns}</b>\n'
    if is_banned(m.from_user.id):
        text += f'🔴 Бан: {time_until(get_ban_until(m.from_user.id))}\n'
    if is_muted(m.from_user.id):
        text += f'🟠 Мут: {time_until(get_mute_until(m.from_user.id))}\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# ПРЕДЛОЖКА
# ============================================================
user_states = {}

@bot.message_handler(func=lambda m: m.text in ('📝 Предложить', '📝 Предложить пост'))
def cmd_suggest(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🔴 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')
    if is_muted(uid):
        return bot.send_message(m.chat.id, f'🟠 Ты в муте. Осталось: {time_until(get_mute_until(uid))}')
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
        f'✍️ Тема: {TOPICS[topic]["name"]}\n\nНапиши текст поста (от 5 символов).',
        c.message.chat.id, c.message.message_id
    )
    bot.register_next_step_handler_by_chat_id(c.message.chat.id, handle_post_text, uid, topic)


def handle_post_text(m, uid, topic):
    if m.from_user.id != uid: return
    if not m.text: return
    text = m.text.strip()
    if len(text) < 5:
        return bot.send_message(m.chat.id, '❌ Слишком коротко.')
    if len(text) > 2000: text = text[:2000]

    name = m.from_user.first_name or 'Аноним'
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO posts (uid, name, topic, text, created) VALUES (?, ?, ?, ?, ?)',
              (uid, name, topic, text, int(time.time())))
    post_id = c.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(m.chat.id, '🟢 Пост отправлен на модерацию!', reply_markup=main_kb(uid))
    user_states.pop(uid, None)
    send_to_mods(post_id, uid, name, topic, text)


def send_to_mods(post_id, author_uid, author_name, topic, text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT uid FROM mods WHERE topic=?', (topic,))
    mod_uids = [r[0] for r in c.fetchall()]
    conn.close()
    mod_uids.extend(ADMIN_IDS)
    mod_uids = list(set(mod_uids))

    caption = (
        f'📬 <b>Новый пост #{post_id}</b>\n\n'
        f'👤 От: {escape_html(author_name)} (<code>{author_uid}</code>)\n'
        f'🗂️ Тема: {TOPICS[topic]["name"]}\n\n'
        f'<b>Текст:</b>\n{escape_html(text)}'
    )
    for mod_uid in mod_uids:
        try:
            bot.send_message(mod_uid, caption, parse_mode='HTML',
                             reply_markup=mod_actions_kb(post_id, author_uid))
        except Exception as e:
            print(f'err {mod_uid}:', e)


# ============================================================
# МОДЕРАЦИЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text in ('🟢 Модерация', '🛡️ Модерация'))
def cmd_mod(m):
    uid = m.from_user.id
    if not is_mod(uid):
        return bot.send_message(m.chat.id, '🔴 Нет доступа')

    conn = sqlite3.connect(DB); c = conn.cursor()
    if is_admin(uid) and not get_mod_topics(uid):
        c.execute('''SELECT id, uid, name, topic, text FROM posts 
                     WHERE status='pending' ORDER BY id ASC LIMIT 10''')
    else:
        topics = get_mod_topics(uid)
        placeholders = ','.join('?' * len(topics))
        c.execute(f'''SELECT id, uid, name, topic, text FROM posts 
                      WHERE status='pending' AND topic IN ({placeholders}) 
                      ORDER BY id ASC LIMIT 10''', topics)
    rows = c.fetchall(); conn.close()

    if not rows:
        return bot.send_message(m.chat.id, '📭 Очередь пуста', reply_markup=main_kb(uid))

    for r in rows:
        post_id, author_uid, name, topic, text = r
        caption = (
            f'📬 <b>Пост #{post_id}</b>\n\n'
            f'👤 От: {escape_html(name)} (<code>{author_uid}</code>)\n'
            f'🗂️ Тема: {TOPICS[topic]["name"]}\n'
            f'🟡 Варнов у автора: {get_warns(author_uid)}\n\n'
            f'<b>Текст:</b>\n{escape_html(text)}'
        )
        bot.send_message(m.chat.id, caption, parse_mode='HTML',
                         reply_markup=mod_actions_kb(post_id, author_uid))


# ============================================================
# ДЕЙСТВИЯ МОДЕРАТОРА
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_ok_'))
def cb_ok(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    post_id = int(c.data.replace('mod_ok_', ''))

    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT uid, topic, text FROM posts WHERE id=?', (post_id,))
    row = c2.fetchone()
    if not row:
        conn.close(); return bot.answer_callback_query(c.id, 'Не найден')
    author_uid, topic, text = row
    if not is_admin(uid) and topic not in get_mod_topics(uid):
        conn.close(); return bot.answer_callback_query(c.id, 'Не твоя тема', show_alert=True)

    c2.execute('UPDATE posts SET status=?, mod_uid=?, decided=? WHERE id=?',
               ('approved', uid, int(time.time()), post_id))
    conn.commit(); conn.close()

    bot.answer_callback_query(c.id, '✅ Одобрено')
    try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    except: pass
    bot.send_message(c.message.chat.id, f'✅ Пост #{post_id} одобрен')
    try: bot.send_message(author_uid, '✅ Твой пост одобрен!')
    except: pass

    if CHANNEL_ID:
        try:
            bot.send_message(CHANNEL_ID, f'{TOPICS[topic]["name"]}\n\n{escape_html(text)}', parse_mode='HTML')
        except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_no_'))
def cb_no(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    post_id = int(c.data.replace('mod_no_', ''))

    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT uid, topic FROM posts WHERE id=?', (post_id,))
    row = c2.fetchone()
    if not row:
        conn.close(); return bot.answer_callback_query(c.id, 'Не найден')
    author_uid, topic = row
    if not is_admin(uid) and topic not in get_mod_topics(uid):
        conn.close(); return bot.answer_callback_query(c.id, 'Не твоя тема', show_alert=True)

    c2.execute('UPDATE posts SET status=?, mod_uid=?, decided=? WHERE id=?',
               ('rejected', uid, int(time.time()), post_id))
    conn.commit(); conn.close()

    bot.answer_callback_query(c.id, '❌ Отклонено')
    try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    except: pass
    bot.send_message(c.message.chat.id, f'❌ Пост #{post_id} отклонён')
    try: bot.send_message(author_uid, '❌ Твой пост отклонён.')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mod_cmt_'))
def cb_cmt(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    post_id = int(c.data.replace('mod_cmt_', ''))
    user_states[uid] = {'action': 'comment', 'post_id': post_id}
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.message.chat.id, f'💬 Комментарий к посту #{post_id}:')
    bot.register_next_step_handler(msg, handle_comment, uid, post_id)


def handle_comment(m, uid, post_id):
    if not m.text: return
    comment = m.text.strip()
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT uid FROM posts WHERE id=?', (post_id,))
    row = c.fetchone()
    if not row:
        conn.close(); return bot.send_message(m.chat.id, '🔴 Пост не найден')
    author_uid = row[0]
    c.execute('UPDATE posts SET status=?, mod_uid=?, mod_comment=?, decided=? WHERE id=?',
              ('rejected', uid, comment, int(time.time()), post_id))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, '🟢 Комментарий отправлен')
    try: bot.send_message(author_uid, f'🔴 Пост отклонён.\n\n💬 {escape_html(comment)}', parse_mode='HTML')
    except: pass


# ============================================================
# ВАРН
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('warn_') and not c.data.startswith('unwarn_'))
def cb_warn(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    target_uid = int(c.data.replace('warn_', ''))

    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('INSERT INTO warns (uid, reason, by_uid, time) VALUES (?, ?, ?, ?)',
               (target_uid, 'Нарушение', uid, int(time.time())))
    conn.commit()
    c2.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (target_uid,))
    warns = c2.fetchone()[0]
    conn.close()

    bot.answer_callback_query(c.id, f'🟡 Варн выдан ({warns}/5)')
    auto_text = ''
    if warns >= WARN_BAN:
        until = int(time.time()) + WARN_BAN_TIME
        conn = sqlite3.connect(DB); c2 = conn.cursor()
        c2.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                   (target_uid, until, f'{WARN_BAN} варнов', uid))
        conn.commit(); conn.close()
        auto_text = f'\n🔴 Автобан на {fmt_time(WARN_BAN_TIME)}'
    elif warns >= WARN_MUTE:
        until = int(time.time()) + WARN_MUTE_TIME
        conn = sqlite3.connect(DB); c2 = conn.cursor()
        c2.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                   (target_uid, until, f'{WARN_MUTE} варнов', uid))
        conn.commit(); conn.close()
        auto_text = f'\n🟠 Автомут на {fmt_time(WARN_MUTE_TIME)}'

    bot.send_message(c.message.chat.id,
                     f'🟡 <code>{target_uid}</code> получил варн ({warns}/5){auto_text}',
                     parse_mode='HTML')
    try: bot.send_message(target_uid, f'🟡 Ты получил варн ({warns}/5){auto_text}')
    except: pass


# ============================================================
# BAN / MUTE
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_ban_'))
def cb_menu_ban(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    target = int(c.data.replace('menu_ban_', ''))
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,
                     f'🔴 На сколько забанить <code>{target}</code>?',
                     parse_mode='HTML', reply_markup=ban_duration_kb('ban', target))


@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_mute_'))
def cb_menu_mute(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    target = int(c.data.replace('menu_mute_', ''))
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,
                     f'🟠 На сколько замутить <code>{target}</code>?',
                     parse_mode='HTML', reply_markup=ban_duration_kb('mute', target))


@bot.callback_query_handler(func=lambda c: c.data.startswith('ban_dur_'))
def cb_ban_dur(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    parts = c.data.split('_')
    target = int(parts[2])
    seconds = parse_time(parts[3])
    if seconds is None: return bot.answer_callback_query(c.id, 'Ошибка')
    until = 0 if seconds == 0 else int(time.time()) + seconds

    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
               (target, until, 'Бан', uid))
    conn.commit(); conn.close()

    bot.answer_callback_query(c.id, '🔴 Забанен')
    try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    except: pass
    bot.send_message(c.message.chat.id, f'🔴 <code>{target}</code> забанен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🔴 Ты забанен на {time_until(until)}')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('mute_dur_'))
def cb_mute_dur(c):
    uid = c.from_user.id
    if not is_mod(uid): return bot.answer_callback_query(c.id, 'Нет доступа', show_alert=True)
    parts = c.data.split('_')
    target = int(parts[2])
    seconds = parse_time(parts[3])
    if seconds is None: return bot.answer_callback_query(c.id, 'Ошибка')
    until = 0 if seconds == 0 else int(time.time()) + seconds

    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
               (target, until, 'Мут', uid))
    conn.commit(); conn.close()

    bot.answer_callback_query(c.id, '🟠 Замучен')
    try: bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    except: pass
    bot.send_message(c.message.chat.id, f'🟠 <code>{target}</code> замучен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🟠 Ты замучен на {time_until(until)}')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cb_cancel(c):
    bot.answer_callback_query(c.id, 'Отменено')
    try: bot.delete_message(c.message.chat.id, c.message.message_id)
    except: pass


# ============================================================
# КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    if not is_mod(m.from_user.id):
        return bot.send_message(m.chat.id, '🔴 Нет доступа')
    p = m.text.split()
    if len(p) < 3:
        return bot.send_message(m.chat.id, 'Использование: <code>/ban uid время</code>\nВремя: 5m, 1h, 1d, forever', parse_mode='HTML')
    try: target = int(p[1])
    except: return bot.send_message(m.chat.id, '🔴 Некорректный UID')
    sec = parse_time(p[2])
    if sec is None: return bot.send_message(m.chat.id, '🔴 Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Бан', m.from_user.id))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'🔴 <code>{target}</code> забанен на {time_until(until)}', parse_mode='HTML')


@bot.message_handler(commands=['mute'])
def cmd_mute(m):
    if not is_mod(m.from_user.id):
        return bot.send_message(m.chat.id, '🔴 Нет доступа')
    p = m.text.split()
    if len(p) < 3:
        return bot.send_message(m.chat.id, 'Использование: <code>/mute uid время</code>', parse_mode='HTML')
    try: target = int(p[1])
    except: return bot.send_message(m.chat.id, '🔴 Некорректный UID')
    sec = parse_time(p[2])
    if sec is None: return bot.send_message(m.chat.id, '🔴 Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Мут', m.from_user.id))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'🟠 <code>{target}</code> замучен на {time_until(until)}', parse_mode='HTML')


@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    if not is_mod(m.from_user.id): return
    p = m.text.split()
    if len(p) < 2: return
    try: target = int(p[1])
    except: return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'🟢 <code>{target}</code> разбанен', parse_mode='HTML')


@bot.message_handler(commands=['unmute'])
def cmd_unmute(m):
    if not is_mod(m.from_user.id): return
    p = m.text.split()
    if len(p) < 2: return
    try: target = int(p[1])
    except: return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'🟢 <code>{target}</code> размучен', parse_mode='HTML')


if __name__ == '__main__':
    print('Suggest bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
