import telebot
import time
import threading
import random
import json
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ==================== НАСТРОЙКИ ====================
TOKEN = '8514412667:AAGtzSPDoy1s63kEaqhlfRYaF-NNdeTU3bo'

SPAM_LIMIT = 30
SPAM_WINDOW = 120
AUTO_MUTE_MINUTES = 5

MUTES_FILE = 'mutes.json'
MESSAGES_FILE = 'messages.json'
STORE_DAYS = 90

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)

SPAM_TRACKER = {}
MUTES = {}
MUTES_LOCK = threading.Lock()

MESSAGES = {}
MESSAGES_LOCK = threading.Lock()


# ==================== ХРАНИЛИЩА ====================
def load_json_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default


def save_json_file(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'save {path} err:', e)


def load_mutes():
    global MUTES
    raw = load_json_file(MUTES_FILE, {})
    MUTES = {}
    for chat_id, users in raw.items():
        MUTES[int(chat_id)] = {}
        for uid, info in users.items():
            MUTES[int(chat_id)][int(uid)] = info


def save_mutes():
    data = {}
    for chat_id, users in MUTES.items():
        data[str(chat_id)] = {}
        for uid, info in users.items():
            data[str(chat_id)][str(uid)] = info
    save_json_file(MUTES_FILE, data)


def load_messages():
    global MESSAGES
    raw = load_json_file(MESSAGES_FILE, {})
    MESSAGES = {}
    for chat_id, data in raw.items():
        MESSAGES[int(chat_id)] = {}
        for uid, days in data.items():
            MESSAGES[int(chat_id)][int(uid)] = days


def save_messages():
    data = {}
    for chat_id, users in MESSAGES.items():
        data[str(chat_id)] = {}
        for uid, days in users.items():
            data[str(chat_id)][str(uid)] = days
    save_json_file(MESSAGES_FILE, data)


def today_str():
    return datetime.now().strftime('%Y-%m-%d')


def cleanup_old_messages():
    """Удаляет записи старше STORE_DAYS дней."""
    cutoff = (datetime.now() - timedelta(days=STORE_DAYS)).strftime('%Y-%m-%d')
    with MESSAGES_LOCK:
        for chat_id in list(MESSAGES.keys()):
            for uid in list(MESSAGES[chat_id].keys()):
                days = MESSAGES[chat_id][uid]
                MESSAGES[chat_id][uid] = {d: c for d, c in days.items() if d >= cutoff}
    save_messages()


load_mutes()
load_messages()
cleanup_old_messages()


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


# ==================== СЧЁТЧИК СООБЩЕНИЙ ====================
def add_message(chat_id, uid):
    today = today_str()
    with MESSAGES_LOCK:
        if chat_id not in MESSAGES:
            MESSAGES[chat_id] = {}
        if uid not in MESSAGES[chat_id]:
            MESSAGES[chat_id][uid] = {}
        MESSAGES[chat_id][uid][today] = MESSAGES[chat_id][uid].get(today, 0) + 1


def count_for_period(chat_id, uid, days):
    """days=None — всё время, days=N — последние N дней."""
    with MESSAGES_LOCK:
        user_days = MESSAGES.get(chat_id, {}).get(uid, {})
        if not user_days:
            return 0
        if days is None:
            return sum(user_days.values())
        cutoff = (datetime.now() - timedelta(days=days - 1)).strftime('%Y-%m-%d')
        return sum(c for d, c in user_days.items() if d >= cutoff)


def get_top(chat_id, days, limit=30):
    with MESSAGES_LOCK:
        users = MESSAGES.get(chat_id, {})
        result = []
        for uid, days_data in users.items():
            if days is None:
                total = sum(days_data.values())
            else:
                cutoff = (datetime.now() - timedelta(days=days - 1)).strftime('%Y-%m-%d')
                total = sum(c for d, c in days_data.items() if d >= cutoff)
            if total > 0:
                result.append((uid, total))
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:limit]


def get_user_rank(chat_id, uid, days):
    top = get_top(chat_id, days, limit=999999)
    for i, (u, _) in enumerate(top, 1):
        if u == uid:
            return i
    return None


def get_username(chat_id, uid):
    try:
        member = bot.get_chat_member(chat_id, uid)
        return member.user.first_name or f'ID {uid}'
    except:
        return f'ID {uid}'


# ==================== МУТ ====================
def is_muted(chat_id, uid):
    with MUTES_LOCK:
        chat = MUTES.get(chat_id, {})
        info = chat.get(uid)
        if not info:
            return False
        if info.get('until', 0) <= time.time():
            del chat[uid]
            save_mutes()
            return False
        return True


def get_mute_left(chat_id, uid):
    with MUTES_LOCK:
        info = MUTES.get(chat_id, {}).get(uid)
        if not info:
            return 0
        return max(0, int(info.get('until', 0) - time.time()))


def add_mute(chat_id, uid, minutes, by_name, reason):
    until = time.time() + minutes * 60
    with MUTES_LOCK:
        if chat_id not in MUTES:
            MUTES[chat_id] = {}
        MUTES[chat_id][uid] = {
            'until': until,
            'minutes': minutes,
            'by': by_name,
            'reason': reason,
        }
    save_mutes()
    return until


def remove_mute(chat_id, uid):
    with MUTES_LOCK:
        if chat_id in MUTES and uid in MUTES[chat_id]:
            del MUTES[chat_id][uid]
            save_mutes()
            return True
    return False


def apply_telegram_mute(chat_id, uid, minutes):
    try:
        until = int(time.time()) + minutes * 60
        bot.restrict_chat_member(
            chat_id, uid,
            permissions=types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=until
        )
        return True
    except Exception as e:
        print('restrict err:', e)
        return False


def remove_telegram_mute(chat_id, uid):
    try:
        bot.restrict_chat_member(
            chat_id, uid,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        return True
    except Exception as e:
        print('unrestrict err:', e)
        return False


def is_group_admin(chat_id, uid):
    try:
        member = bot.get_chat_member(chat_id, uid)
        return member.status in ('administrator', 'creator')
    except:
        return False


# ==================== АВТО-РАЗМУТ ====================
def auto_unmute_loop():
    while True:
        try:
            now = time.time()
            to_unmute = []
            with MUTES_LOCK:
                for chat_id, users in list(MUTES.items()):
                    for uid, info in list(users.items()):
                        if info.get('until', 0) <= now:
                            to_unmute.append((chat_id, uid))
                            del users[uid]
            for chat_id, uid in to_unmute:
                remove_telegram_mute(chat_id, uid)
                try:
                    bot.send_message(chat_id, '✅ Мут снят автоматически.')
                except:
                    pass
            if to_unmute:
                save_mutes()
        except Exception as e:
            print('auto_unmute err:', e)
        time.sleep(30)


threading.Thread(target=auto_unmute_loop, daemon=True).start()


# ==================== СЧЁТЧИК — ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ====================
@bot.message_handler(
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice',
                   'sticker', 'animation', 'video_note', 'location', 'contact'],
    func=lambda m: m.chat.type in ('group', 'supergroup')
)
def count_all_messages(m):
    if m.from_user and not m.from_user.is_bot:
        add_message(m.chat.id, m.from_user.id)


# ==================== РП КОМАНДЫ ====================
ACTIONS = {
    'обнять': ['🤗 {a} обнял {b}', '💞 {a} крепко обнял {b}', '🫂 {a} заключил {b} в объятия'],
    'погладить': ['✋ {a} погладил {b}', '🤲 {a} нежно погладил {b}', '😊 {a} потрепал по голове {b}'],
    'поцеловать': ['💋 {a} поцеловал {b}', '😘 {a} чмокнул {b}', '💞 {a} страстно поцеловал {b}'],
    'поблагодарить': ['🙏 {a} поблагодарил {b}', '💐 {a} сказал спасибо {b}', '😌 {a} искренне поблагодарил {b}'],
    'улыбнуться': ['😊 {a} улыбнулся {b}', '😁 {a} широко улыбнулся {b}', '🙂 {a} мило улыбнулся {b}'],
    'подмигнуть': ['😉 {a} подмигнул {b}', '😏 {a} игриво подмигнул {b}'],
    'ударить': ['👊 {a} ударил {b}', '💥 {a} врезал {b}', '🥊 {a} заехал {b}'],
    'убить': ['🔪 {a} убил {b}', '💀 {a} прикончил {b}', '⚰️ {a} отправил {b} на тот свет'],
    'укусить': ['🦷 {a} укусил {b}', '😬 {a} больно укусил {b}', '🧛 {a} впился в {b}'],
    'пнуть': ['🦵 {a} пнул {b}', '👟 {a} дал пинка {b}', '💢 {a} со всей силы пнул {b}'],
    'шлёпнуть': ['✋ {a} шлёпнул {b}', '👋 {a} дал шлепок {b}'],
    'кинуть тапок': ['🥿 {a} кинул тапок в {b}', '👟 {a} запустил тапок в {b}'],
    'обозвать': ['😠 {a} обозвал {b}', '🤬 {a} наорал на {b}'],
    'отсосать': ['👅 {a} отсосал у {b}', '😮 {a} сделал минет {b}'],
    'трахнуть': ['🍆 {a} трахнул {b}', '🔥 {a} жёстко трахнул {b}', '💦 {a} отымел {b}'],
    'выебать': ['🔥 {a} выебал {b}', '💥 {a} жёстко выебал {b}'],
    'лизнуть': ['👅 {a} лизнул {b}', '😋 {a} облизал {b}'],
    'ласкать': ['💆 {a} ласкает {b}', '🤲 {a} нежно ласкает {b}'],
    'соблазнить': ['😏 {a} соблазнил {b}', '💋 {a} пытается соблазнить {b}'],
    'раздеть': ['👕 {a} раздел {b}', '🔥 {a} сорвал одежду с {b}'],
    'флиртовать': ['😉 {a} флиртует с {b}', '💞 {a} заигрывает с {b}'],
    'жениться': ['💍 {a} женился на {b}', '💒 {a} сделал предложение {b}'],
    'развестись': ['💔 {a} развёлся с {b}', '📄 {a} подал на развод с {b}'],
    'дать пять': ['✋ {a} дал пять {b}', '🙌 {a} дал краба {b}'],
    'дружить': ['🤝 {a} предложил дружбу {b}', '👬 {a} стал другом {b}'],
    'поддержать': ['💪 {a} поддержал {b}', '🤗 {a} утешил {b}'],
    'поздравить': ['🎉 {a} поздравил {b}', '🥳 {a} пожелал всего лучшего {b}'],
    'накормить': ['🍕 {a} накормил {b}', '🍔 {a} угостил {b}'],
    'напоить': ['🍺 {a} напоил {b}', '🥤 {a} дал выпить {b}'],
    'украсть': ['🕵️ {a} украл что-то у {b}', '💰 {a} обокрал {b}'],
    'кинуть снежок': ['❄️ {a} кинул снежок в {b}', '⛄ {a} закидал снегом {b}'],
    'облить водой': ['💧 {a} облил водой {b}', '🌊 {a} окатил {b}'],
    'загипнотизировать': ['🌀 {a} загипнотизировал {b}', '👁️ {a} вводит {b} в транс'],
    'телепортировать': ['✨ {a} телепортировал {b}', '🌌 {a} переместил {b}'],
    'превратить в жабу': ['🐸 {a} превратил {b} в жабу', '🪄 {a} заколдовал {b}'],
    'укусить за ухо': ['👂 {a} укусил за ухо {b}', '😬 {a} прикусил ушко {b}'],
}


def get_action_text(action, a, b):
    variants = ACTIONS.get(action)
    if not variants:
        return None
    return random.choice(variants).format(a=a, b=b)


# ==================== /start ====================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('Как играть', callback_data='rp_how'),
        types.InlineKeyboardButton('Правила РП', callback_data='rp_rules'),
        types.InlineKeyboardButton('Конфиденциальность', callback_data='rp_privacy'),
        types.InlineKeyboardButton('Список команд', callback_data='rp_cmds'),
    )
    text = (
        '💞 РП БОТ\n'
        '━━━━━━━━━━━━━━━\n\n'
        'Добро пожаловать!\n\n'
        'Это бот для ролевых действий в чате.\n'
        'Отвечай на сообщение и пиши команду.\n\n'
        '👇 Выбери раздел:'
    )
    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.message_handler(commands=['help'])
def cmd_help(m):
    cmd_start(m)


# ==================== РАЗДЕЛЫ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'rp_how')
def cb_how(call):
    text = (
        '📖 КАК ИГРАТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '1️⃣ Добавь бота в группу\n\n'
        '2️⃣ Ответь на сообщение человека\n\n'
        '3️⃣ Напиши команду, например /обнять\n\n'
        '4️⃣ Бот пришлёт красивое сообщение.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '📊 СТАТИСТИКА\n\n'
        '/stats — твоя статистика\n'
        '/top — топ за неделю\n'
        '/top день — за сегодня\n'
        '/top всё — за всё время\n'
        '/top месяц — за месяц\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🚫 АНТИСПАМ\n\n'
        f'Если отправить {SPAM_LIMIT} команд за '
        f'{SPAM_WINDOW // 60} мин — автомут на {AUTO_MUTE_MINUTES} мин.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='rp_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'rp_rules')
def cb_rules(call):
    text = (
        '📜 ПРАВИЛА РП\n'
        '━━━━━━━━━━━━━━━\n\n'
        '✅ МОЖНО:\n'
        '• Делать действия по согласию\n'
        '• Использовать любые команды\n'
        '• Отвечать взаимно\n\n'
        '❌ НЕЛЬЗЯ:\n'
        '• Спамить командами\n'
        '• Использовать 18+ без согласия\n'
        '• Оскорблять всерьёз\n'
        '• Преследовать человека\n\n'
        '━━━━━━━━━━━━━━━\n'
        '⚠️ 18+\n'
        '• Только по обоюдному согласию\n'
        '• Запрещено с несовершеннолетними\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🚫 СПАМ\n'
        f'• {SPAM_LIMIT} команд за {SPAM_WINDOW // 60} мин = '
        f'автомут {AUTO_MUTE_MINUTES} мин\n'
        '• Размут автоматический'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='rp_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'rp_privacy')
def cb_privacy(call):
    text = (
        '🔒 КОНФИДЕНЦИАЛЬНОСТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '❌ Бот НЕ:\n'
        '• Не читает личные сообщения\n'
        '• Не собирает данные\n'
        '• Не сохраняет текст сообщений\n'
        '• Не передаёт третьим лицам\n\n'
        '✅ Бот хранит:\n'
        '• Имя и ID (для мута/статистики)\n'
        '• Количество сообщений (не текст)\n'
        '• Активные муты\n\n'
        'Данные хранятся в файлах бота.'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='rp_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'rp_cmds')
def cb_cmds(call):
    text = (
        '📋 СПИСОК КОМАНД\n'
        '━━━━━━━━━━━━━━━\n\n'
        '💞 РОМАНТИКА:\n'
        '/обнять /погладить /поцеловать\n'
        '/флиртовать /жениться /развестись\n\n'
        '🤝 ДРУЖБА:\n'
        '/поблагодарить /дать пять /дружить\n'
        '/поддержать /поздравить\n\n'
        '😈 АГРЕССИЯ:\n'
        '/ударить /убить /укусить /пнуть\n'
        '/шлёпнуть /кинуть тапок /обозвать\n\n'
        '🔥 18+:\n'
        '/отсосать /трахнуть /выебать\n'
        '/лизнуть /ласкать /соблазнить /раздеть\n\n'
        '🎲 ЗАБАВНЫЕ:\n'
        '/накормить /напоить /украсть\n'
        '/кинуть снежок /облить водой\n'
        '/загипнотизировать /телепортировать\n'
        '/превратить в жабу /укусить за ухо\n\n'
        '📊 СТАТИСТИКА:\n'
        '/stats — моя статистика\n'
        '/stats @ник — статистика игрока\n'
        '/top — топ-30 за неделю\n'
        '/top день — за сегодня\n'
        '/top всё — за всё время\n'
        '/top месяц — за месяц\n\n'
        '🛡 МОДЕРАЦИЯ (админы):\n'
        '/mute N — мут на N минут (1–1000)\n'
        '/unmute — снять мут\n'
        '/mutelist — список замученных\n'
        '/ban — забанить\n'
        '/unban ID — разбанить\n'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('Назад', callback_data='rp_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'rp_back')
def cb_back(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton('Как играть', callback_data='rp_how'),
        types.InlineKeyboardButton('Правила РП', callback_data='rp_rules'),
        types.InlineKeyboardButton('Конфиденциальность', callback_data='rp_privacy'),
        types.InlineKeyboardButton('Список команд', callback_data='rp_cmds'),
    )
    text = '💞 РП БОТ\n━━━━━━━━━━━━━━━\n\n👇 Выбери раздел:'
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== СТАТИСТИКА ====================
@bot.message_handler(commands=['stats'])
def cmd_stats(m):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Только в группе.')
        return

    parts = m.text.split()
    if len(parts) >= 2 and parts[1].startswith('@'):
        target_uname = parts[1][1:].lower()
        target_uid = None
        target_name = None
        try:
            with MESSAGES_LOCK:
                for uid in MESSAGES.get(m.chat.id, {}).keys():
                    try:
                        member = bot.get_chat_member(m.chat.id, uid)
                        if member.user.username and member.user.username.lower() == target_uname:
                            target_uid = uid
                            target_name = member.user.first_name
                            break
                    except:
                        continue
        except:
            pass
        if not target_uid:
            bot.reply_to(m, 'Игрок не найден в статистике.')
            return
        uid = target_uid
        name = target_name
    else:
        uid = m.from_user.id
        name = m.from_user.first_name

    total = count_for_period(m.chat.id, uid, None)
    today = count_for_period(m.chat.id, uid, 1)
    week = count_for_period(m.chat.id, uid, 7)
    month = count_for_period(m.chat.id, uid, 30)

    rank_week = get_user_rank(m.chat.id, uid, 7)
    rank_all = get_user_rank(m.chat.id, uid, None)

    text = (
        f'📊 СТАТИСТИКА: {name}\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'📅 Сегодня: {today}\n'
        f'📆 За неделю: {week}\n'
        f'🗓 За месяц: {month}\n'
        f'📈 Всего: {total}\n\n'
        f'🏆 Место за неделю: {rank_week or "—"}\n'
        f'🏆 Место за всё время: {rank_all or "—"}'
    )
    bot.reply_to(m, text)


@bot.message_handler(commands=['top'])
def cmd_top(m):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Только в группе.')
        return

    parts = m.text.split(maxsplit=1)
    arg = parts[1].lower() if len(parts) > 1 else ''

    if arg in ('день', 'day', 'today'):
        days = 1
        title = 'ЗА СЕГОДНЯ'
    elif arg in ('неделя', 'week', '7'):
        days = 7
        title = 'ЗА НЕДЕЛЮ'
    elif arg in ('месяц', 'month', '30'):
        days = 30
        title = 'ЗА МЕСЯЦ'
    elif arg in ('всё', 'все', 'all', 'всего'):
        days = None
        title = 'ЗА ВСЁ ВРЕМЯ'
    else:
        days = 7
        title = 'ЗА НЕДЕЛЮ'

    top = get_top(m.chat.id, days, limit=30)

    if not top:
        bot.reply_to(m, 'Пока нет данных.')
        return

    text = f'🏆 ТОП-30 {title}\n━━━━━━━━━━━━━━━\n\n'
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    for i, (uid, count) in enumerate(top, 1):
        name = get_username(m.chat.id, uid)
        prefix = medals.get(i, f'{i}.')
        text += f'{prefix} {name} — {count}\n'

    text += f'\n📊 Показаны топ-30'
    bot.reply_to(m, text)


# ==================== АНТИСПАМ ====================
def check_spam(uid):
    now = time.time()
    if uid not in SPAM_TRACKER:
        SPAM_TRACKER[uid] = []
    SPAM_TRACKER[uid] = [t for t in SPAM_TRACKER[uid] if now - t < SPAM_WINDOW]
    SPAM_TRACKER[uid].append(now)
    return len(SPAM_TRACKER[uid]) >= SPAM_LIMIT


# ==================== ОБРАБОТЧИК КОМАНД ====================
@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def handle_command(m):
    text = m.text.strip()
    if not text or len(text) < 2:
        return

    action = text[1:].split()[0].lower()

    if action in ('start', 'help', 'stats', 'top'):
        return

    if action in ('mute', 'unmute', 'mutelist', 'ban', 'unban'):
        handle_moderation(m, action)
        return

    if action not in ACTIONS:
        return

    if m.chat.type == 'private':
        bot.reply_to(m, 'Эта команда работает только в группе.')
        return

    if is_muted(m.chat.id, m.from_user.id):
        left = get_mute_left(m.chat.id, m.from_user.id)
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except:
            pass
        bot.send_message(m.chat.id,
            f'🚫 {m.from_user.first_name} в муте. Осталось {left // 60} мин {left % 60} сек.')
        return

    if not m.reply_to_message:
        bot.reply_to(m, '⚠️ Ответь на сообщение человека и напиши команду.')
        return

    target = m.reply_to_message.from_user
    sender = m.from_user

    if target.id == sender.id:
        bot.reply_to(m, '🤡 Нельзя это сделать с самим собой.')
        return

    if target.id == bot.get_me().id:
        bot.reply_to(m, '🤖 Нельзя это сделать с ботом.')
        return

    if check_spam(sender.id):
        SPAM_TRACKER[sender.id] = []
        add_mute(m.chat.id, sender.id, AUTO_MUTE_MINUTES,
                 'Автомодерация', 'спам командами')
        apply_telegram_mute(m.chat.id, sender.id, AUTO_MUTE_MINUTES)
        bot.send_message(m.chat.id,
            f'🚫 {sender.first_name} замучен на {AUTO_MUTE_MINUTES} минут.\n'
            f'Причина: спам командами ({SPAM_LIMIT} за {SPAM_WINDOW // 60} мин)')
        return

    a_name = sender.first_name or 'Кто-то'
    b_name = target.first_name or 'Кто-то'
    result = get_action_text(action, a_name, b_name)
    if not result:
        return

    try:
        bot.reply_to(m, result, reply_to_message_id=m.reply_to_message.message_id)
    except:
        bot.send_message(m.chat.id, result)


# ==================== МОДЕРАЦИЯ ====================
def handle_moderation(m, action):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Модерация только в группах.')
        return

    if not is_group_admin(m.chat.id, m.from_user.id):
        bot.reply_to(m, '⛔ Только админы группы.')
        return

    if action == 'mutelist':
        show_mutelist(m)
        return

    if action == 'unban':
        parts = m.text.split()
        if len(parts) < 2:
            bot.reply_to(m, 'Использование: /unban ID')
            return
        try:
            target_id = int(parts[1])
        except:
            bot.reply_to(m, 'ID должен быть числом.')
            return
        try:
            bot.unban_chat_member(m.chat.id, target_id)
            bot.reply_to(m, f'✅ {target_id} разбанен.')
        except Exception as e:
            bot.reply_to(m, f'Ошибка: {e}')
        return

    if action == 'unmute':
        if not m.reply_to_message:
            bot.reply_to(m, 'Ответь на сообщение.')
            return
        target = m.reply_to_message.from_user
        remove_mute(m.chat.id, target.id)
        remove_telegram_mute(m.chat.id, target.id)
        bot.reply_to(m,
            f'✅ {target.first_name} размучен.\n'
            f'Админ: {m.from_user.first_name}')
        return

    if action == 'ban':
        if not m.reply_to_message:
            bot.reply_to(m, 'Ответь на сообщение.')
            return
        target = m.reply_to_message.from_user
        if is_group_admin(m.chat.id, target.id):
            bot.reply_to(m, '⛔ Нельзя банить админов.')
            return
        try:
            bot.ban_chat_member(m.chat.id, target.id)
            bot.send_message(m.chat.id,
                f'🚫 {target.first_name} забанен.\n'
                f'Кем: {m.from_user.first_name}')
        except Exception as e:
            bot.reply_to(m, f'Ошибка: {e}')
        return

    if action == 'mute':
        parts = m.text.split()
        if len(parts) < 2:
            bot.reply_to(m, 'Использование: /mute 10 (ответом)')
            return
        try:
            minutes = int(parts[1])
        except:
            bot.reply_to(m, 'Число минут: /mute 10')
            return

        if minutes < 1 or minutes > 1000:
            bot.reply_to(m, '⛔ Мут от 1 до 1000 минут.')
            return

        if not m.reply_to_message:
            bot.reply_to(m, 'Ответь на сообщение.')
            return

        target = m.reply_to_message.from_user
        if is_group_admin(m.chat.id, target.id):
            bot.reply_to(m, '⛔ Нельзя мутить админов.')
            return

        reason = ' '.join(parts[2:]) if len(parts) > 2 else 'не указана'

        add_mute(m.chat.id, target.id, minutes,
                 m.from_user.first_name, reason)
        apply_telegram_mute(m.chat.id, target.id, minutes)

        bot.send_message(m.chat.id,
            f'🚫 {target.first_name} замучен.\n'
            f'Кем: {m.from_user.first_name}\n'
            f'Срок: {minutes} мин\n'
            f'Причина: {reason}')


def show_mutelist(m):
    chat_id = m.chat.id
    now = time.time()
    with MUTES_LOCK:
        users = MUTES.get(chat_id, {})
        active = []
        for uid, info in users.items():
            if info.get('until', 0) > now:
                left = int(info['until'] - now)
                active.append({
                    'uid': uid,
                    'left': left,
                    'by': info.get('by', '—'),
                    'reason': info.get('reason', '—'),
                })

    if not active:
        bot.send_message(chat_id, '📋 Список замученных пуст.')
        return

    active.sort(key=lambda x: x['left'], reverse=True)

    text = f'📋 ЗАМУЧЕННЫЕ ({len(active)})\n━━━━━━━━━━━━━━━\n\n'
    for i, u in enumerate(active, 1):
        name = get_username(chat_id, u['uid'])
        left_min = u['left'] // 60
        left_sec = u['left'] % 60
        text += (
            f'{i}. {name}\n'
            f'   Осталось: {left_min} мин {left_sec} сек\n'
            f'   Кем: {u["by"]}\n'
            f'   Причина: {u["reason"]}\n\n'
        )

    if len(text) > 4000:
        text = text[:4000] + '\n...'

    bot.send_message(chat_id, text)


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('RP bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
