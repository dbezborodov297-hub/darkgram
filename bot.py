import telebot
import time
import threading
import random
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ==================== НАСТРОЙКИ ====================
TOKEN = '8514412667:AAEROrRRLNegCw2Z3caY4ek4rL4dAbQrkEY'

MIN_PLAYERS = 4
MAX_PLAYERS = 20
LOBBY_TIME = 5 * 60
NIGHT_TIME = 60
DAY_DISCUSS = 90
DAY_VOTE = 60

SHIELD_PRICE = 100
LUCKY_PRICE = 65
WIN_REWARD = 10

PROFILES_FILE = 'profiles.json'

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)
GAMES = {}
PROFILES = {}
PROFILES_LOCK = threading.Lock()

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
ROLE_ZELENSKY = 'Зеленский'
ROLE_CIVIL = 'Мирный'

ROLE_EMOJI = {
    ROLE_MAFIA: '🔫', ROLE_DON: '👑', ROLE_COMISSAR: '🕵️',
    ROLE_DOCTOR: '💊', ROLE_MANIAC: '🔪', ROLE_ZELENSKY: '🇺🇦',
    ROLE_CIVIL: '👤',
}

ROLE_DESC = {
    ROLE_MAFIA: 'Ночью вместе с мафией выбираешь жертву.',
    ROLE_DON: 'Главный мафии. Комиссар видит тебя как мирного.',
    ROLE_COMISSAR: 'Ночью проверяешь одного игрока — мафия или нет.',
    ROLE_DOCTOR: 'Ночью лечишь одного игрока.',
    ROLE_MANIAC: 'Ночью убиваешь. Побеждаешь, если остаёшься один.',
    ROLE_ZELENSKY: 'Нейтрал. Ночью глушишь игрока — он пропустит следующую ночь. Одноразово — граната глушит третьего.',
    ROLE_CIVIL: 'Ночью спишь. Днём ищешь мафию.',
}


def get_roles_for_count(n):
    if n == 4:
        return [ROLE_MAFIA, ROLE_COMISSAR, ROLE_CIVIL, ROLE_CIVIL]
    if n == 5:
        return [ROLE_DON, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_CIVIL, ROLE_CIVIL]
    if n == 6:
        return [ROLE_DON, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_CIVIL]
    if n == 7:
        return [ROLE_DON, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_CIVIL, ROLE_CIVIL]
    if n == 8:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_CIVIL, ROLE_CIVIL]
    if n == 9:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 2
    if n == 10:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 3
    if n == 11:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 3
    if n == 12:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 4
    if n == 13:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 5
    if n == 14:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 5
    if n == 15:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 6
    if n == 16:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 7
    if n == 17:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 8
    if n == 18:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 8
    if n == 19:
        return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 9
    return [ROLE_DON, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_MAFIA, ROLE_COMISSAR, ROLE_DOCTOR, ROLE_MANIAC, ROLE_ZELENSKY] + [ROLE_CIVIL] * 10


# ==================== ПРОФИЛИ ====================
def load_profiles():
    global PROFILES
    if not os.path.exists(PROFILES_FILE):
        PROFILES = {}
        return
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            PROFILES = json.load(f)
    except:
        PROFILES = {}


def save_profiles():
    try:
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(PROFILES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('save_profiles err:', e)


def get_profile(uid):
    key = str(uid)
    if key not in PROFILES:
        PROFILES[key] = {
            'diamonds': 0,
            'shield': False,
            'lucky': False,
            'wins': 0,
        }
    return PROFILES[key]


def add_diamonds(uid, amount):
    with PROFILES_LOCK:
        p = get_profile(uid)
        p['diamonds'] = p.get('diamonds', 0) + amount
        save_profiles()


def buy_item(uid, item):
    with PROFILES_LOCK:
        p = get_profile(uid)
        if item == 'shield':
            if p.get('shield'):
                return 'already'
            if p.get('diamonds', 0) < SHIELD_PRICE:
                return 'no_money'
            p['diamonds'] -= SHIELD_PRICE
            p['shield'] = True
            save_profiles()
            return 'ok'
        if item == 'lucky':
            if p.get('lucky'):
                return 'already'
            if p.get('diamonds', 0) < LUCKY_PRICE:
                return 'no_money'
            p['diamonds'] -= LUCKY_PRICE
            p['lucky'] = True
            save_profiles()
            return 'ok'
    return 'error'


load_profiles()


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
        self.night_muted = {}
        self.zelensky_used_grenade = False
        self.votes = {}
        self.msg_id = None


def get_game(chat_id):
    return GAMES.get(chat_id)


def alive_players(game):
    return [uid for uid, p in game.players.items() if p['alive']]


def alive_by_role(game, role):
    return [uid for uid, p in game.players.items() if p['alive'] and p['role'] == role]


def count_mafia(game):
    return sum(1 for p in game.players.values() if p['alive'] and p['role'] in (ROLE_MAFIA, ROLE_DON))


def count_maniac(game):
    return sum(1 for p in game.players.values() if p['alive'] and p['role'] == ROLE_MANIAC)


def count_civils(game):
    return sum(1 for p in game.players.values()
               if p['alive'] and p['role'] not in (ROLE_MAFIA, ROLE_DON, ROLE_MANIAC, ROLE_ZELENSKY))


# ==================== /start ====================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('Как играть', callback_data='mm_how'),
        types.InlineKeyboardButton('Все роли и способности', callback_data='mm_roles'),
        types.InlineKeyboardButton('Правила', callback_data='mm_rules'),
        types.InlineKeyboardButton('Конфиденциальность', callback_data='mm_privacy'),
        types.InlineKeyboardButton('Магазин', callback_data='mm_shop'),
        types.InlineKeyboardButton('Мои алмазы', callback_data='mm_balance'),
    )
    text = (
        '🎭 МАФИЯ DARKGRAM\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Добро пожаловать в игру!\n\n'
        'Это бот для игры в мафию в группах.\n'
        'Побеждай — получай алмазы — покупай предметы.\n\n'
        '👇 Выбери раздел:'
    )
    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.message_handler(commands=['help'])
def cmd_help(m):
    cmd_start(m)


# ==================== РАЗДЕЛЫ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'mm_how')
def cb_how(call):
    text = (
        '📖 КАК ИГРАТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '1️⃣ Добавь бота в группу\n\n'
        '2️⃣ Напиши /mafia — начнётся набор (5 минут)\n\n'
        f'3️⃣ Жми «Участвовать» (нужно {MIN_PLAYERS}–{MAX_PLAYERS} игроков)\n\n'
        '4️⃣ Роли придут каждому в личку\n\n'
        '5️⃣ Ночью роли действуют в личке\n\n'
        '6️⃣ Днём все голосуют в группе\n\n'
        '7️⃣ Игра идёт, пока одна сторона не победит\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🎯 ПОБЕДА:\n'
        '• Мафия — если её ≥ остальных\n'
        '• Город — если вся мафия мертва\n'
        '• Маньяк — если остался один\n'
        '• Зеленский — выжить до конца\n\n'
        '━━━━━━━━━━━━━━━\n'
        '💎 АЛМАЗЫ:\n'
        f'• +{WIN_REWARD} за победу\n'
        '• Тратятся в магазине'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_roles')
def cb_roles(call):
    text = (
        '🎭 ВСЕ РОЛИ И СПОСОБНОСТИ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '🔫 МАФИЯ\n'
        'Ночью вместе с другими мафиози выбирает жертву. '
        'Знает своих. Цель — убить всех мирных.\n\n'
        '👑 ДОН\n'
        'Главный мафии. Если комиссар проверит — увидит как мирного. '
        'Ночью выбирает жертву вместе с мафией.\n\n'
        '🕵️ КОМИССАР\n'
        'Ночью проверяет одного игрока. '
        'Узнаёт — мафия он или нет.\n\n'
        '💊 ДОКТОР\n'
        'Ночью лечит одного игрока. '
        'Если мафия выбрала его — выживет.\n\n'
        '🔪 МАНЬЯК\n'
        'Нейтрал. Ночью убивает всех подряд. '
        'Побеждает, если останется один.\n\n'
        '🇺🇦 ЗЕЛЕНСКИЙ\n'
        'Нейтрал. Ночью выбирает игрока и глушит его — '
        'он пропускает следующую ночь (не может действовать).\n'
        '⚠️ Одноразово: граната — глушит третьего игрока.\n\n'
        '👤 МИРНЫЙ\n'
        'Ночью спит. Днём ищет мафию и голосует.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🛒 ПРЕДМЕТЫ В МАГАЗИНЕ\n\n'
        '🛡 ЩИТ — 100 💎\n'
        'Спасает от убийства ночью. На 1 игру.\n\n'
        '🍀 ВЕЗУНЧИК — 65 💎\n'
        'Двойной голос днём (твой голос = 2).\n'
        'После смерти (убили или казнили) — забираешь игрока с собой. На 1 игру.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🎯 УСЛОВИЯ ПОБЕДЫ\n'
        '• 🎉 Мафия — если мафии ≥ остальных\n'
        '• 🏆 Город — если вся мафия и маньяк мертвы\n'
        '• 🔪 Маньяк — если остался один\n'
        '• 🇺🇦 Зеленский — если дожил до конца'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_rules')
def cb_rules(call):
    text = (
        '📜 ПРАВИЛА ИГРЫ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '✅ МОЖНО:\n'
        '• Играть честно\n'
        '• Обсуждать в чате днём\n'
        '• Использовать все роли\n\n'
        '❌ НЕЛЬЗЯ:\n'
        '• Раскрывать свою роль\n'
        '• Спамить командами\n'
        '• Оскорблять всерьёз\n'
        '• Играть с нескольких аккаунтов\n\n'
        '━━━━━━━━━━━━━━━\n'
        '⚙️ ПО ФАЗАМ:\n\n'
        '🌙 НОЧЬ (60 сек)\n'
        '• Мафия выбирает жертву\n'
        '• Комиссар проверяет\n'
        '• Доктор лечит\n'
        '• Маньяк убивает\n'
        '• Зеленский глушит\n\n'
        '☀️ ДЕНЬ (90 сек + 60 сек голосование)\n'
        '• Обсуждаете\n'
        '• Голосуете кнопками\n'
        '• Большинство = казнь\n\n'
        '━━━━━━━━━━━━━━━\n'
        '⚠️ ВАЖНО:\n'
        '• Игра только в группе\n'
        f'• Нужно {MIN_PLAYERS}–{MAX_PLAYERS} игроков\n'
        '• Набор 5 минут\n'
        '• Если меньше 4 — отмена'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_privacy')
def cb_privacy(call):
    text = (
        '🔒 КОНФИДЕНЦИАЛЬНОСТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '❌ Бот НЕ:\n'
        '• Не читает личные сообщения\n'
        '• Не собирает личные данные\n'
        '• Не сохраняет переписку\n'
        '• Не передаёт данные третьим лицам\n'
        '• Не рекламирует\n\n'
        '✅ Бот хранит:\n'
        '• Имя и ID (для отображения)\n'
        '• Алмазы (игровая валюта)\n'
        '• Купленные предметы (щит, везунчик)\n'
        '• Количество побед\n\n'
        '━━━━━━━━━━━━━━━\n'
        '⚠️ Бот НЕ видит:\n'
        '• Твои личные переписки\n'
        '• Сообщения в других чатах\n'
        '• Голосовые, фото, видео\n\n'
        'Бот реагирует ТОЛЬКО на команды, '
        'которые ты пишешь сам.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '📁 Данные хранятся в файле бота.\n'
        'В любой момент можно запросить удаление.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_shop')
def cb_shop_btn(call):
    uid = call.from_user.id
    p = get_profile(uid)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(f'🛡 Щит — {SHIELD_PRICE} 💎', callback_data='shop_shield'))
    kb.add(types.InlineKeyboardButton(f'🍀 Везунчик — {LUCKY_PRICE} 💎', callback_data='shop_lucky'))
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    text = (
        '🛒 МАГАЗИН\n━━━━━━━━━━━━━━━\n\n'
        f'💎 Твои алмазы: {p.get("diamonds", 0)}\n\n'
        f'🛡 Щит — {SHIELD_PRICE} 💎\n'
        'Спасает от убийства. На 1 игру.\n\n'
        f'🍀 Везунчик — {LUCKY_PRICE} 💎\n'
        'Двойной голос + забираешь игрока после смерти. На 1 игру.\n\n'
        f'Статус:\n'
        f'Щит: {"✅" if p.get("shield") else "❌"}\n'
        f'Везунчик: {"✅" if p.get("lucky") else "❌"}\n'
        f'Побед: {p.get("wins", 0)}'
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_balance')
def cb_balance_btn(call):
    p = get_profile(call.from_user.id)
    text = (
        '💎 МОИ АЛМАЗЫ\n━━━━━━━━━━━━━━━\n\n'
        f'💎 Алмазов: {p.get("diamonds", 0)}\n'
        f'🛡 Щит: {"✅" if p.get("shield") else "❌"}\n'
        f'🍀 Везунчик: {"✅" if p.get("lucky") else "❌"}\n'
        f'🏆 Побед: {p.get("wins", 0)}'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='mm_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'mm_back')
def cb_back(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('Как играть', callback_data='mm_how'),
        types.InlineKeyboardButton('Все роли и способности', callback_data='mm_roles'),
        types.InlineKeyboardButton('Правила', callback_data='mm_rules'),
        types.InlineKeyboardButton('Конфиденциальность', callback_data='mm_privacy'),
        types.InlineKeyboardButton('Магазин', callback_data='mm_shop'),
        types.InlineKeyboardButton('Мои алмазы', callback_data='mm_balance'),
    )
    text = '🎭 МАФИЯ DARKGRAM\n━━━━━━━━━━━━━━━\n\n👇 Выбери раздел:'
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== ЛОББИ ====================
@bot.message_handler(commands=['mafia'])
def cmd_mafia(m):
    chat_id = m.chat.id
    if m.chat.type == 'private':
        bot.reply_to(m, 'Только в группе.')
        return
    if chat_id in GAMES:
        bot.reply_to(m, 'Игра уже идёт.')
        return

    game = Game(chat_id, m.from_user.id)
    GAMES[chat_id] = game

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Участвовать', callback_data='mafia_join'))

    text = (
        '🎭 МАФИЯ\n━━━━━━━━━━━━━━━\n\n'
        f'Для начала игры {MIN_PLAYERS} игрока\n'
        f'Макс {MAX_PLAYERS} игроков\n\n'
        f'Время на сбор: 5 минут\n\n'
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
        '🎭 МАФИЯ\n━━━━━━━━━━━━━━━\n\n'
        f'Для начала игры {MIN_PLAYERS} игрока\n'
        f'Макс {MAX_PLAYERS} игроков\n\n'
        f'Время на сбор: 5 минут\n\n'
        f'Сейчас: {len(game.players)}/{MAX_PLAYERS}'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Участвовать', callback_data='mafia_join'))
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=game.msg_id, reply_markup=kb)
    except:
        pass
    bot.answer_callback_query(call.id, 'Ты в игре')

    if len(game.players) >= MAX_PLAYERS:
        start_game(chat_id)


def start_game(chat_id):
    game = get_game(chat_id)
    if not game or game.phase != 'lobby':
        return
    n = len(game.players)
    if n == 0:
        bot.send_message(chat_id, '❌ Никто не зашёл. Игра отменена.')
        GAMES.pop(chat_id, None)
        return
    if n < MIN_PLAYERS:
        bot.send_message(chat_id, f'❌ Мало игроков ({n}/{MIN_PLAYERS}). Игра отменена.')
        GAMES.pop(chat_id, None)
        return

    roles = get_roles_for_count(n)
    random.shuffle(roles)
    for i, uid in enumerate(game.order):
        game.players[uid]['role'] = roles[i]

    game.phase = 'night'
    bot.send_message(chat_id,
        f'🎭 Игра началась!\nИгроков: {n}\n\n🌙 НОЧЬ. {NIGHT_TIME} секунд.')

    for uid, p in game.players.items():
        try:
            prof = get_profile(uid)
            extras = []
            if prof.get('shield'):
                extras.append('🛡 Щит активен')
            if prof.get('lucky'):
                extras.append('🍀 Везунчик активен')

            text = f'{ROLE_EMOJI[p["role"]]} Твоя роль: {p["role"]}\n\n{ROLE_DESC[p["role"]]}\n\n'
            if extras:
                text += '\n'.join(extras) + '\n\n'
            text += 'Игроки:\n'
            for o, other in game.players.items():
                if o != uid:
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

    muted_now = set(game.night_muted.keys())

    for uid in alive_by_role(game, ROLE_MAFIA) + alive_by_role(game, ROLE_DON):
        if uid not in muted_now:
            send_night_action(uid, game, 'mafia')
    for uid in alive_by_role(game, ROLE_COMISSAR):
        if uid not in muted_now:
            send_night_action(uid, game, 'comissar')
    for uid in alive_by_role(game, ROLE_DOCTOR):
        if uid not in muted_now:
            send_night_action(uid, game, 'doctor')
    for uid in alive_by_role(game, ROLE_MANIAC):
        if uid not in muted_now:
            send_night_action(uid, game, 'maniac')
    for uid in alive_by_role(game, ROLE_ZELENSKY):
        if uid not in muted_now:
            send_zelensky_action(uid, game)

    for uid in muted_now:
        if uid in game.players and game.players[uid]['alive']:
            try:
                bot.send_message(uid, '⚡ Ты оглушён и пропускаешь эту ночь.')
            except:
                pass

    game.night_muted = {}

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
            for o, p in game.players.items():
                if p['alive'] and p['role'] not in (ROLE_MAFIA, ROLE_DON):
                    targets.append(o)
            title = '🔫 Кого убить?'
        elif action == 'comissar':
            for o, p in game.players.items():
                if p['alive'] and o != uid:
                    targets.append(o)
            title = '🕵️ Кого проверить?'
        elif action == 'doctor':
            for o, p in game.players.items():
                if p['alive']:
                    targets.append(o)
            title = '💊 Кого лечить?'
        elif action == 'maniac':
            for o, p in game.players.items():
                if p['alive'] and o != uid:
                    targets.append(o)
            title = '🔪 Кого убить?'
        else:
            return
        if not targets:
            return

        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(game.players[t]['name'], callback_data=f'night_{action}_{t}') for t in targets]
        kb.add(*btns)
        bot.send_message(uid, f'{title}\n\n{NIGHT_TIME} секунд.', reply_markup=kb)
    except Exception as e:
        print('night err:', e)


def send_zelensky_action(uid, game):
    try:
        targets = [o for o, p in game.players.items() if p['alive'] and o != uid]
        if not targets:
            return
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(game.players[t]['name'], callback_data=f'night_mute_{t}') for t in targets]
        kb.add(*btns)
        if not game.zelensky_used_grenade:
            kb.add(types.InlineKeyboardButton('💣 Кинуть гранату (1 раз)', callback_data='zelensky_grenade'))
        bot.send_message(uid,
            f'🇺🇦 Зеленский: кого глушить?\nОн пропустит следующую ночь.\n\n{NIGHT_TIME} секунд.',
            reply_markup=kb)
    except Exception as e:
        print('zelensky err:', e)


@bot.callback_query_handler(func=lambda c: c.data == 'zelensky_grenade')
def cb_zelensky_grenade(call):
    uid = call.from_user.id
    game = None
    for cid, g in GAMES.items():
        if uid in g.players:
            game = g
            break
    if not game or game.phase != 'night':
        bot.answer_callback_query(call.id, 'Сейчас не ночь')
        return
    if game.zelensky_used_grenade:
        bot.answer_callback_query(call.id, 'Граната использована')
        return
    targets = [o for o, p in game.players.items() if p['alive'] and o != uid]
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(game.players[t]['name'], callback_data=f'night_grenade_{t}') for t in targets]
    kb.add(*btns)
    bot.answer_callback_query(call.id)
    bot.send_message(uid, '💣 Кого оглушить гранатой?', reply_markup=kb)


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
        bot.answer_callback_query(call.id, 'Недоступно')
        return

    p = game.players[uid]
    if action == 'mafia' and p['role'] not in (ROLE_MAFIA, ROLE_DON):
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return
    if action == 'comissar' and p['role'] != ROLE_COMISSAR:
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return
    if action == 'doctor' and p['role'] != ROLE_DOCTOR:
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return
    if action == 'maniac' and p['role'] != ROLE_MANIAC:
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return
    if action == 'mute' and p['role'] != ROLE_ZELENSKY:
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return
    if action == 'grenade' and p['role'] != ROLE_ZELENSKY:
        bot.answer_callback_query(call.id, 'Не твоя роль')
        return

    if action == 'mafia':
        game.night_killed_by_mafia = target_id
    elif action == 'maniac':
        game.night_killed_by_maniac = target_id
    elif action == 'doctor':
        game.night_saved = target_id
    elif action == 'mute':
        game.night_muted[target_id] = True
        bot.answer_callback_query(call.id, f'Заглушён: {game.players[target_id]["name"]}')
        try:
            bot.edit_message_text(f'⚡ Заглушён: {game.players[target_id]["name"]}',
                                  chat_id=uid, message_id=call.message.message_id)
        except:
            pass
        return
    elif action == 'grenade':
        game.night_muted[target_id] = True
        game.zelensky_used_grenade = True
        bot.answer_callback_query(call.id, f'💣 Граната: {game.players[target_id]["name"]}')
        try:
            bot.edit_message_text(f'💣 Оглушён: {game.players[target_id]["name"]}',
                                  chat_id=uid, message_id=call.message.message_id)
        except:
            pass
        return
    elif action == 'comissar':
        tr = game.players[target_id]['role']
        is_mafia = tr in (ROLE_MAFIA, ROLE_DON)
        if tr == ROLE_DON:
            is_mafia = False
        answer = '🔫 Мафия!' if is_mafia else '👤 Мирный'
        bot.answer_callback_query(call.id, answer, show_alert=True)
        try:
            bot.edit_message_text(f'🕵️ {game.players[target_id]["name"]} — {answer}',
                                  chat_id=uid, message_id=call.message.message_id)
        except:
            pass
        return

    bot.answer_callback_query(call.id, f'Выбрано: {game.players[target_id]["name"]}')
    try:
        bot.edit_message_text(f'Выбор: {game.players[target_id]["name"]}',
                              chat_id=uid, message_id=call.message.message_id)
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

    for uid in list(killed):
        prof = get_profile(uid)
        if prof.get('shield'):
            prof['shield'] = False
            with PROFILES_LOCK:
                save_profiles()
            killed.discard(uid)
            try:
                bot.send_message(uid, '🛡 Щит спас тебя от смерти!')
            except:
                pass

    for uid in killed:
        if uid in game.players and game.players[uid]['alive']:
            game.players[uid]['alive'] = False

    if killed:
        names = ', '.join(game.players[u]['name'] for u in killed if u in game.players)
        bot.send_message(chat_id, f'☀️ Утро. Погибли: {names}')
    else:
        bot.send_message(chat_id, '☀️ Утро. Никто не погиб.')

    for uid in killed:
        prof = get_profile(uid)
        if prof.get('lucky') and uid in game.players:
            prof['lucky'] = False
            with PROFILES_LOCK:
                save_profiles()
            ask_lucky_revenge(uid, game)

    winner = check_win(game)
    if winner:
        end_game(chat_id, winner)
        return
    start_day(chat_id)


def ask_lucky_revenge(uid, game):
    targets = [o for o, p in game.players.items() if p['alive'] and o != uid]
    if not targets:
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(game.players[t]['name'], callback_data=f'lucky_kill_{t}') for t in targets]
    kb.add(*btns)
    try:
        bot.send_message(uid, '🍀 Ты погиб. Забрать кого-то с собой?', reply_markup=kb)
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('lucky_kill_'))
def cb_lucky_kill(call):
    uid = call.from_user.id
    target_id = int(call.data.replace('lucky_kill_', ''))
    game = None
    for cid, g in GAMES.items():
        if uid in g.players:
            game = g
            break
    if not game:
        return
    if target_id not in game.players or not game.players[target_id]['alive']:
        bot.answer_callback_query(call.id, 'Недоступно')
        return
    game.players[target_id]['alive'] = False
    bot.answer_callback_query(call.id, 'Забрал с собой')
    bot.send_message(game.chat_id,
        f'💀 {game.players[uid]["name"]} забрал с собой {game.players[target_id]["name"]}!')
    try:
        bot.edit_message_text(f'Ты забрал {game.players[target_id]["name"]}',
                              chat_id=uid, message_id=call.message.message_id)
    except:
        pass
    winner = check_win(game)
    if winner:
        end_game(game.chat_id, winner)


# ==================== ДЕНЬ ====================
def start_day(chat_id):
    game = get_game(chat_id)
    if not game:
        return
    game.phase = 'day'
    game.votes = {}
    alive = alive_players(game)
    bot.send_message(chat_id, f'🗣 ДЕНЬ. Живых: {len(alive)}\nОбсуждение {DAY_DISCUSS} сек.')

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
    btns = [types.InlineKeyboardButton(game.players[uid]['name'], callback_data=f'vote_{uid}') for uid in alive]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton('Пропустить', callback_data='vote_skip'))
    bot.send_message(chat_id, f'🗳 ГОЛОСОВАНИЕ. {DAY_VOTE} секунд.', reply_markup=kb)

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
        bot.answer_callback_query(call.id, 'Уже голосовал')
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
    for v, t in game.votes.items():
        if t == 'skip':
            continue
        prof = get_profile(v)
        weight = 2 if prof.get('lucky') else 1
        counts[t] = counts.get(t, 0) + weight

    if not counts:
        bot.send_message(chat_id, 'Никто не голосовал. Ночь.')
        start_night(chat_id)
        return
    max_v = max(counts.values())
    leaders = [t for t, v in counts.items() if v == max_v]
    if len(leaders) > 1:
        names = ', '.join(game.players[u]['name'] for u in leaders)
        bot.send_message(chat_id, f'Ничья: {names}. Ночь.')
        start_night(chat_id)
        return
    victim = leaders[0]
    game.players[victim]['alive'] = False
    bot.send_message(chat_id, f'⚖️ Казнён: {game.players[victim]["name"]}\nРоль: {game.players[victim]["role"]}')

    prof = get_profile(victim)
    if prof.get('lucky'):
        prof['lucky'] = False
        with PROFILES_LOCK:
            save_profiles()
        ask_lucky_revenge(victim, game)

    winner = check_win(game)
    if winner:
        end_game(chat_id, winner)
        return
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
        text = '🎉 ПОБЕДА МАФИИ!'
        winners = [u for u, p in game.players.items() if p['role'] in (ROLE_MAFIA, ROLE_DON)]
    elif winner == 'maniac':
        text = '🔪 ПОБЕДА МАНЬЯКА!'
        winners = [u for u, p in game.players.items() if p['role'] == ROLE_MANIAC]
    else:
        text = '🏆 ПОБЕДА ГОРОДА!'
        winners = [u for u, p in game.players.items()
                   if p['role'] not in (ROLE_MAFIA, ROLE_DON, ROLE_MANIAC)]

    text += f'\n\n💎 +{WIN_REWARD} алмазов победителям.\n\nРоли:\n'
    for uid, p in game.players.items():
        status = 'жив' if p['alive'] else 'мёртв'
        text += f'{ROLE_EMOJI[p["role"]]} {p["name"]} — {p["role"]} ({status})\n'

    bot.send_message(chat_id, text)

    for uid in winners:
        add_diamonds(uid, WIN_REWARD)
        with PROFILES_LOCK:
            p = get_profile(uid)
            p['wins'] = p.get('wins', 0) + 1
            save_profiles()
        try:
            bot.send_message(uid, f'💎 +{WIN_REWARD} алмазов за победу!')
        except:
            pass

    GAMES.pop(chat_id, None)


# ==================== МАГАЗИН ====================
@bot.message_handler(commands=['shop'])
def cmd_shop(m):
    uid = m.from_user.id
    p = get_profile(uid)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(f'🛡 Щит — {SHIELD_PRICE} 💎', callback_data='shop_shield'))
    kb.add(types.InlineKeyboardButton(f'🍀 Везунчик — {LUCKY_PRICE} 💎', callback_data='shop_lucky'))
    text = (
        '🛒 МАГАЗИН\n━━━━━━━━━━━━━━━\n\n'
        f'💎 Твои алмазы: {p.get("diamonds", 0)}\n\n'
        f'🛡 Щит — {SHIELD_PRICE} 💎\n'
        'Спасает от убийства. На 1 игру.\n\n'
        f'🍀 Везунчик — {LUCKY_PRICE} 💎\n'
        'Двойной голос + забираешь игрока после смерти. На 1 игру.\n\n'
        f'Статус:\n'
        f'Щит: {"✅" if p.get("shield") else "❌"}\n'
        f'Везунчик: {"✅" if p.get("lucky") else "❌"}\n'
        f'Побед: {p.get("wins", 0)}'
    )
    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('shop_'))
def cb_shop(call):
    uid = call.from_user.id
    item = call.data.replace('shop_', '')
    result = buy_item(uid, item)

    if result == 'ok':
        names = {'shield': 'Щит', 'lucky': 'Везунчик'}
        bot.answer_callback_query(call.id, f'✅ Куплено: {names.get(item)}')
        p = get_profile(uid)
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(f'🛡 Щит — {SHIELD_PRICE} 💎', callback_data='shop_shield'))
        kb.add(types.InlineKeyboardButton(f'🍀 Везунчик — {LUCKY_PRICE} 💎', callback_data='shop_lucky'))
        text = (
            '🛒 МАГАЗИН\n━━━━━━━━━━━━━━━\n\n'
            f'💎 Алмазы: {p.get("diamonds", 0)}\n\n'
            f'Щит: {"✅" if p.get("shield") else "❌"}\n'
            f'Везунчик: {"✅" if p.get("lucky") else "❌"}\n'
            f'Побед: {p.get("wins", 0)}'
        )
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)
        except:
            pass
    elif result == 'already':
        bot.answer_callback_query(call.id, 'Уже куплено')
    elif result == 'no_money':
        bot.answer_callback_query(call.id, 'Недостаточно алмазов')
    else:
        bot.answer_callback_query(call.id, 'Ошибка')


@bot.message_handler(commands=['balance'])
def cmd_balance(m):
    p = get_profile(m.from_user.id)
    bot.send_message(m.chat.id,
        f'💎 Алмазов: {p.get("diamonds", 0)}\n'
        f'🛡 Щит: {"✅" if p.get("shield") else "❌"}\n'
        f'🍀 Везунчик: {"✅" if p.get("lucky") else "❌"}\n'
        f'🏆 Побед: {p.get("wins", 0)}')


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('Mafia bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
