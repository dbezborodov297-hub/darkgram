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
SEASON_FILE = 'season.json'
SEASON_ARCHIVE_FILE = 'season_archive.json'

ADMIN_IDS = [8907438590]
TOKEN = '8747895563:AAHj7kyzKGJjyOEIySTy60n6tYZe1UP7kiI'

START_MEMORY = 5.0
START_TOKENS = 100
START_SPEED = 0.5
OFFLINE_MAX = 8 * 3600
TOP_REFRESH = 300

SEASON_PASS_PRICE = 500_000
SEASON_DEFAULT_DAYS = 7

# ---------------- Магазины ----------------
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

# 15 уровней: (free_tokens, free_speed, prem_tokens, prem_speed)
SEASON_LEVELS = [
    {'free': {'tokens': 200,    'speed': 0},    'prem': {'tokens': 500,    'speed': 0}},
    {'free': {'tokens': 0,      'speed': 2},    'prem': {'tokens': 0,      'speed': 5}},
    {'free': {'tokens': 500,    'speed': 0},    'prem': {'tokens': 1500,   'speed': 0}},
    {'free': {'tokens': 0,      'speed': 5},    'prem': {'tokens': 0,      'speed': 10}},
    {'free': {'tokens': 1500,   'speed': 0},    'prem': {'tokens': 4000,   'speed': 0}},
    {'free': {'tokens': 0,      'speed': 10},   'prem': {'tokens': 0,      'speed': 25}},
    {'free': {'tokens': 5000,   'speed': 0},    'prem': {'tokens': 12000,  'speed': 0}},
    {'free': {'tokens': 0,      'speed': 25},   'prem': {'tokens': 0,      'speed': 60}},
    {'free': {'tokens': 15000,  'speed': 0},    'prem': {'tokens': 40000,  'speed': 0}},
    {'free': {'tokens': 0,      'speed': 50},   'prem': {'tokens': 0,      'speed': 120}},
    {'free': {'tokens': 50000,  'speed': 0},    'prem': {'tokens': 120000, 'speed': 0}},
    {'free': {'tokens': 0,      'speed': 100},  'prem': {'tokens': 0,      'speed': 250}},
    {'free': {'tokens': 150000, 'speed': 0},    'prem': {'tokens': 400000, 'speed': 0}},
    {'free': {'tokens': 0,      'speed': 250},  'prem': {'tokens': 0,      'speed': 600}},
    {'free': {'tokens': 0,      'speed': 0,  'title': 'Легенда сезона'},
     'prem': {'tokens': 1000000, 'speed': 0, 'title': 'Легенда сезона+'}},
]

# Порог season_memory для каждого уровня (15 порогов)
SEASON_THRESHOLDS = [
    1_000, 5_000, 15_000, 50_000, 150_000,
    500_000, 1_500_000, 5_000_000, 15_000_000, 50_000_000,
    150_000_000, 500_000_000, 1_500_000_000, 5_000_000_000, 15_000_000_000
]

ADMIN_STATE = {}  # uid -> {'action': 'broadcast'|'season_post'}

# ---------------- JSON helpers ----------------
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
def load_season(): return load_json(SEASON_FILE, {})
def save_season(d): save_json(SEASON_FILE, d)
def load_season_archive(): return load_json(SEASON_ARCHIVE_FILE, [])
def save_season_archive(d): save_json(SEASON_ARCHIVE_FILE, d)

# ---------------- Season helpers ----------------
def season_is_active(season=None):
    if season is None: season = load_season()
    if not season or not season.get('active'): return False
    end = season.get('end_ts', 0)
    return end > int(time.time())

def season_time_left(season=None):
    if season is None: season = load_season()
    if not season or not season.get('active'): return 0
    left = season.get('end_ts', 0) - int(time.time())
    return max(0, left)

def season_threshold_for_level(level):
    """Возвращает порог season_memory для уровня level (1..15)."""
    if level < 1: return 0
    if level > len(SEASON_THRESHOLDS): return SEASON_THRESHOLDS[-1]
    return SEASON_THRESHOLDS[level-1]

def compute_season_level(season_memory):
    lvl = 0
    for i, thr in enumerate(SEASON_THRESHOLDS):
        if season_memory >= thr:
            lvl = i + 1
        else:
            break
    return lvl

def start_new_season(name, days, admin_uid):
    old = load_season()
    if old and old.get('active'):
        arch = load_season_archive()
        arch.append({
            'name': old.get('name'),
            'start_ts': old.get('start_ts'),
            'end_ts': old.get('end_ts'),
            'finished_ts': int(time.time()),
            'participants': old.get('participants', {}),
        })
        save_season_archive(arch)

    now = int(time.time())
    season = {
        'name': name,
        'active': True,
        'start_ts': now,
        'end_ts': now + days * 86400,
        'started_by': admin_uid,
        'participants': {},   # uid -> {'season_memory': 0, 'level': 0, 'claimed': [], 'premium': False}
        'post_sent': False,
    }
    save_season(season)

    # обнуляем сезонный прогресс у всех игроков
    stats = load_stats()
    for k, p in stats.items():
        p['season_memory'] = 0.0
        p['season_level'] = 0
        p['season_claimed'] = []
        p['season_premium'] = False
    save_stats(stats)
    return season

def end_season():
    season = load_season()
    if not season: return None
    season['active'] = False
    season['end_ts'] = int(time.time())
    save_season(season)

    arch = load_season_archive()
    arch.append({
        'name': season.get('name'),
        'start_ts': season.get('start_ts'),
        'end_ts': season.get('end_ts'),
        'finished_ts': int(time.time()),
        'participants': season.get('participants', {}),
    })
    save_season_archive(arch)
    return season

def ensure_season_field(p):
    """Гарантирует наличие сезонных полей у игрока."""
    if 'season_memory' not in p: p['season_memory'] = 0.0
    if 'season_level' not in p: p['season_level'] = 0
    if 'season_claimed' not in p: p['season_claimed'] = []
    if 'season_premium' not in p: p['season_premium'] = False
    return p

def season_memory_add(p, amount):
    """Начисляет сезонную память и обновляет уровень."""
    p = ensure_season_field(p)
    p['season_memory'] = p.get('season_memory', 0) + amount
    new_level = compute_season_level(p['season_memory'])
    if new_level > p.get('season_level', 0):
        p['season_level'] = new_level
    return p

# ---------------- Players ----------------
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
            'total_earned': 0,
            'season_memory': 0.0,
            'season_level': 0,
            'season_claimed': [],
            'season_premium': False,
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Anonymous')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {
            'memory': START_MEMORY, 'tokens': START_TOKENS,
            'speed': START_SPEED, 'computers': {},
            'last_hack': 0, 'last_update': int(time.time()),
            'total_earned': 0, 'season_memory': 0.0,
            'season_level': 0, 'season_claimed': [], 'season_premium': False,
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
    gained_mem = speed * elapsed
    p['memory'] = p.get('memory', START_MEMORY) + gained_mem
    if season_is_active():
        p = season_memory_add(p, gained_mem)
    inc = income_per_sec(p) * elapsed
    if inc > 0:
        p['tokens'] = p.get('tokens', 0) + inc
        p['total_earned'] = p.get('total_earned', 0) + inc
    p['last_update'] = now
    return p

def is_admin(uid):
    return uid in ADMIN_IDS

def find_uid_by_username(uname):
    uname = uname.lstrip('@').lower()
    stats = load_stats()
    for uid, p in stats.items():
        if (p.get('username') or '').lower() == uname:
            return uid
    return None

def get_all_uids():
    return list(load_stats().keys())

# ---------------- Formatting ----------------
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

def fmt_time(seconds):
    seconds = int(seconds)
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    if d > 0: return f"{d}д {h}ч"
    if h > 0: return f"{h}ч {m}м"
    return f"{m}м"

def btn(text, data, style=None):
    if style:
        try:
            return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
        except TypeError:
            return types.InlineKeyboardButton(text=text, callback_data=data)
    return types.InlineKeyboardButton(text=text, callback_data=data)

# ---------------- Bot init ----------------
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

# ---------------- Background loops ----------------
def update_loop():
    while True:
        try:
            stats = load_stats()
            now = int(time.time())
            active = season_is_active()
            for k in list(stats.keys()):
                p = stats[k]
                last = p.get('last_update', now)
                elapsed = min(now - last, OFFLINE_MAX)
                if elapsed > 0:
                    speed = p.get('speed', START_SPEED)
                    gained = speed * elapsed
                    p['memory'] = p.get('memory', START_MEMORY) + gained
                    if active:
                        p = season_memory_add(p, gained)
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
                    'tokens': p.get('tokens', 0),
                    'season_memory': p.get('season_memory', 0),
                })
            arr.sort(key=lambda x: x['memory'], reverse=True)
            save_json(TOP_CACHE_FILE, arr[:50])
            print('Top refreshed')
        except Exception as e:
            print('top loop err:', e)
        time.sleep(TOP_REFRESH)

threading.Thread(target=update_loop, daemon=True).start()
threading.Thread(target=top_loop, daemon=True).start()

# ---------------- Menus ----------------
def main_menu(is_admin_user=False):
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
    kb.add(btn('🎫 Сезон', 'season_main', 'primary'))
    kb.add(
        btn('🏆 Топ', 'ai_top', 'success'),
        btn('💸 Перевести', 'ai_pay', 'success')
    )
    if is_admin_user:
        kb.add(btn('📢 Пост', 'admin_post_menu', 'danger'))
    return kb

def ai_main_kb(is_admin_user=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('🛒 Память', 'ai_mem_0', 'success'),
        btn('💻 Компьютеры', 'ai_comp_0', 'primary')
    )
    kb.add(
        btn('⚡ Ускорители', 'ai_speed_0', 'success'),
        btn('📊 Статистика', 'ai_stats', 'primary')
    )
    kb.add(btn('🎫 Сезон', 'season_main', 'primary'))
    kb.add(btn('🏆 Топ', 'ai_top', 'success'))
    kb.add(btn('💸 Перевести токены', 'ai_pay', 'success'))
    kb.add(btn('🔄 Обновить', 'ai_main', 'primary'))
    kb.add(btn('◀️ Меню', 'menu_main', 'danger'))
    return kb

# ---------------- Commands ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    p = get_player(uid, m.from_user.first_name, m.from_user.username)
    p = apply_income(p); update_player(uid, p)
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
        f"💰 Доход: <b>{fmt_num(inc)}/сек</b>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML',
                     reply_markup=main_menu(is_admin(uid)))

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>Как играть:</b>\n"
        f"1️⃣ Память капает сама\n"
        f"2️⃣ Трать память на компьютеры\n"
        f"3️⃣ Компьютеры дают токены/сек\n"
        f"4️⃣ Токены — на ускорители\n"
        f"5️⃣ Сезон — отдельный прогресс и награды\n\n"
        f"💸 <b>Перевод:</b> /pay &lt;uid|@username&gt; &lt;кол-во&gt;\n\n"
        f"🎫 /season — сезон\n"
        f"🏆 /top — топ\n"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML',
                     reply_markup=main_menu(is_admin(m.from_user.id)))

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
    bot.send_message(m.chat.id, text, parse_mode='HTML',
                     reply_markup=main_menu(is_admin(m.from_user.id)))

# ---------------- /pay ----------------
@bot.message_handler(commands=['pay'])
def cmd_pay(m):
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /pay &lt;uid|@username&gt; &lt;кол-во&gt;", parse_mode='HTML')
        return
    target_raw, amount_raw = parts[1], parts[2]
    try:
        amount = float(amount_raw)
        if amount <= 0: raise ValueError
    except ValueError:
        bot.reply_to(m, "❌ Кол-во должно быть положительным числом.")
        return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid:
            bot.reply_to(m, "❌ Игрок с таким @username не найден.")
            return
    else:
        if not target_raw.isdigit():
            bot.reply_to(m, "❌ Укажи uid или @username.")
            return
        target_uid = target_raw

    if target_uid == str(m.from_user.id):
        bot.reply_to(m, "❌ Нельзя перевести самому себе.")
        return

    sender = get_player(m.from_user.id, m.from_user.first_name, m.from_user.username)
    sender = apply_income(sender)
    if sender.get('tokens', 0) < amount:
        bot.reply_to(m, f"❌ Недостаточно токенов. У тебя: {fmt_num(sender['tokens'])}")
        return

    receiver = get_player(target_uid)
    receiver = apply_income(receiver)

    sender['tokens'] -= amount
    receiver['tokens'] = receiver.get('tokens', 0) + amount

    update_player(m.from_user.id, sender)
    update_player(target_uid, receiver)

    bot.reply_to(m, f"✅ Переведено <b>{fmt_num(amount)}</b> 🪙 игроку <code>{target_uid}</code>",
                 parse_mode='HTML')
    try:
        bot.send_message(int(target_uid),
                         f"🎁 Тебе перевели <b>{fmt_num(amount)}</b> 🪙!",
                         parse_mode='HTML')
    except: pass

# ---------------- Main AI screens ----------------
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

@bot.callback_query_handler(func=lambda c: c.data == 'ai_main')
def cb_ai_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    try:
        bot.edit_message_text(ai_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=ai_main_kb(is_admin(call.from_user.id)))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_menu_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    text = (
        f"🎭 <b>ХАКЕР-ИИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{fmt_memory(p.get('memory', START_MEMORY))}</b>\n"
        f"⚡ Скорость: <b>{p.get('speed', START_SPEED)} KB/сек</b>\n"
        f"🪙 Токены: <b>{fmt_num(p.get('tokens', 0))}</b>\n"
        f"💰 Доход: <b>{fmt_num(income_per_sec(p))}/сек</b>"
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=main_menu(is_admin(call.from_user.id)))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_pay')
def cb_pay(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "💸 Чтобы перевести токены:\n"
        "<code>/pay &lt;uid или @username&gt; &lt;кол-во&gt;</code>\n\n"
        "Пример: <code>/pay @vasya 500</code>",
        parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == 'ai_stats')
def cb_stats(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    comps = p.get('computers', {})
    lines = []
    for c in COMPUTERS:
        cnt = comps.get(c['id'], 0)
        if cnt > 0:
            lines.append(f"{c['emoji']} {c['name']}: <b>x{cnt}</b>")
    comp_text = "\n".join(lines) if lines else "<i>Пока ничего</i>"
    text = (
        f"📊 <b>СТАТИСТИКА</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{fmt_memory(p.get('memory', START_MEMORY))}</b>\n"
        f"⚡ Скорость: <b>{p.get('speed', START_SPEED)} KB/сек</b>\n"
        f"🪙 Токены: <b>{fmt_num(p.get('tokens', 0))}</b>\n"
        f"💰 Доход: <b>{fmt_num(income_per_sec(p))}/сек</b>\n"
        f"📈 Всего: <b>{fmt_num(p.get('total_earned', 0))}</b>\n\n"
        f"💻 <b>Компьютеры:</b>\n{comp_text}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
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

# ---------------- Memory packs ----------------
PAGE_SIZE = 5

def mem_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = MEMORY_PACKS[start:end]
    total_pages = (len(MEMORY_PACKS) + PAGE_SIZE - 1) // PAGE_SIZE
    text = (
        f"🛒 <b>ПАМЯТЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Сейчас: <b>{fmt_memory(p.get('memory', START_MEMORY))}</b>\n"
        f"🪙 Токены: <b>{fmt_num(p.get('tokens', 0))}</b>\n"
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
    if season_is_active():
        p = season_memory_add(p, item['kb'])
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{item['kb']} KB!")
    page = idx // PAGE_SIZE
    text, kb = mem_page(page, p)
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass

# ---------------- Computers ----------------
def comp_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = COMPUTERS[start:end]
    total_pages = (len(COMPUTERS) + PAGE_SIZE - 1) // PAGE_SIZE
    text = (
        f"💻 <b>КОМПЬЮТЕРЫ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🧠 Память: <b>{fmt_memory(p.get('memory', START_MEMORY))}</b>\n"
        f"📄 Стр. {page+1}/{total_pages}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    comps = p.get('computers', {})
    for i, c in enumerate(items):
        idx = start + i
        owned = comps.get(c['id'], 0)
        label = f"{c['emoji']} {c['name']} — {fmt_memory(c['price'])}"
        if owned > 0: label += f" (x{owned})"
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

# ---------------- Speed packs ----------------
def speed_page(page, p):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    items = SPEED_PACKS[start:end]
    total_pages = (len(SPEED_PACKS) + PAGE_SIZE - 1) // PAGE_SIZE
    text = (
        f"⚡ <b>УСКОРИТЕЛИ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚡ Сейчас: <b>{p.get('speed', START_SPEED)} KB/сек</b>\n"
        f"🪙 Токены: <b>{fmt_num(p.get('tokens', 0))}</b>\n"
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

# ---------------- SEASON ----------------
def season_main_text(p):
    season = load_season()
    if not season or not season.get('active'):
        return ("🎫 <b>СЕЗОН</b>\n━━━━━━━━━━━━━━━\n\n"
                "Сейчас нет активного сезона.\n"
                "Жди анонса!")
    left = season_time_left(season)
    p = ensure_season_field(p)
    sm = p.get('season_memory', 0)
    lvl = p.get('season_level', 0)
    prem = p.get('season_premium', False)
    next_thr = season_threshold_for_level(lvl + 1) if lvl < 15 else None
    if next_thr:
        progress = f"{fmt_memory(sm)} / {fmt_memory(next_thr)}"
    else:
        progress = f"{fmt_memory(sm)} (макс)"
    return (
        f"🎫 <b>СЕЗОН: {season.get('name')}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⏳ Осталось: <b>{fmt_time(left)}</b>\n"
        f"🎯 Сезонная память: <b>{fmt_memory(sm)}</b>\n"
        f"📊 Уровень: <b>{lvl}/15</b>\n"
        f"📈 Прогресс: <b>{progress}</b>\n"
        f"💎 Premium: <b>{'✅' if prem else '❌'}</b>"
    )

def season_main_kb(p):
    p = ensure_season_field(p)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn('📋 Уровни пропуска', 'season_levels', 'primary'))
    if not p.get('season_premium'):
        kb.add(btn(f'💎 Купить Premium ({fmt_num(SEASON_PASS_PRICE)} 🪙)', 'season_buy', 'success'))
    kb.add(btn('🎁 Забрать награды', 'season_claim', 'success'))
    kb.add(btn('◀️ Назад', 'ai_main', 'danger'))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == 'season_main')
def cb_season_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p); update_player(uid, p)
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=season_main_kb(p))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'season_levels')
def cb_season_levels(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = ensure_season_field(p)
    prem = p.get('season_premium', False)
    lvl = p.get('season_level', 0)
    text = "📋 <b>УРОВНИ ПРОПУСКА</b>\n━━━━━━━━━━━━━━━\n\n"
    for i, lv in enumerate(SEASON_LEVELS):
        n = i + 1
        thr = season_threshold_for_level(n)
        src = lv['prem'] if prem else lv['free']
        mark = "✅" if lvl >= n else "🔒"
        parts = []
        if src.get('tokens'): parts.append(f"+{fmt_num(src['tokens'])} 🪙")
        if src.get('speed'): parts.append(f"+{src['speed']} KB/сек")
        if src.get('title'): parts.append(f"🏆 {src['title']}")
        reward = ", ".join(parts) if parts else "—"
        text += f"{mark} Ур.{n} ({fmt_memory(thr)}): {reward}\n"
        if n >= 15: break
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('◀️ Назад', 'season_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'season_buy')
def cb_season_buy(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    p = ensure_season_field(p)
    if not season_is_active():
        bot.answer_callback_query(call.id, "❌ Сезон неактивен"); return
    if p.get('season_premium'):
        bot.answer_callback_query(call.id, "✅ Уже куплено"); return
    if p.get('tokens', 0) < SEASON_PASS_PRICE:
        bot.answer_callback_query(call.id, f"❌ Нужно {fmt_num(SEASON_PASS_PRICE)} 🪙"); return
    p['tokens'] -= SEASON_PASS_PRICE
    p['season_premium'] = True
    update_player(uid, p)
    bot.answer_callback_query(call.id, "💎 Premium активирован!")
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=season_main_kb(p))
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == 'season_claim')
def cb_season_claim(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    p = apply_income(p)
    p = ensure_season_field(p)
    lvl = p.get('season_level', 0)
    claimed = set(p.get('season_claimed', []))
    prem = p.get('season_premium', False)
    got_t, got_s, got_titles = 0, 0, []
    for n in range(1, lvl + 1):
        if n in claimed: continue
        src = SEASON_LEVELS[n-1]['prem'] if prem else SEASON_LEVELS[n-1]['free']
        got_t += src.get('tokens', 0)
        got_s += src.get('speed', 0)
        if src.get('title'): got_titles.append(src['title'])
        claimed.add(n)
    if got_t == 0 and got_s == 0 and not got_titles:
        bot.answer_callback_query(call.id, "Нечего забирать")
        return
    p['tokens'] = p.get('tokens', 0) + got_t
    p['speed'] = p.get('speed', START_SPEED) + got_s
    p['season_claimed'] = list(claimed)
    update_player(uid, p)
    msg = "🎁 Получено:"
    if got_t: msg += f" +{fmt_num(got_t)} 🪙"
    if got_s: msg += f" +{got_s} KB/сек"
    if got_titles: msg += f" 🏆 {', '.join(got_titles)}"
    bot.answer_callback_query(call.id, msg[:200])
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=season_main_kb(p))
    except: pass

@bot.message_handler(commands=['season'])
def cmd_season(m):
    uid = m.from_user.id
    p = get_player(uid, m.from_user.first_name, m.from_user.username)
    p = apply_income(p); update_player(uid, p)
    bot.send_message(m.chat.id, season_main_text(p), parse_mode='HTML',
                     reply_markup=season_main_kb(p))

# ---------------- ADMIN: сезон ----------------
@bot.message_handler(commands=['season_admin'])
def cmd_season_admin(m):
    if not is_admin(m.from_user.id): return
    text = (
        "🛠 <b>УПРАВЛЕНИЕ СЕЗОНОМ</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        "/season_start &lt;название&gt; &lt;дней&gt; — запуск\n"
        "/season_post — публикация о сезоне\n"
        "/season_status — состояние\n"
        "/season_end — завершить"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['season_start'])
def cmd_season_start(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /season_start &lt;название&gt; &lt;дней&gt;", parse_mode='HTML')
        return
    name = parts[1]
    try:
        days = int(parts[2])
        if days <= 0: raise ValueError
    except ValueError:
        bot.reply_to(m, "❌ Дни — число.")
        return
    s = start_new_season(name, days, m.from_user.id)
    bot.send_message(m.chat.id,
        f"✅ Сезон <b>{s['name']}</b> запущен на {days} дн.\n"
        f"Окончание: <code>{time.strftime('%Y-%m-%d %H:%M', time.localtime(s['end_ts']))}</code>",
        parse_mode='HTML')

@bot.message_handler(commands=['season_status'])
def cmd_season_status(m):
    if not is_admin(m.from_user.id): return
    s = load_season()
    if not s or not s.get('active'):
        bot.send_message(m.chat.id, "❌ Активного сезона нет.")
        return
    left = season_time_left(s)
    text = (
        f"🎫 <b>{s['name']}</b>\n"
        f"⏳ Осталось: {fmt_time(left)}\n"
        f"👥 Участников (с прогрессом): {len([1 for u,p in load_stats().items() if p.get('season_memory',0) > 0])}"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['season_end'])
def cmd_season_end(m):
    if not is_admin(m.from_user.id): return
    s = end_season()
    if not s:
        bot.send_message(m.chat.id, "❌ Сезона нет.")
        return
    bot.send_message(m.chat.id, f"🛑 Сезон <b>{s['name']}</b> завершён.", parse_mode='HTML')

@bot.message_handler(commands=['season_post'])
def cmd_season_post(m):
    if not is_admin(m.from_user.id): return
    s = load_season()
    if not s or not s.get('active'):
        bot.reply_to(m, "❌ Нет активного сезона.")
        return
    ADMIN_STATE[m.from_user.id] = {'action': 'season_post'}
    bot.send_message(m.chat.id,
        "📢 Отправь пост о сезоне (текст / фото / видео / документ).\n"
        "Он уйдёт всем игрокам.\n\n❌ /cancel — отмена.",
        parse_mode='HTML')

# ---------------- ADMIN: пост (кнопка) ----------------
@bot.callback_query_handler(func=lambda c: c.data == 'admin_post_menu')
def cb_admin_post_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔"); return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('📢 Рассылка всем', 'admin_post_all', 'primary'))
    kb.add(btn('📌 Пост о сезоне', 'admin_post_season', 'success'))
    kb.add(btn('◀️ Назад', 'menu_main', 'danger'))
    try:
        bot.edit_message_text(
            "📢 <b>ПУБЛИКАЦИЯ</b>\n━━━━━━━━━━━━━━━\n\n"
            "Выбери тип публикации:",
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            parse_mode='HTML', reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'admin_post_all')
def cb_admin_post_all(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔"); return
    ADMIN_STATE[call.from_user.id] = {'action': 'broadcast'}
    bot.answer_callback_query(call.id, "Жду пост...")
    bot.send_message(call.message.chat.id,
        "📢 Отправь пост (текст / фото / видео / документ с подписью).\n\n"
        "❌ /cancel — отмена.", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == 'admin_post_season')
def cb_admin_post_season(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔"); return
    s = load_season()
    if not s or not s.get('active'):
        bot.answer_callback_query(call.id, "❌ Нет активного сезона")
        return
    ADMIN_STATE[call.from_user.id] = {'action': 'season_post'}
    bot.answer_callback_query(call.id, "Жду пост о сезоне...")
    bot.send_message(call.message.chat.id,
        "📢 Отправь пост о сезоне (текст / фото / видео / документ).\n\n"
        "❌ /cancel — отмена.", parse_mode='HTML')

@bot.message_handler(commands=['cancel'])
def cmd_cancel(m):
    if ADMIN_STATE.pop(m.from_user.id, None):
        bot.reply_to(m, "✅ Отменено.")

# ---------------- ADMIN: /give /givemem /users ----------------
@bot.message_handler(commands=['users'])
def cmd_users(m):
    if not is_admin(m.from_user.id): return
    stats = load_stats()
    bot.send_message(m.chat.id, f"👥 Игроков: <b>{len(stats)}</b>", parse_mode='HTML')

@bot.message_handler(commands=['give'])
def cmd_give(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /give &lt;uid|@username&gt; &lt;кол-во&gt;", parse_mode='HTML')
        return
    target_raw, amount_raw = parts[1], parts[2]
    try: amount = float(amount_raw)
    except ValueError:
        bot.reply_to(m, "❌ Кол-во числом."); return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid:
            bot.reply_to(m, "❌ Не найден."); return
    else:
        target_uid = target_raw

    receiver = get_player(target_uid)
    receiver = apply_income(receiver)
    receiver['tokens'] = receiver.get('tokens', 0) + amount
    update_player(target_uid, receiver)
    bot.reply_to(m, f"✅ Выдано <b>{fmt_num(amount)}</b> 🪙 → <code>{target_uid}</code>", parse_mode='HTML')
    try:
        bot.send_message(int(target_uid),
                         f"🎁 Админ выдал тебе <b>{fmt_num(amount)}</b> 🪙!",
                         parse_mode='HTML')
    except: pass

@bot.message_handler(commands=['givemem'])
def cmd_givemem(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /givemem &lt;uid|@username&gt; &lt;KB&gt;", parse_mode='HTML')
        return
    target_raw, amount_raw = parts[1], parts[2]
    try: amount = float(amount_raw)
    except ValueError:
        bot.reply_to(m, "❌ Кол-во числом."); return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid:
            bot.reply_to(m, "❌ Не найден."); return
    else:
        target_uid = target_raw

    receiver = get_player(target_uid)
    receiver = apply_income(receiver)
    receiver['memory'] = receiver.get('memory', START_MEMORY) + amount
    if season_is_active():
        receiver = season_memory_add(receiver, amount)
    update_player(target_uid, receiver)
    bot.reply_to(m, f"✅ Выдано <b>{fmt_memory(amount)}</b> → <code>{target_uid}</code>", parse_mode='HTML')

# ---------------- Универсальный обработчик рассылки (ПОСЛЕДНИЙ) ----------------
@bot.message_handler(
    content_types=['text', 'photo', 'video', 'document', 'animation'],
    func=lambda m: ADMIN_STATE.get(m.from_user.id, {}).get('action') in ('broadcast', 'season_post')
)
def do_broadcast(m):
    action = ADMIN_STATE.pop(m.from_user.id, {}).get('action', 'broadcast')
    uids = get_all_uids()
    bot.reply_to(m, f"⏳ Рассылаю {len(uids)} игрокам...")

    ok, fail = 0, 0
    for uid in uids:
        try:
            if m.content_type == 'text':
                bot.send_message(int(uid), m.text, parse_mode='HTML')
            elif m.content_type == 'photo':
                bot.send_photo(int(uid), m.photo[-1].file_id, caption=m.caption, parse_mode='HTML')
            elif m.content_type == 'video':
                bot.send_video(int(uid), m.video.file_id, caption=m.caption, parse_mode='HTML')
            elif m.content_type == 'animation':
                bot.send_animation(int(uid), m.animation.file_id, caption=m.caption, parse_mode='HTML')
            elif m.content_type == 'document':
                bot.send_document(int(uid), m.document.file_id, caption=m.caption, parse_mode='HTML')
            ok += 1
            time.sleep(0.05)
        except Exception as e:
            fail += 1
    bot.send_message(m.chat.id, f"✅ Готово.\nДоставлено: {ok}\nОшибок: {fail}")

# ---------------- Start polling ----------------
if __name__ == '__main__':
    print("Bot started")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
