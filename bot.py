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
BOSS_MAX_PLAYERS = 4
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
            'wins': 0, 'losses': 0,
            'boss_wins': 0, 'boss_losses': 0,
            'diamonds': 0, 'max_hp': PLAYER_MIN_HP
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Аноним')
        stats[k]['username'] = uname or stats[k].get('username', '')
        for f, v in {'wins':0,'losses':0,'boss_wins':0,'boss_losses':0,'diamonds':0,'max_hp':PLAYER_MIN_HP}.items():
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
    p = get_player(uid); p['boss_wins'] += 1; p['diamonds'] = p.get('diamonds',0) + diamonds; update_player(uid, p)

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

def dname(p):
    if not p: return 'Аноним'
    u = (p.get('username') or '').strip()
    if u: return '@'+u
    f = (p.get('first_name') or '').strip()
    return f if f and f != 'Аноним' else 'Аноним'

def sedit(cid, mid, text, kb=None):
    try:
        bot.edit_message_text(text, chat_id=cid, message_id=mid, parse_mode='HTML', reply_markup=kb)
        return True
    except: return False

bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type','text/plain'); self.end_headers()
        self.wfile.write(b'Bot is running')

threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get('PORT',10000))), Handler).serve_forever(), daemon=True).start()

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('👤 Профиль', callback_data='m_prof'),
        types.InlineKeyboardButton('🏆 Топ', callback_data='m_top')
    )
    kb.add(
        types.InlineKeyboardButton('⚔️ Дуэль', callback_data='m_duel'),
        types.InlineKeyboardButton('🐉 Боссы', callback_data='m_boss')
    )
    kb.add(types.InlineKeyboardButton('💎 Алмазы → HP', callback_data='m_shop'))
    kb.add(types.InlineKeyboardButton('💬 Помощь', callback_data='m_help'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    get_player(uid, m.from_user.first_name, m.from_user.username)
    text = (
        f"🎭 <b>DARKGRAM</b>\n━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{m.from_user.first_name}</b>!\n\n"
        f"⚔️ Дуэли 1 на 1\n"
        f"🐉 Боссы 2-4 игрока\n"
        f"💎 Алмазы → HP\n"
        f"🏆 Топ по победам\n\n"
        f"👇 <i>Выбирай:</i>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"⚔️ <b>Дуэли:</b> <code>/duel</code> в ответ на сообщение\n"
        f"🐉 <b>Боссы:</b> <code>/boss1</code> ... <code>/boss7</code>\n"
        f"💎 <b>Алмазы:</b> <code>/shop</code>\n\n"
        f"🐉 <b>БОССЫ:</b>\n"
        f"1️⃣ 🐺 1000 HP → 2 💎\n"
        f"2️⃣ 🦂 1500 HP → 3 💎\n"
        f"3️⃣ 🦁 2000 HP → 4 💎\n"
        f"4️⃣ 👺 2500 HP → 5 💎\n"
        f"5️⃣ 👹 3000 HP → 6 💎\n"
        f"6️⃣ 🧟 3500 HP → 7 💎\n"
        f"7️⃣ 🐉 5000 HP → 10 💎\n\n"
        f"💎 <b>МАГАЗИН:</b>\n"
        f"10 💎 → +20 HP\n"
        f"25 💎 → +45 HP\n"
        f"40 💎 → +75 HP"
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

def send_profile(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    total = p['wins'] + p['losses']
    wr = round(p['wins']/total*100) if total else 0
    bt = p.get('boss_wins',0) + p.get('boss_losses',0)
    bwr = round(p.get('boss_wins',0)/bt*100) if bt else 0
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"<b>{dname(p)}</b>\n\n"
        f"⚔️ <b>ДУЭЛИ</b>\n"
        f"🏆 Побед: <b>{p['wins']}</b>\n"
        f"💀 Поражений: <b>{p['losses']}</b>\n"
        f"📊 Винрейт: <b>{wr}%</b>\n\n"
        f"🐉 <b>БОССЫ</b>\n"
        f"🏆 Побед: <b>{p.get('boss_wins',0)}</b>\n"
        f"💀 Поражений: <b>{p.get('boss_losses',0)}</b>\n"
        f"📊 Винрейт: <b>{bwr}%</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Алмазы: <b>{p.get('diamonds',0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>"
    )
    bot.send_message(cid, text, parse_mode='HTML')

def send_top(cid):
    stats = load_stats()
    if not stats:
        bot.send_message(cid, "🏆 Пока пусто."); return
    ss = sorted(stats.items(), key=lambda x: x[1].get('wins',0), reverse=True)[:20]
    text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n━━━━━━━━━━━━━━━\n\n"
    n = 0
    for i, (uid, p) in enumerate(ss, 1):
        if p.get('wins',0) == 0: continue
        n += 1
        med = '🥇' if n==1 else '🥈' if n==2 else '🥉' if n==3 else f'<b>{n}.</b>'
        text += f"{med} {dname(p)}\n     ⚔️ {p['wins']} побед · 💀 {p['losses']}\n\n"
    if n == 0: text += "Пока никто не побеждал."
    bot.send_message(cid, text, parse_mode='HTML')

def send_shop(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    text = (
        f"💎 <b>МАГАЗИН АЛМАЗОВ</b>\n━━━━━━━━━━━━━━━\n\n"
        f"💰 Алмазов: <b>{p.get('diamonds',0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>\n\n"
        f"📌 <b>Курсы:</b>\n"
        f"10 💎 → +20 HP\n"
        f"25 💎 → +45 HP\n"
        f"40 💎 → +75 HP"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('10 💎 → +20 HP', callback_data='buy_10'),
        types.InlineKeyboardButton('25 💎 → +45 HP', callback_data='buy_25'),
        types.InlineKeyboardButton('40 💎 → +75 HP', callback_data='buy_40'),
        types.InlineKeyboardButton('◀️ Назад', callback_data='m_back')
    )
    bot.send_message(cid, text, parse_mode='HTML', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_hp(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    costs = {'buy_10': (10,20), 'buy_25': (25,45), 'buy_40': (40,75)}
    cost, hp = costs.get(call.data, (0,0))
    if p.get('diamonds',0) < cost:
        bot.answer_callback_query(call.id, f"❌ Нужно {cost} 💎"); return
    if p.get('max_hp', PLAYER_MIN_HP) + hp > PLAYER_MAX_HP:
        bot.answer_callback_query(call.id, "❌ Максимум HP"); return
    p['diamonds'] -= cost
    p['max_hp'] = p.get('max_hp', PLAYER_MIN_HP) + hp
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{hp} HP")

@bot.message_handler(commands=['duel'])
def cmd_duel(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "⚔️ Только в группах."); return
    if not m.reply_to_message:
        bot.send_message(m.chat.id, "⚔️ Ответь на сообщение игрока и напиши /duel"); return
    t = m.reply_to_message.from_user
    if t.id == m.from_user.id:
        bot.send_message(m.chat.id, "❌ Себе нельзя."); return
    if t.is_bot:
        bot.send_message(m.chat.id, "❌ С ботом нельзя."); return
    ex = get_duel(m.chat.id)
    if ex and ex.get('status') in ('pending','active'):
        bot.send_message(m.chat.id, "⚔️ Уже идёт дуэль."); return
    now = int(time.time())
    duel = {
        'chat_id': m.chat.id,
        'p1_id': str(m.from_user.id), 'p1_name': m.from_user.first_name,
        'p2_id': str(t.id), 'p2_name': t.first_name,
        'p1_hp': DUEL_HP, 'p2_hp': DUEL_HP,
        'p1_aim': False, 'p2_aim': False,
        'turn': str(m.from_user.id), 'status': 'pending',
        'deadline': now + DUEL_TIMEOUT, 'msg_id': None, 'last_action_msg': ''
    }
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('✅ Принять', callback_data='d_yes'),
        types.InlineKeyboardButton('❌ Отклонить', callback_data='d_no')
    )
    sent = bot.send_message(m.chat.id, duel_pending_text(duel), parse_mode='HTML', reply_markup=kb)
    duel['msg_id'] = sent.message_id
    save_duel(m.chat.id, duel)
    threading.Timer(DUEL_TIMEOUT, duel_timeout, args=[m.chat.id]).start()

def duel_pending_text(d):
    left = d['deadline'] - int(time.time())
    return (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{d['p1_name']}</b> вызывает <b>{d['p2_name']}</b>!\n\n"
        f"<i>{d['p2_name']}, принимаешь?</i>\n\n"
        f"⏱ Осталось: <b>{fmt_t(left)}</b>"
    )

def duel_timeout(cid):
    d = get_duel(cid)
    if not d or d.get('status') != 'pending': return
    sedit(cid, d.get('msg_id'), "⌛ Время вышло. Вызов отменён.")
    del_duel(cid)

def duel_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('🔫 Выстрел', callback_data='d_shoot'),
        types.InlineKeyboardButton('🎯 Прицел', callback_data='d_aim'),
        types.InlineKeyboardButton('🎭 Отвлечь', callback_data='d_dist')
    )
    return kb

def duel_text(d):
    a1 = ' 🎯' if d['p1_aim'] else ''
    a2 = ' 🎯' if d['p2_aim'] else ''
    tn = d['p1_name'] if d['turn'] == d['p1_id'] else d['p2_name']
    t = (
        f"⚔️ <b>ДУЭЛЬ</b>\n━━━━━━━━━━━━━━━\n\n"
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

    if call.data == 'd_yes':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌ Неактуально"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌ Не твой вызов"); return
        d['status'] = 'active'; d['last_action_msg'] = ''
        save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb())
        bot.answer_callback_query(call.id, "⚔️ Началась!"); return

    if call.data == 'd_no':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌ Неактуально"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌ Не твой вызов"); return
        del_duel(cid)
        sedit(cid, d['msg_id'], "❌ Отклонено.")
        bot.answer_callback_query(call.id, "Отклонено"); return

    if d.get('status') != 'active': bot.answer_callback_query(call.id, "Не идёт"); return
    if uid != d['turn']: bot.answer_callback_query(call.id, "🎯 Не твой ход"); return

    if call.data == 'd_aim':
        if uid == d['p1_id']: d['p1_aim'] = True
        else: d['p2_aim'] = True
        d['last_action_msg'] = "🎯 <i>Игрок прицелился!</i>"
        next_turn(d); save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb())
        bot.answer_callback_query(call.id, "🎯"); return

    if call.data == 'd_dist':
        if uid == d['p1_id']:
            had = d['p2_aim']; d['p2_aim'] = False
        else:
            had = d['p1_aim']; d['p1_aim'] = False
        msg = random.choice(DISTRACT)
        msg += "\n💥 <b>Прицел сбит!</b>" if had else "\n🤷 <i>Прицела не было.</i>"
        d['last_action_msg'] = msg
        next_turn(d); save_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb())
        bot.answer_callback_query(call.id, "🎭"); return

    if call.data == 'd_shoot':
        if uid == d['p1_id']:
            aim = d['p1_aim']; d['p1_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p2_hp'] = max(0, d['p2_hp'] - dmg)
                msg = f"💥 Попадание! <b>-{dmg}</b> HP"
            else: msg = "🌫 Промах!"
        else:
            aim = d['p2_aim']; d['p2_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p1_hp'] = max(0, d['p1_hp'] - dmg)
                msg = f"💥 Попадание! <b>-{dmg}</b> HP"
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
        sedit(cid, d['msg_id'], duel_text(d), duel_kb())
        bot.answer_callback_query(call.id)

@bot.message_handler(commands=['boss','boss1','boss2','boss3','boss4','boss5','boss6','boss7'])
def cmd_boss(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "🐉 Боссы только в группах."); return
    cmd = m.text.split()[0].replace('/','')
    if '@' in cmd: cmd = cmd.split('@')[0]
    if cmd == 'boss':
        t = "🐉 <b>ВЫБОР БОССА</b>\n━━━━━━━━━━━━━━━\n\n"
        for n, b in BOSSES.items():
            t += f"{n}️⃣ {b['emoji']} <b>{b['name']}</b>\n     ❤️ {b['hp']} HP · 💎 +{b['diamonds']}\n\n"
        t += "<i>Напиши:</i> <code>/boss1</code> ... <code>/boss7</code>"
        bot.send_message(m.chat.id, t, parse_mode='HTML'); return
    try: bn = int(cmd.replace('boss',''))
    except: bn = None
    if not bn or bn not in BOSSES:
        bot.send_message(m.chat.id, "❌ /boss1 ... /boss7"); return
    b = BOSSES[bn]
    g = get_boss(m.chat.id)
    if g and g.get('status') not in ('finished',):
        bot.send_message(m.chat.id, "🐉 Уже идёт бой."); return
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

def is_admin_id(uid):
    try: return int(uid) in ADMIN_IDS
    except: return False

def boss_lobby_kb(is_admin=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('⚔️ Присоединиться', callback_data='b_join'),
        types.InlineKeyboardButton('🚪 Выйти', callback_data='b_leave')
    )
    kb.add(
        types.InlineKeyboardButton('▶️ Начать', callback_data='b_start'),
        types.InlineKeyboardButton('❌ Отменить', callback_data='b_cancel')
    )
    if is_admin:
        kb.add(types.InlineKeyboardButton('➕ Продлить', callback_data='b_ext'))
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
        try: bot.send_message(cid, f"⏱ Мало игроков. Отмена.", parse_mode='HTML')
        except: pass
        del_boss(cid)

@bot.callback_query_handler(func=lambda c: c.data in ('b_join','b_leave','b_start','b_cancel','b_ext'))
def boss_lobby_cb(call):
    cid = call.message.chat.id
    g = get_boss(cid)
    if not g or g.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌ Закрыто"); return
    uid = str(call.from_user.id); is_admin = is_admin_id(uid)
    mid = g.get('lobby_msg_id') or call.message.message_id

    if call.data == 'b_join':
        if uid in g['players']: bot.answer_callback_query(call.id, "✅ Уже в команде"); return
        if len(g['players']) >= BOSS_MAX_PLAYERS: bot.answer_callback_query(call.id, f"❌ Макс {BOSS_MAX_PLAYERS}"); return
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        order = max([pl.get('order',0) for pl in g['players'].values()] + [0]) + 1
        g['players'][uid] = {
            'name': call.from_user.first_name, 'username': call.from_user.username or '',
            'hp': p.get('max_hp', PLAYER_MIN_HP), 'max_hp': p.get('max_hp', PLAYER_MIN_HP),
            'alive': True, 'aim': False, 'dmg_done': 0, 'order': order
        }
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "⚔️ В команде!"); return

    if call.data == 'b_leave':
        if uid not in g['players']: bot.answer_callback_query(call.id, "❌ Не в команде"); return
        was_host = (uid == g['host_id'])
        del g['players'][uid]
        if was_host and g['players']:
            g['host_id'] = sorted(g['players'].keys(), key=lambda u: g['players'][u].get('order',0))[0]
        elif not g['players']:
            del_boss(cid); sedit(cid, mid, "❌ Лобби закрыто.")
            bot.answer_callback_query(call.id, "🚪"); return
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "🚪 Вышел"); return

    if call.data == 'b_start':
        if uid != g['host_id'] and not is_admin: bot.answer_callback_query(call.id, "❌ Только хост"); return        if len(g['players']) < BOSS_MIN_PLAYERS: bot.answer_callback_query(call.id, f"❌ Минимум {BOSS_MIN_PLAYERS}"); return
        bot.answer_callback_query(call.id, "🐉 Начинаем!"); start_boss_fight(cid); return

    if call.data == 'b_cancel':
        if uid != g['host_id'] and not is_admin: bot.answer_callback_query(call.id, "❌ Только хост"); return
        del_boss(cid); sedit(cid, mid, "❌ Отменено.")
        bot.answer_callback_query(call.id, "Отменено"); return

    if call.data == 'b_ext':
        if not is_admin: bot.answer_callback_query(call.id, "❌ Только админ"); return
        g['deadline'] = int(time.time()) + BOSS_LOBBY_TIME
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "➕ Продлено")

def boss_fight_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton('🔫 Атака', callback_data='bf_atk'),
        types.InlineKeyboardButton('🏏 Бита', callback_data='bf_bat'),
        types.InlineKeyboardButton('🎯 Прицел', callback_data='bf_aim')
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
    if ap:
        tn = ap[g.get('turn_idx',0) % len(ap)][1]['name']
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
    g['status'] = 'fight'; g['turn_idx'] = 0; g['last_msg'] = '⚔️ Бой начался!'
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
    if not g or g['status'] != 'fight': bot.answer_callback_query(call.id, "❌ Не идёт"); return
    uid = str(call.from_user.id)
    if uid not in g['players'] or not g['players'][uid]['alive']:
        bot.answer_callback_query(call.id, "💀 Не можешь"); return
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
        g['last_msg'] = f"🔫 <b>{p['name']}</b> бьёт на <b>{dmg}</b>!"
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
            g['last_msg'] = f"🏏 <b>{p['name']}</b> бьёт битой на <b>{dmg}</b>!"
        else:
            if p.get('aim'): p['aim'] = False
            g['last_msg'] = f"🏏 <b>{p['name']}</b> промахнулся!"
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

@bot.callback_query_handler(func=lambda c: c.data.startswith('m_'))
def menu_cb(call):
    u = call.from_user; uid = u.id; cid = call.message.chat.id
    if call.data == 'm_prof': send_profile(cid, uid, u.first_name, u.username)
    elif call.data == 'm_top': send_top(cid)
    elif call.data == 'm_shop': send_shop(cid, uid, u.first_name, u.username)
    elif call.data == 'm_duel': bot.send_message(cid, "⚔️ В группе ответь на сообщение игрока и напиши /duel")
    elif call.data == 'm_boss': bot.send_message(cid, "🐉 Напиши /boss1 ... /boss7")
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
            types.BotCommand('duel','⚔️ Дуэль'),
            types.BotCommand('shop','💎 Магазин'),
        ])
    except: pass

set_commands()
print('Bot started')
bot.infinity_polling()
