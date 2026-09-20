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
CLANS_FILE = 'clans.json'
SEASON_FILE = 'season.json'
HISTORY_FILE = 'season_history.json'

ADMIN_IDS = [8907438590]
TOKEN = '8872773404:AAEblXoLxAi1bGXVWtPNq3Tjmxb27JnlnOg'

DUEL_HP = 100
DUEL_SHOOT_MIN = 25
DUEL_SHOOT_MAX = 45
DUEL_AIM_BONUS = 0.9
DUEL_NOAIM_CHANCE = 0.6
DUEL_TIMEOUT = 300
DUEL_STALE_TIMEOUT = 900

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

SEASON_DURATION = 7 * 24 * 3600
CLAN_CREATE_COST = 50

RANKS = [
    (0,   '🥚 Newbie'),
    (5,   '⚔️ Warrior'),
    (15,  '🛡 Veteran'),
    (30,  '🔥 Master'),
    (50,  '💎 Legend'),
    (100, '👑 Champion'),
    (250, '🌟 God of War'),
]

SKINS = {
    'fire':    {'name': 'Fire',    'emoji': '🔥', 'price': 30},
    'star':    {'name': 'Star',    'emoji': '🌟', 'price': 50},
    'diamond': {'name': 'Diamond', 'emoji': '💎', 'price': 80},
    'crown':   {'name': 'Crown',   'emoji': '👑', 'price': 150},
    'dragon':  {'name': 'Dragon',  'emoji': '🐉', 'price': 250},
}
ARMORS = {
    'light':  {'name': 'Light Armor',  'emoji': '🥼', 'price': 40,  'defense': 10},
    'medium': {'name': 'Medium Armor', 'emoji': '🦺', 'price': 90,  'defense': 25},
    'heavy':  {'name': 'Heavy Armor',  'emoji': '🛡', 'price': 200, 'defense': 45},
}
WEAPONS = {
    'bat':  {'name': 'Bat',    'emoji': '🏏', 'price': 50,  'damage': 15},
    'sword':{'name': 'Sword',  'emoji': '⚔️', 'price': 120, 'damage': 35},
    'axe':  {'name': 'Axe',    'emoji': '🪓', 'price': 200, 'damage': 60},
    'bow':  {'name': 'Bow',    'emoji': '🏹', 'price': 300, 'damage': 90},
}
PETS = {
    'cat':    {'name': 'Cat',    'emoji': '🐱', 'price': 60,  'bonus_hp': 25,  'bonus_dia': 0},
    'wolf':   {'name': 'Wolf',   'emoji': '🐺', 'price': 150, 'bonus_hp': 50,  'bonus_dia': 1},
    'eagle':  {'name': 'Eagle',  'emoji': '🦅', 'price': 300, 'bonus_hp': 100, 'bonus_dia': 2},
    'dragon': {'name': 'Dragon', 'emoji': '🐉', 'price': 600, 'bonus_hp': 250, 'bonus_dia': 5},
}

BOSSES = {
    1: {'name': 'Hungry Wolf',    'emoji': '🐺', 'hp': 1000, 'diamonds': 2},
    2: {'name': 'Desert Scorpion','emoji': '🦂', 'hp': 1500, 'diamonds': 3},
    3: {'name': 'Bloody Lion',    'emoji': '🦁', 'hp': 2000, 'diamonds': 4},
    4: {'name': 'Fire Demon',     'emoji': '👺', 'hp': 2500, 'diamonds': 5},
    5: {'name': 'Dark Lord',      'emoji': '👹', 'hp': 3000, 'diamonds': 6},
    6: {'name': 'Zombie King',    'emoji': '🧟', 'hp': 3500, 'diamonds': 7},
    7: {'name': 'Ancient Dragon', 'emoji': '🐉', 'hp': 5000, 'diamonds': 10},
}

DISTRACT = [
    "🎭 Faked a dodge — aim broke!",
    "💨 Dashed sideways!",
    "🪞 Mirror throw!",
    "🌫 Smoke screen!",
    "🎪 Backflip!",
    "🦅 Soared up!",
    "🎯 Sand in eyes!",
    "🌀 Sharp roll!",
    "🎺 Shouted loud!",
    "🌟 Flash!",
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
def load_clans(): return load_json(CLANS_FILE, {})
def save_clans(d): save_json(CLANS_FILE, d)
def load_history(): return load_json(HISTORY_FILE, [])

def get_all_duels(cid):
    duels = load_duels()
    val = duels.get(str(cid), [])
    if isinstance(val, dict):
        return [val] if val else []
    return val if isinstance(val, list) else []

def save_all_duels(cid, lst):
    duels = load_duels()
    duels[str(cid)] = lst
    save_duels(duels)

def cleanup_duels(cid):
    lst = get_all_duels(cid)
    now = int(time.time())
    new_lst = [d for d in lst if now - d.get('created', 0) < DUEL_STALE_TIMEOUT]
    if len(new_lst) != len(lst):
        save_all_duels(cid, new_lst)
    return new_lst

def find_duel_by_user(cid, uid):
    lst = get_all_duels(cid)
    for d in lst:
        if uid in (d.get('p1_id'), d.get('p2_id')):
            return d
        if d.get('mode') == '2v2' and uid in d.get('team', []):
            return d
    return None

def find_duel_by_id(cid, duel_id):
    lst = get_all_duels(cid)
    for d in lst:
        if d.get('id') == duel_id: return d
    return None

def update_duel(cid, duel):
    lst = get_all_duels(cid)
    for i, d in enumerate(lst):
        if d.get('id') == duel.get('id'):
            lst[i] = duel
            save_all_duels(cid, lst)
            return True
    return False

def add_duel(cid, duel):
    lst = get_all_duels(cid)
    lst.append(duel)
    save_all_duels(cid, lst)

def del_duel_by_id(cid, duel_id):
    lst = get_all_duels(cid)
    lst = [d for d in lst if d.get('id') != duel_id]
    save_all_duels(cid, lst)

def load_season():
    season = load_json(SEASON_FILE, None)
    now = int(time.time())
    if not season or now >= season.get('end', 0):
        if season: end_season(season)
        season = {
            'number': (season['number'] + 1) if season else 1,
            'start': now, 'end': now + SEASON_DURATION
        }
        save_json(SEASON_FILE, season)
        stats = load_stats()
        for k in stats:
            stats[k]['wins'] = 0
        save_stats(stats)
    return season

def end_season(season):
    stats = load_stats()
    top = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:3]
    champions = []
    for uid, p in top:
        if p.get('wins', 0) > 0:
            champions.append({
                'uid': uid, 'name': p.get('first_name', 'Unknown'),
                'username': p.get('username', ''), 'wins': p.get('wins', 0)
            })
    history = load_history()
    history.append({
        'season': season.get('number', 1), 'start': season.get('start', 0),
        'end': season.get('end', 0), 'champions': champions
    })
    save_json(HISTORY_FILE, history)

def get_player(uid, fname='Anonymous', uname=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': fname or 'Anonymous', 'username': uname or '',
            'wins': 0, 'losses': 0, 'boss_wins': 0, 'boss_losses': 0,
            'diamonds': 0, 'max_hp': PLAYER_MIN_HP,
            'last_daily': 0, 'daily_streak': 0, 'last_mine': 0,
            'skin': None, 'armor': None, 'weapon': None, 'pet': None, 'clan': None
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Anonymous')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {'wins':0,'losses':0,'boss_wins':0,'boss_losses':0,
                    'diamonds':0,'max_hp':PLAYER_MIN_HP,
                    'last_daily':0,'daily_streak':0,'last_mine':0,
                    'skin':None,'armor':None,'weapon':None,'pet':None,'clan':None}
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
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {s}s"
    return f"{s}s"

def fmt_days(sec):
    sec = max(0, int(sec))
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    if d > 0: return f"{d}d {h}h"
    if h > 0: return f"{h}h {m}m"
    return f"{m}m"

def get_rank(wins):
    rank = RANKS[0][1]
    for req, name in RANKS:
        if wins >= req: rank = name
    return rank

def dname(p):
    if not p: return 'Anonymous'
    u = (p.get('username') or '').strip()
    if u: return '@' + u
    f = (p.get('first_name') or '').strip()
    return f if f and f != 'Anonymous' else 'Anonymous'

def pname(p, uid=None):
    name = dname(p)
    skin = p.get('skin')
    if skin and skin in SKINS:
        name += ' ' + SKINS[skin]['emoji']
    return name

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
    if style:
        try:
            return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
        except TypeError:
            return types.InlineKeyboardButton(text=text, callback_data=data)
    return types.InlineKeyboardButton(text=text, callback_data=data)

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('👤 Profile', 'm_prof', 'primary'),
        btn('🏆 Top', 'm_top', 'primary')
    )
    kb.add(
        btn('⚔️ Duel', 'm_duel', 'primary'),
        btn('🐉 Bosses', 'm_boss', 'primary')
    )
    kb.add(
        btn('📅 Daily', 'm_daily', 'success'),
        btn('⛏ Mine', 'm_mine', 'success')
    )
    kb.add(btn('💎 Shop', 'm_shop', 'success'))
    kb.add(
        btn('🏅 Season', 'm_season', 'primary'),
        btn('👥 Clans', 'm_clans', 'primary')
    )
    kb.add(btn('💬 Help', 'm_help'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    get_player(uid, m.from_user.first_name, m.from_user.username)
    load_season()
    text = (
        f"🎭 <b>DARKGRAM</b>\n━━━━━━━━━━━━━━━\n\n"
        f"👋 Hi, <b>{m.from_user.first_name}</b>!\n\n"
        f"⚔️ Duels 1v1 & 2v2\n"
        f"🐉 Bosses (2-15)\n"
        f"📅 Daily · ⛏ Mine\n"
        f"💎 Shop\n"
        f"👥 Clans · 🏅 Season\n\n"
        f"👇 <i>Choose:</i>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>HELP</b>\n━━━━━━━━━━━━━━━\n\n"
        f"⚔️ <b>1v1:</b> <code>/duel</code> (reply)\n"
        f"⚔️ <b>Cancel:</b> <code>/duel_cancel</code>\n"
        f"⚔️ <b>2v2:</b> <code>/duel2x2</code>\n"
        f"🐉 <b>Bosses:</b> <code>/boss1</code>...<code>/boss7</code>\n"
        f"📅 <code>/daily</code> · ⛏ <code>/mine</code>\n"
        f"💎 <code>/shop</code> · 🏅 <code>/season</code> · 👥 <code>/clans</code>\n\n"
        f"<i>Multiple duels run at once in one chat!</i>"
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

@bot.message_handler(commands=['season'])
def cmd_season(m):
    send_season(m.chat.id)

@bot.message_handler(commands=['clans'])
def cmd_clans(m):
    send_clans(m.chat.id, m.from_user.id, m.from_user.first_name, m.from_user.username)

def send_season(cid):
    season = load_season()
    now = int(time.time())
    left = season['end'] - now
    stats = load_stats()
    top = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:3]
    text = (
        f"🏅 <b>DARKGRAM SEASON {season['number']}</b>\n━━━━━━━━━━━━━━━\n\n"
        f"📅 Started: <b>{time.strftime('%b %d, %Y', time.localtime(season['start']))}</b>\n"
        f"📅 Ends: <b>{time.strftime('%b %d, %Y', time.localtime(season['end']))}</b>\n"
        f"⏱ Left: <b>{fmt_days(left)}</b>\n\n"
        f"🏆 <b>Season Top-3:</b>\n"
    )
    medals = ['🥇', '🥈', '🥉']
    n = 0
    for i, (uid, p) in enumerate(top):
        if p.get('wins', 0) == 0: continue
        n += 1
        text += f"{medals[i]} {pname(p)} — <b>{p['wins']}</b> wins\n"
    if n == 0: text += "<i>No wins yet.</i>"
    bot.send_message(cid, text, parse_mode='HTML')

def send_profile(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    total = p['wins'] + p['losses']
    wr = round(p['wins'] / total * 100) if total else 0
    bt = p.get('boss_wins', 0) + p.get('boss_losses', 0)
    bwr = round(p.get('boss_wins', 0) / bt * 100) if bt else 0
    rank = get_rank(p.get('wins', 0))
    skin = SKINS.get(p.get('skin'), {}).get('emoji', '—')
    armor = ARMORS.get(p.get('armor'), {}).get('name', 'none')
    weapon = WEAPONS.get(p.get('weapon'), {}).get('name', 'none')
    pet = PETS.get(p.get('pet'), {}).get('emoji', '—')
    clan = p.get('clan') or 'none'
    text = (
        f"👤 <b>PROFILE</b>\n━━━━━━━━━━━━━━━\n\n"
        f"<b>{dname(p)}</b> {skin}\n"
        f"🏅 Rank: <b>{rank}</b>\n"
        f"👥 Clan: <b>{clan}</b>\n\n"
        f"⚔️ <b>DUELS</b> · 🏆 {p['wins']} / 💀 {p['losses']} ({wr}%)\n"
        f"🐉 <b>BOSSES</b> · 🏆 {p.get('boss_wins',0)} / 💀 {p.get('boss_losses',0)} ({bwr}%)\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Diamonds: <b>{p.get('diamonds', 0)}</b>\n"
        f"❤️ Max HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>\n"
        f"🛡 Armor: <b>{armor}</b>\n"
        f"⚔️ Weapon: <b>{weapon}</b>\n"
        f"🐾 Pet: {pet}\n"
        f"🔥 Daily streak: <b>{p.get('daily_streak', 0)}</b>"
    )
    bot.send_message(cid, text, parse_mode='HTML')

def send_top(cid):
    stats = load_stats()
    if not stats:
        bot.send_message(cid, "🏆 Empty."); return
    season = load_season()
    ss = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = f"🏆 <b>SEASON {season['number']} — TOP</b>\n━━━━━━━━━━━━━━━\n\n"
    n = 0
    medals = ['🥇', '🥈', '🥉']
    for i, (uid, p) in enumerate(ss, 1):
        if p.get('wins', 0) == 0: continue
        n += 1
        med = medals[n-1] if n <= 3 else f'<b>{n}.</b>'
        rank = get_rank(p.get('wins', 0))
        text += f"{med} {pname(p)}\n     {rank} · ⚔️ {p['wins']} · 💀 {p['losses']}\n\n"
    if n == 0: text += "Nobody won yet."
    bot.send_message(cid, text, parse_mode='HTML')

def send_shop(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    text = (
        f"💎 <b>SHOP</b>\n━━━━━━━━━━━━━━━\n\n"
        f"💰 Diamonds: <b>{p.get('diamonds', 0)}</b>\n"
        f"❤️ Max HP: <b>{p.get('max_hp', PLAYER_MIN_HP)}</b>\n\n"
        f"<i>Choose category:</i>"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('❤️ HP', 'shop_hp', 'success'),
        btn('🎭 Skins', 'shop_skin', 'primary')
    )
    kb.add(
        btn('🛡 Armor', 'shop_armor', 'primary'),
        btn('⚔️ Weapons', 'shop_weapon', 'danger')
    )
    kb.add(btn('🐾 Pets', 'shop_pet', 'success'))
    kb.add(btn('◀️ Back', 'm_back', 'danger'))
    bot.send_message(cid, text, parse_mode='HTML', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('shop_'))
def shop_cb(call):
    cid = call.message.chat.id
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    cat = call.data.replace('shop_', '')
    if cat == 'hp':
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            btn('10 💎 → +20 HP', 'buy_10', 'success'),
            btn('25 💎 → +45 HP', 'buy_25', 'success'),
            btn('40 💎 → +75 HP', 'buy_40', 'success'),
            btn('◀️ Back', 'm_shop', 'danger')
        )
        bot.edit_message_text(
            f"❤️ <b>HP SHOP</b>\n━━━━━━━━━━━━━━━\n\n💎 {p.get('diamonds',0)} · ❤️ {p.get('max_hp',PLAYER_MIN_HP)}",
            chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    elif cat == 'skin':
        kb = types.InlineKeyboardMarkup(row_width=1)
        for sid, s in SKINS.items():
            owned = '✅ ' if p.get('skin') == sid else ''
            kb.add(btn(f"{owned}{s['emoji']} {s['name']} — {s['price']} 💎", f'buyskin_{sid}', 'primary'))
        kb.add(btn('◀️ Back', 'm_shop', 'danger'))
        bot.edit_message_text(f"🎭 <b>SKINS</b>\n━━━━━━━━━━━━━━━\n\n💰 {p.get('diamonds',0)}",
            chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    elif cat == 'armor':
        kb = types.InlineKeyboardMarkup(row_width=1)
        for aid, a in ARMORS.items():
            owned = '✅ ' if p.get('armor') == aid else ''
            kb.add(btn(f"{owned}{a['emoji']} {a['name']} — {a['price']} 💎", f'buyarmor_{aid}', 'primary'))
        kb.add(btn('◀️ Back', 'm_shop', 'danger'))
        bot.edit_message_text(f"🛡 <b>ARMOR</b>\n━━━━━━━━━━━━━━━\n\n💰 {p.get('diamonds',0)}",
            chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    elif cat == 'weapon':
        kb = types.InlineKeyboardMarkup(row_width=1)
        for wid, w in WEAPONS.items():
            owned = '✅ ' if p.get('weapon') == wid else ''
            kb.add(btn(f"{owned}{w['emoji']} {w['name']} — {w['price']} 💎", f'buyweapon_{wid}', 'danger'))
        kb.add(btn('◀️ Back', 'm_shop', 'danger'))
        bot.edit_message_text(f"⚔️ <b>WEAPONS</b>\n━━━━━━━━━━━━━━━\n\n💰 {p.get('diamonds',0)}",
            chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    elif cat == 'pet':
        kb = types.InlineKeyboardMarkup(row_width=1)
        for pid, pt in PETS.items():
            owned = '✅ ' if p.get('pet') == pid else ''
            kb.add(btn(f"{owned}{pt['emoji']} {pt['name']} — {pt['price']} 💎", f'buypet_{pid}', 'success'))
        kb.add(btn('◀️ Back', 'm_shop', 'danger'))
        bot.edit_message_text(f"🐾 <b>PETS</b>\n━━━━━━━━━━━━━━━\n\n💰 {p.get('diamonds',0)}",
            chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buyskin_'))
def buy_skin(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    sid = call.data.replace('buyskin_', '')
    s = SKINS.get(sid)
    if not s: bot.answer_callback_query(call.id, "Not found"); return
    if p.get('skin') == sid: bot.answer_callback_query(call.id, "✅ Owned"); return
    if p.get('diamonds', 0) < s['price']: bot.answer_callback_query(call.id, f"❌ Need {s['price']} 💎"); return
    p['diamonds'] -= s['price']; p['skin'] = sid; update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {s['name']}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith('buyarmor_'))
def buy_armor(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    aid = call.data.replace('buyarmor_', '')
    a = ARMORS.get(aid)
    if not a: bot.answer_callback_query(call.id, "Not found"); return
    if p.get('armor') == aid: bot.answer_callback_query(call.id, "✅ Owned"); return
    if p.get('diamonds', 0) < a['price']: bot.answer_callback_query(call.id, f"❌ Need {a['price']} 💎"); return
    p['diamonds'] -= a['price']; p['armor'] = aid; update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {a['name']}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith('buyweapon_'))
def buy_weapon(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    wid = call.data.replace('buyweapon_', '')
    w = WEAPONS.get(wid)
    if not w: bot.answer_callback_query(call.id, "Not found"); return
    if p.get('weapon') == wid: bot.answer_callback_query(call.id, "✅ Owned"); return
    if p.get('diamonds', 0) < w['price']: bot.answer_callback_query(call.id, f"❌ Need {w['price']} 💎"); return
    p['diamonds'] -= w['price']; p['weapon'] = wid; update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {w['name']}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith('buypet_'))
def buy_pet(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    pid = call.data.replace('buypet_', '')
    pt = PETS.get(pid)
    if not pt: bot.answer_callback_query(call.id, "Not found"); return
    if p.get('pet') == pid: bot.answer_callback_query(call.id, "✅ Owned"); return
    if p.get('diamonds', 0) < pt['price']: bot.answer_callback_query(call.id, f"❌ Need {pt['price']} 💎"); return
    p['diamonds'] -= pt['price']; p['pet'] = pid; update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ {pt['name']}!")

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_hp(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    costs = {'buy_10': (10, 20), 'buy_25': (25, 45), 'buy_40': (40, 75)}
    cost, hp = costs.get(call.data, (0, 0))
    if p.get('diamonds', 0) < cost:
        bot.answer_callback_query(call.id, f"❌ Need {cost} 💎"); return
    if p.get('max_hp', PLAYER_MIN_HP) + hp > PLAYER_MAX_HP:
        bot.answer_callback_query(call.id, "❌ Max HP"); return
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
            f"📅 <b>DAILY</b>\n━━━━━━━━━━━━━━━\n\n⏳ Already claimed.\n🔥 Streak: <b>{p.get('daily_streak', 0)}</b>\n\n⏰ Next in: <b>{fmt_h(left)}</b>",
            parse_mode='HTML'); return
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
        f"📅 <b>DAILY CLAIMED!</b>\n━━━━━━━━━━━━━━━\n\n💰 +<b>{reward}</b> 💎\n🔥 Streak: <b>{streak}</b> days\n💎 Total: <b>{p['diamonds']}</b>\n\n📌 Tomorrow: <b>{next_reward}</b> 💎",
        parse_mode='HTML')

def send_mine(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    now = int(time.time())
    last = p.get('last_mine', 0)
    diff = now - last
    if diff < MINE_COOLDOWN:
        left = MINE_COOLDOWN - diff
        bot.send_message(cid,
            f"⛏ <b>MINE</b>\n━━━━━━━━━━━━━━━\n\n⏳ Cooling down.\n\n⏰ Next in: <b>{fmt_h(left)}</b>",
            parse_mode='HTML'); return
    pet_bonus = PETS.get(p.get('pet'), {}).get('bonus_dia', 0)
    reward = random.randint(MINE_MIN, MINE_MAX) + pet_bonus
    p['diamonds'] = p.get('diamonds', 0) + reward
    p['last_mine'] = now
    update_player(uid, p)
    pet_txt = f"\n🐾 Pet bonus: +{pet_bonus} 💎" if pet_bonus else ""
    bot.send_message(cid,
        f"⛏ <b>MINED!</b>\n━━━━━━━━━━━━━━━\n\n💎 +<b>{reward}</b> diamonds{pet_txt}\n💰 Total: <b>{p['diamonds']}</b>\n\n⏰ Next in: <b>15 min</b>",
        parse_mode='HTML')

# ===== CLANS =====
def send_clans(cid, uid, fname, uname):
    p = get_player(uid, fname, uname)
    clans = load_clans()
    my = p.get('clan')
    text = f"👥 <b>CLANS</b>\n━━━━━━━━━━━━━━━\n\n"
    if my:
        c = clans.get(my, {})
        text += f"🏰 Your clan: <b>{c.get('name', my)}</b>\n👥 Members: <b>{len(c.get('members', []))}</b>\n\n"
    else:
        text += "You are not in a clan.\n\n"
    text += f"💰 Diamonds: <b>{p.get('diamonds', 0)}</b>\n📌 Create cost: <b>{CLAN_CREATE_COST} 💎</b>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    if not my:
        kb.add(btn(f'➕ Create ({CLAN_CREATE_COST} 💎)', 'clan_new', 'success'))
        kb.add(btn('📋 Join', 'clan_list', 'primary'))
    else:
        kb.add(btn('📋 Clan list', 'clan_list', 'primary'))
        kb.add(btn('🚪 Leave', 'clan_leave', 'danger'))
    kb.add(btn('◀️ Back', 'm_back', 'danger'))
    bot.send_message(cid, text, parse_mode='HTML', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('clan_'))
def clan_cb(call):
    cid = call.message.chat.id
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    d = call.data
    if d == 'clan_new':
        if p.get('clan'): bot.answer_callback_query(call.id, "❌ Already in clan"); return
        if p.get('diamonds', 0) < CLAN_CREATE_COST:
            bot.answer_callback_query(call.id, f"❌ Need {CLAN_CREATE_COST} 💎"); return
        p['diamonds'] -= CLAN_CREATE_COST
        update_player(uid, p)
        msg = bot.send_message(cid, "✏️ Send clan name (max 20 chars):")
        bot.register_next_step_handler(msg, clan_create_step, uid, call.from_user.first_name, call.from_user.username)
        bot.answer_callback_query(call.id); return
    if d == 'clan_list':
        clans = load_clans()
        if not clans:
            bot.answer_callback_query(call.id, "❌ No clans yet"); return
        text = "📋 <b>CLAN LIST</b>\n━━━━━━━━━━━━━━━\n\n"
        kb = types.InlineKeyboardMarkup(row_width=1)
        for cid2, c in clans.items():
            members = len(c.get('members', []))
            text += f"🏰 <b>{c.get('name')}</b> — {members} 👥\n"
            if not p.get('clan'):
                kb.add(btn(f'➕ Join {c.get("name")}', f'clan_join_{cid2}', 'success'))
        kb.add(btn('◀️ Back', 'm_clans', 'danger'))
        bot.edit_message_text(text, chat_id=cid, message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb)
        bot.answer_callback_query(call.id); return
    if d.startswith('clan_join_'):
        clan_id = d.replace('clan_join_', '')
        if p.get('clan'): bot.answer_callback_query(call.id, "❌ Already in clan"); return
        clans = load_clans()
        if clan_id not in clans:
            bot.answer_callback_query(call.id, "❌ Not found"); return
        members = clans[clan_id].get('members', [])
        if uid not in members:
            members.append(uid); clans[clan_id]['members'] = members; save_clans(clans)
        p['clan'] = clan_id; update_player(uid, p)
        bot.answer_callback_query(call.id, f"✅ Joined!")
        send_clans(cid, uid, call.from_user.first_name, call.from_user.username)
        return
    if d == 'clan_leave':
        if not p.get('clan'):
            bot.answer_callback_query(call.id, "❌ Not in clan"); return
        clan_id = p['clan']
        clans = load_clans()
        if clan_id in clans:
            members = clans[clan_id].get('members', [])
            if uid in members: members.remove(uid)
            clans[clan_id]['members'] = members
            if not members: del clans[clan_id]
            save_clans(clans)
        p['clan'] = None; update_player(uid, p)
        bot.answer_callback_query(call.id, "🚪 Left")
        send_clans(cid, uid, call.from_user.first_name, call.from_user.username)
        return
    bot.answer_callback_query(call.id)

def clan_create_step(msg, uid, fname, uname):
    name = (msg.text or '').strip()[:20]
    if not name:
        bot.send_message(msg.chat.id, "❌ Empty name."); return
    clans = load_clans()
    for cid, c in clans.items():
        if c.get('name', '').lower() == name.lower():
            bot.send_message(msg.chat.id, "❌ Name taken."); return
    clan_id = f'c_{int(time.time()*1000)}'
    clans[clan_id] = {'name': name, 'creator': uid, 'members': [uid], 'created': int(time.time())}
    save_clans(clans)
    p = get_player(uid, fname, uname)
    p['clan'] = clan_id
    update_player(uid, p)
    bot.send_message(msg.chat.id, f"🏰 <b>CLAN CREATED!</b>\n\nName: <b>{name}</b>", parse_mode='HTML')

# ===== DUEL 1v1 (multiple per chat) =====
@bot.message_handler(commands=['duel'])
def cmd_duel(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "⚔️ Groups only."); return
    if not m.reply_to_message:
        bot.send_message(m.chat.id, "⚔️ Reply to a player and send /duel"); return
    t = m.reply_to_message.from_user
    if t.id == m.from_user.id: bot.send_message(m.chat.id, "❌ Yourself."); return
    if t.is_bot: bot.send_message(m.chat.id, "❌ Not a bot."); return
    cid = m.chat.id
    cleanup_duels(cid)
    my_ex = find_duel_by_user(cid, str(m.from_user.id))
    if my_ex:
        bot.send_message(cid, "⚔️ You are already in a duel."); return
    target_ex = find_duel_by_user(cid, str(t.id))
    if target_ex:
        bot.send_message(cid, f"⚔️ {t.first_name} is already in a duel."); return
    now = int(time.time())
    duel = {
        'id': f'd_{int(time.time()*1000)}_{random.randint(100,999)}',
        'chat_id': cid, 'mode': '1v1',
        'p1_id': str(m.from_user.id), 'p1_name': m.from_user.first_name,
        'p2_id': str(t.id), 'p2_name': t.first_name,
        'p1_hp': DUEL_HP, 'p2_hp': DUEL_HP,
        'p1_aim': False, 'p2_aim': False,
        'turn': str(m.from_user.id), 'status': 'pending',
        'created': now, 'deadline': now + DUEL_TIMEOUT,
        'msg_id': None, 'last_action_msg': ''
    }
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('✅ Accept', f'd_yes_{duel["id"]}', 'success'),
        btn('❌ Decline', f'd_no_{duel["id"]}', 'danger')
    )
    sent = bot.send_message(cid, duel_pending_text(duel), parse_mode='HTML', reply_markup=kb)
    duel['msg_id'] = sent.message_id
    add_duel(cid, duel)
    threading.Timer(DUEL_TIMEOUT, duel_timeout, args=[cid, duel['id']]).start()

@bot.message_handler(commands=['duel_cancel'])
def cmd_duel_cancel(m):
    cid = m.chat.id
    uid = str(m.from_user.id)
    d = find_duel_by_user(cid, uid)
    if not d:
        bot.send_message(cid, "❌ You have no active duel."); return
    del_duel_by_id(cid, d['id'])
    try:
        bot.edit_message_text("❌ Duel cancelled.", chat_id=cid, message_id=d.get('msg_id'))
    except: pass
    bot.send_message(cid, "❌ Duel cancelled.")

def duel_pending_text(d):
    left = d.get('deadline', 0) - int(time.time())
    if d.get('mode') == '2v2':
        players = "\n".join([f"• {p['name']}" for p in d['players'].values()])
        return (
            f"⚔️ <b>DUEL 2v2 — LOBBY</b>\n━━━━━━━━━━━━━━━\n\n"
            f"👥 Players: <b>{len(d['team'])}/4</b>\n"
            f"⏱ Until start: <b>{fmt_t(left)}</b>\n\n"
            f"<b>Team:</b>\n{players}"
        )
    return (
        f"⚔️ <b>DUEL CHALLENGE!</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{d['p1_name']}</b> challenges <b>{d['p2_name']}</b>!\n\n"
        f"<i>{d['p2_name']}, accept?</i>\n\n"
        f"⏱ Left: <b>{fmt_t(left)}</b>"
    )

def duel_timeout(cid, duel_id):
    d = find_duel_by_id(cid, duel_id)
    if not d or d.get('status') not in ('pending',): return
    del_duel_by_id(cid, duel_id)
    try:
        bot.edit_message_text("⌛ Time out.", chat_id=cid, message_id=d.get('msg_id'))
    except: pass

def duel_kb_1v1(d):
    did = d['id']
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        btn('🔫 Shoot', f'd_shoot_{did}', 'danger'),
        btn('🎯 Aim', f'd_aim_{did}', 'success'),
        btn('🎭 Distract', f'd_dist_{did}', 'primary')
    )
    return kb

def duel_text(d):
    if d.get('mode') == '2v2': return duel_2v2_text(d)
    a1 = ' 🎯' if d['p1_aim'] else ''
    a2 = ' 🎯' if d['p2_aim'] else ''
    tn = d['p1_name'] if d['turn'] == d['p1_id'] else d['p2_name']
    t = (
        f"⚔️ <b>DUEL 1v1</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{d['p1_name']}</b>: ❤️ <b>{d['p1_hp']}</b> HP{a1}\n"
        f"🥷 <b>{d['p2_name']}</b>: ❤️ <b>{d['p2_hp']}</b> HP{a2}\n\n"
        f"🎯 Turn: <b>{tn}</b>"
    )
    if d.get('last_action_msg'): t += f"\n\n{d['last_action_msg']}"
    return t

def next_turn(d):
    d['turn'] = d['p2_id'] if d['turn'] == d['p1_id'] else d['p1_id']

@bot.callback_query_handler(func=lambda c: c.data.startswith('d_'))
def duel_cb(call):
    cid = call.message.chat.id
    uid = str(call.from_user.id)
    parts = call.data.split('_')
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "Bad data"); return
    action = parts[1]
    duel_id = '_'.join(parts[2:])
    d = find_duel_by_id(cid, duel_id)
    if not d:
        bot.answer_callback_query(call.id, "Duel not found"); return
    if d.get('mode') == '2v2':
        handle_2v2(call, cid, d, uid)
        return
    if action == 'yes':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌"); return
        d['status'] = 'active'; d['last_action_msg'] = ''
        update_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1(d))
        bot.answer_callback_query(call.id, "⚔️!"); return
    if action == 'no':
        if d.get('status') != 'pending': bot.answer_callback_query(call.id, "❌"); return
        if uid != d['p2_id']: bot.answer_callback_query(call.id, "❌"); return
        del_duel_by_id(cid, duel_id)
        sedit(cid, d['msg_id'], "❌ Declined.")
        bot.answer_callback_query(call.id, "Declined"); return
    if d.get('status') != 'active': bot.answer_callback_query(call.id, "❌"); return
    if uid != d['turn']: bot.answer_callback_query(call.id, "🎯 Not your turn"); return
    if action == 'aim':
        if uid == d['p1_id']: d['p1_aim'] = True
        else: d['p2_aim'] = True
        d['last_action_msg'] = "🎯 <i>Aiming!</i>"
        next_turn(d); update_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1(d))
        bot.answer_callback_query(call.id, "🎯"); return
    if action == 'dist':
        if uid == d['p1_id']:
            had = d['p2_aim']; d['p2_aim'] = False
        else:
            had = d['p1_aim']; d['p1_aim'] = False
        msg = random.choice(DISTRACT)
        msg += "\n💥 <b>Aim broken!</b>" if had else "\n🤷"
        d['last_action_msg'] = msg
        next_turn(d); update_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1(d))
        bot.answer_callback_query(call.id, "🎭"); return
    if action == 'shoot':
        if uid == d['p1_id']:
            aim = d['p1_aim']; d['p1_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p2_hp'] = max(0, d['p2_hp'] - dmg)
                msg = f"💥 Hit! <b>-{dmg}</b> HP"
            else: msg = "🌫 Miss!"
        else:
            aim = d['p2_aim']; d['p2_aim'] = False
            ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < ch:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                d['p1_hp'] = max(0, d['p1_hp'] - dmg)
                msg = f"💥 Hit! <b>-{dmg}</b> HP"
            else: msg = "🌫 Miss!"
        d['last_action_msg'] = msg
        if d['p1_hp'] <= 0 or d['p2_hp'] <= 0:
            wid = d['p1_id'] if d['p2_hp'] <= 0 else d['p2_id']
            lid = d['p2_id'] if wid == d['p1_id'] else d['p1_id']
            wn = d['p1_name'] if wid == d['p1_id'] else d['p2_name']
            add_duel_win(wid); add_duel_loss(lid)
            del_duel_by_id(cid, duel_id)
            wp = get_player(wid)
            sedit(cid, call.message.message_id,
                f"🏆 <b>DUEL ENDED</b>\n━━━━━━━━━━━━━━━\n\n{msg}\n\n🥇 Winner: <b>{wn}</b>\n🏅 Rank: {get_rank(wp.get('wins',0))}")
            bot.answer_callback_query(call.id, "🏆"); return
        next_turn(d); update_duel(cid, d)
        sedit(cid, d['msg_id'], duel_text(d), duel_kb_1v1(d))
        bot.answer_callback_query(call.id)

# ===== DUEL 2v2 =====
@bot.message_handler(commands=['duel2x2', 'duel2'])
def cmd_duel2x2(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "⚔️ Groups only."); return
    cid = m.chat.id
    cleanup_duels(cid)
    my_ex = find_duel_by_user(cid, str(m.from_user.id))
    if my_ex:
        bot.send_message(cid, "⚔️ You are already in a duel."); return
    now = int(time.time())
    duel_id = f'd_{int(time.time()*1000)}_{random.randint(100,999)}'
    d = {
        'id': duel_id, 'chat_id': cid, 'mode': '2v2',
        'host_id': str(m.from_user.id),
        'team': [], 'players': {}, 'team_a': [], 'team_b': [],
        'status': 'lobby', 'created': now, 'deadline': now + DUEL_TIMEOUT,
        'msg_id': None, 'turn_idx': 0, 'last_action_msg': ''
    }
    d['team'].append(str(m.from_user.id))
    d['players'][str(m.from_user.id)] = {'name': m.from_user.first_name, 'hp': DUEL_HP, 'aim': False, 'team': None}
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('🎭 Join', f'd2_join_{duel_id}', 'success'),
        btn('🚪 Leave', f'd2_leave_{duel_id}', 'danger')
    )
    kb.add(btn('▶️ Start', f'd2_start_{duel_id}', 'primary'))
    sent = bot.send_message(cid, duel_pending_text(d), parse_mode='HTML', reply_markup=kb)
    d['msg_id'] = sent.message_id
    add_duel(cid, d)
    threading.Timer(DUEL_TIMEOUT, duel_timeout, args=[cid, duel_id]).start()

def duel_2v2_text(d):
    if d.get('status') == 'lobby': return duel_pending_text(d)
    a_text = "\n".join([f"• <b>{d['players'][u]['name']}</b>: {'💀' if d['players'][u]['hp'] <= 0 else '❤️ '+str(d['players'][u]['hp'])}" for u in d['team_a']])
    b_text = "\n".join([f"• <b>{d['players'][u]['name']}</b>: {'💀' if d['players'][u]['hp'] <= 0 else '❤️ '+str(d['players'][u]['hp'])}" for u in d['team_b']])
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    tn = '—'
    if alive: tn = d['players'][alive[d['turn_idx'] % len(alive)]]['name']
    t = (
        f"⚔️ <b>DUEL 2v2</b>\n━━━━━━━━━━━━━━━\n\n"
        f"🔵 <b>Team A</b>\n{a_text}\n\n"
        f"🔴 <b>Team B</b>\n{b_text}\n\n"
        f"🎯 Turn: <b>{tn}</b>"
    )
    if d.get('last_action_msg'): t += f"\n\n{d['last_action_msg']}"
    return t

def duel_2v2_attack_kb(d, uid):
    enemy_team = d['team_b'] if uid in d['team_a'] else d['team_a']
    alive = [u for u in enemy_team if d['players'][u]['hp'] > 0]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for u in alive:
        kb.add(btn(f"🔫 {d['players'][u]['name']}", f'd2_atk_{u}_{d["id"]}', 'danger'))
    kb.add(btn('🎯 Aim', f'd2_aim_{d["id"]}', 'success'))
    kb.add(btn('🎭 Distract', f'd2_dist_{d["id"]}', 'primary'))
    return kb

def start_2v2(cid, d):
    ids = d['team'][:]
    random.shuffle(ids)
    d['team_a'] = ids[:2]; d['team_b'] = ids[2:4]
    for u in d['team_a']: d['players'][u]['team'] = 'A'
    for u in d['team_b']: d['players'][u]['team'] = 'B'
    d['status'] = 'active'; d['turn_idx'] = 0
    d['last_action_msg'] = '⚔️ Battle started!'
    update_duel(cid, d)
    sedit(cid, d['msg_id'], duel_2v2_text(d), None)
    send_2v2_turn(cid, d)

def send_2v2_turn(cid, d):
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    if not alive: finish_2v2(cid, d); return
    uid = alive[d['turn_idx'] % len(alive)]
    kb = duel_2v2_attack_kb(d, uid)
    try: bot.send_message(cid, duel_2v2_text(d), parse_mode='HTML', reply_markup=kb)
    except: pass

def handle_2v2(call, cid, d, uid):
    parts = call.data.split('_')
    action = parts[1]
    duel_id = '_'.join(parts[2:]) if not call.data.startswith('d2_atk') else d['id']
    if action == 'join':
        if d['status'] != 'lobby': bot.answer_callback_query(call.id, "❌"); return
        if uid in d['team']: bot.answer_callback_query(call.id, "✅"); return
        if len(d['team']) >= 4: bot.answer_callback_query(call.id, "❌ 4 max"); return
        d['team'].append(uid)
        d['players'][uid] = {'name': call.from_user.first_name, 'hp': DUEL_HP, 'aim': False, 'team': None}
        update_duel(cid, d)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            btn('🎭 Join', f'd2_join_{d["id"]}', 'success'),
            btn('🚪 Leave', f'd2_leave_{d["id"]}', 'danger')
        )
        kb.add(btn('▶️ Start', f'd2_start_{d["id"]}', 'primary'))
        sedit(cid, d['msg_id'], duel_pending_text(d), kb)
        bot.answer_callback_query(call.id, "⚔️"); return
    if action == 'leave':
        if d['status'] != 'lobby': bot.answer_callback_query(call.id, "❌"); return
        if uid not in d['team']: bot.answer_callback_query(call.id, "❌"); return
        d['team'].remove(uid); d['players'].pop(uid, None)
        if not d['team']:
            del_duel_by_id(cid, d['id'])
            sedit(cid, d['msg_id'], "❌ Closed.")
            bot.answer_callback_query(call.id, "🚪"); return
        if uid == d['host_id']: d['host_id'] = d['team'][0]
        update_duel(cid, d)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            btn('🎭 Join', f'd2_join_{d["id"]}', 'success'),
            btn('🚪 Leave', f'd2_leave_{d["id"]}', 'danger')
        )
        kb.add(btn('▶️ Start', f'd2_start_{d["id"]}', 'primary'))
        sedit(cid, d['msg_id'], duel_pending_text(d), kb)
        bot.answer_callback_query(call.id, "🚪"); return
    if action == 'start':
        if uid != d['host_id'] and not is_admin_id(uid):
            bot.answer_callback_query(call.id, "❌ Host only"); return
        if len(d['team']) < 4:
            bot.answer_callback_query(call.id, "❌ Need 4"); return
        bot.answer_callback_query(call.id, "⚔️!"); start_2v2(cid, d); return
    if d['status'] != 'active': bot.answer_callback_query(call.id, "❌"); return
    alive = [u for u in d['team'] if d['players'][u]['hp'] > 0]
    if not alive: bot.answer_callback_query(call.id, "❌"); return
    if uid != alive[d['turn_idx'] % len(alive)]:
        bot.answer_callback_query(call.id, "🎯 Not your turn"); return
    p = d['players'][uid]
    if action == 'aim':
        p['aim'] = True
        d['last_action_msg'] = f"🎯 <b>{p['name']}</b> aiming!"
        d['turn_idx'] += 1; update_duel(cid, d)
        send_2v2_turn(cid, d); bot.answer_callback_query(call.id, "🎯"); return
    if action == 'dist':
        enemy_team = d['team_b'] if p['team'] == 'A' else d['team_a']
        enemies_aim = [u for u in enemy_team if d['players'][u]['hp'] > 0 and d['players'][u].get('aim')]
        if enemies_aim:
            target = random.choice(enemies_aim)
            d['players'][target]['aim'] = False
            msg = f"🎭 <b>{p['name']}</b> broke <b>{d['players'][target]['name']}</b>'s aim!"
        else:
            msg = f"🎭 <b>{p['name']}</b> distracted!"
        d['last_action_msg'] = msg
        d['turn_idx'] += 1; update_duel(cid, d)
        send_2v2_turn(cid, d); bot.answer_callback_query(call.id, "🎭"); return
    if action == 'atk':
        target = parts[2] if len(parts) > 2 else None
        if not target or target not in d['players'] or d['players'][target]['hp'] <= 0:
            bot.answer_callback_query(call.id, "❌"); return
        if d['players'][target]['team'] == p['team']:
            bot.answer_callback_query(call.id, "❌ Ally"); return
        aim = p.get('aim', False)
        ch = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
        if random.random() < ch:
            dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
            d['players'][target]['hp'] = max(0, d['players'][target]['hp'] - dmg)
            msg = f"💥 <b>{p['name']}</b> → <b>{d['players'][target]['name']}</b> for <b>{dmg}</b>!"
        else:
            msg = f"🌫 <b>{p['name']}</b> missed!"
        p['aim'] = False
        d['last_action_msg'] = msg
        d['turn_idx'] += 1; update_duel(cid, d)
        a_alive = [u for u in d['team_a'] if d['players'][u]['hp'] > 0]
        b_alive = [u for u in d['team_b'] if d['players'][u]['hp'] > 0]
        if not a_alive or not b_alive:
            finish_2v2(cid, d); return
        send_2v2_turn(cid, d); bot.answer_callback_query(call.id, f"💥 {dmg}"); return

def finish_2v2(cid, d):
    a_alive = [u for u in d['team_a'] if d['players'][u]['hp'] > 0]
    b_alive = [u for u in d['team_b'] if d['players'][u]['hp'] > 0]
    if a_alive and not b_alive: winners, losers = d['team_a'], d['team_b']
    elif b_alive and not a_alive: winners, losers = d['team_b'], d['team_a']
    else: winners, losers = [], []
    for u in winners: add_duel_win(u)
    for u in losers: add_duel_loss(u)
    wnames = ", ".join([d['players'][u]['name'] for u in winners])
    text = f"🏆 <b>2v2 ENDED!</b>\n\n🥇 Team wins: <b>{wnames}</b>"
    try: bot.send_message(cid, text, parse_mode='HTML')
    except: pass
    del_duel_by_id(cid, d['id'])

# ===== BOSSES =====
@bot.message_handler(commands=['boss', 'boss1', 'boss2', 'boss3', 'boss4', 'boss5', 'boss6', 'boss7'])
def cmd_boss(m):
    if m.chat.type == 'private':
        bot.send_message(m.chat.id, "🐉 Groups only."); return
    cmd = m.text.split()[0].replace('/', '')
    if '@' in cmd: cmd = cmd.split('@')[0]
    if cmd == 'boss':
        t = "🐉 <b>CHOOSE BOSS</b>\n━━━━━━━━━━━━━━━\n\n"
        for n, b in BOSSES.items():
            t += f"{n}️⃣ {b['emoji']} <b>{b['name']}</b>\n     ❤️ {b['hp']} HP · 💎 +{b['diamonds']}\n\n"
        t += "<i>Send:</i> <code>/boss1</code> ... <code>/boss7</code>"
        bot.send_message(m.chat.id, t, parse_mode='HTML'); return
    try: bn = int(cmd.replace('boss', ''))
    except: bn = None
    if not bn or bn not in BOSSES:
        bot.send_message(m.chat.id, "❌ /boss1 ... /boss7"); return
    b = BOSSES[bn]
    g = get_boss(m.chat.id)
    if g and g.get('status') not in ('finished',):
        bot.send_message(m.chat.id, "🐉 Already running."); return
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
        btn('⚔️ Join', 'b_join', 'success'),
        btn('🚪 Leave', 'b_leave', 'danger')
    )
    kb.add(
        btn('▶️ Start', 'b_start', 'primary'),
        btn('❌ Cancel', 'b_cancel', 'danger')
    )
    if is_admin:
        kb.add(btn('➕ Extend', 'b_ext', 'primary'))
    return kb

def boss_lobby_text(g):
    pl = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p.get('max_hp', PLAYER_MIN_HP)} HP" for p in g['players'].values()])
    left = g.get('deadline',0) - int(time.time())
    return (
        f"🐉 <b>BOSS: {g['boss_name']}</b>\n━━━━━━━━━━━━━━━\n\n"
        f"❤️ Boss HP: <b>{g['boss_max_hp']}</b>\n"
        f"💎 Reward: <b>+{g['boss_diamonds']} diamonds</b>\n\n"
        f"👥 Players: <b>{len(g['players'])}/{BOSS_MAX_PLAYERS}</b>\n"
        f"📌 Min: <b>{BOSS_MIN_PLAYERS}</b>\n"
        f"⏱ Until start: <b>{fmt_t(left)}</b>\n\n"
        f"<b>Team:</b>\n{pl}"
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
        try: bot.send_message(cid, "⏱ Too few. Cancelled.", parse_mode='HTML')
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
            bot.answer_callback_query(call.id, f"❌ Max {BOSS_MAX_PLAYERS}"); return
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
            del_boss(cid); sedit(cid, mid, "❌ Closed.")
            bot.answer_callback_query(call.id, "🚪"); return
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "🚪"); return
    if call.data == 'b_start':
        if uid != g['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Host"); return
        if len(g['players']) < BOSS_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Min {BOSS_MIN_PLAYERS}"); return
        bot.answer_callback_query(call.id, "🐉!"); start_boss_fight(cid); return
    if call.data == 'b_cancel':
        if uid != g['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌"); return
        del_boss(cid); sedit(cid, mid, "❌ Cancelled.")
        bot.answer_callback_query(call.id, "Cancelled"); return
    if call.data == 'b_ext':
        if not is_admin: bot.answer_callback_query(call.id, "❌"); return
        g['deadline'] = int(time.time()) + BOSS_LOBBY_TIME
        save_boss_g(cid, g); sedit(cid, mid, boss_lobby_text(g), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "➕")

def boss_fight_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        btn('🔫 Attack', 'bf_atk', 'danger'),
        btn('🏏 Bat', 'bf_bat', 'primary'),
        btn('🎯 Aim', 'bf_aim', 'success')
    )
    return kb

def alive_sorted(g):
    a = [(u,p) for u,p in g['players'].items() if p['alive']]
    a.sort(key=lambda x: x[1].get('order',0))
    return a

def boss_fight_text(g):
    ap = alive_sorted(g)
    pt = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p['hp']}/{p['max_hp']} HP{' 🎯' if p.get('aim') else ''}" for _, p in ap])
    if not pt: pt = "💀 All dead"
    tn = '?'
    if ap: tn = ap[g.get('turn_idx',0) % len(ap)][1]['name']
    pct = int((g['boss_hp'] / g['boss_max_hp']) * 100) if g['boss_max_hp'] else 0
    bar = '█' * (pct//10) + '░' * (10 - pct//10)
    t = (
        f"🐉 <b>{g['boss_name']}</b>\n━━━━━━━━━━━━━━━\n"
        f"❤️ HP: <b>{g['boss_hp']}/{g['boss_max_hp']}</b>\n{bar} {pct}%\n\n"
        f"<b>TEAM:</b>\n{pt}\n\n🎯 Turn: <b>{tn}</b>"
    )
    if g.get('last_msg'): t += f"\n\n{g['last_msg']}"
    return t

def start_boss_fight(cid):
    g = get_boss(cid)
    if not g: return
    g['status'] = 'fight'; g['turn_idx'] = 0; g['last_msg'] = '⚔️ Battle started!'
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
    armor = ARMORS.get(g['players'][tu].get('armor'), {})
    if armor: dmg = int(dmg * (1 - armor.get('defense', 0) / 100))
    t['hp'] = max(0, t['hp'] - dmg)
    msg = f"👹 Boss hits <b>{t['name']}</b> for <b>{dmg}</b>!"
    if t['hp'] <= 0: t['alive'] = False; msg += f"\n💀 <b>{t['name']}</b> died!"
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
    if not ap: bot.answer_callback_query(call.id, "Error"); return
    if uid != ap[g['turn_idx'] % len(ap)][0]:
        bot.answer_callback_query(call.id, "🎯 Not your turn"); return
    p = g['players'][uid]
    if call.data == 'bf_aim':
        p['aim'] = True
        g['last_msg'] = f"🎯 <b>{p['name']}</b> aiming!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, "🎯"); return
    if call.data == 'bf_atk':
        dmg = random.randint(BOSS_ATK_MIN, BOSS_ATK_MAX)
        weapon = WEAPONS.get(p.get('weapon'), {})
        if weapon: dmg += weapon.get('damage', 0)
        if p.get('aim'): dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
        g['boss_hp'] = max(0, g['boss_hp'] - dmg)
        p['dmg_done'] = p.get('dmg_done',0) + dmg
        g['last_msg'] = f"🔫 <b>{p['name']}</b> deals <b>{dmg}</b>!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, f"🔫 {dmg}"); return
    if call.data == 'bf_bat':
        if random.random() < BOSS_BAT_CHANCE:
            dmg = random.randint(BOSS_BAT_MIN, BOSS_BAT_MAX)
            weapon = WEAPONS.get(p.get('weapon'), {})
            if weapon: dmg += weapon.get('damage', 0)
            if p.get('aim'): dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
            g['boss_hp'] = max(0, g['boss_hp'] - dmg)
            p['dmg_done'] = p.get('dmg_done',0) + dmg
            g['last_msg'] = f"🏏 <b>{p['name']}</b> deals <b>{dmg}</b>!"
        else:
            if p.get('aim'): p['aim'] = False
            g['last_msg'] = f"🏏 <b>{p['name']}</b> missed!"
        next_boss_turn(g); save_boss_g(cid, g)
        if check_boss_end(cid, g): return
        sedit(cid, g.get('fight_msg_id'), boss_fight_text(g), boss_fight_kb())
        bot.answer_callback_query(call.id, "🏏"); return

def check_boss_end(cid, g):
    if g['boss_hp'] <= 0:
        g['status'] = 'finished'; save_boss_g(cid, g)
        dia = g['boss_diamonds']
        msg = f"🏆 <b>BOSS DEFEATED!</b>\n━━━━━━━━━━━━━━━\n🐉 <b>{g['boss_name']}</b>\n\n<b>Rewards:</b>\n"
        for u, p in g['players'].items():
            add_boss_win(u, dia)
            msg += f"• {p['name']} — <b>{p.get('dmg_done',0)}</b> dmg, <b>+{dia} 💎</b>\n"
        sedit(cid, g.get('fight_msg_id'), msg); del_boss(cid); return True
    if not [u for u,p in g['players'].items() if p['alive']]:
        g['status'] = 'finished'; save_boss_g(cid, g)
        for u in g['players']: add_boss_loss(u)
        sedit(cid, g.get('fight_msg_id'), "💀 <b>ALL DEAD!</b>"); del_boss(cid); return True
    return False

# ===== MENU =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('m_'))
def menu_cb(call):
    u = call.from_user; uid = u.id; cid = call.message.chat.id
    if call.data == 'm_prof': send_profile(cid, uid, u.first_name, u.username)
    elif call.data == 'm_top': send_top(cid)
    elif call.data == 'm_shop': send_shop(cid, uid, u.first_name, u.username)
    elif call.data == 'm_daily': send_daily(cid, uid, u.first_name, u.username)
    elif call.data == 'm_mine': send_mine(cid, uid, u.first_name, u.username)
    elif call.data == 'm_season': send_season(cid)
    elif call.data == 'm_clans': send_clans(cid, uid, u.first_name, u.username)
    elif call.data == 'm_duel': bot.send_message(cid, "⚔️ /duel (1v1) or /duel2x2 (2v2)\n❌ /duel_cancel — cancel")
    elif call.data == 'm_boss': bot.send_message(cid, "🐉 /boss1 ... /boss7")
    elif call.data == 'm_help': cmd_help(call.message)
    elif call.data == 'm_back':
        bot.send_message(cid, "🎭 Menu:", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start','🎭 Menu'),
            types.BotCommand('help','💬 Help'),
            types.BotCommand('profile','👤 Profile'),
            types.BotCommand('top','🏆 Top'),
            types.BotCommand('daily','📅 Daily'),
            types.BotCommand('mine','⛏ Mine'),
            types.BotCommand('duel','⚔️ Duel 1v1'),
            types.BotCommand('duel_cancel','❌ Cancel duel'),
            types.BotCommand('duel2x2','⚔️ Duel 2v2'),
            types.BotCommand('shop','💎 Shop'),
            types.BotCommand('season','🏅 Season'),
            types.BotCommand('clans','👥 Clans'),
        ])
    except: pass

load_season()
set_commands()
print('Bot started')
bot.infinity_polling()
