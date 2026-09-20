import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
DUELS_FILE = 'duels.json'
BOSS_FILE = 'boss.json'

ADMIN_IDS = [8907438590]
TOKEN = '8872773404:AAEblXoLxAi1bGXVWtPNq3Tjmxb27JnlnOg'

DUEL_HP = 100
DUEL_SHOOT_MIN = 25
DUEL_SHOOT_MAX = 45
DUEL_AIM_BONUS = 0.9
DUEL_NOAIM_CHANCE = 0.6
DUEL_TIMEOUT = 300

BOSS_MIN_PLAYERS = 2
BOSS_MAX_PLAYERS = 15
BOSS_LOBBY_TIME = 300
BOSS_TIMER_UPDATE = 15
BOSS_ATK_MIN = 40
BOSS_ATK_MAX = 90
BOSS_BAT_MIN = 80
BOSS_BAT_MAX = 150
BOSS_BAT_CHANCE = 0.7
BOSS_AIM_BONUS = 1.3
BOSS_DMG_MIN = 50
BOSS_DMG_MAX = 150
PLAYER_MIN_HP = 250
PLAYER_MAX_HP = 5000

DAILY_REWARDS = [5, 7, 10, 15, 20, 30, 50]
DAILY_COOLDOWN = 24 * 3600
MINE_COOLDOWN = 15 * 60
MINE_MIN = 5
MINE_MAX = 10

BOSSES = {
    1: {'name': 'Голодный Волк',      'emoji': '🐺', 'hp': 1000, 'diamonds': 2},
    2: {'name': 'Пустынный Скорпион', 'emoji': '🦂', 'hp': 1500, 'diamonds': 3},
    3: {'name': 'Кровавый Лев',       'emoji': '🦁', 'hp': 2000, 'diamonds': 4},
    4: {'name': 'Демон Огня',         'emoji': '👺', 'hp': 2500, 'diamonds': 5},
    5: {'name': 'Тёмный Лорд',        'emoji': '👹', 'hp': 3000, 'diamonds': 6},
    6: {'name': 'Король Зомби',       'emoji': '🧟', 'hp': 3500, 'diamonds': 7},
    7: {'name': 'Древний Дракон',     'emoji': '🐉', 'hp': 5000, 'diamonds': 10},
}

DISTRACT = [
    "🎭 Отвлекающий маневр — прицел сбит!",
    "💨 Резко ушёл в сторону!",
    "🪞 Зеркальце — прицел сбит!",
    "🌫 Дымовая шашка!",
    "🎪 Сальто — враг растерялся!",
    "🦅 Взлетел на секунду!",
    "🎯 Песок в глаза!",
    "🌀 Кульбит — враг в пустоту!",
    "🎺 Громко крикнул!",
    "🌟 Вспышка — прицел сбит!",
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
def load_duels(): return load_json(DUELS_FILE, {})
def save_duels(d): save_json(DUELS_FILE, d)
def load_boss(): return load_json(BOSS_FILE, {})
def save_boss(d): save_json(BOSS_FILE, d)

def get_player(uid, fname='Аноним', uname=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': fname or 'Аноним', 'username': uname or '',
            'wins': 0, 'losses': 0, 'boss_wins': 0, 'boss_losses': 0,
            'diamonds': 0, 'max_hp': PLAYER_MIN_HP,
            'last_daily': 0, 'daily_streak': 0, 'last_mine': 0
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Аноним')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {'wins':0,'losses':0,'boss_wins':0,'boss_losses':0,
                    'diamonds':0,'max_hp':PLAYER_MIN_HP,
                    'last_daily':0,'daily_streak':0,'last_mine':0}
        for f, v in defaults.items():
            if f not in stats[k]: stats[k][f] = v
    save_stats(stats)
    return stats[k]

def update_player(uid, data):
    stats = load_stats()
    stats[str(uid)] = data
    save_stats(stats)

def add_duel_win(uid):
    p = get_player(uid); p['wins'] += 1; update_player(uid, p)

def add_duel_loss(uid):
    p = get_player(uid); p['losses'] += 1; update_player(uid, p)

def add_boss_win(uid, diamonds=0):
    p = get_player(uid); p['boss_wins'] += 1
    p['diamonds'] = p.get('diamonds', 0) + diamonds
    update_player(uid, p)

def add_boss_loss(uid):
    p = get_player(uid); p['boss_losses'] += 1; update_player(uid, p)

def get_duel(cid): return load_duels().get(str(cid))
def save_duel(cid, d):
    ds = load_duels(); ds[str(cid)] = d; save_duels(ds)
def del_duel(cid):
    ds = load_duels()
    if str(cid) in ds: del ds[str(cid)]; save_duels(ds)

def get_boss(cid): return load_boss().get(str(cid))
def save_boss_g(cid, g):
    bs = load_boss(); bs[str(cid)] = g; save_boss(bs)
def del_boss(cid):
    bs = load_boss()
    if str(cid) in bs: del bs[str(cid)]; save_boss(bs)

def fmt_t(s):
    s = max(0, int(s)); return f"{s//60}:{s%60:02d}"

def fmt_h(sec):
    sec = max(0, int(sec))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0: return f"{h}ч {m}мин"
    if m > 0: return f"{m}мин {s}сек"
    return f"{s}сек"

def dname(p):
    if not p: return 'Аноним'
    u = (p.get('username') or '').strip()
    if u: return '@' + u
    f = (p.get('first_name') or '').strip()
    return f if f and f != 'Аноним' else 'Аноним'

def sedit(cid, mid, text, kb=None):
    try:
        bot.edit_message_text(text, chat_id=cid, message_id=mid, parse_mode='HTML', reply_markup=kb)
        return True
    except: return False

def is_admin_id(uid):
    try: return int(uid) in ADMIN_IDS
    except: return False

bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running')

def run_http():
    HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 10000))), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

def btn(text, data, style=None):
    """Хелпер для создания кнопки с опциональным стилем."""
    if style:
        try:
            return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
        except TypeError:
            return types.InlineKeyboardButton(text=text, callback_data=data)
    return types.InlineKeyboardButton(text=text, callback_data=data)

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('👤 Профиль', 'm_prof', 'primary'),
        btn('🏆 Топ', 'm_top', 'primary')
    )
    kb.add(
        btn('⚔️ Дуэль', 'm_duel', 'primary'),
        btn('🐉 Боссы', 'm_boss', 'primary')
    )
    kb.add(
        btn('📅 Бонус', 'm_daily', 'success'),
        btn('⛏ Шахта', 'm_mine', 'success')
    )
    kb.add(btn('💎 Алмазы → HP', 'm_shop', 'success'))
    kb.add(btn('💬 Помощь', 'm_help'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    get_player(uid, m.from_user.first_name, m.from_user.username)
    text = (
        f"🎭 <b>DARKGRAM</b>\n━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{m.from_user.first_name}</b>!\n\n"
        f"⚔️ Дуэли 1 на 1 и 2 на 2\n"
        f"🐉 Боссы (2-15 игроков)\n"
        f"📅 Ежедневный бонус\n"
        f"⛏ Шахта алмазов\n"
        f"💎 Алмазы → HP\n"
        f"🏆 Топ по победам\n\n"
        f"👇 <i>Выбирай:</i>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"⚔️ <b>Дуэль 1x1:</b> <code>/duel</code> в ответ\n"
        f"⚔️ <b>Дуэль 2x2:</b> <code>/duel2x2</code> в группе\n"
        f"🐉 <b>Боссы:</b> <code>/boss1</code> ... <code>/boss7</code>\n"
        f"📅 <b>Daily:</b> <code>/daily</code>\n"
        f"⛏ <b>Шахта:</b> <code>/mine</code>\n"
        f"💎 <b>Магазин:</b> <code>/shop</code>\n\n"
        f"📅 <b>DAILY:</b> 5 → 7 → 10 → 15 → 20 → 30 → 50 💎\n\n"
        f"⛏ <b>ШАХТА:</b> раз в 15 минут → 5-10 💎"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def cmd_profile(m):
    send_profile(m.chat.id, m.from_user.id, m.from_user.first_name, m.from_user.username)

@bot.message_handler(commands=['top'])
def cmd_top(m):
    send_top(m.chat.id)

@bot.message_handler(commands=['shop'])
def cmd_shop(m):
    send_shop(m.chat.id, m.from_user.id, m.from_user.first_name, m.from_user.username)

@bot.message_handler(commands=['daily'])
def cmd_daily(m):
    send_daily(m.chat.id, m.from_user.id, m.from_user.first_name, m.from_user.username)

@bot.message_handler(commands=['mine'])
def cmd_mine(m):
    send_mine(m.chat.id, m.from_user.id, m.from_user.first_name, m.from_user.username)

def send_profile(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    total = p['wins'] + p['losses']
    wr = round(p['wins'] / total * 100) if total else 0
    bt = p.get('boss_wins', 0) + p.get('boss_losses', 0)
    bwr = round(p.get('boss_wins', 0) / bt * 100) if bt else 0
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"<b>{dname(p)}</b>\n\n"
        f"⚔️ <b>ДУЭЛИ</b>\n"
        f"🏆 Побед: <b>{p['wins']}</b>\n"
        f"💀 Поражений: <b>{p['losses']}</b>\n"
        f"📊 Винрейт: <b>{wr}%</b>\n\n"
        f"🐉 <b>БОССЫ</b>\n"
        f"🏆 Побед: <b>{p.get('boss_wins', 0)}</b>\n"
        f"💀 Поражений: <b>{p.get('boss_losses', 0)}</b>\n"
        f"📊 Винрейт: <b>{bwr}%</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Алмазы: <b>{p.get('diamonds', 0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>\n"
        f"🔥 Серия daily: <b>{p.get('daily_streak', 0)}</b>"
    )
    bot.send_message(cid, text, parse_mode='HTML')

def send_top(cid):
    stats = load_stats()
    if not stats:
        bot.send_message(cid, "🏆 Пока пусто."); return
    ss = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n━━━━━━━━━━━━━━━\n\n"
    n = 0
    for i, (uid, p) in enumerate(ss, 1):
        if p.get('wins', 0) == 0: continue
        n += 1
        med = '🥇' if n==1 else '🥈' if n==2 else '🥉' if n==3 else f'<b>{n}.</b>'
        text += f"{med} {dname(p)}\n     ⚔️ {p['wins']} побед · 💀 {p['losses']}\n\n"
    if n == 0: text += "Пока никто не побеждал."
    bot.send_message(cid, text, parse_mode='HTML')

def send_shop(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    text = (
        f"💎 <b>МАГАЗИН АЛМАЗОВ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"💰 Алмазов: <b>{p.get('diamonds', 0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>\n\n"
        f"📌 <b>Курсы:</b>\n"
        f"10 💎 → +20 HP\n"
        f"25 💎 → +45 HP\n"
        f"40 💎 → +75 HP"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        btn('10 💎 → +20 HP', 'buy_10', 'success'),
        btn('25 💎 → +45 HP', 'buy_25', 'success'),
        btn('40 💎 → +75 HP', 'buy_40', 'success'),
        btn('◀️ Назад', 'm_back', 'danger')
    )
    bot.send_message(cid, text, parse_mode='HTML', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_hp(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    costs = {'buy_10': (10, 20), 'buy_25': (25, 45), 'buy_40': (40, 75)}
    cost, hp = costs.get(call.data, (0, 0))
    if p.get('diamonds', 0) < cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {cost} 💎"); return
    if p.get('max_hp', PLAYER_MIN_HP) + hp > PLAYER_MAX_HP:
        bot.answer_callback_query(call.id, "❌ Максимум HP"); return
    p['diamonds'] -= cost
    p['max_hp'] = p.get('max_hp', PLAYER_MIN_HP) + hp
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{hp} HP")

def send_daily(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    now = int(time.time())
    last = p.get('last_daily', 0)
    diff = now - last
    if diff < DAILY_COOLDOWN:
        left = DAILY_COOLDOWN - diff
        bot.send_message(cid,
            f"📅 <b>DAILY БОНУС</b>\n━━━━━━━━━━━━━━━\n\n"
            f"⏳ Уже взял сегодня.\n"
            f"🔥 Серия: <b>{p.get('daily_streak', 0)}</b>\n\n"
            f"⏰ Следующий через: <b>{fmt_h(left)}</b>",
            parse_mode='HTML')
        return
    if last > 0 and diff < 48 * 3600:
        p['daily_streak'] = p.get('daily_streak', 0) + 1
    else:
        p['daily_streak'] = 1
    streak = p['daily_streak']
    idx = min(streak - 1, len(DAILY_REWARDS) - 1)
    reward = DAILY_REWARDS[idx]
    p['diamonds'] = p.get('diamonds', 0) + reward
    p['last_daily'] = now
    update_player(uid, p)
    next_reward = DAILY_REWARDS[min(streak, len(DAILY_REWARDS) - 1)]
    bot.send_message(cid,
        f"📅 <b>DAILY БОНУС!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"💰 +<b>{reward}</b> 💎\n"
        f"🔥 Серия: <b>{streak}</b> дней\n"
        f"💎 Всего: <b>{p['diamonds']}</b>\n\n"
        f"📌 Завтра: <b>{next_reward}</b> 💎",
        parse_mode='HTML')

def send_mine(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    now = int(time.time())
    last = p.get('last_mine', 0)
    diff = now - last
    if diff < MINE_COOLDOWN:
        left = MINE_COOLDOWN - diff
        bot.send_message(cid,
            f"⛏ <b>ШАХТА</b>\n━━━━━━━━━━━━━━━\n\n"
            f"⏳ Остывает.\n\n"
            f"⏰ Через: <b>{fmt_h(left)}</b>",
            parse_mode='HTML')
        return
    reward = random.randint(MINE_MIN, MINE_MAX)
    p['diamonds'] = p.get('diamonds', 0) + reward
    p['last_mine'] = now
    update_player(uid, p)
    bot.send_message(cid,
        f"⛏ <b>ДОБЫЧА!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"💎 +<b>{reward}</b> алмазов\n"
        f"💰 Всего: <b>{p['diamonds']}</b>\n\n"
        f"⏰ Через: <b>15 минут</b>",
        parse_mode='HTML')

# ===== ДУЭЛЬ 1x1 =====
@bot.message_handler(commands=['duel'])
def cmd_duel(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "⚔️ Только в группах."); return
    if not m.reply_to_message:
        bot.send_message(m.chat.id, "⚔️ Ответь на сообщение игрока и напиши /duel"); return
    t = m.reply_to_message.from_user
    if t.id == m.from_user.id: bot.send_message(m.chat.id, "❌ Себе нельзя."); return
    if t.is_bot: bot.send_message(m.chat.id, "❌ С ботом нельзя."); return
    ex = get_duel(m.chat.id)
    if ex and ex.get('status') in ('pending', 'active'):
        bot.send_message(m.chat.id, "⚔️ Уже идёт."); return
    now = int(time.time())
    duel = {
        'chat_id': m.chat.id, 'mode': '1v1',
        'p1_id': str(m.from_user.id), 'p1_name': m.from_user.first_name,
        'p2_id': str(t.id), 'p2_name': t.first_name,
        'p1_hp': DUEL_HP, 'p2_hp': DUEL_HP,
        'p1_aim': False, 'p2_aim': False,
        'turn': str(m.from_user.id), 'status': 'pending',
        'deadline': now + DUEL_TIMEOUT, 'msg_id': None, 'last_action_msg': ''
    }
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('✅ Принять', 'd_yes', 'success'),
        btn('❌ Отклонить', 'd_no', 'danger')
    )
    sent = bot.send_message(m.chat.id, duel_pending_text(duel), parse_mode='HTML', reply_markup=kb)
    duel['msg_id'] = sent.message_id
    save_duel(m.chat.id, duel)
    threading.Timer(DUEL_TIMEOUT, duel_timeout, args=[m.chat.id]).start()

def duel_pending_text(d):
    left = d['deadline'] - int(time.time())
    if d.get('mode') == '2v2':
        players = "\n".join([f"• {p['name']}" for p in d['players'].values()])
        return (
            f"⚔️ <b>ДУЭЛЬ 2x2 — СБОР</b>\n━━━━━━━━━━━━━━━\n\n"
            f"👥 Игроков: <b>{len(d['team'])}/4</b>\n"
            f"⏱ До старта: <b>{fmt_t(left)}</b>\n\n"
            f"<b>Команда:</b>\n{players}"
        )
    return (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{d['p1_name']}</b> вызывает <b>{d['p2_name']}</b>!\n\n"
        f"<i>{d['p2_name']}, принимаешь?</i>\n\n"
        f"⏱ Осталось: <b>{fmt_t(left)}</b>"
    )

def duel_timeout(cid):
    d = get_duel(cid)
    if not d or d.get('status') != 'pending': return
    sedit(cid, d.get('msg_id'), "⌛ Время вышло.")
    del_duel(cid)

def duel_kb_1v1():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        btn('🔫 Выстрел', 'd_shoot', 'danger'),
        btn('🎯 Прицел', 'd_aim', 'success'),
        btn('🎭 Отвлечь', 'd_dist', 'primary')
    )
    return kb

def duel_text(d):
    if d.get('mode') == '2v2': return duel_2v2_text(d)
    a1 = ' 🎯' if d['p1_aim'] else ''
    a2 = ' 🎯' if d['p2_aim'] else ''
    tn = d['p1_name'] if d['turn'] == d['p1_id'] else d['p2_name']
    t = (
        f"⚔️ <b>ДУЭЛЬ 1x1</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{d['p1_name']}</b>: ❤️ <b>{d['p1_hp']}</b> HP{a1}\n"
        f"🥷 <b>{d['p2_name']}</b>: ❤️ <b>{d['p2_hp']}</b> HP{a2}\n\n"
        f"🎯 Ход: <b>{tn}</b>"
    )
    if d.get('last_action_msg'): t += f"\n\n{d['last_action_msg']}"
    return t

def next_turn(d):
    d['turn'] = d['p2_id'] if d['turn'] == d['p1_id'] else d['p1_id']

@bot.callback_query_handler(func=lambda c: c.data.startswith('d_'))
def duel_cb(call):
    cid = call.message.chat.id
    d = get_duel(cid)
    if not d:
        bot.answer_callback_query(call.id, "Не найдена"); return
    uid = str(call.from_user.id)
    if d.get('mode') == '2v2': handle_2v2(call, cid, d, uid); return

    if call.data == 'd_yes':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌"); return
        d['status'] = 'active'; d['last_action_msg'] = ''
        save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1())
        bot.answer_callback_query(call.id, "⚔️"); return

    if call.data == 'd_no':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌"); return
        del_duel(cid); sedit(cid, d['msg_id'], "❌ Отклонено.")
        bot.answer_callback_query(call.id, "Отклонено"); return

    if d.get('status') != 'active': bot.answer_callback_query(call.id, "❌"); return
    if uid != d['turn']: bot.answer_callback_query(call.id, "🎯 Не твой ход"); return

    if call.data == 'd_aim':
        if uid == d['p1_id']: d['p1_aim'] = True
        else: d['p2_aim'] = True
        d['last_action_msg'] = "🎯 <i>Прицелился!</i>"
        next_turn(d); save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1())
        bot.answer_callback_query(call.id, "🎯"); return

    if call.data == 'd_dist':
        if uid == d['p1_id']:
            had = d['p2_aim']; d['p2_aim'] = False
        else:
            had = d['p1_aim']; d['p1_aim'] = False
        msg = random.choice(DISTRACT)
        msg += "\n💥 <b>Прицел сбит!</b>" if had else "\n🤷"
        d['last_action_msg'] = msg
        next_turn(d); save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1())
        bot.answer_callback_query(call.id, "🎭"); return

    if call.data == 'd_shoot':
        if uid == d['p1_id']:
            aim = d['p1_aim']; d['p1_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p2_hp'] = max(0, d['p2_hp'] - dmg)
                msg = f"💥 <b>-{dmg}</b> HP"
            else: msg = "🌫 Промах!"
        else:
            aim = d['p2_aim']; d['p2_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p1_hp'] = max(0, d['p1_hp'] - dmg)
                msg = f"💥 <b>-{dmg}</b> HP"
            else: msg = "🌫 Промах!"
        d['last_action_msg'] = msg
        if d['p1_hp'] <= 0 or d['p2_hp'] <= 0:
            wid = d['p1_id'] if d['p2_hp'] <= 0 else d['p2_id']
            lid = d['p2_id'] if wid == d['p1_id'] else d['p1_id']
            wn = d['p1_name'] if wid == d['p1_id'] else d['p2_name']
            add_duel_win(wid); add_duel_loss(lid); del_duel(cid)
            sedit(cid, call.message.message_id,
                f"🏆 <b>ДУЭЛЬ ОКОНЧЕНА</b>\n━━━━━━━━━━━━━━━\n\n{msg}\n\n🥇 Победил: <b>{wn}</b>")
            bot.answer_callback_query(call.id, "🏆"); return
        next_turn(d); save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1())
        bot.answer_callback_query(call.id)

# ===== ДУЭЛЬ 2x2 =====
@bot.message_handler(commands=['duel2x2', 'duel2'])
def cmd_duel2x2(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "⚔️ Только в группах."); return
    ex = get_duel(m.chat.id)
    if ex and ex.get('status') in ('pending', 'active'):
        bot.send_message(m.chat.id, "⚔️ Уже идёт."); return
    now = int(time.time())
    d = {
        'chat_id': m.chat.id, 'mode': '2v2',
        'host_id': str(m.from_user.id),
        'team': [], 'players': {},
        'team_a': [], 'team_b': [],
        'status': 'lobby', 'deadline': now + DUEL_TIMEOUT,
        'msg_id': None, 'turn_idx': 0, 'last_action_msg': ''
    }
    d['team'].append(str(m.from_user.id))
    d['players'][str(m.from_user.id)] = {'name': m.from_user.first_name, 'hp': DUEL_HP, 'aim': False, 'team': None}
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('🎭 Присоединиться', 'd2_join', 'success'),
        btn('🚪 Выйти', 'd2_leave', 'danger')
    )
    kb.add(btn('▶️ Начать (хост)', 'd2_start', 'primary'))
    sent = bot.send_message(m.chat.id, duel_pending_text(d), parse_mode='HTML', reply_markup=kb)
    d['msg_id'] = sent.message_id
    save_duel(m.chat.id, d)
    threading.Timer(DUEL_TIMEOUT, duel_timeout, args=[m.chat.id]).start()

def duel_2v2_text(d):
    if d.get('status') == 'lobby': return duel_pending_text(d)
    a_text = "\n".join([f"• <b>{d['players'][u]['name']}</b>: {'💀' if d['players'][u]['hp'] <= 0 else '❤️ '+str(d['players'][u]['hp'])}" for u in d['team_a']])
    b_text = "\n".join([f"• <b>{d['players'][u]['name']}</b>: {'💀' if d['players'][u]['hp'] <= 0 else '❤️ '+str(d['players'][u]['hp'])}" for u in d['team_b']])
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    tn = '—'
    if alive: tn = d['players'][alive[d['turn_idx'] % len(alive)]]['name']
    t = (
        f"⚔️ <b>ДУЭЛЬ 2x2</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🔵 <b>Команда А</b>\n{a_text}\n\n"
        f"🔴 <b>Команда Б</b>\n{b_text}\n\n"
        f"🎯 Ход: <b>{tn}</b>"
    )
    if d.get('last_action_msg'): t += f"\n\n{d['last_action_msg']}"
    return t

def duel_2v2_attack_kb(d, uid):
    enemy_team = d['team_b'] if uid in d['team_a'] else d['team_a']
    alive = [u for u in enemy_team if d['players'][u]['hp'] > 0]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for u in alive:
        kb.add(btn(f"🔫 {d['players'][u]['name']}", f'd2_atk_{u}', 'danger'))
    kb.add(btn('🎯 Прицел', 'd2_aim', 'success'))
    kb.add(btn('🎭 Отвлечь', 'd2_dist', 'primary'))
    return kb

def start_2v2(cid):
    d = get_duel(cid)
    if not d: return
    ids = d['team'][:]
    random.shuffle(ids)
    d['team_a'] = ids[:2]; d['team_b'] = ids[2:4]
    for u in d['team_a']: d['players'][u]['team'] = 'A'
    for u in d['team_b']: d['players'][u]['team'] = 'B'
    d['status'] = 'active'; d['turn_idx'] = 0
    d['last_action_msg'] = '⚔️ Бой начался!'
    save_duel(cid, d)
    sedit(cid, d['msg_id'], duel_2v2_text(d), None)
    send_2v2_turn(cid)

def send_2v2_turn(cid):
    d = get_duel(cid)
    if not d or d.get('status') != 'active': return
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    if not alive: finish_2v2(cid); return
    uid = alive[d['turn_idx'] % len(alive)]
    kb = duel_2v2_attack_kb(d, uid)
    try:
        bot.send_message(cid, duel_2v2_text(d), parse_mode='HTML', reply_markup=kb)
    except: pass

def handle_2v2(call, cid, d, uid):
    if call.data == 'd2_join':
        if d['status'] != 'lobby': bot.answer_callback_query(call.id, "❌"); return
        if uid in d['team']: bot.answer_callback_query(call.id, "✅"); return
        if len(d['team']) >= 4: bot.answer_callback_query(call.id, "❌ 4 игрока"); return
        d['team'].append(uid)
        d['players'][uid] = {'name': call.from_user.first_name, 'hp': DUEL_HP, 'aim': False, 'team': None}
        save_duel(cid, d)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            btn('🎭 Присоединиться', 'd2_join', 'success'),
            btn('🚪 Выйти', 'd2_leave', 'danger')
        )
        kb.add(btn('▶️ Начать (хост)', 'd2_start', 'primary'))
        sedit(cid, d['msg_id'], duel_pending_text(d), kb)
        bot.answer_callback_query(call.id, "⚔️"); return

    if call.data == 'd2_leave':
        if d['status'] != 'lobby': bot.answer_callback_query(call.id, "❌"); return
        if uid not in d['team']: bot.answer_callback_query(call.id, "❌"); return
        d['team'].remove(uid); d['players'].pop(uid, None)
        if not d['team']:
            del_duel(cid); sedit(cid, d['msg_id'], "❌ Закрыто.")
            bot.answer_callback_query(call.id, "🚪"); return
        if uid == d['host_id']: d['host_id'] = d['team'][0]
        save_duel(cid, d)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            btn('🎭 Присоединиться', 'd2_join', 'success'),
            btn('🚪 Выйти', 'd2_leave', 'danger')
        )
        kb.add(btn('▶️ Начать (хост)', 'd2_start', 'primary'))
        sedit(cid, d['msg_id'], duel_pending_text(d), kb)
        bot.answer_callback_query(call.id, "🚪"); return

    if call.data == 'd2_start':
        if uid != d['host_id'] and not is_admin_id(uid):
            bot.answer_callback_query(call.id, "❌ Хост"); return
        if len(d['team']) < 4:
            bot.answer_callback_query(call.id, "❌ 4 игрока"); return
        bot.answer_callback_query(call.id, "⚔️!"); start_2v2(cid); return

    if d['status'] != 'active': bot.answer_callback_query(call.id, "❌"); return
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    if not alive: bot.answer_callback_query(call.id, "❌"); return
    if uid != alive[d['turn_idx'] % len(alive)]:
        bot.answer_callback_query(call.id, "🎯 Не твой ход"); return
    p = d['players'][uid]

    if call.data == 'd2_aim':
        p['aim'] = True
        d['last_action_msg'] = f"🎯 <b>{p['name']}</b> прицелился!"
        d['turn_idx'] += 1; save_duel(cid, d)
        send_2v2_turn(cid); bot.answer_callback_query(call.id, "🎯"); return

    if call.data == 'd2_dist':
        enemy_team = d['team_b'] if p['team'] == 'A' else d['team_a']
        enemies_aim = [u for u in enemy_team if d['players'][u]['hp'] > 0 and d['players'][u].get('aim')]
        if enemies_aim:
            target = random.choice(enemies_aim)
            d['players'][target]['aim'] = False
            msg = f"🎭 <b>{p['name']}</b> сбил прицел у <b>{d['players'][target]['name']}</b>!"
        else:
            msg = f"🎭 <b>{p['name']}</b> отвлёк!"
        d['last_action_msg'] = msg
        d['turn_idx'] += 1; save_duel(cid, d)
        send_2v2_turn(cid); bot.answer_callback_query(call.id, "🎭"); return

    if call.data.startswith('d2_atk_'):
        target = call.data.replace('d2_atk_', '')
        if target not in d['players'] or d['players'][target]['hp'] <= 0:
            bot.answer_callback_query(call.id, "❌"); return
        if d['players'][target]['team'] == p['team']:
            bot.answer_callback_query(call.id, "❌ Союзник"); return
        aim = p.get('aim', False)
        ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
        if random.random() < ch:
            dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
            d['players'][target]['hp'] = max(0, d['players'][target]['hp'] - dmg)
            msg = f"💥 <b>{p['name']}</b> → <b>{d['players'][target]['name']}</b> на <b>{dmg}</b>!"
        else:
            msg = f"🌫 <b>{p['name']}</b> промахнулся!"
        p['aim'] = False
        d['last_action_msg'] = msg
        d['turn_idx'] += 1; save_duel(cid, d)
        a_alive = [u for u in d['team_a'] if d['players'][u]['hp'] > 0]
        b_alive = [u for u in d['team_b'] if d['players'][u]['hp'] > 0]
        if not a_alive or not b_alive: finish_2v2(cid); return
        send_2v2_turn(cid); bot.answer_callback_query(call.id, f"💥 {dmg}"); return

def finish_2v2(cid):
    d = get_duel(cid)
    if not d: return
    a_alive = [u for u in d['team_a'] if d['players'][u]['hp'] > 0]
    b_alive = [u for u in d['team_b'] if d['players'][u]['hp'] > 0]
    if a_alive and not b_alive: winners, losers = d['team_a'], d['team_b']
    elif b_alive and not a_alive: winners, losers = d['team_b'], d['team_a']
    else: winners, losers = [], []
    for u in winners: add_duel_win(u)
    for u in losers: add_duel_loss(u)
    wnames = ", ".join([d['players'][u]['name'] for u in winners])
    text = (
        f"🏆 <b>ДУЭЛЬ 2x2 ОКОНЧЕНА!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥇 Победила: <b>{wnames}</b>"
    )
    try: bot.send_message(cid, text, parse_mode='HTML')
    except: pass
    del_duel(cid)

# ===== БОССЫ =====
@bot.message_handler(commands=['boss', 'boss1', 'boss2', 'boss3', 'boss4', 'boss5', 'boss6', 'boss7'])
def cmd_boss(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "🐉 Только в группах."); return
    cmd = m.text.split()[0].replace('/', '')
    if '@' in cmd: cmd = cmd.split('@')[0]
    if cmd == 'boss':
        t = "🐉 <b>ВЫБОР БОССА</b>\n━━━━━━━━━━━━━━━\n\n"
        for n, b in BOSSES.items():
            t += f"{n}️⃣ {b['emoji']} <b>{b['name']}</b>\n     ❤️ {b['hp']} HP · 💎 +{b['diamonds']}\n\n"
        t += "<i>Напиши:</i> <code>/boss1</code> ... <code>/boss7</code>"
        bot.send_message(m.chat.id, t, parse_mode='HTML'); return
    try: bn = int(cmd.replace('boss', ''))
    except: bn = None
    if not bn or bn not in BOSSES:
        bot.send_message(m.chat.id, "❌ /boss1 ... /boss7"); return
    b = BOSSES[bn]
    g = get_boss(m.chat.id)
    if g and g.get('status') not in ('finished',):
        bot.send_message(m.chat.id, "🐉 Уже идёт."); return
    now = int(time.time())
    p = get_player(m.from_user.id, m.from_user.first_name, m.from_user.username)
    g = {
        'chat_id': m.chat.id, 'host_id': str(m.from_user.id),
        'boss_num': bn, 'boss_name': f"{b['emoji']} {b['name']}",
        'boss_hp': b['hp'], 'boss_max_hp': b['hp'], 'boss_diamonds': b['diamonds'],
        'players': {}, 'turn_idx': 0, 'status': 'lobby',
        'deadline': now + BOSS_LOBBY_TIME, 'lobby_msg_id': None,
        'fight_msg_id': None, 'last_msg': ''
    }
    g['players'][str(m.from_user.id)] = {
        'name': m.from_user.first_name, 'username': m.from_user.username or '',
        'hp': p.get('max_hp', PLAYER_MIN_HP), 'max_hp': p.get('max_hp', PLAYER_MIN_HP),
        'alive': True, 'aim': False, 'dmg_done': 0, 'order': 0
    }
    save_boss_g(m.chat.id, g)
    sent = bot.send_message(m.chat.id, boss_lobby_text(g), parse_mode='HTML',
        reply_markup=boss_lobby_kb(is_admin_id(m.from_user.id)))
    g['lobby_msg_id'] = sent.message_id
    save_boss_g(m.chat.id, g)
    threading.Timer(BOSS_LOBBY_TIME, boss_lobby_timeout, args=[m.chat.id]).start()
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[m.chat.id]).start()

def boss_lobby_kb(is_admin=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('⚔️ Присоединиться', 'b_join', 'success'),
        btn('🚪 Выйти', 'b_leave', 'danger')
    )
    kb.add(
        btn('▶️ Начать', 'b_start', 'primary'),
        btn('❌ Отменить', 'b_cancel', 'danger')
    )
    if is_admin:
        kb.add(btn('➕ Продлить', 'b_ext', 'primary'))
    return kb

def boss_lobby_text(g):
    pl = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p.get('max_hp', PLAYER_MIN_HP)} HP" for p in g['players'].values()])
    left = g.get('deadline',0) - int(time.time())
    return (
        f"🐉 <b>БОСС: {g['boss_name']}</b>\n━━━━━━━━━━━━━━━\n\n"
        f"❤️ HP босса: <b>{g['boss_max_hp']}</b>\n"
        f"💎 Награда: <b>+{g['boss_diamonds']} алмазов</b>\n\n"
        f"👥 Игроков: <b>{len(g['players'])}/{BOSS_MAX_PLAYERS}</b>\n"
        f"📌 Минимум: <b>{BOSS_MIN_PLAYERS}</b>\n"
        f"⏱ До старта: <b>{fmt_t(left)}</b>\n\n"
        f"<b>Команда:</b>\n{pl}"
    )

def boss_lobby_tick(cid):
    g = get_boss(cid)
    if not g or g.get('status') != 'lobby': return
    if (g.get('deadline',0) - int(time.time())) <= 0: return
    if g.get('lobby_msg_id'):
        sedit(cid, g['lobby_msg_id'], boss_lobby_text(g), boss_lobby_kb(is_admin_id(g['host_id'])))
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[cid]).start()

def boss_lobby_timeout(cid):
    g = get_boss(cid)
    if not g or g.get('status') != 'lobby': return
    if len(g['players']) >= BOSS_MIN_PLAYERS: start_boss_fight(cid)
    else:
        try: bot.send_message(cid, "⏱ Мало игроков. Отмена.", parse_mode='HTML')
        except: pass
        del_boss(cid)

@bot.callback_query_handler(func=lambda c: c.data in ('b_join','b_leave','b_start','b_cancel','b_ext'))
def boss_lobby_cb(call):
    cid = call.message.chat.id
    g = get_boss(cid)
    if not g or g.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌"); return
    uid = str(call.from_user.id); is_admin = is_admin_id(uid)
    mid = g.get('lobby_msg_id') or call.message.message_id

    if call.data == 'b_join':
        if uid in g['players']: bot.answer_callback_query(call.id, "✅"); return
        if len(g['players']) >= BOSS_MAX_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Макс {BOSS_MAX_PLAYERS}"); return
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        order = max([pl.get('order',0) for pl in g['players'].values()] + [0]) + 1
        g['players'][uid] = {
            'name': call.from_user.first_name, 'username': call.from_user.username or '',
            'hp': p.get('max_hp', PLAYER_MIN_HP), 'max_hp': p.get('max_hp', PLAYER_MIN_HP),
            'alive': True, 'aim': False, 'dmg_done': 0, 'order': order
        }
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "⚔️"); return

    if call.data == 'b_leave':
        if uid not in g['players']: bot.answer_callback_query(call.id, "❌"); return
        was_host = (uid == g['host_id'])
        del g['players'][uid]
        if was_host and g['players']:
            g['host_id'] = sorted(g['players'].keys(), key=lambda u: g['players'][u].get('order',0))[0]
        elif not g['players']:
            del_boss(cid); sedit(cid, mid, "❌ Закрыто.")
            bot.answer_callback_query(call.id, "🚪"); return
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "🚪"); return

    if call.data == 'b_start':
        if uid != g['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Хост"); return
        if len(g['players']) < BOSS_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Минимум {BOSS_MIN_PLAYERS}"); return
        bot.answer_callback_query(call.id, "🐉!"); start_boss_fight(cid); return

    if call.data == 'b_cancel':
        if uid != g['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌"); return
        del_boss(cid); sedit(cid, mid, "❌ Отменено.")
        bot.answer_callback_query(call.id, "Отменено"); return

    if call.data == 'b_ext':
        if not is_admin: bot.answer_callback_query(call.id, "❌"); return
        g['deadline'] = int(time.time()) + BOSS_LOBBY_TIME
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "➕"); return

def boss_fight_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        btn('🔫 Атака', 'bf_atk', 'danger'),
        btn('🏏 Бита', 'bf_bat', 'primary'),
        btn('🎯 Прицел', 'bf_aim', 'success')
    )
    return kb

def alive_sorted(g):
    a = [(u,p) for u,p in g['players'].items() if p['alive']]
    a.sort(key=lambda x: x[1].get('order',0))
    return a

def boss_fight_text(g):
    ap = alive_sorted(g)
    pt = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p['hp']}/{p['max_hp']} HP{' 🎯' if p.get('aim') else ''}" for _, p in ap])
    if not pt: pt = "💀 Все погибли"
    tn = '?'
    if ap: tn = ap[g.get('turn_idx',0) % len(ap)][1]['name']
    pct = int((g['boss_hp'] / g['boss_max_hp']) * 100) if g['boss_max_hp'] else 0
    bar = '█' * (pct//10) + '░' * (10 - pct//10)
    t = (
        f"🐉 <b>{g['boss_name']}</b>\n━━━━━━━━━━━━━━━\n"
        f"❤️ HP: <b>{g['boss_hp']}/{g['boss_max_hp']}</b>\n"
        f"{bar} {pct}%\n\n"
        f"<b>КОМАНДА:</b>\n{pt}\n\n"
        f"🎯 Ход: <b>{tn}</b>"
    )
    if g.get('last_msg'): t += f"\n\n{g['last_msg']}"
    return t

def start_boss_fight(cid):
    g = get_boss(cid)
    if not g: return
    g['status'] = 'fight'; g['turn_idx'] = 0; g['last_msg'] = '⚔️ Началось!'
    for u in g['players']: g['players'][u]['aim'] = False
    save_boss_g(cid, g)
    try:
        msg = bot.send_message(cid, boss_fight_text(g), parse_mode='HTML', reply_markup=boss_fight_kb())
        g['fight_msg_id'] = msg.message_id
        save_boss_g(cid, g)
    except: pass

def next_boss_turn(g):
    ap = alive_sorted(g)
    if not ap: return
    g['turn_idx'] += 1
    if g['turn_idx'] % len(ap) == 0: boss_attack(g)

def boss_attack(g):
    ap = alive_sorted(g)
    if not ap: return
    tu, t = random.choice(ap)
    dmg = random.randint(BOSS_DMG_MIN, BOSS_DMG_MAX)
    t['hp'] = max(0, t['hp'] - dmg)
    msg = f"👹 Босс бьёт <b>{t['name']}</b> на <b>{dmg}</b>!"
    if t['hp'] <= 0: t['alive'] = False; msg += f"\n💀 <b>{t['name']}</b> погиб!"
    g['last_msg'] = msg

@bot.callback_query_handler(func=lambda c: c.data.startswith('bf_'))
def boss_fight_cb(call):
    cid = call.message.chat.id
    g = get_boss(cid)
    if not g or g['status'] != 'fight': bot.answer_callback_query(call.id, "❌"); return
    uid = str(call.from_user.id)
    if uid not in g['players'] or not g['players'][uid]['alive']:
        bot.answer_callback_query(call.id, "💀"); return
    ap = alive_sorted(g)
    if not ap: bot.answer_callback_query(call.id, "Ошибка"); return
    if uid != ap[g['turn_idx'] % len(ap)][0]:
        bot.answer_callback_query(call.id, "🎯 Не твой ход"); return
    p = g['players'][uid]

    if call.data == 'bf_aim':
        p['aim'] = True
        g['last_msg'] = f"🎯 <b>{p['name']}</b> прицелился!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, "🎯"); return

    if call.data == 'bf_atk':
        dmg = random.randint(BOSS_ATK_MIN, BOSS_ATK_MAX)
        if p.get('aim'): dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
        g['boss_hp'] = max(0, g['boss_hp'] - dmg)
        p['dmg_done'] = p.get('dmg_done',0) + dmg
        g['last_msg'] = f"🔫 <b>{p['name']}</b> на <b>{dmg}</b>!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, f"🔫 {dmg}"); return

    if call.data == 'bf_bat':
        if random.random() < BOSS_BAT_CHANCE:
            dmg = random.randint(BOSS_BAT_MIN, BOSS_BAT_MAX)
            if p.get('aim'): dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
            g['boss_hp'] = max(0, g['boss_hp'] - dmg)
            p['dmg_done'] = p.get('dmg_done',0) + dmg
            g['last_msg'] = f"🏏 <b>{p['name']}</b> на <b>{dmg}</b>!"
        else:
            if p.get('aim'): p['aim'] = False
            g['last_msg'] = f"🏏 <b>{p['name']}</b> промах!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, "🏏"); return

def check_boss_end(cid, g):
    if g['boss_hp'] <= 0:
        g['status'] = 'finished'; save_boss_g(cid, g)
        dia = g['boss_diamonds']
        msg = f"🏆 <b>БОСС ПОВЕРЖЕН!</b>\n━━━━━━━━━━━━━━━\n🐉 <b>{g['boss_name']}</b>\n\n<b>Награды:</b>\n"
        for u, p in g['players'].items():
            add_boss_win(u, dia)
            msg += f"• {p['name']} — <b>{p.get('dmg_done',0)}</b> урона, <b>+{dia} 💎</b>\n"
        sedit(cid, g.get('fight_msg_id'), msg); del_boss(cid); return True
    if not [u for u,p in g['players'].items() if p['alive']]:
        g['status'] = 'finished'; save_boss_g(cid, g)
        for u in g['players']: add_boss_loss(u)
        sedit(cid, g.get('fight_msg_id'), "💀 <b>ВСЕ ПОГИБЛИ!</b>"); del_boss(cid); return True
    return False

# ===== МЕНЮ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('m_'))
def menu_cb(call):
    u = call.from_user; uid = u.id; cid = call.message.chat.id
    if call.data == 'm_prof': send_profile(cid, uid, u.first_name, u.username)
    elif call.data == 'm_top': send_top(cid)
    elif call.data == 'm_shop': send_shop(cid, uid, u.first_name, u.username)
    elif call.data == 'm_daily': send_daily(cid, uid, u.first_name, u.username)
    elif call.data == 'm_mine': send_mine(cid, uid, u.first_name, u.username)
    elif call.data == 'm_duel': bot.send_message(cid, "⚔️ /duel (1x1) или /duel2x2 (2x2)")
    elif call.data == 'm_boss': bot.send_message(cid, "🐉 /boss1 ... /boss7")
    elif call.data == 'm_help': cmd_help(call.message)
    elif call.data == 'm_back':
        bot.send_message(cid, "🎭 Меню:", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start','🎭 Меню'),
            types.BotCommand('help','💬 Помощь'),
            types.BotCommand('profile','👤 Профиль'),
            types.BotCommand('top','🏆 Топ'),
            types.BotCommand('daily','📅 Бонус'),
            types.BotCommand('mine','⛏ Шахта'),
            types.BotCommand('duel','⚔️ Дуэль 1x1'),
            types.BotCommand('duel2x2','⚔️ Дуэль 2x2'),
            types.BotCommand('shop','💎 Магазин'),
        ])
    except: pass

set_commands()
print('Bot started')
bot.infinity_polling()
