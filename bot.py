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
MAFIA_FILE = 'mafia.json'
BOSS_FILE = 'boss.json'

ADMIN_IDS = [8907438590]

DUEL_HP = 100
DUEL_SHOOT_MIN = 25
DUEL_SHOOT_MAX = 45
DUEL_AIM_BONUS = 0.9
DUEL_NOAIM_CHANCE = 0.6
DUEL_ACCEPT_TIMEOUT = 300

MAFIA_MIN_PLAYERS = 4
MAFIA_MAX_PLAYERS = 50
MAFIA_NIGHT_TIME = 60
MAFIA_VOTE_TIME = 45
MAFIA_LOBBY_TIME = 230
MAFIA_TIMER_UPDATE = 15

BOSS_MAX_HP = 2000
BOSS_DMG_MIN = 50
BOSS_DMG_MAX = 150
BOSS_PLAYER_MIN_HP = 250
BOSS_PLAYER_MAX_HP = 2000
BOSS_HP_PER_EGG = 5
BOSS_REWARD_EGGS = 2
BOSS_MIN_PLAYERS = 2
BOSS_MAX_PLAYERS = 4
BOSS_LOBBY_TIME = 300
BOSS_TIMER_UPDATE = 15
BOSS_ATK_MIN = 40
BOSS_ATK_MAX = 90
BOSS_BAT_MIN = 80
BOSS_BAT_MAX = 150
BOSS_BAT_HIT_CHANCE = 0.7
BOSS_AIM_BONUS = 1.3

TOKEN = '8883984473:AAHh0Hd9CDcbWqgvZdJShXqXvnn6S3YniHw'

DISTRACT_MESSAGES = [
    "🎭 Сделал отвлекающий маневр, сбил прицел соперника!",
    "💨 Резко ушёл в сторону — соперник потерял цель!",
    "🪞 Бросил зеркальце — прицел сбит!",
    "🌫 Выпустил дымовую шашку — соперник ничего не видит!",
    "🎪 Сделал сальто — враг растерялся!",
    "🦅 Взлетел на секунду — прицел сорван!",
    "🎯 Бросил песок в глаза — соперник промахнётся!",
    "🌀 Резкий кульбит — соперник целится в пустоту!",
    "🎺 Громко крикнул — враг дёрнулся!",
    "🌟 Ослепил вспышкой — прицел сбит!",
]

BOSS_NAMES = [
    "🐉 Древний Дракон", "👹 Тёмный Лорд", "🦁 Кровавый Лев",
    "🐺 Голодный Волк", "🦂 Пустынный Скорпион", "👺 Демон Огня",
    "🧟 Король Зомби",
]

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stats(): return load_json(STATS_FILE, {})
def save_stats(d): save_json(STATS_FILE, d)
def load_duels(): return load_json(DUELS_FILE, {})
def save_duels(d): save_json(DUELS_FILE, d)
def load_mafia(): return load_json(MAFIA_FILE, {})
def save_mafia(d): save_json(MAFIA_FILE, d)
def load_boss(): return load_json(BOSS_FILE, {})
def save_boss(d): save_json(BOSS_FILE, d)

def is_admin_id(user_id):
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def get_player(user_id, first_name='Аноним', username=''):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'wins': 0, 'losses': 0,
            'mafia_wins': 0, 'mafia_losses': 0,
            'duels_played': 0, 'mafia_played': 0,
            'boss_wins': 0, 'boss_losses': 0,
            'eggs': 0,
            'max_hp': BOSS_PLAYER_MIN_HP
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        defaults = {
            'wins':0,'losses':0,'mafia_wins':0,'mafia_losses':0,
            'duels_played':0,'mafia_played':0,'boss_wins':0,'boss_losses':0,
            'eggs':0,'max_hp':BOSS_PLAYER_MIN_HP
        }
        for f, v in defaults.items():
            if f not in stats[key]: stats[key][f] = v
    save_stats(stats)
    return stats[key]

def update_player(user_id, data):
    stats = load_stats()
    stats[str(user_id)] = data
    save_stats(stats)

def add_duel_win(user_id):
    p = get_player(user_id); p['wins'] += 1; p['duels_played'] += 1; update_player(user_id, p)

def add_duel_loss(user_id):
    p = get_player(user_id); p['losses'] += 1; p['duels_played'] += 1; update_player(user_id, p)

def add_mafia_win(user_id):
    p = get_player(user_id); p['mafia_wins'] += 1; p['mafia_played'] += 1; update_player(user_id, p)

def add_mafia_loss(user_id):
    p = get_player(user_id); p['mafia_losses'] += 1; p['mafia_played'] += 1; update_player(user_id, p)

def add_boss_win(user_id, eggs=0):
    p = get_player(user_id); p['boss_wins'] += 1; p['eggs'] = p.get('eggs',0) + eggs; update_player(user_id, p)

def add_boss_loss(user_id):
    p = get_player(user_id); p['boss_losses'] += 1; update_player(user_id, p)

def get_duel(chat_id): return load_duels().get(str(chat_id))
def save_duel(chat_id, duel): d = load_duels(); d[str(chat_id)] = duel; save_duels(d)
def del_duel(chat_id):
    d = load_duels()
    if str(chat_id) in d: del d[str(chat_id)]; save_duels(d)

def get_mafia(chat_id): return load_mafia().get(str(chat_id))
def save_mafia_game(chat_id, game): m = load_mafia(); m[str(chat_id)] = game; save_mafia(m)
def del_mafia(chat_id):
    m = load_mafia()
    if str(chat_id) in m: del m[str(chat_id)]; save_mafia(m)

def get_boss(chat_id): return load_boss().get(str(chat_id))
def save_boss_game(chat_id, game): b = load_boss(); b[str(chat_id)] = game; save_boss(b)
def del_boss(chat_id):
    b = load_boss()
    if str(chat_id) in b: del b[str(chat_id)]; save_boss(b)

def assign_roles(players):
    ids = list(players.keys()); count = len(ids)
    random.shuffle(ids)
    if count <= 5: mafia_count = 1
    elif count <= 8: mafia_count = 2
    elif count <= 12: mafia_count = 3
    elif count <= 20: mafia_count = 4
    else: mafia_count = max(1, count // 5)
    roles = ['mafia'] * mafia_count
    if count >= 4: roles.append('doctor')
    if count >= 4: roles.append('sheriff')
    while len(roles) < count: roles.append('civilian')
    random.shuffle(roles)
    for i, uid in enumerate(ids):
        players[uid]['role'] = roles[i]
    return players

def role_ru(role):
    return {'mafia':'🔪 Мафия','doctor':'💉 Доктор','sheriff':'🔍 Шериф','civilian':'👤 Мирный житель'}.get(role, role)

def fmt_time(sec):
    sec = max(0, int(sec))
    return f"{sec//60}:{sec%60:02d}"

def display_name(p):
    if not p: return 'Аноним'
    uname = (p.get('username') or '').strip()
    if uname: return '@' + uname
    fname = (p.get('first_name') or '').strip()
    if fname and fname != 'Аноним': return fname
    return 'Аноним'

bot = telebot.TeleBot(TOKEN)

@bot.middleware_handler(update_types=['message'])
def update_user_info(bot_instance, message):
    try:
        if message.from_user:
            uid = message.from_user.id
            uname = message.from_user.username or ''
            fname = message.from_user.first_name or 'Аноним'
            stats = load_stats()
            key = str(uid)
            if key in stats:
                changed = False
                if stats[key].get('username') != uname:
                    stats[key]['username'] = uname; changed = True
                if stats[key].get('first_name') != fname:
                    stats[key]['first_name'] = fname; changed = True
                if changed: save_stats(stats)
            else:
                stats[key] = {
                    'first_name': fname, 'username': uname,
                    'wins': 0, 'losses': 0,
                    'mafia_wins': 0, 'mafia_losses': 0,
                    'duels_played': 0, 'mafia_played': 0,
                    'boss_wins': 0, 'boss_losses': 0,
                    'eggs': 0, 'max_hp': BOSS_PLAYER_MIN_HP
                }
                save_stats(stats)
    except: pass

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Darkgram Bot is running')

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='👤 Профиль', callback_data='menu_profile'),
        types.InlineKeyboardButton(text='🏆 Топ', callback_data='menu_top')
    )
    kb.add(
        types.InlineKeyboardButton(text='⚔️ Дуэль', callback_data='menu_duel'),
        types.InlineKeyboardButton(text='🎭 Мафия', callback_data='menu_mafia')
    )
    kb.add(
        types.InlineKeyboardButton(text='🐉 Босс', callback_data='menu_boss'),
        types.InlineKeyboardButton(text='🥚 Яйца', callback_data='menu_eggs')
    )
    kb.add(types.InlineKeyboardButton(text='💬 Помощь', callback_data='menu_help'))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(message):
    uid = message.from_user.id
    get_player(uid, message.from_user.first_name, message.from_user.username)
    text = (
        f"🎭 <b>DARKGRAM</b> 🎭\n\n"
        f"Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"⚔️ Дуэли 1 на 1\n"
        f"🎭 Мафия 4-50 игроков\n"
        f"🐉 Босс 2-4 игрока\n"
        f"🥚 Яйца → HP\n"
        f"🏆 Топ по победам\n\n"
        f"Выбирай:"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n\n"
        f"⚔️ <b>Дуэли:</b> /duel в ответ на сообщение\n"
        f"🎭 <b>Мафия:</b> /mafia в группе (4-50)\n"
        f"🐉 <b>Босс:</b> /boss в группе (2-4)\n\n"
        f"🏏 <b>Бой с боссом:</b>\n"
        f"🔫 Атака — 40-90\n"
        f"🏏 Бита — 80-150 (70% точность)\n"
        f"🎯 Прицел — следующий удар x1.3 и точно попадёт\n"
        f"👹 Босс бьёт 50-150 раз в раунд\n\n"
        f"🥚 <b>Яйца:</b> 2 за победу, 1 яйцо = +5 HP"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['eggs'])
def cmd_eggs(message):
    uid = message.from_user.id
    get_player(uid, message.from_user.first_name, message.from_user.username)
    bot.send_message(message.chat.id, eggs_menu_text(uid), parse_mode='HTML', reply_markup=eggs_menu_kb())

@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    uid = message.from_user.id
    p = get_player(uid, message.from_user.first_name, message.from_user.username)
    total = p['wins'] + p['losses']
    wr = round(p['wins'] / total * 100) if total else 0
    mafia_total = p['mafia_wins'] + p['mafia_losses']
    mafia_wr = round(p['mafia_wins'] / mafia_total * 100) if mafia_total else 0
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n\n"
        f"<b>{display_name(p)}</b>\n\n"
        f"⚔️ <b>Дуэли:</b> 🏆 {p['wins']} / 💀 {p['losses']} ({wr}%)\n"
        f"🎭 <b>Мафия:</b> 🏆 {p['mafia_wins']} / 💀 {p['mafia_losses']} ({mafia_wr}%)\n"
        f"🐉 <b>Босс:</b> 🏆 {p.get('boss_wins',0)} / 💀 {p.get('boss_losses',0)}\n\n"
        f"🥚 Яйца: <b>{p.get('eggs',0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', BOSS_PLAYER_MIN_HP)}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['top'])
def cmd_top(message):
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "🏆 Пока пусто."); return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n\n"
    placed = 0
    for i, (uid, p) in enumerate(sorted_stats, 1):
        if p.get('wins', 0) == 0: continue
        placed += 1
        medal = '🥇' if placed==1 else '🥈' if placed==2 else '🥉' if placed==3 else f'{placed}.'
        text += f"{medal} {display_name(p)} — {p['wins']} ⚔️, {p['losses']} 💀\n"
    if placed == 0: text += "Пока никто не побеждал."
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['post'])
def cmd_post(message):
    if not is_admin_id(message.from_user.id): return
    text = message.text.replace('/post','').strip()
    if not text:
        bot.send_message(message.chat.id, "📢 Использование: /post Текст"); return
    stats = load_stats(); sent = 0
    for uid in list(stats.keys()):
        try:
            bot.send_message(int(uid), "📢 " + text, parse_mode='HTML')
            sent += 1; time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"📢 Разослано: {sent} из {len(stats)}")

# ===== БОСС =====
def boss_lobby_kb(is_admin=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='⚔️ Присоединиться', callback_data='boss_join'),
        types.InlineKeyboardButton(text='🚪 Выйти', callback_data='boss_leave')
    )
    kb.add(
        types.InlineKeyboardButton(text='▶️ Начать бой', callback_data='boss_start'),
        types.InlineKeyboardButton(text='❌ Отменить', callback_data='boss_cancel')
    )
    if is_admin:
        kb.add(types.InlineKeyboardButton(text='➕ Продлить 5:00', callback_data='boss_extend'))
    return kb

def boss_lobby_text(game):
    players_list = "\n".join([f"• {p['name']} — {p.get('max_hp', BOSS_PLAYER_MIN_HP)} HP" for p in game['players'].values()])
    left = game.get('deadline', 0) - int(time.time())
    return (
        f"🐉 <b>БОСС: {game['boss_name']}</b>\n\n"
        f"👹 HP босса: <b>{BOSS_MAX_HP}</b>\n"
        f"👥 {len(game['players'])}/{BOSS_MAX_PLAYERS} (мин. {BOSS_MIN_PLAYERS})\n"
        f"⏱ До старта: <b>{fmt_time(left)}</b>\n\n"
        f"<b>Команда:</b>\n{players_list}"
    )

@bot.message_handler(commands=['boss'])
def cmd_boss(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "🐉 Босс только в группах."); return
    game = get_boss(message.chat.id)
    if game and game.get('status') not in ('finished',):
        bot.send_message(message.chat.id, "🐉 Уже идёт бой."); return
    now = int(time.time())
    boss_name = random.choice(BOSS_NAMES)
    p = get_player(message.from_user.id, message.from_user.first_name, message.from_user.username)
    game = {
        'chat_id': message.chat.id,
        'host_id': str(message.from_user.id),
        'boss_name': boss_name,
        'boss_hp': BOSS_MAX_HP,
        'players': {}, 'order': [], 'turn_idx': 0,
        'status': 'lobby',
        'deadline': now + BOSS_LOBBY_TIME,
        'lobby_msg_id': None, 'fight_msg_id': None,
        'last_msg': '', 'log': []
    }
    game['players'][str(message.from_user.id)] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
        'max_hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
        'alive': True, 'aim': False, 'dmg_done': 0
    }
    game['order'] = [str(message.from_user.id)]
    save_boss_game(message.chat.id, game)
    sent = bot.send_message(
        message.chat.id, boss_lobby_text(game), parse_mode='HTML',
        reply_markup=boss_lobby_kb(is_admin_id(message.from_user.id))
    )
    game['lobby_msg_id'] = sent.message_id
    save_boss_game(message.chat.id, game)
    threading.Timer(BOSS_LOBBY_TIME, boss_lobby_timeout, args=[message.chat.id]).start()
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[message.chat.id]).start()

def boss_lobby_tick(chat_id):
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby': return
    left = game.get('deadline', 0) - int(time.time())
    if left <= 0: return
    try:
        bot.edit_message_text(
            boss_lobby_text(game), chat_id=chat_id,
            message_id=game['lobby_msg_id'], parse_mode='HTML',
            reply_markup=boss_lobby_kb(is_admin_id(game['host_id']))
        )
    except: pass
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[chat_id]).start()

def boss_lobby_timeout(chat_id):
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby': return
    count = len(game['players'])
    if count >= BOSS_MIN_PLAYERS:
        try: bot.send_message(chat_id, f"⏱ Автостарт. Игроков: {count}", parse_mode='HTML')
        except: pass
        start_boss_fight(chat_id)
    else:
        try: bot.send_message(chat_id, f"⏱ Мало игроков ({count}). Отмена.", parse_mode='HTML')
        except: pass
        del_boss(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('boss_join') or c.data.startswith('boss_leave') or c.data.startswith('boss_start') or c.data.startswith('boss_cancel') or c.data.startswith('boss_extend'))
def boss_lobby_cb(call):
    chat_id = call.message.chat.id
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌ Закрыто"); return
    uid = str(call.from_user.id)
    is_admin = is_admin_id(uid)

    if call.data == 'boss_join':
        if uid in game['players']:
            bot.answer_callback_query(call.id, "✅ Уже в команде"); return
        if len(game['players']) >= BOSS_MAX_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Макс {BOSS_MAX_PLAYERS}"); return
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        game['players'][uid] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username or '',
            'hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
            'max_hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
            'alive': True, 'aim': False, 'dmg_done': 0
        }
        game['order'].append(uid)
        save_boss_game(chat_id, game)
        try:
            bot.edit_message_text(
                boss_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=boss_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "⚔️ В команде!")
        return

    if call.data == 'boss_leave':
        if uid not in game['players']:
            bot.answer_callback_query(call.id, "❌ Не в команде"); return
        was_host = (uid == game['host_id'])
        del game['players'][uid]
        if uid in game['order']: game['order'].remove(uid)
        if was_host and game['players']:
            new_host_id = list(game['players'].keys())[0]
            game['host_id'] = new_host_id
            try: bot.send_message(chat_id, f"👑 Новый хост: <b>{game['players'][new_host_id]['name']}</b>", parse_mode='HTML')
            except: pass
        elif not game['players']:
            del_boss(chat_id)
            try: bot.edit_message_text("❌ Закрыто.", chat_id=chat_id, message_id=call.message.message_id)
            except: pass
            bot.answer_callback_query(call.id, "🚪 Закрыто"); return
        save_boss_game(chat_id, game)
        try:
            bot.edit_message_text(
                boss_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=boss_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "🚪 Вышел")
        return

    if call.data == 'boss_start':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост"); return
        if len(game['players']) < BOSS_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Минимум {BOSS_MIN_PLAYERS}"); return
        bot.answer_callback_query(call.id, "🐉 Начинаем!")
        start_boss_fight(chat_id)
        return

    if call.data == 'boss_cancel':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост"); return
        del_boss(chat_id)
        try: bot.edit_message_text("❌ Отменено.", chat_id=chat_id, message_id=call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, "Отменено")
        return

    if call.data == 'boss_extend':
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ Только админ"); return
        game['deadline'] = int(time.time()) + BOSS_LOBBY_TIME
        save_boss_game(chat_id, game)
        try:
            bot.edit_message_text(
                boss_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=boss_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "➕ Продлено 5:00")
        return

def boss_fight_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(text='🔫 Атака', callback_data='boss_fight_atk'),
        types.InlineKeyboardButton(text='🏏 Бита', callback_data='boss_fight_bat'),
        types.InlineKeyboardButton(text='🎯 Прицел', callback_data='boss_fight_aim')
    )
    return kb

def boss_fight_text(game):
    alive_players = [(uid, p) for uid, p in game['players'].items() if p['alive']]
    players_text = "\n".join([f"• {p['name']} — {p['hp']}/{p['max_hp']} HP{' 🎯' if p.get('aim') else ''}" for _, p in alive_players])
    if not players_text: players_text = "💀 Все погибли"
    turn_name = '?'
    if game['order']:
        idx = game.get('turn_idx', 0) % len(game['order'])
        if idx < len(game['order']):
            turn_uid = game['order'][idx]
            if turn_uid in game['players']:
                turn_name = game['players'][turn_uid]['name']
    text = (
        f"🐉 <b>{game['boss_name']}</b>\n"
        f"❤️ HP босса: <b>{game['boss_hp']}/{BOSS_MAX_HP}</b>\n\n"
        f"<b>Команда:</b>\n{players_text}\n\n"
        f"🎯 Ход: <b>{turn_name}</b>"
    )
    if game.get('last_msg'): text += f"\n\n{game['last_msg']}"
    return text

def start_boss_fight(chat_id):
    game = get_boss(chat_id)
    if not game: return
    game['status'] = 'fight'
    game['turn_idx'] = 0
    game['last_msg'] = ''
    for uid in game['players']:
        game['players'][uid]['aim'] = False
    game['order'] = [uid for uid in game['order'] if game['players'][uid]['alive']]
    save_boss_game(chat_id, game)
    bot.send_message(
        chat_id,
        f"🐉 <b>БОЙ С БОССОМ НАЧАЛСЯ!</b>\n\n"
        f"👹 <b>{game['boss_name']}</b> — {game['boss_hp']} HP\n"
        f"👥 Игроков: {len(game['order'])}\n\n"
        f"Кнопки: 🔫 Атака / 🏏 Бита / 🎯 Прицел",
        parse_mode='HTML'
    )
    send_boss_turn(chat_id)

def send_boss_turn(chat_id):
    game = get_boss(chat_id)
    if not game or game['status'] != 'fight': return
    if not game['order']: return
    idx = game['turn_idx'] % len(game['order'])
    current_uid = game['order'][idx]
    if not game['players'][current_uid]['alive']:
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        check_boss_end(chat_id, game)
        return
    try:
        msg = bot.send_message(
            chat_id, boss_fight_text(game), parse_mode='HTML',
            reply_markup=boss_fight_kb()
        )
        game['fight_msg_id'] = msg.message_id
        save_boss_game(chat_id, game)
    except: pass

def next_boss_turn(game):
    if not game['order']: return
    game['turn_idx'] += 1
    if game['turn_idx'] % len(game['order']) == 0 and game['turn_idx'] > 0:
        boss_attack(game)

def boss_attack(game):
    alive = [(uid, p) for uid, p in game['players'].items() if p['alive']]
    if not alive: return
    target_uid, target = random.choice(alive)
    dmg = random.randint(BOSS_DMG_MIN, BOSS_DMG_MAX)
    target['hp'] = max(0, target['hp'] - dmg)
    msg = f"👹 Босс атакует <b>{target['name']}</b> на {dmg} HP!"
    if target['hp'] <= 0:
        target['alive'] = False
        msg += f"\n💀 <b>{target['name']}</b> погиб!"
    game['last_msg'] = msg

@bot.callback_query_handler(func=lambda c: c.data.startswith('boss_fight_'))
def boss_fight_cb(call):
    chat_id = call.message.chat.id
    game = get_boss(chat_id)
    if not game or game['status'] != 'fight':
        bot.answer_callback_query(call.id, "❌ Бой не идёт"); return
    uid = str(call.from_user.id)
    if uid not in game['players'] or not game['players'][uid]['alive']:
        bot.answer_callback_query(call.id, "💀 Не можешь ходить"); return
    if not game['order']:
        bot.answer_callback_query(call.id, "Ошибка"); return
    idx = game['turn_idx'] % len(game['order'])
    if uid != game['order'][idx]:
        bot.answer_callback_query(call.id, "🎯 Не твой ход"); return
    p = game['players'][uid]

    if call.data == 'boss_fight_aim':
        p['aim'] = True
        game['last_msg'] = f"🎯 <b>{p['name']}</b> прицелился!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        check_boss_end(chat_id, game)
        if game.get('status') != 'fight': return
        send_boss_turn(chat_id)
        bot.answer_callback_query(call.id, "🎯 Прицел!")
        return

    if call.data == 'boss_fight_atk':
        dmg = random.randint(BOSS_ATK_MIN, BOSS_ATK_MAX)
        if p.get('aim'):
            dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
        game['boss_hp'] = max(0, game['boss_hp'] - dmg)
        p['dmg_done'] = p.get('dmg_done', 0) + dmg
        game['last_msg'] = f"🔫 <b>{p['name']}</b> бьёт на {dmg} урона!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        check_boss_end(chat_id, game)
        if game.get('status') != 'fight': return
        send_boss_turn(chat_id)
        bot.answer_callback_query(call.id, f"🔫 {dmg}")
        return

    if call.data == 'boss_fight_bat':
        if random.random() < BOSS_BAT_HIT_CHANCE:
            dmg = random.randint(BOSS_BAT_MIN, BOSS_BAT_MAX)
            if p.get('aim'):
                dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
            game['boss_hp'] = max(0, game['boss_hp'] - dmg)
            p['dmg_done'] = p.get('dmg_done', 0) + dmg
            game['last_msg'] = f"🏏 <b>{p['name']}</b> бьёт битой на {dmg}!"
        else:
            if p.get('aim'): p['aim'] = False
            game['last_msg'] = f"🏏 <b>{p['name']}</b> промахнулся битой!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        check_boss_end(chat_id, game)
        if game.get('status') != 'fight': return
        send_boss_turn(chat_id)
        bot.answer_callback_query(call.id, "🏏")
        return

def check_boss_end(chat_id, game):
    if game['boss_hp'] <= 0:
        game['status'] = 'finished'
        save_boss_game(chat_id, game)
        msg = "🏆 <b>БОСС ПОВЕРЖЕН!</b>\n\n"
        for uid, p in game['players'].items():
            add_boss_win(uid, BOSS_REWARD_EGGS)
            msg += f"• {p['name']} — {p.get('dmg_done',0)} урона, +{BOSS_REWARD_EGGS} 🥚\n"
        bot.send_message(chat_id, msg, parse_mode='HTML')
        del_boss(chat_id)
        return
    alive = [uid for uid, p in game['players'].items() if p['alive']]
    if not alive:
        game['status'] = 'finished'
        save_boss_game(chat_id, game)
        for uid in game['players']:
            add_boss_loss(uid)
        bot.send_message(chat_id, "💀 <b>ВСЕ ПОГИБЛИ!</b>\n\nБосс выжил.", parse_mode='HTML')
        del_boss(chat_id)

# ===== ЯЙЦА =====
def eggs_menu_text(uid):
    p = get_player(uid)
    return (
        f"🥚 <b>МАГАЗИН ЯИЦ</b>\n\n"
        f"У тебя: <b>{p.get('eggs', 0)}</b> яиц\n"
        f"Макс. HP: <b>{p.get('max_hp', BOSS_PLAYER_MIN_HP)}</b>\n\n"
        f"1 🥚 = <b>+{BOSS_HP_PER_EGG} HP</b>\n"
        f"Максимум HP: {BOSS_PLAYER_MAX_HP}"
    )

def eggs_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text=f'🥚 +{BOSS_HP_PER_EGG} HP (1 яйцо)', callback_data='eggs_buy_1'),
        types.InlineKeyboardButton(text=f'🥚 +{BOSS_HP_PER_EGG*5} HP (5 яиц)', callback_data='eggs_buy_5'),
        types.InlineKeyboardButton(text='◀️ Назад', callback_data='menu_back')
    )
    return kb

@bot.callback_query_handler(func=lambda c: c.data.startswith('eggs_buy_'))
def eggs_buy_cb(call):
    uid = str(call.from_user.id)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    count = 5 if call.data == 'eggs_buy_5' else 1
    if p.get('eggs', 0) < count:
        bot.answer_callback_query(call.id, "❌ Мало яиц"); return
    add_hp = BOSS_HP_PER_EGG * count
    if p.get('max_hp', BOSS_PLAYER_MIN_HP) + add_hp > BOSS_PLAYER_MAX_HP:
        bot.answer_callback_query(call.id, "❌ Максимум HP"); return
    p['eggs'] -= count
    p['max_hp'] = p.get('max_hp', BOSS_PLAYER_MIN_HP) + add_hp
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{add_hp} HP")
    try:
        bot.edit_message_text(
            eggs_menu_text(uid), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=eggs_menu_kb()
        )
    except: pass

# ===== ДУЭЛИ =====
@bot.message_handler(commands=['duel'])
def cmd_duel(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "⚔️ Только в группах."); return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "⚔️ Ответь на сообщение игрока и напиши /duel"); return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        bot.send_message(message.chat.id, "❌ Себе нельзя."); return
    if target.is_bot:
        bot.send_message(message.chat.id, "❌ С ботом нельзя."); return
    existing = get_duel(message.chat.id)
    if existing and existing.get('status') in ('pending','active'):
        bot.send_message(message.chat.id, "⚔️ Уже идёт дуэль."); return
    now = int(time.time())
    duel = {
        'chat_id': message.chat.id,
        'p1_id': str(message.from_user.id),
        'p1_name': message.from_user.first_name,
        'p2_id': str(target.id),
        'p2_name': target.first_name,
        'p1_hp': DUEL_HP, 'p2_hp': DUEL_HP,
        'p1_aim': False, 'p2_aim': False,
        'turn': str(message.from_user.id),
        'status': 'pending',
        'created': now,
        'deadline': now + DUEL_ACCEPT_TIMEOUT,
        'msg_id': None,
        'last_action_msg': ''
    }
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='✅ Принять', callback_data='duel_accept'),
        types.InlineKeyboardButton(text='❌ Отклонить', callback_data='duel_decline')
    )
    sent = bot.send_message(
        message.chat.id, build_duel_pending_text(duel),
        parse_mode='HTML', reply_markup=kb
    )
    duel['msg_id'] = sent.message_id
    save_duel(message.chat.id, duel)
    threading.Timer(DUEL_ACCEPT_TIMEOUT, duel_timeout, args=[message.chat.id]).start()

def build_duel_pending_text(duel):
    left = duel['deadline'] - int(time.time())
    return (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"🥷 <b>{duel['p1_name']}</b> вызывает <b>{duel['p2_name']}</b>!\n\n"
        f"{duel['p2_name']}, принимаешь?\n\n"
        f"⏱ Осталось: <b>{fmt_time(left)}</b>"
    )

def duel_timeout(chat_id):
    duel = get_duel(chat_id)
    if not duel or duel.get('status') != 'pending': return
    try:
        bot.edit_message_text(
            "⌛ Время вышло. Вызов отменён.",
            chat_id=chat_id, message_id=duel['msg_id'], parse_mode='HTML'
        )
    except: pass
    del_duel(chat_id)

def duel_kb(duel):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(text='🔫 Выстрел', callback_data='duel_shoot'),
        types.InlineKeyboardButton(text='🎯 Прицел', callback_data='duel_aim'),
        types.InlineKeyboardButton(text='🎭 Отвлечь', callback_data='duel_distract')
    )
    return kb

def duel_status_text(duel):
    p1_aim = ' 🎯' if duel['p1_aim'] else ''
    p2_aim = ' 🎯' if duel['p2_aim'] else ''
    turn_name = duel['p1_name'] if duel['turn']==duel['p1_id'] else duel['p2_name']
    text = (
        f"⚔️ <b>ДУЭЛЬ</b>\n\n"
        f"🥷 <b>{duel['p1_name']}</b>: {duel['p1_hp']} HP{p1_aim}\n"
        f"🥷 <b>{duel['p2_name']}</b>: {duel['p2_hp']} HP{p2_aim}\n\n"
        f"🎯 Ход: <b>{turn_name}</b>"
    )
    if duel.get('last_action_msg'): text += f"\n\n{duel['last_action_msg']}"
    return text

def next_turn(duel):
    duel['turn'] = duel['p2_id'] if duel['turn'] == duel['p1_id'] else duel['p1_id']

@bot.callback_query_handler(func=lambda c: c.data.startswith('duel_'))
def duel_cb(call):
    chat_id = call.message.chat.id
    duel = get_duel(chat_id)
    if not duel:
        bot.answer_callback_query(call.id, "Не найдена"); return
    uid = str(call.from_user.id)

    if call.data == 'duel_accept':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Неактуально"); return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов"); return
        duel['status'] = 'active'; duel['last_action_msg'] = ''
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel), chat_id=chat_id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "⚔️ Началась!")
        return

    if call.data == 'duel_decline':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Неактуально"); return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов"); return
        del_duel(chat_id)
        bot.edit_message_text("❌ Отклонено.", chat_id=chat_id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Отклонено")
        return

    if duel.get('status') != 'active':
        bot.answer_callback_query(call.id, "Не идёт"); return
    if uid != duel['turn']:
        bot.answer_callback_query(call.id, "🎯 Не твой ход"); return

    if call.data == 'duel_aim':
        if uid == duel['p1_id']: duel['p1_aim'] = True
        else: duel['p2_aim'] = True
        duel['last_action_msg'] = "🎯 Игрок прицелился!"
        next_turn(duel); save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel), chat_id=chat_id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "🎯")
        return

    if call.data == 'duel_distract':
        if uid == duel['p1_id']:
            had = duel['p2_aim']; duel['p2_aim'] = False
        else:
            had = duel['p1_aim']; duel['p1_aim'] = False
        msg = random.choice(DISTRACT_MESSAGES)
        msg += "\n💥 Прицел сбит!" if had else "\n🤷 Прицела не было."
        duel['last_action_msg'] = msg
        next_turn(duel); save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel), chat_id=chat_id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "🎭")
        return

    if call.data == 'duel_shoot':
        if uid == duel['p1_id']:
            aim = duel['p1_aim']; duel['p1_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p2_hp'] = max(0, duel['p2_hp'] - dmg)
                msg = f"💥 Попадание! -{dmg} HP"
            else: msg = "🌫 Промах!"
        else:
            aim = duel['p2_aim']; duel['p2_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p1_hp'] = max(0, duel['p1_hp'] - dmg)
                msg = f"💥 Попадание! -{dmg} HP"
            else: msg = "🌫 Промах!"
        duel['last_action_msg'] = msg
        if duel['p1_hp'] <= 0 or duel['p2_hp'] <= 0:
            winner_id = duel['p1_id'] if duel['p2_hp'] <= 0 else duel['p2_id']
            loser_id = duel['p2_id'] if winner_id == duel['p1_id'] else duel['p1_id']
            winner_name = duel['p1_name'] if winner_id == duel['p1_id'] else duel['p2_name']
            add_duel_win(winner_id); add_duel_loss(loser_id)
            del_duel(chat_id)
            bot.edit_message_text(
                f"🏆 <b>ДУЭЛЬ ОКОНЧЕНА</b>\n\n{msg}\n\n🥇 Победил: <b>{winner_name}</b>",
                chat_id=chat_id, message_id=call.message.message_id, parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "🏆")
            return
        next_turn(duel); save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel), chat_id=chat_id,
            message_id=call.message.message_id, parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id)

# ===== МАФИЯ =====
def mafia_lobby_kb(is_admin=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='🎭 Присоединиться', callback_data='mafia_join'),
        types.InlineKeyboardButton(text='🚪 Выйти', callback_data='mafia_leave')
    )
    kb.add(
        types.InlineKeyboardButton(text='▶️ Начать', callback_data='mafia_start'),
        types.InlineKeyboardButton(text='❌ Отменить', callback_data='mafia_cancel')
    )
    if is_admin:
        kb.add(types.InlineKeyboardButton(text='➕ Продлить 3:50', callback_data='mafia_extend'))
    return kb

def mafia_lobby_text(game):
    players_list = "\n".join([f"• {p['name']}" for p in game['players'].values()])
    left = game.get('deadline', 0) - int(time.time())
    return (
        f"🎭 <b>МАФИЯ — СБОР</b>\n\n"
        f"👑 Хост: <b>{game['host_name']}</b>\n"
        f"👥 {len(game['players'])}/{MAFIA_MAX_PLAYERS} (мин. {MAFIA_MIN_PLAYERS})\n"
        f"⏱ До закрытия: <b>{fmt_time(left)}</b>\n\n"
        f"<b>Игроки:</b>\n{players_list}"
    )

@bot.message_handler(commands=['mafia'])
def cmd_mafia(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "🎭 Только в группах."); return
    game = get_mafia(message.chat.id)
    if game and game.get('status') not in ('finished',):
        bot.send_message(message.chat.id, "🎭 Уже идёт."); return
    now = int(time.time())
    game = {
        'chat_id': message.chat.id,
        'host_id': str(message.from_user.id),
        'host_name': message.from_user.first_name,
        'players': {}, 'status': 'lobby', 'day': 0,
        'night_actions': {}, 'votes': {},
        'vote_msg_id': None, 'lobby_msg_id': None,
        'deadline': now + MAFIA_LOBBY_TIME, 'log': []
    }
    game['players'][str(message.from_user.id)] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'alive': True, 'role': None
    }
    save_mafia_game(message.chat.id, game)
    sent = bot.send_message(
        message.chat.id, mafia_lobby_text(game),
        parse_mode='HTML', reply_markup=mafia_lobby_kb(is_admin_id(message.from_user.id))
    )
    game['lobby_msg_id'] = sent.message_id
    save_mafia_game(message.chat.id, game)
    threading.Timer(MAFIA_LOBBY_TIME, mafia_lobby_timeout, args=[message.chat.id]).start()
    threading.Timer(MAFIA_TIMER_UPDATE, mafia_lobby_tick, args=[message.chat.id]).start()

def mafia_lobby_tick(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'lobby': return
    left = game.get('deadline', 0) - int(time.time())
    if left <= 0: return
    try:
        bot.edit_message_text(
            mafia_lobby_text(game), chat_id=chat_id,
            message_id=game['lobby_msg_id'], parse_mode='HTML',
            reply_markup=mafia_lobby_kb(is_admin_id(game['host_id']))
        )
    except: pass
    threading.Timer(MAFIA_TIMER_UPDATE, mafia_lobby_tick, args=[chat_id]).start()

def mafia_lobby_timeout(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'lobby': return
    count = len(game['players'])
    if count >= MAFIA_MIN_PLAYERS:
        try: bot.send_message(chat_id, f"⏱ Автостарт. Игроков: {count}", parse_mode='HTML')
        except: pass
        start_mafia_game(chat_id)
    else:
        try: bot.send_message(chat_id, f"⏱ Мало игроков ({count}). Закрыто.", parse_mode='HTML')
        except: pass
        del_mafia(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('mafia_join') or c.data.startswith('mafia_leave') or c.data.startswith('mafia_start') or c.data.startswith('mafia_cancel') or c.data.startswith('mafia_extend'))
def mafia_lobby_cb(call):
    chat_id = call.message.chat.id
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌ Закрыто"); return
    uid = str(call.from_user.id)
    is_admin = is_admin_id(uid)

    if call.data == 'mafia_join':
        if uid in game['players']:
            bot.answer_callback_query(call.id, "✅ Уже в игре"); return
        if len(game['players']) >= MAFIA_MAX_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Макс {MAFIA_MAX_PLAYERS}"); return
        game['players'][uid] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username or '',
            'alive': True, 'role': None
        }
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "🎭 В игре!")
        return

    if call.data == 'mafia_leave':
        if uid not in game['players']:
            bot.answer_callback_query(call.id, "❌ Не в игре"); return
        was_host = (uid == game['host_id'])
        del game['players'][uid]
        if was_host and game['players']:
            new_host_id = list(game['players'].keys())[0]
            game['host_id'] = new_host_id
            game['host_name'] = game['players'][new_host_id]['name']
        elif not game['players']:
            del_mafia(chat_id)
            try: bot.edit_message_text("❌ Закрыто.", chat_id=chat_id, message_id=call.message.message_id)
            except: pass
            bot.answer_callback_query(call.id, "🚪"); return
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "🚪 Вышел")
        return

    if call.data == 'mafia_start':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост"); return
        if len(game['players']) < MAFIA_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Минимум {MAFIA_MIN_PLAYERS}"); return
        bot.answer_callback_query(call.id, "🎭 Начинаем!")
        start_mafia_game(chat_id)
        return

    if call.data == 'mafia_cancel':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост"); return
        del_mafia(chat_id)
        try: bot.edit_message_text("❌ Отменено.", chat_id=chat_id, message_id=call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, "Отменено")
        return

    if call.data == 'mafia_extend':
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ Только админ"); return
        game['deadline'] = int(time.time()) + MAFIA_LOBBY_TIME
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game), chat_id=chat_id,
                message_id=call.message.message_id, parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "➕ Продлено 3:50")

def start_mafia_game(chat_id):
    game = get_mafia(chat_id)
    if not game: return
    assign_roles(game['players'])
    game['status'] = 'roles'
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"🎭 <b>ИГРА НАЧАЛАСЬ!</b>\n\n👥 Игроков: {len(game['players'])}\n💌 Роли в личке.", parse_mode='HTML')
    for uid, p in game['players'].items():
        try:
            role = p['role']
            role_text = f"🎭 <b>ТВОЯ РОЛЬ: {role_ru(role)}</b>\n\n"
            if role == 'mafia': role_text += "🌙 Ночью выбирай жертву.\n☀️ Днём притворяйся мирным! 🤫"
            elif role == 'doctor': role_text += "🌙 Ночью лечи игроков.\nЕсли мафия выбрала того же — выживет! 💉"
            elif role == 'sheriff': role_text += "🌙 Ночью проверяй игроков. 🔍"
            else: role_text += "🌙 Ночью спишь.\n☀️ Днём голосуй против мафии 🗳️"
            bot.send_message(int(uid), role_text, parse_mode='HTML')
        except: pass
    threading.Timer(3.0, start_night, args=[chat_id]).start()

def start_night(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') == 'finished': return
    game['status'] = 'night'
    game['day'] += 1
    game['night_actions'] = {}
    game['votes'] = {}
    game['vote_msg_id'] = None
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"🌙 <b>НОЧЬ {game['day']}</b>\n\nВсе засыпают... 💤\n⏱ 60 секунд", parse_mode='HTML')
    for uid, p in game['players'].items():
        if not p['alive']: continue
        role = p['role']
        try:
            if role == 'mafia':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive'] or tp['role'] == 'mafia': continue
                    kb.add(types.InlineKeyboardButton(text=f"🔪 {tp['name']}", callback_data=f'mafia_kill_{tuid}'))
                if kb.keyboard: bot.send_message(int(uid), "🔪 Выбери жертву:", reply_markup=kb)
            elif role == 'doctor':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    kb.add(types.InlineKeyboardButton(text=f"💉 {tp['name']}", callback_data=f'mafia_heal_{tuid}'))
                if kb.keyboard: bot.send_message(int(uid), "💉 Кого лечить?", reply_markup=kb)
            elif role == 'sheriff':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive'] or tuid == uid: continue
                    kb.add(types.InlineKeyboardButton(text=f"🔍 {tp['name']}", callback_data=f'mafia_check_{tuid}'))
                if kb.keyboard: bot.send_message(int(uid), "🔍 Кого проверить?", reply_markup=kb)
        except: pass
    threading.Timer(MAFIA_NIGHT_TIME, end_night, args=[chat_id]).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('mafia_kill_') or c.data.startswith('mafia_heal_') or c.data.startswith('mafia_check_'))
def mafia_night_cb(call):
    try:
        parts = call.data.split('_')
        action = parts[1]; target_id = parts[2]
        uid = str(call.from_user.id)
        game = get_mafia(call.message.chat.id)
        if not game or game.get('status') != 'night':
            bot.answer_callback_query(call.id, "🌙 Не ночь"); return
        p = game['players'].get(uid)
        if not p or p.get('role') != action_to_role(action):
            bot.answer_callback_query(call.id, "❌ Не твоя роль"); return
        if not p.get('alive'):
            bot.answer_callback_query(call.id, "💀 Мёртв"); return
        if target_id not in game['players'] or not game['players'][target_id].get('alive'):
            bot.answer_callback_query(call.id, "❌ Цель мертва"); return
        game['night_actions'][action] = target_id
        save_mafia_game(call.message.chat.id, game)
        target_name = game['players'][target_id]['name']
        if action == 'kill':
            bot.edit_message_text(f"🔪 Ты выбрал убить: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "🔪")
        elif action == 'heal':
            bot.edit_message_text(f"💉 Ты лечишь: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "💉")
        elif action == 'check':
            is_mafia = (game['players'][target_id].get('role') == 'mafia')
            bot.edit_message_text(
                f"🔍 Проверка: {target_name}\n\n{'🔪 МАФИЯ!' if is_mafia else '👤 не мафия'}",
                chat_id=call.message.chat.id, message_id=call.message.message_id
            )
            bot.answer_callback_query(call.id, "🔍")
    except: bot.answer_callback_query(call.id, "Ошибка")

def action_to_role(action):
    return {'kill':'mafia','heal':'doctor','check':'sheriff'}.get(action)

def end_night(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'night': return
    kill_target = game['night_actions'].get('kill')
    heal_target = game['night_actions'].get('heal')
    killed_name = None
    if kill_target and kill_target != heal_target:
        if kill_target in game['players'] and game['players'][kill_target]['alive']:
            game['players'][kill_target]['alive'] = False
            killed_name = game['players'][kill_target]['name']
    save_mafia_game(chat_id, game)
    text = f"☀️ <b>УТРО {game['day']}</b>\n\n"
    text += f"💀 Убит: <b>{killed_name}</b>" if killed_name else "☀️ Никто не погиб! 💉"
    bot.send_message(chat_id, text, parse_mode='HTML')

    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        bot.send_message(chat_id, "🏆 <b>МИРНЫЕ ПОБЕДИЛИ!</b>", parse_mode='HTML')
        del_mafia(chat_id); return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        bot.send_message(chat_id, "🔪 <b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id); return
    threading.Timer(2.0, start_vote, args=[chat_id]).start()

def build_vote_text(game):
    votes = game.get('votes', {})
    counts = {}
    for t in votes.values(): counts[t] = counts.get(t, 0) + 1
    text = "🗳️ <b>ГОЛОСОВАНИЕ</b>\n\n⏱ 45 сек\n\n<b>Голоса:</b>\n"
    for uid, p in game['players'].items():
        if not p['alive']: continue
        cnt = counts.get(uid, 0)
        text += f"• {p['name']} — {cnt} {'█'*cnt if cnt else '·'}\n"
    text += f"\nВсего: {len(votes)}"
    return text

def start_vote(chat_id):
    game = get_mafia(chat_id)
    if not game: return
    game['status'] = 'vote'
    game['votes'] = {}
    save_mafia_game(chat_id, game)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid, p in game['players'].items():
        if p['alive']:
            kb.add(types.InlineKeyboardButton(text=f"🗳️ {p['name']}", callback_data=f'vote_{uid}'))
    if not kb.keyboard:
        bot.send_message(chat_id, "🤷 Все мертвы.")
        del_mafia(chat_id); return
    msg = bot.send_message(chat_id, build_vote_text(game), reply_markup=kb, parse_mode='HTML')
    game['vote_msg_id'] = msg.message_id
    save_mafia_game(chat_id, game)
    threading.Timer(MAFIA_VOTE_TIME, end_vote, args=[chat_id]).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('vote_'))
def vote_cb(call):
    game = get_mafia(call.message.chat.id)
    if not game or game.get('status') != 'vote':
        bot.answer_callback_query(call.id, "🗳️ Закрыто"); return
    uid = str(call.from_user.id)
    if not game['players'].get(uid, {}).get('alive'):
        bot.answer_callback_query(call.id, "💀 Мёртв"); return
    target = call.data.replace('vote_','')
    if target not in game['players'] or not game['players'][target].get('alive'):
        bot.answer_callback_query(call.id, "❌ Недоступно"); return
    game['votes'][uid] = target
    save_mafia_game(call.message.chat.id, game)
    try:
        kb = types.InlineKeyboardMarkup(row_width=2)
        for tuid, tp in game['players'].items():
            if tp['alive']:
                kb.add(types.InlineKeyboardButton(text=f"🗳️ {tp['name']}", callback_data=f'vote_{tuid}'))
        bot.edit_message_text(
            build_vote_text(game), chat_id=call.message.chat.id,
            message_id=call.message.message_id, parse_mode='HTML', reply_markup=kb
        )
    except: pass
    bot.answer_callback_query(call.id, f"🗳️ {game['players'][target]['name']}")

def end_vote(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'vote': return
    votes = game['votes']
    if not votes:
        bot.send_message(chat_id, "🤷 Никто не голосовал. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start(); return
    counts = {}
    for t in votes.values(): counts[t] = counts.get(t, 0) + 1
    max_v = max(counts.values())
    top = [t for t, c in counts.items() if c == max_v]
    if len(top) > 1:
        bot.send_message(chat_id, "🤝 Ничья. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start(); return
    target = top[0]
    target_name = game['players'][target]['name']
    target_role = game['players'][target]['role']
    game['players'][target]['alive'] = False
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"⚖️ <b>КАЗНЁН: {target_name}</b>\n🎭 {role_ru(target_role)}", parse_mode='HTML')
    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        bot.send_message(chat_id, "🏆 <b>МИРНЫЕ ПОБЕДИЛИ!</b>", parse_mode='HTML')
        del_mafia(chat_id); return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        bot.send_message(chat_id, "🔪 <b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id); return
    threading.Timer(2.0, start_night, args=[chat_id]).start()

@bot.message_handler(commands=['stopgame'])
def cmd_stopgame(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game: return
    if str(message.from_user.id) != game['host_id'] and not is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Только хост или админ."); return
    del_mafia(message.chat.id)
    bot.send_message(message.chat.id, "❌ Остановлено.")

# ===== МЕНЮ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_'))
def menu_cb(call):
    data = call.data
    uid = call.from_user.id
    if data == 'menu_profile':
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        total = p['wins'] + p['losses']
        wr = round(p['wins']/total*100) if total else 0
        text = (
            f"👤 <b>ПРОФИЛЬ</b>\n\n<b>{display_name(p)}</b>\n\n"
            f"⚔️ Дуэли: 🏆 {p['wins']} / 💀 {p['losses']} ({wr}%)\n"
            f"🎭 Мафия: 🏆 {p['mafia_wins']} / 💀 {p['mafia_losses']}\n"
            f"🐉 Босс: 🏆 {p.get('boss_wins',0)} / 💀 {p.get('boss_losses',0)}\n\n"
            f"🥚 Яйца: {p.get('eggs',0)}\n"
            f"❤️ Макс. HP: {p.get('max_hp', BOSS_PLAYER_MIN_HP)}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    elif data == 'menu_top':
        stats = load_stats()
        sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins',0), reverse=True)[:15]
        text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n\n"
        placed = 0
        for i, (u, p) in enumerate(sorted_stats, 1):
            if p.get('wins',0) == 0: continue
            placed += 1
            medal = '🥇' if placed==1 else '🥈' if placed==2 else '🥉' if placed==3 else f'{placed}.'
            text += f"{medal} {display_name(p)} — {p['wins']} ⚔️\n"
        bot.send_message(call.message.chat.id, text or "🏆 Пусто", parse_mode='HTML')
    elif data == 'menu_duel':
        bot.send_message(call.message.chat.id, "⚔️ В группе ответь на сообщение игрока и напиши /duel")
    elif data == 'menu_mafia':
        bot.send_message(call.message.chat.id, "🎭 В группе напиши /mafia")
    elif data == 'menu_boss':
        bot.send_message(call.message.chat.id, "🐉 В группе напиши /boss — соберём команду 2-4 игрока")
    elif data == 'menu_eggs':
        bot.send_message(call.message.chat.id, eggs_menu_text(uid), parse_mode='HTML', reply_markup=eggs_menu_kb())
    elif data == 'menu_help':
        bot.send_message(call.message.chat.id, "💬 Дуэли: /duel.\n🎭 Мафия: /mafia.\n🐉 Босс: /boss.\n🥚 Яйца: /eggs.")
    elif data == 'menu_back':
        bot.send_message(call.message.chat.id, "🎭 Меню:", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start', '🎭 Меню'),
            types.BotCommand('help', '💬 Помощь'),
            types.BotCommand('profile', '👤 Профиль'),
            types.BotCommand('top', '🏆 Топ'),
            types.BotCommand('duel', '⚔️ Дуэль'),
            types.BotCommand('mafia', '🎭 Мафия'),
            types.BotCommand('boss', '🐉 Босс'),
            types.BotCommand('eggs', '🥚 Яйца'),
        ])
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()
