import telebot
from telebot import types
import sqlite3
import random
import time
import os
from datetime import datetime

TOKEN = '8872773404:AAGYxkiXGG8qwqIglIJwqnf6EkNBh4cPPDA'
bot = telebot.TeleBot(TOKEN)

DB = 'database.db'
COOLDOWN = 3600  # 1 час

# ---------- БАЗА ----------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            irises INTEGER DEFAULT 0,
            diamonds INTEGER DEFAULT 0,
            last_case INTEGER DEFAULT 0,
            current_id TEXT DEFAULT NULL,
            inventory TEXT DEFAULT '',
            reg_date INTEGER DEFAULT 0,
            cases_opened INTEGER DEFAULT 0,
            mission_day TEXT DEFAULT '',
            missions_done TEXT DEFAULT '',
            mission_progress TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id, username='', first_name=''):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''SELECT irises, diamonds, last_case, current_id, inventory,
                          reg_date, cases_opened, mission_day, missions_done, mission_progress
                   FROM users WHERE user_id=?''', (user_id,))
    row = cur.fetchone()
    if row is None:
        now = int(time.time())
        cur.execute('INSERT INTO users (user_id, username, first_name, reg_date) VALUES (?, ?, ?, ?)',
                    (user_id, username, first_name, now))
        conn.commit()
        row = (0, 0, 0, None, '', now, 0, '', '', '')
    else:
        cur.execute('UPDATE users SET username=?, first_name=? WHERE user_id=?',
                    (username, first_name, user_id))
        conn.commit()
    conn.close()
    return {
        'irises': row[0], 'diamonds': row[1], 'last_case': row[2], 'current_id': row[3],
        'inventory': row[4], 'reg_date': row[5], 'cases_opened': row[6],
        'mission_day': row[7], 'missions_done': row[8], 'mission_progress': row[9]
    }

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for key, val in kwargs.items():
        cur.execute(f'UPDATE users SET {key}=? WHERE user_id=?', (val, user_id))
    conn.commit()
    conn.close()

def get_top(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT user_id, first_name, username, irises FROM users ORDER BY irises DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_rank(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*)+1 FROM users WHERE irises > (SELECT irises FROM users WHERE user_id=?)', (user_id,))
    rank = cur.fetchone()[0]
    conn.close()
    return rank

def get_total_users():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    n = cur.fetchone()[0]
    conn.close()
    return n

init_db()

# ---------- МАГАЗИН ----------
SHOP = [
    {'id': '1001001', 'price': 50,   'name': 'Обычный ID'},
    {'id': '1002002', 'price': 100,  'name': 'Редкий ID'},
    {'id': '1003003', 'price': 150,  'name': 'Редкий ID+'},
    {'id': '1004004', 'price': 250,  'name': 'Эпический ID'},
    {'id': '1005005', 'price': 400,  'name': 'Эпический ID+'},
    {'id': '1006006', 'price': 600,  'name': 'Легендарный ID'},
    {'id': '1007007', 'price': 900,  'name': 'Мифический ID'},
    {'id': '1008008', 'price': 1500, 'name': 'Божественный ID'},
    {'id': '6666666', 'price': 2000, 'name': 'Дьявольский ID'},
    {'id': '8886665', 'price': 3500, 'name': 'Проклятый ID'},
    {'id': '0000001', 'price': 5000, 'name': 'Первый ID'},
    {'id': '0009000', 'price': 7777, 'name': 'Ангельский ID'},
]

# ---------- МИССИИ СЕЗОНА DARKGRAM ----------
# 8 миссий в пуле, каждый день выдаётся 5 случайных
MISSIONS_POOL = [
    {'key': 'open_case',   'name': 'Открой 1 кейс ID',        'goal': 1,  'reward': 10, 'type': 'open_case'},
    {'key': 'open_3case',  'name': 'Открой 3 кейса ID',        'goal': 3,  'reward': 25, 'type': 'open_case'},
    {'key': 'open_5case',  'name': 'Открой 5 кейсов ID',       'goal': 5,  'reward': 50, 'type': 'open_case'},
    {'key': 'buy_1',       'name': 'Купи 1 ID в магазине',     'goal': 1,  'reward': 30, 'type': 'buy'},
    {'key': 'buy_2',       'name': 'Купи 2 ID в магазине',     'goal': 2,  'reward': 60, 'type': 'buy'},
    {'key': 'earn_100',    'name': 'Заработай 100 ирисок',     'goal': 100,'reward': 20, 'type': 'earn_irises'},
    {'key': 'check_top',   'name': 'Посмотри топ игроков',     'goal': 1,  'reward': 5,  'type': 'check_top'},
    {'key': 'check_prof',  'name': 'Открой свой профиль',      'goal': 1,  'reward': 5,  'type': 'check_profile'},
]

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def get_daily_missions(user_id):
    """Возвращает 5 миссий на сегодня для юзера."""
    u = get_user(user_id)
    today = today_str()

    if u['mission_day'] != today:
        # Новый день — выбираем 5 случайных миссий
        chosen = random.sample(MISSIONS_POOL, 5)
        keys = ','.join(m['key'] for m in chosen)
        progress = ','.join('0' for _ in chosen)
        update_user(user_id, mission_day=today, missions_done='', mission_progress=progress)
        return chosen, [0]*5, [False]*5

    # Уже есть миссии на сегодня — берём те, что сохранены
    done_keys = set(u['missions_done'].split(',')) if u['missions_done'] else set()
    progress_list = [int(x) for x in u['mission_progress'].split(',')] if u['mission_progress'] else []

    # Восстанавливаем список миссий по ключам — но у нас сохранены только прогрессы.
    # Проще: сохраним ключи тоже. Добавим поле missions_keys через простой трюк —
    # будем хранить ключи в missions_done как "key|done" неудобно. 
    # Поэтому храним ключи в mission_day как "date|key1,key2,..."
    # Но чтобы не усложнять — пересоберём так: используем mission_day = "date|keys"
    if '|' in u['mission_day']:
        keys = u['mission_day'].split('|')[1].split(',')
    else:
        # fallback: заново выдаём
        chosen = random.sample(MISSIONS_POOL, 5)
        keys = [m['key'] for m in chosen]
        update_user(user_id, mission_day=f"{today}|{','.join(keys)}", missions_done='', mission_progress='0,0,0,0,0')
        return chosen, [0]*5, [False]*5

    missions = []
    for k in keys:
        for m in MISSIONS_POOL:
            if m['key'] == k:
                missions.append(m)
                break

    while len(progress_list) < len(missions):
        progress_list.append(0)

    return missions, progress_list, [k in done_keys for k in keys]

def add_mission_progress(user_id, mission_type, amount=1):
    """Двигает прогресс миссий нужного типа."""
    missions, progress, done = get_daily_missions(user_id)
    u = get_user(user_id)
    keys = [m['key'] for m in missions]
    changed = False

    for i, m in enumerate(missions):
        if done[i]:
            continue
        if m['type'] != mission_type:
            continue
        progress[i] += amount
        if progress[i] >= m['goal']:
            progress[i] = m['goal']
            done[i] = True
            # Начисляем алмазы
            u2 = get_user(user_id)
            update_user(user_id, diamonds=u2['diamonds'] + m['reward'])
            try:
                bot.send_message(user_id,
                    f'🎯 *Миссия выполнена!*\n{m["name"]}\n💠 +{m["reward"]} алмазов',
                    parse_mode='Markdown')
            except Exception:
                pass
        changed = True

    if changed:
        done_keys = ','.join(keys[i] for i in range(len(keys)) if done[i])
        progress_str = ','.join(str(p) for p in progress)
        update_user(user_id,
                    missions_done=done_keys,
                    mission_progress=progress_str,
                    mission_day=f"{today_str()}|{','.join(keys)}")

def mark_mission_done(user_id, mission_type):
    """Для миссий 'сделай 1 раз'."""
    add_mission_progress(user_id, mission_type, 1)

# ---------- КЛАВИАТУРА ----------
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('🎲 Верификация ID', '🛒 Магазин')
    kb.add('👤 Профиль', '🏆 Топ игроков')
    kb.add('🌑 Сезон Darkgram')
    return kb

# ---------- /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id,
             message.from_user.username or '',
             message.from_user.first_name or '')
    bot.send_message(
        message.chat.id,
        '👋 Добро пожаловать в *ID Верификацию*!\n\n'
        '🎲 Открывай кейсы — получай случайные ID\n'
        '🛒 В магазине 12 ID за ириски\n'
        '🌑 Сезон Darkgram — выполняй миссии, получай алмазы\n'
        '🏆 Соревнуйся за топ',
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

# ---------- ПРОФИЛЬ ----------
@bot.message_handler(func=lambda m: m.text and 'Профиль' in m.text or (m.text == '/profile'))
def profile(message):
    u = get_user(message.from_user.id,
                 message.from_user.username or '',
                 message.from_user.first_name or '')
    rank = get_rank(message.from_user.id)
    total = get_total_users()
    name = message.from_user.first_name or 'Игрок'
    username = f'@{message.from_user.username}' if message.from_user.username else '—'
    reg = time.strftime('%d.%m.%Y', time.localtime(u['reg_date']))

    text = (
        f'👤 *Профиль игрока*\n\n'
        f'🪪 Имя: *{name}*\n'
        f'🔗 Юзернейм: {username}\n'
        f'🆔 Telegram ID: `{message.from_user.id}`\n\n'
        f'💎 Ириски: `{u["irises"]}`\n'
        f'💠 Алмазы: `{u["diamonds"]}`\n'
        f'🎲 Открыто кейсов: `{u["cases_opened"]}`\n'
        f'🎁 Текущий ID: `{u["current_id"] or "нет"}`\n'
        f'📦 Инвентарь: `{u["inventory"] or "пусто"}`\n\n'
        f'🏆 Место в топе: *{rank}* из *{total}*\n'
        f'📅 Регистрация: `{reg}`'
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    mark_mission_done(message.from_user.id, 'check_profile')

# ---------- ТОП ----------
@bot.message_handler(func=lambda m: m.text and 'Топ' in m.text or (m.text == '/top'))
def top(message):
    rows = get_top(10)
    if not rows:
        bot.send_message(message.chat.id, 'Топ пока пуст.')
        return

    medals = ['🥇', '🥈', '🥉'] + ['▫️'] * 7
    text = '🏆 *Топ-10 игроков по ирискам*\n\n'
    for i, (uid, first_name, username, irises) in enumerate(rows):
        name = first_name or 'Игрок'
        if username:
            name += f' (@{username})'
        text += f'{medals[i]} {i+1}. {name} — 💎 `{irises}`\n'

    me_rank = get_rank(message.from_user.id)
    me = get_user(message.from_user.id)
    if me_rank > 10:
        text += f'\n...\n📍 Ты на *{me_rank}* месте — 💎 `{me["irises"]}`'

    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    mark_mission_done(message.from_user.id, 'check_top')

# ---------- СЕЗОН DARKGRAM ----------
@bot.message_handler(func=lambda m: m.text and 'Darkgram' in m.text or (m.text == '/season'))
def season(message):
    user_id = message.from_user.id
    missions, progress, done = get_daily_missions(user_id)
    u = get_user(user_id)

    text = f'🌑 *Сезон Darkgram*\n💠 Алмазов: `{u["diamonds"]}`\n\n'
    text += '*Миссии на сегодня (5):*\n\n'

    for i, m in enumerate(missions):
        mark = '✅' if done[i] else '⬜'
        text += f'{mark} {m["name"]} — `{progress[i]}/{m["goal"]}` 💠{m["reward"]}\n'

    text += '\n🔄 Миссии обновляются каждый день.'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ---------- ВЕРИФИКАЦИЯ ----------
@bot.message_handler(func=lambda m: m.text and 'Верификация' in m.text or (m.text == '/verify'))
def verify(message):
    user_id = message.from_user.id
    u = get_user(user_id, message.from_user.username or '', message.from_user.first_name or '')
    now = int(time.time())

    if now - u['last_case'] < COOLDOWN:
        left = COOLDOWN - (now - u['last_case'])
        mins, secs = divmod(left, 60)
        bot.reply_to(message, f'⏳ Кейс откроется через *{mins} мин {secs} сек*.', parse_mode='Markdown')
        return

    msg = bot.send_message(message.chat.id, '🔍 Верификация...\n⬜⬜⬜⬜⬜ 0%')
    stages = [
        ('⬛⬜⬜⬜⬜ 20%', 0.4),
        ('⬛⬛⬜⬜⬜ 40%', 0.4),
        ('⬛⬛⬛⬜⬜ 60%', 0.4),
        ('⬛⬛⬛⬛⬜ 80%', 0.4),
        ('⬛⬛⬛⬛⬛ 100%', 0.4),
    ]
    for t, delay in stages:
        time.sleep(delay)
        try:
            bot.edit_message_text(f'🔍 Верификация...\n{t}', message.chat.id, msg.message_id)
        except Exception:
            pass

    new_id = str(random.randint(1000000, 9999999))
    reward = random.randint(5, 25)

    update_user(user_id,
                last_case=now,
                current_id=new_id,
                irises=u['irises'] + reward,
                cases_opened=u['cases_opened'] + 1)

    bot.send_message(
        message.chat.id,
        f'✅ *Верификация завершена!*\n\n'
        f'🆔 Твой ID: `{new_id}`\n'
        f'💎 Награда: `+{reward}` ирисок\n\n'
        f'⏳ Следующий кейс через 1 час.',
        parse_mode='Markdown'
    )

    add_mission_progress(user_id, 'open_case', 1)
    add_mission_progress(user_id, 'earn_irises', reward)

# ---------- МАГАЗИН ----------
@bot.message_handler(func=lambda m: m.text and 'Магазин' in m.text or (m.text == '/shop'))
def shop(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(SHOP):
        kb.add(types.InlineKeyboardButton(
            f'{item["name"]} — {item["id"]} | 💎 {item["price"]}',
            callback_data=f'buy_{i}'
        ))
    bot.send_message(message.chat.id, '🛒 *Магазин ID*\nВыбери товар:', parse_mode='Markdown', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy(call):
    idx = int(call.data.split('_')[1])
    item = SHOP[idx]
    user_id = call.from_user.id
    u = get_user(user_id, call.from_user.username or '', call.from_user.first_name or '')

    if u['irises'] < item['price']:
        bot.answer_callback_query(call.id, f'❌ Не хватает {item["price"] - u["irises"]} ирисок', show_alert=True)
        return

    inventory = (u['inventory'] + f',{item["id"]}') if u['inventory'] else item['id']
    update_user(user_id, irises=u['irises'] - item['price'], inventory=inventory)
    bot.answer_callback_query(call.id, '✅ Куплено!', show_alert=True)
    bot.send_message(
        call.message.chat.id,
        f'✅ Ты купил *{item["name"]}*\n🆔 ID: `{item["id"]}`\n💎 Списано: `{item["price"]}`',
        parse_mode='Markdown'
    )
    add_mission_progress(user_id, 'buy', 1)

# ---------- /give ----------
ADMIN_ID = 0  # вставь свой Telegram ID

@bot.message_handler(commands=['give'])
def give(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        amount = int(parts[1])
        u = get_user(message.from_user.id)
        update_user(message.from_user.id, irises=u['irises'] + amount)
        bot.reply_to(message, f'💎 Выдано `{amount}` ирисок.', parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, 'Использование: /give 1000')

# ---------- /givemoney (алмазы) ----------
@bot.message_handler(commands=['givemoney'])
def givemoney(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        amount = int(parts[1])
        u = get_user(message.from_user.id)
        update_user(message.from_user.id, diamonds=u['diamonds'] + amount)
        bot.reply_to(message, f'💠 Выдано `{amount}` алмазов.', parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, 'Использование: /givemoney 100')

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    print('Бот запущен...')
    bot.infinity_polling()
