import telebot
import sqlite3
import json
import time
import random
import threading
from telebot import types

TOKEN = '8624166568:AAF_TcYkIv26LLvWXbLjBRZyp9IWzZFgMeE'
bot = telebot.TeleBot(TOKEN)
DB = 'rp_countries.db'


# ============================================================
# ЗДАНИЯ
# ============================================================
BUILDINGS = {
    'farm':     {'name': '🌾 Ферма',       'cost': 200, 'desc': '+500 еды/час'},
    'factory':  {'name': '🏭 Завод',       'cost': 500, 'desc': '+300💰/час, -2 стабильности'},
    'barracks': {'name': '⚔️ Казармы',     'cost': 300, 'desc': '+200 армии/час'},
    'school':   {'name': '🎓 Школа',       'cost': 400, 'desc': '+1 технология/час'},
    'hospital': {'name': '🏥 Больница',    'cost': 350, 'desc': '+2 стабильности/час, +население'},
    'police':   {'name': '🚔 Полиция',     'cost': 250, 'desc': '+3 стабильности/час'},
    'mine':     {'name': '⛏️ Шахта',       'cost': 400, 'desc': '+300 металла/час'},
    'oilrig':   {'name': '🛢️ Нефтевышка',  'cost': 600, 'desc': '+200 нефти/час, -1 стабильности'},
}


# ============================================================
# БД
# ============================================================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, flag TEXT, owner INTEGER,
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
        country_id INTEGER, name TEXT,
        population INTEGER DEFAULT 100000,
        buildings TEXT DEFAULT '{}'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT, time INTEGER, text TEXT
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


def add_news(text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO news (time, text) VALUES (?, ?)', (int(time.time()), text))
    c.execute('DELETE FROM news WHERE id NOT IN (SELECT id FROM news ORDER BY id DESC LIMIT 50)')
    conn.commit()
    conn.close()


# ============================================================
# 25 СТРАН
# ============================================================
COUNTRIES_25 = [
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
# ТИК
# ============================================================
def economy_tick():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM countries')
    countries = c.fetchall()

    for country in countries:
        cid, name, flag, owner = country[0], country[1], country[2], country[3]
        pop, treasury, army, tech = country[4], country[5], country[6], country[7]
        stability, food, metal, oil = country[8], country[9], country[10], country[11]
        is_npc = country[12]

        c.execute('SELECT buildings FROM cities WHERE country_id=?', (cid,))
        rows = c.fetchall()
        bonus = {'food': 0, 'treasury': 0, 'army': 0, 'tech': 0, 'stability': 0, 'metal': 0, 'oil': 0, 'pop_bonus': 0}
        for (bj,) in rows:
            try:
                b = json.loads(bj or '{}')
                for k, cnt in b.items():
                    if k == 'farm': bonus['food'] += 500 * cnt
                    elif k == 'factory':
                        bonus['treasury'] += 300 * cnt
                        bonus['stability'] -= 2 * cnt
                    elif k == 'barracks': bonus['army'] += 200 * cnt
                    elif k == 'school': bonus['tech'] += 1 * cnt
                    elif k == 'hospital':
                        bonus['stability'] += 2 * cnt
                        bonus['pop_bonus'] += cnt
                    elif k == 'police': bonus['stability'] += 3 * cnt
                    elif k == 'mine': bonus['metal'] += 300 * cnt
                    elif k == 'oilrig':
                        bonus['oil'] += 200 * cnt
                        bonus['stability'] -= 1 * cnt
            except: pass

        income = int((pop / 10000) * (1 + tech * 0.1) * (stability / 100)) + bonus['treasury']
        expense = int(army * 0.5)
        treasury += income - expense
        if treasury < 0:
            treasury = 0
            stability -= 5

        food += bonus['food']
        metal += bonus['metal']
        oil += bonus['oil']
        army += bonus['army']
        tech += bonus['tech']
        stability += bonus['stability']
        stability = max(0, min(100, stability))
        if bonus['stability'] == 0 and stability < 100:
            stability += 1

        if food > pop / 1000:
            growth = int((food / 100) * (stability / 100)) + bonus['pop_bonus'] * 500
            pop += growth
            food -= growth * 10

        c.execute('''UPDATE countries SET treasury=?, population=?, stability=?, food=?, 
            metal=?, oil=?, army=?, tech=? WHERE id=?''',
            (treasury, pop, stability, food, metal, oil, army, tech, cid))

        if is_npc:
            npc_action(cid, name, treasury, army, stability)

    conn.commit()
    conn.close()


def npc_action(cid, name, treasury, army, stability):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    actions = []
    if treasury > 600: actions.append('farm')
    if treasury > 800: actions.append('factory')
    if treasury > 500 and army < 100000: actions.append('barracks')
    if stability < 50: actions.append('police')
    if actions:
        bkey = random.choice(actions)
        cost = BUILDINGS[bkey]['cost']
        if treasury >= cost:
            c.execute('UPDATE countries SET treasury = treasury - ? WHERE id=?', (cost, cid))
            c.execute('SELECT id, buildings FROM cities WHERE country_id=? LIMIT 1', (cid,))
            row = c.fetchone()
            if row:
                city_id, bj = row
                try: b = json.loads(bj or '{}')
                except: b = {}
                b[bkey] = b.get(bkey, 0) + 1
                c.execute('UPDATE cities SET buildings=? WHERE id=?', (json.dumps(b), city_id))
                add_news(f'{name}: построено {BUILDINGS[bkey]["name"]}')
    conn.commit()
    conn.close()


def start_tick():
    while True:
        time.sleep(3600)
        try:
            economy_tick()
            print('tick ok')
        except Exception as e:
            print('tick err:', e)


threading.Thread(target=start_tick, daemon=True).start()


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🏛️ Моя страна', callback_data='menu_my'),
        types.InlineKeyboardButton('🏗️ Строительство', callback_data='menu_build'),
    )
    kb.add(
        types.InlineKeyboardButton('🏙️ Города', callback_data='menu_cities'),
        types.InlineKeyboardButton('📰 Новости', callback_data='menu_news'),
    )
    kb.add(
        types.InlineKeyboardButton('🏆 Топ', callback_data='menu_top'),
        types.InlineKeyboardButton('🌍 Все страны', callback_data='menu_all'),
    )
    kb.add(types.InlineKeyboardButton('❓ Помощь', callback_data='menu_help'))
    return kb


def countries_kb(page=0):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, name, flag, owner FROM countries ORDER BY name')
    all_c = c.fetchall()
    conn.close()

    per_page = 8
    total = (len(all_c) + per_page - 1) // per_page
    page = max(0, min(page, total - 1))
    chunk = all_c[page * per_page:(page + 1) * per_page]

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for cid, name, flag, owner in chunk:
        if owner:
            btns.append(types.InlineKeyboardButton(f'🔒 {flag} {name}', callback_data='taken'))
        else:
            btns.append(types.InlineKeyboardButton(f'{flag} {name}', callback_data=f'take_{cid}'))
    kb.add(*btns)

    nav = []
    if page > 0: nav.append(types.InlineKeyboardButton('◀️', callback_data=f'page_{page-1}'))
    nav.append(types.InlineKeyboardButton(f'{page+1}/{total}', callback_data='noop'))
    if page < total - 1: nav.append(types.InlineKeyboardButton('▶️', callback_data=f'page_{page+1}'))
    kb.add(*nav)
    return kb


def confirm_take_kb(cid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Да, выбрать', callback_data=f'confirm_take_{cid}'),
        types.InlineKeyboardButton('❌ Отмена', callback_data='menu_all'),
    )
    return kb


def cities_menu_kb(country_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT id, name, population FROM cities WHERE country_id=?', (country_id,))
    cities = c.fetchall()
    conn.close()

    kb = types.InlineKeyboardMarkup(row_width=1)
    for cid, name, pop in cities:
        kb.add(types.InlineKeyboardButton(f'🏙️ {name} ({pop:,})', callback_data=f'city_{cid}'))
    kb.add(types.InlineKeyboardButton('➕ Основать город (5000💰)', callback_data='found_city'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_main'))
    return kb


def buildings_menu_kb(city_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for bkey, b in BUILDINGS.items():
        kb.add(types.InlineKeyboardButton(
            f'{b["name"]} ({b["cost"]}💰)',
            callback_data=f'build_{city_id}_{bkey}'
        ))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data=f'city_{city_id}'))
    return kb


# ============================================================
# ХЕНДЛЕРЫ КОМАНД
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    country = get_country_by_owner(m.from_user.id)
    name = m.from_user.first_name or 'друг'

    if country:
        text = (
            f'🏛️ <b>RP Countries</b>\n'
            f'━━━━━━━━━━━━━━━\n\n'
            f'Привет, {name}!\n\n'
            f'Ты правишь <b>{country[2]} {country[1]}</b>.\n\n'
            f'Выбери действие:'
        )
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())
    else:
        text = (
            f'🏛️ <b>RP Countries</b>\n'
            f'━━━━━━━━━━━━━━━\n\n'
            f'Привет, {name}!\n\n'
            f'Это игра про управление страной.\n\n'
            f'⚠️ Страну можно выбрать <b>только один раз</b>.\n\n'
            f'Нажми кнопку ниже:'
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🌍 Выбрать страну', callback_data='menu_all'))
        kb.add(types.InlineKeyboardButton('❓ Помощь', callback_data='menu_help'))
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'noop')
def cb_noop(c): bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data == 'taken')
def cb_taken(c): bot.answer_callback_query(c.id, '🔒 Занята', show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_main(c):
    country = get_country_by_owner(c.from_user.id)
    if not country:
        text = '🏛️ <b>RP Countries</b>\n\nСначала выбери страну:'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🌍 Выбрать', callback_data='menu_all'))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)
        return
    text = f'🏛️ <b>{country[2]} {country[1]}</b>\n━━━━━━━━━━━━━━━\n\nВыбери действие:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=main_menu())


@bot.callback_query_handler(func=lambda c: c.data == 'menu_my')
def cb_my(c):
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'У тебя нет страны', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT id, name, population, buildings FROM cities WHERE country_id=?', (country[0],))
    cities = cc.fetchall()
    conn.close()

    total_b = 0
    for _, _, _, bj in cities:
        try:
            b = json.loads(bj or '{}')
            total_b += sum(b.values())
        except: pass

    income = int((country[4]/10000) * (1 + country[7]*0.1) * (country[8]/100))

    text = (
        f'🏛️ <b>{country[2]} {country[1]}</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: <b>{country[4]:,}</b>\n'
        f'💰 Казна: <b>{country[5]:,}</b>\n'
        f'⚔️ Армия: <b>{country[6]:,}</b>\n'
        f'🔬 Технологии: <b>{country[7]}</b>\n'
        f'📊 Стабильность: <b>{country[8]}</b>\n\n'
        f'🌾 Еда: {country[9]:,}\n'
        f'⛏️ Металл: {country[10]:,}\n'
        f'🛢️ Нефть: {country[11]:,}\n\n'
        f'🏙️ Городов: <b>{len(cities)}</b>\n'
        f'🏗️ Зданий: <b>{total_b}</b>\n\n'
        f'💡 Базовый доход: ~<b>{income:,}</b>💰/час'
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🏗️ Строить', callback_data='menu_build'),
        types.InlineKeyboardButton('🏙️ Города', callback_data='menu_cities'),
    )
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_my'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_all')
def cb_all(c):
    text = '<b>🌍 Выбери страну</b>\n\n⚠️ Выбор — навсегда!'
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=countries_kb(0))
    except:
        bot.send_message(c.message.chat.id, text, parse_mode='HTML', reply_markup=countries_kb(0))


@bot.callback_query_handler(func=lambda c: c.data.startswith('page_'))
def cb_page(c):
    page = int(c.data.split('_')[1])
    bot.edit_message_text('<b>🌍 Выбери страну</b>\n\n⚠️ Выбор — навсегда!',
                          c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=countries_kb(page))


@bot.callback_query_handler(func=lambda c: c.data.startswith('take_'))
def cb_take(c):
    cid = int(c.data.split('_')[1])
    existing = get_country_by_owner(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, f'У тебя уже есть {existing[1]}', show_alert=True)
        return
    country = get_country_by_id(cid)
    if not country or country[3]:
        bot.answer_callback_query(c.id, 'Занята', show_alert=True)
        return

    text = (
        f'🏛️ Выбрать <b>{country[2]} {country[1]}</b>?\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: {country[4]:,}\n'
        f'💰 Казна: {country[5]:,}\n'
        f'⚔️ Армия: {country[6]:,}\n'
        f'🔬 Технологии: {country[7]}\n\n'
        f'⚠️ <b>Страну нельзя поменять!</b>'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=confirm_take_kb(cid))


@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm_take_'))
def cb_confirm(c):
    cid = int(c.data.split('_')[2])
    existing = get_country_by_owner(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, 'Уже есть страна', show_alert=True)
        return
    country = get_country_by_id(cid)
    if not country or country[3]:
        bot.answer_callback_query(c.id, 'Занята', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('UPDATE countries SET owner=?, is_npc=0 WHERE id=?', (c.from_user.id, cid))
    cc.execute('INSERT INTO cities (country_id, name, population, buildings) VALUES (?, ?, ?, ?)',
               (cid, 'Столица', 500000, '{}'))
    conn.commit()
    conn.close()
    add_news(f'{country[2]} {country[1]}: новый правитель!')

    text = (
        f'✅ <b>Поздравляем!</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'Ты правишь {country[2]} <b>{country[1]}</b>.\n\n'
        f'Твоя столица создана. Пора строить!'
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🏛️ Моя страна', callback_data='menu_my'),
        types.InlineKeyboardButton('🏗️ Строить', callback_data='menu_build'),
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_build')
def cb_build(c):
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return
    text = '🏗️ <b>Строительство</b>\n━━━━━━━━━━━━━━━\n\nВыбери город, где строить:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=cities_menu_kb(country[0]))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_cities')
def cb_cities(c):
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return
    text = '🏙️ <b>Твои города</b>\n━━━━━━━━━━━━━━━\n\nВыбери город или основывай новый:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=cities_menu_kb(country[0]))


@bot.callback_query_handler(func=lambda c: c.data.startswith('city_') and c.data[5:].isdigit())
def cb_city(c):
    city_id = int(c.data.split('_')[1])
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT name, population, buildings, country_id FROM cities WHERE id=?', (city_id,))
    row = cc.fetchone()
    conn.close()

    if not row or row[3] != country[0]:
        bot.answer_callback_query(c.id, 'Это не твой город', show_alert=True)
        return

    name, pop, bj, _ = row
    try: b = json.loads(bj or '{}')
    except: b = {}

    text = f'🏙️ <b>{name}</b>\n━━━━━━━━━━━━━━━\n\n👥 Население: <b>{pop:,}</b>\n\n<b>Здания:</b>\n'
    if not b:
        text += 'Пока пусто.'
    else:
        for k, cnt in b.items():
            if k in BUILDINGS:
                text += f'{BUILDINGS[k]["name"]} × {cnt}\n'

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🏗️ Построить', callback_data=f'build_menu_{city_id}'))
    kb.add(types.InlineKeyboardButton('◀️ К городам', callback_data='menu_cities'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('build_menu_'))
def cb_build_menu(c):
    city_id = int(c.data.split('_')[2])
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT name, country_id FROM cities WHERE id=?', (city_id,))
    row = cc.fetchone()
    conn.close()

    if not row or row[1] != country[0]:
        bot.answer_callback_query(c.id, 'Не твой город', show_alert=True)
        return

    text = (
        f'🏗️ <b>Что построить в «{row[0]}»?</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💰 Казна: <b>{country[5]:,}</b>\n\n'
        f'Выбери здание:'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=buildings_menu_kb(city_id))


@bot.callback_query_handler(func=lambda c: c.data.startswith('build_') and c.data.count('_') == 2)
def cb_do_build(c):
    parts = c.data.split('_')
    city_id = int(parts[1])
    bkey = parts[2]

    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return

    if bkey not in BUILDINGS:
        bot.answer_callback_query(c.id, 'Неизвестное здание', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT name, buildings, country_id FROM cities WHERE id=?', (city_id,))
    row = cc.fetchone()

    if not row or row[2] != country[0]:
        conn.close()
        bot.answer_callback_query(c.id, 'Не твой город', show_alert=True)
        return

    cost = BUILDINGS[bkey]['cost']
    if country[5] < cost:
        conn.close()
        bot.answer_callback_query(c.id, f'Не хватает {cost - country[5]}💰', show_alert=True)
        return

    try: b = json.loads(row[1] or '{}')
    except: b = {}
    b[bkey] = b.get(bkey, 0) + 1

    cc.execute('UPDATE countries SET treasury = treasury - ? WHERE id=?', (cost, country[0]))
    cc.execute('UPDATE cities SET buildings=? WHERE id=?', (json.dumps(b), city_id))
    conn.commit()
    conn.close()

    add_news(f'{country[2]} {country[1]}: построено {BUILDINGS[bkey]["name"]}')

    bot.answer_callback_query(c.id, f'✅ {BUILDINGS[bkey]["name"]} построено!', show_alert=True)

    # Обновляем экран городов
    cb_build_menu(c)


@bot.callback_query_handler(func=lambda c: c.data == 'found_city')
def cb_found_city(c):
    country = get_country_by_owner(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return

    cost = 5000
    if country[5] < cost:
        bot.answer_callback_query(c.id, f'Нужно {cost}💰', show_alert=True)
        return

    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT COUNT(*) FROM cities WHERE country_id=?', (country[0],))
    cnt = cc.fetchone()[0]
    city_name = f'Город-{cnt + 1}'

    cc.execute('UPDATE countries SET treasury = treasury - ? WHERE id=?', (cost, country[0]))
    cc.execute('INSERT INTO cities (country_id, name, population, buildings) VALUES (?, ?, ?, ?)',
               (country[0], city_name, 100000, '{}'))
    conn.commit()
    conn.close()

    add_news(f'{country[2]} {country[1]}: основан {city_name}')
    bot.answer_callback_query(c.id, f'✅ {city_name} основан!', show_alert=True)

    text = '🏙️ <b>Твои города</b>\n━━━━━━━━━━━━━━━\n\nВыбери город:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=cities_menu_kb(country[0]))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_news')
def cb_news(c):
    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT text FROM news ORDER BY id DESC LIMIT 15')
    rows = cc.fetchall()
    conn.close()

    text = '<b>📰 Новости мира</b>\n━━━━━━━━━━━━━━━\n\n'
    if not rows:
        text += 'Пока пусто.'
    else:
        for (t,) in rows:
            text += f'• {t}\n'

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_news'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_top')
def cb_top(c):
    conn = sqlite3.connect(DB)
    cc = conn.cursor()
    cc.execute('SELECT name, flag, treasury, army FROM countries ORDER BY treasury DESC LIMIT 10')
    rows = cc.fetchall()
    conn.close()

    text = '<b>🏆 Топ стран по казне</b>\n━━━━━━━━━━━━━━━\n\n'
    for i, (name, flag, treas, army) in enumerate(rows, 1):
        text += f'{i}. {flag} {name} — 💰{treas:,}\n'

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_top'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_help')
def cb_help(c):
    text = (
        '🏛️ <b>RP Countries — Помощь</b>\n'
        '━━━━━━━━━━━━━━━\n\n'
        '<b>🎯 Цель</b>\n'
        'Развивай страну: экономика, армия, города.\n\n'
        '<b>📋 Кнопки</b>\n\n'
        '🏛️ <b>Моя страна</b> — статистика\n'
        '🏗️ <b>Строительство</b> — постройки\n'
        '🏙️ <b>Города</b> — список, основание новых\n'
        '📰 <b>Новости</b> — что в мире\n'
        '🏆 <b>Топ</b> — рейтинг\n'
        '🌍 <b>Все страны</b> — список\n\n'
        '<b>⚙️ Как играть</b>\n\n'
        '1. Выбери страну (навсегда!)\n'
        '2. Строй здания — эффект каждый час\n'
        '3. Основывай города (5000💰)\n'
        '4. Следи за ресурсами\n\n'
        '<b>💡 Совет</b>\n'
        'Строй фермы → еда → рост населения → больше дохода.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    init_db()
    init_countries()
    print('RP Countries bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
