import telebot
import time
import threading
import random
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

# ==================== НАСТРОЙКИ ====================
TOKEN = '8514412667:AAFbNzWkRVsnAO6V4H7C_kq1XHjGaeQT8hA'

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

# NFT: всего штук на весь бот
NFT_TYPES = {
    'glass':  {'emoji': '🍸', 'name': 'Glass',    'price': 50,  'max': 5,  'bonus': 0.1},
    'fountain': {'emoji': '⛲', 'name': 'Fountain', 'price': 450, 'max': 7,  'bonus': 0.1},
    'seat':   {'emoji': '💺', 'name': 'Seat',     'price': 650, 'max': 11, 'bonus': 0.1},
}

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)

try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Webhook deleted')
except Exception as e:
    print('webhook err:', e)


def btn(text, data, style=None):
    try:
        return types.InlineKeyboardButton(text=text, callback_data=data, style=style)
    except TypeError:
        return types.InlineKeyboardButton(text=text, callback_data=data)


USERS = {}
USERS_LOCK = threading.Lock()

NFT_DATA = {}       # {'minted': {'glass': 3, 'fountain': 5}, 'items': {nft_id: {...}}}
NFT_LOCK = threading.Lock()

MARKET = {}         # {nft_id: {'seller': uid, 'price': N}}
MARKET_LOCK = threading.Lock()

SHOP = {}
SHOP_LOCK = threading.Lock()

ACTIVE_TRADES = {}
TRADES_LOCK = threading.Lock()

NEXT_NFT_ID = 1


# ==================== ВАЛЮТЫ ====================
CURRENCIES = {
    'GRAM':     {'name': '💎 GRAM',     'start': 1.00,  'volatility': 0.05},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'start': 2.50,  'volatility': 0.07},
    'DRK':      {'name': '🖤 DRK',      'start': 5.00,  'volatility': 0.10},
    'BSG':      {'name': '⚡ BSG•BST',  'start': 10.00, 'volatility': 0.12},
    'WWR':      {'name': '📢 WWR',      'start': 25.00, 'volatility': 0.15},
}

RATES = {k: v['start'] for k, v in CURRENCIES.items()}
RATES_LOCK = threading.Lock()


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


# ==================== ХРАНИЛИЩА ====================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'save {path} err:', e)


def load_users():
    global USERS
    USERS = load_json(USERS_FILE, {})

def save_users():
    save_json(USERS_FILE, USERS)

def load_nft():
    global NFT_DATA, NEXT_NFT_ID
    NFT_DATA = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    if 'minted' not in NFT_DATA: NFT_DATA['minted'] = {}
    if 'items' not in NFT_DATA: NFT_DATA['items'] = {}
    # вычисляем следующий ID
    max_id = 0
    for nid in NFT_DATA['items']:
        try:
            num = int(nid.split('-')[1])
            if num > max_id: max_id = num
        except: pass
    NEXT_NFT_ID = max_id + 1

def save_nft():
    save_json(NFT_FILE, NFT_DATA)

def load_market():
    global MARKET
    MARKET = load_json(MARKET_FILE, {})

def save_market():
    save_json(MARKET_FILE, MARKET)

def load_shop():
    global SHOP
    SHOP = load_json(SHOP_FILE, {})
    for cur in ['DRK', 'DARKGRAM', 'BSG']:
        if cur not in SHOP:
            SHOP[cur] = {'percent': 0, 'updated': 0}

def save_shop():
    save_json(SHOP_FILE, SHOP)


load_users()
load_nft()
load_market()
load_shop()


# ==================== ПОЛЬЗОВАТЕЛЬ ====================
def get_user(uid):
    key = str(uid)
    if key not in USERS:
        USERS[key] = {
            'name': '',
            'gram': START_GRAM,
            'verified': False,
            'wins': 0,
            'losses': 0,
            'total_profit': 0,
            'shop': {},
            'wwr': False,
            'nfts': [],   # список ID NFT
        }
        save_users()
    if 'nfts' not in USERS[key]:
        USERS[key]['nfts'] = []
    return USERS[key]


def get_user_nft_bonus(uid):
    """Бонус от NFT: +0.1 за каждый."""
    u = get_user(uid)
    nfts = u.get('nfts', [])
    return len(nfts) * 0.1


# ==================== КУРСЫ ====================
def update_rates():
    with RATES_LOCK:
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            vol = info['volatility']
            change = random.uniform(-vol, vol)
            new_rate = max(0.01, round(rate * (1 + change), 4))
            RATES[cur] = new_rate


def get_chance_up(cur):
    with RATES_LOCK:
        rate = RATES[cur]
        start = CURRENCIES[cur]['start']
    diff = (rate - start) / start
    chance = 50 - diff * 100
    return round(max(15, min(85, chance)))


def rate_loop():
    while True:
        try:
            update_rates()
        except Exception as e:
            print('rate err:', e)
        time.sleep(TRADE_TICK)


threading.Thread(target=rate_loop, daemon=True).start()


def shop_loop():
    while True:
        try:
            with SHOP_LOCK:
                now = int(time.time())
                for cur in ['DRK', 'DARKGRAM', 'BSG']:
                    if now - SHOP[cur].get('updated', 0) > 1800:
                        if cur == 'DRK':
                            SHOP[cur]['percent'] = random.choice([15, 20, 25, 30])
                        elif cur == 'DARKGRAM':
                            SHOP[cur]['percent'] = random.choice([3, 5, 7, 10])
                        elif cur == 'BSG':
                            SHOP[cur]['percent'] = random.choice([5, 10, 15])
                        SHOP[cur]['updated'] = now
                save_shop()
        except Exception as e:
            print('shop err:', e)
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
    with RATES_LOCK:
        rate = RATES[trade.cur]
    mult = rate / trade.open_rate
    profit = trade.bet * (mult - 1)
    # NFT бонус
    nft_bonus = get_user_nft_bonus(trade.uid)
    if profit > 0:
        profit = profit * (1 + nft_bonus)
    return round(profit, 2), mult


def trade_loop_for(trade):
    while not trade.closed:
        try:
            profit, mult = trade_profit(trade)
            if mult <= AUTO_CLOSE_MULT:
                close_trade(trade, auto=True)
                return
            if time.time() - trade.open_time > MAX_TRADE_TIME:
                close_trade(trade, auto=True)
                return
            update_trade_message(trade, profit, mult)
        except Exception as e:
            print('trade err:', e)
        time.sleep(TRADE_TICK)


def update_trade_message(trade, profit, mult):
    try:
        with RATES_LOCK:
            rate = RATES[trade.cur]
        chance = get_chance_up(trade.cur)
        arrow = '📈' if chance >= 50 else '📉'
        sign = '+' if profit >= 0 else ''
        pnl_emoji = '🟢' if profit > 0 else ('🔴' if profit < 0 else '⚪')

        text = (
            f'{CURRENCIES[trade.cur]["name"]} — торговля\n'
            f'━━━━━━━━━━━━━━━\n\n'
            f'💰 Ставка: {trade.bet} GRAM\n'
            f'📊 Курс открытия: {trade.open_rate:.4f}\n'
            f'📈 Текущий курс: {rate:.4f}\n'
            f'✖️ Множитель: {mult:.2f}x\n'
            f'{pnl_emoji} P&L: {sign}{profit} GRAM\n\n'
            f'{arrow} Шанс вверх: {chance}% | Вниз: {100-chance}%\n\n'
            f'⏱ Осталось: {max(0, int(MAX_TRADE_TIME - (time.time()-trade.open_time)))} сек'
        )

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(btn('ЗАКРЫТЬ СДЕЛКУ', f'close_{trade.uid}', 'danger'))
        kb.add(btn('Обновить', f'refresh_{trade.uid}', 'primary'))

        bot.edit_message_text(text, chat_id=trade.chat_id, message_id=trade.msg_id, reply_markup=kb)
    except:
        pass


def close_trade(trade, auto=False):
    with trade.lock:
        if trade.closed:
            return
        trade.closed = True

    profit, mult = trade_profit(trade)

    with USERS_LOCK:
        u = get_user(trade.uid)
        u['gram'] = round(u.get('gram', 0) + trade.bet + profit, 2)
        if profit > 0:
            u['wins'] = u.get('wins', 0) + 1
            u['total_profit'] = round(u.get('total_profit', 0) + profit, 2)
        elif profit < 0:
            u['losses'] = u.get('losses', 0) + 1
        save_users()

    sign = '+' if profit >= 0 else ''
    pnl_emoji = '🟢' if profit > 0 else ('🔴' if profit < 0 else '⚪')
    reason = ' (авто)' if auto else ''

    text = (
        f'✅ СДЕЛКА ЗАКРЫТА{reason}\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'{CURRENCIES[trade.cur]["name"]}\n'
        f'💰 Ставка: {trade.bet} GRAM\n'
        f'📊 Курс: {trade.open_rate:.4f} → {RATES[trade.cur]:.4f}\n'
        f'✖️ Множитель: {mult:.2f}x\n'
        f'{pnl_emoji} Итог: {sign}{profit} GRAM\n\n'
        f'💼 Баланс: {u["gram"]} GRAM'
    )

    try:
        bot.edit_message_text(text, chat_id=trade.chat_id, message_id=trade.msg_id)
    except:
        pass

    with TRADES_LOCK:
        if trade.uid in ACTIVE_TRADES:
            del ACTIVE_TRADES[trade.uid]


@bot.callback_query_handler(func=lambda c: c.data.startswith('close_'))
def cb_close(call):
    uid = int(call.data.replace('close_', ''))
    if call.from_user.id != uid:
        bot.answer_callback_query(call.id, 'Не твоя сделка')
        return
    with TRADES_LOCK:
        trade = ACTIVE_TRADES.get(uid)
    if not trade:
        bot.answer_callback_query(call.id, 'Сделка закрыта')
        return
    bot.answer_callback_query(call.id, 'Закрываю...')
    close_trade(trade)


@bot.callback_query_handler(func=lambda c: c.data.startswith('refresh_'))
def cb_refresh(call):
    bot.answer_callback_query(call.id, 'Обновлено')


# ==================== МЕНЮ ====================
def main_menu():
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
        btn('👛 Кошелёк', 'menu_wallet', 'primary'),
        btn('🏆 Топ GRAM', 'menu_top', 'success')
    )
    kb.add(btn('📊 Курсы валют', 'menu_rates', 'primary'))
    kb.add(btn('ℹ️ Как играть', 'menu_how', 'primary'))
    return kb


@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    u = get_user(uid)
    u['name'] = m.from_user.first_name or 'Player'
    save_users()

    text = (
        f'💎 DARKGRAM TRADE\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👋 Привет, {m.from_user.first_name}!\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'🎨 NFT: {len(u.get("nfts", []))} шт\n'
        f'✅ Верификация: {"✅" if u["verified"] else "❌"}\n\n'
        f'👇 Выбери действие:'
    )

    kb = main_menu()
    if not u['verified']:
        kb.add(btn('🎯 Пройти верификацию (+100 GRAM)', 'verify', 'success'))

    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.message_handler(commands=['help'])
def cmd_help(m):
    cmd_start(m)


# ==================== КОЛБЭКИ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_back')
def cb_menu_back(call):
    uid = call.from_user.id
    u = get_user(uid)
    text = (
        f'💎 DARKGRAM TRADE\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'🎨 NFT: {len(u.get("nfts", []))} шт\n'
        f'✅ Верификация: {"✅" if u["verified"] else "❌"}\n\n'
        f'👇 Выбери действие:'
    )
    kb = main_menu()
    if not u['verified']:
        kb.add(btn('🎯 Пройти верификацию (+100 GRAM)', 'verify', 'success'))
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
        bot.answer_callback_query(call.id, 'Уже пройдена')
        return
    with USERS_LOCK:
        u['verified'] = True
        u['gram'] = u.get('gram', 0) + VERIFY_BONUS
        save_users()
    bot.answer_callback_query(call.id, f'✅ +{VERIFY_BONUS} GRAM!')
    bot.send_message(call.message.chat.id,
        f'🎉 Верификация пройдена!\n\n💎 +{VERIFY_BONUS} GRAM')
    cb_menu_back(call)


# ==================== ТРЕЙДИНГ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_trade')
def cb_menu_trade(call):
    u = get_user(call.from_user.id)
    if not u['verified']:
        bot.answer_callback_query(call.id, 'Пройди верификацию')
        return
    if call.from_user.id in ACTIVE_TRADES:
        bot.answer_callback_query(call.id, 'У тебя уже есть открытая сделка')
        return
    bot.answer_callback_query(call.id)

    kb = types.InlineKeyboardMarkup(row_width=2)
    for cur in CURRENCIES:
        with RATES_LOCK:
            rate = RATES[cur]
        kb.add(btn(f'{CURRENCIES[cur]["name"]} ({rate:.2f})', f'trade_cur_{cur}', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))

    text = (
        f'📈 ТРЕЙДИНГ\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'📊 Ставка: от {MIN_BET} до {MAX_BET} GRAM\n\n'
        f'👇 Выбери валюту:'
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith('trade_cur_'))
def cb_trade_cur(call):
    cur = call.data.replace('trade_cur_', '')
    if cur not in CURRENCIES:
        return
    uid = call.from_user.id
    u = get_user(uid)
    with RATES_LOCK:
        rate = RATES[cur]
    chance = get_chance_up(cur)
    arrow = '📈' if chance >= 50 else '📉'

    text = (
        f'{CURRENCIES[cur]["name"]}\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'📊 Курс: {rate:.4f}\n'
        f'{arrow} Шанс вверх: {chance}% | Вниз: {100-chance}%\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'📊 Ставка: {MIN_BET}–{MAX_BET}\n\n'
        f'✍️ Напиши сумму ставки числом:'
    )
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, text)
    bot.register_next_step_handler(msg, process_bet, cur)


def process_bet(m, cur):
    uid = m.from_user.id
    u = get_user(uid)
    try:
        bet = float(m.text.strip())
    except:
        bot.reply_to(m, '❌ Напиши число. Например: 100')
        return
    if bet < MIN_BET:
        bot.reply_to(m, f'❌ Минимум: {MIN_BET} GRAM')
        return
    if bet > MAX_BET:
        bot.reply_to(m, f'❌ Максимум: {MAX_BET} GRAM')
        return
    if bet > u.get('gram', 0):
        bot.reply_to(m, f'❌ У тебя только {u["gram"]} GRAM')
        return

    with USERS_LOCK:
        u['gram'] = round(u['gram'] - bet, 2)
        save_users()

    trade = Trade(uid, cur, bet)
    with TRADES_LOCK:
        ACTIVE_TRADES[uid] = trade

    with RATES_LOCK:
        rate = RATES[cur]
    chance = get_chance_up(cur)
    arrow = '📈' if chance >= 50 else '📉'

    text = (
        f'{CURRENCIES[cur]["name"]} — торговля\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💰 Ставка: {bet} GRAM\n'
        f'📊 Курс открытия: {rate:.4f}\n'
        f'{arrow} Шанс вверх: {chance}% | Вниз: {100-chance}%\n\n'
        f'⏱ Макс: {MAX_TRADE_TIME} сек'
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn('ЗАКРЫТЬ СДЕЛКУ', f'close_{uid}', 'danger'))
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

    with NFT_LOCK:
        minted = NFT_DATA.get('minted', {})

    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, info in NFT_TYPES.items():
        sold = minted.get(key, 0)
        left = info['max'] - sold
        if left > 0:
            kb.add(btn(
                f'{info["emoji"]} {info["name"]} — {sold}/{info["max"]} — {info["price"]} GRAM',
                f'nft_buy_{key}', 'success'
            ))
        else:
            kb.add(btn(
                f'{info["emoji"]} {info["name"]} — {sold}/{info["max"]} — РАСПРОДАНО',
                'nft_sold', 'danger'
            ))
    kb.add(btn('📦 Мои NFT', 'nft_my', 'primary'))
    kb.add(btn('◀️ Назад', 'menu_back', 'danger'))

    text = (
        f'🎨 NFT DROP\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'🎨 Моих NFT: {len(u.get("nfts", []))}\n'
        f'💰 Бонус: +{get_user_nft_bonus(uid):.1f}x к прибыли\n\n'
        f'💡 NFT дают +0.1 к прибыли. Лимит — на весь бот!'
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'nft_sold')
def cb_nft_sold(call):
    bot.answer_callback_query(call.id, '❌ Распродано', show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_buy_'))
def cb_nft_buy(call):
    global NEXT_NFT_ID
    key = call.data.replace('nft_buy_', '')
    if key not in NFT_TYPES:
        return
    info = NFT_TYPES[key]
    uid = call.from_user.id
    u = get_user(uid)

    with NFT_LOCK:
        sold = NFT_DATA.get('minted', {}).get(key, 0)
        if sold >= info['max']:
            bot.answer_callback_query(call.id, 'Распродано')
            return
        if u.get('gram', 0) < info['price']:
            bot.answer_callback_query(call.id, 'Недостаточно GRAM')
            return

        with USERS_LOCK:
            u['gram'] -= info['price']
            nft_id = f'N-{NEXT_NFT_ID:04d}'
            NEXT_NFT_ID += 1
            u['nfts'] = u.get('nfts', []) + [nft_id]
            save_users()

        NFT_DATA['minted'][key] = sold + 1
        NFT_DATA['items'][nft_id] = {
            'type': key,
            'owner': uid,
            'bought_at': int(time.time()),
        }
        save_nft()

    bot.answer_callback_query(call.id, f'✅ Куплено! ID: {nft_id}')
    bot.send_message(call.message.chat.id,
        f'🎉 Ты купил {info["emoji"]} {info["name"]}!\n\nID: <code>{nft_id}</code>\nБонус: +{info["bonus"]}x к прибыли',
        parse_mode='HTML')
    cb_menu_nft(call)


@bot.callback_query_handler(func=lambda c: c.data == 'nft_my')
def cb_nft_my(call):
    uid = call.from_user.id
    u = get_user(uid)
    nfts = u.get('nfts', [])

    if not nfts:
        text = '📦 У тебя нет NFT.'
        kb = types.InlineKeyboardMarkup()
        kb.add(btn('◀️ Назад', 'menu_nft', 'danger'))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        bot.answer_callback_query(call.id)
        return

    text = '📦 МОИ NFT\n━━━━━━━━━━━━━━━\n\n'
    kb = types.InlineKeyboardMarkup(row_width=1)

    for nid in nfts:
        with NFT_LOCK:
            item = NFT_DATA['items'].get(nid)
        if not item:
            continue
        info = NFT_TYPES[item['type']]
        with MARKET_LOCK:
            on_sale = nid in MARKET
        status = '🏪 На продаже' if on_sale else '✅ В кошельке'
        text += f'{info["emoji"]} {info["name"]}\n   ID: <code>{nid}</code>\n   {status}\n\n'
        kb.add(btn(f'{info["emoji"]} {nid}', f'nft_item_{nid}', 'primary'))

    kb.add(btn('◀️ Назад', 'menu_nft', 'danger'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=kb, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode='HTML')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_item_'))
def cb_nft_item(call):
    nid = call.data.replace('nft_item_', '')
    uid = call.from_user.id

    with NFT_LOCK:
        item = NFT_DATA['items'].get(nid)
    if not item or item['owner'] != uid:
        bot.answer_callback_query(call.id, 'Не твой NFT')
        return

    info = NFT_TYPES[item['type']]

    with MARKET_LOCK:
        on_sale = nid in MARKET
        price = MARKET[nid]['price'] if on_sale else 0

    kb = types.InlineKeyboardMarkup(row_width=1)
    if on_sale:
        kb.add(btn(f'❌ Снять с продажи ({price} GRAM)', f'nft_unsell_{nid}', 'danger'))
    else:
        kb.add(btn('💰 Выставить на продажу', f'nft_sell_{nid}', 'success'))
    kb.add(btn('◀️ Назад', 'nft_my', 'danger'))

    text = (
        f'{info["emoji"]} {info["name"]}\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'ID: <code>{nid}</code>\n'
        f'Бонус: +{info["bonus"]}x\n'
        f'Статус: {"🏪 На продаже за " + str(price) + " GRAM" if on_sale else "✅ В кошельке"}'
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
    with NFT_LOCK:
        item = NFT_DATA['items'].get(nid)
    if not item or item['owner'] != uid:
        bot.answer_callback_query(call.id, 'Не твой NFT')
        return
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        f'💰 За сколько GRAM продать <code>{nid}</code>?\n\nНапиши число:',
        parse_mode='HTML')
    bot.register_next_step_handler(msg, process_sell, nid)


def process_sell(m, nid):
    uid = m.from_user.id
    try:
        price = float(m.text.strip())
        if price <= 0:
            raise ValueError
    except:
        bot.reply_to(m, '❌ Напиши положительное число.')
        return

    with MARKET_LOCK:
        MARKET[nid] = {'seller': uid, 'price': round(price, 2), 'listed_at': int(time.time())}
    save_market()

    bot.reply_to(m, f'✅ <code>{nid}</code> выставлен за {price} GRAM', parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data.startswith('nft_unsell_'))
def cb_nft_unsell(call):
    nid = call.data.replace('nft_unsell_', '')
    uid = call.from_user.id
    with MARKET_LOCK:
        if nid in MARKET and MARKET[nid]['seller'] == uid:
            del MARKET[nid]
            save_market()
            bot.answer_callback_query(call.id, '✅ Снято с продажи')
        else:
            bot.answer_callback_query(call.id, 'Не найдено')


# ==================== РЫНОК ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_market')
def cb_menu_market(call):
    with MARKET_LOCK:
        items = list(MARKET.items())

    if not items:
        text = '🏪 РЫНОК ПУСТ\n━━━━━━━━━━━━━━━\n\nПока никто не выставил NFT на продажу.'
        kb = types.InlineKeyboardMarkup()
        kb.add(btn('🆔 Купить по ID', 'market_byid', 'primary'))
        kb.add(btn('◀️ Назад', 'menu_back', 'danger'))
        try:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        bot.answer_callback_query(call.id)
        return

    text = '🏪 РЫНОК NFT\n━━━━━━━━━━━━━━━\n\n'
    kb = types.InlineKeyboardMarkup(row_width=1)

    for nid, data in items[:10]:
        with NFT_LOCK:
            item = NFT_DATA['items'].get(nid)
        if not item:
            continue
        info = NFT_TYPES[item['type']]
        seller = get_user(data['seller'])
        text += f'{info["emoji"]} {nid} — {data["price"]} GRAM\n   Продавец: {seller.get("name", "?")}\n\n'
        kb.add(btn(f'💎 Купить {info["emoji"]} {nid} — {data["price"]} GRAM',
                   f'market_buy_{nid}', 'success'))

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
    msg = bot.send_message(call.message.chat.id, '🆔 Напиши ID NFT (например N-0001):')
    bot.register_next_step_handler(msg, process_buy_byid)


def process_buy_byid(m):
    nid = m.text.strip().upper()
    with MARKET_LOCK:
        if nid not in MARKET:
            bot.reply_to(m, f'❌ NFT <code>{nid}</code> не найден на рынке.', parse_mode='HTML')
            return
    do_market_buy_msg(m, nid)


def do_market_buy(call, nid):
    buyer = call.from_user.id
    with MARKET_LOCK:
        if nid not in MARKET:
            bot.answer_callback_query(call.id, 'Не найдено')
            return
        data = MARKET[nid]
        seller = data['seller']
        price = data['price']

    if buyer == seller:
        bot.answer_callback_query(call.id, 'Это твой NFT')
        return

    bu = get_user(buyer)
    if bu.get('gram', 0) < price:
        bot.answer_callback_query(call.id, 'Недостаточно GRAM')
        return

    with USERS_LOCK:
        bu['gram'] = round(bu['gram'] - price, 2)
        su = get_user(seller)
        su['gram'] = round(su.get('gram', 0) + price, 2)

        if nid in su.get('nfts', []):
            su['nfts'].remove(nid)
        bu['nfts'] = bu.get('nfts', []) + [nid]
        save_users()

    with NFT_LOCK:
        NFT_DATA['items'][nid]['owner'] = buyer
        save_nft()

    with MARKET_LOCK:
        if nid in MARKET:
            del MARKET[nid]
        save_market()

    bot.answer_callback_query(call.id, f'✅ Куплено за {price} GRAM')
    bot.send_message(call.message.chat.id,
        f'🎉 Ты купил <code>{nid}</code> за {price} GRAM!',
        parse_mode='HTML')
    try:
        bot.send_message(seller, f'💰 Твой NFT <code>{nid}</code> купили за {price} GRAM!',
                         parse_mode='HTML')
    except:
        pass


def do_market_buy_msg(m, nid):
    buyer = m.from_user.id
    with MARKET_LOCK:
        data = MARKET.get(nid)
    if not data:
        bot.reply_to(m, 'Не найдено')
        return
    seller = data['seller']
    price = data['price']

    if buyer == seller:
        bot.reply_to(m, 'Это твой NFT')
        return

    bu = get_user(buyer)
    if bu.get('gram', 0) < price:
        bot.reply_to(m, f'❌ Недостаточно GRAM. Нужно {price}, у тебя {bu["gram"]}')
        return

    with USERS_LOCK:
        bu['gram'] = round(bu['gram'] - price, 2)
        su = get_user(seller)
        su['gram'] = round(su.get('gram', 0) + price, 2)
        if nid in su.get('nfts', []):
            su['nfts'].remove(nid)
        bu['nfts'] = bu.get('nfts', []) + [nid]
        save_users()

    with NFT_LOCK:
        NFT_DATA['items'][nid]['owner'] = buyer
        save_nft()

    with MARKET_LOCK:
        if nid in MARKET:
            del MARKET[nid]
        save_market()

    bot.reply_to(m, f'🎉 Куплено <code>{nid}</code> за {price} GRAM!', parse_mode='HTML')
    try:
        bot.send_message(seller, f'💰 Твой NFT <code>{nid}</code> купили за {price} GRAM!',
                         parse_mode='HTML')
    except:
        pass


# ==================== КОШЕЛЁК ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_wallet')
def cb_menu_wallet(call):
    u = get_user(call.from_user.id)
    text = (
        f'👛 КОШЕЛЁК\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💎 GRAM: {u.get("gram", 0)}\n'
        f'🏆 Побед: {u.get("wins", 0)}\n'
        f'💔 Поражений: {u.get("losses", 0)}\n'
        f'📈 Профит: {u.get("total_profit", 0)}\n'
        f'🎨 NFT: {len(u.get("nfts", []))} шт (+{get_user_nft_bonus(call.from_user.id):.1f}x)'
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
    arr = []
    for uid, u in USERS.items():
        arr.append((u.get('name', 'Player'), u.get('gram', 0)))
    arr.sort(key=lambda x: x[1], reverse=True)

    text = '🏆 ТОП ПО GRAM\n━━━━━━━━━━━━━━━\n\n'
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    for i, (name, gram) in enumerate(arr[:20], 1):
        prefix = medals.get(i, f'{i}.')
        text += f'{prefix} {name} — {gram} GRAM\n'

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
    text = '📊 КУРСЫ ВАЛЮТ\n━━━━━━━━━━━━━━━\n\n'
    with RATES_LOCK:
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            start = info['start']
            change = ((rate - start) / start) * 100
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

    text = (
        f'🛒 МАГАЗИН БИТКОИНОВ\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n\n'
        f'🖤 DRK (+{drk}%) — 50 GRAM\n'
        f'🌑 DARKGRAM (+{dg}%) — 75 GRAM\n'
        f'⚡ BSG•BST (+{bsg}%) — 100 GRAM\n'
        f'📢 WWR (+50%) — 100 GRAM\n\n'
        f'Куплено: DRK {"✅" if u.get("shop",{}).get("DRK") else "❌"} | DARKGRAM {"✅" if u.get("shop",{}).get("DARKGRAM") else "❌"} | BSG {"✅" if u.get("shop",{}).get("BSG") else "❌"} | WWR {"✅" if u.get("wwr") else "❌"}'
    )
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
        if u.get('wwr'):
            bot.answer_callback_query(call.id, 'Уже куплено')
            return
        if u.get('gram', 0) < 100:
            bot.answer_callback_query(call.id, 'Недостаточно GRAM')
            return
        with USERS_LOCK:
            u['gram'] -= 100
            u['wwr'] = True
            save_users()
        bot.answer_callback_query(call.id, '✅ WWR куплено')
    else:
        if item not in prices:
            return
        if u.get('shop', {}).get(item):
            bot.answer_callback_query(call.id, 'Уже куплено')
            return
        if u.get('gram', 0) < prices[item]:
            bot.answer_callback_query(call.id, 'Недостаточно GRAM')
            return
        with USERS_LOCK:
            u['gram'] -= prices[item]
            if 'shop' not in u: u['shop'] = {}
            u['shop'][item] = True
            save_users()
        bot.answer_callback_query(call.id, f'✅ {item} куплено')

    cb_menu_shop(call)


# ==================== КАК ИГРАТЬ ====================
@bot.callback_query_handler(func=lambda c: c.data == 'menu_how')
def cb_menu_how(call):
    text = (
        'ℹ️ КАК ИГРАТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '📖 ОСНОВЫ:\n\n'
        '1️⃣ Верификация → +100 GRAM\n\n'
        '2️⃣ 📈 Трейдинг → валюта → ставка\n'
        f'   • Мин: {MIN_BET} | Макс: {MAX_BET} GRAM\n\n'
        '3️⃣ Курс меняется каждые 3 сек\n\n'
        '4️⃣ Жми ЗАКРЫТЬ — забрать профит\n\n'
        '5️⃣ Курс упал до 0.5x — авто-закрытие\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🎨 NFT:\n'
        '• 🍸 — 5 шт по 50 GRAM\n'
        '• ⛲ — 7 шт по 450 GRAM\n'
        '• 💺 — 11 шт по 650 GRAM\n'
        '• +0.1 к прибыли за каждый\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🏪 РЫНОК:\n'
        '• Продавай NFT за любую цену\n'
        '• Покупай по ID\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🛒 МАГАЗИН:\n'
        '• Биткоины DRK/DARKGRAM/BSG с процентами\n'
        '• WWR — особая валюта\n\n'
        '🏆 Цель: набрать больше всех GRAM!'
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
    print('Trade+NFT bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
