import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
ADMIN_IDS = [8907438590]
TOKEN = '8747895563:AAF8QcoYgXxdWVLm_HE0MREaM34YPCnpKdM'

# ===== НАСТРОЙКИ =====
START_MEMORY = 5          # KB на старте
START_TOKENS = 100        # токенов на старте
START_COMPUTERS = {}      # нет компов на старте
HACK_COOLDOWN = 10        # сек
HACK_MIN = 5              # мин токенов с хака
HACK_MAX = 15             # макс токенов с хака
OFFLINE_MAX = 8 * 3600    # 8 часов офлайна

# ===== ПАМЯТЬ (улучшения) =====
MEMORY_PACKS = [
    {'kb': 5,   'price': 50,     'name': '+5 KB'},
    {'kb': 10,  'price': 200,    'name': '+10 KB'},
    {'kb': 25,  'price': 800,    'name': '+25 KB'},
    {'kb': 50,  'price': 3000,   'name': '+50 KB'},
    {'kb': 100, 'price': 12000,  'name': '+100 KB'},
    {'kb': 250, 'price': 50000,  'name': '+250 KB'},
    {'kb': 500, 'price': 200000, 'name': '+500 KB'},
    {'kb': 1000,'price': 800000, 'name': '+1 MB'},
    {'kb': 5000,'price': 5000000,'name': '+5 MB'},
    {'kb': 10000,'price': 25000000,'name': '+10 MB'},
    {'kb': 50000,'price': 150000000,'name': '+50 MB'},
    {'kb': 100000,'price': 800000000,'name': '+100 MB'},
    {'kb': 500000,'price': 5000000000,'name': '+500 MB'},
    {'kb': 1000000,'price': 30000000000,'name': '+1 GB'},
    {'kb': 5000000,'price': 200000000000,'name': '+5 GB'},
    {'kb': 10000000,'price': 1500000000000,'name': '+10 GB'},
    {'kb': 50000000,'price': 10000000000000,'name': '+50 GB'},
    {'kb': 100000000,'price': 80000000000000,'name': '+100 GB'},
    {'kb': 500000000,'price': 500000000000000,'name': '+500 GB'},
    {'kb': 1000000000,'price': 3000000000000000,'name': '+1 TB'},
]

# ===== КОМПЬЮТЕРЫ =====
COMPUTERS = [
    {'id': 'laptop',   'name': 'Ноутбук',      'emoji': '🖥', 'price': 50,   'income': 1},
    {'id': 'pc',       'name': 'ПК',           'emoji': '💻', 'price': 200,  'income': 5},
    {'id': 'server',   'name': 'Сервер',       'emoji': '🖥', 'price': 1000, 'income': 25},
    {'id': 'datacent', 'name': 'Дата-центр',   'emoji': '🗄', 'price': 5000, 'income': 150},
    {'id': 'farm',     'name': 'Ферма',        'emoji': '🏭', 'price': 25000,'income': 800},
    {'id': 'quantum',  'name': 'Квантовый ПК', 'emoji': '🚀', 'price': 100000,'income': 5000},
    {'id': 'neural',   'name': 'Нейросеть',    'emoji': '🌌', 'price': 500000,'income': 30000},
    {'id': 'god',      'name': 'ИИ-Бог',       'emoji': '🧠', 'price': 2000000,'income': 200000},
]

# ===== ЗАГРУЗКА / СОХРАНЕНИЕ =====
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

# ===== ИГРОК =====
def get_player(uid, fname='Anonymous', uname=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': fname or 'Anonymous',
            'username': uname or '',
            'memory': START_MEMORY,
            'tokens': START_TOKENS,
            'computers': {},
            'last_hack': 0,
            'last_income': int(time.time()),
            'total_earned': 0
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Anonymous')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {
            'memory': START_MEMORY, 'tokens': START_TOKENS,
            'computers': {}, 'last_hack': 0,
            'last_income': int(time.time()), 'total_earned': 0
        }
        for f, v in defaults.items():
            if f not in stats[k]: stats[k][f] = v
    save_stats(stats)
    return stats[k]

def update_player(uid, data):
    stats = load_stats()
    stats[str(uid)] = data
    save_stats(stats)

# ===== ДОХОД =====
def income_per_sec(p):
    total = 0
    computers = p.get('computers', {})
    for c in COMPUTERS:
        count = computers.get(c['id'], 0)
        total += count * c['income']
    return total

def apply_income(p):
    now = int(time.time())
    last = p.get('last_income', now)
    elapsed = min(now - last, OFFLINE_MAX)
    if elapsed <= 0: return p
    inc = income_per_sec(p) * elapsed
    if inc > 0:
        p['tokens'] = p.get('tokens', 0) + inc
        p['total_earned'] = p.get('total_earned', 0) + inc
    p['last_income'] = now
    return p

# ===== ФОРМАТ ЧИСЕЛ =====
def fmt_num(n):
    n = int(n)
    if n >= 1_000_000_000_000:
        return f"{n//1_000_000_000_000}трлн"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B".rstrip('0').rstrip('.') + 'B' if n < 10_000_000_000 else f"{n//1_000_000_000}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".rstrip('0').rstrip('.') + 'M' if n < 10_000_000 else f"{n//1_000_000}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K".rstrip('0').rstrip('.') + 'K' if n < 10_000 else f"{n//1_000}K"
    return str(n)

def fmt_memory(kb):
    if kb >= 1_000_000_000:
        return f"{kb/1_000_000_000:.1f} TB"
    if kb >= 1_000_000:
        return f"{kb/1_000_000:.1f} GB"
    if kb >= 1_000:
        return f"{kb/1_000:.1f} MB"
    return f"{kb} KB"

# ===== БОТ =====
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

# ===== ФОНОВЫЙ ДОХОД =====
def income_loop():
    while True:
        try:
            stats = load_stats()
            for k in list(stats.keys()):
                p = stats[k]
                now = int(time.time())
                last = p.get('last_income', now)
                elapsed = min(now - last, OFFLINE_MAX)
                inc = income_per_sec(p) * elapsed
                if inc > 0:
                    p['tokens'] = p.get('tokens', 0) + inc
                    p['total_earned'] = p.get('total_earned', 0) + inc
                p['last_income'] = now
                stats[k] = p
            save_stats(stats)
        except Exception as e:
            print('income error:', e)
        time.sleep(5)

threading.Thread(target=income_loop, daemon=True).start()

# ===== МЕНЮ =====
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🖥 Мой ИИ', callback_data='ai_main'))
    kb.add(
        types.InlineKeyboardButton('🛒 Память', callback_data='ai_mem_0'),
        types.InlineKeyboardButton('💻 Компьютеры', callback_data='ai_comp_0')
    )
    kb.add(types.InlineKeyboardButton('📊 Статистика', callback_data='ai_stats'))
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

    text = (
        f"🎭 <b>ХАКЕР-ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{m.from_user.first_name}</b>!\n\n"
        f"🖥 <b>МОЙ ИИ</b>\n"
        f"🧠 Память: <b>{mem}</b>\n"
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
        f"🖥 /start — открыть игру\n\n"
        f"📖 <b>Как играть:</b>\n"
        f"1️⃣ Улучшай память ИИ (KB, MB, GB)\n"
        f"2️⃣ Покупай компьютеры за память\n"
        f"3️⃣ Компьютеры приносят токены\n"
        f"4️⃣ Токены — на новую память\n\n"
        f"💰 Доход капает в секунду.\n"
        f"🌙 Офлайн — до 8 часов."
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

# ===== МОЙ ИИ =====
def ai_main_text(p):
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    inc = income_per_sec(p)
    total_earned = fmt_num(p.get('total_earned', 0))
    comps = p.get('computers', {})
    comp_count = sum(comps.values())
    return (
        f"🖥 <b>МОЙ ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>\n"
        f"💻 Компьютеров: <b>{comp_count}</b>\n"
        f"📈 Всего заработано: <b>{total_earned}</b>"
    )

def ai_main_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🔓 Хакнуть', callback_data='ai_hack'))
    kb.add(
        types.InlineKeyboardButton('🛒 Память', callback_data='ai_mem_0'),
        types.InlineKeyboardButton('💻 Компьютеры', callback_data='ai_comp_0')
    )
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='ai_main'))
    kb.add(types.InlineKeyboardButton('◀️ Меню', callback_data='menu_main'))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == 'ai_main')
def cb_ai_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    try:
        bot.edit_message_text(
            ai_main_text(p),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=ai_main_kb()
        )
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
    text = (
        f"🎭 <b>ХАКЕР-ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>"
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=main_menu())
    except: pass
    bot.answer_callback_query(call.id)

# ===== ХАК =====
@bot.callback_query_handler(func=lambda c: c.data == 'ai_hack')
def cb_hack(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    now = int(time.time())
    last = p.get('last_hack', 0)
    diff = now - last
    if diff < HACK_COOLDOWN:
        left = HACK_COOLDOWN - diff
        bot.answer_callback_query(call.id, f"⏱ Подожди {left} сек")
        return
    base = random.randint(HACK_MIN, HACK_MAX)
    mem = p.get('memory', START_MEMORY)
    mult = 1 + (mem / 1000)
    earned = int(base * mult)
    p['tokens'] = p.get('tokens', 0) + earned
    p['total_earned'] = p.get('total_earned', 0) + earned
    p['last_hack'] = now
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"🪙 +{fmt_num(earned)}")

# ===== ПАМЯТЬ =====
PAGE_SIZE = 5

def mem_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = MEMORY_PACKS[start:end]
    total_pages = (len(MEMORY_PACKS) + PAGE_SIZE - 1) // PAGE_SIZE
    mem = fmt_memory(p.get('memory', START_MEMORY))
    tokens = fmt_num(p.get('tokens', 0))
    text = (
        f"🛒 <b>УЛУЧШЕНИЯ ПАМЯТИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{mem}</b>\n"
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"📄 Стр. {page+1}/{total_pages}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(items):
        idx = start + i
        kb.add(types.InlineKeyboardButton(
            f"{item['name']} — {fmt_num(item['price'])} 🪙",
            callback_data=f'ai_mem_buy_{idx}'
        ))
    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton('◀️', callback_data=f'ai_mem_{page-1}'))
    nav_row.append(types.InlineKeyboardButton(f'{page+1}/{total_pages}', callback_data='ai_none'))
    if page < total_pages - 1:
        nav_row.append(types.InlineKeyboardButton('▶️', callback_data=f'ai_mem_{page+1}'))
    kb.row(*nav_row)
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='ai_main'))
    return text, kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_mem_') and not c.data.startswith('ai_mem_buy_'))
def cb_mem(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    try:
        page = int(call.data.replace('ai_mem_', ''))
    except:
        page = 0
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
        bot.answer_callback_query(call.id, "Ошибка")
        return
    item = MEMORY_PACKS[idx]
    price = item['price']
    tokens = p.get('tokens', 0)
    if tokens < price:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_num(price)} 🪙")
        return
    p['tokens'] = tokens - price
    p['memory'] = p.get('memory', START_MEMORY) + item['kb']
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {item['name']}!")
    page = idx // PAGE_SIZE
    text, kb = mem_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass

# ===== КОМПЬЮТЕРЫ =====
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
        f"<i>Покупаешь за память, приносят токены</i>"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, c in enumerate(items):
        idx = start + i
        owned = comps.get(c['id'], 0)
        label = f"{c['emoji']} {c['name']} — {fmt_memory(c['price'])}"
        if owned > 0:
            label += f" (x{owned})"
        kb.add(types.InlineKeyboardButton(label, callback_data=f'ai_comp_buy_{idx}'))
    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton('◀️', callback_data=f'ai_comp_{page-1}'))
    nav_row.append(types.InlineKeyboardButton(f'{page+1}/{total_pages}', callback_data='ai_none'))
    if page < total_pages - 1:
        nav_row.append(types.InlineKeyboardButton('▶️', callback_data=f'ai_comp_{page+1}'))
    kb.row(*nav_row)
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='ai_main'))
    return text, kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('ai_comp_') and not c.data.startswith('ai_comp_buy_'))
def cb_comp(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    update_player(uid, p)
    try:
        page = int(call.data.replace('ai_comp_', ''))
    except:
        page = 0
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
        bot.answer_callback_query(call.id, "Ошибка")
        return
    item = COMPUTERS[idx]
    price = item['price']
    mem = p.get('memory', START_MEMORY)
    if mem < price:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_memory(price)}")
        return
    p['memory'] = mem - price
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

# ===== СТАТИСТИКА =====
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
        f"🪙 Токены: <b>{tokens}</b>\n"
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>\n"
        f"📈 Всего заработано: <b>{total}</b>\n\n"
        f"<b>Компьютеры:</b>\n{comps_text}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='ai_main'))
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
        ])
    except: pass

set_commands()
print('Bot started')
bot.infinity_polling()
