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

TOKEN = '8883984473:AAF12ux76ov704A-CDbFAbBoDWp1rr3j_4k'

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
            'duels_played': 0, 'mafia_played': 0
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        for f in ['wins','losses','mafia_wins','mafia_losses','duels_played','mafia_played']:
            if f not in stats[key]: stats[key][f] = 0
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

def get_duel(chat_id):
    return load_duels().get(str(chat_id))

def save_duel(chat_id, duel):
    d = load_duels(); d[str(chat_id)] = duel; save_duels(d)

def del_duel(chat_id):
    d = load_duels()
    if str(chat_id) in d: del d[str(chat_id)]; save_duels(d)

def get_mafia(chat_id):
    return load_mafia().get(str(chat_id))

def save_mafia_game(chat_id, game):
    m = load_mafia(); m[str(chat_id)] = game; save_mafia(m)

def del_mafia(chat_id):
    m = load_mafia()
    if str(chat_id) in m: del m[str(chat_id)]; save_mafia(m)

def assign_roles(players):
    ids = list(players.keys())
    count = len(ids)
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
    m = sec // 60
    s = sec % 60
    return f"{m}:{s:02d}"

bot = telebot.TeleBot(TOKEN)

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
        f"🏆 Топ по победам\n"
        f"👤 Профиль\n\n"
        f"Выбирай:"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n\n"
        f"⚔️ <b>Дуэли:</b>\n"
        f"В группе ответь на сообщение игрока и напиши /duel\n"
        f"У соперника 5 минут на принятие вызова\n"
        f"Кнопки: 🔫 Выстрел / 🎯 Прицел / 🎭 Отвлечь\n"
        f"Отвлечь — сбивает прицел сопернику!\n\n"
        f"🎭 <b>Мафия:</b>\n"
        f"В группе напиши /mafia\n"
        f"Лобби работает 3:50\n"
        f"Если 4+ — автостарт по истечении\n"
        f"Если меньше — лобби закрывается\n"
        f"Роли приходят в личку 💌\n"
        f"Ночь 60 сек, день 45 сек"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

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
        f"<b>{p['first_name']}</b>\n"
        f"{('@'+p['username']) if p.get('username') else '—'}\n\n"
        f"⚔️ <b>Дуэли:</b>\n"
        f"🏆 Побед: {p['wins']}\n"
        f"💀 Поражений: {p['losses']}\n"
        f"📊 Винрейт: {wr}%\n\n"
        f"🎭 <b>Мафия:</b>\n"
        f"🏆 Побед: {p['mafia_wins']}\n"
        f"💀 Поражений: {p['mafia_losses']}\n"
        f"📊 Винрейт: {mafia_wr}%"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['top'])
def cmd_top(message):
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "🏆 Пока пусто.")
        return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n\n"
    for i, (uid, p) in enumerate(sorted_stats, 1):
        if p.get('wins', 0) == 0: continue
        name = p.get('username') and ('@'+p['username']) or p.get('first_name', 'Аноним')
        medal = '🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'{i}.'
        text += f"{medal} {name} — {p['wins']} побед ⚔️, {p['losses']} 💀\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['post'])
def cmd_post(message):
    if not is_admin_id(message.from_user.id): return
    text = message.text.replace('/post','').strip()
    if not text:
        bot.send_message(message.chat.id, "📢 Использование: /post Текст")
        return
    stats = load_stats()
    sent = 0
    for uid in list(stats.keys()):
        try:
            bot.send_message(int(uid), "📢 " + text, parse_mode='HTML')
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"📢 Разослано: {sent} из {len(stats)}")

# ===== ДУЭЛИ =====
@bot.message_handler(commands=['duel'])
def cmd_duel(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "⚔️ Дуэли только в группах.")
        return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "⚔️ Ответь на сообщение игрока и напиши /duel")
        return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        bot.send_message(message.chat.id, "❌ Себе нельзя.")
        return
    if target.is_bot:
        bot.send_message(message.chat.id, "❌ С ботом нельзя.")
        return
    existing = get_duel(message.chat.id)
    if existing and existing.get('status') in ('pending','active'):
        bot.send_message(message.chat.id, "⚔️ В этом чате уже идёт дуэль.")
        return
    now = int(time.time())
    duel = {
        'chat_id': message.chat.id,
        'p1_id': str(message.from_user.id),
        'p1_name': message.from_user.first_name,
        'p2_id': str(target.id),
        'p2_name': target.first_name,
        'p1_hp': DUEL_HP,
        'p2_hp': DUEL_HP,
        'p1_aim': False,
        'p2_aim': False,
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
        message.chat.id,
        build_duel_pending_text(duel),
        parse_mode='HTML',
        reply_markup=kb
    )
    duel['msg_id'] = sent.message_id
    save_duel(message.chat.id, duel)
    threading.Timer(DUEL_ACCEPT_TIMEOUT, duel_timeout, args=[message.chat.id]).start()

def build_duel_pending_text(duel):
    left = duel['deadline'] - int(time.time())
    return (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"🥷 <b>{duel['p1_name']}</b> вызывает <b>{duel['p2_name']}</b>!\n\n"
        f"{duel['p2_name']}, ты принимаешь?\n\n"
        f"⏱ Осталось: <b>{fmt_time(left)}</b>"
    )

def duel_timeout(chat_id):
    duel = get_duel(chat_id)
    if not duel or duel.get('status') != 'pending':
        return
    try:
        bot.edit_message_text(
            "⌛ <b>Время вышло</b>\n\nВызов на дуэль отменён.",
            chat_id=chat_id,
            message_id=duel['msg_id'],
            parse_mode='HTML'
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
    if duel.get('last_action_msg'):
        text += f"\n\n{duel['last_action_msg']}"
    return text

def next_turn(duel):
    duel['turn'] = duel['p2_id'] if duel['turn'] == duel['p1_id'] else duel['p1_id']

@bot.callback_query_handler(func=lambda c: c.data.startswith('duel_'))
def duel_cb(call):
    chat_id = call.message.chat.id
    duel = get_duel(chat_id)
    if not duel:
        bot.answer_callback_query(call.id, "Дуэль не найдена")
        return
    uid = str(call.from_user.id)

    if call.data == 'duel_accept':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Вызов уже неактуален")
            return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов")
            return
        duel['status'] = 'active'
        duel['last_action_msg'] = ''
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "⚔️ Дуэль началась!")
        return

    if call.data == 'duel_decline':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Вызов уже неактуален")
            return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов")
            return
        del_duel(chat_id)
        bot.edit_message_text("❌ Дуэль отклонена.", chat_id=chat_id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Отклонено")
        return

    if duel.get('status') != 'active':
        bot.answer_callback_query(call.id, "Дуэль ещё не началась")
        return

    if uid != duel['turn']:
        bot.answer_callback_query(call.id, "🎯 Сейчас не твой ход")
        return

    if call.data == 'duel_aim':
        if uid == duel['p1_id']:
            duel['p1_aim'] = True
        else:
            duel['p2_aim'] = True
        duel['last_action_msg'] = "🎯 Игрок прицелился!"
        next_turn(duel)
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "🎯 Прицел!")
        return

    if call.data == 'duel_distract':
        if uid == duel['p1_id']:
            had_aim = duel['p2_aim']
            duel['p2_aim'] = False
        else:
            had_aim = duel['p1_aim']
            duel['p1_aim'] = False
        msg = random.choice(DISTRACT_MESSAGES)
        if had_aim:
            msg += "\n💥 Прицел соперника сбит!"
        else:
            msg += "\n🤷 У соперника не было прицела."
        duel['last_action_msg'] = msg
        next_turn(duel)
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "🎭 Отвлёк!")
        return

    if call.data == 'duel_shoot':
        if uid == duel['p1_id']:
            aim = duel['p1_aim']
            duel['p1_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p2_hp'] = max(0, duel['p2_hp'] - dmg)
                msg = f"💥 Попадание! -{dmg} HP"
            else:
                msg = "🌫 Промах!"
        else:
            aim = duel['p2_aim']
            duel['p2_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p1_hp'] = max(0, duel['p1_hp'] - dmg)
                msg = f"💥 Попадание! -{dmg} HP"
            else:
                msg = "🌫 Промах!"

        duel['last_action_msg'] = msg

        if duel['p1_hp'] <= 0 or duel['p2_hp'] <= 0:
            winner_id = duel['p1_id'] if duel['p2_hp'] <= 0 else duel['p2_id']
            loser_id = duel['p2_id'] if winner_id == duel['p1_id'] else duel['p1_id']
            winner_name = duel['p1_name'] if winner_id == duel['p1_id'] else duel['p2_name']
            add_duel_win(winner_id)
            add_duel_loss(loser_id)
            del_duel(chat_id)
            bot.edit_message_text(
                f"🏆 <b>ДУЭЛЬ ОКОНЧЕНА</b>\n\n{msg}\n\n🥇 Победил: <b>{winner_name}</b>",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "🏆 Победа!")
            return

        next_turn(duel)
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
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
        types.InlineKeyboardButton(text='▶️ Начать игру', callback_data='mafia_start'),
        types.InlineKeyboardButton(text='❌ Отменить', callback_data='mafia_cancel')
    )
    if is_admin:
        kb.add(types.InlineKeyboardButton(text='➕ Продлить на 3:50', callback_data='mafia_extend'))
    return kb

def mafia_lobby_text(game, admin_view=False):
    players_list = "\n".join([f"• {p['name']}" for p in game['players'].values()])
    left = game.get('deadline', 0) - int(time.time())
    text = (
        f"🎭 <b>МАФИЯ — СБОР ИГРОКОВ</b>\n\n"
        f"👑 Хост: <b>{game['host_name']}</b>\n"
        f"👥 Игроков: <b>{len(game['players'])}/{MAFIA_MAX_PLAYERS}</b> (мин. {MAFIA_MIN_PLAYERS})\n"
        f"⏱ До закрытия: <b>{fmt_time(left)}</b>\n\n"
        f"<b>Игроки:</b>\n{players_list}\n\n"
        f"Жми кнопки ниже 👇"
    )
    return text

@bot.message_handler(commands=['mafia'])
def cmd_mafia(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "🎭 Мафия только в группах.")
        return
    game = get_mafia(message.chat.id)
    if game and game.get('status') not in ('finished',):
        bot.send_message(message.chat.id, "🎭 В этом чате уже идёт игра.")
        return
    now = int(time.time())
    game = {
        'chat_id': message.chat.id,
        'host_id': str(message.from_user.id),
        'host_name': message.from_user.first_name,
        'players': {},
        'status': 'lobby',
        'day': 0,
        'night_actions': {},
        'votes': {},
        'vote_msg_id': None,
        'lobby_msg_id': None,
        'deadline': now + MAFIA_LOBBY_TIME,
        'log': []
    }
    game['players'][str(message.from_user.id)] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'alive': True,
        'role': None
    }
    save_mafia_game(message.chat.id, game)
    sent = bot.send_message(
        message.chat.id,
        mafia_lobby_text(game, is_admin_id(message.from_user.id)),
        parse_mode='HTML',
        reply_markup=mafia_lobby_kb(is_admin_id(message.from_user.id))
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
            mafia_lobby_text(game),
            chat_id=chat_id,
            message_id=game['lobby_msg_id'],
            parse_mode='HTML',
            reply_markup=mafia_lobby_kb(is_admin_id(game['host_id']))
        )
    except: pass
    threading.Timer(MAFIA_TIMER_UPDATE, mafia_lobby_tick, args=[chat_id]).start()

def mafia_lobby_timeout(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'lobby': return
    count = len(game['players'])
    if count >= MAFIA_MIN_PLAYERS:
        try:
            bot.send_message(chat_id, f"⏱ Время лобби вышло. Игроков: {count}. Автостарт!", parse_mode='HTML')
        except: pass
        start_mafia_game(chat_id)
    else:
        try:
            bot.send_message(chat_id, f"⏱ Время вышло. Игроков: {count} (нужно {MAFIA_MIN_PLAYERS}). Лобби закрыто.", parse_mode='HTML')
        except: pass
        del_mafia(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('mafia_join') or c.data.startswith('mafia_leave') or c.data.startswith('mafia_start') or c.data.startswith('mafia_cancel') or c.data.startswith('mafia_extend'))
def mafia_lobby_cb(call):
    chat_id = call.message.chat.id
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌ Лобби закрыто")
        return
    uid = str(call.from_user.id)
    is_admin = is_admin_id(uid)

    if call.data == 'mafia_join':
        if uid in game['players']:
            bot.answer_callback_query(call.id, "✅ Ты уже в игре")
            return
        if len(game['players']) >= MAFIA_MAX_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Максимум {MAFIA_MAX_PLAYERS}")
            return
        game['players'][uid] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username or '',
            'alive': True,
            'role': None
        }
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game),
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "🎭 Ты в игре!")
        return

    if call.data == 'mafia_leave':
        if uid not in game['players']:
            bot.answer_callback_query(call.id, "❌ Ты не в игре")
            return
        was_host = (uid == game['host_id'])
        del game['players'][uid]
        if was_host and game['players']:
            new_host_id = list(game['players'].keys())[0]
            game['host_id'] = new_host_id
            game['host_name'] = game['players'][new_host_id]['name']
            try:
                bot.send_message(chat_id, f"👑 Новый хост: <b>{game['host_name']}</b>", parse_mode='HTML')
            except: pass
        elif not game['players']:
            del_mafia(chat_id)
            try:
                bot.edit_message_text("❌ Лобби закрыто — все вышли.", chat_id=chat_id, message_id=call.message.message_id)
            except: pass
            bot.answer_callback_query(call.id, "🚪 Лобби закрыто")
            return
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game),
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "🚪 Ты вышел")
        return

    if call.data == 'mafia_start':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост")
            return
        if len(game['players']) < MAFIA_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Нужно минимум {MAFIA_MIN_PLAYERS}")
            return
        bot.answer_callback_query(call.id, "🎭 Игра начинается!")
        start_mafia_game(chat_id)
        return

    if call.data == 'mafia_cancel':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост")
            return
        del_mafia(chat_id)
        try:
            bot.edit_message_text("❌ Игра отменена.", chat_id=chat_id, message_id=call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, "Отменено")
        return

    if call.data == 'mafia_extend':
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ Только админ")
            return
        game['deadline'] = int(time.time()) + MAFIA_LOBBY_TIME
        save_mafia_game(chat_id, game)
        try:
            bot.edit_message_text(
                mafia_lobby_text(game),
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=mafia_lobby_kb(is_admin)
            )
        except: pass
        bot.answer_callback_query(call.id, "➕ Продлено на 3:50")

def start_mafia_game(chat_id):
    game = get_mafia(chat_id)
    if not game: return
    assign_roles(game['players'])
    game['status'] = 'roles'
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"🎭 <b>ИГРА НАЧАЛАСЬ!</b>\n\n👥 Игроков: {len(game['players'])}\n💌 Роли отправлены в личку.", parse_mode='HTML')
    for uid, p in game['players'].items():
        try:
            role = p['role']
            role_text = f"🎭 <b>ТВОЯ РОЛЬ: {role_ru(role)}</b>\n\n"
            if role == 'mafia':
                role_text += "🌙 Ночью выбирай жертву.\n☀️ Днём притворяйся мирным! 🤫"
            elif role == 'doctor':
                role_text += "🌙 Ночью лечи игроков.\nЕсли мафия выбрала того же — он выживет! 💉"
            elif role == 'sheriff':
                role_text += "🌙 Ночью проверяй игроков.\nУзнаешь мафия или нет 🔍"
            else:
                role_text += "🌙 Ночью спишь.\n☀️ Днём голосуй против мафии 🗳️"
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
    bot.send_message(chat_id, f"🌙 <b>НОЧЬ {game['day']}</b>\n\nВсе засыпают... 💤\n⏱ 60 секунд\nНочные роли — действуйте в личке 💌", parse_mode='HTML')
    for uid, p in game['players'].items():
        if not p['alive']: continue
        role = p['role']
        try:
            if role == 'mafia':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    if tp['role'] == 'mafia': continue
                    kb.add(types.InlineKeyboardButton(text=f"🔪 {tp['name']}", callback_data=f'mafia_kill_{tuid}'))
                if kb.keyboard:
                    bot.send_message(int(uid), "🔪 Выбери жертву:", reply_markup=kb)
            elif role == 'doctor':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    kb.add(types.InlineKeyboardButton(text=f"💉 {tp['name']}", callback_data=f'mafia_heal_{tuid}'))
                if kb.keyboard:
                    bot.send_message(int(uid), "💉 Кого лечить?", reply_markup=kb)
            elif role == 'sheriff':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    if tuid == uid: continue
                    kb.add(types.InlineKeyboardButton(text=f"🔍 {tp['name']}", callback_data=f'mafia_check_{tuid}'))
                if kb.keyboard:
                    bot.send_message(int(uid), "🔍 Кого проверить?", reply_markup=kb)
        except: pass
    threading.Timer(MAFIA_NIGHT_TIME, end_night, args=[chat_id]).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('mafia_kill_') or c.data.startswith('mafia_heal_') or c.data.startswith('mafia_check_'))
def mafia_night_cb(call):
    try:
        parts = call.data.split('_')
        action = parts[1]
        target_id = parts[2]
        uid = str(call.from_user.id)
        game = get_mafia(call.message.chat.id)
        if not game or game.get('status') != 'night':
            bot.answer_callback_query(call.id, "🌙 Уже не ночь")
            return
        p = game['players'].get(uid)
        if not p or p.get('role') != action_to_role(action):
            bot.answer_callback_query(call.id, "❌ Не твоя роль")
            return
        if not p.get('alive'):
            bot.answer_callback_query(call.id, "💀 Ты мёртв")
            return
        if target_id not in game['players'] or not game['players'][target_id].get('alive'):
            bot.answer_callback_query(call.id, "❌ Цель мертва")
            return
        game['night_actions'][action] = target_id
        save_mafia_game(call.message.chat.id, game)
        target_name = game['players'][target_id]['name']
        if action == 'kill':
            bot.edit_message_text(f"🔪 Ты выбрал убить: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "🔪 Жертва выбрана")
        elif action == 'heal':
            bot.edit_message_text(f"💉 Ты лечишь: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "💉 Лечение выбрано")
        elif action == 'check':
            target_role = game['players'][target_id].get('role')
            is_mafia = (target_role == 'mafia')
            bot.edit_message_text(
                f"🔍 Проверка: {target_name}\n\nРезультат: {'🔪 МАФИЯ!' if is_mafia else '👤 не мафия'}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            bot.answer_callback_query(call.id, "🔍 Проверено")
    except Exception as e:
        bot.answer_callback_query(call.id, "Ошибка")

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
    if killed_name:
        text += f"💀 Убит: <b>{killed_name}</b>"
    else:
        text += "☀️ Этой ночью никто не погиб! 💉"
    bot.send_message(chat_id, text, parse_mode='HTML')

    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        bot.send_message(chat_id, "🏆 <b>МИРНЫЕ ПОБЕДИЛИ!</b>\n\n🎉 Все мафии найдены!", parse_mode='HTML')
        del_mafia(chat_id)
        return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        bot.send_message(chat_id, "🔪 <b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return

    threading.Timer(2.0, start_vote, args=[chat_id]).start()

def build_vote_text(game):
    votes = game.get('votes', {})
    counts = {}
    for t in votes.values():
        counts[t] = counts.get(t, 0) + 1
    text = "🗳️ <b>ГОЛОСОВАНИЕ</b>\n\n⏱ 45 секунд\n\n<b>Голоса:</b>\n"
    for uid, p in game['players'].items():
        if not p['alive']: continue
        cnt = counts.get(uid, 0)
        bar = '█' * cnt if cnt > 0 else '·'
        text += f"• {p['name']} — {cnt} {bar}\n"
    text += f"\nВсего голосов: {len(votes)}"
    return text

def start_vote(chat_id):
    game = get_mafia(chat_id)
    if not game: return
    game['status'] = 'vote'
    game['votes'] = {}
    game['vote_msg_id'] = None
    save_mafia_game(chat_id, game)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid, p in game['players'].items():
        if p['alive']:
            kb.add(types.InlineKeyboardButton(text=f"🗳️ {p['name']}", callback_data=f'vote_{uid}'))
    if not kb.keyboard:
        bot.send_message(chat_id, "🤷 Все мертвы. Игра завершена.")
        del_mafia(chat_id)
        return
    msg = bot.send_message(chat_id, build_vote_text(game), reply_markup=kb, parse_mode='HTML')
    game['vote_msg_id'] = msg.message_id
    save_mafia_game(chat_id, game)
    threading.Timer(MAFIA_VOTE_TIME, end_vote, args=[chat_id]).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('vote_'))
def vote_cb(call):
    game = get_mafia(call.message.chat.id)
    if not game or game.get('status') != 'vote':
        bot.answer_callback_query(call.id, "🗳️ Голосование закрыто")
        return
    uid = str(call.from_user.id)
    if not game['players'].get(uid, {}).get('alive'):
        bot.answer_callback_query(call.id, "💀 Ты мёртв")
        return
    target = call.data.replace('vote_','')
    if target not in game['players'] or not game['players'][target].get('alive'):
        bot.answer_callback_query(call.id, "❌ Недоступно")
        return
    game['votes'][uid] = target
    save_mafia_game(call.message.chat.id, game)
    try:
        kb = types.InlineKeyboardMarkup(row_width=2)
        for tuid, tp in game['players'].items():
            if tp['alive']:
                kb.add(types.InlineKeyboardButton(text=f"🗳️ {tp['name']}", callback_data=f'vote_{tuid}'))
        bot.edit_message_text(
            build_vote_text(game),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=kb
        )
    except: pass
    bot.answer_callback_query(call.id, f"🗳️ Голос: {game['players'][target]['name']}")

def end_vote(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'vote': return
    votes = game['votes']
    if not votes:
        bot.send_message(chat_id, "🤷 Никто не голосовал. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start()
        return
    counts = {}
    for t in votes.values():
        counts[t] = counts.get(t, 0) + 1
    max_v = max(counts.values())
    top = [t for t, c in counts.items() if c == max_v]
    if len(top) > 1:
        bot.send_message(chat_id, "🤝 Ничья. Никто не казнён. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start()
        return
    target = top[0]
    target_name = game['players'][target]['name']
    target_role = game['players'][target]['role']
    game['players'][target]['alive'] = False
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"⚖️ <b>КАЗНЁН: {target_name}</b>\n\n🎭 Роль: {role_ru(target_role)}", parse_mode='HTML')

    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        bot.send_message(chat_id, "🏆 <b>МИРНЫЕ ПОБЕДИЛИ!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        bot.send_message(chat_id, "🔪 <b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return

    threading.Timer(2.0, start_night, args=[chat_id]).start()

@bot.message_handler(commands=['stopgame'])
def cmd_stopgame(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game: return
    if str(message.from_user.id) != game['host_id'] and not is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Только хост или админ.")
        return
    del_mafia(message.chat.id)
    bot.send_message(message.chat.id, "❌ Игра остановлена.")

@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_'))
def menu_cb(call):
    data = call.data
    uid = call.from_user.id
    if data == 'menu_profile':
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        total = p['wins'] + p['losses']
        wr = round(p['wins']/total*100) if total else 0
        text = (
            f"👤 <b>ПРОФИЛЬ</b>\n\n<b>{p['first_name']}</b>\n\n"
            f"⚔️ Дуэли: 🏆 {p['wins']} / 💀 {p['losses']} ({wr}%)\n"
            f"🎭 Мафия: 🏆 {p['mafia_wins']} / 💀 {p['mafia_losses']}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    elif data == 'menu_top':
        stats = load_stats()
        sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins',0), reverse=True)[:15]
        text = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n\n"
        for i, (u, p) in enumerate(sorted_stats, 1):
            if p.get('wins',0) == 0: continue
            name = p.get('username') and ('@'+p['username']) or p.get('first_name','Аноним')
            medal = '🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'{i}.'
            text += f"{medal} {name} — {p['wins']} ⚔️\n"
        bot.send_message(call.message.chat.id, text or "🏆 Пусто", parse_mode='HTML')
    elif data == 'menu_duel':
        bot.send_message(call.message.chat.id, "⚔️ В группе ответь на сообщение игрока и напиши /duel")
    elif data == 'menu_mafia':
        bot.send_message(call.message.chat.id, "🎭 В группе напиши /mafia чтобы собрать игру")
    elif data == 'menu_help':
        bot.send_message(call.message.chat.id, "💬 Дуэли: /duel в ответ на сообщение.\n🎭 Мафия: /mafia — и жми кнопки.")
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
        ])
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()
