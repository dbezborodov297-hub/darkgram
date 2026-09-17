import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ===== ФАЙЛЫ =====
STATS_FILE = 'stats.json'
DUELS_FILE = 'duels.json'
MAFIA_FILE = 'mafia.json'

ADMIN_IDS = [8907438590]

DUEL_HP = 100
DUEL_SHOOT_MIN = 25
DUEL_SHOOT_MAX = 45
DUEL_AIM_BONUS = 0.9
DUEL_NOAIM_CHANCE = 0.6

MAFIA_MIN_PLAYERS = 4
MAFIA_MAX_PLAYERS = 50
MAFIA_NIGHT_TIME = 60
MAFIA_VOTE_TIME = 90

TOKEN = '8883984473:AAF12ux76ov704A-CDbFAbBoDWp1rr3j_4k'

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
    return {'mafia':'Мафия','doctor':'Доктор','sheriff':'Шериф','civilian':'Мирный житель'}.get(role, role)

bot = telebot.TeleBot(TOKEN)

# ===== HTTP-СЕРВЕР (заглушка для Render) =====
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Darkgram Mafia Bot is running')

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

# ===== ГЛАВНОЕ МЕНЮ =====
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='Профиль', callback_data='menu_profile'),
        types.InlineKeyboardButton(text='Топ', callback_data='menu_top')
    )
    kb.add(
        types.InlineKeyboardButton(text='Дуэль', callback_data='menu_duel'),
        types.InlineKeyboardButton(text='Мафия', callback_data='menu_mafia')
    )
    kb.add(types.InlineKeyboardButton(text='Помощь', callback_data='menu_help'))
    return kb

# ===== /start =====
@bot.message_handler(commands=['start'])
def cmd_start(message):
    uid = message.from_user.id
    get_player(uid, message.from_user.first_name, message.from_user.username)
    text = (
        f"<b>DARKGRAM</b>\n\n"
        f"Привет, {message.from_user.first_name}!\n\n"
        f"Что тут есть:\n"
        f"• Дуэли 1 на 1\n"
        f"• Мафия (4-50 игроков)\n"
        f"• Топ по победам\n"
        f"• Профиль\n\n"
        f"Выбирай:"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

# ===== /help =====
@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        f"<b>ПОМОЩЬ</b>\n\n"
        f"<b>Дуэли:</b>\n"
        f"В группе: <code>/duel @username</code> — вызвать на дуэль\n"
        f"Кнопки: Выстрел / Прицелиться\n"
        f"У каждого 100 HP. Кто первый снял — победил.\n\n"
        f"<b>Мафия:</b>\n"
        f"В группе: <code>/mafia</code> — создать игру\n"
        f"<code>/join</code> — присоединиться\n"
        f"<code>/startgame</code> — начать (минимум 4)\n"
        f"Роли приходят в личку. Ночью действуй, днём голосуй.\n\n"
        f"<b>Команды:</b>\n"
        f"/profile — профиль\n"
        f"/top — топ по победам\n"
        f"/duel @user — дуэль\n"
        f"/mafia — новая игра мафии\n"
        f"/join — войти в игру\n"
        f"/leave — выйти\n"
        f"/startgame — начать\n"
        f"/stopgame — остановить (хост)"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ===== /profile =====
@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    uid = message.from_user.id
    p = get_player(uid, message.from_user.first_name, message.from_user.username)
    total = p['wins'] + p['losses']
    wr = round(p['wins'] / total * 100) if total else 0
    mafia_total = p['mafia_wins'] + p['mafia_losses']
    mafia_wr = round(p['mafia_wins'] / mafia_total * 100) if mafia_total else 0
    text = (
        f"<b>ПРОФИЛЬ</b>\n\n"
        f"<b>{p['first_name']}</b>\n"
        f"{('@'+p['username']) if p.get('username') else '—'}\n\n"
        f"<b>Дуэли:</b>\n"
        f"Побед: {p['wins']}\n"
        f"Поражений: {p['losses']}\n"
        f"Винрейт: {wr}%\n\n"
        f"<b>Мафия:</b>\n"
        f"Побед: {p['mafia_wins']}\n"
        f"Поражений: {p['mafia_losses']}\n"
        f"Винрейт: {mafia_wr}%"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ===== /top =====
@bot.message_handler(commands=['top'])
def cmd_top(message):
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "Пока пусто.")
        return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = "<b>ТОП ПО ПОБЕДАМ В ДУЭЛЯХ</b>\n\n"
    for i, (uid, p) in enumerate(sorted_stats, 1):
        if p.get('wins', 0) == 0: continue
        name = p.get('username') and ('@'+p['username']) or p.get('first_name', 'Аноним')
        medal = '🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'{i}.'
        text += f"{medal} {name} — {p['wins']} побед, {p['losses']} поражений\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ===== /post (админ) =====
@bot.message_handler(commands=['post'])
def cmd_post(message):
    if not is_admin_id(message.from_user.id): return
    text = message.text.replace('/post','').strip()
    if not text:
        bot.send_message(message.chat.id, "Использование: /post Текст")
        return
    stats = load_stats()
    sent = 0
    for uid in list(stats.keys()):
        try:
            bot.send_message(int(uid), text, parse_mode='HTML')
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"Разослано: {sent} из {len(stats)}")

# ===== ДУЭЛИ =====
@bot.message_handler(commands=['duel'])
def cmd_duel(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "Дуэли только в группах.")
        return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "Ответь на сообщение игрока и напиши /duel — вызовешь его.")
        return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        bot.send_message(message.chat.id, "Себе нельзя.")
        return
    if target.is_bot:
        bot.send_message(message.chat.id, "С ботом нельзя.")
        return
    existing = get_duel(message.chat.id)
    if existing and existing.get('status') in ('pending','active'):
        bot.send_message(message.chat.id, "В этом чате уже идёт дуэль.")
        return
    challenger_name = message.from_user.first_name
    target_name = target.first_name
    duel = {
        'chat_id': message.chat.id,
        'p1_id': str(message.from_user.id),
        'p1_name': challenger_name,
        'p2_id': str(target.id),
        'p2_name': target_name,
        'p1_hp': DUEL_HP,
        'p2_hp': DUEL_HP,
        'p1_aim': False,
        'p2_aim': False,
        'turn': str(message.from_user.id),
        'status': 'pending',
        'created': int(time.time())
    }
    save_duel(message.chat.id, duel)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='Принять', callback_data=f'duel_accept'),
        types.InlineKeyboardButton(text='Отклонить', callback_data=f'duel_decline')
    )
    bot.send_message(
        message.chat.id,
        f"{challenger_name} вызывает {target_name} на дуэль!\n\n{target_name}, ты принимаешь?",
        reply_markup=kb
    )

def duel_kb(duel):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='Выстрел', callback_data='duel_shoot'),
        types.InlineKeyboardButton(text='Прицелиться', callback_data='duel_aim')
    )
    return kb

def duel_status_text(duel):
    return (
        f"<b>ДУЭЛЬ</b>\n\n"
        f"{duel['p1_name']}: {duel['p1_hp']} HP {'(прицелился)' if duel['p1_aim'] else ''}\n"
        f"{duel['p2_name']}: {duel['p2_hp']} HP {'(прицелился)' if duel['p2_aim'] else ''}\n\n"
        f"Ход: {duel['p1_name'] if duel['turn']==duel['p1_id'] else duel['p2_name']}"
    )

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
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "Не твой вызов")
            return
        duel['status'] = 'active'
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "Дуэль началась!")
        return

    if call.data == 'duel_decline':
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "Не твой вызов")
            return
        del_duel(chat_id)
        bot.edit_message_text("Дуэль отклонена.", chat_id=chat_id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Отклонено")
        return

    if duel['status'] != 'active':
        bot.answer_callback_query(call.id, "Дуэль ещё не началась")
        return

    if uid != duel['turn']:
        bot.answer_callback_query(call.id, "Сейчас не твой ход")
        return

    if call.data == 'duel_aim':
        if uid == duel['p1_id']:
            duel['p1_aim'] = True
        else:
            duel['p2_aim'] = True
        next_turn(duel)
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel),
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id, "Прицел!")
        return

    if call.data == 'duel_shoot':
        if uid == duel['p1_id']:
            aim = duel['p1_aim']
            duel['p1_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p2_hp'] = max(0, duel['p2_hp'] - dmg)
                msg = f"Попадание! -{dmg} HP"
            else:
                msg = "Промах!"
        else:
            aim = duel['p2_aim']
            duel['p2_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p1_hp'] = max(0, duel['p1_hp'] - dmg)
                msg = f"Попадание! -{dmg} HP"
            else:
                msg = "Промах!"

        # Проверка победы
        if duel['p1_hp'] <= 0 or duel['p2_hp'] <= 0:
            winner_id = duel['p1_id'] if duel['p2_hp'] <= 0 else duel['p2_id']
            loser_id = duel['p2_id'] if winner_id == duel['p1_id'] else duel['p1_id']
            winner_name = duel['p1_name'] if winner_id == duel['p1_id'] else duel['p2_name']
            add_duel_win(winner_id)
            add_duel_loss(loser_id)
            del_duel(chat_id)
            bot.edit_message_text(
                f"<b>ДУЭЛЬ ОКОНЧЕНА</b>\n\n{msg}\n\nПобедил: {winner_name}",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "Победа!")
            return

        next_turn(duel)
        save_duel(chat_id, duel)
        bot.edit_message_text(
            duel_status_text(duel) + f"\n\n{msg}",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=duel_kb(duel)
        )
        bot.answer_callback_query(call.id)

# ===== МАФИЯ =====
@bot.message_handler(commands=['mafia'])
def cmd_mafia(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "Мафия только в группах. Добавь бота в группу.")
        return
    game = get_mafia(message.chat.id)
    if game and game.get('status') not in ('finished',):
        bot.send_message(message.chat.id, "В этом чате уже идёт игра.")
        return
    game = {
        'chat_id': message.chat.id,
        'host_id': str(message.from_user.id),
        'host_name': message.from_user.first_name,
        'players': {},
        'status': 'lobby',
        'day': 0,
        'night_actions': {},
        'votes': {},
        'log': []
    }
    # Хост автоматически входит
    game['players'][str(message.from_user.id)] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'alive': True,
        'role': None
    }
    save_mafia_game(message.chat.id, game)
    text = (
        f"<b>МАФИЯ</b>\n\n"
        f"Хост: {message.from_user.first_name}\n"
        f"Игроков: 1\n\n"
        f"Напишите /join чтобы присоединиться.\n"
        f"Минимум {MAFIA_MIN_PLAYERS} игроков.\n"
        f"Хост запускает: /startgame"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['join'])
def cmd_join(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game or game.get('status') != 'lobby':
        bot.send_message(message.chat.id, "Сейчас нет набора в игру.")
        return
    uid = str(message.from_user.id)
    if uid in game['players']:
        bot.send_message(message.chat.id, "Ты уже в игре.")
        return
    if len(game['players']) >= MAFIA_MAX_PLAYERS:
        bot.send_message(message.chat.id, f"Максимум {MAFIA_MAX_PLAYERS} игроков.")
        return
    game['players'][uid] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'alive': True,
        'role': None
    }
    save_mafia_game(message.chat.id, game)
    bot.send_message(message.chat.id, f"{message.from_user.first_name} в игре. Всего: {len(game['players'])}")

@bot.message_handler(commands=['leave'])
def cmd_leave(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game or game.get('status') != 'lobby': return
    uid = str(message.from_user.id)
    if uid in game['players']:
        del game['players'][uid]
        save_mafia_game(message.chat.id, game)
        bot.send_message(message.chat.id, f"{message.from_user.first_name} вышел. Всего: {len(game['players'])}")

@bot.message_handler(commands=['startgame'])
def cmd_startgame(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game or game.get('status') != 'lobby':
        bot.send_message(message.chat.id, "Игра не в лобби.")
        return
    if str(message.from_user.id) != game['host_id']:
        bot.send_message(message.chat.id, "Только хост может начать.")
        return
    if len(game['players']) < MAFIA_MIN_PLAYERS:
        bot.send_message(message.chat.id, f"Нужно минимум {MAFIA_MIN_PLAYERS} игроков.")
        return
    assign_roles(game['players'])
    game['status'] = 'roles'
    save_mafia_game(message.chat.id, game)
    bot.send_message(message.chat.id, f"Игра начинается! Игроков: {len(game['players'])}\nРоли отправлены в личку.")
    # Отправка ролей
    for uid, p in game['players'].items():
        try:
            role = p['role']
            role_text = (
                f"<b>ТВОЯ РОЛЬ: {role_ru(role)}</b>\n\n"
            )
            if role == 'mafia':
                role_text += "Ночью выбирай жертву. Ты можешь убить любого игрока.\nДнём притворяйся мирным!"
            elif role == 'doctor':
                role_text += "Ночью выбирай, кого лечить. Если мафия выберет его же — он выживет."
            elif role == 'sheriff':
                role_text += "Ночью проверяй одного игрока. Узнаешь — мафия он или нет."
            else:
                role_text += "Ты мирный житель. Ночью спишь. Днём голосуй против мафии!"
            bot.send_message(int(uid), role_text, parse_mode='HTML')
        except: pass
    # Старт ночи через 3 сек
    threading.Timer(3.0, start_night, args=[message.chat.id]).start()

def start_night(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') == 'finished': return
    game['status'] = 'night'
    game['day'] += 1
    game['night_actions'] = {}
    game['votes'] = {}
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"<b>НОЧЬ {game['day']}</b>\n\nВсе засыпают. Ночные роли — действуйте в личке.", parse_mode='HTML')
    # Отправляем кнопки мафии/доктору/шерифу
    for uid, p in game['players'].items():
        if not p['alive']: continue
        role = p['role']
        try:
            if role == 'mafia':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    if tp['role'] == 'mafia': continue
                    kb.add(types.InlineKeyboardButton(text=tp['name'], callback_data=f'mafia_kill_{tuid}'))
                bot.send_message(int(uid), "Выбери жертву:", reply_markup=kb)
            elif role == 'doctor':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    kb.add(types.InlineKeyboardButton(text=tp['name'], callback_data=f'mafia_heal_{tuid}'))
                bot.send_message(int(uid), "Кого лечить?", reply_markup=kb)
            elif role == 'sheriff':
                kb = types.InlineKeyboardMarkup(row_width=2)
                for tuid, tp in game['players'].items():
                    if not tp['alive']: continue
                    if tuid == uid: continue
                    kb.add(types.InlineKeyboardButton(text=tp['name'], callback_data=f'mafia_check_{tuid}'))
                bot.send_message(int(uid), "Кого проверить?", reply_markup=kb)
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
            bot.answer_callback_query(call.id, "Уже не ночь")
            return
        p = game['players'].get(uid)
        if not p or p.get('role') != action_to_role(action):
            bot.answer_callback_query(call.id, "Не твоя роль")
            return
        game['night_actions'][action] = target_id
        save_mafia_game(call.message.chat.id, game)
        target_name = game['players'][target_id]['name']
        if action == 'kill':
            bot.edit_message_text(f"Ты выбрал убить: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "Жертва выбрана")
        elif action == 'heal':
            bot.edit_message_text(f"Ты лечишь: {target_name}", chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.answer_callback_query(call.id, "Лечение выбрано")
        elif action == 'check':
            target_role = game['players'][target_id].get('role')
            is_mafia = (target_role == 'mafia')
            bot.edit_message_text(
                f"Проверка: {target_name}\n\nРезультат: {'МАФИЯ!' if is_mafia else 'не мафия'}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            bot.answer_callback_query(call.id, "Проверено")
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

    text = f"<b>УТРО {game['day']}</b>\n\n"
    if killed_name:
        text += f"Убит: {killed_name}"
    else:
        text += "Этой ночью никто не погиб."
    bot.send_message(chat_id, text, parse_mode='HTML')

    # Проверка победы
    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        # Мирные победили
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        game['status'] = 'finished'
        save_mafia_game(chat_id, game)
        bot.send_message(chat_id, "<b>МИРНЫЕ ПОБЕДИЛИ!</b>\n\nВсе мафии найдены.", parse_mode='HTML')
        del_mafia(chat_id)
        return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        game['status'] = 'finished'
        save_mafia_game(chat_id, game)
        bot.send_message(chat_id, "<b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return

    # Начинаем голосование
    start_vote(chat_id)

def start_vote(chat_id):
    game = get_mafia(chat_id)
    if not game: return
    game['status'] = 'vote'
    game['votes'] = {}
    save_mafia_game(chat_id, game)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid, p in game['players'].items():
        if p['alive']:
            kb.add(types.InlineKeyboardButton(text=p['name'], callback_data=f'vote_{uid}'))
    bot.send_message(chat_id, f"<b>ГОЛОСОВАНИЕ</b>\n\nКого казнить? У всех {MAFIA_VOTE_TIME} сек.", reply_markup=kb, parse_mode='HTML')
    threading.Timer(MAFIA_VOTE_TIME, end_vote, args=[chat_id]).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith('vote_'))
def vote_cb(call):
    game = get_mafia(call.message.chat.id)
    if not game or game.get('status') != 'vote':
        bot.answer_callback_query(call.id, "Голосование закрыто")
        return
    uid = str(call.from_user.id)
    if not game['players'].get(uid, {}).get('alive'):
        bot.answer_callback_query(call.id, "Ты мёртв")
        return
    target = call.data.replace('vote_','')
    game['votes'][uid] = target
    save_mafia_game(call.message.chat.id, game)
    bot.answer_callback_query(call.id, f"Голос: {game['players'][target]['name']}")

def end_vote(chat_id):
    game = get_mafia(chat_id)
    if not game or game.get('status') != 'vote': return
    votes = game['votes']
    if not votes:
        bot.send_message(chat_id, "Никто не голосовал. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start()
        return
    counts = {}
    for t in votes.values():
        counts[t] = counts.get(t, 0) + 1
    max_v = max(counts.values())
    top = [t for t, c in counts.items() if c == max_v]
    if len(top) > 1:
        bot.send_message(chat_id, "Ничья. Никто не казнён. Ночь.")
        threading.Timer(2.0, start_night, args=[chat_id]).start()
        return
    target = top[0]
    target_name = game['players'][target]['name']
    target_role = game['players'][target]['role']
    game['players'][target]['alive'] = False
    save_mafia_game(chat_id, game)
    bot.send_message(chat_id, f"<b>КАЗНЁН: {target_name}</b>\nРоль: {role_ru(target_role)}", parse_mode='HTML')

    # Проверка победы
    alive = [u for u,p in game['players'].items() if p['alive']]
    alive_mafia = [u for u in alive if game['players'][u]['role'] == 'mafia']
    alive_civ = [u for u in alive if game['players'][u]['role'] != 'mafia']
    if not alive_mafia:
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_loss(uid)
            else: add_mafia_win(uid)
        bot.send_message(chat_id, "<b>МИРНЫЕ ПОБЕДИЛИ!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return
    if len(alive_mafia) >= len(alive_civ):
        for uid, p in game['players'].items():
            if p['role'] == 'mafia': add_mafia_win(uid)
            else: add_mafia_loss(uid)
        bot.send_message(chat_id, "<b>МАФИЯ ПОБЕДИЛА!</b>", parse_mode='HTML')
        del_mafia(chat_id)
        return

    threading.Timer(2.0, start_night, args=[chat_id]).start()

@bot.message_handler(commands=['stopgame'])
def cmd_stopgame(message):
    if message.chat.type == 'private': return
    game = get_mafia(message.chat.id)
    if not game: return
    if str(message.from_user.id) != game['host_id'] and not is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, "Только хост или админ может остановить.")
        return
    del_mafia(message.chat.id)
    bot.send_message(message.chat.id, "Игра остановлена.")

# ===== CALLBACK ДЛЯ МЕНЮ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_'))
def menu_cb(call):
    data = call.data
    uid = call.from_user.id
    if data == 'menu_profile':
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        total = p['wins'] + p['losses']
        wr = round(p['wins']/total*100) if total else 0
        text = (
            f"<b>ПРОФИЛЬ</b>\n\n<b>{p['first_name']}</b>\n\n"
            f"Дуэли: {p['wins']} побед / {p['losses']} поражений ({wr}%)\n"
            f"Мафия: {p['mafia_wins']} побед / {p['mafia_losses']} поражений"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    elif data == 'menu_top':
        stats = load_stats()
        sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins',0), reverse=True)[:15]
        text = "<b>ТОП ДУЭЛЯНТОВ</b>\n\n"
        for i, (u, p) in enumerate(sorted_stats, 1):
            if p.get('wins',0) == 0: continue
            name = p.get('username') and ('@'+p['username']) or p.get('first_name','Аноним')
            text += f"{i}. {name} — {p['wins']} побед\n"
        bot.send_message(call.message.chat.id, text or "Пусто", parse_mode='HTML')
    elif data == 'menu_duel':
        bot.send_message(call.message.chat.id, "В группе ответь на сообщение игрока и напиши /duel")
    elif data == 'menu_mafia':
        bot.send_message(call.message.chat.id, "В группе напиши /mafia чтобы собрать игру")
    elif data == 'menu_help':
        bot.send_message(call.message.chat.id, "Дуэли: /duel в ответ на сообщение.\nМафия: /mafia, /join, /startgame.")
    bot.answer_callback_query(call.id)

# ===== СТАРТ =====
def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start', 'Меню'),
            types.BotCommand('help', 'Помощь'),
            types.BotCommand('profile', 'Профиль'),
            types.BotCommand('top', 'Топ по победам'),
            types.BotCommand('duel', 'Вызвать на дуэль'),
            types.BotCommand('mafia', 'Создать мафию'),
            types.BotCommand('join', 'Войти в мафию'),
            types.BotCommand('startgame', 'Начать мафию'),
        ])
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()
