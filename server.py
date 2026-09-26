import json
import os
import time
import threading
import random
from datetime import date
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

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

SHOP_ITEMS = {
    'DRK':      {'name': '🖤 DRK',      'price': 50,  'percent': 20},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'price': 75,  'percent': 5},
    'BSG':      {'name': '⚡ BSG•BST',  'price': 100, 'percent': 10},
    'WWR':      {'name': '📢 WWR',      'price': 100, 'percent': 50},
}

CURRENCIES = {
    'GRAM':     {'name': '💎 GRAM',     'start': 1.00,  'volatility': 0.05},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'start': 2.50,  'volatility': 0.07},
    'DRK':      {'name': '🖤 DRK',      'start': 5.00,  'volatility': 0.10},
    'BSG':      {'name': '⚡ BSG•BST',  'start': 10.00, 'volatility': 0.12},
    'WWR':      {'name': '📢 WWR',      'start': 25.00, 'volatility': 0.15},
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

RATES = {k: v['start'] for k, v in CURRENCIES.items()}
RATES_LOCK = threading.Lock()

ONLINE = {}
ONLINE_LOCK = threading.Lock()
ONLINE_TIMEOUT = 60

ACTIVE_TRADES = {}
TRADES_LOCK = threading.Lock()
TRADE_TICK = 3
MAX_TRADE_TIME = 120
AUTO_CLOSE_MULT = 0.5


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


def today_str(): return date.today().isoformat()


def get_user(uid):
    users = load_json(USERS_FILE, {})
    key = str(uid)
    if key not in users:
        users[key] = {
            'name': '', 'gram': 0, 'verified': False,
            'wins': 0, 'losses': 0, 'total_profit': 0,
            'nfts': [], 'skins': [],
            'shop': {}, 'wwr': False,
            'day': 1, 'tasks_done': {}, 'tasks_date': '',
            'stats': {'trades': 0, 'wins_trade': 0, 'bought_nft': 0, 'sold_nft': 0, 'earned': 0, 'bought_skins': 0, 'bought_bit': 0},
        }
        save_json(USERS_FILE, users)
    u = users[key]
    defaults = {
        'nfts': [], 'skins': [], 'shop': {}, 'wwr': False,
        'day': 1, 'tasks_done': {}, 'tasks_date': '',
        'stats': {'trades': 0, 'wins_trade': 0, 'bought_nft': 0, 'sold_nft': 0, 'earned': 0, 'bought_skins': 0, 'bought_bit': 0},
    }
    for f, v in defaults.items():
        if f not in u: u[f] = v
    return u


def save_user(uid, data):
    users = load_json(USERS_FILE, {})
    users[str(uid)] = data
    save_json(USERS_FILE, users)


def check_tasks_reset(u):
    if u.get('tasks_date', '') != today_str():
        u['tasks_date'] = today_str()
        u['tasks_done'] = {}
    return u


def check_task(uid, tid):
    u = get_user(uid)
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


def get_nft_bonus(uid):
    u = get_user(uid)
    return len(u.get('nfts', [])) * 0.1


# ==================== ФОН — КУРСЫ ====================
def rate_loop():
    while True:
        try:
            with RATES_LOCK:
                for cur, info in CURRENCIES.items():
                    rate = RATES[cur]
                    change = random.uniform(-info['volatility'], info['volatility'])
                    RATES[cur] = max(0.01, round(rate * (1 + change), 4))
        except Exception as e:
            print('rate err:', e)
        time.sleep(TRADE_TICK)


threading.Thread(target=rate_loop, daemon=True).start()


# ==================== ФОН — ТРЕЙДЫ ====================
def trade_close_check():
    """Каждые 3 сек проверяем сделки: авто-закрытие по падению или по времени."""
    while True:
        try:
            now = time.time()
            to_close = []
            with TRADES_LOCK:
                for uid, t in list(ACTIVE_TRADES.items()):
                    with RATES_LOCK:
                        rate = RATES.get(t['currency'], t['open_rate'])
                    mult = rate / t['open_rate']
                    if mult <= AUTO_CLOSE_MULT:
                        to_close.append((uid, 'auto_drop'))
                    elif now - t['open_time'] > MAX_TRADE_TIME:
                        to_close.append((uid, 'auto_time'))
            for uid, reason in to_close:
                close_trade_internal(uid)
        except Exception as e:
            print('trade check err:', e)
        time.sleep(TRADE_TICK)


def close_trade_internal(uid):
    with TRADES_LOCK:
        t = ACTIVE_TRADES.get(uid)
        if not t: return
        del ACTIVE_TRADES[uid]

    with RATES_LOCK:
        rate = RATES.get(t['currency'], t['open_rate'])
    mult = rate / t['open_rate']
    profit = t['bet'] * (mult - 1)
    nft_bonus = get_nft_bonus(uid)
    if profit > 0:
        profit = profit * (1 + nft_bonus)
    profit = round(profit, 2)

    u = get_user(uid)
    u['gram'] = round(u.get('gram', 0) + t['bet'] + profit, 2)
    u['stats']['trades'] = u['stats'].get('trades', 0) + 1
    if profit > 0:
        u['wins'] = u.get('wins', 0) + 1
        u['total_profit'] = round(u.get('total_profit', 0) + profit, 2)
        u['stats']['wins_trade'] = u['stats'].get('wins_trade', 0) + 1
        u['stats']['earned'] = round(u['stats'].get('earned', 0) + profit, 2)
    elif profit < 0:
        u['losses'] = u.get('losses', 0) + 1
    save_user(uid, u)


threading.Thread(target=trade_close_check, daemon=True).start()


# ==================== РОУТЫ ====================
@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


@app.route('/api/player', methods=['POST', 'GET'])
def api_player():
    if request.method == 'POST':
        d = request.json or {}
        uid = d.get('uid')
        if d.get('name'):
            u = get_user(uid)
            u['name'] = d['name']
            save_user(uid, u)
    else:
        uid = request.args.get('uid')
        if not uid:
            d = request.json or {}
            uid = d.get('uid')
    if not uid:
        return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    return jsonify({
        'name': u.get('name', 'Player'),
        'gram': u.get('gram', 0),
        'wins': u.get('wins', 0),
        'losses': u.get('losses', 0),
        'total_profit': u.get('total_profit', 0),
        'nfts': u.get('nfts', []),
        'skins': u.get('skins', []),
        'verified': u.get('verified', False),
        'day': u.get('day', 1),
    })


@app.route('/api/verify', methods=['POST'])
def api_verify():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    if u.get('verified'):
        return jsonify({'error': 'Уже пройдена'}), 400
    u['verified'] = True
    u['gram'] = u.get('gram', 0) + 100
    save_user(uid, u)
    return jsonify({'ok': True})


@app.route('/api/rates')
def api_rates():
    with RATES_LOCK:
        result = {}
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            change = ((rate - info['start']) / info['start']) * 100
            result[cur] = {
                'name': info['name'],
                'rate': round(rate, 4),
                'change': round(change, 2),
            }
    return jsonify(result)


# ==================== ТРЕЙД ====================
@app.route('/api/trade/open', methods=['POST'])
def api_trade_open():
    d = request.json or {}
    uid = d.get('uid')
    cur = d.get('currency')
    bet = d.get('bet')
    if not uid or not cur or cur not in CURRENCIES:
        return jsonify({'error': 'bad'}), 400
    try:
        bet = float(bet)
    except:
        return jsonify({'error': 'bad bet'}), 400
    if bet < 10 or bet > 500:
        return jsonify({'error': 'Ставка 10–500'}), 400
    u = get_user(uid)
    if u.get('gram', 0) < bet:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    with TRADES_LOCK:
        if uid in ACTIVE_TRADES:
            return jsonify({'error': 'Уже есть сделка'}), 400
    with RATES_LOCK:
        rate = RATES[cur]
    u['gram'] = round(u['gram'] - bet, 2)
    save_user(uid, u)
    t = {
        'uid': uid, 'currency': cur, 'bet': bet,
        'open_rate': rate, 'open_time': time.time(),
    }
    with TRADES_LOCK:
        ACTIVE_TRADES[uid] = t
    return jsonify({'ok': True, 'trade': enrich_trade(t)})


def enrich_trade(t):
    with RATES_LOCK:
        rate = RATES.get(t['currency'], t['open_rate'])
    mult = rate / t['open_rate']
    profit = t['bet'] * (mult - 1)
    nft_bonus = get_nft_bonus(t['uid'])
    if profit > 0:
        profit = profit * (1 + nft_bonus)
    return {
        'currency': t['currency'],
        'bet': t['bet'],
        'open_rate': t['open_rate'],
        'current_rate': round(rate, 4),
        'mult': round(mult, 4),
        'profit': round(profit, 2),
    }


@app.route('/api/trade/status', methods=['POST', 'GET'])
def api_trade_status():
    if request.method == 'POST':
        d = request.json or {}
        uid = d.get('uid')
    else:
        uid = request.args.get('uid')
    if not uid: return jsonify({'trade': None})
    with TRADES_LOCK:
        t = ACTIVE_TRADES.get(uid)
    if not t:
        return jsonify({'trade': None, 'closed': True})
    return jsonify({'trade': enrich_trade(t), 'closed': False})


@app.route('/api/trade/close', methods=['POST'])
def api_trade_close():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    with TRADES_LOCK:
        t = ACTIVE_TRADES.get(uid)
    if not t:
        return jsonify({'error': 'Нет сделки'}), 400
    with RATES_LOCK:
        rate = RATES.get(t['currency'], t['open_rate'])
    mult = rate / t['open_rate']
    profit = t['bet'] * (mult - 1)
    nft_bonus = get_nft_bonus(uid)
    if profit > 0:
        profit = profit * (1 + nft_bonus)
    profit = round(profit, 2)
    with TRADES_LOCK:
        del ACTIVE_TRADES[uid]
    u = get_user(uid)
    u['gram'] = round(u.get('gram', 0) + t['bet'] + profit, 2)
    u['stats']['trades'] = u['stats'].get('trades', 0) + 1
    if profit > 0:
        u['wins'] = u.get('wins', 0) + 1
        u['total_profit'] = round(u.get('total_profit', 0) + profit, 2)
        u['stats']['wins_trade'] = u['stats'].get('wins_trade', 0) + 1
        u['stats']['earned'] = round(u['stats'].get('earned', 0) + profit, 2)
    elif profit < 0:
        u['losses'] = u.get('losses', 0) + 1
    save_user(uid, u)
    return jsonify({'ok': True, 'profit': profit})


# ==================== NFT ====================
@app.route('/api/nft')
def api_nft():
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    return jsonify({
        'types': NFT_TYPES,
        'skins': SKIN_TYPES,
        'minted': nft_data.get('minted', {}),
    })


@app.route('/api/nft/buy', methods=['POST'])
def api_nft_buy():
    d = request.json or {}
    uid = d.get('uid')
    key = d.get('key')
    if not uid or not key or key not in NFT_TYPES:
        return jsonify({'error': 'bad'}), 400
    info = NFT_TYPES[key]
    u = get_user(uid)
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    minted = nft_data.get('minted', {})
    items = nft_data.get('items', {})
    sold = minted.get(key, 0)
    if sold >= info['max']:
        return jsonify({'error': 'Распродано'}), 400
    if u.get('gram', 0) < info['price']:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    max_num = 0
    for nid in items:
        try:
            n = int(nid.split('-')[1])
            if n > max_num: max_num = n
        except: pass
    new_id = f'N-{max_num + 1:04d}'
    u['gram'] = round(u.get('gram', 0) - info['price'], 2)
    u['nfts'] = u.get('nfts', []) + [new_id]
    u['stats']['bought_nft'] = u['stats'].get('bought_nft', 0) + 1
    save_user(uid, u)
    minted[key] = sold + 1
    items[new_id] = {'type': key, 'owner': uid, 'skin': None, 'bought_at': int(time.time())}
    nft_data['minted'] = minted
    nft_data['items'] = items
    save_json(NFT_FILE, nft_data)
    return jsonify({'ok': True, 'nft_id': new_id})


@app.route('/api/nft/sell', methods=['POST'])
def api_nft_sell():
    d = request.json or {}
    uid = d.get('uid')
    nid = d.get('nft_id')
    price = d.get('price')
    if not uid or not nid or not price:
        return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    if nid not in u.get('nfts', []):
        return jsonify({'error': 'Нет такого NFT'}), 400
    market = load_json(MARKET_FILE, {})
    market[nid] = {'seller': uid, 'price': round(float(price), 2), 'listed_at': int(time.time())}
    save_json(MARKET_FILE, market)
    return jsonify({'ok': True})


# ==================== СКИНЫ ====================
@app.route('/api/skin/buy', methods=['POST'])
def api_skin_buy():
    d = request.json or {}
    uid = d.get('uid')
    key = d.get('key')
    nft_id = d.get('nft_id')
    if not uid or not key or key not in SKIN_TYPES:
        return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    if not u.get('nfts'):
        return jsonify({'error': 'Сначала купи NFT'}), 400
    if nft_id not in u.get('nfts', []):
        return jsonify({'error': 'Нет такого NFT'}), 400
    info = SKIN_TYPES[key]
    if u.get('gram', 0) < info['price']:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    u['gram'] = round(u['gram'] - info['price'], 2)
    u['skins'] = u.get('skins', []) + [key]
    u['stats']['bought_skins'] = u['stats'].get('bought_skins', 0) + 1
    save_user(uid, u)
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    if nft_id in nft_data.get('items', {}):
        nft_data['items'][nft_id]['skin'] = key
        save_json(NFT_FILE, nft_data)
    return jsonify({'ok': True})


# ==================== МАГАЗИН ====================
@app.route('/api/shop')
def api_shop():
    uid = request.args.get('uid')
    u = get_user(uid) if uid else {}
    return jsonify({
        'items': SHOP_ITEMS,
        'owned': u.get('shop', {}) if u else {},
    })


@app.route('/api/shop/buy', methods=['POST'])
def api_shop_buy():
    d = request.json or {}
    uid = d.get('uid')
    item = d.get('item')
    if not uid or item not in SHOP_ITEMS:
        return jsonify({'error': 'bad'}), 400
    info = SHOP_ITEMS[item]
    u = get_user(uid)
    if u.get('shop', {}).get(item):
        return jsonify({'error': 'Уже куплено'}), 400
    if u.get('gram', 0) < info['price']:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    u['gram'] = round(u['gram'] - info['price'], 2)
    if 'shop' not in u: u['shop'] = {}
    u['shop'][item] = True
    if item == 'WWR': u['wwr'] = True
    u['stats']['bought_bit'] = u['stats'].get('bought_bit', 0) + 1
    save_user(uid, u)
    return jsonify({'ok': True})


# ==================== ЗАДАНИЯ ====================
@app.route('/api/tasks')
def api_tasks():
    uid = request.args.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    check_tasks_reset(u)
    save_user(uid, u)
    day = u.get('day', 1)
    if day > 10: day = 10
    tasks = TASKS_BY_DAY.get(day, [])
    result = []
    for t in tasks:
        done = t['id'] in u.get('tasks_done', {})
        ready = (not done) and check_task(uid, t['id'])
        result.append({'id': t['id'], 'text': t['text'], 'done': done, 'ready': ready})
    return jsonify({'day': day, 'tasks': result})


@app.route('/api/tasks/claim', methods=['POST'])
def api_tasks_claim():
    d = request.json or {}
    uid = d.get('uid')
    tid = d.get('task_id')
    if not uid or not tid: return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    check_tasks_reset(u)
    if tid in u.get('tasks_done', {}):
        return jsonify({'error': 'Уже получено'}), 400
    if not check_task(uid, tid):
        return jsonify({'error': 'Не выполнено'}), 400
    u['tasks_done'][tid] = True
    u['gram'] = round(u.get('gram', 0) + TASK_REWARD, 2)
    save_user(uid, u)
    return jsonify({'ok': True, 'reward': TASK_REWARD})


# ==================== РЫНОК ====================
@app.route('/api/market')
def api_market():
    market = load_json(MARKET_FILE, {})
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    result = []
    for nid, data in market.items():
        item = nft_data.get('items', {}).get(nid)
        if not item: continue
        info = NFT_TYPES.get(item['type'], {})
        seller = get_user(data['seller'])
        result.append({
            'nft_id': nid,
            'emoji': info.get('emoji', ''),
            'name': info.get('name', ''),
            'price': data['price'],
            'seller_name': seller.get('name', '?'),
        })
    return jsonify(result)


@app.route('/api/market/buy', methods=['POST'])
def api_market_buy():
    d = request.json or {}
    uid = d.get('uid')
    nid = d.get('nft_id')
    if not uid or not nid: return jsonify({'error': 'bad'}), 400
    market = load_json(MARKET_FILE, {})
    if nid not in market:
        return jsonify({'error': 'Не найдено'}), 400
    data = market[nid]
    seller = data['seller']
    price = data['price']
    if str(uid) == str(seller):
        return jsonify({'error': 'Это твой NFT'}), 400
    bu = get_user(uid)
    if bu.get('gram', 0) < price:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    su = get_user(seller)
    bu['gram'] = round(bu['gram'] - price, 2)
    su['gram'] = round(su.get('gram', 0) + price, 2)
    if nid in su.get('nfts', []): su['nfts'].remove(nid)
    bu['nfts'] = bu.get('nfts', []) + [nid]
    su['stats']['sold_nft'] = su['stats'].get('sold_nft', 0) + 1
    save_user(uid, bu)
    save_user(seller, su)
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    if nid in nft_data.get('items', {}):
        nft_data['items'][nid]['owner'] = uid
        save_json(NFT_FILE, nft_data)
    del market[nid]
    save_json(MARKET_FILE, market)
    return jsonify({'ok': True})


# ==================== ТОП ====================
@app.route('/api/top')
def api_top():
    users = load_json(USERS_FILE, {})
    arr = []
    for uid, u in users.items():
        arr.append({'name': u.get('name', 'Player'), 'gram': u.get('gram', 0)})
    arr.sort(key=lambda x: x['gram'], reverse=True)
    return jsonify(arr[:20])


# ==================== ПЕРЕВОД ====================
@app.route('/api/pay', methods=['POST'])
def api_pay():
    d = request.json or {}
    uid = d.get('uid')
    target = str(d.get('target', '')).strip()
    amount = d.get('amount')
    try:
        amount = float(amount)
    except:
        return jsonify({'error': 'Неверная сумма'}), 400
    if amount <= 0:
        return jsonify({'error': 'Сумма > 0'}), 400
    if not uid or not target:
        return jsonify({'error': 'Заполни поля'}), 400
    users = load_json(USERS_FILE, {})
    if target not in users:
        return jsonify({'error': 'Получатель не найден'}), 400
    if target == str(uid):
        return jsonify({'error': 'Нельзя себе'}), 400
    u = users[str(uid)]
    if u.get('gram', 0) < amount:
        return jsonify({'error': 'Недостаточно GRAM'}), 400
    r = users[target]
    u['gram'] = round(u['gram'] - amount, 2)
    r['gram'] = round(r.get('gram', 0) + amount, 2)
    save_json(USERS_FILE, users)
    return jsonify({'ok': True})


# ==================== ОНЛАЙН ====================
@app.route('/api/ping', methods=['POST'])
def api_ping():
    d = request.json or {}
    uid = d.get('uid')
    if uid:
        with ONLINE_LOCK:
            ONLINE[str(uid)] = time.time()
    return jsonify({'ok': True})


@app.route('/api/online')
def api_online():
    now = time.time()
    with ONLINE_LOCK:
        active = [u for u, t in ONLINE.items() if now - t < ONLINE_TIMEOUT]
        return jsonify({'count': len(active)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
