import telebot
import json
import os
import time
import random
import threading
from telebot import types

TOKEN = '8514412667:AAFyU_-lQNC1nSAzUrXANMk2qMG5EhCqcqk'
DATA_FILE = 'rp_data.json'

bot = telebot.TeleBot(TOKEN)

# ============================================================
# ЗДАНИЯ
# ============================================================
BUILDINGS = {
    'farm':     {'name': '🌾 Ферма',      'cost': 200, 'desc': '+500 еды/час'},
    'factory':  {'name': '🏭 Завод',      'cost': 500, 'desc': '+300💰/час'},
    'barracks': {'name': '⚔️ Казармы',    'cost': 300, 'desc': '+200 армии/час'},
    'school':   {'name': '🎓 Школа',      'cost': 400, 'desc': '+1 технология/час'},
    'hospital': {'name': '🏥 Больница',   'cost': 350, 'desc': '+2 стабильности/час'},
    'police':   {'name': '🚔 Полиция',    'cost': 250, 'desc': '+3 стабильности/час'},
    'mine':     {'name': '⛏️ Шахта',      'cost': 400, 'desc': '+300 металла/час'},
    'oilrig':   {'name': '🛢️ Нефтевышка', 'cost': 600, 'desc': '+200 нефти/час'},
}

COUNTRIES_25 = [
    {'name': 'Россия', 'flag': '🇷🇺', 'pop': 146000000, 'treas': 50000, 'army': 1000000, 'tech': 5},
    {'name': 'США', 'flag': '🇺🇸', 'pop': 330000000, 'treas': 80000, 'army': 1500000, 'tech': 7},
    {'name': 'Китай', 'flag': '🇨🇳', 'pop': 1400000000, 'treas': 70000, 'army': 2000000, 'tech': 6},
    {'name': 'Германия', 'flag': '🇩🇪', 'pop': 83000000, 'treas': 60000, 'army': 300000, 'tech': 6},
    {'name': 'Франция', 'flag': '🇫🇷', 'pop': 67000000, 'treas': 55000, 'army': 350000, 'tech': 6},
    {'name': 'Великобритания', 'flag': '🇬🇧', 'pop': 67000000, 'treas': 58000, 'army': 300000, 'tech': 6},
    {'name': 'Япония', 'flag': '🇯🇵', 'pop': 125000000, 'treas': 65000, 'army': 250000, 'tech': 7},
    {'name': 'Индия', 'flag': '🇮🇳', 'pop': 1380000000, 'treas': 40000, 'army': 1400000, 'tech': 4},
    {'name': 'Бразилия', 'flag': '🇧🇷', 'pop': 213000000, 'treas': 35000, 'army': 400000, 'tech': 4},
    {'name': 'Канада', 'flag': '🇨🇦', 'pop': 38000000, 'treas': 50000, 'army': 150000, 'tech': 6},
    {'name': 'Италия', 'flag': '🇮🇹', 'pop': 60000000, 'treas': 48000, 'army': 200000, 'tech': 5},
    {'name': 'Испания', 'flag': '🇪🇸', 'pop': 47000000, 'treas': 40000, 'army': 150000, 'tech': 5},
    {'name': 'Турция', 'flag': '🇹🇷', 'pop': 84000000, 'treas': 30000, 'army': 500000, 'tech': 4},
    {'name': 'Южная Корея', 'flag': '🇰🇷', 'pop': 51000000, 'treas': 55000, 'army': 600000, 'tech': 7},
    {'name': 'Иран', 'flag': '🇮🇷', 'pop': 85000000, 'treas': 30000, 'army': 600000, 'tech': 4},
    {'name': 'Польша', 'flag': '🇵🇱', 'pop': 38000000, 'treas': 35000, 'army': 200000, 'tech': 5},
    {'name': 'Украина', 'flag': '🇺🇦', 'pop': 44000000, 'treas': 25000, 'army': 300000, 'tech': 4},
    {'name': 'Саудовская Аравия', 'flag': '🇸🇦', 'pop': 34000000, 'treas': 70000, 'army': 200000, 'tech': 5},
    {'name': 'Австралия', 'flag': '🇦🇺', 'pop': 26000000, 'treas': 45000, 'army': 100000, 'tech': 6},
    {'name': 'Мексика', 'flag': '🇲🇽', 'pop': 129000000, 'treas': 25000, 'army': 250000, 'tech': 3},
    {'name': 'Индонезия', 'flag': '🇮🇩', 'pop': 274000000, 'treas': 22000, 'army': 400000, 'tech': 3},
    {'name': 'Нигерия', 'flag': '🇳🇬', 'pop': 206000000, 'treas': 15000, 'army': 200000, 'tech': 2},
    {'name': 'Египет', 'flag': '🇪🇬', 'pop': 104000000, 'treas': 20000, 'army': 450000, 'tech': 3},
    {'name': 'ЮАР', 'flag': '🇿🇦', 'pop': 59000000, 'treas': 25000, 'army': 100000, 'tech': 4},
    {'name': 'Аргентина', 'flag': '🇦🇷', 'pop': 45000000, 'treas': 28000, 'army': 150000, 'tech': 4},
]


# ============================================================
# ДАННЫЕ
# ============================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # Первый запуск — создаём 25 стран
    data = {'countries': {}, 'users': {}, 'news': []}
    for i, c in enumerate(COUNTRIES_25):
        data['countries'][str(i)] = {
            'id': i,
            'name': c['name'],
            'flag': c['flag'],
            'owner': None,
            'pop': c['pop'],
            'treas': c['treas'],
            'army': c['army'],
            'tech': c['tech'],
            'stability': 70,
            'food': 5000,
            'metal': 2000,
            'oil': 1000,
            'isNpc': True,
            'cities': [],
        }
    return data


def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('save err:', e)


data = load_data()


def add_news(text):
    data['news'].insert(0, {'time': int(time.time()), 'text': text})
    data['news'] = data['news'][:50]


def get_my_country(uid):
    for cid, c in data['countries'].items():
        if c.get('owner') == uid:
            return c
    return None


# ============================================================
# ЭКОНОМИКА — раз в час
# ============================================================
def economy_tick():
    for cid, c in data['countries'].items():
        # Доход с городов
        income = 0
        for city in c['cities']:
            inc = city['pop'] * 0.0005 * 3600 + 50
            b = city.get('buildings', {})
            if 'factory' in b:
                inc += 300 * b['factory']
            income += inc

        expense = c['army'] * 0.5
        c['treas'] += income - expense
        if c['treas'] < 0:
            c['treas'] = 0
            c['stability'] -= 5

        # Ресурсы от зданий
        for city in c['cities']:
            b = city.get('buildings', {})
            c['food'] += 500 * b.get('farm', 0)
            c['metal'] += 300 * b.get('mine', 0)
            c['oil'] += 200 * b.get('oilrig', 0)
            c['army'] += 200 * b.get('barracks', 0)
            c['tech'] += 1 * b.get('school', 0)
            c['stability'] += 2 * b.get('hospital', 0) + 3 * b.get('police', 0)

        c['stability'] = max(0, min(100, c['stability']))

        # Рост населения
        if c['food'] > c['pop'] / 1000:
            growth = int((c['food'] / 100) * (c['stability'] / 100))
            c['pop'] += growth
            c['food'] -= growth * 10

        # NPC ход
        if c['isNpc'] and c['treas'] > 800 and c['cities']:
            bkey = random.choice(['farm', 'factory', 'barracks', 'police'])
            cost = BUILDINGS[bkey]['cost']
            if c['treas'] >= cost:
                c['treas'] -= cost
                city = c['cities'][0]
                city.setdefault('buildings', {})
                city['buildings'][bkey] = city['buildings'].get(bkey, 0) + 1
                add_news(f'{c["flag"]} {c["name"]}: построено {BUILDINGS[bkey]["name"]}')

    save_data()


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
def fmt(n):
    n = int(n)
    if n >= 1_000_000_000: return f'{n/1_000_000_000:.1f} млрд'
    if n >= 1_000_000: return f'{n/1_000_000:.1f} млн'
    if n >= 1_000: return f'{n/1_000:.1f} тыс'
    return str(n)


def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🏛️ Моя страна', callback_data='menu_my'),
        types.InlineKeyboardButton('🏗️ Строить', callback_data='menu_build'),
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
    all_c = list(data['countries'].values())
    per_page = 8
    total = (len(all_c) + per_page - 1) // per_page
    page = max(0, min(page, total - 1))
    chunk = all_c[page * per_page:(page + 1) * per_page]

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for c in chunk:
        if c.get('owner'):
            btns.append(types.InlineKeyboardButton(f'🔒 {c["flag"]} {c["name"]}', callback_data='taken'))
        else:
            btns.append(types.InlineKeyboardButton(f'{c["flag"]} {c["name"]}', callback_data=f'take_{c["id"]}'))
    kb.add(*btns)

    nav = []
    if page > 0: nav.append(types.InlineKeyboardButton('◀️', callback_data=f'page_{page-1}'))
    nav.append(types.InlineKeyboardButton(f'{page+1}/{total}', callback_data='noop'))
    if page < total - 1: nav.append(types.InlineKeyboardButton('▶️', callback_data=f'page_{page+1}'))
    kb.add(*nav)
    return kb


def cities_menu_kb(country):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, city in enumerate(country['cities']):
        kb.add(types.InlineKeyboardButton(
            f'🏙️ {city["name"]} ({fmt(city["pop"])})',
            callback_data=f'city_{i}'
        ))
    kb.add(types.InlineKeyboardButton('➕ Основать город (5000💰)', callback_data='found_city'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    return kb


def buildings_kb(city_idx):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for bkey, b in BUILDINGS.items():
        kb.add(types.InlineKeyboardButton(
            f'{b["name"]} ({b["cost"]}💰)',
            callback_data=f'build_{city_idx}_{bkey}'
        ))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_build'))
    return kb


# ============================================================
# КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    country = get_my_country(uid)
    name = m.from_user.first_name or 'друг'

    if country:
        text = (
            f'🏛️ <b>RP Countries</b>\n\n'
            f'Привет, {name}!\n\n'
            f'Ты правишь {country["flag"]} <b>{country["name"]}</b>.\n\n'
            f'Выбери действие:'
        )
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())
    else:
        text = (
            f'🏛️ <b>RP Countries</b>\n\n'
            f'Привет, {name}!\n\n'
            f'Игра про управление страной.\n\n'
            f'⚠️ Страну можно выбрать <b>только один раз</b>.\n\n'
            f'Нажми кнопку ниже:'
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🌍 Выбрать страну', callback_data='menu_all'))
        kb.add(types.InlineKeyboardButton('❓ Помощь', callback_data='menu_help'))
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)


# ============================================================
# CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == 'noop')
def cb_noop(c): bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data == 'taken')
def cb_taken(c): bot.answer_callback_query(c.id, '🔒 Занята', show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_main(c):
    country = get_my_country(c.from_user.id)
    if not country:
        text = '🏛️ Сначала выбери страну:'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('🌍 Выбрать', callback_data='menu_all'))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
        return
    text = f'🏛️ <b>{country["flag"]} {country["name"]}</b>\n\nВыбери действие:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=main_menu())


@bot.callback_query_handler(func=lambda c: c.data == 'menu_my')
def cb_my(c):
    country = get_my_country(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'У тебя нет страны', show_alert=True)
        return

    income = 0
    total_b = 0
    for city in country['cities']:
        inc = city['pop'] * 0.0005 * 3600 + 50
        b = city.get('buildings', {})
        if 'factory' in b: inc += 300 * b['factory']
        income += inc
        total_b += sum(b.values())

    text = (
        f'🏛️ <b>{country["flag"]} {country["name"]}</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: <b>{fmt(country["pop"])}</b>\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n'
        f'⚔️ Армия: <b>{fmt(country["army"])}</b>\n'
        f'🔬 Технологии: <b>{int(country["tech"])}</b>\n'
        f'📊 Стабильность: <b>{int(country["stability"])}</b>\n\n'
        f'🌾 Еда: {fmt(country["food"])}\n'
        f'⛏️ Металл: {fmt(country["metal"])}\n'
        f'🛢️ Нефть: {fmt(country["oil"])}\n\n'
        f'🏙️ Городов: <b>{len(country["cities"])}</b>\n'
        f'🏗️ Зданий: <b>{total_b}</b>\n\n'
        f'💡 Доход: ~<b>{fmt(income)}</b>💰/час'
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
    cid = c.data.split('_')[1]
    existing = get_my_country(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, f'У тебя уже есть {existing["name"]}', show_alert=True)
        return
    country = data['countries'].get(cid)
    if not country or country.get('owner'):
        bot.answer_callback_query(c.id, 'Занята', show_alert=True)
        return

    text = (
        f'🏛️ Выбрать <b>{country["flag"]} {country["name"]}</b>?\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: {fmt(country["pop"])}\n'
        f'💰 Казна: {fmt(country["treas"])}\n'
        f'⚔️ Армия: {fmt(country["army"])}\n\n'
        f'⚠️ <b>Страну нельзя поменять!</b>'
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Да', callback_data=f'confirm_{cid}'),
        types.InlineKeyboardButton('❌ Нет', callback_data='menu_all'),
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm_'))
def cb_confirm(c):
    cid = c.data.split('_')[1]
    existing = get_my_country(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, 'Уже есть страна', show_alert=True)
        return
    country = data['countries'].get(cid)
    if not country or country.get('owner'):
        bot.answer_callback_query(c.id, 'Занята', show_alert=True)
        return

    country['owner'] = c.from_user.id
    country['isNpc'] = False
    country['cities'].append({'name': 'Столица', 'pop': 500000, 'buildings': {}})
    add_news(f'{country["flag"]} {country["name"]}: новый правитель!')
    save_data()

    text = (
        f'✅ <b>Поздравляем!</b>\n\n'
        f'Ты правишь {country["flag"]} <b>{country["name"]}</b>.\n\n'
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
    country = get_my_country(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return
    if not country['cities']:
        bot.answer_callback_query(c.id, 'Сначала нужен город', show_alert=True)
        return

    text = '🏗️ <b>Строительство</b>\n\nВыбери город:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=cities_menu_kb(country))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_cities')
def cb_cities(c):
    country = get_my_country(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return
    text = '🏙️ <b>Твои города</b>\n\nВыбери город:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=cities_menu_kb(country))


@bot.callback_query_handler(func=lambda c: c.data.startswith('city_') and c.data[5:].isdigit())
def cb_city(c):
    idx = int(c.data.split('_')[1])
    country = get_my_country(c.from_user.id)
    if not country or idx >= len(country['cities']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True)
        return

    city = country['cities'][idx]
    b = city.get('buildings', {})
    inc = (city['pop'] * 0.0005 * 3600 + 50)
    if 'factory' in b: inc += 300 * b['factory']

    text = f'🏙️ <b>{city["name"]}</b>\n━━━━━━━━━━━━━━━\n\n👥 Население: <b>{fmt(city["pop"])}</b>\n💡 Доход: <b>{fmt(inc)}</b>💰/час\n\n<b>Здания:</b>\n'
    if not b:
        text += 'Пока пусто.'
    else:
        for k, cnt in b.items():
            if k in BUILDINGS:
                text += f'{BUILDINGS[k]["name"]} × {cnt}\n'

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🏗️ Построить', callback_data=f'build_menu_{idx}'))
    kb.add(types.InlineKeyboardButton('◀️ К городам', callback_data='menu_cities'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('build_menu_'))
def cb_build_menu(c):
    idx = int(c.data.split('_')[2])
    country = get_my_country(c.from_user.id)
    if not country or idx >= len(country['cities']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True)
        return

    text = (
        f'🏗️ <b>Что строить в «{country["cities"][idx]["name"]}»?</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n\n'
        f'Выбери здание:'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=buildings_kb(idx))


@bot.callback_query_handler(func=lambda c: c.data.startswith('build_') and c.data.count('_') == 2)
def cb_do_build(c):
    parts = c.data.split('_')
    idx = int(parts[1])
    bkey = parts[2]

    country = get_my_country(c.from_user.id)
    if not country or idx >= len(country['cities']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True)
        return

    if bkey not in BUILDINGS:
        bot.answer_callback_query(c.id, 'Неизвестное', show_alert=True)
        return

    b = BUILDINGS[bkey]
    if country['treas'] < b['cost']:
        bot.answer_callback_query(c.id, f'Не хватает {b["cost"] - int(country["treas"])}💰', show_alert=True)
        return

    country['treas'] -= b['cost']
    city = country['cities'][idx]
    city.setdefault('buildings', {})
    city['buildings'][bkey] = city['buildings'].get(bkey, 0) + 1

    add_news(f'{country["flag"]} {country["name"]}: построено {b["name"]}')
    save_data()

    bot.answer_callback_query(c.id, f'✅ {b["name"]}', show_alert=True)

    text = (
        f'🏗️ <b>Что строить в «{city["name"]}»?</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n\n'
        f'Выбери здание:'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=buildings_kb(idx))


@bot.callback_query_handler(func=lambda c: c.data == 'found_city')
def cb_found(c):
    country = get_my_country(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True)
        return
    cost = 5000
    if country['treas'] < cost:
        bot.answer_callback_query(c.id, f'Нужно {cost}💰', show_alert=True)
        return
    country['treas'] -= cost
    name = f'Город-{len(country["cities"]) + 1}'
    country['cities'].append({'name': name, 'pop': 100000, 'buildings': {}})
    add_news(f'{country["flag"]} {country["name"]}: основан {name}')
    save_data()

    bot.answer_callback_query(c.id, f'✅ {name}', show_alert=True)
    text = '🏙️ <b>Твои города</b>\n\nВыбери город:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=cities_menu_kb(country))


@bot.callback_query_handler(func=lambda c: c.data == 'menu_news')
def cb_news(c):
    text = '<b>📰 Новости мира</b>\n━━━━━━━━━━━━━━━\n\n'
    if not data['news']:
        text += 'Пока пусто.'
    else:
        for n in data['news'][:15]:
            text += f'• {n["text"]}\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_news'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_top')
def cb_top(c):
    countries = sorted(data['countries'].values(), key=lambda x: x['treas'], reverse=True)[:10]
    text = '<b>🏆 Топ стран по казне</b>\n━━━━━━━━━━━━━━━\n\n'
    for i, c in enumerate(countries, 1):
        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'{i}.'
        text += f'{medal} {c["flag"]} {c["name"]} — {fmt(c["treas"])}💰\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_top'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_help')
def cb_help(c):
    text = (
        '🏛️ <b>RP Countries — Помощь</b>\n'
        '━━━━━━━━━━━━━━━\n\n'
        '<b>🎯 Цель:</b> развивай страну.\n\n'
        '<b>🏗️ Здания:</b>\n'
        '🌾 Ферма — еда\n'
        '🏭 Завод — деньги\n'
        '⚔️ Казармы — армия\n'
        '🎓 Школа — технологии\n'
        '🏥 Больница — стабильность\n'
        '🚔 Полиция — стабильность\n'
        '⛏️ Шахта — металл\n'
        '🛢️ Нефтевышка — нефть\n\n'
        '<b>💡 Экономика тикает раз в час.</b>\n'
        'Города приносят доход автоматически.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


if __name__ == '__main__':
    print('RP Countries bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
