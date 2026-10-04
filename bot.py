import telebot
import sqlite3
import time
import random
import threading
from telebot import types

TOKEN = '7844349770:AAGCLpxi_HMhxJA1EAF_XbF_nQsUhRFzo_w'
WEBAPP_URL = 'https://darkgram-2.onrender.com'
COOLDOWN = 120
START_STARS = 100

COUNTRIES = [
    ('🇦🇩','common'),('🇦🇱','common'),('🇦🇲','common'),('🇦🇹','common'),
    ('🇦🇿','common'),('🇧🇦','common'),('🇧🇬','common'),('🇧🇾','common'),
    ('🇨🇭','common'),('🇨🇿','common'),('🇩🇰','common'),('🇪🇪','common'),
    ('🇫🇮','common'),('🇬🇪','common'),('🇭🇷','common'),('🇭🇺','common'),
    ('🇮🇸','common'),('🇮🇪','common'),('🇱🇹','common'),('🇱🇻','common'),
    ('🇲🇩','common'),('🇲🇪','common'),('🇲🇰','common'),('🇳🇴','common'),
    ('🇵🇹','common'),('🇷🇴','common'),('🇷🇸','common'),('🇸🇰','common'),
    ('🇸🇮','common'),('🇸🇪','common'),('🇺🇦','common'),('🇬🇷','common'),
    ('🇨🇾','common'),('🇲🇹','common'),('🇱🇺','common'),('🇲🇨','common'),
    ('🇱🇮','common'),('🇸🇲','common'),('🇻🇦','common'),
    ('🇵🇱','rare'),('🇦🇷','rare'),('🇦🇺','rare'),('🇧🇪','rare'),
    ('🇧🇷','rare'),('🇨🇦','rare'),('🇨🇱','rare'),('🇨🇴','rare'),
    ('🇪🇬','rare'),('🇮🇱','rare'),('🇮🇩','rare'),('🇮🇷','rare'),
    ('🇰🇿','rare'),('🇲🇽','rare'),('🇲🇦','rare'),('🇳🇱','rare'),
    ('🇳🇿','rare'),('🇳🇬','rare'),('🇵🇰','rare'),('🇵🇪','rare'),
    ('🇵🇭','rare'),('🇸🇦','rare'),('🇿🇦','rare'),('🇰🇷','rare'),
    ('🇪🇸','rare'),('🇹🇭','rare'),('🇹🇷','rare'),('🇻🇳','rare'),
    ('🇦🇪','rare'),('🇲🇾','rare'),
    ('🇬🇧','epic'),('🇩🇪','epic'),('🇫🇷','epic'),('🇮🇹','epic'),
    ('🇯🇵','epic'),('🇮🇳','epic'),
    ('🇺🇸','legendary'),('🇷🇺','legendary'),('🇨🇳','legendary'),
]

RARITY_NAMES = {
    'common': '⚪ Обычная',
    'rare': '🔵 Редкая',
    'epic': '🟣 Эпическая',
    'legendary': '🟡 Легендарная',
}
RARITY_WEIGHT = {'common': 60, 'rare': 25, 'epic': 12, 'legendary': 3}
RARITY_MIN_PRICE = {'common': 5, 'rare': 25, 'epic': 100, 'legendary': 500}
RARITY_MAX_PRICE = {'common': 50, 'rare': 200, 'epic': 1000, 'legendary': 10000}

SEASONS = {
    1:  {'name': '🍂 Осенний листопад', 'emoji': '🍁'},
    2:  {'name': '🌧️ Дождливый ноябрь', 'emoji': '🌧️'},
    3:  {'name': '🌫️ Туманы',           'emoji': '🌫️'},
    4:  {'name': '❄️ Первый снег',       'emoji': '❄️'},
    5:  {'name': '🎃 Хэллоуин',          'emoji': '🎃'},
    6:  {'name': '🕸️ Тёмная осень',      'emoji': '🕸️'},
    7:  {'name': '🍄 Грибной сезон',     'emoji': '🍄'},
    8:  {'name': '🌰 Урожай',            'emoji': '🌰'},
    9:  {'name': '🍷 Виноград',          'emoji': '🍷'},
    10: {'name': '🦔 Ёжики',             'emoji': '🦔'},
    11: {'name': '🐿️ Белки',             'emoji': '🐿️'},
    12: {'name': '🦌 Олени',             'emoji': '🦌'},
    13: {'name': '🐺 Волки',             'emoji': '🐺'},
    14: {'name': '🦉 Совы',              'emoji': '🦉'},
    15: {'name': '🐻 Медведи',           'emoji': '🐻'},
    16: {'name': '🦊 Лисы',              'emoji': '🦊'},
    17: {'name': '🐇 Зайцы',             'emoji': '🐇'},
    18: {'name': '🦇 Летучие мыши',      'emoji': '🦇'},
    19: {'name': '🕷️ Пауки',            'emoji': '🕷️'},
    20: {'name': '🍁 Клён',              'emoji': '🍁'},
    21: {'name': '🌲 Хвойный лес',       'emoji': '🌲'},
    22: {'name': '🌳 Дуб',               'emoji': '🌳'},
    23: {'name': '🍂 Листва',            'emoji': '🍂'},
    24: {'name': '🥧 Пироги',            'emoji': '🥧'},
    25: {'name': '☕ Чай',               'emoji': '☕'},
    26: {'name': '🍵 Какао',             'emoji': '🍵'},
    27: {'name': '🕯️ Свечи',            'emoji': '🕯️'},
    28: {'name': '📚 Книги',             'emoji': '📚'},
    29: {'name': '🎨 Краски осени',      'emoji': '🎨'},
    30: {'name': '👑 Финал сезона',      'emoji': '👑'},
}
SEASON_START = 1730419200

POINTS_PER_CASE_MIN = 100
POINTS_PER_CASE_MAX = 500
POINTS_PER_BONUS = 2000

MAX_LEVEL = 20
LEVEL_BASE = 5000
LEVEL_STEP = 2500

PASS_REWARDS = {
    1:  {'free': ('⭐', 50),   'premium': ('⭐', 200)},
    2:  {'free': ('⭐', 100),  'premium': ('🎁', 3)},
    3:  {'free': ('🎁', 2),   'premium': ('⭐', 300)},
    4:  {'free': ('⭐', 200),  'premium': ('🟣', 1)},
    5:  {'free': ('🟣', 1),   'premium': ('⭐', 500)},
    6:  {'free': ('⭐', 300),  'premium': ('🟣', 2)},
    7:  {'free': ('🎁', 3),   'premium': ('🟡', 1)},
    8:  {'free': ('⭐', 500),  'premium': ('🟡', 2)},
    9:  {'free': ('🟣', 1),   'premium': ('💎', 1)},
    10: {'free': ('🟡', 1),   'premium': ('👑', 2)},
    11: {'free': ('⭐', 700),  'premium': ('⭐', 1500)},
    12: {'free': ('🎁', 4),   'premium': ('🟣', 3)},
    13: {'free': ('⭐', 900),  'premium': ('🟡', 2)},
    14: {'free': ('🟣', 2),   'premium': ('💎', 2)},
    15: {'free': ('🟡', 1),   'premium': ('👑', 3)},
    16: {'free': ('⭐', 1200), 'premium': ('🟡', 3)},
    17: {'free': ('🎁', 5),   'premium': ('💎', 2)},
    18: {'free': ('🟣', 2),   'premium': ('👑', 3)},
    19: {'free': ('🟡', 2),   'premium': ('💎', 3)},
    20: {'free': ('💎', 1),   'premium': ('👑', 5)},
}

bot = telebot.TeleBot(TOKEN)
DB = 'gifts.db'


def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, name TEXT,
        last_case INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
        last_bonus INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 100,
        total_earned INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        username TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, flag TEXT, rarity TEXT, time INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_uid INTEGER, seller_name TEXT,
        flag TEXT, rarity TEXT, price INTEGER, time INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS season (
        uid INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
        premium INTEGER DEFAULT 0, claimed TEXT DEFAULT ''
    )''')
    conn.commit(); conn.close()

init_db()


def get_user(uid, name='Игрок'):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT uid, name, last_case, total, last_bonus, streak, stars, total_earned, total_spent FROM users WHERE uid=?', (uid,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO users (uid, name, stars) VALUES (?, ?, ?)', (uid, name, START_STARS))
        conn.commit()
        row = (uid, name, 0, 0, 0, 0, START_STARS, 0, 0)
    conn.close()
    return row


def update_user(uid, **kwargs):
    conn = sqlite3.connect(DB); c = conn.cursor()
    for k, v in kwargs.items():
        c.execute(f'UPDATE users SET {k}=? WHERE uid=?', (v, uid))
    conn.commit(); conn.close()


def add_gift(uid, flag, rarity):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT INTO gifts (uid, flag, rarity, time) VALUES (?, ?, ?, ?)',
              (uid, flag, rarity, int(time.time())))
    conn.commit(); conn.close()


def get_user_gifts(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT id, flag, rarity FROM gifts WHERE uid=? ORDER BY id DESC', (uid,))
    rows = c.fetchall(); conn.close()
    return rows


def get_user_stats(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT rarity, COUNT(*) FROM gifts WHERE uid=? GROUP BY rarity', (uid,))
    rows = dict(c.fetchall()); conn.close()
    return rows


def get_top_cases(limit=20):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT name, total FROM users ORDER BY total DESC LIMIT ?', (limit,))
    rows = c.fetchall(); conn.close()
    return rows


def get_top_spent(limit=20):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT name, total_spent FROM users ORDER BY total_spent DESC LIMIT ?', (limit,))
    rows = c.fetchall(); conn.close()
    return rows


def roll_country():
    rarity = random.choices(list(RARITY_WEIGHT.keys()), weights=list(RARITY_WEIGHT.values()))[0]
    pool = [c for c in COUNTRIES if c[1] == rarity]
    return random.choice(pool)


def min_price(r): return RARITY_MIN_PRICE.get(r, 5)
def max_price(r): return RARITY_MAX_PRICE.get(r, 100)


def get_current_season():
    days = int((time.time() - SEASON_START) / 86400) % 30
    return days + 1


def get_season_info():
    num = get_current_season()
    return num, SEASONS.get(num, SEASONS[1])


def points_for_level(level):
    return LEVEL_BASE + (level - 1) * LEVEL_STEP


def total_points_for_level(level):
    total = 0
    for i in range(1, level):
        total += points_for_level(i)
    return total


def get_level_from_points(points):
    level = 1
    acc = 0
    while level < MAX_LEVEL:
        need = points_for_level(level)
        if points < acc + need:
            break
        acc += need
        level += 1
    return level


def progress_in_level(points):
    level = get_level_from_points(points)
    if level >= MAX_LEVEL:
        return points, points, 1.0
    prev = total_points_for_level(level)
    in_lvl = points - prev
    need = points_for_level(level)
    return in_lvl, need, min(1.0, in_lvl / need)


def get_season(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT xp, level, premium, claimed FROM season WHERE uid=?', (uid,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO season (uid) VALUES (?)', (uid,))
        conn.commit()
        row = (0, 1, 0, '')
    conn.close()
    points = row[0]
    level = get_level_from_points(points)
    return points, level, row[2], row[3]


def update_season(uid, **kwargs):
    conn = sqlite3.connect(DB); c = conn.cursor()
    for k, v in kwargs.items():
        c.execute(f'UPDATE season SET {k}=? WHERE uid=?', (v, uid))
    conn.commit(); conn.close()


def add_xp(uid, amount):
    points, old_level, premium, claimed = get_season(uid)
    new_points = points + amount
    new_level = get_level_from_points(new_points)
    update_season(uid, xp=new_points, level=new_level)
    return new_level > old_level, new_level


def claim_reward(uid, level):
    points, cur_level, premium, claimed = get_season(uid)
    if cur_level < level:
        return None
    claimed_list = claimed.split(',') if claimed else []
    if str(level) in claimed_list:
        return 'already'
    reward = PASS_REWARDS.get(level)
    if not reward:
        return None
    free = reward['free']
    if free[0] == '⭐':
        user = get_user(uid)
        update_user(uid, stars=user[6] + free[1])
    elif free[0] == '🎁':
        for _ in range(free[1]):
            flag, rarity = roll_country()
            add_gift(uid, flag, rarity)
    if premium:
        prem = reward['premium']
        if prem[0] == '⭐':
            user = get_user(uid)
            update_user(uid, stars=user[6] + prem[1])
        elif prem[0] in ('🟣', '🟡', '👑', '💎'):
            for _ in range(prem[1]):
                flag, rarity = roll_country()
                add_gift(uid, flag, rarity)
    claimed_list.append(str(level))
    update_season(uid, claimed=','.join(claimed_list))
    return free, prem if premium else None


def main_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton('🎁 Открыть кейс', callback_data='menu_case', style='primary'))
    kb.add(
        types.InlineKeyboardButton('📦 Мои флаги', callback_data='menu_my'),
        types.InlineKeyboardButton('🛒 Аукцион', callback_data='menu_auction'),
    )
    kb.add(
        types.InlineKeyboardButton('💸 Продать', callback_data='menu_sell', style='success'),
        types.InlineKeyboardButton('💰 Баланс', callback_data='menu_balance'),
    )
    kb.add(types.InlineKeyboardButton('🏆 Топ игроков', callback_data='menu_top_app', style='primary'))
    kb.add(
        types.InlineKeyboardButton('🍂 Сезон', callback_data='menu_season'),
        types.InlineKeyboardButton('🎫 Пропуск', callback_data='menu_pass', style='success'),
    )
    kb.add(
        types.InlineKeyboardButton('🎁 Бонус дня', callback_data='menu_daily'),
        types.InlineKeyboardButton('📊 Стата', callback_data='menu_stats'),
    )
    return kb


@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Игрок'
    get_user(uid, name)
    text = (
        f'🎁 <b>Gift Bot</b>\n\n'
        f'Привет, <b>{name}</b>!\n\n'
        f'🎰 Кейс — раз в 2 минуты\n'
        f'💸 Продавай по своей цене\n'
        f'🏆 Открывай топ игроков\n\n'
        f'Выбирай 👇'
    )
    rm = types.ReplyKeyboardRemove()
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu(uid))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_top_app')
def cb_menu_top_app(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        '🏆 Открыть таблицу лидеров',
        web_app=types.WebAppInfo(url=WEBAPP_URL + '/top')
    ))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.edit_message_text(
        '🏆 <b>Топ игроков</b>\n\nОткрой таблицу лидеров:',
        c.message.chat.id, c.message.message_id,
        parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_menu_main(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    text = '🎁 <b>Gift Bot</b>\n\nВыбирай 👇'
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              parse_mode='HTML', reply_markup=main_menu(uid))
    except:
        bot.send_message(c.message.chat.id, text, parse_mode='HTML', reply_markup=main_menu(uid))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_case')
def cb_case(c):
    uid = c.from_user.id
    name = c.from_user.first_name or 'Игрок'
    user = get_user(uid, name)
    now = int(time.time())
    left = COOLDOWN - (now - user[2])
    if left > 0:
        bot.answer_callback_query(c.id, f'⏱️ {left // 60}:{left % 60:02d}', show_alert=True)
        return
    bot.answer_callback_query(c.id)
    update_user(uid, last_case=now)
    msg = bot.send_message(c.message.chat.id, '🎁 Открываем...')

    def animate():
        frames = [
            '🎰 <b>Крутим...</b>\n\n⬜⬜⬜⬜⬜',
            '🎰 <b>Крутим...</b>\n\n🟨⬜⬜⬜⬜',
            '🎰 <b>Крутим...</b>\n\n🟨🟨⬜⬜⬜',
            '🎰 <b>Крутим...</b>\n\n🟨🟨🟨⬜⬜',
            '🎰 <b>Крутим...</b>\n\n🟨🟨🟨🟨⬜',
            '✨ <b>Почти...</b>\n\n🟨🟨🟨🟨🟨',
        ]
        for frame in frames:
            try: bot.edit_message_text(frame, msg.chat.id, msg.message_id, parse_mode='HTML')
            except: pass
            time.sleep(0.6)

        flag, rarity = roll_country()
        add_gift(uid, flag, rarity)
        update_user(uid, total=user[3] + 1)
        points_gain = random.randint(POINTS_PER_CASE_MIN, POINTS_PER_CASE_MAX)
        leveled_up, new_level = add_xp(uid, points_gain)
        mn, mx = min_price(rarity), max_price(rarity)
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton('💸 Продать', callback_data='menu_sell', style='success'))
        kb.add(types.InlineKeyboardButton('🎁 Ещё кейс', callback_data='menu_case', style='primary'))
        kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
        result = (
            f'🎉 <b>Тебе выпало!</b>\n\n'
            f'<b>{flag} {flag} {flag}</b>\n\n'
            f'{RARITY_NAMES[rarity]}\n'
            f'💰 Цена: <b>{mn}-{mx} ⭐</b>\n'
            f'🎯 Очки: <b>+{points_gain}</b>'
        )
        try: bot.edit_message_text(result, msg.chat.id, msg.message_id, parse_mode='HTML', reply_markup=kb)
        except: pass
        if leveled_up:
            try: bot.send_message(msg.chat.id, f'🍂 <b>Уровень {new_level}!</b>', parse_mode='HTML')
            except: pass

    threading.Thread(target=animate).start()


@bot.callback_query_handler(func=lambda c: c.data == 'menu_my')
def cb_my(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    gifts = get_user_gifts(uid)
    if not gifts:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🎁 Открыть кейс', callback_data='menu_case', style='primary'))
        kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
        return bot.edit_message_text('📦 Пусто.', c.message.chat.id, c.message.message_id, reply_markup=kb)
    by_rarity = {'legendary': [], 'epic': [], 'rare': [], 'common': []}
    for _id, flag, rarity in gifts:
        by_rarity[rarity].append(flag)
    text = f'📦 <b>Коллекция</b> — {len(gifts)} флагов\n\n'
    for rarity in ['legendary', 'epic', 'rare', 'common']:
        flags = by_rarity[rarity]
        if not flags: continue
        unique = {}
        for f in flags: unique[f] = unique.get(f, 0) + 1
        text += f'<b>{RARITY_NAMES[rarity]}</b> · {len(flags)}\n'
        items = list(unique.items())
        for i in range(0, len(items), 6):
            line = ''
            for f, cnt in items[i:i+6]:
                line += f + (f'×{cnt}' if cnt > 1 else '') + ' '
            text += line + '\n'
        text += '\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('💸 Продать', callback_data='menu_sell', style='success'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.edit_message_text(text[:4000], c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


sell_states = {}

@bot.callback_query_handler(func=lambda c: c.data == 'menu_sell')
def cb_sell_menu(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    gifts = get_user_gifts(uid)
    if not gifts:
        return bot.answer_callback_query(c.id, 'Нет флагов', show_alert=True)
    unique = {}
    for gid, flag, rarity in gifts:
        key = (flag, rarity)
        if key not in unique: unique[key] = gid
    items = list(unique.items())[:30]
    kb = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f'{flag}', callback_data=f'sellpick_{gid}') for (flag, _), gid in items]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    try: bot.edit_message_text('💸 <b>Продажа</b>\n\nВыбери флаг:', c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('sellpick_'))
def cb_sellpick(c):
    uid = c.from_user.id
    gid = int(c.data.replace('sellpick_', ''))
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT flag, rarity FROM gifts WHERE id=? AND uid=?', (gid, uid))
    row = cur.fetchone(); conn.close()
    if not row:
        return bot.answer_callback_query(c.id, 'Не найдено', show_alert=True)
    flag, rarity = row
    mn, mx = min_price(rarity), max_price(rarity)
    sell_states[uid] = {'gid': gid, 'flag': flag, 'rarity': rarity}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,
        f'💸 <b>Установи цену</b>\n\n{flag} {flag} {flag}\n{RARITY_NAMES[rarity]}\n\n'
        f'💰 Мин: <b>{mn} ⭐</b>\n💰 Макс: <b>{mx} ⭐</b>\n\n✍️ Отправь число:',
        parse_mode='HTML')


@bot.message_handler(func=lambda m: m.from_user.id in sell_states, content_types=['text'])
def handle_price(m):
    uid = m.from_user.id
    state = sell_states.get(uid)
    if not state: return
    try: price = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Введи число')
    mn, mx = min_price(state['rarity']), max_price(state['rarity'])
    if price < mn or price > mx:
        return bot.send_message(m.chat.id, f'❌ Цена: от {mn} до {mx} ⭐')
    gid, flag = state['gid'], state['flag']
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT id FROM gifts WHERE id=? AND uid=?', (gid, uid))
    if not cur.fetchone():
        conn.close(); sell_states.pop(uid, None)
        return bot.send_message(m.chat.id, '❌ Флаг продан')
    cur.execute('DELETE FROM gifts WHERE id=?', (gid,))
    conn.commit(); conn.close()
    user = get_user(uid)
    new_stars = user[6] + price
    update_user(uid, stars=new_stars, total_earned=user[7] + price)
    add_xp(uid, min(500, price // 2))
    sell_states.pop(uid, None)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('💸 Ещё', callback_data='menu_sell', style='success'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.send_message(m.chat.id,
        f'✅ <b>Продано!</b>\n\n{flag} {flag} {flag}\n💰 +<b>{price} ⭐</b>\n💼 Баланс: <b>{new_stars} ⭐</b>',
        parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_auction')
def cb_auction(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT id, seller_name, flag, rarity, price FROM auctions WHERE seller_uid != ? ORDER BY price ASC LIMIT 30', (uid,))
    rows = cur.fetchall(); conn.close()
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not rows:
        kb.add(types.InlineKeyboardButton('💸 Выставить свой', callback_data='menu_list', style='success'))
    else:
        for aid, seller, flag, rarity, price in rows:
            kb.add(types.InlineKeyboardButton(f'{flag} {flag} — {price} ⭐ · {seller}', callback_data=f'buy_{aid}'))
        kb.add(types.InlineKeyboardButton('💸 Выставить свой', callback_data='menu_list', style='success'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    try: bot.edit_message_text('🛒 <b>Аукцион</b>', c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def cb_buy(c):
    uid = c.from_user.id
    aid = int(c.data.replace('buy_', ''))
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT seller_uid, flag, rarity, price FROM auctions WHERE id=?', (aid,))
    row = cur.fetchone()
    if not row:
        conn.close(); return bot.answer_callback_query(c.id, 'Продан', show_alert=True)
    seller_uid, flag, rarity, price = row
    if seller_uid == uid:
        conn.close(); return bot.answer_callback_query(c.id, 'Твой лот', show_alert=True)
    buyer = get_user(uid)
    if buyer[6] < price:
        conn.close(); return bot.answer_callback_query(c.id, f'Не хватает {price - buyer[6]} ⭐', show_alert=True)
    cur.execute('DELETE FROM auctions WHERE id=?', (aid,))
    cur.execute('INSERT INTO gifts (uid, flag, rarity, time) VALUES (?, ?, ?, ?)', (uid, flag, rarity, int(time.time())))
    conn.commit(); conn.close()
    update_user(uid, stars=buyer[6] - price, total_spent=buyer[8] + price)
    add_xp(uid, min(300, price // 3))
    seller = get_user(seller_uid)
    if seller:
        update_user(seller_uid, stars=seller[6] + price, total_earned=seller[7] + price)
        try: bot.send_message(seller_uid, f'💰 <b>Флаг продан!</b>\n\n{flag} {flag} {flag}\n+{price} ⭐', parse_mode='HTML')
        except: pass
    bot.answer_callback_query(c.id, f'✅ Куплено за {price} ⭐')
    cb_auction(c)


list_states = {}

@bot.callback_query_handler(func=lambda c: c.data == 'menu_list')
def cb_list_menu(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    gifts = get_user_gifts(uid)
    if not gifts: return bot.answer_callback_query(c.id, 'Нет флагов', show_alert=True)
    unique = {}
    for gid, flag, rarity in gifts:
        key = (flag, rarity)
        if key not in unique: unique[key] = gid
    items = list(unique.items())[:30]
    kb = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f'{flag}', callback_data=f'listpick_{gid}') for (flag, _), gid in items]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_auction'))
    try: bot.edit_message_text('📤 <b>На аукцион</b>\n\nВыбери флаг:', c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('listpick_'))
def cb_listpick(c):
    uid = c.from_user.id
    gid = int(c.data.replace('listpick_', ''))
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT flag, rarity FROM gifts WHERE id=? AND uid=?', (gid, uid))
    row = cur.fetchone(); conn.close()
    if not row: return bot.answer_callback_query(c.id, 'Не найдено', show_alert=True)
    flag, rarity = row
    mn, mx = min_price(rarity), max_price(rarity)
    list_states[uid] = {'gid': gid, 'flag': flag, 'rarity': rarity}
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,
        f'📤 <b>Цена лота</b>\n\n{flag} {flag} {flag}\n{RARITY_NAMES[rarity]}\n\n'
        f'💰 Мин: <b>{mn} ⭐</b>\n💰 Макс: <b>{mx} ⭐</b>\n\n✍️ Отправь число:',
        parse_mode='HTML')


@bot.message_handler(func=lambda m: m.from_user.id in list_states, content_types=['text'])
def handle_list_price(m):
    uid = m.from_user.id
    state = list_states.get(uid)
    if not state: return
    try: price = int(m.text.strip())
    except: return bot.send_message(m.chat.id, '❌ Введи число')
    mn, mx = min_price(state['rarity']), max_price(state['rarity'])
    if price < mn or price > mx:
        return bot.send_message(m.chat.id, f'❌ Цена: от {mn} до {mx} ⭐')
    gid, flag, rarity = state['gid'], state['flag'], state['rarity']
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute('SELECT id FROM gifts WHERE id=? AND uid=?', (gid, uid))
    if not cur.fetchone():
        conn.close(); list_states.pop(uid, None)
        return bot.send_message(m.chat.id, '❌ Флаг продан')
    name = m.from_user.first_name or 'Игрок'
    cur.execute('DELETE FROM gifts WHERE id=?', (gid,))
    cur.execute('INSERT INTO auctions (seller_uid, seller_name, flag, rarity, price, time) VALUES (?, ?, ?, ?, ?, ?)',
                (uid, name, flag, rarity, price, int(time.time())))
    conn.commit(); conn.close()
    list_states.pop(uid, None)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🛒 Аукцион', callback_data='menu_auction', style='primary'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.send_message(m.chat.id,
        f'✅ <b>Выставлено!</b>\n\n{flag} {flag} {flag}\n💰 Цена: <b>{price} ⭐</b>',
        parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_balance')
def cb_balance(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    user = get_user(uid)
    gifts = get_user_gifts(uid)
    collection = sum(min_price(r) for _, _, r in gifts)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    text = (
        f'💰 <b>Баланс</b>\n\n'
        f'💵 Звёзды: <b>{user[6]} ⭐</b>\n'
        f'📈 Заработано: <b>{user[7]} ⭐</b>\n'
        f'📉 Потрачено: <b>{user[8]} ⭐</b>\n\n'
        f'📦 Флагов: <b>{len(gifts)}</b>\n'
        f'💎 Мин. стоимость: <b>{collection} ⭐</b>'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_top_cases')
def cb_top_cases(c):
    top = get_top_cases(20)
    text = '🏆 <b>Топ по кейсам</b>\n\n'
    if not top: text += '<i>Пусто</i>'
    else:
        quote = ''
        for i, (name, total) in enumerate(top, 1):
            medal = ['🥇','🥈','🥉'][i-1] if i <= 3 else f'{i}.'
            if i <= 3: quote += f'{medal} <b>{name}</b> · {total} ⚡\n'
            else: quote += f'{medal} {name} · {total} ⚡\n'
        text += f'<blockquote>{quote}</blockquote>'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('💎 Топ трат', callback_data='menu_top_spent', style='primary'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_top_spent')
def cb_top_spent(c):
    top = get_top_spent(20)
    text = '💎 <b>Топ по тратам</b>\n\n'
    if not top: text += '<i>Пусто</i>'
    else:
        quote = ''
        for i, (name, spent) in enumerate(top, 1):
            medal = ['🥇','🥈','🥉'][i-1] if i <= 3 else f'{i}.'
            if i <= 3: quote += f'{medal} <b>{name}</b> · {spent} ⭐\n'
            else: quote += f'{medal} {name} · {spent} ⭐\n'
        text += f'<blockquote>{quote}</blockquote>'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🏆 Топ кейсов', callback_data='menu_top_cases', style='primary'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.answer_callback_query(c.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_season')
def cb_season(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    points, level, premium, claimed = get_season(uid)
    season_num, season = get_season_info()
    in_lvl, need, progress = progress_in_level(points)
    bar = '🟨' * int(progress * 10) + '⬜' * (10 - int(progress * 10))
    status = '🏆 МАКСИМУМ' if level >= MAX_LEVEL else f'{bar}\n{in_lvl:,} / {need:,}'
    text = (
        f'{season["emoji"]} <b>{season["name"]}</b>\n'
        f'📅 Сезон: <b>{season_num}/30</b>\n\n'
        f'🎯 Уровень: <b>{level}/{MAX_LEVEL}</b>\n{status}\n\n'
        f'⭐ Очков: <b>{points:,}</b>\n'
        f'🎫 Премиум: {"✅" if premium else "❌"}'
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🎫 Пропуск', callback_data='menu_pass', style='success'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_pass')
def cb_pass(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    points, level, premium, claimed = get_season(uid)
    claimed_list = claimed.split(',') if claimed else []
    season_num, season = get_season_info()
    in_lvl, need, progress = progress_in_level(points)
    text = f'🎫 <b>Пропуск</b>\n{season["emoji"]} {season["name"]} · {season_num}/30\n\n🎯 Уровень: <b>{level}/{MAX_LEVEL}</b>\n'
    if level < MAX_LEVEL: text += f'📊 {in_lvl:,} / {need:,}\n'
    text += '\n'
    for lvl in range(1, MAX_LEVEL + 1):
        reward = PASS_REWARDS.get(lvl)
        if not reward: continue
        free, prem = reward['free'], reward['premium']
        f_str = f'{free[0]}×{free[1]}' if free[1] > 1 else f'{free[0]}'
        p_str = f'{prem[0]}×{prem[1]}' if prem[1] > 1 else f'{prem[0]}'
        need_lvl = total_points_for_level(lvl)
        status = '✅' if str(lvl) in claimed_list else ('🎁' if lvl <= level else '🔒')
        text += f'{status} <b>Ур.{lvl}</b> ({need_lvl:,}) · {f_str} / {p_str}\n'
    kb = types.InlineKeyboardMarkup(row_width=5)
    btns = []
    for lvl in range(1, MAX_LEVEL + 1):
        if str(lvl) in claimed_list:
            btns.append(types.InlineKeyboardButton(f'✅{lvl}', callback_data=f'claim_{lvl}'))
        elif lvl <= level:
            btns.append(types.InlineKeyboardButton(f'🎁{lvl}', callback_data=f'claim_{lvl}', style='success'))
        else:
            btns.append(types.InlineKeyboardButton(f'🔒{lvl}', callback_data='locked'))
    kb.add(*btns)
    if not premium:
        kb.add(types.InlineKeyboardButton('💎 Премиум (500 ⭐)', callback_data='buy_premium', style='primary'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    if len(text) > 4000: text = text[:3900] + '...'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'locked')
def cb_locked(c): bot.answer_callback_query(c.id, '🔒', show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith('claim_'))
def cb_claim(c):
    uid = c.from_user.id
    lvl = int(c.data.replace('claim_', ''))
    result = claim_reward(uid, lvl)
    if result == 'already':
        return bot.answer_callback_query(c.id, '✅ Уже', show_alert=True)
    if result is None:
        return bot.answer_callback_query(c.id, '❌ Нельзя', show_alert=True)
    free, prem = result
    bot.answer_callback_query(c.id, f'🎁 +{free[0]}×{free[1]}', show_alert=True)
    cb_pass(c)


@bot.callback_query_handler(func=lambda c: c.data == 'buy_premium')
def cb_buy_premium(c):
    uid = c.from_user.id
    user = get_user(uid)
    points, level, premium, claimed = get_season(uid)
    if premium: return bot.answer_callback_query(c.id, '✅ Куплен', show_alert=True)
    if user[6] < 500: return bot.answer_callback_query(c.id, '❌ Нужно 500 ⭐', show_alert=True)
    update_user(uid, stars=user[6] - 500, total_spent=user[8] + 500)
    update_season(uid, premium=1)
    bot.answer_callback_query(c.id, '🎫 Активирован!', show_alert=True)
    cb_pass(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_stats')
def cb_stats(c):
    uid = c.from_user.id
    bot.answer_callback_query(c.id)
    user = get_user(uid)
    stats = get_user_stats(uid)
    now = int(time.time())
    left = max(0, COOLDOWN - (now - user[2]))
    points, level, premium, claimed = get_season(uid)
    in_lvl, need_lvl, lvl_progress = progress_in_level(points)
    lvl_bar = '🟨' * int(lvl_progress * 10) + '⬜' * (10 - int(lvl_progress * 10))
    total_possible = len(set(c[0] for c in COUNTRIES))
    unique_have = len(set(flag for _, flag, _ in get_user_gifts(uid)))
    progress = int((unique_have / total_possible) * 100) if total_possible else 0
    coll_bar = '🟩' * int(progress / 10) + '⬜' * (10 - int(progress / 10))
    lvl_status = '🏆 МАКСИМУМ' if level >= MAX_LEVEL else f'{lvl_bar}\n{in_lvl:,} / {need_lvl:,} очков'
    text = (
        f'📊 <b>Статистика</b>\n\n'
        f'👤 <b>{user[1]}</b>\n\n'
        f'<b>🎯 Уровень: {level}/{MAX_LEVEL}</b>\n{lvl_status}\n\n'
        f'<b>📦 Коллекция</b>\n{coll_bar} {progress}%\n'
        f'Уникальных: {unique_have}/{total_possible}\n\n'
        f'🟡 Legendary — {stats.get("legendary", 0)}\n'
        f'🟣 Epic — {stats.get("epic", 0)}\n'
        f'🔵 Rare — {stats.get("rare", 0)}\n'
        f'⚪ Common — {stats.get("common", 0)}\n'
        f'━━━━━━━━━━━━━━\n'
        f'📦 Всего: <b>{user[3]}</b>\n'
        f'💰 Звёзды: <b>{user[6]} ⭐</b>\n\n'
    )
    if left == 0: text += '🎁 Кейс: <b>готов</b>'
    else: text += f'⏱️ Кейс: <b>{left // 60}:{left % 60:02d}</b>'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_daily')
def cb_daily(c):
    uid = c.from_user.id
    name = c.from_user.first_name or 'Игрок'
    user = get_user(uid, name)
    now = int(time.time())
    if now - user[4] < 86400:
        left = 86400 - (now - user[4])
        bot.answer_callback_query(c.id, f'⏳ {left // 3600}ч {(left % 3600) // 60}м', show_alert=True)
        return
    streak = user[5] + 1 if now - user[4] < 172800 else 1
    rewards = min(streak, 5)
    bonus_stars = 50 * streak
    for _ in range(rewards):
        flag, rarity = roll_country()
        add_gift(uid, flag, rarity)
    update_user(uid, total=user[3] + rewards, last_bonus=now, streak=streak, stars=user[6] + bonus_stars)
    add_xp(uid, POINTS_PER_BONUS)
    bot.answer_callback_query(c.id, f'🎁 +{rewards} флагов, +{bonus_stars} ⭐', show_alert=True)
    cb_menu_main(c)


if __name__ == '__main__':
    print('Bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
