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
POSTS_FILE = 'posts_api.json'
GROUPS_FILE = 'groups.json'

ADMIN_IDS = [8907438590]

DUEL_HP = 100
DUEL_SHOOT_MIN = 25
DUEL_SHOOT_MAX = 45
DUEL_AIM_BONUS = 0.9
DUEL_NOAIM_CHANCE = 0.6
DUEL_ACCEPT_TIMEOUT = 300

BOSS_DMG_MIN = 50
BOSS_DMG_MAX = 150
BOSS_PLAYER_MIN_HP = 250
BOSS_PLAYER_MAX_HP = 2000
BOSS_HP_PER_EGG = 5
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

BOSSES = {
    1: {'name': 'Голодный Волк',       'emoji': '🐺', 'hp': 1000, 'eggs': 2},
    2: {'name': 'Пустынный Скорпион',  'emoji': '🦂', 'hp': 1500, 'eggs': 3},
    3: {'name': 'Кровавый Лев',        'emoji': '🦁', 'hp': 2000, 'eggs': 4},
    4: {'name': 'Демон Огня',          'emoji': '👺', 'hp': 2500, 'eggs': 5},
    5: {'name': 'Тёмный Лорд',         'emoji': '👹', 'hp': 3000, 'eggs': 6},
    6: {'name': 'Король Зомби',        'emoji': '🧟', 'hp': 3500, 'eggs': 7},
    7: {'name': 'Древний Дракон',      'emoji': '🐉', 'hp': 5000, 'eggs': 10},
}

TOKEN = '8901361348:AAFH5WEtT3gJy_rd2TYTbX1nDqCzOpMJ3Kw'

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
def load_boss(): return load_json(BOSS_FILE, {})
def save_boss(d): save_json(BOSS_FILE, d)
def load_posts(): return load_json(POSTS_FILE, [])
def save_posts(d): save_json(POSTS_FILE, d)
def load_groups(): return load_json(GROUPS_FILE, {})
def save_groups(d): save_json(GROUPS_FILE, d)

def is_admin_id(user_id):
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def remember_group(chat):
    try:
        if chat.type in ('group', 'supergroup'):
            groups = load_groups()
            cid = str(chat.id)
            if cid not in groups:
                groups[cid] = {'title': chat.title or 'Группа', 'added': int(time.time())}
                save_groups(groups)
    except:
        pass

def update_username(user_id, first_name='', username=''):
    try:
        stats = load_stats()
        key = str(user_id)
        fname = first_name or 'Аноним'
        uname = username or ''
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
                'wins': 0, 'losses': 0, 'duels_played': 0,
                'boss_wins': 0, 'boss_losses': 0,
                'eggs': 0, 'max_hp': BOSS_PLAYER_MIN_HP
            }
            save_stats(stats)
    except:
        pass

def get_player(user_id, first_name='Аноним', username=''):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'wins': 0, 'losses': 0, 'duels_played': 0,
            'boss_wins': 0, 'boss_losses': 0,
            'eggs': 0, 'max_hp': BOSS_PLAYER_MIN_HP
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        defaults = {
            'wins':0,'losses':0,'duels_played':0,
            'boss_wins':0,'boss_losses':0,
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

def add_boss_win(user_id, eggs=0):
    p = get_player(user_id); p['boss_wins'] += 1; p['eggs'] = p.get('eggs',0) + eggs; update_player(user_id, p)

def add_boss_loss(user_id):
    p = get_player(user_id); p['boss_losses'] += 1; update_player(user_id, p)

def get_duel(chat_id): return load_duels().get(str(chat_id))
def save_duel(chat_id, duel):
    d = load_duels(); d[str(chat_id)] = duel; save_duels(d)
def del_duel(chat_id):
    d = load_duels()
    if str(chat_id) in d:
        del d[str(chat_id)]; save_duels(d)

def get_boss(chat_id): return load_boss().get(str(chat_id))
def save_boss_game(chat_id, game):
    b = load_boss(); b[str(chat_id)] = game; save_boss(b)
def del_boss(chat_id):
    b = load_boss()
    if str(chat_id) in b:
        del b[str(chat_id)]; save_boss(b)

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

def safe_edit(chat_id, msg_id, text, reply_markup=None):
    try:
        bot.edit_message_text(
            text, chat_id=chat_id, message_id=msg_id,
            parse_mode='HTML', reply_markup=reply_markup
        )
        return True
    except:
        return False

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
        types.InlineKeyboardButton(text='🐉 Босс', callback_data='menu_boss')
    )
    kb.add(types.InlineKeyboardButton(text='🥚 Яйца', callback_data='menu_eggs'))
    kb.add(types.InlineKeyboardButton(text='💬 Помощь', callback_data='menu_help'))
    return kb

# ===== ПОСТЫ =====
pending_posts = {}

@bot.message_handler(commands=['post_new'])
def cmd_post_new(message):
    if not is_admin_id(message.from_user.id):
        return
    uid = message.from_user.id
    if message.reply_to_message:
        post = extract_post_from_message(message.reply_to_message)
        if post:
            show_post_preview(message.chat.id, uid, post)
            return
        else:
            bot.send_message(message.chat.id, "❌ Не могу взять это сообщение.")
            return
    pending_posts[uid] = None
    bot.send_message(
        message.chat.id,
        "📝 <b>СОЗДАНИЕ ПОСТА</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "Отправь мне <b>текст</b> поста, или <b>фото/видео с подписью</b>.\n\n"
        "Или ответь командой <code>/post_new</code> на любое сообщение.",
        parse_mode='HTML'
    )

def extract_post_from_message(msg):
    try:
        post = {'text': '', 'media_type': None, 'file_id': None, 'caption': ''}
        if msg.text:
            post['text'] = msg.text
            return post
        if msg.caption:
            post['caption'] = msg.caption
        if msg.photo:
            post['media_type'] = 'photo'
            post['file_id'] = msg.photo[-1].file_id
            return post
        if msg.video:
            post['media_type'] = 'video'
            post['file_id'] = msg.video.file_id
            return post
        if msg.document:
            post['media_type'] = 'document'
            post['file_id'] = msg.document.file_id
            return post
        return None
    except:
        return None

def show_post_preview(chat_id, uid, post):
    pending_posts[uid] = post
    preview_text = "📢 <b>ПРЕВЬЮ ПОСТА</b>\n━━━━━━━━━━━━━━━\n\n"
    if post.get('caption'):
        preview_text += post['caption'] + "\n\n"
    if post.get('text'):
        preview_text += post['text'] + "\n\n"
    if post.get('media_type'):
        preview_text += f"📎 Медиа: <i>{post['media_type']}</i>"
    preview_text += "\n\n<i>Опубликовать?</i>"

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(text='✅ Опубликовать', callback_data='post_confirm'),
        types.InlineKeyboardButton(text='❌ Отмена', callback_data='post_cancel')
    )
    bot.send_message(chat_id, preview_text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'], func=lambda m: m.from_user and is_admin_id(m.from_user.id) and m.chat.type == 'private' and m.from_user.id in pending_posts and pending_posts.get(m.from_user.id) is None)
def admin_sending_post(message):
    uid = message.from_user.id
    post = extract_post_from_message(message)
    if post:
        show_post_preview(message.chat.id, uid, post)

@bot.callback_query_handler(func=lambda c: c.data == 'post_confirm' or c.data == 'post_cancel')
def post_confirm_cb(call):
    uid = call.from_user.id
    if not is_admin_id(uid):
        bot.answer_callback_query(call.id, "❌ Только админ")
        return
    if call.data == 'post_cancel':
        pending_posts.pop(uid, None)
        safe_edit(call.message.chat.id, call.message.message_id, "❌ Пост отменён.")
        bot.answer_callback_query(call.id, "Отменено")
        return
    post = pending_posts.pop(uid, None)
    if not post:
        bot.answer_callback_query(call.id, "❌ Пост потерялся")
        return
    safe_edit(call.message.chat.id, call.message.message_id, "📢 Отправляю...")
    bot.answer_callback_query(call.id, "Публикую!")
    threading.Thread(target=broadcast_post, args=[post, call.message.chat.id]).start()

def broadcast_post(post, admin_chat_id):
    stats = load_stats()
    groups = load_groups()
    total = len(groups) + len(stats)
    sent_groups = 0
    sent_users = 0
    for cid in list(groups.keys()):
        try:
            send_post_to_chat(int(cid), post)
            sent_groups += 1
            time.sleep(0.05)
        except: pass
    for uid in list(stats.keys()):
        try:
            send_post_to_chat(int(uid), post)
            sent_users += 1
            time.sleep(0.05)
        except: pass
    try:
        bot.send_message(
            admin_chat_id,
            f"✅ <b>ПОСТ ОПУБЛИКОВАН!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📢 Группы: <b>{sent_groups}/{len(groups)}</b>\n"
            f"👥 Игроки: <b>{sent_users}/{len(stats)}</b>\n"
            f"📊 Всего: <b>{sent_groups + sent_users}/{total}</b>",
            parse_mode='HTML'
        )
    except: pass

def send_post_to_chat(chat_id, post):
    try:
        if post.get('media_type') == 'photo':
            bot.send_photo(chat_id, post['file_id'], caption=post.get('caption', ''), parse_mode='HTML')
        elif post.get('media_type') == 'video':
            bot.send_video(chat_id, post['file_id'], caption=post.get('caption', ''), parse_mode='HTML')
        elif post.get('media_type') == 'document':
            bot.send_document(chat_id, post['file_id'], caption=post.get('caption', ''), parse_mode='HTML')
        else:
            bot.send_message(chat_id, post.get('text', ''), parse_mode='HTML')
    except: pass

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def cmd_start(message):
    remember_group(message.chat)
    uid = message.from_user.id
    update_username(uid, message.from_user.first_name, message.from_user.username)
    get_player(uid, message.from_user.first_name, message.from_user.username)
    text = (
        f"🎭 <b>DARKGRAM</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"⚔️ <b>Дуэли 1 на 1</b>\n"
        f"🐉 <b>Боссы 2-4 игрока</b>\n"
        f"🥚 <b>Яйца → HP</b>\n"
        f"🏆 <b>Топ по победам</b>\n\n"
        f"👇 <i>Выбирай кнопки ниже</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def cmd_help(message):
    remember_group(message.chat)
    update_username(message.from_user.id, message.from_user.first_name, message.from_user.username)
    text = (
        f"💬 <b>ПОМОЩЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚔️ <b>Дуэли:</b> <code>/duel</code> в ответ на сообщение\n"
        f"🐉 <b>Боссы:</b> <code>/boss1</code> ... <code>/boss7</code>\n"
        f"🥚 <b>Яйца:</b> <code>/eggs</code>\n\n"
        f"🏏 <b>Бой с боссом:</b>\n"
        f"🔫 Атака — 40-90\n"
        f"🏏 Бита — 80-150 (70% точность)\n"
        f"🎯 Прицел — следующий удар x1.3\n\n"
        f"🐉 <b>БОССЫ:</b>\n"
        f"1️⃣ 🐺 Волк — 1000 HP → +2 🥚\n"
        f"2️⃣ 🦂 Скорпион — 1500 HP → +3 🥚\n"
        f"3️⃣ 🦁 Лев — 2000 HP → +4 🥚\n"
        f"4️⃣ 👺 Демон — 2500 HP → +5 🥚\n"
        f"5️⃣ 👹 Лорд — 3000 HP → +6 🥚\n"
        f"6️⃣ 🧟 Зомби — 3500 HP → +7 🥚\n"
        f"7️⃣ 🐉 Дракон — 5000 HP → +10 🥚\n\n"
        f"🥚 <b>Яйца:</b> 1 яйцо = +5 HP"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    remember_group(message.chat)
    uid = message.from_user.id
    update_username(uid, message.from_user.first_name, message.from_user.username)
    p = get_player(uid, message.from_user.first_name, message.from_user.username)
    total = p['wins'] + p['losses']
    wr = round(p['wins'] / total * 100) if total else 0
    boss_total = p.get('boss_wins',0) + p.get('boss_losses',0)
    boss_wr = round(p.get('boss_wins',0) / boss_total * 100) if boss_total else 0
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"<b>{display_name(p)}</b>\n\n"
        f"⚔️ <b>ДУЭЛИ</b>\n"
        f"🏆 Побед: <b>{p['wins']}</b>\n"
        f"💀 Поражений: <b>{p['losses']}</b>\n"
        f"📊 Винрейт: <b>{wr}%</b>\n\n"
        f"🐉 <b>БОССЫ</b>\n"
        f"🏆 Побед: <b>{p.get('boss_wins',0)}</b>\n"
        f"💀 Поражений: <b>{p.get('boss_losses',0)}</b>\n"
        f"📊 Винрейт: <b>{boss_wr}%</b>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🥚 Яйца: <b>{p.get('eggs',0)}</b>\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', BOSS_PLAYER_MIN_HP)}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['top'])
def cmd_top(message):
    remember_group(message.chat)
    update_username(message.from_user.id, message.from_user.first_name, message.from_user.username)
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "🏆 Пока пусто.")
        return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('wins', 0), reverse=True)[:20]
    text = f"🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n━━━━━━━━━━━━━━━\n\n"
    placed = 0
    for i, (uid, p) in enumerate(sorted_stats, 1):
        if p.get('wins', 0) == 0: continue
        placed += 1
        medal = '🥇' if placed==1 else '🥈' if placed==2 else '🥉' if placed==3 else f'<b>{placed}.</b>'
        text += f"{medal} {display_name(p)}\n     ⚔️ {p['wins']} побед · 💀 {p['losses']}\n\n"
    if placed == 0: text += "Пока никто не побеждал."
    bot.send_message(message.chat.id, text, parse_mode='HTML')

# ===== ЯЙЦА =====
def eggs_menu_text(uid):
    p = get_player(uid)
    return (
        f"🥚 <b>МАГАЗИН ЯИЦ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"💰 У тебя: <b>{p.get('eggs', 0)}</b> яиц\n"
        f"❤️ Макс. HP: <b>{p.get('max_hp', BOSS_PLAYER_MIN_HP)}</b>\n\n"
        f"📌 <b>1 🥚 = +{BOSS_HP_PER_EGG} HP</b>\n"
        f"📈 Максимум HP: <b>{BOSS_PLAYER_MAX_HP}</b>\n\n"
        f"<i>Выбери сколько купить:</i>"
    )

def eggs_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text=f'🥚 +{BOSS_HP_PER_EGG} HP (1 яйцо)', callback_data='eggs_buy_1'),
        types.InlineKeyboardButton(text=f'🥚 +{BOSS_HP_PER_EGG*5} HP (5 яиц)', callback_data='eggs_buy_5'),
        types.InlineKeyboardButton(text=f'🥚 +{BOSS_HP_PER_EGG*10} HP (10 яиц)', callback_data='eggs_buy_10'),
        types.InlineKeyboardButton(text='◀️ Назад', callback_data='menu_back')
    )
    return kb

@bot.message_handler(commands=['eggs'])
def cmd_eggs(message):
    remember_group(message.chat)
    uid = message.from_user.id
    update_username(uid, message.from_user.first_name, message.from_user.username)
    get_player(uid, message.from_user.first_name, message.from_user.username)
    bot.send_message(message.chat.id, eggs_menu_text(uid), parse_mode='HTML', reply_markup=eggs_menu_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith('eggs_buy_'))
def eggs_buy_cb(call):
    uid = str(call.from_user.id)
    update_username(uid, call.from_user.first_name, call.from_user.username)
    p = get_player(uid, call.from_user.first_name, call.from_user.username)
    counts = {'eggs_buy_1': 1, 'eggs_buy_5': 5, 'eggs_buy_10': 10}
    count = counts.get(call.data, 1)
    if p.get('eggs', 0) < count:
        bot.answer_callback_query(call.id, f"❌ Нужно {count} яиц")
        return
    add_hp = BOSS_HP_PER_EGG * count
    if p.get('max_hp', BOSS_PLAYER_MIN_HP) + add_hp > BOSS_PLAYER_MAX_HP:
        bot.answer_callback_query(call.id, "❌ Максимум HP")
        return
    p['eggs'] -= count
    p['max_hp'] = p.get('max_hp', BOSS_PLAYER_MIN_HP) + add_hp
    update_player(uid, p)
    bot.answer_callback_query(call.id, f"✅ +{add_hp} HP")
    safe_edit(call.message.chat.id, call.message.message_id, eggs_menu_text(uid), eggs_menu_kb())

# ===== БОСС =====
@bot.message_handler(commands=['boss', 'boss1', 'boss2', 'boss3', 'boss4', 'boss5', 'boss6', 'boss7'])
def cmd_boss(message):
    remember_group(message.chat)
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "🐉 Боссы только в группах.")
        return
    update_username(message.from_user.id, message.from_user.first_name, message.from_user.username)

    # Разбираем номер босса из команды
    cmd = message.text.split()[0].replace('/', '').replace('@', ' ').split()[0]
    boss_num = None
    if cmd == 'boss':
        # Если просто /boss — показываем список
        text = f"🐉 <b>ВЫБОР БОССА</b>\n━━━━━━━━━━━━━━━\n\n"
        for num, b in BOSSES.items():
            text += f"{num}️⃣ {b['emoji']} <b>{b['name']}</b>\n     ❤️ {b['hp']} HP · 🥚 +{b['eggs']} яиц\n\n"
        text += f"<i>Напиши команду:</i>\n"
        text += f"<code>/boss1</code> ... <code>/boss7</code>"
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        return
    else:
        try: boss_num = int(cmd.replace('boss', ''))
        except: boss_num = None
    if not boss_num or boss_num not in BOSSES:
        bot.send_message(message.chat.id, "❌ Неверный номер. /boss1 ... /boss7")
        return

    boss = BOSSES[boss_num]
    game = get_boss(message.chat.id)
    if game and game.get('status') not in ('finished',):
        bot.send_message(message.chat.id, "🐉 Уже идёт бой.")
        return
    now = int(time.time())
    p = get_player(message.from_user.id, message.from_user.first_name, message.from_user.username)
    game = {
        'chat_id': message.chat.id,
        'host_id': str(message.from_user.id),
        'boss_num': boss_num,
        'boss_name': f"{boss['emoji']} {boss['name']}",
        'boss_hp': boss['hp'],
        'boss_max_hp': boss['hp'],
        'boss_eggs': boss['eggs'],
        'players': {},
        'turn_idx': 0,
        'status': 'lobby',
        'deadline': now + BOSS_LOBBY_TIME,
        'lobby_msg_id': None,
        'fight_msg_id': None,
        'last_msg': ''
    }
    game['players'][str(message.from_user.id)] = {
        'name': message.from_user.first_name,
        'username': message.from_user.username or '',
        'hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
        'max_hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
        'alive': True, 'aim': False, 'dmg_done': 0, 'order': 0
    }
    save_boss_game(message.chat.id, game)
    sent = bot.send_message(
        message.chat.id,
        boss_lobby_text(game),
        parse_mode='HTML',
        reply_markup=boss_lobby_kb(is_admin_id(message.from_user.id))
    )
    game['lobby_msg_id'] = sent.message_id
    save_boss_game(message.chat.id, game)
    threading.Timer(BOSS_LOBBY_TIME, boss_lobby_timeout, args=[message.chat.id]).start()
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[message.chat.id]).start()

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
    players_list = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p.get('max_hp', BOSS_PLAYER_MIN_HP)} HP" for p in game['players'].values()])
    left = game.get('deadline', 0) - int(time.time())
    return (
        f"🐉 <b>БОСС: {game['boss_name']}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"❤️ HP босса: <b>{game['boss_max_hp']}</b>\n"
        f"🥚 Награда: <b>+{game['boss_eggs']} яиц</b>\n\n"
        f"👥 Игроков: <b>{len(game['players'])}/{BOSS_MAX_PLAYERS}</b>\n"
        f"📌 Минимум: <b>{BOSS_MIN_PLAYERS}</b>\n"
        f"⏱ До старта: <b>{fmt_time(left)}</b>\n\n"
        f"<b>Команда:</b>\n{players_list}"
    )

def boss_lobby_tick(chat_id):
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby':
        return
    left = game.get('deadline', 0) - int(time.time())
    if left <= 0: return
    if game.get('lobby_msg_id'):
        safe_edit(chat_id, game['lobby_msg_id'], boss_lobby_text(game), boss_lobby_kb(is_admin_id(game['host_id'])))
    threading.Timer(BOSS_TIMER_UPDATE, boss_lobby_tick, args=[chat_id]).start()

def boss_lobby_timeout(chat_id):
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby': return
    count = len(game['players'])
    if count >= BOSS_MIN_PLAYERS:
        start_boss_fight(chat_id)
    else:
        try:
            bot.send_message(chat_id, f"⏱ Мало игроков ({count}). Отмена.", parse_mode='HTML')
        except: pass
        del_boss(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith('boss_join') or c.data.startswith('boss_leave') or c.data.startswith('boss_start') or c.data.startswith('boss_cancel') or c.data.startswith('boss_extend'))
def boss_lobby_cb(call):
    chat_id = call.message.chat.id
    game = get_boss(chat_id)
    if not game or game.get('status') != 'lobby':
        bot.answer_callback_query(call.id, "❌ Закрыто")
        return
    uid = str(call.from_user.id)
    update_username(uid, call.from_user.first_name, call.from_user.username)
    is_admin = is_admin_id(uid)
    msg_id = game.get('lobby_msg_id') or call.message.message_id

    if call.data == 'boss_join':
        if uid in game['players']:
            bot.answer_callback_query(call.id, "✅ Уже в команде")
            return
        if len(game['players']) >= BOSS_MAX_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Макс {BOSS_MAX_PLAYERS}")
            return
        p = get_player(uid, call.from_user.first_name, call.from_user.username)
        order = max([pl.get('order', 0) for pl in game['players'].values()] + [0]) + 1
        game['players'][uid] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username or '',
            'hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
            'max_hp': p.get('max_hp', BOSS_PLAYER_MIN_HP),
            'alive': True, 'aim': False, 'dmg_done': 0, 'order': order
        }
        save_boss_game(chat_id, game)
        safe_edit(chat_id, msg_id, boss_lobby_text(game), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "⚔️ В команде!")
        return

    if call.data == 'boss_leave':
        if uid not in game['players']:
            bot.answer_callback_query(call.id, "❌ Не в команде")
            return
        was_host = (uid == game['host_id'])
        del game['players'][uid]
        if was_host and game['players']:
            new_host_id = sorted(game['players'].keys(), key=lambda u: game['players'][u].get('order',0))[0]
            game['host_id'] = new_host_id
        elif not game['players']:
            del_boss(chat_id)
            safe_edit(chat_id, msg_id, "❌ Лобби закрыто.")
            bot.answer_callback_query(call.id, "🚪 Закрыто")
            return
        save_boss_game(chat_id, game)
        safe_edit(chat_id, msg_id, boss_lobby_text(game), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "🚪 Вышел")
        return

    if call.data == 'boss_start':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост")
            return
        if len(game['players']) < BOSS_MIN_PLAYERS:
            bot.answer_callback_query(call.id, f"❌ Минимум {BOSS_MIN_PLAYERS}")
            return
        bot.answer_callback_query(call.id, "🐉 Начинаем!")
        start_boss_fight(chat_id)
        return

    if call.data == 'boss_cancel':
        if uid != game['host_id'] and not is_admin:
            bot.answer_callback_query(call.id, "❌ Только хост")
            return
        del_boss(chat_id)
        safe_edit(chat_id, msg_id, "❌ Отменено.")
        bot.answer_callback_query(call.id, "Отменено")
        return

    if call.data == 'boss_extend':
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ Только админ")
            return
        game['deadline'] = int(time.time()) + BOSS_LOBBY_TIME
        save_boss_game(chat_id, game)
        safe_edit(chat_id, msg_id, boss_lobby_text(game), boss_lobby_kb(is_admin))
        bot.answer_callback_query(call.id, "➕ Продлено 5:00")

def boss_fight_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(text='🔫 Атака', callback_data='boss_fight_atk'),
        types.InlineKeyboardButton(text='🏏 Бита', callback_data='boss_fight_bat'),
        types.InlineKeyboardButton(text='🎯 Прицел', callback_data='boss_fight_aim')
    )
    return kb

def get_alive_players_sorted(game):
    alive = [(uid, p) for uid, p in game['players'].items() if p['alive']]
    alive.sort(key=lambda x: x[1].get('order', 0))
    return alive

def boss_fight_text(game):
    alive_players = get_alive_players_sorted(game)
    players_text = "\n".join([f"• <b>{p['name']}</b> — ❤️ {p['hp']}/{p['max_hp']} HP{' 🎯' if p.get('aim') else ''}" for _, p in alive_players])
    if not players_text: players_text = "💀 Все погибли"
    turn_name = '?'
    if alive_players:
        idx = game.get('turn_idx', 0) % len(alive_players)
        turn_name = alive_players[idx][1]['name']
    hp_pct = int((game['boss_hp'] / game['boss_max_hp']) * 100) if game['boss_max_hp'] else 0
    bar = '█' * (hp_pct // 10) + '░' * (10 - hp_pct // 10)
    text = (
        f"🐉 <b>{game['boss_name']}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❤️ HP: <b>{game['boss_hp']}/{game['boss_max_hp']}</b>\n"
        f"{bar} {hp_pct}%\n\n"
        f"<b>КОМАНДА:</b>\n{players_text}\n\n"
        f"🎯 Ход: <b>{turn_name}</b>"
    )
    if game.get('last_msg'):
        text += f"\n\n{game['last_msg']}"
    return text

def start_boss_fight(chat_id):
    game = get_boss(chat_id)
    if not game: return
    game['status'] = 'fight'
    game['turn_idx'] = 0
    game['last_msg'] = '⚔️ Бой начался!'
    for uid in game['players']:
        game['players'][uid]['aim'] = False
    save_boss_game(chat_id, game)
    try:
        msg = bot.send_message(chat_id, boss_fight_text(game), parse_mode='HTML', reply_markup=boss_fight_kb())
        game['fight_msg_id'] = msg.message_id
        save_boss_game(chat_id, game)
    except: pass

def next_boss_turn(game):
    alive = get_alive_players_sorted(game)
    if not alive: return
    game['turn_idx'] += 1
    if game['turn_idx'] % len(alive) == 0:
        boss_attack(game)

def boss_attack(game):
    alive = get_alive_players_sorted(game)
    if not alive: return
    target_uid, target = random.choice(alive)
    dmg = random.randint(BOSS_DMG_MIN, BOSS_DMG_MAX)
    target['hp'] = max(0, target['hp'] - dmg)
    msg = f"👹 Босс атакует <b>{target['name']}</b> на <b>{dmg}</b> HP!"
    if target['hp'] <= 0:
        target['alive'] = False
        msg += f"\n💀 <b>{target['name']}</b> погиб!"
    game['last_msg'] = msg

@bot.callback_query_handler(func=lambda c: c.data.startswith('boss_fight_'))
def boss_fight_cb(call):
    chat_id = call.message.chat.id
    game = get_boss(chat_id)
    if not game or game['status'] != 'fight':
        bot.answer_callback_query(call.id, "❌ Бой не идёт")
        return
    uid = str(call.from_user.id)
    if uid not in game['players'] or not game['players'][uid]['alive']:
        bot.answer_callback_query(call.id, "💀 Не можешь ходить")
        return
    alive = get_alive_players_sorted(game)
    if not alive:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    idx = game['turn_idx'] % len(alive)
    current_uid = alive[idx][0]
    if uid != current_uid:
        bot.answer_callback_query(call.id, "🎯 Не твой ход")
        return
    p = game['players'][uid]

    if call.data == 'boss_fight_aim':
        p['aim'] = True
        game['last_msg'] = f"🎯 <b>{p['name']}</b> прицелился!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        if check_boss_end(chat_id, game): return
        safe_edit(chat_id, game.get('fight_msg_id'), boss_fight_text(game), boss_fight_kb())
        bot.answer_callback_query(call.id, "🎯")
        return

    if call.data == 'boss_fight_atk':
        dmg = random.randint(BOSS_ATK_MIN, BOSS_ATK_MAX)
        if p.get('aim'):
            dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
        game['boss_hp'] = max(0, game['boss_hp'] - dmg)
        p['dmg_done'] = p.get('dmg_done', 0) + dmg
        game['last_msg'] = f"🔫 <b>{p['name']}</b> бьёт на <b>{dmg}</b>!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        if check_boss_end(chat_id, game): return
        safe_edit(chat_id, game.get('fight_msg_id'), boss_fight_text(game), boss_fight_kb())
        bot.answer_callback_query(call.id, f"🔫 {dmg}")
        return

    if call.data == 'boss_fight_bat':
        if random.random() < BOSS_BAT_HIT_CHANCE:
            dmg = random.randint(BOSS_BAT_MIN, BOSS_BAT_MAX)
            if p.get('aim'):
                dmg = int(dmg * BOSS_AIM_BONUS); p['aim'] = False
            game['boss_hp'] = max(0, game['boss_hp'] - dmg)
            p['dmg_done'] = p.get('dmg_done', 0) + dmg
            game['last_msg'] = f"🏏 <b>{p['name']}</b> бьёт битой на <b>{dmg}</b>!"
        else:
            if p.get('aim'): p['aim'] = False
            game['last_msg'] = f"🏏 <b>{p['name']}</b> промахнулся!"
        next_boss_turn(game)
        save_boss_game(chat_id, game)
        if check_boss_end(chat_id, game): return
        safe_edit(chat_id, game.get('fight_msg_id'), boss_fight_text(game), boss_fight_kb())
        bot.answer_callback_query(call.id, "🏏")
        return

def check_boss_end(chat_id, game):
    if game['boss_hp'] <= 0:
        game['status'] = 'finished'
        save_boss_game(chat_id, game)
        eggs = game['boss_eggs']
        msg = (
            f"🏆 <b>БОСС ПОВЕРЖЕН!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐉 <b>{game['boss_name']}</b>\n\n"
            f"<b>Награды:</b>\n"
        )
        for uid, p in game['players'].items():
            add_boss_win(uid, eggs)
            msg += f"• {p['name']} — <b>{p.get('dmg_done',0)}</b> урона, <b>+{eggs} 🥚</b>\n"
        safe_edit(chat_id, game.get('fight_msg_id'), msg)
        del_boss(chat_id)
        return True
    alive = [uid for uid, p in game['players'].items() if p['alive']]
    if not alive:
        game['status'] = 'finished'
        save_boss_game(chat_id, game)
        for uid in game['players']:
            add_boss_loss(uid)
        safe_edit(chat_id, game.get('fight_msg_id'),
            f"💀 <b>ВСЕ ПОГИБЛИ!</b>\n━━━━━━━━━━━━━━━\nБосс выжил.")
        del_boss(chat_id)
        return True
    return False

# ===== ДУЭЛИ =====
@bot.message_handler(commands=['duel'])
def cmd_duel(message):
    remember_group(message.chat)
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, "⚔️ Только в группах.")
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
    update_username(message.from_user.id, message.from_user.first_name, message.from_user.username)
    existing = get_duel(message.chat.id)
    if existing and existing.get('status') in ('pending','active'):
        bot.send_message(message.chat.id, "⚔️ Уже идёт дуэль.")
        return
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
    sent = bot.send_message(message.chat.id, build_duel_pending_text(duel), parse_mode='HTML', reply_markup=kb)
    duel['msg_id'] = sent.message_id
    save_duel(message.chat.id, duel)
    threading.Timer(DUEL_ACCEPT_TIMEOUT, duel_timeout, args=[message.chat.id]).start()

def build_duel_pending_text(duel):
    left = duel['deadline'] - int(time.time())
    return (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{duel['p1_name']}</b>\n"
        f"     ⚔️ вызывает\n"
        f"🥷 <b>{duel['p2_name']}</b>\n\n"
        f"<i>{duel['p2_name']}, ты принимаешь?</i>\n\n"
        f"⏱ Осталось: <b>{fmt_time(left)}</b>"
    )

def duel_timeout(chat_id):
    duel = get_duel(chat_id)
    if not duel or duel.get('status') != 'pending': return
    safe_edit(chat_id, duel.get('msg_id'), "⌛ Время вышло. Вызов отменён.")
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
        f"⚔️ <b>ДУЭЛЬ</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🥷 <b>{duel['p1_name']}</b>: ❤️ <b>{duel['p1_hp']}</b> HP{p1_aim}\n"
        f"🥷 <b>{duel['p2_name']}</b>: ❤️ <b>{duel['p2_hp']}</b> HP{p2_aim}\n\n"
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
        bot.answer_callback_query(call.id, "Не найдена")
        return
    uid = str(call.from_user.id)
    update_username(uid, call.from_user.first_name, call.from_user.username)

    if call.data == 'duel_accept':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Неактуально")
            return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов")
            return
        duel['status'] = 'active'
        duel['last_action_msg'] = ''
        save_duel(chat_id, duel)
        safe_edit(chat_id, duel['msg_id'], duel_status_text(duel), duel_kb(duel))
        bot.answer_callback_query(call.id, "⚔️ Началась!")
        return

    if call.data == 'duel_decline':
        if duel.get('status') != 'pending':
            bot.answer_callback_query(call.id, "❌ Неактуально")
            return
        if uid != duel['p2_id']:
            bot.answer_callback_query(call.id, "❌ Не твой вызов")
            return
        del_duel(chat_id)
        safe_edit(chat_id, duel['msg_id'], "❌ Отклонено.")
        bot.answer_callback_query(call.id, "Отклонено")
        return

    if duel.get('status') != 'active':
        bot.answer_callback_query(call.id, "Не идёт")
        return
    if uid != duel['turn']:
        bot.answer_callback_query(call.id, "🎯 Не твой ход")
        return

    if call.data == 'duel_aim':
        if uid == duel['p1_id']: duel['p1_aim'] = True
        else: duel['p2_aim'] = True
        duel['last_action_msg'] = "🎯 <i>Игрок прицелился!</i>"
        next_turn(duel)
        save_duel(chat_id, duel)
        safe_edit(chat_id, duel['msg_id'], duel_status_text(duel), duel_kb(duel))
        bot.answer_callback_query(call.id, "🎯")
        return

    if call.data == 'duel_distract':
        if uid == duel['p1_id']:
            had = duel['p2_aim']; duel['p2_aim'] = False
        else:
            had = duel['p1_aim']; duel['p1_aim'] = False
        msg = random.choice(DISTRACT_MESSAGES)
        msg += "\n💥 <b>Прицел сбит!</b>" if had else "\n🤷 <i>Прицела не было.</i>"
        duel['last_action_msg'] = msg
        next_turn(duel)
        save_duel(chat_id, duel)
        safe_edit(chat_id, duel['msg_id'], duel_status_text(duel), duel_kb(duel))
        bot.answer_callback_query(call.id, "🎭")
        return

    if call.data == 'duel_shoot':
        if uid == duel['p1_id']:
            aim = duel['p1_aim']; duel['p1_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p2_hp'] = max(0, duel['p2_hp'] - dmg)
                msg = f"💥 Попадание! <b>-{dmg}</b> HP"
            else: msg = "🌫 Промах!"
        else:
            aim = duel['p2_aim']; duel['p2_aim'] = False
            chance = DUEL_AIM_BONUS if aim else DUEL_NOAIM_CHANCE
            if random.random() < chance:
                dmg = random.randint(DUEL_SHOOT_MIN, DUEL_SHOOT_MAX)
                duel['p1_hp'] = max(0, duel['p1_hp'] - dmg)
                msg = f"💥 Попадание! <b>-{dmg}</b> HP"
            else: msg = "🌫 Промах!"
        duel['last_action_msg'] = msg
        if duel['p1_hp'] <= 0 or duel['p2_hp'] <= 0:
            winner_id = duel['p1_id'] if duel['p2_hp'] <= 0 else duel['p2_id']
            loser_id = duel['p2_id'] if winner_id == duel['p1_id'] else duel['p1_id']
            winner_name = duel['p1_name'] if winner_id == duel['p1_id'] else duel['p2_name']
            add_duel_win(winner_id)
            add_duel_loss(loser_id)
            del_duel(chat_id)
            safe_edit(chat_id, call.message.message_id,
                f"🏆 <b>ДУЭЛЬ ОКОНЧЕНА</b>\n━━━━━━━━━━━━━━━\n\n{msg}\n\n🥇 Победил: <b>{winner_name}</b>")
            bot.answer_callback_query(call.id, "🏆")
            return
        next_turn(duel)
        save_duel(chat_id, duel)
        safe_edit(chat_id, duel['msg_id'], duel_status_text(duel), duel_kb(duel))
        bot.answer_callback_query(call.id)

# ===== МЕНЮ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith('menu_'))
def menu_cb(call):
    data = call.data
    uid = call.from_user.id
    update_username(uid, call.from_user.first_name, call.from_user.username)
    if data == 'menu_profile':
        cmd_profile(call.message)
    elif data == 'menu_top':
        cmd_top(call.message)
    elif data == 'menu_duel':
        bot.send_message(call.message.chat.id, "⚔️ В группе ответь на сообщение игрока и напиши /duel")
    elif data == 'menu_boss':
        bot.send_message(call.message.chat.id, "🐉 Напиши /boss1 ... /boss7 чтобы выбрать босса")
    elif data == 'menu_eggs':
        bot.send_message(call.message.chat.id, eggs_menu_text(uid), parse_mode='HTML', reply_markup=eggs_menu_kb())
    elif data == 'menu_help':
        cmd_help(call.message)
    elif data == 'menu_back':
        bot.send_message(call.message.chat.id, "🎭 Меню:", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

def set_commands():
    try:
        cmds = [
            types.BotCommand('start', '🎭 Меню'),
            types.BotCommand('help', '💬 Помощь'),
            types.BotCommand('profile', '👤 Профиль'),
            types.BotCommand('top', '🏆 Топ'),
            types.BotCommand('duel', '⚔️ Дуэль'),
            types.BotCommand('eggs', '🥚 Яйца'),
        ]
        if ADMIN_IDS:
            cmds.append(types.BotCommand('post_new', '📢 Создать пост'))
        bot.set_my_commands(cmds)
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()
