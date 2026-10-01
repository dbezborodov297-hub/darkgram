import telebot
import json
import os
import time
import random
import threading
from telebot import types

TOKEN = '8471116013:AAF1MVURZqUPXzAUWMyQo5rx8dps9x1z4rw'
DATA_FILE = 'rp_data.json'

bot = telebot.TeleBot(TOKEN)

# ============================================================
# ЗДАНИЯ
# ============================================================
BUILDINGS = {
    'farm':     {'name': '🌾 Ферма',      'cost': 300,  'desc': '+200 еды/мин'},
    'factory':  {'name': '🏭 Завод',      'cost': 800,  'desc': '+500💰/мин, -1 стаб.'},
    'barracks': {'name': '⚔️ Казармы',    'cost': 500,  'desc': '+100 армии/мин'},
    'school':   {'name': '🎓 Школа',      'cost': 1000, 'desc': '+0.5 тех./мин'},
    'hospital': {'name': '🏥 Больница',   'cost': 700,  'desc': '+2 стаб./мин'},
    'police':   {'name': '🚔 Полиция',    'cost': 400,  'desc': '+1 стаб./мин'},
    'mine':     {'name': '⛏️ Шахта',      'cost': 600,  'desc': '+150 металла/мин'},
    'oilrig':   {'name': '🛢️ Нефтевышка', 'cost': 900,  'desc': '+100 нефти/мин'},
    'market':   {'name': '🏪 Рынок',      'cost': 700,  'desc': '+300💰/мин'},
    'bank':     {'name': '🏦 Банк',       'cost': 1500, 'desc': '+800💰/мин'},
    'wall':     {'name': '🛡️ Стена',      'cost': 1200, 'desc': '+30% защиты'},
    'port':     {'name': '⚓ Порт',       'cost': 1000, 'desc': '+200💰/+100 еды'},
}

PROVINCE_TYPES = {
    'plain':    {'name': '🌾 Равнина',   'bonus': {'food': 500},    'desc': 'Много еды'},
    'forest':   {'name': '🌲 Лес',       'bonus': {'food': 200, 'metal': 100}, 'desc': 'Еда + металл'},
    'mountain': {'name': '⛰️ Горы',      'bonus': {'metal': 400},   'desc': 'Много металла'},
    'desert':   {'name': '🏜️ Пустыня',   'bonus': {'oil': 300},     'desc': 'Нефть'},
    'coast':    {'name': '🌊 Побережье', 'bonus': {'treasury': 400},'desc': 'Торговля'},
    'city':     {'name': '🏙️ Город',     'bonus': {'treasury': 600},'desc': 'Экономика'},
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


def make_provinces(pop):
    types_pool = ['plain', 'forest', 'mountain', 'desert', 'coast', 'city']
    random.shuffle(types_pool)
    return [
        {'name': f'Провинция {i+1}', 'type': types_pool[i % len(types_pool)],
         'pop': pop // 6, 'buildings': {}}
        for i in range(5)
    ]


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    d = {'countries': {}, 'news': [], 'alliances': [], 'wars': []}
    for i, c in enumerate(COUNTRIES_25):
        d['countries'][str(i)] = {
            'id': i, 'name': c['name'], 'flag': c['flag'],
            'owner': None, 'pop': c['pop'], 'treas': c['treas'],
            'army': c['army'], 'tech': c['tech'], 'stability': 70,
            'food': 5000, 'metal': 2000, 'oil': 1000,
            'isNpc': True, 'bonus': 0,
            'provinces': make_provinces(c['pop']),
        }
    return d


def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print('save err:', e)


data = load_data()


def add_news(t):
    data['news'].insert(0, {'time': int(time.time()), 'text': t})
    data['news'] = data['news'][:50]


def get_my(uid):
    for c in data['countries'].values():
        if c.get('owner') == uid:
            return c
    return None


def get_country(cid):
    return data['countries'].get(str(cid))


def fmt(n):
    n = int(n)
    if n >= 1e9: return f'{n/1e9:.1f} млрд'
    if n >= 1e6: return f'{n/1e6:.1f} млн'
    if n >= 1e3: return f'{n/1e3:.1f} тыс'
    return str(n)


def find_alliance(c1, c2):
    for a in data.get('alliances', []):
        if str(c1) in a['members'] and str(c2) in a['members']:
            return a
    return None


def is_at_war(c1, c2):
    for w in data.get('wars', []):
        if {w['attacker'], w['defender']} == {str(c1), str(c2)}:
            return True
    return False


def province_income(p, c):
    inc = p['pop'] * 0.0001 + 20
    t = p.get('type', 'plain')
    if t in PROVINCE_TYPES:
        inc += PROVINCE_TYPES[t]['bonus'].get('treasury', 0)
    b = p.get('buildings', {})
    for k, cnt in b.items():
        if k == 'factory': inc += 500 * cnt
        elif k == 'market': inc += 300 * cnt
        elif k == 'bank': inc += 800 * cnt
        elif k == 'port': inc += 200 * cnt
    inc *= (1 + c['tech'] * 0.05) * (1 + c.get('bonus', 0))
    return inc


def country_income(c):
    return sum(province_income(p, c) for p in c['provinces'])


# ============================================================
# ТИК
# ============================================================
def tick():
    for c in data['countries'].values():
        income = country_income(c)
        expense = c['army'] * 0.05
        c['treas'] += income - expense
        if c['treas'] < 0:
            c['treas'] = 0
            c['stability'] -= 2

        for p in c['provinces']:
            t = p.get('type', 'plain')
            if t in PROVINCE_TYPES:
                bonus = PROVINCE_TYPES[t]['bonus']
                c['food'] += bonus.get('food', 0)
                c['metal'] += bonus.get('metal', 0)
                c['oil'] += bonus.get('oil', 0)

            b = p.get('buildings', {})
            for k, cnt in b.items():
                if k == 'farm': c['food'] += 200 * cnt
                elif k == 'mine': c['metal'] += 150 * cnt
                elif k == 'oilrig': c['oil'] += 100 * cnt
                elif k == 'barracks': c['army'] += 100 * cnt
                elif k == 'school': c['tech'] += 0.5 * cnt
                elif k == 'hospital': c['stability'] += 2 * cnt
                elif k == 'police': c['stability'] += 1 * cnt
                elif k == 'factory': c['stability'] -= 1 * cnt
                elif k == 'port': c['food'] += 100 * cnt

        c['stability'] = max(0, min(100, c['stability']))

        if c['food'] > c['pop'] / 500:
            growth = int((c['food'] / 500) * (c['stability'] / 100))
            c['pop'] += growth
            c['food'] -= growth * 5

        if c['isNpc'] and random.random() < 0.05:
            npc_action(c)

    process_wars()

    if random.random() < 0.1:
        random_event()

    save_data()


def npc_action(c):
    if not c['provinces']: return
    actions = []
    if c['treas'] > 500: actions.append('farm')
    if c['treas'] > 1000: actions.append('factory')
    if c['treas'] > 600: actions.append('barracks')
    if c['stability'] < 50: actions.append('police')
    if c['treas'] > 900: actions.append('mine')
    if c['treas'] > 2000: actions.append('wall')
    if not actions: return
    bkey = random.choice(actions)
    cost = BUILDINGS[bkey]['cost']
    if c['treas'] >= cost:
        c['treas'] -= cost
        p = random.choice(c['provinces'])
        p.setdefault('buildings', {})
        p['buildings'][bkey] = p['buildings'].get(bkey, 0) + 1


def process_wars():
    finished = []
    for w in data.get('wars', []):
        w['turns'] = w.get('turns', 0) + 1
        a = get_country(w['attacker'])
        d = get_country(w['defender'])
        if not a or not d:
            finished.append(w); continue

        a_power = a['army'] * (1 + a['tech'] * 0.1) * (a['stability'] / 100)
        d_power = d['army'] * (1 + d['tech'] * 0.1) * (d['stability'] / 100)
        for p in d['provinces']:
            wall = p.get('buildings', {}).get('wall', 0)
            d_power *= (1 + wall * 0.3)

        if random.random() < 0.5:
            d['army'] = max(0, d['army'] - int(d['army'] * 0.15))
            a['army'] = max(0, a['army'] - int(a['army'] * 0.08))
            d['stability'] -= 3
        else:
            a['army'] = max(0, a['army'] - int(a['army'] * 0.15))
            d['army'] = max(0, d['army'] - int(d['army'] * 0.08))
            a['stability'] -= 3

        if a['army'] < a['pop'] * 0.0001 or d['army'] < d['pop'] * 0.0001 or w['turns'] >= 10:
            winner, loser = (a, d) if a_power > d_power else (d, a)
            loot = int(loser['treas'] * 0.3)
            winner['treas'] += loot
            loser['treas'] -= loot
            cap_msg = ''
            if loser['provinces'] and winner['provinces']:
                captured = loser['provinces'].pop(0)
                winner['provinces'].append(captured)
                cap_msg = f' и захватил провинцию «{captured["name"]}»'
            add_news(f'🏆 Война {a["flag"]} {a["name"]} vs {d["flag"]} {d["name"]} окончена! Победил {winner["flag"]} {winner["name"]}, забрал {fmt(loot)}💰{cap_msg}')
            finished.append(w)

    for w in finished:
        data['wars'].remove(w)


def random_event():
    events = [
        ('🌋 Извержение вулкана в {name}!', lambda c: c.update({'stability': max(0, c['stability'] - 15)})),
        ('💎 Найдено золото в {name}!', lambda c: c.update({'treas': c['treas'] + 3000})),
        ('🌾 Урожай в {name}!', lambda c: c.update({'food': c['food'] + 5000})),
        ('⚔️ Бунт в {name}!', lambda c: c.update({'stability': max(0, c['stability'] - 20)})),
        ('🎉 Бум в {name}!', lambda c: c.update({'treas': c['treas'] + 5000})),
    ]
    ev, action = random.choice(events)
    c = random.choice(list(data['countries'].values()))
    try:
        action(c)
        add_news(ev.format(name=f'{c["flag"]} {c["name"]}'))
    except: pass


def start_tick():
    while True:
        time.sleep(60)
        try:
            tick()
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
        types.InlineKeyboardButton('🗺️ Провинции', callback_data='menu_prov'),
    )
    kb.add(
        types.InlineKeyboardButton('⚔️ Армия', callback_data='menu_army'),
        types.InlineKeyboardButton('🤝 Дипломатия', callback_data='menu_dip'),
    )
    kb.add(
        types.InlineKeyboardButton('⚔️ Война', callback_data='menu_war'),
        types.InlineKeyboardButton('🛒 Торговля', callback_data='menu_trade'),
    )
    kb.add(
        types.InlineKeyboardButton('📰 Новости', callback_data='menu_news'),
        types.InlineKeyboardButton('🏆 Топ', callback_data='menu_top'),
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


def provinces_kb(c):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(c['provinces']):
        t = PROVINCE_TYPES.get(p['type'], {'name': '❓'})
        kb.add(types.InlineKeyboardButton(
            f'{t["name"]} {p["name"]} ({fmt(p["pop"])})',
            callback_data=f'prov_{i}'
        ))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    return kb


def buildings_kb(idx):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for bkey, b in BUILDINGS.items():
        kb.add(types.InlineKeyboardButton(
            f'{b["name"]} ({b["cost"]}💰)',
            callback_data=f'build_{idx}_{bkey}'
        ))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_prov'))
    return kb


# ============================================================
# КОМАНДЫ
# ============================================================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    c = get_my(m.from_user.id)
    name = m.from_user.first_name or 'друг'
    if c:
        text = f'🏛️ Привет, {name}!\n\nТы правишь {c["flag"]} <b>{c["name"]}</b>.\n\nВыбери действие:'
        bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())
    else:
        text = (
            f'🏛️ <b>RP Countries</b>\n\n'
            f'Привет, {name}!\n\n'
            f'Игра про управление страной.\n\n'
            f'⚠️ Страну можно выбрать <b>только один раз</b>.\n\n'
            f'Жми кнопку:'
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
    country = get_my(c.from_user.id)
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
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    income = country_income(country)
    expense = country['army'] * 0.05
    total_b = sum(sum(p.get('buildings', {}).values()) for p in country['provinces'])
    my_wars = [w for w in data.get('wars', []) if str(country['id']) in (w['attacker'], w['defender'])]
    my_ally = [a for a in data.get('alliances', []) if str(country['id']) in a['members']]

    text = (
        f'🏛️ <b>{country["flag"]} {country["name"]}</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: <b>{fmt(country["pop"])}</b>\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n'
        f'⚔️ Армия: <b>{fmt(country["army"])}</b>\n'
        f'🔬 Технологии: <b>{int(country["tech"])}</b>\n'
        f'📊 Стабильность: <b>{int(country["stability"])}%</b>\n\n'
        f'🌾 Еда: {fmt(country["food"])}\n'
        f'⛏️ Металл: {fmt(country["metal"])}\n'
        f'🛢️ Нефть: {fmt(country["oil"])}\n\n'
        f'🗺️ Провинций: <b>{len(country["provinces"])}</b>\n'
        f'🏗️ Зданий: <b>{total_b}</b>\n\n'
        f'📈 Доход: <b>+{fmt(income)}</b>💰/мин\n'
        f'📉 Расход: <b>-{fmt(expense)}</b>💰/мин\n'
        f'💵 Итого: <b>{fmt(income - expense)}</b>💰/мин\n'
    )
    if my_wars: text += f'\n⚔️ <b>ВОЙНА</b>: {len(my_wars)} активных'
    if my_ally: text += f'\n🤝 Союзов: {len(my_ally)}'

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_my'),
        types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'),
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_prov')
def cb_prov(c):
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    text = f'🗺️ <b>Провинции {country["flag"]} {country["name"]}</b>\n\nВыбери провинцию:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=provinces_kb(country))


@bot.callback_query_handler(func=lambda c: c.data.startswith('prov_'))
def cb_prov_one(c):
    idx = int(c.data.split('_')[1])
    country = get_my(c.from_user.id)
    if not country or idx >= len(country['provinces']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True); return
    p = country['provinces'][idx]
    t = PROVINCE_TYPES.get(p['type'], {'name': '❓', 'desc': ''})
    b = p.get('buildings', {})
    inc = province_income(p, country)

    text = (
        f'{t["name"]} <b>{p["name"]}</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'Тип: {t["name"]} — {t["desc"]}\n'
        f'👥 Население: <b>{fmt(p["pop"])}</b>\n'
        f'💡 Доход: <b>+{fmt(inc)}</b>💰/мин\n\n'
        f'<b>Здания:</b>\n'
    )
    if not b:
        text += 'Пока пусто.'
    else:
        for k, cnt in b.items():
            if k in BUILDINGS:
                text += f'{BUILDINGS[k]["name"]} × {cnt}\n'

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🏗️ Построить', callback_data=f'buildmenu_{idx}'))
    kb.add(types.InlineKeyboardButton('◀️ К провинциям', callback_data='menu_prov'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('buildmenu_'))
def cb_bm(c):
    idx = int(c.data.split('_')[1])
    country = get_my(c.from_user.id)
    if not country or idx >= len(country['provinces']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True); return
    text = (
        f'🏗️ <b>Что строить в «{country["provinces"][idx]["name"]}»?</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n\n'
        f'Выбери здание:'
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=buildings_kb(idx))


@bot.callback_query_handler(func=lambda c: c.data.startswith('build_') and c.data.count('_') == 2)
def cb_build(c):
    parts = c.data.split('_')
    idx = int(parts[1])
    bkey = parts[2]
    country = get_my(c.from_user.id)
    if not country or idx >= len(country['provinces']):
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True); return
    if bkey not in BUILDINGS:
        bot.answer_callback_query(c.id, 'Неизвестное', show_alert=True); return
    b = BUILDINGS[bkey]
    if country['treas'] < b['cost']:
        bot.answer_callback_query(c.id, f'Не хватает {b["cost"] - int(country["treas"])}💰', show_alert=True); return
    country['treas'] -= b['cost']
    p = country['provinces'][idx]
    p.setdefault('buildings', {})
    p['buildings'][bkey] = p['buildings'].get(bkey, 0) + 1
    add_news(f'{country["flag"]} {country["name"]}: построено {b["name"]}')
    save_data()
    bot.answer_callback_query(c.id, f'✅ {b["name"]}', show_alert=True)
    cb_bm(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_army')
def cb_army(c):
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    text = (
        f'⚔️ <b>Армия</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'⚔️ Сейчас: <b>{fmt(country["army"])}</b>\n'
        f'💰 Казна: <b>{fmt(country["treas"])}</b>\n\n'
        f'Найм: 1 солдат = 2💰\n'
    )
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('+1 000', callback_data='rec_1000'),
        types.InlineKeyboardButton('+5 000', callback_data='rec_5000'),
        types.InlineKeyboardButton('+10 000', callback_data='rec_10000'),
    )
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('rec_'))
def cb_rec(c):
    amount = int(c.data.split('_')[1])
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    cost = amount * 2
    if country['treas'] < cost:
        bot.answer_callback_query(c.id, f'Нужно {fmt(cost)}💰', show_alert=True); return
    country['treas'] -= cost
    country['army'] += amount
    save_data()
    bot.answer_callback_query(c.id, f'✅ +{fmt(amount)} солдат', show_alert=True)
    cb_army(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_trade')
def cb_trade(c):
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    text = (
        f'🛒 <b>Торговля</b>\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'🌾 Еда: {fmt(country["food"])} (1💰)\n'
        f'⛏️ Металл: {fmt(country["metal"])} (3💰)\n'
        f'🛢️ Нефть: {fmt(country["oil"])} (5💰)\n'
    )
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('🌾 1000', callback_data='sell_food_1000'),
        types.InlineKeyboardButton('⛏️ 500', callback_data='sell_metal_500'),
        types.InlineKeyboardButton('🛢️ 300', callback_data='sell_oil_300'),
    )
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('sell_'))
def cb_sell(c):
    parts = c.data.split('_')
    res, amount = parts[1], int(parts[2])
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    prices = {'food': 1, 'metal': 3, 'oil': 5}
    if country[res] < amount:
        bot.answer_callback_query(c.id, 'Недостаточно', show_alert=True); return
    country[res] -= amount
    money = amount * prices[res]
    country['treas'] += money
    save_data()
    bot.answer_callback_query(c.id, f'✅ +{fmt(money)}💰', show_alert=True)
    cb_trade(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_dip')
def cb_dip(c):
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    others = [x for x in data['countries'].values() if x['id'] != country['id'] and x.get('owner')]
    if not others:
        text = '🤝 Нет других игроков.\n\nСоюзы возможны только между игроками.'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for o in others:
        kb.add(types.InlineKeyboardButton(f'🤝 {o["flag"]} {o["name"]}', callback_data=f'ally_{o["id"]}'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    text = '🤝 <b>Предложить союз</b>\n\nВыбери страну:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('ally_'))
def cb_ally(c):
    target = c.data.split('_')[1]
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    t = get_country(target)
    if not t:
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True); return
    if is_at_war(country['id'], target):
        bot.answer_callback_query(c.id, 'Вы в войне', show_alert=True); return
    if find_alliance(country['id'], target):
        bot.answer_callback_query(c.id, 'Уже союз', show_alert=True); return
    data.setdefault('alliances', []).append({'members': [str(country['id']), str(target)], 'time': int(time.time())})
    add_news(f'🤝 {country["flag"]} {country["name"]} и {t["flag"]} {t["name"]} заключили союз')
    save_data()
    bot.answer_callback_query(c.id, '✅ Союз заключён!', show_alert=True)
    cb_dip(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_war')
def cb_war(c):
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    others = [x for x in data['countries'].values() if x['id'] != country['id']]
    kb = types.InlineKeyboardMarkup(row_width=1)
    for o in others[:10]:
        kb.add(types.InlineKeyboardButton(f'⚔️ {o["flag"]} {o["name"]} ({fmt(o["army"])})', callback_data=f'war_{o["id"]}'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    text = '⚔️ <b>Объявить войну</b>\n\nВыбери страну:'
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('war_'))
def cb_war_declare(c):
    target = c.data.split('_')[1]
    country = get_my(c.from_user.id)
    if not country:
        bot.answer_callback_query(c.id, 'Нет страны', show_alert=True); return
    t = get_country(target)
    if not t:
        bot.answer_callback_query(c.id, 'Не найдено', show_alert=True); return
    if find_alliance(country['id'], target):
        bot.answer_callback_query(c.id, 'Нельзя атаковать союзника', show_alert=True); return
    if is_at_war(country['id'], target):
        bot.answer_callback_query(c.id, 'Уже в войне', show_alert=True); return
    data.setdefault('wars', []).append({'attacker': str(country['id']), 'defender': str(target), 'turns': 0, 'time': int(time.time())})
    add_news(f'⚔️ {country["flag"]} {country["name"]} объявил войну {t["flag"]} {t["name"]}!')
    save_data()
    bot.answer_callback_query(c.id, '⚔️ Война объявлена!', show_alert=True)
    cb_main(c)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_news')
def cb_news(c):
    text = '📰 <b>Новости мира</b>\n━━━━━━━━━━━━━━━\n\n'
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
    top = sorted(data['countries'].values(), key=lambda x: x['treas'], reverse=True)[:10]
    text = '🏆 <b>Топ стран</b>\n━━━━━━━━━━━━━━━\n\n'
    for i, c in enumerate(top, 1):
        m = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'{i}.'
        text += f'{m} {c["flag"]} {c["name"]} — {fmt(c["treas"])}💰\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_top'))
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_all')
def cb_all(c):
    text = '🌍 <b>Выбери страну</b>\n\n⚠️ Выбор — навсегда!'
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=countries_kb(0))
    except:
        bot.send_message(c.message.chat.id, text, parse_mode='HTML', reply_markup=countries_kb(0))


@bot.callback_query_handler(func=lambda c: c.data.startswith('page_'))
def cb_page(c):
    page = int(c.data.split('_')[1])
    bot.edit_message_text('🌍 <b>Выбери страну</b>\n\n⚠️ Выбор — навсегда!',
                          c.message.chat.id, c.message.message_id,
                          parse_mode='HTML', reply_markup=countries_kb(page))


@bot.callback_query_handler(func=lambda c: c.data.startswith('take_'))
def cb_take(c):
    cid = c.data.split('_')[1]
    existing = get_my(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, f'У тебя уже есть {existing["name"]}', show_alert=True); return
    country = get_country(cid)
    if not country or country.get('owner'):
        bot.answer_callback_query(c.id, 'Занята', show_alert=True); return
    text = (
        f'🏛️ Выбрать <b>{country["flag"]} {country["name"]}</b>?\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👥 Население: {fmt(country["pop"])}\n'
        f'💰 Казна: {fmt(country["treas"])}\n'
        f'⚔️ Армия: {fmt(country["army"])}\n'
        f'🗺️ Провинций: {len(country["provinces"])}\n\n'
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
    existing = get_my(c.from_user.id)
    if existing:
        bot.answer_callback_query(c.id, 'Уже есть страна', show_alert=True); return
    country = get_country(cid)
    if not country or country.get('owner'):
        bot.answer_callback_query(c.id, 'Занята', show_alert=True); return
    country['owner'] = c.from_user.id
    country['isNpc'] = False
    add_news(f'{country["flag"]} {country["name"]}: новый правитель!')
    save_data()
    text = f'✅ Поздравляем!\n\nТы правишь {country["flag"]} <b>{country["name"]}</b>.\n\n{len(country["provinces"])} провинций готовы к развитию!'
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('🏛️ Моя страна', callback_data='menu_my'),
        types.InlineKeyboardButton('🗺️ Провинции', callback_data='menu_prov'),
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_help')
def cb_help(c):
    text = (
        '🏛️ <b>RP Countries — Помощь</b>\n'
        '━━━━━━━━━━━━━━━\n\n'
        '<b>🎯 Цель:</b> разбогатеть и захватить мир.\n\n'
        '<b>🗺️ Провинции:</b>\n'
        '5 штук, каждая со своим типом и бонусами:\n'
        '🌾 Равнина — еда\n'
        '🌲 Лес — еда+металл\n'
        '⛰️ Горы — металл\n'
        '🏜️ Пустыня — нефть\n'
        '🌊 Побережье — деньги\n'
        '🏙️ Город — экономика\n\n'
        '<b>🏗️ Здания (12):</b>\n'
        'Ферма, Завод, Казармы, Школа, Больница,\n'
        'Полиция, Шахта, Нефтевышка, Рынок, Банк,\n'
        'Стена, Порт\n\n'
        '<b>⚔️ Война:</b>\n'
        'Объяви войну → сражения → победитель\n'
        'забирает 30% казны и провинцию.\n\n'
        '<b>🤝 Союзы:</b>\n'
        'Только между игроками. Союзников\n'
        'нельзя атаковать.\n\n'
        '<b>🛒 Торговля:</b>\n'
        'Продавай еду/металл/нефть.\n\n'
        '<b>⏱️ Экономика:</b>\n'
        'Доход капает раз в минуту.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ В меню', callback_data='menu_main'))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode='HTML', reply_markup=kb)


if __name__ == '__main__':
    print('RP Countries bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
