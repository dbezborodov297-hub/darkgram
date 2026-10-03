import telebot
import sqlite3
import time
import re
import random
import threading
from telebot import types

# ============================================================
# ✏️ НАСТРОЙКИ — ЗАПОЛНИ ЭТО
# ============================================================
TOKEN = '8641977356:AAEithSvkupfKQAX-R8Dg10Wk7I_UuBlYFs'      # ← токен от BotFather
SUPER_ADMIN = 6430796415                # ← ТВОЙ ID (главный)
OWNER_IDS = [8907438590, 8852612552]     # ← ТВОЙ ID + ID второго админа
CHANNEL_ID = 4337299468                       # ← ID канала или None

# ============================================================
# ОСТАЛЬНОЕ — НЕ ТРОГАЙ
# ============================================================
WARN_MUTE = 3
WARN_BAN = 5
WARN_MUTE_TIME = 3600
WARN_BAN_TIME = 86400

COOLDOWN = 180
DAILY_LIMIT = 20

ROLES = {
    0: {'name': 'Обычный',      'icon': '👤', 'warn': False, 'mute': False, 'ban': False, 'post': False, 'manage': False},
    1: {'name': 'Младший мод',  'icon': '🛡️', 'warn': True,  'mute': True,  'ban': False, 'post': False, 'manage': False},
    2: {'name': 'Старший мод',  'icon': '⚔️', 'warn': True,  'mute': True,  'ban': True,  'post': False, 'manage': False},
    3: {'name': 'Постер',       'icon': '📝', 'warn': False, 'mute': False, 'ban': False, 'post': True,  'manage': False},
    4: {'name': 'Админ',        'icon': '👑', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
    5: {'name': 'Владелец',     'icon': '💎', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
    6: {'name': 'Главный',      'icon': '⭐', 'warn': True,  'mute': True,  'ban': True,  'post': True,  'manage': True},
}

NO_RIGHTS = ['❌ Не твоя епархия', '❌ Тебе нельзя', '❌ Не дорос', '❌ Руки коротки', '❌ Нет доступа, бро']

GROUP_MESSAGES = [
    '👋 {name}, я стесняюсь писать в группах\n\n📩 Написать админу → в личке\n👉 @{username}',
    '🤖 В группе я только читаю\n\n📬 Всё личное — в ЛС\n👉 @{username}',
    '📩 Личные вопросы — только в личке\n\n👉 @{username}',
    '🙈 Тут много людей, мне неловко\n\n📬 Стучись в личку → @{username}',
    '💬 Хочешь поговорить? Приходи в личку\n\n👉 @{username}',
    '🤫 В группе я молчу. Жду в личке\n\n👉 @{username}',
]

CD_MESSAGES = [
    '⏱️ Эй, не так быстро!\n\nПодожди <b>{time}</b>',
    '✋ Стоп-стоп. Ещё <b>{time}</b>',
    '⏳ Полегче. Через <b>{time}</b> снова можно',
    '🛑 Остынь немного. Осталось <b>{time}</b>',
]

LIMIT_MESSAGES = [
    '📊 На сегодня хватит. {n} — это максимум',
    '📊 Всё, лимит. Приходи завтра',
    '📊 Ты исчерпал дневной запас ({n}). До завтра!',
]

SUCCESS_MESSAGES = [
    '✅ Ушло админам! Не спамь — жди ответа',
    '✅ Отправлено! Админ ответит, если нужно',
    '✅ Готово. Сообщение на месте',
    '✅ Передал админам. Не скучай',
]

BAN_MESSAGES = [
    '🚫 {target} отправляется в изгнание на {time}',
    '🚫 {target} уходит в тень на {time}',
    '🚫 Пока-пока, {target} — увидимся через {time}',
    '🚫 {target} — отдохни от нас {time}',
]

MUTE_MESSAGES = [
    '🔇 {target} — молчать {time}',
    '🔇 {target} уходит в режим тишины на {time}',
    '🔇 Тс-с-с, {target}. Поговорим через {time}',
    '🔇 {target} закрывает рот на {time}',
]

WARN_MESSAGES = [
    '⚠️ {target}, это предупреждение ({n}/5)',
    '⚠️ {target} получает варн ({n}/5)',
    '⚠️ Эй, {target}, остынь ({n}/5)',
    '⚠️ {target}, ещё разок — и будет хуже ({n}/5)',
]

RULES_TEXT = """📜 <b>Правила ТГКБ</b>

<b>🤝 Уважение</b>
• Без мата, оскорблений, травли
• Спор — ок, хамство — нет

<b>📵 Контент</b>
• Без NSFW и жестокости
• Без рекламы без разрешения
• Без чужих личных данных

<b>🚫 Поведение</b>
• Без спама и флуда
• Без скама и мошенничества
• Без вредоносных ссылок

<b>⚖️ Наказания</b>
• 3 варна → мут на час
• 5 варнов → бан на сутки
• Серьёзное — бан навсегда

<b>💬 Связь:</b> 📩 Написать админу

<i>Незнание правил не освобождает от бана 🙂</i>
"""

PRIVACY_TEXT = """🔒 <b>Приватность</b>

Тут всё просто — <b>твои данные принадлежат тебе</b>.

<b>Что храним:</b>
• ID и имя из Telegram
• Сообщения, отправленные боту
• Роли и наказания

<b>Кому передаём:</b>
• Только админам этого бота
• Больше никому

<b>Что НЕ делаем:</b>
• Не продаём
• Не передаём третьим лицам
• Не следим без причины

<b>Твои права:</b>
• /mydata — посмотреть данные
• /deleteme — удалить всё

<i>Мы не ЦРУ. Мы просто следим за порядком.</i>
"""

bot = telebot.TeleBot(TOKEN)
DB = 'roles.db'


def delete_msg_safe(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print('delete err:', e)


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
    if uid == SUPER_ADMIN: return 6
    if uid in OWNER_IDS: return 5
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT role FROM roles WHERE uid=?', (uid,))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def set_role(uid, role):
    if uid == SUPER_ADMIN: return
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO roles (uid, role) VALUES (?, ?)', (uid, role))
    conn.commit(); conn.close()

def can(uid, action):
    role = get_role(uid)
    if role >= 5: return True
    return ROLES.get(role, {}).get(action, False)


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

def fmt_time_short(seconds):
    if seconds < 60: return f'{seconds} сек'
    m = seconds // 60
    s = seconds % 60
    if s == 0: return f'{m} мин'
    return f'{m} мин {s} сек'

def time_until(until_ts):
    if until_ts is None: return '—'
    if until_ts == 0: return 'навсегда'
    left = until_ts - int(time.time())
    if left <= 0: return 'истёк'
    return fmt_time(left)

def escape_html(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ============================================================
# АНТИСПАМ
# ============================================================
support_states = {}
user_last_send = {}
user_daily_count = {}

def check_cooldown(uid):
    last = user_last_send.get(uid, 0)
    left = COOLDOWN - (int(time.time()) - last)
    return max(0, left)

def check_daily(uid):
    now = int(time.time())
    times = user_daily_count.get(uid, [])
    times = [t for t in times if now - t < 86400]
    user_daily_count[uid] = times
    return len(times) >= DAILY_LIMIT


def resolve_target(m, args):
    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user.id
    if args:
        try: return int(args[0])
        except: return None
    return None


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
def main_menu_inline(uid):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('📩 Написать админу', callback_data='menu_write_admin'))
    role = get_role(uid)
    if role >= 1:
        kb.add(types.InlineKeyboardButton('🛡️ Штаб модерации', callback_data='menu_mod'))
    if role >= 4:
        kb.add(types.InlineKeyboardButton('👑 Центр управления', callback_data='menu_admin'))
    if role == 6:
        kb.add(types.InlineKeyboardButton('⭐ Панель главного', callback_data='menu_super'))
    kb.add(
        types.InlineKeyboardButton('📜 Правила', callback_data='menu_rules'),
        types.InlineKeyboardButton('🔒 Приватность', callback_data='menu_privacy'),
    )
    return kb


@bot.message_handler(commands=['start', 'menu'])
def cmd_start(m):
    uid = m.from_user.id
    if is_banned(uid):
        return bot.send_message(m.chat.id, f'🚫 Ты забанен. Осталось: {time_until(get_ban_until(uid))}')

    name = escape_html(m.from_user.first_name or 'друг')
    role = get_role(uid)
    role_name = ROLES.get(role, {}).get('name', 'Обычный')
    icon = ROLES.get(role, {}).get('icon', '👤')

    greetings = [
        f'С возвращением, {name}!',
        f'О, {name}, снова ты!',
        f'Привет-привет, {name}!',
        f'{name}, ты как раз вовремя.',
        f'Ну здорово, {name}!',
        f'Кто пришёл! {name}!',
    ]

    text = f'👋 <b>{random.choice(greetings)}</b>\n\n🎭 Твоя роль: {icon} <b>{role_name}</b>\n\n'
    if uid == SUPER_ADMIN:
        text += '⭐ Ты главный. Всё под контролем.\n'
    elif can(uid, 'manage'):
        text += '👑 У тебя полный доступ.\n'
    elif can(uid, 'ban'):
        text += '⚔️ Ты старший мод.\n'
    elif can(uid, 'warn'):
        text += '🛡️ Ты модератор.\n'
    elif can(uid, 'post'):
        text += '📝 Ты постер.\n'
    else:
        text += '📩 Есть вопросы? Пиши админу.\n'
    text += '\n📜 /rules — правила\n🔒 /privacy — приватность'

    rm = types.ReplyKeyboardRemove()
    bot.send_message(m.chat.id, '⏳', reply_markup=rm)
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu_inline(uid))


@bot.message_handler(commands=['myid', 'whoami'])
def cmd_myid(m):
    uid = m.from_user.id
    role = get_role(uid)
    text = f'👤 ID: <code>{uid}</code>\n'
    text += f'{ROLES[role]["icon"]} Роль: <b>{ROLES[role]["name"]}</b>\n'
    text += f'⚠️ Варнов: <b>{get_warns(uid)}</b>\n'
    if is_banned(uid): text += f'🚫 Бан: {time_until(get_ban_until(uid))}\n'
    if is_muted(uid): text += f'🔇 Мут: {time_until(get_mute_until(uid))}\n'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'menu_back')
def cb_menu_back(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    text = f'🎭 Твоя роль: {ROLES[get_role(uid)]["icon"]} <b>{ROLES[get_role(uid)]["name"]}</b>\n\nВыбирай:'
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              parse_mode='HTML', reply_markup=main_menu_inline(uid))
    except: pass


# ============================================================
# НАПИСАТЬ АДМИНУ
# ============================================================
@bot.message_handler(func=lambda m: m.text in ('📩 Написать админу', 'Написать админу'))
def cmd_write_admin(m):
    uid = m.from_user.id
    if m.chat.type != 'private':
        try:
            notice = bot.send_message(
                m.chat.id,
                random.choice(GROUP_MESSAGES).format(
                    name=escape_html(m.from_user.first_name or 'Друг'),
                    username=bot.get_me().username
                ),
                reply_to_message_id=m.message_id
            )
            threading.Timer(120, delete_msg_safe, args=[m.chat.id, notice.message_id]).start()
        except Exception as e:
            print('group notice err:', e)
        return

    if is_banned(uid): return bot.send_message(m.chat.id, f'🚫 Забанен. {time_until(get_ban_until(uid))}')
    if is_muted(uid): return bot.send_message(m.chat.id, f'🔇 Мут. {time_until(get_mute_until(uid))}')
    if check_daily(uid): return bot.send_message(m.chat.id, random.choice(LIMIT_MESSAGES).format(n=DAILY_LIMIT), parse_mode='HTML')
    cd = check_cooldown(uid)
    if cd > 0: return bot.send_message(m.chat.id, random.choice(CD_MESSAGES).format(time=fmt_time_short(cd)), parse_mode='HTML')

    support_states[uid] = {'action': 'write_admin'}
    bot.send_message(m.chat.id,
        '✍️ <b>Напиши сообщение админу</b>\n\n📎 Текст, фото, видео, голосовое, документ\n'
        f'📊 Осталось на день: <b>{DAILY_LIMIT - len(user_daily_count.get(uid, []))}</b>',
        parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'menu_write_admin')
def cb_menu_write_admin(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    if is_banned(uid): return bot.send_message(uid, f'🚫 Забанен. {time_until(get_ban_until(uid))}')
    if is_muted(uid): return bot.send_message(uid, f'🔇 Мут. {time_until(get_mute_until(uid))}')
    if check_daily(uid): return bot.send_message(uid, random.choice(LIMIT_MESSAGES).format(n=DAILY_LIMIT), parse_mode='HTML')
    cd = check_cooldown(uid)
    if cd > 0: return bot.send_message(uid, random.choice(CD_MESSAGES).format(time=fmt_time_short(cd)), parse_mode='HTML')
    support_states[uid] = {'action': 'write_admin'}
    bot.send_message(uid, '✍️ <b>Напиши сообщение админу</b>\n\n📎 Текст, фото, видео, голосовое, документ', parse_mode='HTML')


@bot.message_handler(
    func=lambda m: support_states.get(m.from_user.id, {}).get('action') == 'write_admin',
    content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'audio', 'sticker']
)
def handle_write_admin(m):
    uid = m.from_user.id
    if support_states.get(uid, {}).get('action') != 'write_admin': return
    support_states.pop(uid, None)
    user_last_send[uid] = int(time.time())
    user_daily_count.setdefault(uid, []).append(int(time.time()))
    name = m.from_user.first_name or 'Аноним'
    username = f'@{m.from_user.username}' if m.from_user.username else '—'
    left_today = DAILY_LIMIT - len(user_daily_count.get(uid, []))
    for admin_id in set(OWNER_IDS + [SUPER_ADMIN]):
        try:
            bot.send_message(admin_id,
                f'📩 <b>Сообщение от пользователя</b>\n\n👤 {escape_html(name)} ({username})\n🆔 <code>{uid}</code>\n📊 Осталось: {left_today}',
                parse_mode='HTML')
            bot.forward_message(admin_id, m.chat.id, m.message_id)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton('💬 Ответить', callback_data=f'reply_to_{uid}'))
            bot.send_message(admin_id, '↓ Ответить:', reply_markup=kb)
        except Exception as e:
            print(f'admin err {admin_id}:', e)
    bot.send_message(m.chat.id,
        f'{random.choice(SUCCESS_MESSAGES)}\n\n⏱️ Блокировка на 3 минуты\n📊 Осталось: <b>{left_today}</b>',
        parse_mode='HTML', reply_markup=main_menu_inline(uid))


reply_states = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith('reply_to_'))
def cb_reply_to(c):
    if c.from_user.id not in OWNER_IDS and c.from_user.id != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
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
    if uid not in OWNER_IDS and uid != SUPER_ADMIN: return
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
# ШТАБ МОДЕРАЦИИ
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_mod')
def cb_menu_mod(c):
    uid = c.from_user.id
    if get_role(uid) < 1:
        return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    if can(uid, 'warn'): kb.add(types.InlineKeyboardButton('⚠️ Варн', callback_data='mod_warn'))
    if can(uid, 'mute'): kb.add(types.InlineKeyboardButton('🔇 Мут', callback_data='mod_mute'))
    if can(uid, 'ban'): kb.add(types.InlineKeyboardButton('🚫 Бан', callback_data='mod_ban', style='danger'))
    kb.add(types.InlineKeyboardButton('✅ Размут', callback_data='mod_unmute', style='success'))
    if can(uid, 'ban'): kb.add(types.InlineKeyboardButton('✅ Разбан', callback_data='mod_unban', style='success'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text('🛡️ <b>Штаб модерации</b>\n\nЧто делаем?',
                          c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'mod_warn')
def cb_mod_warn(c):
    if not can(c.from_user.id, 'warn'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '⚠️ <code>/warn uid</code> — или ответь на сообщение', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'mod_mute')
def cb_mod_mute(c):
    if not can(c.from_user.id, 'mute'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '🔇 <code>/mute uid 1h</code>\n\n5m, 1h, 1d, forever', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'mod_ban')
def cb_mod_ban(c):
    if not can(c.from_user.id, 'ban'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '🚫 <code>/ban uid 1d</code>\n\n5m, 1h, 1d, forever', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'mod_unmute')
def cb_mod_unmute(c):
    if not can(c.from_user.id, 'mute'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '✅ <code>/unmute uid</code>', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'mod_unban')
def cb_mod_unban(c):
    if not can(c.from_user.id, 'ban'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '✅ <code>/unban uid</code>', parse_mode='HTML')


# ============================================================
# ЦЕНТР УПРАВЛЕНИЯ
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_admin')
def cb_menu_admin(c):
    uid = c.from_user.id
    if not can(uid, 'manage'):
        return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🎭 Роли', callback_data='panel_roles'),
        types.InlineKeyboardButton('🔇 Глушилка', callback_data='panel_gag'),
    )
    kb.add(
        types.InlineKeyboardButton('📝 Пост', callback_data='panel_post'),
        types.InlineKeyboardButton('📊 Стата', callback_data='panel_stats'),
    )
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text('👑 <b>Центр управления</b>', c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'panel_roles')
def cb_panel_roles(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('👤 Назначить роль', callback_data='roles_assign'),
        types.InlineKeyboardButton('📋 Список ролей', callback_data='roles_list'),
        types.InlineKeyboardButton('❌ Снять роль', callback_data='roles_remove', style='danger'),
        types.InlineKeyboardButton('◀️ Назад', callback_data='menu_admin'),
    )
    bot.answer_callback_query(c.id)
    bot.edit_message_text('🎭 <b>Управление ролями</b>', c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'panel_gag')
def cb_panel_gag(c):
    if not can(c.from_user.id, 'manage'): return
    enabled = get_setting('gag_bots', '0') == '1'
    status = '🔴 ВКЛЮЧЕНА' if enabled else '🟢 ВЫКЛЮЧЕНА'
    kb = types.InlineKeyboardMarkup(row_width=1)
    if enabled:
        kb.add(types.InlineKeyboardButton('🟢 Выключить', callback_data='gag_off', style='success'))
    else:
        kb.add(types.InlineKeyboardButton('🔴 Включить', callback_data='gag_on', style='danger'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_admin'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(f'🔇 <b>Глушилка</b>\n\nСтатус: <b>{status}</b>',
                          c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'panel_post')
def cb_panel_post(c):
    if not can(c.from_user.id, 'post'): return
    bot.answer_callback_query(c.id)
    post_states[c.from_user.id] = {'action': 'post'}
    bot.send_message(c.message.chat.id, '📝 Отправь текст поста (можно с фото).')


@bot.callback_query_handler(func=lambda c: c.data == 'panel_stats')
def cb_panel_stats(c):
    if not can(c.from_user.id, 'manage'): return
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT COUNT(*) FROM bans'); bans = c2.fetchone()[0]
    c2.execute('SELECT COUNT(*) FROM mutes'); mutes = c2.fetchone()[0]
    c2.execute('SELECT COUNT(*) FROM warns'); warns = c2.fetchone()[0]
    c2.execute('SELECT COUNT(*) FROM roles WHERE role > 0'); rc = c2.fetchone()[0]
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_admin'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(
        f'📊 <b>Цифры дня</b>\n\n🚫 Банов: <b>{bans}</b>\n🔇 Мутов: <b>{mutes}</b>\n⚠️ Варнов: <b>{warns}</b>\n🎭 Ролей: <b>{rc}</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


# ============================================================
# ГЛУШИЛКА
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'gag_on')
def cb_gag_on(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    set_setting('gag_bots', '1')
    bot.answer_callback_query(c.id, '🔴 Включено')
    bot.edit_message_text('🔇 <b>Глушилка</b>\n\nСтатус: <b>🔴 ВКЛЮЧЕНА</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'gag_off')
def cb_gag_off(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
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
# РОЛИ — КНОПКИ
# ============================================================
role_states = {}

@bot.callback_query_handler(func=lambda c: c.data == 'roles_assign')
def cb_roles_assign(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    role_states[c.from_user.id] = {'action': 'assign_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '👤 Отправь <b>UID</b>:', parse_mode='HTML')


@bot.message_handler(func=lambda m: role_states.get(m.from_user.id, {}).get('action') == 'assign_uid')
def handle_assign_uid(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    try: target = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Некорректный UID')
    role_states[uid] = {'action': 'assign_role', 'target': target}
    kb = types.InlineKeyboardMarkup(row_width=1)
    for r, info in ROLES.items():
        if r in (5, 6): continue
        kb.add(types.InlineKeyboardButton(f'{info["icon"]} {info["name"]}', callback_data=f'assign_pick_{r}'))
    bot.send_message(m.chat.id, f'🎭 Роль для <code>{target}</code>:', parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('assign_pick_'))
def cb_assign_pick(c):
    uid = c.from_user.id
    if not can(uid, 'manage'): return
    state = role_states.get(uid, {})
    if state.get('action') != 'assign_role': return
    role = int(c.data.replace('assign_pick_', ''))
    target = state['target']
    if role not in ROLES or role >= 5: return

    if uid == SUPER_ADMIN:
        pass
    elif get_role(uid) == 5:
        if target == SUPER_ADMIN or get_role(target) == 5:
            return bot.answer_callback_query(c.id, '❌ Нельзя', show_alert=True)
    elif get_role(target) >= get_role(uid):
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
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT uid, role FROM roles WHERE role > 0 ORDER BY role DESC')
    rows = c2.fetchall(); conn.close()
    text = '📋 <b>Роли</b>\n\n'
    text += f'⭐ Главный: <code>{SUPER_ADMIN}</code>\n'
    for oid in OWNER_IDS:
        if oid != SUPER_ADMIN:
            text += f'👑 Админ: <code>{oid}</code>\n'
    for r_uid, role in rows:
        info = ROLES.get(role, {})
        text += f'{info.get("icon","?")} {info.get("name","?")} — <code>{r_uid}</code>\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='panel_roles'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'roles_remove')
def cb_roles_remove(c):
    if not can(c.from_user.id, 'manage'): return bot.answer_callback_query(c.id, random.choice(NO_RIGHTS), show_alert=True)
    role_states[c.from_user.id] = {'action': 'remove_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '❌ Отправь <b>UID</b>:', parse_mode='HTML')


@bot.message_handler(func=lambda m: role_states.get(m.from_user.id, {}).get('action') == 'remove_uid')
def handle_remove_uid(m):
    uid = m.from_user.id
    if not can(uid, 'manage'): return
    try: target = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Некорректный UID')
    if target == SUPER_ADMIN: return bot.send_message(m.chat.id, '❌ Главного нельзя')
    if uid == SUPER_ADMIN:
        pass
    elif get_role(uid) == 5:
        if get_role(target) == 5: return bot.send_message(m.chat.id, '❌ Другого админа нельзя')
    elif get_role(target) >= get_role(uid):
        return bot.send_message(m.chat.id, '❌ Нельзя')
    set_role(target, 0)
    role_states.pop(uid, None)
    bot.send_message(m.chat.id, f'✅ Роль <code>{target}</code> снята', parse_mode='HTML')


# ============================================================
# ПАНЕЛЬ ГЛАВНОГО
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_super')
def cb_menu_super(c):
    uid = c.from_user.id
    if uid != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, '⭐ Только для главного', show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('👑 Снять админа', callback_data='super_demote_admin', style='danger'),
        types.InlineKeyboardButton('📋 Все админы', callback_data='super_list_admins'),
        types.InlineKeyboardButton('🗑️ Стереть данные', callback_data='super_nuke', style='danger'),
        types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'),
    )
    bot.answer_callback_query(c.id)
    bot.edit_message_text('⭐ <b>Панель главного</b>\n\nТолько для тебя. Осторожно.',
        c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'super_demote_admin')
def cb_super_demote(c):
    if c.from_user.id != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    role_states[c.from_user.id] = {'action': 'super_demote_uid'}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, '👑 Отправь <b>UID админа</b>:', parse_mode='HTML')


@bot.message_handler(func=lambda m: role_states.get(m.from_user.id, {}).get('action') == 'super_demote_uid')
def handle_super_demote(m):
    uid = m.from_user.id
    if uid != SUPER_ADMIN: return
    try: target = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Некорректный UID')
    if target == SUPER_ADMIN: return bot.send_message(m.chat.id, '❌ Себя нельзя')
    set_role(target, 0)
    role_states.pop(uid, None)
    bot.send_message(m.chat.id, f'✅ <code>{target}</code> больше не админ', parse_mode='HTML')
    try: bot.send_message(target, '👋 С тебя сняли права')
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == 'super_list_admins')
def cb_super_list_admins(c):
    if c.from_user.id != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    text = '📋 <b>Все админы</b>\n\n'
    text += f'⭐ Главный: <code>{SUPER_ADMIN}</code>\n'
    for oid in OWNER_IDS:
        if oid != SUPER_ADMIN:
            text += f'👑 Админ: <code>{oid}</code>\n'
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('SELECT uid FROM roles WHERE role=4')
    for row in c2.fetchall():
        text += f'👑 Админ (из ролей): <code>{row[0]}</code>\n'
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_super'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'super_nuke')
def cb_super_nuke(c):
    if c.from_user.id != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Да, стереть', callback_data='super_nuke_confirm', style='danger'),
        types.InlineKeyboardButton('❌ Отмена', callback_data='menu_super'),
    )
    bot.answer_callback_query(c.id)
    bot.edit_message_text('⚠️ <b>Стереть ВСЕ данные?</b>\n\nЭто удалит роли, варны, баны, муты.\n\n<b>НЕОБРАТИМО!</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'super_nuke_confirm')
def cb_super_nuke_confirm(c):
    if c.from_user.id != SUPER_ADMIN:
        return bot.answer_callback_query(c.id, 'Нет', show_alert=True)
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('DELETE FROM roles')
    c2.execute('DELETE FROM warns')
    c2.execute('DELETE FROM bans')
    c2.execute('DELETE FROM mutes')
    c2.execute('DELETE FROM personal_access')
    conn.commit(); conn.close()
    bot.answer_callback_query(c.id, 'Стёрто')
    bot.edit_message_text('✅ Все данные стёрты.', c.message.chat.id, c.message.message_id, parse_mode='HTML')


# ============================================================
# МОДЕРАЦИЯ — КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['warn'])
def cmd_warn(m):
    uid = m.from_user.id
    if not can(uid, 'warn'): return bot.send_message(m.chat.id, '❌ Нет прав')
    args = m.text.split()[1:]
    target = resolve_target(m, args)
    if not target: return bot.send_message(m.chat.id, 'Ответь на сообщение или /warn uid')
    if target == uid: return bot.send_message(m.chat.id, '❌ Себе нельзя')
    if get_role(target) >= get_role(uid): return bot.send_message(m.chat.id, '❌ Нельзя равному/выше')

    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT INTO warns (uid, reason, by_uid, time) VALUES (?, ?, ?, ?)',
              (target, 'Нарушение', uid, int(time.time())))
    conn.commit()
    c.execute('SELECT COUNT(*) FROM warns WHERE uid=?', (target,))
    warns = c.fetchone()[0]; conn.close()

    bot.send_message(m.chat.id, random.choice(WARN_MESSAGES).format(target=f'<code>{target}</code>', n=warns), parse_mode='HTML')
    auto = ''
    if warns >= WARN_BAN:
        until = int(time.time()) + WARN_BAN_TIME
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                  (target, until, f'{WARN_BAN} варнов', uid))
        conn.commit(); conn.close()
        auto = f'\n💀 {WARN_BAN} варнов — автобан на {fmt_time(WARN_BAN_TIME)}'
    elif warns >= WARN_MUTE:
        until = int(time.time()) + WARN_MUTE_TIME
        conn = sqlite3.connect(DB); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)',
                  (target, until, f'{WARN_MUTE} варнов', uid))
        conn.commit(); conn.close()
        auto = f'\n🤐 {WARN_MUTE} варна — автомут на {fmt_time(WARN_MUTE_TIME)}'
    if auto: bot.send_message(m.chat.id, auto)
    try: bot.send_message(target, f'⚠️ Варн ({warns}/5){auto}')
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
    c.execute('INSERT OR REPLACE INTO mutes (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)', (target, until, 'Мут', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, random.choice(MUTE_MESSAGES).format(target=f'<code>{target}</code>', time=time_until(until)), parse_mode='HTML')
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
    c.execute('INSERT OR REPLACE INTO bans (uid, until, reason, by_uid) VALUES (?, ?, ?, ?)', (target, until, 'Бан', uid))
    conn.commit(); conn.close()

    bot.send_message(m.chat.id, random.choice(BAN_MESSAGES).format(target=f'<code>{target}</code>', time=time_until(until)), parse_mode='HTML')
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
# ПОСТИНГ
# ============================================================
post_states = {}

@bot.message_handler(func=lambda m: post_states.get(m.from_user.id, {}).get('action') == 'post',
                     content_types=['text', 'photo'])
def handle_post(m):
    uid = m.from_user.id
    if not can(uid, 'post'): return
    post_states.pop(uid, None)
    if not CHANNEL_ID: return bot.send_message(m.chat.id, '❌ Канал не настроен')
    try:
        if m.photo:
            bot.send_photo(CHANNEL_ID, m.photo[-1].file_id, caption=m.caption or '')
        else:
            bot.send_message(CHANNEL_ID, m.text)
        bot.send_message(m.chat.id, '✅ Опубликовано!')
    except Exception as e:
        bot.send_message(m.chat.id, f'❌ Ошибка: {e}')


# ============================================================
# ПРАВИЛА / ПРИВАТНОСТЬ / ДАННЫЕ
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_rules')
def cb_menu_rules(c):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(RULES_TEXT, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_privacy')
def cb_menu_privacy(c):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(PRIVACY_TEXT, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.message_handler(commands=['rules'])
def cmd_rules(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_back'))
    bot.send_message(m.chat.id, RULES_TEXT, parse_mode='HTML', reply_markup=kb)


@bot.message_handler(commands=['privacy'])
def cmd_privacy(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_back'))
    bot.send_message(m.chat.id, PRIVACY_TEXT, parse_mode='HTML', reply_markup=kb)


@bot.message_handler(commands=['limits'])
def cmd_limits(m):
    uid = m.from_user.id
    cd = check_cooldown(uid)
    today = len(user_daily_count.get(uid, []))
    status = f'⏱️ {fmt_time_short(cd)}' if cd > 0 else '✅ готов'
    text = f'📊 <b>Твои лимиты</b>\n\n⏱️ Кулдаун: <b>{status}</b>\n📩 Сегодня: <b>{today}/{DAILY_LIMIT}</b>\n⏳ Осталось: <b>{DAILY_LIMIT - today}</b>'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['mydata'])
def cmd_mydata(m):
    uid = m.from_user.id
    role = get_role(uid)
    warns = get_warns(uid)
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT until FROM bans WHERE uid=?', (uid,))
    ban_row = c.fetchone()
    c.execute('SELECT until FROM mutes WHERE uid=?', (uid,))
    mute_row = c.fetchone()
    c.execute('SELECT COUNT(*) FROM personal_access WHERE uid=?', (uid,))
    pa = c.fetchone()[0]
    conn.close()
    text = (
        f'📊 <b>Твои данные</b>\n\n'
        f'🆔 ID: <code>{uid}</code>\n'
        f'👤 Имя: {escape_html(m.from_user.first_name or "—")}\n'
        f'🔗 Username: @{m.from_user.username or "—"}\n\n'
        f'{ROLES[role]["icon"]} Роль: <b>{ROLES[role]["name"]}</b>\n'
        f'⚠️ Варнов: <b>{warns}</b>\n'
        f'🚫 Бан: <b>{time_until(ban_row[0]) if ban_row else "нет"}</b>\n'
        f'🔇 Мут: <b>{time_until(mute_row[0]) if mute_row else "нет"}</b>\n'
        f'🔑 Личных доступов: <b>{pa}</b>\n'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🗑️ Удалить мои данные', callback_data='delete_mydata', style='danger'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_back'))
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'delete_mydata')
def cb_delete_mydata(c):
    uid = c.from_user.id
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Да, удалить', callback_data='confirm_delete', style='danger'),
        types.InlineKeyboardButton('❌ Отмена', callback_data='menu_back'),
    )
    bot.answer_callback_query(c.id)
    bot.edit_message_text(
        '⚠️ <b>Удалить все твои данные?</b>\n\n• Роли\n• Варны\n• Баны/муты\n• Личные доступы\n\n<b>Восстановить нельзя!</b>',
        c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'confirm_delete')
def cb_confirm_delete(c):
    uid = c.from_user.id
    conn = sqlite3.connect(DB); c2 = conn.cursor()
    c2.execute('DELETE FROM roles WHERE uid=?', (uid,))
    c2.execute('DELETE FROM warns WHERE uid=?', (uid,))
    c2.execute('DELETE FROM bans WHERE uid=?', (uid,))
    c2.execute('DELETE FROM mutes WHERE uid=?', (uid,))
    c2.execute('DELETE FROM personal_access WHERE uid=?', (uid,))
    conn.commit(); conn.close()
    bot.answer_callback_query(c.id, 'Удалено')
    bot.edit_message_text('✅ <b>Данные удалены</b>\n\nВсё стёрто. /start — начать заново.',
        c.message.chat.id, c.message.message_id, parse_mode='HTML')


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print('TGKB bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
