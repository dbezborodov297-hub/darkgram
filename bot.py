import telebot
import time
import threading
import random
import json
import os
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ==================== НАСТРОЙКИ ====================
TOKEN = '8514412667:AAHN-vz-JKdZcwj2eHV000x6g-fRPXyJWLk'
WEBAPP_URL = 'https://darkgram-2.onrender.com'

START_GRAM = 0
VERIFY_BONUS = 100
MIN_BET = 10
MAX_BET = 500

TRADE_TICK = 3
MAX_TRADE_TIME = 120
AUTO_CLOSE_MULT = 0.5

USERS_FILE = 'users.json'
NFT_FILE = 'nft.json'
MARKET_FILE = 'market.json'
SHOP_FILE = 'shop_prices.json'

NFT_TYPES = {
    'glass':    {'emoji': '🍸', 'name': 'Glass',    'price': 50,   'max': 5,  'bonus': 0.1},
    'fountain': {'emoji': '⛲', 'name': 'Fountain', 'price': 450,  'max': 7,  'bonus': 0.1},
    'seat':     {'emoji': '💺', 'name': 'Seat',     'price': 650,  'max': 11, 'bonus': 0.1},
    'disc':     {'emoji': '📀', 'name': 'Disc',     'price': 2500, 'max': 25, 'bonus': 0.1},
    'statue':   {'emoji': '🗽', 'name': 'Statue',   'price': 320,  'max': 12, 'bonus': 0.1},
    'lotus':    {'emoji': '🪷', 'name': 'Lotus',    'price': 45,   'max': 35, 'bonus': 0.1},
    'yoyo':     {'emoji': '🪀', 'name': 'YoYo',     'price': 950,  'max': 7,  'bonus': 0.1},
    '8ball':    {'emoji': '🎱', 'name': '8Ball',    'price': 1000, 'max': 17, 'bonus': 0.1},
}

SKIN_TYPES = {
    'soccer':   {'emoji': '⚽', 'name': 'Soccer',   'price': 1090},
    'baseball': {'emoji': '⚾', 'name': 'Baseball', 'price': 1320},
    'softball': {'emoji': '🥎', 'name': 'Softball', 'price': 1020},
    'basket':   {'emoji': '🏀', 'name': 'Basket',   'price': 1160},
    'volley':   {'emoji': '🏐', 'name': 'Volley',   'price': 1200},
}

TASKS_BY_DAY = {
    1: [
        {'id': 'trade1',  'text': 'Сделай 1 сделку в трейдинге'},
        {'id': 'trade3',  'text': 'Сделай 3 сделки'},
        {'id': 'buy_bit', 'text': 'Купи любой биткоин'},
        {'id': 'earn50',  'text': 'Заработай 50 GRAM'},
        {'id': 'nft1',    'text': 'Купи 1 любой NFT'},
    ],
    2: [
        {'id': 'trade5',  'text': 'Сделай 5 сделок'},
        {'id': 'nft2',    'text': 'Купи 2 NFT'},
        {'id': 'sell_nft','text': 'Выставь NFT на продажу'},
        {'id': 'earn100', 'text': 'Заработай 100 GRAM'},
        {'id': 'buy_bit2','text': 'Купи 2 биткоина'},
    ],
    3: [
        {'id': 'trade7',  'text': 'Сделай 7 сделок'},
        {'id': 'nft3',    'text': 'Купи 3 NFT'},
        {'id': 'earn200', 'text': 'Заработай 200 GRAM'},
        {'id': 'buy_skin','text': 'Купи 1 скин'},
        {'id': 'win3',    'text': 'Выиграй 3 сделки'},
    ],
    4: [
        {'id': 'trade10', 'text': 'Сделай 10 сделок'},
        {'id': 'nft5',    'text': 'Купи 5 NFT'},
        {'id': 'earn300', 'text': 'Заработай 300 GRAM'},
        {'id': 'skin2',   'text': 'Купи 2 скина'},
        {'id': 'win5',    'text': 'Выиграй 5 сделок'},
    ],
    5: [
        {'id': 'trade15', 'text': 'Сделай 15 сделок'},
        {'id': 'nft7',    'text': 'Купи 7 NFT'},
        {'id': 'earn500', 'text': 'Заработай 500 GRAM'},
        {'id': 'sell3',   'text': 'Продай 3 NFT'},
        {'id': 'win8',    'text': 'Выиграй 8 сделок'},
    ],
    6: [
        {'id': 'trade20', 'text': 'Сделай 20 сделок'},
        {'id': 'nft10',   'text': 'Купи 10 NFT'},
        {'id': 'earn700', 'text': 'Заработай 700 GRAM'},
        {'id': 'skin3',   'text': 'Купи 3 скина'},
        {'id': 'win12',   'text': 'Выиграй 12 сделок'},
    ],
    7: [
        {'id': 'trade25', 'text': 'Сделай 25 сделок'},
        {'id': 'nft12',   'text': 'Купи 12 NFT'},
        {'id': 'earn1000','text': 'Заработай 1000 GRAM'},
        {'id': 'buy_all', 'text': 'Купи все типы биткоинов'},
        {'id': 'win15',   'text': 'Выиграй 15 сделок'},
    ],
    8: [
        {'id': 'trade30', 'text': 'Сделай 30 сделок'},
        {'id': 'nft15',   'text': 'Купи 15 NFT'},
        {'id': 'earn1500','text': 'Заработай 1500 GRAM'},
        {'id': 'skin5',   'text': 'Купи 5 скинов'},
        {'id': 'win20',   'text': 'Выиграй 20 сделок'},
    ],
    9: [
        {'id': 'trade40', 'text': 'Сделай 40 сделок'},
        {'id': 'nft20',   'text': 'Купи 20 NFT'},
        {'id': 'earn2000','text': 'Заработай 2000 GRAM'},
        {'id': 'sell5',   'text': 'Продай 5 NFT'},
        {'id': 'win25',   'text': 'Выиграй 25 сделок'},
    ],
    10: [
        {'id': 'trade50', 'text': 'Сделай 50 сделок'},
        {'id': 'nft25',   'text': 'Купи 25 NFT'},
        {'id': 'earn3000','text': 'Заработай 3000 GRAM'},
        {'id': 'skin7',   'text': 'Купи 7 скинов'},
        {'id': 'win30',   'text': 'Выиграй 30 сделок'},
    ],
}
TASK_REWARD = 20

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)

try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Webhook deleted')
except Exception as e:
    print('webhook err:', e)


def btn(text, data, style=None):
    if style:
        try:
            return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
        except TypeError:
            return types.InlineKeyboardButton(text=text, callback_data=data)
    return types.InlineKeyboardButton(text=text, callback_data=data)


USERS = {}
USERS_LOCK = threading.Lock()

NFT_DATA = {}
NFT_LOCK = threading.Lock()

MARKET = {}
MARKET_LOCK = threading.Lock()

SHOP = {}
SHOP_LOCK = threading.Lock()

ACTIVE_TRADES = {}
TRADES_LOCK = threading.Lock()

NEXT_NFT_ID = 1


CURRENCIES = {
    'GRAM':     {'name': '💎 GRAM',     'start': 1.00,  'volatility': 0.05},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'start': 2.50,  'volatility': 0.07},
    'DRK':      {'name': '🖤 DRK',      'start': 5.00,  'volatility': 0.10},
    'BSG':      {'name': '⚡ BSG•BST',  'start': 10.00, 'volatility': 0.12},
    'WWR':      {'name': '📢 WWR',      'start': 25.00, 'volatility': 0.15},
}

RATES = {k: v['start'] for k, v in CURRENCIES.items()}
RATES_LOCK = threading.Lock()


# ==================== HTTP ====================
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


# ==================== ХРАНИЛИЩА ====================
def load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return default

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'save {path} err:', e)

def load_users():
    global USERS
    USERS = load_json(USERS_FILE, {})

def save_users(): save_json(USERS_FILE, USERS)

def load_nft():
    global NFT_DATA, NEXT_NFT_ID
    NFT_DATA = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    if 'minted' not in NFT_DATA: NFT_DATA['minted'] = {}
    if 'items' not in NFT_DATA: NFT_DATA['items'] = {}
    max_id = 0
    for nid in NFT_DATA['items']:
        try:
            num = int(nid.split('-')[1])
            if num > max_id: max_id = num
        except: pass
    NEXT_NFT_ID = max_id + 1

def save_nft(): save_json(NFT_FILE, NFT_DATA)

def load_market():
    global MARKET
    MARKET = load_json(MARKET_FILE, {})

def save_market(): save_json(MARKET_FILE, MARKET)

def load_shop():
    global SHOP
    SHOP = load_json(SHOP_FILE, {})
    for cur in ['DRK', 'DARKGRAM', 'BSG']:
        if cur not in SHOP: SHOP[cur] = {'percent': 0, 'updated': 0}

def save_shop(): save_json(SHOP_FILE, SHOP)


load_users()
load_nft()
load_market()
load_shop()


def get_user(uid):
    key = str(uid)
    if key not in USERS:
        USERS[key] = {
            'name': '', 'gram': START_GRAM, 'verified': False,
            'wins': 0, 'losses': 0, 'total_profit': 0,
            'shop': {}, 'wwr': False,
            'nfts': [], 'skins': [],
            'day': 1, 'tasks_done': {}, 'tasks_date': '',
            'stats': {'trades': 0, 'wins_trade': 0, 'bought_nft': 0, 'sold_nft': 0, 'earned': 0, 'bought_skins': 0, 'bought_bit': 0},
        }
        save_users()
    u = USERS[key]
    if 'nfts' not in u: u['nfts'] = []
    if 'skins' not in u: u['skins'] = []
    if 'day' not in u: u['day'] = 1
    if 'tasks_done' not in u: u['tasks_done'] = {}
    if 'tasks_date' not in u: u['tasks_date'] = ''
    if 'stats' not in u:
        u['stats'] = {'trades': 0, 'wins_trade': 0, 'bought_nft': 0, 'sold_nft': 0, 'earned': 0, 'bought_skins': 0, 'bought_bit': 0}
    return u


def get_nft_bonus(uid):
    u = get_user(uid)
    return len(u.get('nfts', [])) * 0.1


def update_rates():
    with RATES_LOCK:
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            change = random.uniform(-info['volatility'], info['volatility'])
            RATES[cur] = max(0.01, round(rate * (1 + change), 4))


def get_chance_up(cur):
    with RATES_LOCK:
        rate = RATES[cur]
        start = CURRENCIES[cur]['start']
    diff = (rate - start) / start
    return round(max(15, min(85, 50 - diff * 100)))


def rate_loop():
    while True:
        try: update_rates()
        except: pass
        time.sleep(TRADE_TICK)

threading.Thread(target=rate_loop, daemon=True).start()


def shop_loop():
    while True:
        try:
            with SHOP_LOCK:
                now = int(time.time())
                for cur in ['DRK', 'DARKGRAM', 'BSG']:
                    if now - SHOP[cur].get('updated', 0) > 1800:
                        if cur == 'DRK': SHOP[cur]['percent'] = random.choice([15, 20, 25, 30])
                        elif cur == 'DARKGRAM': SHOP[cur]['percent'] = random.choice([3, 5, 7, 10])
                        elif cur == 'BSG': SHOP[cur]['percent'] = random.choice([5, 10, 15])
                        SHOP[cur]['updated'] = now
                save_shop()
        except: pass
        time.sleep(60)

threading.Thread(target=shop_loop, daemon=True).start()


# ==================== ТРЕЙД ====================
class Trade:
    def __init__(self, uid, cur, bet):
        self.uid = uid
        self.cur = cur
        self.bet = bet
        self.open_rate = RATES[cur]
        self.open_time = time.time()
        self.msg_id = None
        self.chat_id = None
        self.lock = threading.Lock()
        self.closed = False


def trade_profit(trade):
    with RATES_LOCK: rate = RATES[trade.cur]
    mult = rate / trade.open_rate
    profit = trade.bet * (mult - 1)
    nft_bonus = get_nft_bonus(trade.uid)
    if profit > 0: profit = profit * (1 + nft_bonus)
    return round(profit, 2), mult


def trade_loop_for(trade):
    while not trade.closed:
        try:
            profit, mult = trade_profit(trade)
            if mult <= AUTO_CLOSE_MULT:
                close_trade(trade, auto=True); return
            if time.time() - trade.open_time > MAX_TRADE_TIME:
                close_trade(trade, auto=True); return
            update_trade_message(trade, profit, mult)
        except: pass
        time.sleep(TRADE_TICK)


def update_trade_message(trade, profit, mult):
    try:
        with RATES_LOCK: rate = RATES[trade.cur]
        chance = get_chance_up(trade.cur)
        arrow = '📈' if chance >= 50 else '📉'
        sign = '+' if profit >= 0 else ''
        pnl = '🟢' if profit > 0 else ('🔴' if profit < 0 else '⚪')
        text = (
            f'{CURRENCIES[trade.cur]["name"]} — торговля\n'
            f'━━━━━━━━━━━━━━━\n\n'
            f'💰 Ставка: {trade.bet} GRAM\n'
            f'📊 Курс: {trade.open_rate:.4f} → {rate:.4f}\n'
            f'✖️ Множитель: {mult:.2f}x\n'
            f'{pnl} P&L: {sign}{profit} GRAM\n\n'
            f'{arrow} Вверх: {chance}% | Вниз: {100-chance}%'
        )
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(btn('ЗАКРЫТЬ', f'close_{trade.uid}', 'danger'))
        kb.add(btn('Обновить', f'refresh_{trade.uid}', 'primary'))
        bot.edit_message_text(text, chat_id=trade.chat_id, message_id=trade.msg_id, reply_markup=kb)
    except: pass


def close_trade(trade, auto=False):
    with trade.lock:
        if trade.closed: return
        trade.closed = True

    profit, mult = trade_profit(trade)

    with USERS_LOCK:
        u = get_user(trade.uid)
        u['gram'] = round(u.get('gram', 0) + trade.bet + profit, 2)
        u['stats']['trades'] = u['stats'].get('trades', 0) + 1
        if profit > 0:
            u['wins'] = u.get('wins', 0) + 1
            u['total_profit'] = round(u.get('total_profit', 0) + profit, 2)
            u['stats']['wins_trade'] = u['stats'].get('wins_trade', 0) + 1
            u['stats']['earned'] = round(u['stats'].get('earned', 0) + profit, 2)
        elif profit < 0:
            u['losses'] = u.get('losses', 0) + 1
        save_users()
        gram = u['gram']

    sign = '+' if profit >= 0 else ''
    pnl = '🟢' if profit > 0 else ('🔴' if profit < 0 else '⚪')
    reason = ' (авто)' if auto else ''
    text = (
        f'✅ СДЕЛКА{reason}\n━━━━━━━━━━━━━━━\n\n'
        f'{CURRENCIES[trade.cur]["name"]}\n'
        f'Курс: {trade.open_rate:.4f} → {RATES[trade.cur]:.4f}\n'
        f'{pnl} Итог: {sign}{profit} GRAM\n\n'
        f'💼 Баланс: {gram} GRAM'
    )
    try: bot.edit_message_text(text, chat_id=trade.chat_id, message_id=trade.msg_id)
    except: pass

    with TRADES_LOCK:
        if trade.uid in ACTIVE_TRADES: del ACTIVE_TRADES[trade.uid]


@bot.callback_query_handler(func=lambda c: c.data.startswith('close_'))
def cb_close(call):
    uid = int(call.data.replace('close_', ''))
    if call.from_user.id != uid:
        bot.answer_callback_query(call.id, 'Не твоя'); return
    with TRADES_LOCK: trade = ACTIVE_TRADES.get(uid)
    if not trade:
        bot.answer_callback_query(call.id, 'Закрыта'); return
    bot.answer_callback_query(call.id, 'Закрываю...')
    close_trade(trade)


@bot.callback_query_handler(func=lambda c: c.data.startswith('refresh_'))
def cb_refresh(call): bot.answer_callback_query(call.id, 'ОК')


# ==================== ЗАДАНИЯ ====================
def today_str(): return date.today().isoformat()


def check_tasks_reset(u):
    if u.get('tasks_date', '') != today_str():
        u['tasks_date'] = today_str()
        u['tasks_done'] = {}
        save_users()


def get_tasks_for_user(uid):
    u = get_user(uid)
    check_tasks_reset(u)
    day = u.get('day', 1)
    if day > 10: day = 10
    return TASKS_BY_DAY.get(day, [])


def task_completed(uid, tid):
    u = get_user(uid)
    check_tasks_reset(u)
    s = u.get('stats', {})
    if tid.startswith('trade'):
        try: n = int(tid.replace('trade', ''))
        except: n = 0
        return s.get('trades', 0) >= n
    if tid.startswith('win'):
        try: n = int(tid.replace('win', ''))
        except: n = 0
        return s.get('wins_trade', 0) >= n
    if tid.startswith('nft'):
        try: n = int(tid.replace('nft', ''))
        except: n = 0
        return s.get('bought_nft', 0) >= n
    if tid.startswith('earn'):
        try: n = int(tid.replace('earn', ''))
        except: n = 0
        return s.get('earned', 0) >= n
    if tid.startswith('sell'):
        if tid == 'sell_nft': return s.get('sold_nft', 0) >= 1
        try: n = int(tid.replace('sell', ''))
        except: n = 0
        return s.get('sold_nft', 0) >= n
    if tid.startswith('skin'):
        try: n = int(tid.replace('skin', ''))
        except: n = 0
        return s.get('bought_skins', 0) >= n
    if tid == 'buy_bit': return s.get('bought_bit', 0) >= 1
    if tid == 'buy_bit2': return s.get('bought_bit', 0) >= 2
    if tid == 'buy_skin': return s.get('bought_skins', 0) >= 1
    if tid == 'buy_all': return len(u.get('shop', {})) >= 3
    return False


def claim_task(uid, tid):
    u = get_user(uid)
    check_tasks_reset(u)
    if tid in u.get('tasks_done', {}): return False
    if not task_completed(uid, tid): return False
    u['tasks_done'][tid] = True
    u['gram'] = round(u.get('gram', 0) + TASK_REWARD, 2)
    save_users()
    return True


@bot.callback_query_handler(func=lambda c: c.data == 'menu_tasks')
def cb_menu_tasks(call):
    uid = call.from_user.id
    u = get_user(uid)
    check_tasks_reset(u)
    tasks = get_tasks_for_user(uid)
    day = u.get('day', 1)
    if day > 10: day = 10

    text = f'🎯 ЗАДАНИЯ ДНЯ {day}/10\n━━━━━━━━━━━━━━━\n\n+{TASK_REWARD} GRAM за каждое\n\n'
    kb = types.InlineKeyboardMarkup(row_width=1)
    done_count = 0
    for t in tasks:
        done = t['id'] in u.get('tasks_done', {})
        done_count += 1 if done else 0
        if done:
            text += f'✅ {t["text"]}\n'
            kb.add(btn(f'✅ {t["text"]}', f'task_done_{t["id"]}', 'success'))
        elif task_completed(uid, t['id']):
            text += f'🎁 {t["text"]} — ГОТОВО\n'
            kb.add(btn(f'🎁 Забрать: {t["text"]}', f'task_claim_{t["id"]}', 'success'))
        else:
            text += f'⏳ {t["text"]}\n'
            kb.add(btn(f'⏳ {t["text"]}', f'task_na_{t["id"]}', 'danger'))
    text += f'\nВыполнено: {done_count}/{len(tasks)}'
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('task_claim_'))
def cb_task_claim(call):
    tid = call.data.replace('task_claim_', '')
    if claim_task(call.from_user.id, tid):
        bot.answer_callback_query(call.id, f'✅ +{TASK_REWARD} GRAM!')
    else:
        bot.answer_callback_query(call.id, '❌ Не выполнено')
    cb_menu_tasks(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith('task_done_'))
def cb_task_done(call): bot.answer_callback_query(call.id, '✅ Уже')


@bot.callback_query_handler(func=lambda c: c.data.startswith('task_na_'))
def cb_task_na(call): bot.answer_callback_query(call.id, '⏳ Не готово')


# ==================== МЕНЮ ====================
def main_menu(uid=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn('📈 Трейдинг', 'menu_trade', 'primary'),
        btn('🛒 Магазин', 'menu_shop', 'success')
    )
    kb.add(
        btn('🎨 NFT', 'menu_nft', 'primary'),
        btn('🏪 Рынок', 'menu_market', 'success')
    )
    kb.add(
        btn('🎯 Задания', 'menu_tasks', 'success'),
        btn('👛 Кошелёк', 'menu_wallet', 'primary')
    )
    kb.add(btn('🏆 Топ GRAM', 'menu_top', 'success'))
    kb.add(btn('📊 Курсы валют', 'menu_rates', 'primary'))
    kb.add(btn('ℹ️ Как играть', 'menu_how', 'primary'))
    return kb


def webapp_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🎮 Открыть игру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    return kb


@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    u = get_user(uid)
    u['name'] = m.from_user.first_name or 'Player'
    save_users()

    text = (
        f'💎 DARKGRAM TRADE\n━━━━━━━━━━━━━━━\n\n'
        f'👋 Привет, {m.from_user.first_name}!\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'🎨 NFT: {len(u.get("nfts", []))} шт\n'
        f'📅 День: {u.get("day", 1)}/10\n'
        f'✅ Верификация: {"✅" if u["verified"] else "❌"}\n\n'
        f'👇 Играй кнопкой ниже или в боте:'
    )
    bot.send_message(m.chat.id, text, reply_markup=webapp_kb())
    bot.send_message(m.chat.id, 'Меню:', reply_markup=main_menu(uid))


@bot.message_handler(commands=['help'])
def cmd_help(m): cmd_start(m)


@bot.message_handler(commands=['game'])
def cmd_game(m):
    bot.send_message(m.chat.id, '🎮 Открой игру:', reply_markup=webapp_kb())


@bot.callback_query_handler(func=lambda c: c.data == 'menu_back')
def cb_menu_back(call):
    uid = call.from_user.id
    u = get_user(uid)
    text = (
        f'💎 DARKGRAM TRADE\n━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'🎨 NFT: {len(u.get("nfts", []))} шт\n'
        f'📅 День: {u.get("day", 1)}/10\n'
        f'✅ Верификация: {"✅" if u["verified"] else "❌"}\n\n'
        f'👇 Выбери:'
    )
    kb = main_menu(uid)
    if not u['verified']:
        kb.add(btn('🎯 Верификация (+100 GRAM)', 'verify', 'success'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'verify')
def cb_verify(call):
    uid = call.from_user.id
    u = get_user(uid)
    if u.get('verified'):
        bot.answer_callback_query(call.id, 'Уже'); return
    with USERS_LOCK:
        u['verified'] = True
        u['gram'] = u.get('gram', 0) + VERIFY_BONUS
        save_users()
    bot.answer_callback_query(call.id, f'✅ +{VERIFY_BONUS} GRAM!')
    bot.send_message(call.message.chat.id, f'🎉 +{VERIFY_BONUS} GRAM')
    cb_menu_back(call)


# ==================== ТРЕЙДИНГ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_trade')
def cb_menu_trade(call):
    u = get_user(call.from_user.id)
    if not u['verified']:
        bot.answer_callback_query(call.id, 'Пройди верификацию'); return
    if call.from_user.id in ACTIVE_TRADES:
        bot.answer_callback_query(call.id, 'Уже есть сделка'); return
    bot.answer_callback_query(call.id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for cur in CURRENCIES:
        with RATES_LOCK: rate = RATES[cur]
        kb.add(btn(f'{CURRENCIES[cur]["name"]} ({rate:.2f})', f'trade_cur_{cur}', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    text = f'📈 ТРЕЙДИНГ\n━━━━━━━━━━━━━━━\n\n💼 Баланс: {u["gram"]} GRAM\n📊 {MIN_BET}–{MAX_BET}\n\n👇 Валюта:'
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('trade_cur_'))
def cb_trade_cur(call):
    cur = call.data.replace('trade_cur_', '')
    if cur not in CURRENCIES: return
    uid = call.from_user.id
    u = get_user(uid)
    with RATES_LOCK: rate = RATES[cur]
    chance = get_chance_up(cur)
    arrow = '📈' if chance >= 50 else '📉'
    text = (
        f'{CURRENCIES[cur]["name"]}\n━━━━━━━━━━━━━━━\n\n'
        f'📊 Курс: {rate:.4f}\n{arrow} Вверх: {chance}% | Вниз: {100-chance}%\n\n'
        f'💼 Баланс: {u["gram"]}\n\n✍️ Сумма:'
    )
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, text)
    bot.register_next_step_handler(msg, process_bet, cur)


def process_bet(m, cur):
    uid = m.from_user.id
    u = get_user(uid)
    try: bet = float(m.text.strip())
    except: bot.reply_to(m, '❌ Число'); return
    if bet < MIN_BET or bet > MAX_BET:
        bot.reply_to(m, f'❌ {MIN_BET}–{MAX_BET}'); return
    if bet > u.get('gram', 0):
        bot.reply_to(m, f'❌ Только {u["gram"]}'); return

    with USERS_LOCK:
        u['gram'] = round(u['gram'] - bet, 2)
        save_users()

    trade = Trade(uid, cur, bet)
    with TRADES_LOCK: ACTIVE_TRADES[uid] = trade

    with RATES_LOCK: rate = RATES[cur]
    chance = get_chance_up(cur)
    arrow = '📈' if chance >= 50 else '📉'
    text = (
        f'{CURRENCIES[cur]["name"]}\n━━━━━━━━━━━━━━━\n\n'
        f'💰 Ставка: {bet} GRAM\n📊 Курс: {rate:.4f}\n'
        f'{arrow} Вверх: {chance}% | Вниз: {100-chance}%'
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('ЗАКРЫТЬ', f'close_{uid}', 'danger'))
    kb.add(btn('Обновить', f'refresh_{uid}', 'primary'))
    msg = bot.send_message(m.chat.id, text, reply_markup=kb)
    trade.msg_id = msg.message_id
    trade.chat_id = m.chat.id
    threading.Thread(target=trade_loop_for, args=(trade,), daemon=True).start()


# ==================== NFT ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_nft')
def cb_menu_nft(call):
    uid = call.from_user.id
    u = get_user(uid)
    with NFT_LOCK: minted = NFT_DATA.get('minted', {})
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, info in NFT_TYPES.items():
        sold = minted.get(key, 0)
        left = info['max'] - sold
        if left > 0:
            kb.add(btn(f'{info["emoji"]} {info["name"]} — {sold}/{info["max"]} — {info["price"]} GRAM',
                       f'nft_buy_{key}', 'success'))
        else:
            kb.add(btn(f'{info["emoji"]} {info["name"]} — {sold}/{info["max"]} — РАСПРОДАНО',
                       'nft_sold', 'danger'))
    kb.add(btn('📦 Мои NFT', 'nft_my', 'primary'))
    kb.add(btn('🎨 Купить скины', 'skins_menu', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    text = (
        f'🎨 NFT DROP\n━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]}\n🎨 NFT: {len(u.get("nfts", []))}\n'
        f'💰 Бонус: +{get_nft_bonus(uid):.1f}x'
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'nft_sold')
def cb_nft_sold(call): bot.answer_callback_query(call.id, '❌ Распродано', show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_buy_'))
def cb_nft_buy(call):
    global NEXT_NFT_ID
    key = call.data.replace('nft_buy_', '')
    if key not in NFT_TYPES: return
    info = NFT_TYPES[key]
    uid = call.from_user.id
    u = get_user(uid)
    with NFT_LOCK:
        sold = NFT_DATA.get('minted', {}).get(key, 0)
        if sold >= info['max']:
            bot.answer_callback_query(call.id, 'Распродано'); return
        if u.get('gram', 0) < info['price']:
            bot.answer_callback_query(call.id, 'Мало GRAM'); return
        with USERS_LOCK:
            u['gram'] -= info['price']
            nid = f'N-{NEXT_NFT_ID:04d}'
            NEXT_NFT_ID += 1
            u['nfts'] = u.get('nfts', []) + [nid]
            u['stats']['bought_nft'] = u['stats'].get('bought_nft', 0) + 1
            save_users()
        NFT_DATA['minted'][key] = sold + 1
        NFT_DATA['items'][nid] = {'type': key, 'owner': uid, 'skin': None, 'bought_at': int(time.time())}
        save_nft()
    bot.answer_callback_query(call.id, f'✅ {nid}')
    bot.send_message(call.message.chat.id, f'🎉 Куплен {info["emoji"]}\nID: <code>{nid}</code>', parse_mode='HTML')
    cb_menu_nft(call)


@bot.callback_query_handler(func=lambda c: c.data == 'nft_my')
def cb_nft_my(call):
    uid = call.from_user.id
    u = get_user(uid)
    nfts = u.get('nfts', [])
    if not nfts:
        text = '📦 Нет NFT.'
        kb = types.InlineKeyboardMarkup()
        kb.add(btn('◀️ Назад', 'menu_nft', 'danger'))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        bot.answer_callback_query(call.id); return
    text = '📦 МОИ NFT\n━━━━━━━━━━━━━━━\n\n'
    kb = types.InlineKeyboardMarkup(row_width=1)
    for nid in nfts:
        with NFT_LOCK: item = NFT_DATA['items'].get(nid)
        if not item: continue
        info = NFT_TYPES[item['type']]
        skin = ''
        if item.get('skin'): skin = ' + ' + SKIN_TYPES[item['skin']]['emoji']
        text += f'{info["emoji"]}{skin} {nid}\n'
        kb.add(btn(f'{info["emoji"]}{skin} {nid}', f'nft_item_{nid}', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_nft', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_item_'))
def cb_nft_item(call):
    nid = call.data.replace('nft_item_', '')
    uid = call.from_user.id
    with NFT_LOCK: item = NFT_DATA['items'].get(nid)
    if not item or item['owner'] != uid:
        bot.answer_callback_query(call.id, 'Не твой'); return
    info = NFT_TYPES[item['type']]
    with MARKET_LOCK:
        on_sale = nid in MARKET
        price = MARKET[nid]['price'] if on_sale else 0
    skin_txt = ''
    if item.get('skin'): skin_txt = f'\nСкин: {SKIN_TYPES[item["skin"]]["emoji"]}'
    kb = types.InlineKeyboardMarkup(row_width=1)
    if on_sale:
        kb.add(btn(f'❌ Снять ({price} GRAM)', f'nft_unsell_{nid}', 'danger'))
    else:
        kb.add(btn('💰 На продажу', f'nft_sell_{nid}', 'success'))
    kb.add(btn('🎨 Сменить скин', f'nft_skin_{nid}', 'primary'))
    kb.add(btn('◀️ Назад', 'nft_my', 'danger'))
    text = (
        f'{info["emoji"]} {info["name"]}{skin_txt}\n━━━━━━━━━━━━━━━\n\n'
        f'ID: <code>{nid}</code>\nБонус: +{info["bonus"]}x\n'
        f'Статус: {"🏪 За " + str(price) if on_sale else "✅ В кошельке"}'
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=kb, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode='HTML')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_sell_'))
def cb_nft_sell(call):
    nid = call.data.replace('nft_sell_', '')
    uid = call.from_user.id
    with NFT_LOCK: item = NFT_DATA['items'].get(nid)
    if not item or item['owner'] != uid:
        bot.answer_callback_query(call.id, 'Не твой'); return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        f'💰 За сколько GRAM продать <code>{nid}</code>?', parse_mode='HTML')
    bot.register_next_step_handler(msg, process_sell, nid)


def process_sell(m, nid):
    uid = m.from_user.id
    try:
        price = float(m.text.strip())
        if price <= 0: raise ValueError
    except:
        bot.reply_to(m, '❌ Число'); return
    with MARKET_LOCK:
        MARKET[nid] = {'seller': uid, 'price': round(price, 2), 'listed_at': int(time.time())}
    save_market()
    bot.reply_to(m, f'✅ <code>{nid}</code> за {price} GRAM', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_unsell_'))
def cb_nft_unsell(call):
    nid = call.data.replace('nft_unsell_', '')
    uid = call.from_user.id
    with MARKET_LOCK:
        if nid in MARKET and MARKET[nid]['seller'] == uid:
            del MARKET[nid]
            save_market()
            bot.answer_callback_query(call.id, '✅ Снято')
        else:
            bot.answer_callback_query(call.id, 'Не найдено')


# ==================== СКИНЫ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'skins_menu')
def cb_skins_menu(call):
    uid = call.from_user.id
    u = get_user(uid)
    has = len(u.get('nfts', [])) > 0
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, info in SKIN_TYPES.items():
        kb.add(btn(f'{info["emoji"]} {info["name"]} — {info["price"]} GRAM',
                   f'skin_buy_{key}', 'success'))
    kb.add(btn('◀️ Назад', 'menu_nft', 'danger'))
    warn = '' if has else '\n\n⚠️ Сначала купи NFT!'
    text = f'🎨 СКИНЫ\n━━━━━━━━━━━━━━━\n\n💼 {u["gram"]} GRAM\n🎨 NFT: {len(u.get("nfts", []))}{warn}'
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('skin_buy_'))
def cb_skin_buy(call):
    key = call.data.replace('skin_buy_', '')
    if key not in SKIN_TYPES: return
    info = SKIN_TYPES[key]
    uid = call.from_user.id
    u = get_user(uid)
    if not u.get('nfts'):
        bot.answer_callback_query(call.id, '❌ Сначала NFT', show_alert=True); return
    if u.get('gram', 0) < info['price']:
        bot.answer_callback_query(call.id, 'Мало GRAM'); return
    with USERS_LOCK:
        u['gram'] -= info['price']
        u['skins'] = u.get('skins', []) + [key]
        u['stats']['bought_skins'] = u['stats'].get('bought_skins', 0) + 1
        save_users()
    bot.answer_callback_query(call.id, f'✅ {info["emoji"]}')
    msg = bot.send_message(call.message.chat.id, f'✅ Куплен {info["emoji"]}\n\nНа какой NFT надеть? ID:', parse_mode='HTML')
    bot.register_next_step_handler(msg, process_skin_attach, key)


def process_skin_attach(m, skin_key):
    uid = m.from_user.id
    nid = m.text.strip().upper()
    u = get_user(uid)
    if nid not in u.get('nfts', []):
        bot.reply_to(m, f'❌ <code>{nid}</code> не найден', parse_mode='HTML'); return
    with NFT_LOCK:
        item = NFT_DATA['items'].get(nid)
        if not item: return
        item['skin'] = skin_key
        save_nft()
    bot.reply_to(m, f'✅ {SKIN_TYPES[skin_key]["emoji"]} на <code>{nid}</code>', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_skin_'))
def cb_nft_skin(call):
    nid = call.data.replace('nft_skin_', '')
    uid = call.from_user.id
    u = get_user(uid)
    if nid not in u.get('nfts', []):
        bot.answer_callback_query(call.id, 'Не твой'); return
    if not u.get('skins'):
        bot.answer_callback_query(call.id, 'Нет скинов'); return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key in u['skins']:
        info = SKIN_TYPES.get(key)
        if info:
            kb.add(btn(f'{info["emoji"]} {info["name"]}', f'skin_set_{nid}_{key}', 'primary'))
    kb.add(btn('◀️ Назад', f'nft_item_{nid}', 'danger'))
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text('Выбери скин:', chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('skin_set_'))
def cb_skin_set(call):
    parts = call.data.replace('skin_set_', '').split('_', 1)
    if len(parts) != 2: return
    nid, skin_key = parts
    uid = call.from_user.id
    u = get_user(uid)
    if nid not in u.get('nfts', []): return
    with NFT_LOCK:
        item = NFT_DATA['items'].get(nid)
        if item:
            item['skin'] = skin_key
            save_nft()
    bot.answer_callback_query(call.id, '✅')


# ==================== РЫНОК ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_market')
def cb_menu_market(call):
    with MARKET_LOCK: items = list(MARKET.items())
    if not items:
        text = '🏪 РЫНОК ПУСТ'
        kb = types.InlineKeyboardMarkup()
        kb.add(btn('🆔 Купить по ID', 'market_byid', 'primary'))
        kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        bot.answer_callback_query(call.id); return
    text = '🏪 РЫНОК\n━━━━━━━━━━━━━━━\n\n'
    kb = types.InlineKeyboardMarkup(row_width=1)
    for nid, data in items[:10]:
        with NFT_LOCK: item = NFT_DATA['items'].get(nid)
        if not item: continue
        info = NFT_TYPES[item['type']]
        seller = get_user(data['seller'])
        skin = ''
        if item.get('skin'): skin = ' + ' + SKIN_TYPES[item['skin']]['emoji']
        text += f'{info["emoji"]}{skin} {nid} — {data["price"]} GRAM\n{seller.get("name","?")}\n\n'
        kb.add(btn(f'💎 Купить {nid} — {data["price"]}', f'market_buy_{nid}', 'success'))
    kb.add(btn('🆔 Купить по ID', 'market_byid', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('market_buy_'))
def cb_market_buy(call):
    nid = call.data.replace('market_buy_', '')
    do_market_buy(call, nid)


@bot.callback_query_handler(func=lambda c: c.data == 'market_byid')
def cb_market_byid(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, '🆔 ID NFT:')
    bot.register_next_step_handler(msg, process_buy_byid)


def process_buy_byid(m):
    nid = m.text.strip().upper()
    with MARKET_LOCK:
        if nid not in MARKET:
            bot.reply_to(m, f'❌ <code>{nid}</code> не найден', parse_mode='HTML'); return
    do_market_buy_msg(m, nid)


def do_market_buy(call, nid):
    buyer = call.from_user.id
    with MARKET_LOCK:
        if nid not in MARKET:
            bot.answer_callback_query(call.id, 'Нет'); return
        data = MARKET[nid]
        seller = data['seller']; price = data['price']
    if buyer == seller:
        bot.answer_callback_query(call.id, 'Твой'); return
    bu = get_user(buyer)
    if bu.get('gram', 0) < price:
        bot.answer_callback_query(call.id, 'Мало GRAM'); return
    with USERS_LOCK:
        bu['gram'] = round(bu['gram'] - price, 2)
        su = get_user(seller)
        su['gram'] = round(su.get('gram', 0) + price, 2)
        if nid in su.get('nfts', []): su['nfts'].remove(nid)
        bu['nfts'] = bu.get('nfts', []) + [nid]
        su['stats']['sold_nft'] = su['stats'].get('sold_nft', 0) + 1
        save_users()
    with NFT_LOCK:
        NFT_DATA['items'][nid]['owner'] = buyer
        save_nft()
    with MARKET_LOCK:
        if nid in MARKET: del MARKET[nid]
        save_market()
    bot.answer_callback_query(call.id, f'✅ За {price}')
    bot.send_message(call.message.chat.id, f'🎉 Куплен <code>{nid}</code> за {price}', parse_mode='HTML')
    try: bot.send_message(seller, f'💰 Твой <code>{nid}</code> купили за {price}!', parse_mode='HTML')
    except: pass


def do_market_buy_msg(m, nid):
    buyer = m.from_user.id
    with MARKET_LOCK: data = MARKET.get(nid)
    if not data: bot.reply_to(m, 'Нет'); return
    seller = data['seller']; price = data['price']
    if buyer == seller: bot.reply_to(m, 'Твой'); return
    bu = get_user(buyer)
    if bu.get('gram', 0) < price:
        bot.reply_to(m, f'❌ Нужно {price}'); return
    with USERS_LOCK:
        bu['gram'] = round(bu['gram'] - price, 2)
        su = get_user(seller)
        su['gram'] = round(su.get('gram', 0) + price, 2)
        if nid in su.get('nfts', []): su['nfts'].remove(nid)
        bu['nfts'] = bu.get('nfts', []) + [nid]
        su['stats']['sold_nft'] = su['stats'].get('sold_nft', 0) + 1
        save_users()
    with NFT_LOCK:
        NFT_DATA['items'][nid]['owner'] = buyer
        save_nft()
    with MARKET_LOCK:
        if nid in MARKET: del MARKET[nid]
        save_market()
    bot.reply_to(m, f'🎉 <code>{nid}</code> за {price}', parse_mode='HTML')
    try: bot.send_message(seller, f'💰 <code>{nid}</code> купили за {price}!', parse_mode='HTML')
    except: pass


# ==================== КОШЕЛЁК ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_wallet')
def cb_menu_wallet(call):
    u = get_user(call.from_user.id)
    text = (
        f'👛 КОШЕЛЁК\n━━━━━━━━━━━━━━━\n\n'
        f'💎 GRAM: {u.get("gram", 0)}\n'
        f'🏆 Побед: {u.get("wins", 0)}\n'
        f'💔 Поражений: {u.get("losses", 0)}\n'
        f'📈 Профит: {u.get("total_profit", 0)}\n'
        f'🎨 NFT: {len(u.get("nfts", []))} (+{get_nft_bonus(call.from_user.id):.1f}x)\n'
        f'🎨 Скинов: {len(u.get("skins", []))}'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== ТОП ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_top')
def cb_menu_top(call):
    arr = sorted([(u.get('name', 'Player'), u.get('gram', 0)) for u in USERS.values()],
                 key=lambda x: x[1], reverse=True)
    text = '🏆 ТОП GRAM\n━━━━━━━━━━━━━━━\n\n'
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    for i, (name, gram) in enumerate(arr[:20], 1):
        text += f'{medals.get(i, str(i) + ".")} {name} — {gram} GRAM\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== КУРСЫ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_rates')
def cb_menu_rates(call):
    text = '📊 КУРСЫ\n━━━━━━━━━━━━━━━\n\n'
    with RATES_LOCK:
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            change = ((rate - info['start']) / info['start']) * 100
            arrow = '📈' if change >= 0 else '📉'
            sign = '+' if change >= 0 else ''
            text += f'{info["name"]}\n{arrow} {rate:.4f} ({sign}{change:.2f}%)\n\n'
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('🔄 Обновить', 'menu_rates', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== МАГАЗИН ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_shop')
def cb_menu_shop(call):
    uid = call.from_user.id
    u = get_user(uid)
    with SHOP_LOCK:
        drk = SHOP.get('DRK', {}).get('percent', 20)
        dg = SHOP.get('DARKGRAM', {}).get('percent', 5)
        bsg = SHOP.get('BSG', {}).get('percent', 10)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn(f'🖤 DRK (+{drk}%) — 50 GRAM', 'buy_DRK', 'success'))
    kb.add(btn(f'🌑 DARKGRAM (+{dg}%) — 75 GRAM', 'buy_DARKGRAM', 'success'))
    kb.add(btn(f'⚡ BSG•BST (+{bsg}%) — 100 GRAM', 'buy_BSG', 'success'))
    kb.add(btn('📢 WWR (+50%) — 100 GRAM', 'buy_WWR', 'success'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    text = f'🛒 МАГАЗИН\n━━━━━━━━━━━━━━━\n\n💼 {u["gram"]} GRAM'
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def cb_buy(call):
    item = call.data.replace('buy_', '')
    uid = call.from_user.id
    u = get_user(uid)
    prices = {'DRK': 50, 'DARKGRAM': 75, 'BSG': 100, 'WWR': 100}
    if item == 'WWR':
        if u.get('wwr'): bot.answer_callback_query(call.id, 'Уже'); return
        if u.get('gram', 0) < 100: bot.answer_callback_query(call.id, 'Мало'); return
        with USERS_LOCK:
            u['gram'] -= 100; u['wwr'] = True; save_users()
        bot.answer_callback_query(call.id, '✅')
    else:
        if item not in prices: return
        if u.get('shop', {}).get(item): bot.answer_callback_query(call.id, 'Уже'); return
        if u.get('gram', 0) < prices[item]: bot.answer_callback_query(call.id, 'Мало'); return
        with USERS_LOCK:
            u['gram'] -= prices[item]
            if 'shop' not in u: u['shop'] = {}
            u['shop'][item] = True
            u['stats']['bought_bit'] = u['stats'].get('bought_bit', 0) + 1
            save_users()
        bot.answer_callback_query(call.id, '✅')
    cb_menu_shop(call)


# ==================== КАК ИГРАТЬ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_how')
def cb_menu_how(call):
    text = (
        'ℹ️ КАК ИГРАТЬ\n━━━━━━━━━━━━━━━\n\n'
        '🎮 Mini App — кнопка «Открыть игру»\n\n'
        '1️⃣ Верификация → +100 GRAM\n'
        '2️⃣ Трейдинг — ставки, курс 3 сек\n'
        '3️⃣ Задания — 10 дней × 5 × +20 GRAM\n'
        '4️⃣ NFT — 8 видов, +0.1x к прибыли\n'
        '5️⃣ Скины — на NFT\n'
        '6️⃣ Рынок — продажа NFT\n'
        '7️⃣ Магазин биткоинов\n'
        '🏆 Топ по GRAM!'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('Bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
