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
TOKEN = '8514412667:AAE9QkHtAG2Z8HIZn2DDBZ740crDzqw4ljk'

START_GRAM = 0
VERIFY_BONUS = 100
MIN_BET = 10
MAX_BET = 500

TRADE_TICK = 3          # обновление курса раз в 3 сек
MAX_TRADE_TIME = 120    # макс. время позиции
AUTO_CLOSE_MULT = 0.5   # авто-закрытие при падении до 0.5x

SHOP_FILE = 'shop_prices.json'
USERS_FILE = 'users.json'
TRADES_FILE = 'trades.json'

# ==================== БОТ ====================
bot = telebot.TeleBot(TOKEN)

try:
    bot.delete_webhook(drop_pending_updates=True)
    print('Webhook deleted')
except Exception as e:
    print('webhook err:', e)

USERS = {}
USERS_LOCK = threading.Lock()

SHOP = {}
SHOP_LOCK = threading.Lock()

ACTIVE_TRADES = {}      # uid -> Trade
TRADES_LOCK = threading.Lock()


# ==================== ВАЛЮТЫ ====================
CURRENCIES = {
    'GRAM': {'name': '💎 GRAM', 'start': 1.00, 'volatility': 0.05},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'start': 2.50, 'volatility': 0.07},
    'DRK': {'name': '🖤 DRK', 'start': 5.00, 'volatility': 0.10},
    'BSG': {'name': '⚡ BSG•BST', 'start': 10.00, 'volatility': 0.12},
    'WWR': {'name': '📢 WWR', 'start': 25.00, 'volatility': 0.15},
}

# Курсы валют (общие, меняются)
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
    raw = load_json(USERS_FILE, {})
    USERS = raw


def save_users():
    save_json(USERS_FILE, USERS)


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
            'shop': {},          # {'DRK': True, 'DARKGRAM': True, ...}
            'wwr': False,
        }
        save_users()
    return USERS[key]


def save_user():
    save_users()


def load_shop():
    global SHOP
    raw = load_json(SHOP_FILE, {})
    # проценты магазина (курс биткоинов)
    for cur in ['DRK', 'DARKGRAM', 'BSG']:
        if cur not in raw:
            raw[cur] = {'percent': 0, 'updated': 0}
    SHOP = raw


def save_shop():
    save_json(SHOP_FILE, SHOP)


load_users()
load_shop()


# ==================== ЛОГИКА КУРСА ====================
def update_rates():
    """Обновляет курсы валют каждые TRADE_TICK секунд."""
    with RATES_LOCK:
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            vol = info['volatility']
            change = random.uniform(-vol, vol)
            new_rate = rate * (1 + change)
            new_rate = max(0.01, round(new_rate, 4))
            RATES[cur] = new_rate


def get_chance_up(cur):
    """Шанс, что курс пойдёт вверх."""
    base = 50
    # если курс низко относительно старта — шанс вверх выше
    with RATES_LOCK:
        rate = RATES[cur]
        start = CURRENCIES[cur]['start']
    diff = (rate - start) / start
    chance = base - diff * 100
    chance = max(15, min(85, chance))
    return round(chance)


def get_shop_bonus(uid, cur):
    """Бонус от купленных биткоинов."""
    u = get_user(uid)
    shop = u.get('shop', {})
    bonus = 0
    for s in shop:
        if shop[s]:
            bonus += SHOP.get(s, {}).get('percent', 0)
    if u.get('wwr') and cur == 'WWR':
        bonus += 50
    return bonus


# ==================== ФОН — ОБНОВЛЕНИЕ КУРСОВ ====================
def rate_loop():
    while True:
        try:
            update_rates()
        except Exception as e:
            print('rate loop err:', e)
        time.sleep(TRADE_TICK)


threading.Thread(target=rate_loop, daemon=True).start()


# ==================== ФОН — ОБНОВЛЕНИЕ МАГАЗИНА ====================
def shop_loop():
    while True:
        try:
            with SHOP_LOCK:
                now = int(time.time())
                for cur in ['DRK', 'DARKGRAM', 'BSG']:
                    if now - SHOP[cur].get('updated', 0) > 1800:  # 30 мин
                        # меняем процент
                        if cur == 'DRK':
                            SHOP[cur]['percent'] = random.choice([15, 20, 25, 30])
                        elif cur == 'DARKGRAM':
                            SHOP[cur]['percent'] = random.choice([3, 5, 7, 10])
                        elif cur == 'BSG':
                            SHOP[cur]['percent'] = random.choice([5, 10, 15])
                        SHOP[cur]['updated'] = now
                save_shop()
        except Exception as e:
            print('shop loop err:', e)
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
    """Считает текущую прибыль."""
    with RATES_LOCK:
        rate = RATES[trade.cur]
    mult = rate / trade.open_rate
    profit = trade.bet * (mult - 1)
    return round(profit, 2), mult


def trade_loop_for(trade):
    """Обновляет сообщение с курсом и шансом."""
    while not trade.closed:
        try:
            profit, mult = trade_profit(trade)

            # авто-закрытие при падении
            if mult <= AUTO_CLOSE_MULT:
                close_trade(trade, auto=True)
                return

            # превышено время
            if time.time() - trade.open_time > MAX_TRADE_TIME:
                close_trade(trade, auto=True)
                return

            update_trade_message(trade, profit, mult)
        except Exception as e:
            print('trade loop err:', e)
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
            f'{arrow} Шанс вверх: {chance}% | Вниз: {100 - chance}%\n\n'
            f'⏱ Осталось: {max(0, int(MAX_TRADE_TIME - (time.time() - trade.open_time)))} сек\n'
            f'⚠️ Авто-закрытие при {AUTO_CLOSE_MULT}x'
        )

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton('ЗАКРЫТЬ СДЕЛКУ', callback_data=f'close_{trade.uid}'))
        kb.add(types.InlineKeyboardButton('Обновить', callback_data=f'refresh_{trade.uid}'))

        bot.edit_message_text(text, chat_id=trade.chat_id, message_id=trade.msg_id,
                              reply_markup=kb)
    except Exception as e:
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
    uid = int(call.data.replace('refresh_', ''))
    if call.from_user.id != uid:
        bot.answer_callback_query(call.id, 'Не твоя сделка')
        return
    bot.answer_callback_query(call.id, 'Обновлено')


# ==================== МЕНЮ ====================
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('📈 Трейдинг', callback_data='menu_trade'),
        types.InlineKeyboardButton('🛒 Магазин', callback_data='menu_shop')
    )
    kb.add(
        types.InlineKeyboardButton('👛 Кошелёк', callback_data='menu_wallet'),
        types.InlineKeyboardButton('🏆 Топ GRAM', callback_data='menu_top')
    )
    kb.add(types.InlineKeyboardButton('📊 Курсы валют', callback_data='menu_rates'))
    kb.add(types.InlineKeyboardButton('ℹ️ Как играть', callback_data='menu_how'))
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
        f'💼 Твой баланс: {u["gram"]} GRAM\n'
        f'✅ Верификация: {"пройдена" if u["verified"] else "не пройдена"}\n\n'
        f'📈 Торгуй валютами, зарабатывай GRAM!\n'
        f'🛒 Покупай биткоины для бонусов.\n'
        f'🏆 Поднимайся в топ.\n\n'
        f'👇 Выбери действие:'
    )

    kb = main_menu()
    if not u['verified']:
        kb.add(types.InlineKeyboardButton('🎯 Пройти верификацию', callback_data='verify'))

    bot.send_message(m.chat.id, text, reply_markup=kb)


@bot.message_handler(commands=['help'])
def cmd_help(m):
    cmd_start(m)


@bot.message_handler(commands=['wallet'])
def cmd_wallet(m):
    u = get_user(m.from_user.id)
    text = (
        f'👛 КОШЕЛЁК\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💎 GRAM: {u.get("gram", 0)}\n'
        f'🏆 Побед: {u.get("wins", 0)}\n'
        f'💔 Поражений: {u.get("losses", 0)}\n'
        f'📈 Всего профита: {u.get("total_profit", 0)}\n\n'
        f'🛒 Биткоины:\n'
        f'• DRK: {"✅" if u.get("shop", {}).get("DRK") else "❌"}\n'
        f'• DARKGRAM: {"✅" if u.get("shop", {}).get("DARKGRAM") else "❌"}\n'
        f'• BSG•BST: {"✅" if u.get("shop", {}).get("BSG") else "❌"}\n'
        f'• 📢 WWR: {"✅" if u.get("wwr") else "❌"}'
    )
    bot.send_message(m.chat.id, text, reply_markup=main_menu())


# ==================== КОЛБЭКИ ====================
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
        kb.add(types.InlineKeyboardButton(
            f'{CURRENCIES[cur]["name"]} ({rate:.2f})',
            callback_data=f'trade_cur_{cur}'
        ))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))

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
        f'📊 Текущий курс: {rate:.4f}\n'
        f'{arrow} Шанс вверх: {chance}% | Вниз: {100 - chance}%\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n'
        f'📊 Ставка: от {MIN_BET} до {MAX_BET}\n\n'
        f'✍️ Напиши сумму ставки числом.\n\n'
        f'Например: 100'
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
        bot.reply_to(m, f'❌ Минимальная ставка: {MIN_BET} GRAM')
        return
    if bet > MAX_BET:
        bot.reply_to(m, f'❌ Максимальная ставка: {MAX_BET} GRAM')
        return
    if bet > u.get('gram', 0):
        bot.reply_to(m, f'❌ У тебя только {u["gram"]} GRAM')
        return

    # списываем ставку
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
        f'{arrow} Шанс вверх: {chance}% | Вниз: {100 - chance}%\n\n'
        f'⏱ Макс. время: {MAX_TRADE_TIME} сек\n'
        f'⚠️ Авто-закрытие при {AUTO_CLOSE_MULT}x\n\n'
        f'Жми ЗАКРЫТЬ, когда захочешь забрать.'
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('ЗАКРЫТЬ СДЕЛКУ', callback_data=f'close_{uid}'))
    kb.add(types.InlineKeyboardButton('Обновить', callback_data=f'refresh_{uid}'))

    msg = bot.send_message(m.chat.id, text, reply_markup=kb)
    trade.msg_id = msg.message_id
    trade.chat_id = m.chat.id

    threading.Thread(target=trade_loop_for, args=(trade,), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == 'menu_shop')
def cb_menu_shop(call):
    uid = call.from_user.id
    u = get_user(uid)

    with SHOP_LOCK:
        drk = SHOP.get('DRK', {}).get('percent', 20)
        dg = SHOP.get('DARKGRAM', {}).get('percent', 5)
        bsg = SHOP.get('BSG', {}).get('percent', 10)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(f'🖤 DRK (+{drk}% к прибыли) — 50 GRAM', callback_data='buy_DRK'))
    kb.add(types.InlineKeyboardButton(f'🌑 DARKGRAM (+{dg}% к прибыли) — 75 GRAM', callback_data='buy_DARKGRAM'))
    kb.add(types.InlineKeyboardButton(f'⚡ BSG•BST (+{bsg}% к прибыли) — 100 GRAM', callback_data='buy_BSG'))
    kb.add(types.InlineKeyboardButton(f'📢 WWR (+50% к прибыли WWR) — 100 GRAM', callback_data='buy_WWR'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))

    text = (
        f'🛒 МАГАЗИН БИТКОИНОВ\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💼 Баланс: {u["gram"]} GRAM\n\n'
        f'🖤 DRK (+{drk}%) — 50 GRAM\n'
        f'🌑 DARKGRAM (+{dg}%) — 75 GRAM\n'
        f'⚡ BSG•BST (+{bsg}%) — 100 GRAM\n'
        f'📢 WWR (+50%) — 100 GRAM\n\n'
        f'💡 Бонусы складываются. Проценты меняются каждые 30 мин.\n\n'
        f'Куплено:\n'
        f'• DRK: {"✅" if u.get("shop", {}).get("DRK") else "❌"}\n'
        f'• DARKGRAM: {"✅" if u.get("shop", {}).get("DARKGRAM") else "❌"}\n'
        f'• BSG•BST: {"✅" if u.get("shop", {}).get("BSG") else "❌"}\n'
        f'• WWR: {"✅" if u.get("wwr") else "❌"}'
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
            if 'shop' not in u:
                u['shop'] = {}
            u['shop'][item] = True
            save_users()
        bot.answer_callback_query(call.id, f'✅ {item} куплено')

    cb_menu_shop(call)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_wallet')
def cb_menu_wallet(call):
    u = get_user(call.from_user.id)
    text = (
        f'👛 КОШЕЛЁК\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'💎 GRAM: {u.get("gram", 0)}\n'
        f'🏆 Побед: {u.get("wins", 0)}\n'
        f'💔 Поражений: {u.get("losses", 0)}\n'
        f'📈 Всего профита: {u.get("total_profit", 0)}'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


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
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


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
    kb.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='menu_rates'))
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_how')
def cb_menu_how(call):
    text = (
        'ℹ️ КАК ИГРАТЬ\n'
        '━━━━━━━━━━━━━━━\n\n'
        '📖 ОСНОВЫ:\n\n'
        '1️⃣ Пройди верификацию → получишь 100 GRAM\n\n'
        '2️⃣ Заходи в Трейдинг → выбирай валюту → ставь сумму\n'
        f'   • Мин: {MIN_BET} | Макс: {MAX_BET} GRAM\n\n'
        '3️⃣ Курс меняется каждые 3 сек — вверх или вниз\n\n'
        '4️⃣ Жми ЗАКРЫТЬ, когда профит устроит\n\n'
        '5️⃣ Если курс упадёт до 0.5x — сделка закроется сама\n\n'
        '━━━━━━━━━━━━━━━\n'
        '📊 ШАНС ВВЕРХ/ВНИЗ:\n'
        'Показывается перед и во время сделки.\n'
        'Чем ниже курс относительно старта — тем выше шанс вверх.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🛒 МАГАЗИН:\n'
        'Покупай биткоины → они дают бонус к прибыли.\n'
        'Проценты меняются каждые 30 мин.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '📢 WWR:\n'
        'Особая валюта. Купить за 100 GRAM.\n'
        'Даёт +50% к прибыли на WWR-сделках.\n\n'
        '━━━━━━━━━━━━━━━\n'
        '🏆 ЦЕЛЬ:\n'
        'Набрать больше всех GRAM и попасть в топ!'
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('◀️ Назад', callback_data='menu_back'))
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'menu_back')
def cb_menu_back(call):
    uid = call.from_user.id
    u = get_user(uid)
    text = (
        f'💎 DARKGRAM TRADE\n'
        f'━━━━━━━━━━━━━━━\n\n'
        f'👋 Привет!\n\n'
        f'💼 Твой баланс: {u["gram"]} GRAM\n'
        f'✅ Верификация: {"пройдена" if u["verified"] else "не пройдена"}\n\n'
        f'👇 Выбери действие:'
    )
    kb = main_menu()
    if not u['verified']:
        kb.add(types.InlineKeyboardButton('🎯 Пройти верификацию', callback_data='verify'))
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
        f'🎉 Верификация пройдена!\n\n💎 Тебе начислено {VERIFY_BONUS} GRAM\n\nТеперь можешь торговать!')
    cb_menu_back(call)


# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print('Trade bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
