import json
import os
import time
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

DATA_FILE = 'rp_data.json'

BUILDINGS = {
    'farm':     {'name': '🌾 Ферма',      'cost': 200, 'desc': '+500 еды/час'},
    'factory':  {'name': '🏭 Завод',      'cost': 500, 'desc': '+300💰/час'},
    'barracks': {'name': '⚔️ Казармы',    'cost': 300, 'desc': '+200 армии/час'},
    'school':   {'name': '🎓 Школа',      'cost': 400, 'desc': '+1 технология/час'},
    'hospital': {'name': '🏥 Больница',   'cost': 350, 'desc': '+2 стабильности/час'},
    'police':   {'name': '🚔 Полиция',    'cost': 250, 'desc': '+3 стабильности/час'},
    'mine':     {'name': '⛏️ Шахта',      'cost': 400, 'desc': '+300 металла/час'},
    'oilrig':   {'name': '🛢️ Нефтевышка', 'cost': 600, 'desc': '+200 нефти/час'},
}

COUNTRIES_25 = [
    {'name': 'Россия', 'flag': '🇷🇺', 'pop': 146000000, 'treas': 50000, 'army': 1000000, 'tech': 5},
    {'name': 'США', 'flag': '🇺🇸', 'pop': 330000000, 'treas': 80000, 'army': 1500000, 'tech': 7},
    {'name': 'Китай', 'flag': '🇨🇳', 'pop': 1400000000, 'treas': 70000, 'army': 2000000, 'tech': 6},
    {'name': 'Германия', 'flag': '🇩🇪', 'pop': 83000000, 'treas': 60000, 'army': 300000, 'tech': 6},
    {'name': 'Франция', 'flag': '🇫🇷', 'pop': 67000000, 'treas': 55000, 'army': 350000, 'tech': 6},
    {'name': 'Великобритания', 'flag': '🇬🇧', 'pop': 67000000, 'treas': 58000, 'army': 300000, 'tech': 6},
    {'name': 'Япония', 'flag': '🇯🇵', 'pop': 125000000, 'treas': 65000, 'army': 250000, 'tech': 7},
    {'name': 'Индия', 'flag': '🇮🇳', 'pop': 1380000000, 'treas': 40000, 'army': 1400000, 'tech': 4},
    {'name': 'Бразилия', 'flag': '🇧🇷', 'pop': 213000000, 'treas': 35000, 'army': 400000, 'tech': 4},
    {'name': 'Канада', 'flag': '🇨🇦', 'pop': 38000000, 'treas': 50000, 'army': 150000, 'tech': 6},
    {'name': 'Италия', 'flag': '🇮🇹', 'pop': 60000000, 'treas': 48000, 'army': 200000, 'tech': 5},
    {'name': 'Испания', 'flag': '🇪🇸', 'pop': 47000000, 'treas': 40000, 'army': 150000, 'tech': 5},
    {'name': 'Турция', 'flag': '🇹🇷', 'pop': 84000000, 'treas': 30000, 'army': 500000, 'tech': 4},
    {'name': 'Южная Корея', 'flag': '🇰🇷', 'pop': 51000000, 'treas': 55000, 'army': 600000, 'tech': 7},
    {'name': 'Иран', 'flag': '🇮🇷', 'pop': 85000000, 'treas': 30000, 'army': 600000, 'tech': 4},
    {'name': 'Польша', 'flag': '🇵🇱', 'pop': 38000000, 'treas': 35000, 'army': 200000, 'tech': 5},
    {'name': 'Украина', 'flag': '🇺🇦', 'pop': 44000000, 'treas': 25000, 'army': 300000, 'tech': 4},
    {'name': 'Саудовская Аравия', 'flag': '🇸🇦', 'pop': 34000000, 'treas': 70000, 'army': 200000, 'tech': 5},
    {'name': 'Австралия', 'flag': '🇦🇺', 'pop': 26000000, 'treas': 45000, 'army': 100000, 'tech': 6},
    {'name': 'Мексика', 'flag': '🇲🇽', 'pop': 129000000, 'treas': 25000, 'army': 250000, 'tech': 3},
    {'name': 'Индонезия', 'flag': '🇮🇩', 'pop': 274000000, 'treas': 22000, 'army': 400000, 'tech': 3},
    {'name': 'Нигерия', 'flag': '🇳🇬', 'pop': 206000000, 'treas': 15000, 'army': 200000, 'tech': 2},
    {'name': 'Египет', 'flag': '🇪🇬', 'pop': 104000000, 'treas': 20000, 'army': 450000, 'tech': 3},
    {'name': 'ЮАР', 'flag': '🇿🇦', 'pop': 59000000, 'treas': 25000, 'army': 100000, 'tech': 4},
    {'name': 'Аргентина', 'flag': '🇦🇷', 'pop': 45000000, 'treas': 28000, 'army': 150000, 'tech': 4},
]


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    data = {'countries': {}, 'news': []}
    for i, c in enumerate(COUNTRIES_25):
        data['countries'][str(i)] = {
            'id': i, 'name': c['name'], 'flag': c['flag'], 'owner': None,
            'pop': c['pop'], 'treas': c['treas'], 'army': c['army'], 'tech': c['tech'],
            'stability': 70, 'food': 5000, 'metal': 2000, 'oil': 1000,
            'isNpc': True, 'cities': [],
        }
    return data


def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('save err:', e)


data = load_data()


def add_news(text):
    data['news'].insert(0, {'time': int(time.time()), 'text': text})
    data['news'] = data['news'][:50]
    save_data()


# ============================================================
# ЭКОНОМИКА (раз в час в фоне)
# ============================================================
import threading


def economy_tick():
    for cid, c in data['countries'].items():
        income = 0
        for city in c['cities']:
            inc = city['pop'] * 0.0005 * 3600 + 50
            b = city.get('buildings', {})
            if 'factory' in b:
                inc += 300 * b['factory']
            income += inc
        expense = c['army'] * 0.5
        c['treas'] += income - expense
        if c['treas'] < 0:
            c['treas'] = 0
            c['stability'] -= 5
        for city in c['cities']:
            b = city.get('buildings', {})
            c['food'] += 500 * b.get('farm', 0)
            c['metal'] += 300 * b.get('mine', 0)
            c['oil'] += 200 * b.get('oilrig', 0)
            c['army'] += 200 * b.get('barracks', 0)
            c['tech'] += 1 * b.get('school', 0)
            c['stability'] += 2 * b.get('hospital', 0) + 3 * b.get('police', 0)
        c['stability'] = max(0, min(100, c['stability']))
        if c['food'] > c['pop'] / 1000:
            growth = int((c['food'] / 100) * (c['stability'] / 100))
            c['pop'] += growth
            c['food'] -= growth * 10
        if c['isNpc'] and c['treas'] > 800 and c['cities']:
            bkey = random.choice(['farm', 'factory', 'barracks', 'police'])
            cost = BUILDINGS[bkey]['cost']
            if c['treas'] >= cost:
                c['treas'] -= cost
                city = c['cities'][0]
                city.setdefault('buildings', {})
                city['buildings'][bkey] = city['buildings'].get(bkey, 0) + 1
                add_news(f'{c["flag"]} {c["name"]}: построено {BUILDINGS[bkey]["name"]}')
    save_data()


def start_tick():
    while True:
        time.sleep(3600)
        try:
            economy_tick()
        except Exception as e:
            print('tick err:', e)


threading.Thread(target=start_tick, daemon=True).start()


# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


@app.route('/api/state')
def api_state():
    return jsonify({
        'countries': list(data['countries'].values()),
        'news': data['news'][:20],
        'buildings': BUILDINGS,
    })


@app.route('/api/take', methods=['POST'])
def api_take():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    if not uid or cid not in data['countries']:
        return jsonify({'error': 'bad request'}), 400

    for c in data['countries'].values():
        if c.get('owner') == uid:
            return jsonify({'error': 'already_have', 'country': c['name']}), 400

    country = data['countries'][cid]
    if country.get('owner'):
        return jsonify({'error': 'taken'}), 400

    country['owner'] = uid
    country['isNpc'] = False
    country['cities'].append({'name': 'Столица', 'pop': 500000, 'buildings': {}})
    add_news(f'{country["flag"]} {country["name"]}: новый правитель!')
    return jsonify({'ok': True})


@app.route('/api/build', methods=['POST'])
def api_build():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    city_idx = d.get('city_idx', 0)
    bkey = d.get('building')

    if not uid or cid not in data['countries'] or bkey not in BUILDINGS:
        return jsonify({'error': 'bad'}), 400

    country = data['countries'][cid]
    if country.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 400
    if city_idx >= len(country['cities']):
        return jsonify({'error': 'no_city'}), 400

    b = BUILDINGS[bkey]
    if country['treas'] < b['cost']:
        return jsonify({'error': 'no_money', 'need': b['cost'] - int(country['treas'])}), 400

    country['treas'] -= b['cost']
    city = country['cities'][city_idx]
    city.setdefault('buildings', {})
    city['buildings'][bkey] = city['buildings'].get(bkey, 0) + 1
    add_news(f'{country["flag"]} {country["name"]}: построено {b["name"]}')
    return jsonify({'ok': True, 'treas': country['treas']})


@app.route('/api/found_city', methods=['POST'])
def api_found_city():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    name = (d.get('name') or '').strip()[:20]
    if not uid or cid not in data['countries']:
        return jsonify({'error': 'bad'}), 400

    country = data['countries'][cid]
    if country.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 400
    if country['treas'] < 5000:
        return jsonify({'error': 'no_money'}), 400

    if not name:
        name = f'Город-{len(country["cities"]) + 1}'
    country['treas'] -= 5000
    country['cities'].append({'name': name, 'pop': 100000, 'buildings': {}})
    add_news(f'{country["flag"]} {country["name"]}: основан {name}')
    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
