import telebot
import sqlite3
import time
import re
from telebot import types

TOKEN = '8641977356:AAEOuInqlZbeeS98OHzA7ChxbeedU-RvRR4'
OWNER_ID = 6430796415 # Твой ID (узнать: /myid)
CHANNEL_ID = 4337299468 # ID канала для публикации

# Автонаказания
WARN_MUTE = 3    # 3 варна = автомут
WARN_BAN = 5     # 5 варнов = автобан
WARN_MUTE_TIME = 3600
WARN_BAN_TIME = 86400

# Роли
ROLES = {
    0: {'name': 'Обычный',       'icon': '👤', 'warn': False, 'mute': False, 'ban': False, 'post': False, 'manage': False},
    1: {'name': 'Младший мод',   'icon': '🛡️', 'warn': True,  'mute': True,  'ban': False, 'post': False, 'manage': False},
    2: {'name': 'Старший мод',   'icon': '⚔️', 'warn': True,  'mute': True,  'ban': True,  'post': False, 'manage': False},
    3: {'name': 'Постер',        'icon': '📝', 'warn': False, 'mute': False, 'ban': False, 'post': True,  'manage': False},
    4: {'name': 'Админ',         'icon': '👑', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
    5: {'name': 'Владелец',      'icon': '💎', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
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
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, name TEXT, text TEXT, photo TEXT,
        created INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS personal_access (
        uid INTEGER, command TEXT, PRIMARY KEY (uid, command)
    )''')
    conn.commit()
    conn.close()

init_db()


# ============================================================
# РОЛИ
# ============================================================
def get_role(uid):
    if uid == OWNER_ID: return 5
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT role FROM roles WHERE uid=?', (uid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def set_role(uid, role):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO roles (uid, role) VALUES (?, ?)', (uid, role))
    conn.commit()
    conn.close()

def can(uid, action):
    """action: warn / mute / ban / post / manage"""
    role = get_role(uid)
    if role == 5: return True
    return ROLES.get(role, {}).get(action, False)

def has_personal_access(uid, command):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT 1 FROM personal_access WHERE uid=? AND command=?', (uid, command))
    row = c.fetchone()
    conn.close()
    return bool(row)


# ============================================================
# НАКАЗАНИЯ
# ============================================================
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


# ============================================================
# ПАРСИНГ ЦЕЛИ (@username или reply)
# ============================================================
def resolve_target(m, args):
    """Возвращает uid цели из аргументов или reply."""
    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user.id
    if args:
        target = args[0]
        if target.startswith('@'):
            return None  # нельзя resolve @username без базы
        try:
            return int(target)
        except:
            return None
    return None


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    role = get_role(uid)
    if can(uid, 'post'):
        kb.add('Опубликовать')
    if can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban'):
        kb.add('Модерация')
    if can(uid, 'manage'):
        kb.add('Роли', 'Статистика')
    return kb


def mod_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    if can(uid, 'warn'):
        kb.add(types.InlineKeyboardButton('Варн', callback_data='ask_warn'))
    if can(uid, 'mute'):
        kb.add(types.InlineKeyboardButton('Мут', callback_data='ask_mute'))
    if can(uid, 'ban'):
        kb.add(types.InlineKeyboardButton('Бан', callback_data='ask_ban', style='danger'))
    return kb


def duration_kb(action):
    kb = types.InlineKeyboardMarkup(row_width=3)
    times = [
        ('1м', '1m'), ('5м', '5m'), ('30м', '30m'),
        ('1ч', '1h'), ('6ч', '6h'), ('1д', '1d'),
        ('7д', '7d'), ('30д', '30d'), ('Навсегда', 'forever'),
    ]
    btns = [types.InlineKeyboardButton(label, callback_data=f'{action}_dur_{val}') for label, val in times]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('Отмена', callback_data='cancel', style='danger'))
    return kb


def roles_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for r, info in ROLES.items():
        if r == 5: continue
        kb.add(types.InlineKeyboardButton(f'{info["icon"]} {info["name"]}', callback_data=f'setrole_{r}'))
    return kb


# ============================================================
# СТАРТ
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🚫 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')
    role = get_role(uid)
    role_name = ROLES.get(role, {}).get('name', 'Обычный')
    icon = ROLES.get(role, {}).get('icon', '👤')
    text = (
        f'👋 <b>Модерация-бот</b>\n\n'
        f'Твоя роль: {icon} <b>{role_name}</b>\n\n'
        f'Используй меню ниже.'
    )
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
# МОДЕРАЦИЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text == 'Модерация')
def cmd_mod(m):
    uid = m.from_user.id
    if not (can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban')):
        return
    text = (
        '🛡️ <b>Модерация</b>\n\n'
        'Команды:\n'
        '<code>/warn uid</code> — варн\n'
        '<code>/mute uid 1h</code> — мут\n'
        '<code>/ban uid 1d</code> — бан\n'
        '<code>/unban uid</code>\n'
        '<code>/unmute uid</code>\n\n'
        'Или ответь на сообщение и напиши команду без uid.'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# ВАРН
# ============================================================
@bot.message_handler(commands=['warn'])
def cmd_warn(m):
    uid = m.from_user.id
    if not can(uid, 'warn'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    args = m.text.split()[1:]
    target = resolve_target(m, args)
    if not target:
        return bot.send_message(m.chat.id, 'Использование: ответь на сообщение или <code>/warn uid</code>', parse_mode='HTML')
    if target == uid:
        return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid):
        return bot.send_message(m.chat.id, '❌ Нельзя выдать равному или выше')

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT INTO warns (uid, reason, by_uid, time) VALUES (?, ?, ?, ?)',
              (target, 'Нарушение', uid, int(time.time())))
    conn.commit()
    c.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (target,))
    warns = c.fetchone()[0]
    conn.close()

    bot.send_message(m.chat.id, f'⚠️ <code>{target}</code> получил варн ({warns}/5)', parse_mode='HTML')

    # Автонаказание
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

    if auto:
        bot.send_message(m.chat.id, f'⚡ Автонаказание:{auto}')

    try: bot.send_message(target, f'⚠️ Ты получил варн ({warns}/5){auto}')
    except: pass


# ============================================================
# МУТ
# ============================================================
@bot.message_handler(commands=['mute'])
def cmd_mute(m):
    uid = m.from_user.id
    if not can(uid, 'mute'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target:
        return bot.send_message(m.chat.id, 'Использование: <code>/mute uid 1h</code>', parse_mode='HTML')
    if target == uid:
        return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid):
        return bot.send_message(m.chat.id, '❌ Нельзя равному или выше')

    time_str = parts[1] if len(parts) > 1 else '1h'
    sec = parse_time(time_str)
    if sec is None:
        return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Мут', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, f'🔇 <code>{target}</code> замучен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🔇 Ты замучен на {time_until(until)}')
    except: pass


# ============================================================
# БАН
# ============================================================
@bot.message_handler(commands=['ban'])
def cmd_ban(m):
    uid = m.from_user.id
    if not can(uid, 'ban'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target:
        return bot.send_message(m.chat.id, 'Использование: <code>/ban uid 1d</code>', parse_mode='HTML')
    if target == uid:
        return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid):
        return bot.send_message(m.chat.id, '❌ Нельзя равному или выше')

    time_str = parts[1] if len(parts) > 1 else 'forever'
    sec = parse_time(time_str)
    if sec is None:
        return bot.send_message(m.chat.id, '❌ Время: 5m, 1h, 1d, forever')
    until = 0 if sec == 0 else int(time.time()) + sec

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
              (target, until, 'Бан', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, f'🚫 <code>{target}</code> забанен на {time_until(until)}', parse_mode='HTML')
    try: bot.send_message(target, f'🚫 Ты забанен на {time_until(until)}')
    except: pass


# ============================================================
# РАЗБАН / РАЗМУТ
# ============================================================
@bot.message_handler(commands=['unban'])
def cmd_unban(m):
    uid = m.from_user.id
    if not can(uid, 'ban'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target:
        return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM bans WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> разбанен', parse_mode='HTML')


@bot.message_handler(commands=['unmute'])
def cmd_unmute(m):
    uid = m.from_user.id
    if not can(uid, 'mute'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target:
        return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('DELETE FROM mutes WHERE uid=?', (target,))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> размучен', parse_mode='HTML')


# ============================================================
# ПОСТИНГ
# ============================================================
user_states = {}

@bot.message_handler(func=lambda m: m.text == 'Опубликовать')
def cmd_post(m):
    uid = m.from_user.id
    if not can(uid, 'post'):
        return
    if not CHANNEL_ID:
        return bot.send_message(m.chat.id, '❌ Канал не настроен')
    user_states[uid] = {'action': 'post_text'}
    bot.send_message(m.chat.id, '📝 Отправь текст поста (можно с фото).')


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('action') == 'post_text', content_types=['text', 'photo'])
def handle_post(m):
    uid = m.from_user.id
    if not can(uid, 'post'):
        return
    try:
        if m.photo:
            photo = m.photo[-1].file_id
            caption = m.caption or ''
            bot.send_photo(CHANNEL_ID, photo, caption=caption)
        else:
            bot.send_message(CHANNEL_ID, m.text)
        bot.send_message(m.chat.id, '✅ Опубликовано!', reply_markup=main_kb(uid))
    except Exception as e:
        bot.send_message(m.chat.id, f'❌ Ошибка: {e}')
    user_states.pop(uid, None)


# ============================================================
# УПРАВЛЕНИЕ РОЛЯМИ
# ============================================================
@bot.message_handler(commands=['setrole'])
def cmd_setrole(m):
    uid = m.from_user.id
    if not can(uid, 'manage'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target or len(parts) < 2:
        return bot.send_message(m.chat.id, 'Использование: <code>/setrole uid 2</code>\n\n0 — Обычный\n1 — Младший мод\n2 — Старший мод\n3 — Постер\n4 — Админ', parse_mode='HTML')
    try:
        role = int(parts[1])
    except:
        return bot.send_message(m.chat.id, '❌ Роль от 0 до 4')
    if role not in ROLES or role == 5:
        return bot.send_message(m.chat.id, '❌ Роль от 0 до 4')
    if get_role(target) >= get_role(uid) and target != uid:
        return bot.send_message(m.chat.id, '❌ Нельзя менять равному или выше')

    set_role(target, role)
    info = ROLES[role]
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> → {info["icon"]} <b>{info["name"]}</b>', parse_mode='HTML')
    try: bot.send_message(target, f'Твоя роль: {info["icon"]} <b>{info["name"]}</b>', parse_mode='HTML')
    except: pass


@bot.message_handler(commands=['removerole'])
def cmd_removerole(m):
    uid = m.from_user.id
    if not can(uid, 'manage'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target:
        return bot.send_message(m.chat.id, 'Использование: <code>/removerole uid</code>', parse_mode='HTML')
    set_role(target, 0)
    bot.send_message(m.chat.id, f'✅ Роль <code>{target}</code> снята', parse_mode='HTML')


@bot.message_handler(commands=['roles'])
def cmd_roles(m):
    uid = m.from_user.id
    if not can(uid, 'manage'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT uid, role FROM roles WHERE role > 0 ORDER BY role DESC')
    rows = c.fetchall()
    conn.close()
    if not rows:
        return bot.send_message(m.chat.id, 'Нет назначенных ролей')
    text = '<b>Роли</b>\n\n'
    for r_uid, role in rows:
        info = ROLES.get(role, {})
        text += f'{info.get("icon", "?")} {info.get("name", "?")} — <code>{r_uid}</code>\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# ЛИЧНЫЙ ДОСТУП
# ============================================================
@bot.message_handler(commands=['ldk'])
def cmd_ldk(m):
    """+лдк — выдать личный доступ к команде"""
    uid = m.from_user.id
    if not can(uid, 'manage'):
        return bot.send_message(m.chat.id, '❌ Нет прав')
    parts = m.text.split()[1:]
    target = resolve_target(m, parts)
    if not target or len(parts) < 2:
        return bot.send_message(m.chat.id, 'Использование: <code>/ldk uid команда</code>\n\nКоманды: ban, mute, warn, post', parse_mode='HTML')
    command = parts[1].lower()
    if command not in ('ban', 'mute', 'warn', 'post'):
        return bot.send_message(m.chat.id, '❌ Команда: ban, mute, warn, post')
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO personal_access (uid, command) VALUES (?, ?)', (target, command))
    conn.commit(); conn.close()
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> получил доступ к <b>{command}</b>', parse_mode='HTML')


# ============================================================
# ПРОВЕРКА МУТА/БАНА НА ВСЕ КОМАНДЫ
# ============================================================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def check_ban_mute(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🚫 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')
    # проверка мутов для команд, кроме модерации
    if is_muted(uid):
        # разрешаем модераторам писать
        if not (can(uid, 'warn') or can(uid, 'mute') or can(uid, 'ban')):
            return bot.send_message(m.chat.id, f'🔇 Ты в муте. Осталось: {time_until(get_mute_until(uid))}')


if __name__ == '__main__':
    print('Roles bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
