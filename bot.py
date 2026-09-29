import telebot
import sqlite3
import json
import time
import random
import threading
from datetime import datetime

TOKEN = '8514412667:AAEBoRMZ6ADcqCFqMIoftu7IaunnOQDQnUM'
bot = telebot.TeleBot(TOKEN)
DB = 'rp_countries.db'


# ============================================================
# БАЗА ДАННЫХ
# ============================================================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        flag TEXT,
        owner INTEGER,
        population INTEGER DEFAULT 1000000,
        treasury INTEGER DEFAULT 5000,
        army INTEGER DEFAULT 1000,
        tech INTEGER DEFAULT 1,
        stability INTEGER DEFAULT 70,
        food INTEGER DEFAULT 5000,
        metal INTEGER DEFAULT 2000,
        oil INTEGER DEFAULT 1000,
        is_npc INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER,
        name TEXT,
        population INTEGER DEFAULT 100000,
        buildings TEXT DEFAULT '[]'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time INTEGER,
        text TEXT
    )''')
    conn.commit()
    conn.close()


def get_country_by_owner(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM countries WHERE owner=?', (uid,))
    row = c.fetchone()
    conn.close()
    return row


def get_country_by_id(cid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM countries WHERE id=?', (cid,))
    row = c.fetchone()
    conn.close()
    return row


def get_country_by_name(name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM countries WHERE name LIKE ?', (f'%{name}%',))
    row = c.fetchone()
    conn.close()
    return row


# ============================================================
# 25 СТРАН
# ============================================================
COUNTRIES_25 = [
    # (название, флаг, население, казна, армия, технологии)
    ('Россия', '🇷🇺', 146000000, 50000, 1000000, 5),
    ('США', '🇺🇸', 330000000, 80000, 1500000, 7),
    ('Китай', '🇨🇳', 1400000000, 70000, 2000000, 6),
    ('Германия', '🇩🇪', 83000000, 60000, 300000, 6),
    ('Франция', '🇫🇷', 67000000, 55000, 350000, 6),
    ('Великобритания', '🇬🇧', 67000000, 58000, 300000, 6),
    ('Япония', '🇯🇵', 125000000, 65000, 250000, 7),
    ('Индия', '🇮🇳', 1380000000, 40000, 1400000, 4),
    ('Бразилия', '🇧🇷', 213000000, 35000, 400000, 4),
    ('Канада', '🇨🇦', 38000000, 50000, 150000, 6),
    ('Италия', '🇮🇹', 60000000, 48000, 200000, 5),
    ('Испания', '🇪🇸', 47000000, 40000, 150000, 5),
    ('Турция', '🇹🇷', 84000000, 30000, 500000, 4),
    ('Южная Корея', '🇰🇷', 51000000, 55000, 600000, 7),
    ('Иран', '🇮🇷', 85000000, 30000, 600000, 4),
    ('Польша', '🇵🇱', 38000000, 35000, 200000, 5),
    ('Украина', '🇺🇦', 44000000, 25000, 300000, 4),
    ('Саудовская Аравия', '🇸🇦', 34000000, 70000, 200000, 5),
    ('Австралия', '🇦🇺', 26000000, 45000, 100000, 6),
    ('Мексика', '🇲🇽', 129000000, 25000, 250000, 3),
    ('Индонезия', '🇮🇩', 274000000, 22000, 400000, 3),
    ('Нигерия', '🇳🇬', 206000000, 15000, 200000, 2),
    ('Египет', '🇪🇬', 104000000, 20000, 450000, 3),
    ('ЮАР', '🇿🇦', 59000000, 25000, 100000, 4),
    ('Аргентина', '🇦🇷', 45000000, 28000, 150000, 4),
]


def init_countries():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for name, flag, pop, treas, army, tech in COUNTRIES_25:
        c.execute('''INSERT OR IGNORE INTO countries 
            (name, flag, population, treasury, army, tech) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (name, flag, pop, treas, army, tech))
    conn.commit()
    conn.close()


# ============================================================
# ЭКОНОМИЧЕСКИЙ ТИК (раз в час)
# ============================================================
def economy_tick():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute('SELECT * FROM countries')
    countries = c.fetchall()

    for country in countries:
        cid = country[0]
        name = country[1]
        pop = country[4]
        treasury = country[5]
        army = country[6]
        tech = country[7]
        stability = country[8]
        food = country[9]
        is_npc = country[12]

        # Доход
        income = int((pop / 10000) * (1 + tech * 0.1) * (stability / 100))
        # Расход
        expense = int(army * 0.5)
        # Прирост
        treasury += income - expense
        if treasury < 0:
            treasury = 0
            stability -= 5

        # Рост населения (если еды хватает)
        if food > pop / 1000:
            growth = int((food / 100) * (stability / 100))
            pop += growth
            food -= growth * 10

        # Стабильность
        if stability < 100:
            stability = min(100, stability + 1)
        if stability < 0:
            stability = 0

        c.execute('''UPDATE countries SET 
            treasury=?, population=?, stability=?, food=? 
            WHERE id=?''', (treasury, pop, stability, food, cid))

        # NPC логика
        if is_npc:
            npc_action(cid, name, treasury, army, stability)

    conn.commit()
    conn.close()


def npc_action(cid, name, treasury, army, stability):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    actions = []
    if treasury > 1000:
        actions.append(('build', 'Ферма'))
    if treasury > 2000:
        actions.append(('build', 'Завод'))
    if treasury > 1500 and army < 50000:
        actions.append(('recruit', 1000))
    if stability < 40:
        actions.append(('police', None))

    if actions:
        action = random.choice(actions)
        if action[0] == 'build':
            building = action[1]
            cost = 500 if building == 'Завод' else 200
            if treasury >= cost:
                c.execute('UPDATE countries SET treasury = treasury - ? WHERE id=?', (cost, cid))
                c.execute('UPDATE cities SET buildings = json_insert(buildings, "$[#]", ?) WHERE country_id=? LIMIT 1',
                          (building, cid))
                add_news(f'{name}: построено {building}')
        elif action[0] == 'recruit':
            count = action[1]
            cost = count * 2
            if treasury >= cost:
                c.execute('UPDATE countries SET treasury = treasury - ?, army = army + ? WHERE id=?',
                          (cost, count, cid))
                add_news(f'{name}: армия увеличена на {count}')

    conn.commit()
    conn.close()


def add_news(text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO news (time, text) VALUES (?, ?)', (int(time.time()), text))
    c.execute('DELETE FROM news WHERE id NOT IN (SELECT id FROM news ORDER BY id DESC LIMIT 50)')
    conn.commit()
    conn.close()


# ============================================================
# ФОНОВЫЙ ТИК
# ============================================================
def start_tick():
    while True:
        time.sleep(3600)  # раз в час
        try:
            economy_tick()
            print('Economy tick done')
        except Exception as e:
            print('tick err:', e)


threading.Thread(target=start_tick, daemon=True).start()


# ============================================================
# КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['start'])
def cmd_start(m):
    text = (
        '🏛️ <b>RP Countries</b>\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Выбери страну и управляй ей.\n'
        '⚠️ Страну можно выбрать <b>только один раз</b>!\n\n'
        '<b>Команды:</b>\n'
        '/countries — список стран\n'
        '/take Россия — занять страну\n'
        '/my — моя страна\n'
        '/build Москва Завод — построить\n'
        '/news — новости мира\n'
        '/top — топ стран'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['countries'])
def cmd_countries(m):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT name, flag, owner FROM countries ORDER BY name')
    rows = c.fetchall()
    conn.close()

    text = '<b>🌍 Страны мира (25)</b>\n\n'
    for name, flag, owner in rows:
        status = '👤' if owner else '🟢'
        text += f'{status} {flag} {name}\n'

    text += '\n🟢 — свободна, 👤 — занята'
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['take'])
def cmd_take(m):
    # Проверка: игрок уже имеет страну
    existing = get_country_by_owner(m.from_user.id)
    if existing:
        bot.reply_to(
            m,
            f'❌ Ты уже правишь {existing[2]} {existing[1]}.\n\n'
            f'Страну нельзя поменять — выбор сделан навсегда.'
        )
        return

    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(m, 'Используй: /take Россия')
        return

    name = args[1]
    country = get_country_by_name(name)

    if not country:
        bot.reply_to(m, f'Страна «{name}» не найдена. Смотри /countries')
        return

    if country[3]:  # owner
        bot.reply_to(m, f'{country[2]} {country[1]} уже занята.')
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE countries SET owner=?, is_npc=0 WHERE id=?', (m.from_user.id, country[0]))
    c.execute('INSERT INTO cities (country_id, name, population) VALUES (?, ?, ?)',
              (country[0], f'Столица {country[1]}', 500000))
    conn.commit()
    conn.close()

    add_news(f'{country[2]} {country[1]}: новый правитель!')

    bot.reply_to(
        m,
        f'✅ Ты теперь правишь {country[2]} {country[1]}!\n\n'
        f'⚠️ Помни: страну нельзя поменять.\n'
        f'Твоя столица создана. Смотри /my'
    )


@bot.message_handler(commands=['my'])
def cmd_my(m):
    country = get_country_by_owner(m.from_user.id)
    if not country:
        bot.reply_to(m, 'У тебя нет страны. Используй /take Название')
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT name, population FROM cities WHERE country_id=?', (country[0],))
    cities = c.fetchall()
    conn.close()

    text = (
        f'<b>{country[2]} {country[1]}</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: {country[4]:,}\n'
        f'💰 Казна: {country[5]:,}\n'
        f'⚔️ Армия: {country[6]:,}\n'
        f'🔬 Технологии: {country[7]}\n'
        f'📊 Стабильность: {country[8]}\n'
        f'🌾 Еда: {country[9]:,}\n'
        f'⛏️ Металл: {country[10]:,}\n'
        f'🛢️ Нефть: {country[11]:,}\n\n'
        f'🏙️ Города: {len(cities)}\n'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['build'])
def cmd_build(m):
    args = m.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(m, 'Используй: /build Москва Завод\n\nЗдания: Ферма, Завод, Казармы, Школа, Больница, Полиция')
        return

    city_name, building = args[1], args[2]
    country = get_country_by_owner(m.from_user.id)
    if not country:
        bot.reply_to(m, 'У тебя нет страны.')
        return

    costs = {'Ферма': 200, 'Завод': 500, 'Казармы': 300, 'Школа': 400, 'Больница': 350, 'Полиция': 250}
    if building not in costs:
        bot.reply_to(m, f'Неизвестное здание. Доступно: {", ".join(costs.keys())}')
        return

    cost = costs[building]
    if country[5] < cost:
        bot.reply_to(m, f'Не хватает денег. Нужно {cost}, у тебя {country[5]}.')
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE countries SET treasury = treasury - ? WHERE id=?', (cost, country[0]))
    c.execute('UPDATE cities SET buildings = json_insert(buildings, "$[#]", ?) WHERE country_id=? AND name LIKE ?',
              (building, country[0], f'%{city_name}%'))
    conn.commit()
    conn.close()

    bot.reply_to(m, f'✅ {building} построено в {city_name}!')


@bot.message_handler(commands=['news'])
def cmd_news(m):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT text, time FROM news ORDER BY id DESC LIMIT 15')
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(m, 'Пока новостей нет.')
        return

    text = '<b>📰 Новости мира</b>\n\n'
    for txt, ts in rows:
        text += f'• {txt}\n'

    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['top'])
def cmd_top(m):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT name, flag, treasury, army, population FROM countries ORDER BY treasury DESC LIMIT 10')
    rows = c.fetchall()
    conn.close()

    text = '<b>🏆 Топ стран по казне</b>\n\n'
    for i, (name, flag, treas, army, pop) in enumerate(rows, 1):
        text += f'{i}. {flag} {name} — 💰{treas:,}\n'

    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    init_db()
    init_countries()
    print('RP Countries bot started (25 countries)')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
