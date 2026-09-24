import telebot
import time
import threading
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ==================== НАСТРОЙКИ ====================
TOKEN = '8747895563:AAGrxrG2y491FEM6acCtpnGk0YuH6e31VGA'

MIN_PLAYERS = 4
MAX_PLAYERS = 15
LOBBY_TIME = 5 * 60
NIGHT_TIME = 60
DAY_DISCUSS = 90
DAY_VOTE = 60

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)
GAMES = {}

# ==================== HTTP ДЛЯ RENDER ====================
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

# ==================== РОЛИ ====================
ROLE_MAFIA = 'Мафия'
ROLE_DON = 'Дон'
ROLE_COMISSAR = 'Комиссар'
ROLE_DOCTOR = 'Доктор'
ROLE_MANIAC = 'Маньяк'
ROLE_CIVIL = 'Мирный'

ROLE_EMOJI = {
    ROLE_MAFIA: '🔫',
    ROLE_DON: '👑',
    ROLE_COMISSAR: '🕵️',
    ROLE_DOCTOR: '💊',
    ROLE_MANIAC: '🔪',
    ROLE_CIVIL: '👤',
}

ROLE_DESC = {
    ROLE_MAFIA: 'Ночью вместе с мафией выбираешь жертву.',
    ROLE_DON: 'Главный мафии. Комиссар видит тебя как мирного. Ночью выбираешь жертву.',
    ROLE_COMISSAR: 'Ночью проверяешь одного игрока — мафия он или нет.',
    ROLE_DOCTOR: 'Ночью лечишь одного игрока. Если его выбрала мафия — он выживет.',
    ROLE_MANIAC: 'Ночью убиваешь одного. Побеждаешь, если остаёшься один.',
    ROLE_CIVIL: 'Ночью спишь. Днём ищешь мафию и голосуешь.',
}


def get_roles_for_count(n):
    if n == 4:
        return [ROLE_MAFIA, ROLE_COMISSAR, ROLE_CIVIL, ROLE_CIVIL]
    if n == 5:
        return [ROLE_DON, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_CIVIL, ROLE_CIVIL]
    if n == 6:
        return [ROLE_DON, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_CIVIL]
    if n == 7:
        return [ROLE_DON, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC,
                ROLE_CIVIL, ROLE_CIVIL]
    if n == 8:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR,
                ROLE_MANIAC, ROLE_CIVIL, ROLE_CIVIL]
    if n == 9:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR,
                ROLE_MANIAC, ROLE_CIVIL, ROLE_CIVIL, ROLE_CIVIL]
    if n == 10:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR,
                ROLE_MANIAC] + [ROLE_CIVIL] * 4
    if n == 11:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR,
                ROLE_DOCTOR, ROLE_MANIAC] + [ROLE_CIVIL] * 4
    if n == 12:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR,
                ROLE_DOCTOR, ROLE_MANIAC] + [ROLE_CIVIL] * 5
    if n == 13:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR,
                ROLE_DOCTOR, ROLE_MANIAC] + [ROLE_CIVIL] * 6
    if n == 14:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA,
                ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC] + [ROLE_CIVIL] * 6
    return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA,
            ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC] + [ROLE_CIVIL] * 7


# ==================== ИГРА ====================
class Game:
    def __init__(self, chat_id, host_id):
        self.chat_id = chat_id
        self.host_id = host_id
        self.players = {}
        self.order = []
        self.phase = 'lobby'
        self.lobby_end = time.time() + LOBBY_TIME
        self.night_killed_by_mafia = None
        self.night_killed_by_maniac = None
        self.night_saved = None
        self.votes = {}
        self.msg_id = None


def get_game(chat_id):
    return GAMES.get(chat_id)


def alive_players(game):
    return [uid for uid, p in game.players.items() if p['alive']]


def alive_by_role(game, role):
    return [uid for uid, p in game.players.items() if p['alive'] and p['role'] == role]


def count_mafia(game):
    return sum(1 for p in game.players.values()
               if p['alive'] and p['role'] in (ROLE_MAFIA, ROLE_DON))


def count_maniac(game):
    return sum(1 for p in game.players.values()
               if p['alive'] and p['role'] == ROLE_MANIAC)


def count_civils(game):
    return sum(1 for p in game.players.values()
               if p['alive'] and p['role'] not in (ROLE_MAFIA, ROLE_DON, ROLE_MANIAC))


# ==================== ЛОББИ ====================
@bot.message_handler(commands=['mafia'])
def cmd_mafia(m):
    chat_id = m.chat.id

    if m.chat.type == 'private':
        bot.reply_to(m, 'Эта команда работает только в группе.')
        return

    if chat_id in GAMES:
        bot.reply_to(m, 'Игра уже идёт в этом чате.')
        return

    game = Game(chat_id, m.from_user.id)
    GAMES[chat_id] = game

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Участвовать', callback_data='mafia_join'))

    text = (
        '🎭 МАФИЯ\n'
        '━━━━━━━━━━━━━━━\n\n'
        f'Набор игроков: {MIN_PLAYERS}–{MAX_PLAYERS}\n'
        'Время на сбор: 5 минут\n\n'
        f'Сейчас: 0/{MAX_PLAYERS}'
    )
    msg = bot.send_message(chat_id, text, reply_markup=kb)
    game.msg_id = msg.message_id

    def lobby_watch():
        while chat_id in GAMES:
            g = GAMES.get(chat_id)
            if not g or g.phase != 'lobby':
                return
            if time.time() >= g.lobby_end:
                start_game(chat_id)
                return
            time.sleep(2)

    threading.Thread(target=lobby_watch, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == 'mafia_join')
def cb_join(call):
    chat_id = call.message.chat.id
    game = get_game(chat_id)

    if not game or game.phase != 'lobby':
        bot.answer_callback_query(call.id, 'Набор закрыт')
        return

    uid = call.from_user.id

    if uid in game.players:
        bot.answer_callback_query(call.id, 'Ты уже в игре')
        return

    if len(game.players) >= MAX_PLAYERS:
        bot.answer_callback_query(call.id, 'Мест нет')
        return

    name = call.from_user.first_name or 'Игрок'
    game.players[uid] = {'name': name, 'role': None, 'alive': True}
    game.order.append(uid)

    text = (
        '🎭 МАФИЯ\n'
        '━━━━━━━━━━━━━━━\n\n'
        f'Набор игроков: {MIN_PLAYERS}–{MAX_PLAYERS}\n'
        'Время на сбор: 5 минут\n\n'
        f'Сейчас: {len(game.players)}/{MAX_PLAYERS}'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Участвовать', callback_data='mafia_join'))

    try:
        bot.edit_message_text(text, chat_id=chat_id,
                              message_id=game.msg_id, reply_markup=kb)
    except:
        pass

    bot.answer_callback_query(call.id, 'Ты в игре')

    if len(game.players) >= MAX_PLAYERS:
        start_game(chat_id)


# ==================== СТАРТ ====================
def start_game(chat_id):
    game = get_game(chat_id)
    if not game or game.phase != 'lobby':
        return

    n = len(game.players)

    if n < MIN_PLAYERS:
        bot.send_message(chat_id, f'❌ Недостаточно игроков ({n}/{MIN_PLAYERS}). Игра отменена.')
        GAMES.pop(chat_id, None)
        return

    roles = get_roles_for_count(n)
    random.shuffle(roles)

    for i, uid in enumerate(game.order):
        game.players[uid]['role'] = roles[i]

    game.phase = 'night'

    bot.send_message(
        chat_id,
        f'🎭 Игра началась!\n\n'
        f'Игроков: {n}\n'
        f'Роли разосланы в личку.\n\n'
        f'🌙 НОЧЬ. У всех есть {NIGHT_TIME} секунд.'
    )

    for uid, p in game.players.items():
        try:
            text = (
                f'{ROLE_EMOJI[p["role"]]} Твоя роль: {p["role"]}\n\n'
                f'{ROLE_DESC[p["role"]]}\n\n'
                f'Игроки:\n'
            )
            for other_uid, other in game.players.items():
                if other_uid != uid:
                    text += f'• {other["name"]}\n'
            bot.send_message(uid, text)
        except:
            pass

    start_night(chat_id)


# ==================== НОЧЬ ====================
def start_night(chat_id):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = 'night'
    game.night_killed_by_mafia = None
    game.night_killed_by_maniac = None
    game.night_saved = None
    game.votes = {}

    mafia_ids = alive_by_role(game, ROLE_MAFIA) + alive_by_role(game, ROLE_DON)
    for uid in mafia_ids:
        send_night_action(uid, game, 'mafia')

    for uid in alive_by_role(game, ROLE_COMISSAR):
        send_night_action(uid, game, 'comissar')

    for uid in alive_by_role(game, ROLE_DOCTOR):
        send_night_action(uid, game, 'doctor')

    for uid in alive_by_role(game, ROLE_MANIAC):
        send_night_action(uid, game, 'maniac')

    def night_watch():
        time.sleep(NIGHT_TIME)
        g = get_game(chat_id)
        if g and g.phase == 'night':
            resolve_night(chat_id)

    threading.Thread(target=night_watch, daemon=True).start()


def send_night_action(uid, game, action):
    try:
        targets = []
        if action == 'mafia':
            for other_uid, p in game.players.items():
                if p['alive'] and p['role'] not in (ROLE_MAFIA, ROLE_DON):
                    targets.append(other_uid)
            title = '🔫 Кого убить?'
        elif action == 'comissar':
            for other_uid, p in game.players.items():
                if p['alive'] and other_uid != uid:
                    targets.append(other_uid)
            title = '🕵️ Кого проверить?'
        elif action == 'doctor':
            for other_uid, p in game.players.items():
                if p['alive']:
                    targets.append(other_uid)
            title = '💊 Кого лечить?'
        elif action == 'maniac':
            for other_uid, p in game.players.items():
                if p['alive'] and other_uid != uid:
                    targets.append(other_uid)
            title = '🔪 Кого убить?'
        else:
            return

        if not targets:
            return

        kb = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for t in targets:
            buttons.append(types.InlineKeyboardButton(
                game.players[t]['name'],
                callback_data=f'night_{action}_{t}'
            ))
        kb.add(*buttons)

        bot.send_message(uid, f'{title}\n\nУ тебя {NIGHT_TIME} секунд.',
                         reply_markup=kb)
    except Exception as e:
        print('send_night_action error:', e)


@bot.callback_query_handler(func=lambda c: c.data.startswith('night_'))
def cb_night(call):
    parts = call.data.split('_')
    if len(parts) != 3:
        return

    action = parts[1]
    target_id = int(parts[2])
    uid = call.from_user.id

    game = None
    for cid, g in GAMES.items():
        if uid in g.players:
            game = g
            break

    if not game or game.phase != 'night':
        bot.answer_callback_query(call.id, 'Сейчас не ночь')
        return

    if target_id not in game.players or not game.players[target_id]['alive']:
        bot.answer_callback_query(call.id, 'Этот игрок недоступен')
        return

    p = game.players[uid]

    if action == 'mafia' and p['role'] not in (ROLE_MAFIA, ROLE_DON):
        bot.answer_callback_query(call.id, 'Ты не мафия')
        return
    if action == 'comissar' and p['role'] != ROLE_COMISSAR:
        bot.answer_callback_query(call.id, 'Ты не комиссар')
        return
    if action == 'doctor' and p['role'] != ROLE_DOCTOR:
        bot.answer_callback_query(call.id, 'Ты не доктор')
        return
    if action == 'maniac' and p['role'] != ROLE_MANIAC:
        bot.answer_callback_query(call.id, 'Ты не маньяк')
        return

    if action == 'mafia':
        game.night_killed_by_mafia = target_id
    elif action == 'maniac':
        game.night_killed_by_maniac = target_id
    elif action == 'doctor':
        game.night_saved = target_id
    elif action == 'comissar':
        target_role = game.players[target_id]['role']
        is_mafia = target_role in (ROLE_MAFIA, ROLE_DON)
        if target_role == ROLE_DON:
            is_mafia = False
        answer = '🔫 Мафия!' if is_mafia else '👤 Мирный'
        bot.answer_callback_query(call.id, answer, show_alert=True)
        try:
            bot.edit_message_text(
                f'🕵️ Проверка: {game.players[target_id]["name"]} — {answer}',
                chat_id=uid,
                message_id=call.message.message_id
            )
        except:
            pass
        return

    bot.answer_callback_query(call.id, f'Выбрано: {game.players[target_id]["name"]}')
    try:
        bot.edit_message_text(
            f'Твой выбор: {game.players[target_id]["name"]}',
            chat_id=uid,
            message_id=call.message.message_id
        )
    except:
        pass


# ==================== УТРО ====================
def resolve_night(chat_id):
    game = get_game(chat_id)
    if not game or game.phase != 'night':
        return

    killed = set()

    if game.night_killed_by_mafia and game.night_killed_by_mafia != game.night_saved:
        killed.add(game.night_killed_by_mafia)

    if game.night_killed_by_maniac and game.night_killed_by_maniac != game.night_saved:
        killed.add(game.night_killed_by_maniac)

    for uid in killed:
        if uid in game.players and game.players[uid]['alive']:
            game.players[uid]['alive'] = False

    if killed:
        names = ', '.join(game.players[u]['name'] for u in killed if u in game.players)
        bot.send_message(chat_id, f'☀️ Утро.\n\nЭтой ночью погибли: {names}')
    else:
        bot.send_message(chat_id, '☀️ Утро.\n\nЭтой ночью никто не погиб.')

    winner = check_win(game)
    if winner:
        end_game(chat_id, winner)
        return

    start_day(chat_id)


# ==================== ДЕНЬ ====================
def start_day(chat_id):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = 'day'
    game.votes = {}

    alive = alive_players(game)
    text = (
        '🗣 ДЕНЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        f'Живых: {len(alive)}\n\n'
        f'Обсуждение {DAY_DISCUSS} секунд, потом голосование.'
    )
    bot.send_message(chat_id, text)

    def day_watch():
        time.sleep(DAY_DISCUSS)
        g = get_game(chat_id)
        if g and g.phase == 'day':
            start_vote(chat_id)

    threading.Thread(target=day_watch, daemon=True).start()


def start_vote(chat_id):
    game = get_game(chat_id)
    if not game or game.phase != 'day':
        return

    game.votes = {}

    alive = alive_players(game)
    if not alive:
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for uid in alive:
        buttons.append(types.InlineKeyboardButton(
            game.players[uid]['name'],
            callback_data=f'vote_{uid}'
        ))
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton('Пропустить', callback_data='vote_skip'))

    bot.send_message(
        chat_id,
        f'🗳 ГОЛОСОВАНИЕ\n\nУ тебя {DAY_VOTE} секунд.\nБольшинство голосов — казнь.',
        reply_markup=kb
    )

    def vote_watch():
        time.sleep(DAY_VOTE)
        g = get_game(chat_id)
        if g and g.phase == 'day':
            resolve_vote(chat_id)

    threading.Thread(target=vote_watch, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith('vote_'))
def cb_vote(call):
    uid = call.from_user.id

    game = None
    for cid, g in GAMES.items():
        if uid in g.players and g.players[uid]['alive']:
            game = g
            break

    if not game or game.phase != 'day':
        bot.answer_callback_query(call.id, 'Сейчас не день')
        return

    if uid in game.votes:
        bot.answer_callback_query(call.id, 'Ты уже голосовал')
        return

    val = call.data.replace('vote_', '')
    if val == 'skip':
        game.votes[uid] = 'skip'
        bot.answer_callback_query(call.id, 'Пропущено')
    else:
        try:
            target = int(val)
        except:
            return
        if target not in game.players or not game.players[target]['alive']:
            bot.answer_callback_query(call.id, 'Недоступно')
            return
        game.votes[uid] = target
        bot.answer_callback_query(call.id, f'Голос за {game.players[target]["name"]}')


def resolve_vote(chat_id):
    game = get_game(chat_id)
    if not game or game.phase != 'day':
        return

    counts = {}
    for voter, target in game.votes.items():
        if target == 'skip':
            continue
        counts[target] = counts.get(target, 0) + 1

    if not counts:
        bot.send_message(chat_id, 'Никто не проголосовал. Ночь.')
        game.phase = 'night'
        start_night(chat_id)
        return

    max_votes = max(counts.values())
    leaders = [t for t, v in counts.items() if v == max_votes]

    if len(leaders) > 1:
        names = ', '.join(game.players[u]['name'] for u in leaders)
        bot.send_message(chat_id, f'Ничья: {names}. Никто не казнён. Ночь.')
        game.phase = 'night'
        start_night(chat_id)
        return

    victim = leaders[0]
    game.players[victim]['alive'] = False
    bot.send_message(
        chat_id,
        f'⚖️ Казнён: {game.players[victim]["name"]}\n'
        f'Его роль: {game.players[victim]["role"]}'
    )

    winner = check_win(game)
    if winner:
        end_game(chat_id, winner)
        return

    game.phase = 'night'
    start_night(chat_id)


# ==================== ПОБЕДА ====================
def check_win(game):
    mafia = count_mafia(game)
    maniac = count_maniac(game)
    civils = count_civils(game)
    alive = len(alive_players(game))

    if maniac >= 1 and alive == 1 and maniac == alive:
        return 'maniac'

    if mafia >= 1 and mafia >= civils + maniac:
        return 'mafia'

    if mafia == 0 and maniac == 0:
        return 'city'

    return None


def end_game(chat_id, winner):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = 'end'

    if winner == 'mafia':
        text = '🎉 ПОБЕДА МАФИИ!\n\nМафия захватила город.'
    elif winner == 'maniac':
        text = '🔪 ПОБЕДА МАНЬЯКА!\n\nОн остался один.'
    else:
        text = '🏆 ПОБЕДА ГОРОДА!\n\nМафия и маньяк мертвы.'

    text += '\n\nРоли:\n'
    for uid, p in game.players.items():
        status = 'жив' if p['alive'] else 'мёртв'
        text += f'{ROLE_EMOJI[p["role"]]} {p["name"]} — {p["role"]} ({status})\n'

    bot.send_message(chat_id, text)
    GAMES.pop(chat_id, None)


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('Mafia bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
