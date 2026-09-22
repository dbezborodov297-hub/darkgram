import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
TOP_CACHE_FILE = 'top_cache.json'

ADMIN_IDS = [8907438590]
TOKEN = '8747895563:AAF8QcoYgXxdWVLm_HE0MREaM34YPCnpKdM'

START_MEMORY = 5.0
START_TOKENS = 100
START_SPEED = 0.5
HACK_COOLDOWN = 10
HACK_MIN = 5
HACK_MAX = 15
OFFLINE_MAX = 8 * 3600
TOP_REFRESH = 300

MEMORY_PACKS = [
    {'kb': 5,   'price': 50},
    {'kb': 10,  'price': 200},
    {'kb': 25,  'price': 800},
    {'kb': 50,  'price': 3000},
    {'kb': 100, 'price': 12000},
    {'kb': 250, 'price': 50000},
    {'kb': 500, 'price': 200000},
    {'kb': 1000,'price': 800000},
    {'kb': 5000,'price': 5000000},
    {'kb': 10000,'price': 25000000},
    {'kb': 50000,'price': 150000000},
    {'kb': 100000,'price': 800000000},
    {'kb': 500000,'price': 5000000000},
    {'kb': 1000000,'price': 30000000000},
    {'kb': 5000000,'price': 200000000000},
    {'kb': 10000000,'price': 1500000000000},
    {'kb': 50000000,'price': 10000000000000},
    {'kb': 100000000,'price': 80000000000000},
    {'kb': 500000000,'price': 500000000000000},
    {'kb': 1000000000,'price': 3000000000000000},
]

COMPUTERS = [
    {'id': 'laptop',   'name': 'Ноутбук',      'emoji': '🖥', 'price': 50,     'income': 1},
    {'id': 'pc',       'name': 'ПК',           'emoji': '💻', 'price': 200,    'income': 5},
    {'id': 'server',   'name': 'Сервер',       'emoji': '🖥', 'price': 1000,   'income': 25},
    {'id': 'datacent', 'name': 'Дата-центр',   'emoji': '🗄', 'price': 5000,   'income': 150},
    {'id': 'farm',     'name': 'Ферма',        'emoji': '🏭', 'price': 25000,  'income': 800},
    {'id': 'quantum',  'name': 'Квантовый ПК', 'emoji': '🚀', 'price': 100000, 'income': 5000},
    {'id': 'neural',   'name': 'Нейросеть',    'emoji': '🌌', 'price': 500000, 'income': 30000},
    {'id': 'god',      'name': 'ИИ-Бог',       'emoji': '🧠', 'price': 2000000,'income': 200000},
]

SPEED_PACKS = [
    {'speed': 0.5, 'price': 100},
    {'speed': 1,   'price': 250},
    {'speed': 2,   'price': 600},
    {'speed': 5,   'price': 1500},
    {'speed': 10,  'price': 5000},
    {'speed': 25,  'price': 15000},
    {'speed': 50,  'price': 50000},
    {'speed': 100, 'price': 200000},
    {'speed': 500, 'price': 1000000},
    {'speed': 1000,'price': 5000000},
]

def load_json(f, d):
    if not os.path.exists(f): return d
    try:
        with open(f, 'r', encoding='utf-8') as fh: return json.load(fh)
    except: return d

def save_json(f, d):
    with open(f, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)

def load_stats(): return load_json(STATS_FILE, {})
def save_stats(d): save_json(STATS_FILE, d)
def load_top_cache(): return load_json(TOP_CACHE_FILE, [])

def get_player(uid, fname='Anonymous', uname=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': fname or 'Anonymous',
            'username': uname or '',
            'memory': START_MEMORY,
            'tokens': START_TOKENS,
            'speed': START_SPEED,
            'computers': {},
            'last_hack': 0,
            'last_update': int(time.time()),
            'total_earned': 0
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Anonymous')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {
            'memory': START_MEMORY, 'tokens': START_TOKENS,
            'speed': START_SPEED, 'computers': {},
            'last_hack': 0, 'last_update': int(time.time()),
            'total_earned': 0
        }
        for f, v in defaults.items():
            if f not in stats[k]: stats[k][f] = v
    save_stats(stats)
    return stats[k]

def update_player(uid, data):
    stats = load_stats()
    stats[str(uid)] = data
    save_stats(stats)

def income_per_sec(p):
    total = 0
    computers = p.get('computers', {})
    for c in COMPUTERS:
        count = computers.get(c['id'], 0)
        total += count * c['income']
    return total

def apply_income(p):
    now = int(time.time())
    last = p.get('last_update', now)
    elapsed = min(now - last, OFFLINE_MAX)
    if elapsed <= 0: return p
    speed = p.get('speed', START_SPEED)
    p['memory'] = p.get('memory', START_MEMORY) + speed * elapsed
    inc = income_per_sec(p) * elapsed
    if inc > 0:
        p['tokens'] = p.get('tokens', 0) + inc
        p['total_earned'] = p.get('total_earned', 0) + inc
    p['last_update'] = now
    return p

def fmt_num(n):
    n = float(n)
    if n >= 1_000_000_000_000:
        return f"{int(n//1_000_000_000_000)}T"
    if n >= 1_000_000_000:
        v = n / 1_000_000_000
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'B') if v < 100 else f"{int(v)}B"
    if n >= 1_000_000:
        v = n / 1_000_000
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'M') if v < 100 else f"{int(v)}M"
    if n >= 1_000:
        v = n / 1_000
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'K') if v < 100 else f"{int(v)}K"
    return str(int(n))

def fmt_memory(kb):
    kb = float(kb)
    if kb >= 1_000_000_000:
        return f"{kb/1_000_000_000:.2f} TB"
    if kb >= 1_000_000:
        return f"{kb/1_000_000:.2f} GB"
    if kb >= 1_000:
        return f"{kb/1_000:.2f} MB"
    return f"{kb:.1f} KB"

def btn(text, data, style=None):
    if style:
        try:
            return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
        except TypeError:
            return types.InlineKeyboardButton(text=text, callback_data=data)
    return types.InlineKeyboardButton(text=text, callback_data=data)

bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot running')

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

def update_loop():
    while True:
        try:
            stats = load_stats()
            now = int(time.time())
            for k in list(stats.keys()):
                p = stats[k]
                last = p.get('last_update', now)
                elapsed = min(now - last, OFFLINE_MAX)
                if elapsed > 0:
                    speed = p.get('speed', START_SPEED)
                    p['memory'] = p.get('memory', START_MEMORY) + speed * elapsed
                    inc = income_per_sec(p) * elapsed
                    if inc > 0:
                        p['tokens'] = p.get('tokens', 0) + inc
                        p['total_earned'] = p.get('total_earned', 0) + inc
                    p['last_update'] = now
                    stats[k] = p
            save_stats(stats)
        except Exception as e:
            print('update loop err:', e)
        time.sleep(5)

def top_loop():
    while True:
        try:
            stats = load_stats()
            arr = []
            for k, p in stats.items():
                arr.append({
                    'uid': k,
                    'name': p.get('first_name', 'Anonymous'),
                    'username': p.get('username', ''),
                    'memory': p.get('memory', 0),
                    'tokens': p.get('tokens', 0)
                })
            arr.sort(key=lambda x: x['memory'], reverse=True)
            save_json(TOP_CACHE_FILE, arr[:50])
            print('Top refreshed')
        except Exception as e:
            print('top loop err:', e)
        time.sleep(TOP_REFRESH)

threading.Thread(target=update_loop, daemon=True).start()
threading.Thread(target=top_loop, daemon=True).start()

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn('🖥 Мой ИИ', 'ai_main', 'primary'))
    kb.add(
        btn('🛒 Память', 'ai_mem_0', 'success'),
        btn('💻 Компьютеры', 'ai_comp_0', 'primary')
    )
    kb.add(
        btn('⚡ Ускорители', 'ai_speed_0', 'success'),
        btn('📊 Статистика', 'ai_stats', 'primary')
    )
    kb.add(btn('🏆 Топ', 'ai_top', 'success'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    p = get_player(uid, m.from_user.first_name, m.from_user.username)
    p = apply_income(p)
    update_player(uid, p)

    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    inc = income_per_sec(p)
    speed = p.get('speed', START_SPEED)

    text = (
        f"🎭 <b>ХАКЕР-ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{m.from_user.first_name}</b>!\n\n"
        f"🖥 <b>МОЙ ИИ</b>\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"⚡ Скорость: <b>{speed} KB/сек</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>\n\n"
        f"👇 <i>Выбирай:</i>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>Как играть:</b>\n"
        f"1️⃣ Память капает сама (старт 0.5 KB/сек)\n"
        f"2️⃣ Трать память на компьютеры\n"
        f"3️⃣ Компьютеры дают токены/сек\n"
        f"4️⃣ Токены — на ускорители памяти\n"
        f"5️⃣ Больше памяти → топ → круче!\n\n"
        f"🏆 /top — топ по памяти\n"
        f"⏱ Топ обновляется раз в 5 минут\n"
        f"🌙 Офлайн — до 8 часов."
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['top'])
def cmd_top(m):
    arr = load_top_cache()
    if not arr:
        text = "🏆 Топ пока пуст."
    else:
        text = "🏆 <b>ТОП ПО ПАМЯТИ</b>\n━━━━━━━━━━━━━━━\n\n"
        medals = ['🥇', '🥈', '🥉']
        for i, u in enumerate(arr[:15]):
            name = u.get('username') and '@' + u['username'] or u.get('name', 'Anonymous')
            medal = medals[i] if i < 3 else f"<b>{i+1}.</b>"
            text += f"{medal} {name} — <b>{fmt_memory(u['memory'])}</b>\n"
        text += "\n⏱ <i>Обновляется каждые 5 минут</i>"
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

def ai_main_text(p):
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    inc = income_per_sec(p)
    speed = p.get('speed', START_SPEED)
    total = fmt_num(p.get('total_earned', 0))
    comps = p.get('computers', {})
    comp_count = sum(comps.values())
    return (
        f"🖥 <b>МОЙ ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"⚡ Скорость: <b>{speed} KB/сек</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>\n"
        f"💻 Компьютеров: <b>{comp_count}</b>\n"
        f"📈 Всего заработано: <b>{total}</b>"
    )

def ai_main_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('🛒 Память', 'ai_mem_0', 'success'),
        btn('💻 Компьютеры', 'ai_comp_0', 'primary')
    )
    kb.add(
        btn('⚡ Ускорители', 'ai_speed_0', 'success'),
        btn('📊 Статистика', 'ai_stats', 'primary')
    )
    kb.add(btn('🏆 Топ', 'ai_top', 'success'))
    kb.add(btn('🔄 Обновить', 'ai_main', 'primary'))
    kb.add(btn('◀️ Меню', 'menu_main', 'danger'))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == 'ai_main')
def cb_ai_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    try:
        bot.edit_message_text(ai_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=ai_main_kb())
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_menu_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    inc = income_per_sec(p)
    speed = p.get('speed', START_SPEED)
    text = (
        f"🎭 <b>ХАКЕР-ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"⚡ Скорость: <b>{speed} KB/сек</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>"
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=main_menu())
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_top')
def cb_top(call):
    arr = load_top_cache()
    if not arr:
        text = "🏆 Топ пока пуст."
    else:
        text = "🏆 <b>ТОП ПО ПАМЯТИ</b>\n━━━━━━━━━━━━━━━\n\n"
        medals = ['🥇', '🥈', '🥉']
        for i, u in enumerate(arr[:15]):
            name = u.get('username') and '@' + u['username'] or u.get('name', 'Anonymous')
            medal = medals[i] if i < 3 else f"<b>{i+1}.</b>"
            text += f"{medal} {name} — <b>{fmt_memory(u['memory'])}</b>\n"
        text += "\n⏱ <i>Обновляется каждые 5 минут</i>"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

PAGE_SIZE = 5

def mem_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = MEMORY_PACKS[start:end]
    total_pages = (len(MEMORY_PACKS) + PAGE_SIZE - 1) // PAGE_SIZE
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    text = (
        f"🛒 <b>ПАМЯТЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Сейчас: <b>{mem}</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"📄 Стр. {page+1}/{total_pages}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(items):
        idx = start + i
        kb.add(btn(f"+{item['kb']} KB — {fmt_num(item['price'])} 🪙",
            f'ai_mem_buy_{idx}', 'success'))
    nav = []
    if page > 0: nav.append(btn('◀️', f'ai_mem_{page-1}', 'primary'))
    nav.append(btn(f'{page+1}/{total_pages}', 'ai_none', 'primary'))
    if page < total_pages - 1: nav.append(btn('▶️', f'ai_mem_{page+1}', 'primary'))
    kb.row(*nav)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    return text, kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_mem_') and not c.data.startswith('ai_mem_buy_'))
def cb_mem(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    try: page = int(call.data.replace('ai_mem_', ''))
    except: page = 0
    text, kb = mem_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_mem_buy_'))
def cb_mem_buy(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    idx = int(call.data.replace('ai_mem_buy_', ''))
    if idx < 0 or idx >= len(MEMORY_PACKS):
        bot.answer_callback_query(call.id, "Ошибка"); return
    item = MEMORY_PACKS[idx]
    if p.get('tokens', 0) < item['price']:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_num(item['price'])} 🪙"); return
    p['tokens'] -= item['price']
    p['memory'] = p.get('memory', START_MEMORY) + item['kb']
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{item['kb']} KB!")
    page = idx // PAGE_SIZE
    text, kb = mem_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass

def comp_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = COMPUTERS[start:end]
    total_pages = (len(COMPUTERS) + PAGE_SIZE - 1) // PAGE_SIZE
    mem = fmt_memory(p.get('memory', START_MEMORY))
    comps = p.get('computers', {})
    text = (
        f"💻 <b>КОМПЬЮТЕРЫ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"📄 Стр. {page+1}/{total_pages}\n\n"
        f"<i>Покупаешь за память — приносят токены</i>"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, c in enumerate(items):
        idx = start + i
        owned = comps.get(c['id'], 0)
        label = f"{c['emoji']} {c['name']} — {fmt_memory(c['price'])}"
        if owned > 0:
            label += f" (x{owned})"
        kb.add(btn(label, f'ai_comp_buy_{idx}', 'primary'))
    nav = []
    if page > 0: nav.append(btn('◀️', f'ai_comp_{page-1}', 'success'))
    nav.append(btn(f'{page+1}/{total_pages}', 'ai_none', 'primary'))
    if page < total_pages - 1: nav.append(btn('▶️', f'ai_comp_{page+1}', 'success'))
    kb.row(*nav)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    return text, kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_comp_') and not c.data.startswith('ai_comp_buy_'))
def cb_comp(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    try: page = int(call.data.replace('ai_comp_', ''))
    except: page = 0
    text, kb = comp_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_comp_buy_'))
def cb_comp_buy(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    idx = int(call.data.replace('ai_comp_buy_', ''))
    if idx < 0 or idx >= len(COMPUTERS):
        bot.answer_callback_query(call.id, "Ошибка"); return
    item = COMPUTERS[idx]
    if p.get('memory', START_MEMORY) < item['price']:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_memory(item['price'])}"); return
    p['memory'] = p.get('memory', START_MEMORY) - item['price']
    comps = p.get('computers', {})
    comps[item['id']] = comps.get(item['id'], 0) + 1
    p['computers'] = comps
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    page = idx // PAGE_SIZE
    text, kb = comp_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass

def speed_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = SPEED_PACKS[start:end]
    total_pages = (len(SPEED_PACKS) + PAGE_SIZE - 1) // PAGE_SIZE
    speed = p.get('speed', START_SPEED)
    tokens = fmt_num(p.get('tokens', 0))
    text = (
        f"⚡ <b>УСКОРИТЕЛИ ПАМЯТИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚡ Сейчас: <b>{speed} KB/сек</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"📄 Стр. {page+1}/{total_pages}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(items):
        idx = start + i
        kb.add(btn(f"+{item['speed']} KB/сек — {fmt_num(item['price'])} 🪙",
            f'ai_speed_buy_{idx}', 'success'))
    nav = []
    if page > 0: nav.append(btn('◀️', f'ai_speed_{page-1}', 'primary'))
    nav.append(btn(f'{page+1}/{total_pages}', 'ai_none', 'primary'))
    if page < total_pages - 1: nav.append(btn('▶️', f'ai_speed_{page+1}', 'primary'))
    kb.row(*nav)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    return text, kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_speed_') and not c.data.startswith('ai_speed_buy_'))
def cb_speed(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    try: page = int(call.data.replace('ai_speed_', ''))
    except: page = 0
    text, kb = speed_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_speed_buy_'))
def cb_speed_buy(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    idx = int(call.data.replace('ai_speed_buy_', ''))
    if idx < 0 or idx >= len(SPEED_PACKS):
        bot.answer_callback_query(call.id, "Ошибка"); return
    item = SPEED_PACKS[idx]
    if p.get('tokens', 0) < item['price']:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_num(item['price'])} 🪙"); return
    p['tokens'] -= item['price']
    p['speed'] = p.get('speed', START_SPEED) + item['speed']
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{item['speed']} KB/сек!")
    page = idx // PAGE_SIZE
    text, kb = speed_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == 'ai_stats')
def cb_stats(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    inc = income_per_sec(p)
    total = fmt_num(p.get('total_earned', 0))
    speed = p.get('speed', START_SPEED)
    comps = p.get('computers', {})
    lines = []
    for c in COMPUTERS:
        cnt = comps.get(c['id'], 0)
        if cnt > 0:
            lines.append(f"{c['emoji']} {c['name']}: x{cnt} ({fmt_num(cnt*c['income'])}/сек)")
    comps_text = "\n".join(lines) if lines else "Нет компьютеров"
    text = (
        f"📊 <b>СТАТИСТИКА</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"⚡ Скорость: <b>{speed} KB/сек</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>\n"
        f"📈 Всего заработано: <b>{total}</b>\n\n"
        f"<b>Компьютеры:</b>\n{comps_text}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_none')
def cb_none(call):
    bot.answer_callback_query(call.id)

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start','🖥 Игра'),
            types.BotCommand('help','💬 Помощь'),
            types.BotCommand('top','🏆 Топ'),
        ])
    except: pass

set_commands()
print('Bot started')
bot.infinity_polling()
