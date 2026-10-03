import telebot
import sqlite3
import time
import random
import threading
from telebot import types

TOKEN = '8471116013:AAEXY8F8ZHnA-qTAenLdfLzWSRIQEHvRWoQ'
COOLDOWN = 120

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
    ('🇯🇵','epic'),('🇮🇳','epic'),('🇧🇷','epic'),('🇨🇦','epic'),
    ('🇦🇺','epic'),('🇪🇸','epic'),('🇲🇽','epic'),('🇰🇷','epic'),

    ('🇺🇸','legendary'),('🇷🇺','legendary'),('🇨🇳','legendary'),
]

RARITY_NAMES = {
    'common': '⚪ Обычная',
    'rare': '🔵 Редкая',
    'epic': '🟣 Эпическая',
    'legendary': '🟡 Легендарная',
}
RARITY_WEIGHT = {'common': 60, 'rare': 25, 'epic': 12, 'legendary': 3}

ACHIEVEMENTS = {
    'first':        {'name': '🎁 Первый флаг',   'desc': 'Открой первый кейс'},
    'ten':          {'name': '🔟 Десятка',       'desc': 'Собери 10 флагов'},
    'fifty':        {'name': '📦 Коллекционер',  'desc': 'Собери 50 флагов'},
    'epic_first':   {'name': '🟣 Эпик',          'desc': 'Выбей первый эпик'},
    'legend_first': {'name': '🟡 Легенда',       'desc': 'Выбей первую легенду'},
    'legend_three': {'name': '👑 Король легенд', 'desc': 'Выбей 3 легенды'},
}

bot = telebot.TeleBot(TOKEN)
DB = 'gifts.db'


def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, name TEXT,
        last_case INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
        last_bonus INTEGER DEFAULT 0, streak INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, flag TEXT, rarity TEXT, time INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        uid INTEGER, key TEXT, time INTEGER, PRIMARY KEY (uid, key)
    )''')
    conn.commit(); conn.close()

init_db()


def get_user(uid, name='Игрок'):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT uid, name, last_case, total, last_bonus, streak FROM users WHERE uid=?', (uid,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO users (uid, name) VALUES (?, ?)', (uid, name))
        conn.commit()
        row = (uid, name, 0, 0, 0, 0)
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
    c.execute('SELECT flag, rarity FROM gifts WHERE uid=? ORDER BY id DESC', (uid,))
    rows = c.fetchall(); conn.close()
    return rows


def get_user_stats(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT rarity, COUNT(*) FROM gifts WHERE uid=? GROUP BY rarity', (uid,))
    rows = dict(c.fetchall()); conn.close()
    return rows


def get_top(limit=10):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('''SELECT u.name, u.total,
                 (SELECT COUNT(*) FROM gifts WHERE uid=u.uid AND rarity='legendary'),
                 (SELECT COUNT(*) FROM gifts WHERE uid=u.uid AND rarity='epic')
                 FROM users u ORDER BY u.total DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close()
    return rows


def get_achievements(uid):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('SELECT key FROM achievements WHERE uid=?', (uid,))
    rows = [r[0] for r in c.fetchall()]; conn.close()
    return rows


def add_achievement(uid, key):
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO achievements (uid, key, time) VALUES (?, ?, ?)',
              (uid, key, int(time.time())))
    conn.commit(); conn.close()


def check_achievements(uid):
    gifts = get_user_gifts(uid)
    stats = get_user_stats(uid)
    have = get_achievements(uid)
    new = []
    if 'first' not in have and len(gifts) >= 1:
        add_achievement(uid, 'first'); new.append('first')
    if 'ten' not in have and len(gifts) >= 10:
        add_achievement(uid, 'ten'); new.append('ten')
    if 'fifty' not in have and len(gifts) >= 50:
        add_achievement(uid, 'fifty'); new.append('fifty')
    if 'epic_first' not in have and stats.get('epic', 0) >= 1:
        add_achievement(uid, 'epic_first'); new.append('epic_first')
    if 'legend_first' not in have and stats.get('legendary', 0) >= 1:
        add_achievement(uid, 'legend_first'); new.append('legend_first')
    if 'legend_three' not in have and stats.get('legendary', 0) >= 3:
        add_achievement(uid, 'legend_three'); new.append('legend_three')
    return new


def roll_country():
    rarity = random.choices(list(RARITY_WEIGHT.keys()), weights=list(RARITY_WEIGHT.values()))[0]
    pool = [c for c in COUNTRIES if c[1] == rarity]
    return random.choice(pool)


def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add('🎁 Открыть кейс', '📦 Мои флаги')
    kb.add('📊 Статистика', '🏆 Топ игроков')
    kb.add('🏅 Достижения', '🎁 Бонус дня')
    return kb


# ============================================================
# START
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Игрок'
    get_user(uid, name)

    text = (
        f'🎁 <b>Gift Bot</b>\n\n'
        f'Привет, <b>{name}</b>!\n\n'
        f'Открывай кейсы, собирай флаги стран, соревнуйся с другими.\n\n'
        f'🎰 Кейс — раз в 2 минуты\n'
        f'🏅 Достижения — за коллекцию\n'
        f'🎁 Бонус дня — каждый день\n\n'
        f'Жми кнопку ниже 👇'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())


# ============================================================
# КЕЙС
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎁 Открыть кейс')
def cmd_open_case(m):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Игрок'
    user = get_user(uid, name)
    last_case = user[2]
    now = int(time.time())

    left = COOLDOWN - (now - last_case)
    if left > 0:
        mins = left // 60
        secs = left % 60
        text = (
            f'⏱️ <b>Кейс остывает</b>\n\n'
            f'Осталось: <b>{mins}:{secs:02d}</b>\n\n'
            f'Возвращайся скорее!'
        )
        bot.send_message(m.chat.id, text, parse_mode='HTML')
        return

    update_user(uid, last_case=now)
    msg = bot.send_message(m.chat.id, '🎁 Открываем...')

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
            try:
                bot.edit_message_text(frame, m.chat.id, msg.message_id, parse_mode='HTML')
            except: pass
            time.sleep(0.6)

        flag, rarity = roll_country()
        add_gift(uid, flag, rarity)
        update_user(uid, total=user[3] + 1)

        result = (
            f'🎉 <b>Тебе выпало!</b>\n\n'
            f'<b>{flag} {flag} {flag}</b>\n\n'
            f'{RARITY_NAMES[rarity]}\n\n'
            f'⏱️ Следующий кейс через 2 минуты'
        )
        try:
            bot.edit_message_text(result, m.chat.id, msg.message_id, parse_mode='HTML')
        except: pass

        new = check_achievements(uid)
        for key in new:
            ach = ACHIEVEMENTS[key]
            try:
                bot.send_message(m.chat.id,
                    f'🏅 <b>Новое достижение!</b>\n\n{ach["name"]}\n<i>{ach["desc"]}</i>',
                    parse_mode='HTML')
            except: pass

    threading.Thread(target=animate).start()


# ============================================================
# МОИ ФЛАГИ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📦 Мои флаги')
def cmd_my_gifts(m):
    uid = m.from_user.id
    gifts = get_user_gifts(uid)
    if not gifts:
        return bot.send_message(m.chat.id, '📦 У тебя пока нет флагов.\n\nОткрой первый кейс!', reply_markup=main_kb())

    by_rarity = {'legendary': [], 'epic': [], 'rare': [], 'common': []}
    for flag, rarity in gifts:
        by_rarity[rarity].append(flag)

    text = f'📦 <b>Твоя коллекция</b> — {len(gifts)} флагов\n\n'

    for rarity in ['legendary', 'epic', 'rare', 'common']:
        flags = by_rarity[rarity]
        if not flags:
            continue
        unique = {}
        for f in flags:
            unique[f] = unique.get(f, 0) + 1
        text += f'<b>{RARITY_NAMES[rarity]}</b> · {len(flags)}\n'
        items = list(unique.items())
        for i in range(0, len(items), 6):
            row = items[i:i+6]
            line = ''
            for f, cnt in row:
                cell = f
                if cnt > 1:
                    cell += f'×{cnt}'
                line += f'{cell} '
            text += line + '\n'
        text += '\n'

    if len(text) > 4000:
        text = text[:3900] + '\n\n...показаны не все'
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())


# ============================================================
# СТАТИСТИКА
# ============================================================
@bot.message_handler(func=lambda m: m.text == '📊 Статистика')
def cmd_stats(m):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Игрок'
    user = get_user(uid, name)
    stats = get_user_stats(uid)
    total = user[3]
    last_case = user[2]
    now = int(time.time())
    left = max(0, COOLDOWN - (now - last_case))

    total_possible = len(set(c[0] for c in COUNTRIES))
    unique_have = len(set(flag for flag, _ in get_user_gifts(uid)))
    progress = int((unique_have / total_possible) * 100) if total_possible else 0
    bar_filled = int(progress / 10)
    bar = '🟩' * bar_filled + '⬜' * (10 - bar_filled)

    text = (
        f'📊 <b>Статистика</b>\n\n'
        f'👤 <b>{name}</b>\n\n'
        f'<b>Прогресс коллекции</b>\n'
        f'{bar} {progress}%\n'
        f'Уникальных: {unique_have}/{total_possible}\n\n'
        f'<b>По редкости</b>\n'
        f'🟡 Legendary — {stats.get("legendary", 0)}\n'
        f'🟣 Epic — {stats.get("epic", 0)}\n'
        f'🔵 Rare — {stats.get("rare", 0)}\n'
        f'⚪ Common — {stats.get("common", 0)}\n'
        f'━━━━━━━━━━━━━━\n'
        f'📦 Всего: <b>{total}</b>\n\n'
    )
    if left == 0:
        text += '🎁 Кейс: <b>готов</b>'
    else:
        text += f'⏱️ Кейс через: <b>{left // 60}:{left % 60:02d}</b>'

    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())


# ============================================================
# ТОП
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏆 Топ игроков')
def cmd_top(m):
    top = get_top(10)
    if not top:
        return bot.send_message(m.chat.id, '🏆 Пока никто не играл.', reply_markup=main_kb())

    text = '🏆 <b>Топ игроков</b>\n\n'
    for i, (name, total, legend, epic) in enumerate(top, 1):
        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'<b>{i}.</b>'
        extra = ''
        if legend or epic:
            extra = f' · 🟡{legend} 🟣{epic}'
        text += f'{medal} <b>{name}</b> — {total} 📦{extra}\n'

    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🏅 Достижения')
def cmd_achievements(m):
    uid = m.from_user.id
    have = get_achievements(uid)

    text = f'🏅 <b>Достижения</b> — {len(have)}/{len(ACHIEVEMENTS)}\n\n'
    for key, ach in ACHIEVEMENTS.items():
        done = '✅' if key in have else '🔒'
        text += f'{done} <b>{ach["name"]}</b>\n'
        text += f'    <i>{ach["desc"]}</i>\n\n'

    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())


# ============================================================
# БОНУС ДНЯ
# ============================================================
@bot.message_handler(func=lambda m: m.text == '🎁 Бонус дня')
def cmd_daily(m):
    uid = m.from_user.id
    name = m.from_user.first_name or 'Игрок'
    user = get_user(uid, name)
    last_bonus = user[4]
    streak = user[5]
    now = int(time.time())

    if now - last_bonus < 86400:
        left = 86400 - (now - last_bonus)
        h = left // 3600
        mn = (left % 3600) // 60
        text = (
            f'🎁 <b>Бонус дня</b>\n\n'
            f'⏳ Уже получен!\n\n'
            f'Осталось: <b>{h} ч {mn} мин</b>\n'
            f'🔥 Стрик: <b>{streak} дней</b>'
        )
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())
        return

    if now - last_bonus < 172800:
        streak += 1
    else:
        streak = 1

    reward = min(streak, 5)
    for _ in range(reward):
        flag, rarity = roll_country()
        add_gift(uid, flag, rarity)
    update_user(uid, total=user[3] + reward, last_bonus=now, streak=streak)

    text = (
        f'🎁 <b>Бонус дня</b>\n\n'
        f'🎉 Ты получил <b>{reward}</b> флагов!\n\n'
        f'🔥 Стрик: <b>{streak} дней</b>\n'
        f'💡 Заходи каждый день — награда растёт!\n\n'
        f'⏰ Следующий бонус через 24 часа'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_kb())
    check_achievements(uid)


# ============================================================
# КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['roll'])
def cmd_roll(m): cmd_open_case(m)

@bot.message_handler(commands=['top'])
def cmd_top_short(m): cmd_top(m)

@bot.message_handler(commands=['my'])
def cmd_my_short(m): cmd_my_gifts(m)

@bot.message_handler(commands=['daily'])
def cmd_daily_short(m): cmd_daily(m)


if __name__ == '__main__':
    print('Gift bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
