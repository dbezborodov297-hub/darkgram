import json
import os
import time
import threading
from datetime import date
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

USERS_FILE = 'users.json'
NFT_FILE = 'nft.json'
MARKET_FILE = 'market.json'

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

CURRENCIES = {
    'GRAM':     {'name': '💎 GRAM',     'start': 1.00,  'volatility': 0.05},
    'DARKGRAM': {'name': '🌑 DARKGRAM', 'start': 2.50,  'volatility': 0.07},
    'DRK':      {'name': '🖤 DRK',      'start': 5.00,  'volatility': 0.10},
    'BSG':      {'name': '⚡ BSG•BST',  'start': 10.00, 'volatility': 0.12},
    'WWR':      {'name': '📢 WWR',      'start': 25.00, 'volatility': 0.15},
}

RATES = {k: v['start'] for k, v in CURRENCIES.items()}
RATES_LOCK = threading.Lock()

ONLINE = {}       # uid -> timestamp
ONLINE_LOCK = threading.Lock()
ONLINE_TIMEOUT = 60

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


def get_user(uid):
    users = load_json(USERS_FILE, {})
    key = str(uid)
    if key not in users:
        users[key] = {
            'name': '', 'gram': 0, 'verified': False,
            'wins': 0, 'losses': 0, 'total_profit': 0,
            'nfts': [], 'skins': [],
        }
        save_json(USERS_FILE, users)
    return users[key]


def save_user(uid, data):
    users = load_json(USERS_FILE, {})
    users[str(uid)] = data
    save_json(USERS_FILE, users)


# ==================== ФОН — ОБНОВЛЕНИЕ КУРСОВ ====================
def rate_loop():
    while True:
        try:
            with RATES_LOCK:
                for cur, info in CURRENCIES.items():
                    rate = RATES[cur]
                    vol = info['volatility']
                    import random
                    change = random.uniform(-vol, vol)
                    RATES[cur] = max(0.01, round(rate * (1 + change), 4))
        except Exception as e:
            print('rate err:', e)
        time.sleep(3)

threading.Thread(target=rate_loop, daemon=True).start()


# ==================== РОУТЫ ====================
@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


@app.route('/api/player', methods=['POST', 'GET'])
def api_player():
    uid = None
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
    })


@app.route('/api/rates')
def api_rates():
    with RATES_LOCK:
        result = {}
        for cur, info in CURRENCIES.items():
            rate = RATES[cur]
            start = info['start']
            change = ((rate - start) / start) * 100
            result[cur] = {
                'name': info['name'],
                'rate': round(rate, 4),
                'change': round(change, 2),
            }
    return jsonify(result)


@app.route('/api/nft')
def api_nft():
    nft_data = load_json(NFT_FILE, {'minted': {}, 'items': {}})
    return jsonify({
        'types': NFT_TYPES,
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

    # выдать NFT
    max_num = 0
    for nid in items:
        try:
            n = int(nid.split('-')[1])
            if n > max_num: max_num = n
        except: pass
    new_id = f'N-{max_num + 1:04d}'

    u['gram'] = round(u.get('gram', 0) - info['price'], 2)
    u['nfts'] = u.get('nfts', []) + [new_id]
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
    nid = d.get('nid')
    price = d.get('price')
    if not uid or not nid or not price:
        return jsonify({'error': 'bad'}), 400

    market = load_json(MARKET_FILE, {})
    market[nid] = {'seller': uid, 'price': round(float(price), 2), 'listed_at': int(time.time())}
    save_json(MARKET_FILE, market)
    return jsonify({'ok': True})


@app.route('/api/top')
def api_top():
    users = load_json(USERS_FILE, {})
    arr = []
    for uid, u in users.items():
        arr.append({'name': u.get('name', 'Player'), 'gram': u.get('gram', 0)})
    arr.sort(key=lambda x: x['gram'], reverse=True)
    return jsonify(arr[:20])


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
