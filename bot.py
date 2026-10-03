import telebot
import sqlite3
import time
import re
from telebot import types

TOKEN = '8641977356:AAEithSvkupfKQAX-R8Dg10Wk7I_UuBlYFs'
OWNER_IDS = [6430796415,8907438590]  # ← два ID админов
CHANNEL_ID = 4337299468 # ID канала, если нужно (например: -1001234567890)

WARN_MUTE = 3
WARN_BAN = 5
WARN_MUTE_TIME = 3600
WARN_BAN_TIME = 86400

ROLES = {
    0: {'name': 'Обычный',      'icon': '👤', 'warn': False, 'mute': False, 'ban': False, 'post': False, 'manage': False},
    1: {'name': 'Младший мод',  'icon': '🛡️', 'warn': True,  'mute': True,  'ban': False, 'post': False, 'manage': False},
    2: {'name': 'Старший мод',  'icon': '⚔️', 'warn': True,  'mute': True,  'ban': True,  'post': False, 'manage': False},
    3: {'name': 'Постер',       'icon': '📝', 'warn': False, 'mute': False, 'ban': False, 'post': True,  'manage': False},
    4: {'name': 'Админ',        'icon': '👑', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
    5: {'name': 'Владелец',     'icon': '💎', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
}

bot = telebot.TeleBot(TOKEN)
DB = 'roles.db'


# ============================================================
# БД
# ============================================================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS roles (
        uid INTEGER PRIMARY KEY, role INTEGER DEFAULT 0
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
    c.execute('''CREATE TABLE IF NOT EXISTS personal_access (
        uid INTEGER, command TEXT, PRIMARY KEY (uid, command)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    conn.commit()
    conn.close()

init_db()


def get_setting(key, default=None):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = c.fetchone(); conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit(); conn.close()


# ============================================================
# РОЛИ
# ============================================================
def get_role(uid):
    if uid in OWNER_IDS: return 5
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT role FROM roles WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def set_role(uid, role):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO roles (uid, role) VALUES (?, ?)', (uid, role))
    conn.commit(); conn.close()

def can(uid, action):
    if get_role(uid) == 5: return True
    return ROLES.get(get_role(uid), {}).get(action, False)


# ============================================================
# НАКАЗАНИЯ
# ============================================================
def get_warns(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (uid,))
    n = c.fetchone()[0]; conn.close()
    return n

def is_banned(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT until FROM bans WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
    if not row: return False
    if row[0] == 0 or row[0] > int(time.time()): return True
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (uid,))
    conn.commit(); conn.close()
    return False

def is_muted(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
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


# ============================================================
# ВРЕМЯ
# ============================================================
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


def resolve_target(m, args):
    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user.id
    if args:
        try: return int(args[0])
        except: return None
    return None


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add('Написать админу')
    if can(uid, 'post'):
        kb.add('Опубликовать')
    if can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban'):
        kb.add('Модерация')
    if can(uid, 'manage'):
        kb.add('Роли', 'Глушилка', 'Статистика')
    return kb


def duration_kb(action):
    kb = types.InlineKeyboardMarkup(row_width=3)
    times = [('1м','1m'),('5м','5m'),('30м','30m'),('1ч','1h'),('6ч','6h'),('1д','1d'),('7д','7d'),('30д','30d'),('Навсегда','forever')]
    btns = [types.InlineKeyboardButton(l, callback_data=f'{action}_dur_{v}') for l, v in times]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('Отмена', callback_data='cancel', style='danger'))
    return kb


# ============================================================
# START
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🚫 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')
    name = m.from_user.first_name or 'друг'
    role = get_role(uid)
    role_name = ROLES.get(role, {}).get('name', 'Обычный')
    icon = ROLES.get(role, {}).get('icon', '👤')
    text = (
        f'👋 <b>Привет, {escape_html(name)}!</b>\n\n'
        f'Твоя роль: {icon} <b>{role_name}</b>\n\n'
        f'<b>Что можно:</b>\n'
        f'• 📩 <b>Написать админу</b> — задать вопрос\n'
    )
    if can(uid, 'post'):
        text += '• 📝 <b>Опубликовать</b> — пост в канал\n'
    if can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban'):
        text += '• 🛡️ <b>Модерация</b> — мут, бан, варн\n'
    if can(uid, 'manage'):
        text += '• 🎭 <b>Роли</b> — управление\n'
        text += '• 🔇 <b>Глушилка</b> — блок ботов\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb(uid))


@bot.message_handler(commands=['myid'])
def cmd_myid(m):
    uid = m.from_user.id
    role = get_role(uid)
    text = f'👤 ID: <code>{uid}</code>\n'
    text += f'{ROLES[role]["icon"]} Роль: <b>{ROLES[role]["name"]}</b>\n'
    text += f'⚠️ Варнов: <b>{get_warns(uid)}</b>\n'
    if is_banned(uid): text += f'🚫 Бан: {time_until(get_ban_until(uid))}\n'
    if is_muted(uid): text += f'🔇 Мут: {time_until(get_mute_until(uid))}\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# СВЯЗЬ С АДМИНОМ
# ============================================================
support_states = {}

@bot.message_handler(func=lambda m: m.text == 'Написать админу')
def cmd_write_admin(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🚫 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')
    support_states[uid] = {'action': 'write_admin'}
    bot.send_message(m.chat.id, '✍️ Напиши сообщение админу.\n\nМожно: текст, фото, видео, голосовое, документ.')


@bot.message_handler(
    func=lambda m: support_states.get(m.from_user.id, {}).get('action') == 'write_admin',
    content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'audio', 'sticker']
)
def handle_write_admin(m):
    uid = m.from_user.id
    if support_states.get(uid, {}).get('action') != 'write_admin':
        return
    support_states.pop(uid, None)
    name = m.from_user.first_name or 'Аноним'
    username = f'@{m.from_user.username}' if m.from_user.username else '—'

    for admin_id in OWNER_IDS:
        try:
            bot.send_message(admin_id,
                f'📩 <b>Сообщение от пользователя</b>\n\n'
                f'👤 {escape_html(name)} ({username})\n'
                f'🆔 <code>{uid}</code>',
                parse_mode='HTML')
            bot.forward_message(admin_id, m.chat.id, m.message_id)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton('💬 Ответить', callback_data=f'reply_to_{uid}'))
            bot.send_message(admin_id, '↓ Ответить:', reply_markup=kb)
        except Exception as e:
            print(f'admin err {admin_id}:', e)

    bot.send_message(m.chat.id, '✅ Сообщение отправлено!', reply_markup=main_kb(uid))


reply_states = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith('reply_to_'))
def cb_reply_to(c):
    if c.from_user.id not in OWNER_IDS:
        return bot.answer_callback_query(c.id, 'Нет прав', show_alert=True)
    target = int(c.data.replace('reply_to_', ''))
    reply_states[c.from_user.id] = {'action': 'reply', 'target': target}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, f'💬 Напиши ответ для <code>{target}</code>:', parse_mode='HTML')


@bot.message_handler(
    func=lambda m: reply_states.get(m.from_user.id, {}).get('action') == 'reply',
    content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'audio']
)
def handle_admin_reply(m):
    uid = m.from_user.id
    if uid not in OWNER_IDS: return
    state = reply_states.get(uid, {})
    if state.get('action') != 'reply': return
    target = state['target']
    reply_states.pop(uid, None)
    try:
        bot.send_message(target, '📬 <b>Ответ от админа:</b>', parse_mode='HTML')
        if m.text: bot.send_message(target, m.text)
        elif m.photo: bot.send_photo(target, m.photo[-1].file_id, caption=m.caption or '')
        elif m.video: bot.send_video(target, m.video.file_id, caption=m.caption or '')
        elif m.voice: bot.send_voice(target, m.voice.file_id)
        elif m.video_note: bot.send_video_note(target, m.video_note.file_id)
        elif m.document: bot.send_document(target, m.document.file_id, caption=m.caption or '')
        elif m.audio: bot.send_audio(target, m.audio.file_id, caption=m.caption or '')
        bot.send_message(uid, '✅ Ответ отправлен!')
    except Exception as e:
        bot.send_message(uid, f'❌ Ошибка: {e}')


# ============================================================
# ГЛУШИЛКА БОТОВ
# ============================================================
@bot.message_handler(func=lambda m: m.text == 'Глушилка')
def cmd_gag_menu(m):
    if not can(m.from_user.id, 'manage'): return
    enabled = get_setting('gag_bots', '0') == '1'
    status = '🔴 ВКЛЮЧЕНА' if enabled else '🟢 ВЫКЛЮЧЕНА'
    kb = types.InlineKeyboardMarkup(row_width=1)
    if enabled:
        kb.add(types.InlineKeyboardButton('🟢 Выключить', callback_data='gag_off', style='success'))
    else:
        kb.add(types.InlineKeyboardButton('🔴 Включить', callback_data='gag_on', style='danger'))
    bot.send_message(m.chat.id,
        f'🔇 <b>Глушилка ботов</b>\n\nСтатус: <b>{status}</b>\n\n'
        f'Когда включена — бот удаляет все сообщения от других ботов в группах.',
        parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'gag_on')
def cb_gag_on(c):
    if not can(c.from_user.id, 'manage'):
        return bot.answer_callback_query(c.id, 'Нет прав', show_alert=True)
    set_setting('gag_bots', '1')
    bot.answer_callback_query(c.id, '🔴 Включено')
    bot.edit_message_text('🔇 <b>Глушилка</b>\n\nСтатус: <b>🔴 ВКЛЮЧЕНА</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'gag_off')
def cb_gag_off(c):
    if not can(c.from_user.id, 'manage'):
        return bot.answer_callback_query(c.id, 'Нет прав', show_alert=True)
    set_setting('gag_bots', '0')
    bot.answer_callback_query(c.id, '🟢 Выключено')
    bot.edit_message_text('🔇 <b>Глушилка</b>\n\nСтатус: <b>🟢 ВЫКЛЮЧЕНА</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML')


@bot.message_handler(commands=['gag'])
def cmd_gag_on(m):
    if not can(m.from_user.id, 'manage'): return
    set_setting('gag_bots', '1')
    bot.send_message(m.chat.id, '🔇 Глушилка <b>включена</b>', parse_mode='HTML')


@bot.message_handler(commands=['ungag'])
def cmd_gag_off(m):
    if not can(m.from_user.id, 'manage'): return
    set_setting('gag_bots', '0')
    bot.send_message(m.chat.id, '🟢 Глушилка <b>выключена</b>', parse_mode='HTML')


@bot.message_handler(
    func=lambda m: get_setting('gag_bots', '0') == '1'
                   and m.from_user is not None
                   and m.from_user.is_bot
                   and m.from_user.id != bot.get_me().id,
    content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'audio', 'sticker', 'animation']
)
def gag_bots(m):
    try: bot.delete_message(m.chat.id, m.message_id)
    except Exception as e: print('gag err:', e)


# ============================================================
# МОДЕРАЦИЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text == 'Модерация')
def cmd_mod(m):
    uid = m.from_user.id
    if not (can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban')): return
    text = (
        '🛡️ <b>Модерация</b>\n\n'
        '<code>/warn uid</code> — варн\n'
        '<code>/mute uid 1h</code> — мут\n'
        '<code>/ban uid 1d</code> — бан\n'
        '<code>/unban uid</code>\n'
        '<code>/unmute uid</code>\n\n'
        'Или ответь на сообщение и напиши команду без uid.'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['warn'])
def cmd_warn(m):
    uid = m.from_user.id
    if not can(uid, 'warn'): return bot.send_message(m.chat.id, '❌ Нет прав')
    args = m.text.split()[1:]
    target = resolve_target(m, args)
    if not target: return bot.send_message(m.chat.id, 'Ответь на сообщение или укажи uid')
    if target == uid: return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid): return bot.send_message(m.chat.id, '❌ Нельзя равному/выше')

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT INTO warns (uid, reason, by_uid, time) VALUES (?, ?, ?, ?)',
              (target, 'Нарушение', uid, int(time.time())))
    conn.commit()
    c.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (target,))
    warns = c.fetchone()[0]; conn.close()

    bot.send_message(m.chat.id, f'⚠️ <code>{target}</code> получил варн ({warns}/5)', parse_mode='HTML')
    auto = ''
    if warns >= WARN_BAN:
        until = int(time.time()) + WARN_BAN_TIME
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                  (target, until, f'{WARN_BAN} варнов', uid))
        conn.commit(); conn.close()
        auto = f'\n🚫 Автобан на {fmt_time(WARN_BAN_TIME)}'
    elif warns >= WARN_MUTE:
        until = int(time.time()) + WARN_MUTE_TIME
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                  (target, until, f'{WARN_MUTE} варнов', uid))
        conn.commit(); conn.close()
        auto = f'\n🔇 Автомут на {fmt_time(WARN_MUTE_TIME)}'
    if auto: bot.send_message(m.chat.id, f'⚡ Автонаказание:{auto}')
    try: bot.send_message(target, f'⚠️ Ты получил варн ({warns}/5){auto}')
    except: pass


@bot.message_handler(commands=['mute'])
def cmd_mute(m):
    uid = m.from_user.id
    if not can(uid, 'mute'): return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target: return bot.send_message(m.chat.id, 'Ответь на сообщение или /mute uid 1h')
    if target == uid: return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid): return bot.send_message(m.chat.id, '❌ Нельзя равному/выше')

    time_str = parts[1] if len(parts) > 1 else '1h'
    sec = parse_time(time_str)
    if sec is None: return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Мут', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, f'🔇 <code>{target}</code> замучен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🔇 Ты замучен на {time_until(until)}')
    except: pass


@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    uid = m.from_user.id
    if not can(uid, 'ban'): return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target: return bot.send_message(m.chat.id, 'Ответь на сообщение или /ban uid 1d')
    if target == uid: return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid): return bot.send_message(m.chat.id, '❌ Нельзя равному/выше')

    time_str = parts[1] if len(parts) > 1 else 'forever'
    sec = parse_time(time_str)
    if sec is None: return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Бан', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, f'🚫 <code>{target}</code> забанен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🚫 Ты забанен на {time_until(until)}')
    except: pass


@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    uid = m.from_user.id
    if not can(uid, 'ban'): return
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target: return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> разбанен', parse_mode='HTML')


@bot.message_handler(commands=['unmute'])
def cmd_unmute(m):
    uid = m.from_user.id
    if not can(uid, 'mute'): return
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target: return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> размучен', parse_mode='HTML')


# ============================================================
# ПАНЕЛЬ РОЛЕЙ
# ============================================================
role_states = {}

@bot.message_handler(func=lambda m: m.text == 'Роли')
def cmd_roles_panel(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('👤 Назначить роль', callback_data='roles_assign'),
        types.InlineKeyboardButton('📋 Список ролей', callback_data='roles_list'),
        types.InlineKeyboardButton('❌ Снять роль', callback_data='roles_remove', style='danger'),
    )
    bot.send_message(m.chat.id, '🎭 <b>Управление ролями</b>', parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'roles_assign')
def cb_roles_assign(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    role_states[c.from_user.id] = {'action': 'assign_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '👤 Отправь <b>UID</b> пользователя:', parse_mode='HTML')


@bot.message_handler(func=lambda m: role_states.get(m.from_user.id, {}).get('action') == 'assign_uid')
def handle_assign_uid(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    try: target = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Некорректный UID')
    role_states[uid] = {'action': 'assign_role', 'target': target}
    kb = types.InlineKeyboardMarkup(row_width=1)
    for r, info in ROLES.items():
        if r == 5: continue
        kb.add(types.InlineKeyboardButton(f'{info["icon"]} {info["name"]}', callback_data=f'assign_pick_{r}'))
    bot.send_message(m.chat.id, f'🎭 Выбери роль для <code>{target}</code>:', parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('assign_pick_'))
def cb_assign_pick(c):
    uid = c.from_user.id
    if not can(uid, 'manage'): return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    state = role_states.get(uid, {})
    if state.get('action') != 'assign_role': return
    role = int(c.data.replace('assign_pick_', ''))
    target = state['target']
    if role not in ROLES or role == 5: return
    if get_role(target) >= get_role(uid) and target != uid:
        return bot.answer_callback_query(c.id, 'Нельзя', show_alert=True)
    set_role(target, role)
    info = ROLES[role]
    role_states.pop(uid, None)
    bot.answer_callback_query(c.id, 'Готово')
    bot.edit_message_text(f'✅ <code>{target}</code> → {info["icon"]} <b>{info["name"]}</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML')
    try: bot.send_message(target, f'Твоя роль: {info["icon"]} <b>{info["name"]}</b>', parse_mode='HTML')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == 'roles_list')
def cb_roles_list(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT uid, role FROM roles WHERE role > 0 ORDER BY role DESC')
    rows = c2.fetchall(); conn.close()
    text = '📋 <b>Назначенные роли</b>\n\n'
    if not rows:
        text += 'Пока пусто'
    else:
        for r_uid, role in rows:
            info = ROLES.get(role, {})
            text += f'{info.get("icon","?")} {info.get("name","?")} — <code>{r_uid}</code>\n'
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'roles_remove')
def cb_roles_remove(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    role_states[c.from_user.id] = {'action': 'remove_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '❌ Отправь <b>UID</b>:', parse_mode='HTML')


@bot.message_handler(func=lambda m: role_states.get(m.from_user.id, {}).get('action') == 'remove_uid')
def handle_remove_uid(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    try: target = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Некорректный UID')
    if get_role(target) >= get_role(uid) and target != uid:
        return bot.send_message(m.chat.id, '❌ Нельзя')
    set_role(target, 0)
    role_states.pop(uid, None)
    bot.send_message(m.chat.id, f'✅ Роль <code>{target}</code> снята', parse_mode='HTML')


# ============================================================
# ПОСТИНГ
# ============================================================
post_states = {}

@bot.message_handler(func=lambda m: m.text == 'Опубликовать')
def cmd_post(m):
    uid = m.from_user.id
    if not can(uid, 'post'): return
    if not CHANNEL_ID: return bot.send_message(m.chat.id, '❌ Канал не настроен')
    post_states[uid] = {'action': 'post'}
    bot.send_message(m.chat.id, '📝 Отправь текст поста (можно с фото).')


@bot.message_handler(func=lambda m: post_states.get(m.from_user.id, {}).get('action') == 'post',
                     content_types=['text', 'photo'])
def handle_post(m):
    uid = m.from_user.id
    if not can(uid, 'post'): return
    post_states.pop(uid, None)
    try:
        if m.photo:
            bot.send_photo(CHANNEL_ID, m.photo[-1].file_id, caption=m.caption or '')
        else:
            bot.send_message(CHANNEL_ID, m.text)
        bot.send_message(m.chat.id, '✅ Опубликовано!', reply_markup=main_kb(uid))
    except Exception as e:
        bot.send_message(m.chat.id, f'❌ Ошибка: {e}')


# ============================================================
# СТАТИСТИКА
# ============================================================
@bot.message_handler(func=lambda m: m.text == 'Статистика')
def cmd_stats(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM bans')
    bans = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM mutes')
    mutes = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM warns')
    warns = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM roles WHERE role > 0')
    roles_count = c.fetchone()[0]
    conn.close()
    bot.send_message(m.chat.id,
        f'📊 <b>Статистика</b>\n\n'
        f'🚫 Банов: <b>{bans}</b>\n'
        f'🔇 Мутов: <b>{mutes}</b>\n'
        f'⚠️ Варнов: <b>{warns}</b>\n'
        f'🎭 Ролей: <b>{roles_count}</b>',
        parse_mode='HTML')


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print('Roles bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
