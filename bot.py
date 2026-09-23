import telebot
import json
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ---------------- Настройки ----------------
STATS_FILE = 'stats.json'
SEASON_FILE = 'season.json'

ADMIN_IDS = [8907438590]              # сюда свой Telegram ID
TOKEN = '8747895563:AAHj7kyzKGJjyOEIySTy60n6tYZe1UP7kiI'          # токен от @BotFather
WEBAPP_URL = 'https://твой-адрес.com' # HTTPS-адрес, где лежит index.html

START_MEMORY = 5.0
START_TOKENS = 100
START_SPEED = 0.5
OFFLINE_MAX = 8 * 3600
SEASON_PASS_PRICE = 500_000
SEASON_DEFAULT_DAYS = 7

COMPUTERS = [
    {'id': 'laptop',  'name': 'Ноутбук',      'price': 50,     'income': 1},
    {'id': 'pc',      'name': 'ПК',           'price': 200,    'income': 5},
    {'id': 'server',  'name': 'Сервер',       'price': 1000,   'income': 25},
    {'id': 'dc',      'name': 'Дата-центр',   'price': 5000,   'income': 150},
    {'id': 'farm',    'name': 'Ферма',        'price': 25000,  'income': 800},
    {'id': 'quantum', 'name': 'Квантовый ПК', 'price': 100000, 'income': 5000},
    {'id': 'neural',  'name': 'Нейросеть',    'price': 500000, 'income': 30000},
    {'id': 'god',     'name': 'ИИ-Бог',       'price': 2000000,'income': 200000},
]

SPEED_PACKS = [
    {'speed': 0.5,  'price': 100},
    {'speed': 1,    'price': 250},
    {'speed': 2,    'price': 600},
    {'speed': 5,    'price': 1500},
    {'speed': 10,   'price': 5000},
    {'speed': 25,   'price': 15000},
    {'speed': 50,   'price': 50000},
    {'speed': 100,  'price': 200000},
    {'speed': 500,  'price': 1000000},
    {'speed': 1000, 'price': 5000000},
]

SEASON_LEVELS = [
    {'free': {'tokens': 200,   'speed': 0},   'prem': {'tokens': 500,    'speed': 0}},
    {'free': {'tokens': 0,     'speed': 2},   'prem': {'tokens': 0,      'speed': 5}},
    {'free': {'tokens': 500,   'speed': 0},   'prem': {'tokens': 1500,   'speed': 0}},
    {'free': {'tokens': 0,     'speed': 5},   'prem': {'tokens': 0,      'speed': 10}},
    {'free': {'tokens': 1500,  'speed': 0},   'prem': {'tokens': 4000,   'speed': 0}},
    {'free': {'tokens': 0,     'speed': 10},  'prem': {'tokens': 0,      'speed': 25}},
    {'free': {'tokens': 5000,  'speed': 0},   'prem': {'tokens': 12000,  'speed': 0}},
    {'free': {'tokens': 0,     'speed': 25},  'prem': {'tokens': 0,      'speed': 60}},
    {'free': {'tokens': 15000, 'speed': 0},   'prem': {'tokens': 40000,  'speed': 0}},
    {'free': {'tokens': 0,     'speed': 50},  'prem': {'tokens': 0,      'speed': 120}},
    {'free': {'tokens': 50000, 'speed': 0},   'prem': {'tokens': 120000, 'speed': 0}},
    {'free': {'tokens': 0,     'speed': 100}, 'prem': {'tokens': 0,      'speed': 250}},
    {'free': {'tokens': 150000,'speed': 0},   'prem': {'tokens': 400000, 'speed': 0}},
    {'free': {'tokens': 0,     'speed': 250}, 'prem': {'tokens': 0,      'speed': 600}},
    {'free': {'tokens': 0,     'speed': 0},   'prem': {'tokens': 1000000,'speed': 0}},
]

SEASON_THRESHOLDS = [
    1000, 5000, 15000, 50000, 150000,
    500000, 1500000, 5000000, 15000000, 50000000,
    150000000, 500000000, 1500000000, 5000000000, 15000000000
]

ADMIN_STATE = {}

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
def load_season(): return load_json(SEASON_FILE, {})
def save_season(d): save_json(SEASON_FILE, d)

# ---------------- Season helpers ----------------
def season_active():
    s = load_season()
    return bool(s and s.get('active') and s.get('end_ts', 0) > int(time.time()))

def season_left():
    s = load_season()
    if not s or not s.get('active'): return 0
    return max(0, s.get('end_ts', 0) - int(time.time()))

def compute_level(sm):
    lvl = 0
    for i, thr in enumerate(SEASON_THRESHOLDS):
        if sm >= thr: lvl = i + 1
        else: break
    return lvl

# ---------------- Players ----------------
def income_per_sec(p):
    total = 0
    comps = p.get('computers', {})
    for c in COMPUTERS:
        total += comps.get(c['id'], 0) * c['income']
    return total

def get_player(uid, name='Player', username=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': name or 'Player',
            'username': username or '',
            'memory': START_MEMORY,
            'tokens': START_TOKENS,
            'speed': START_SPEED,
            'computers': {},
            'last_update': int(time.time()),
            'total_earned': 0,
            'season_memory': 0.0,
            'season_level': 0,
            'season_claimed': [],
            'season_premium': False,
        }
    else:
        if name: stats[k]['first_name'] = name
        if username: stats[k]['username'] = username
        defaults = {
            'memory': START_MEMORY, 'tokens': START_TOKENS,
            'speed': START_SPEED, 'computers': {},
            'last_update': int(time.time()), 'total_earned': 0,
            'season_memory': 0.0, 'season_level': 0,
            'season_claimed': [], 'season_premium': False,
        }
        for f, v in defaults.items():
            if f not in stats[k]: stats[k][f] = v
    save_stats(stats)
    return stats[k]

def update_player(uid, p):
    stats = load_stats()
    stats[str(uid)] = p
    save_stats(stats)

def apply_income(p):
    now = int(time.time())
    last = p.get('last_update', now)
    elapsed = min(now - last, OFFLINE_MAX)
    if elapsed <= 0: return p
    gained_mem = p.get('speed', START_SPEED) * elapsed
    p['memory'] = p.get('memory', START_MEMORY) + gained_mem
    if season_active():
        p['season_memory'] = p.get('season_memory', 0) + gained_mem
        new_lvl = compute_level(p['season_memory'])
        if new_lvl > p.get('season_level', 0):
            p['season_level'] = new_lvl
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
    if n >= 1e12: return f"{int(n//1e12)}T"
    if n >= 1e9:
        v = n / 1e9
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'B') if v < 100 else f"{int(v)}B"
    if n >= 1e6:
        v = n / 1e6
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'M') if v < 100 else f"{int(v)}M"
    if n >= 1e3:
        v = n / 1e3
        return (f"{v:.1f}".rstrip('0').rstrip('.') + 'K') if v < 100 else f"{int(v)}K"
    return str(int(n))

def fmt_memory(kb):
    kb = float(kb)
    if kb >= 1e9: return f"{kb/1e9:.2f} TB"
    if kb >= 1e6: return f"{kb/1e6:.2f} GB"
    if kb >= 1e3: return f"{kb/1e3:.2f} MB"
    return f"{kb:.1f} KB"

def fmt_time(sec):
    sec = int(sec)
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
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
            active = season_active()
            for k in list(stats.keys()):
                p = stats[k]
                last = p.get('last_update', now)
                elapsed = min(now - last, OFFLINE_MAX)
                if elapsed > 0:
                    gained = p.get('speed', START_SPEED) * elapsed
                    p['memory'] = p.get('memory', START_MEMORY) + gained
                    if active:
                        p['season_memory'] = p.get('season_memory', 0) + gained
                        new_lvl = compute_level(p['season_memory'])
                        if new_lvl > p.get('season_level', 0):
                            p['season_level'] = new_lvl
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

threading.Thread(target=update_loop, daemon=True).start()

# ---------------- Menus ----------------
def main_menu(is_admin_user=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn('Открыть игру', 'open_webapp', 'primary'))
    kb.add(
        btn('Мой ИИ', 'ai_main', 'primary'),
        btn('Статистика', 'ai_stats', 'success')
    )
    kb.add(
        btn('Топ', 'ai_top', 'success'),
        btn('Сезон', 'season_main', 'primary')
    )
    kb.add(btn('Перевести токены', 'ai_pay', 'success'))
    if is_admin_user:
        kb.add(btn('Админ-панель', 'admin_menu', 'danger'))
    return kb

def ai_main_kb(is_admin_user=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('Мой ИИ', 'ai_main', 'primary'),
        btn('Статистика', 'ai_stats', 'success')
    )
    kb.add(
        btn('Топ', 'ai_top', 'success'),
        btn('Сезон', 'season_main', 'primary')
    )
    kb.add(btn('Перевести токены', 'ai_pay', 'success'))
    kb.add(btn('Обновить', 'ai_main', 'primary'))
    kb.add(btn('Меню', 'menu_main', 'danger'))
    return kb

def webapp_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='Открыть игру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    return kb

# ---------------- Commands ----------------
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    p = get_player(uid, m.from_user.first_name, m.from_user.username or '')
    p = apply_income(p)
    update_player(uid, p)

    text = (
        f"ХАКЕР-ИИ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Привет, {m.from_user.first_name}!\n\n"
        f"Память: {fmt_memory(p.get('memory', START_MEMORY))}\n"
        f"Скорость: {p.get('speed', START_SPEED)} KB/сек\n"
        f"Токены: {fmt_num(p.get('tokens', 0))}\n"
        f"Доход: {fmt_num(income_per_sec(p))}/сек\n\n"
        f"Играй кнопкой ниже или прямо здесь."
    )
    bot.send_message(m.chat.id, text,
                     reply_markup=webapp_kb())
    bot.send_message(m.chat.id, 'Меню:', reply_markup=main_menu(is_admin(uid)))

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        "ПОМОЩЬ\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Память капает сама.\n"
        "Трать память на компьютеры.\n"
        "Компьютеры дают токены.\n"
        "Токены — на скорость.\n\n"
        "/start — начать\n"
        "/top — топ\n"
        "/season — сезон\n"
        "/pay <id|@username> <кол-во> — перевод"
    )
    bot.send_message(m.chat.id, text, reply_markup=main_menu(is_admin(m.from_user.id)))

@bot.message_handler(commands=['top'])
def cmd_top(m):
    stats = load_stats()
    arr = []
    for uid, p in stats.items():
        arr.append({'name': p.get('first_name', 'Player'), 'memory': p.get('memory', 0)})
    arr.sort(key=lambda x: x['memory'], reverse=True)
    if not arr:
        bot.send_message(m.chat.id, 'Топ пуст.')
        return
    text = "ТОП ПО ПАМЯТИ\n━━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(arr[:15]):
        text += f"{i+1}. {u['name']} — {fmt_memory(u['memory'])}\n"
    bot.send_message(m.chat.id, text, reply_markup=main_menu(is_admin(m.from_user.id)))

@bot.message_handler(commands=['season'])
def cmd_season(m):
    uid = m.from_user.id
    p = get_player(uid, m.from_user.first_name, m.from_user.username or '')
    p = apply_income(p); update_player(uid, p)
    bot.send_message(m.chat.id, season_main_text(p),
                     parse_mode='HTML', reply_markup=season_main_kb(p))

@bot.message_handler(commands=['pay'])
def cmd_pay(m):
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /pay <id|@username> <кол-во>")
        return
    target_raw, amount_raw = parts[1], parts[2]
    try:
        amount = float(amount_raw)
        if amount <= 0: raise ValueError
    except ValueError:
        bot.reply_to(m, "Кол-во должно быть числом.")
        return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid:
            bot.reply_to(m, "Игрок не найден.")
            return
    else:
        if not target_raw.isdigit():
            bot.reply_to(m, "Укажи uid или @username.")
            return
        target_uid = target_raw

    if target_uid == str(m.from_user.id):
        bot.reply_to(m, "Нельзя себе.")
        return

    sender = get_player(m.from_user.id, m.from_user.first_name, m.from_user.username or '')
    sender = apply_income(sender)
    if sender.get('tokens', 0) < amount:
        bot.reply_to(m, f"Мало токенов. У тебя: {fmt_num(sender['tokens'])}")
        return

    receiver = get_player(target_uid); receiver = apply_income(receiver)
    sender['tokens'] -= amount
    receiver['tokens'] = receiver.get('tokens', 0) + amount
    update_player(m.from_user.id, sender)
    update_player(target_uid, receiver)
    bot.reply_to(m, f"Переведено {fmt_num(amount)} токенов игроку {target_uid}")
    try:
        bot.send_message(int(target_uid), f"Тебе перевели {fmt_num(amount)} токенов!")
    except: pass

# ---------------- Callbacks: главное меню ----------------
@bot.callback_query_handler(func=lambda c: c.data == 'open_webapp')
def cb_open_webapp(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, 'Игра:', reply_markup=webapp_kb())

@bot.callback_query_handler(func=lambda c: c.data == 'menu_main')
def cb_menu_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p); update_player(uid, p)
    text = (
        f"ХАКЕР-ИИ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Память: {fmt_memory(p.get('memory', START_MEMORY))}\n"
        f"Скорость: {p.get('speed', START_SPEED)} KB/сек\n"
        f"Токены: {fmt_num(p.get('tokens', 0))}\n"
        f"Доход: {fmt_num(income_per_sec(p))}/сек"
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=main_menu(is_admin(call.from_user.id)))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_main')
def cb_ai_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p); update_player(uid, p)
    text = (
        f"МОЙ ИИ\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Память: {fmt_memory(p.get('memory', START_MEMORY))}\n"
        f"Скорость: {p.get('speed', START_SPEED)} KB/сек\n"
        f"Токены: {fmt_num(p.get('tokens', 0))}\n"
        f"Доход: {fmt_num(income_per_sec(p))}/сек\n"
        f"Всего заработано: {fmt_num(p.get('total_earned', 0))}"
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=ai_main_kb(is_admin(call.from_user.id)))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_stats')
def cb_stats(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p); update_player(uid, p)
    comps = p.get('computers', {})
    lines = []
    for c in COMPUTERS:
        cnt = comps.get(c['id'], 0)
        if cnt > 0:
            lines.append(f"{c['name']}: x{cnt}")
    comp_text = "\n".join(lines) if lines else "Пока ничего"
    text = (
        f"СТАТИСТИКА\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Память: {fmt_memory(p.get('memory', START_MEMORY))}\n"
        f"Скорость: {p.get('speed', START_SPEED)} KB/сек\n"
        f"Токены: {fmt_num(p.get('tokens', 0))}\n"
        f"Доход: {fmt_num(income_per_sec(p))}/сек\n\n"
        f"Компьютеры:\n{comp_text}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('Назад', 'ai_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_top')
def cb_top(call):
    stats = load_stats()
    arr = []
    for uid, p in stats.items():
        arr.append({'name': p.get('first_name', 'Player'), 'memory': p.get('memory', 0)})
    arr.sort(key=lambda x: x['memory'], reverse=True)
    text = "ТОП ПО ПАМЯТИ\n━━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(arr[:15]):
        text += f"{i+1}. {u['name']} — {fmt_memory(u['memory'])}\n"
    if not arr: text = "Топ пуст."
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('Назад', 'ai_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'ai_pay')
def cb_pay(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "Перевод токенов:\n/pay <id или @username> <кол-во>\n\nПример: /pay @vasya 500")

# ---------------- Season UI ----------------
def season_main_text(p):
    s = load_season()
    if not s or not s.get('active'):
        return "СЕЗОН\n━━━━━━━━━━━━━━━\n\nСейчас нет активного сезона."
    left = season_left()
    sm = p.get('season_memory', 0)
    lvl = p.get('season_level', 0)
    prem = p.get('season_premium', False)
    next_thr = SEASON_THRESHOLDS[lvl] if lvl < 15 else None
    prog = f"{fmt_memory(sm)} / {fmt_memory(next_thr)}" if next_thr else f"{fmt_memory(sm)} (макс)"
    return (
        f"СЕЗОН: {s.get('name')}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"Осталось: {fmt_time(left)}\n"
        f"Сезонная память: {fmt_memory(sm)}\n"
        f"Уровень: {lvl}/15\n"
        f"Прогресс: {prog}\n"
        f"Premium: {'да' if prem else 'нет'}"
    )

def season_main_kb(p):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('Уровни пропуска', 'season_levels', 'primary'))
    if not p.get('season_premium'):
        kb.add(btn(f'Купить Premium ({fmt_num(SEASON_PASS_PRICE)} токенов)', 'season_buy', 'success'))
    kb.add(btn('Забрать награды', 'season_claim', 'success'))
    kb.add(btn('Назад', 'ai_main', 'danger'))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == 'season_main')
def cb_season_main(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p); update_player(uid, p)
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=season_main_kb(p))
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'season_levels')
def cb_season_levels(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    prem = p.get('season_premium', False)
    lvl = p.get('season_level', 0)
    text = "УРОВНИ ПРОПУСКА\n━━━━━━━━━━━━━━━\n\n"
    for i in range(15):
        n = i + 1
        src = SEASON_LEVELS[i]['prem'] if prem else SEASON_LEVELS[i]['free']
        parts = []
        if src.get('tokens'): parts.append(f"+{fmt_num(src['tokens'])} токенов")
        if src.get('speed'): parts.append(f"+{src['speed']} KB/сек")
        mark = "✓" if lvl >= n else "-"
        text += f"{mark} Ур.{n} ({fmt_memory(SEASON_THRESHOLDS[i])}): {', '.join(parts) or '—'}\n"
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('Назад', 'season_main', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'season_buy')
def cb_season_buy(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p)
    if not season_active():
        bot.answer_callback_query(call.id, "Сезон неактивен"); return
    if p.get('season_premium'):
        bot.answer_callback_query(call.id, "Уже куплено"); return
    if p.get('tokens', 0) < SEASON_PASS_PRICE:
        bot.answer_callback_query(call.id, f"Нужно {fmt_num(SEASON_PASS_PRICE)} токенов"); return
    p['tokens'] -= SEASON_PASS_PRICE
    p['season_premium'] = True
    update_player(uid, p)
    bot.answer_callback_query(call.id, "Premium активирован")
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=season_main_kb(p))
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == 'season_claim')
def cb_season_claim(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username or '')
    p = apply_income(p)
    lvl = p.get('season_level', 0)
    claimed = set(p.get('season_claimed', []))
    prem = p.get('season_premium', False)
    got_t, got_s = 0, 0
    for n in range(1, lvl + 1):
        if n in claimed: continue
        src = SEASON_LEVELS[n-1]['prem'] if prem else SEASON_LEVELS[n-1]['free']
        got_t += src.get('tokens', 0)
        got_s += src.get('speed', 0)
        claimed.add(n)
    if got_t == 0 and got_s == 0:
        bot.answer_callback_query(call.id, "Нечего забирать"); return
    p['tokens'] += got_t
    p['speed'] += got_s
    p['season_claimed'] = list(claimed)
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"+{fmt_num(got_t)} токенов, +{got_s} KB/сек")
    try:
        bot.edit_message_text(season_main_text(p), chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=season_main_kb(p))
    except: pass

# ---------------- Admin ----------------
@bot.callback_query_handler(func=lambda c: c.data == 'admin_menu')
def cb_admin_menu(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа"); return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('Пост всем', 'admin_post_all', 'primary'))
    kb.add(btn('Пост о сезоне', 'admin_post_season', 'success'))
    kb.add(btn('Назад', 'menu_main', 'danger'))
    try:
        bot.edit_message_text(
            "АДМИН-ПАНЕЛЬ\n━━━━━━━━━━━━━━━\n\n"
            "/season_start <название> <дней>\n"
            "/season_end\n"
            "/give <uid|@username> <кол-во>\n"
            "/givemem <uid|@username> <KB>\n"
            "/users",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb)
    except: pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'admin_post_all')
def cb_admin_post_all(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа"); return
    ADMIN_STATE[call.from_user.id] = {'action': 'broadcast'}
    bot.answer_callback_query(call.id, "Жду пост")
    bot.send_message(call.message.chat.id,
        "Отправь пост (текст, фото, видео, документ).\n/cancel — отмена.")

@bot.callback_query_handler(func=lambda c: c.data == 'admin_post_season')
def cb_admin_post_season(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа"); return
    if not season_active():
        bot.answer_callback_query(call.id, "Нет активного сезона"); return
    ADMIN_STATE[call.from_user.id] = {'action': 'season_post'}
    bot.answer_callback_query(call.id, "Жду пост о сезоне")
    bot.send_message(call.message.chat.id,
        "Отправь пост о сезоне.\n/cancel — отмена.")

@bot.message_handler(commands=['cancel'])
def cmd_cancel(m):
    if ADMIN_STATE.pop(m.from_user.id, None):
        bot.reply_to(m, "Отменено")

@bot.message_handler(commands=['users'])
def cmd_users(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id, f"Игроков: {len(load_stats())}")

@bot.message_handler(commands=['give'])
def cmd_give(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /give <uid|@username> <кол-во>"); return
    target_raw, amount_raw = parts[1], parts[2]
    try: amount = float(amount_raw)
    except: bot.reply_to(m, "Кол-во числом"); return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid: bot.reply_to(m, "Не найден"); return
    else:
        target_uid = target_raw

    rec = get_player(target_uid); rec = apply_income(rec)
    rec['tokens'] = rec.get('tokens', 0) + amount
    update_player(target_uid, rec)
    bot.reply_to(m, f"Выдано {fmt_num(amount)} токенов → {target_uid}")
    try:
        bot.send_message(int(target_uid), f"Админ выдал тебе {fmt_num(amount)} токенов!")
    except: pass

@bot.message_handler(commands=['givemem'])
def cmd_givemem(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /givemem <uid|@username> <KB>"); return
    target_raw, amount_raw = parts[1], parts[2]
    try: amount = float(amount_raw)
    except: bot.reply_to(m, "Кол-во числом"); return

    if target_raw.startswith('@'):
        target_uid = find_uid_by_username(target_raw)
        if not target_uid: bot.reply_to(m, "Не найден"); return
    else:
        target_uid = target_raw

    rec = get_player(target_uid); rec = apply_income(rec)
    rec['memory'] = rec.get('memory', START_MEMORY) + amount
    if season_active():
        rec['season_memory'] = rec.get('season_memory', 0) + amount
        new_lvl = compute_level(rec['season_memory'])
        if new_lvl > rec.get('season_level', 0):
            rec['season_level'] = new_lvl
    update_player(target_uid, rec)
    bot.reply_to(m, f"Выдано {fmt_memory(amount)} → {target_uid}")

@bot.message_handler(commands=['season_start'])
def cmd_season_start(m):
    if not is_admin(m.from_user.id): return
    parts = m.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(m, "Использование: /season_start <название> <дней>"); return
    name = parts[1]
    try:
        days = int(parts[2])
        if days <= 0: raise ValueError
    except: bot.reply_to(m, "Дни — число"); return

    now = int(time.time())
    save_season({'name': name, 'active': True, 'start_ts': now,
                 'end_ts': now + days * 86400})
    stats = load_stats()
    for k, p in stats.items():
        p['season_memory'] = 0.0
        p['season_level'] = 0
        p['season_claimed'] = []
        p['season_premium'] = False
    save_stats(stats)
    bot.send_message(m.chat.id, f"Сезон {name} запущен на {days} дн.")

@bot.message_handler(commands=['season_end'])
def cmd_season_end(m):
    if not is_admin(m.from_user.id): return
    s = load_season()
    if not s: bot.reply_to(m, "Сезона нет"); return
    s['active'] = False
    save_season(s)
    bot.send_message(m.chat.id, f"Сезон {s.get('name')} завершён")

# ---------------- Broadcast ----------------
@bot.message_handler(
    content_types=['text', 'photo', 'video', 'document', 'animation'],
    func=lambda m: ADMIN_STATE.get(m.from_user.id, {}).get('action') in ('broadcast', 'season_post')
)
def do_broadcast(m):
    ADMIN_STATE.pop(m.from_user.id, None)
    uids = get_all_uids()
    bot.reply_to(m, f"Рассылаю {len(uids)} игрокам...")
    ok, fail = 0, 0
    for uid in uids:
        try:
            if m.content_type == 'text':
                bot.send_message(int(uid), m.text)
            elif m.content_type == 'photo':
                bot.send_photo(int(uid), m.photo[-1].file_id, caption=m.caption)
            elif m.content_type == 'video':
                bot.send_video(int(uid), m.video.file_id, caption=m.caption)
            elif m.content_type == 'animation':
                bot.send_animation(int(uid), m.animation.file_id, caption=m.caption)
            elif m.content_type == 'document':
                bot.send_document(int(uid), m.document.file_id, caption=m.caption)
            ok += 1
            time.sleep(0.05)
        except: fail += 1
    bot.send_message(m.chat.id, f"Готово.\nДоставлено: {ok}\nОшибок: {fail}")

# ---------------- Start ----------------
if __name__ == '__main__':
    print('Bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
