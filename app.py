import json
import os
import time
import random
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = 'rp_data.json'

# ========== ЗДАНИЯ (без эмодзи) ==========
BUILDINGS = {
    'farm':     {'name': 'Ферма',      'cost': 300,  'desc': '+200 еды/мин',       'icon': 'wheat',  'effect': {'food': 200}},
    'factory':  {'name': 'Завод',      'cost': 800,  'desc': '+500💰/мин, -1 стаб.', 'icon': 'factory','effect': {'treasury': 500, 'stability': -1}},
    'barracks': {'name': 'Казармы',    'cost': 500,  'desc': '+100 армии/мин',      'icon': 'sword',  'effect': {'army': 100}},
    'school':   {'name': 'Школа',      'cost': 1000, 'desc': '+0.5 тех./мин',       'icon': 'book',   'effect': {'tech': 0.5}},
    'hospital': {'name': 'Больница',   'cost': 700,  'desc': '+2 стаб./мин',        'icon': 'heart',  'effect': {'stability': 2}},
    'police':   {'name': 'Полиция',    'cost': 400,  'desc': '+1 стаб./мин',        'icon': 'shield', 'effect': {'stability': 1}},
    'mine':     {'name': 'Шахта',      'cost': 600,  'desc': '+150 металла/мин',    'icon': 'pickaxe','effect': {'metal': 150}},
    'oilrig':   {'name': 'Нефтевышка', 'cost': 900,  'desc': '+100 нефти/мин',      'icon': 'oil',    'effect': {'oil': 100}},
    'market':   {'name': 'Рынок',      'cost': 700,  'desc': '+300💰/мин',          'icon': 'cart',   'effect': {'treasury': 300}},
    'bank':     {'name': 'Банк',       'cost': 1500, 'desc': '+800💰/мин',          'icon': 'bank',   'effect': {'treasury': 800}},
    'wall':     {'name': 'Стена',      'cost': 1200, 'desc': '+30% защиты',         'icon': 'wall',   'effect': {'defense': 0.3}},
    'port':     {'name': 'Порт',       'cost': 1000, 'desc': '+200💰/+100 еды',     'icon': 'anchor', 'effect': {'treasury': 200, 'food': 100}},
}

PROVINCE_TYPES = {
    'plain':    {'name': 'Равнина',   'icon': 'plain',   'bonus': {'food': 500},    'desc': 'Много еды'},
    'forest':   {'name': 'Лес',       'icon': 'forest',  'bonus': {'food': 200, 'metal': 100}, 'desc': 'Еда + металл'},
    'mountain': {'name': 'Горы',      'icon': 'mountain','bonus': {'metal': 400},   'desc': 'Много металла'},
    'desert':   {'name': 'Пустыня',   'icon': 'desert',  'bonus': {'oil': 300},     'desc': 'Нефть'},
    'coast':    {'name': 'Побережье', 'icon': 'coast',   'bonus': {'treasury': 400},'desc': 'Торговля'},
    'city':     {'name': 'Город',     'icon': 'city',    'bonus': {'treasury': 600},'desc': 'Экономика'},
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


def make_provinces(pop):
    types_pool = ['plain', 'forest', 'mountain', 'desert', 'coast', 'city']
    random.shuffle(types_pool)
    return [
        {'name': f'Провинция {i+1}', 'type': types_pool[i % len(types_pool)],
         'pop': pop // 6, 'buildings': {}}
        for i in range(5)
    ]


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    d = {'countries': {}, 'news': [], 'alliances': [], 'wars': []}
    for i, c in enumerate(COUNTRIES_25):
        d['countries'][str(i)] = {
            'id': i, 'name': c['name'], 'flag': c['flag'],
            'owner': None, 'pop': c['pop'], 'treas': c['treas'],
            'army': c['army'], 'tech': c['tech'], 'stability': 70,
            'food': 5000, 'metal': 2000, 'oil': 1000,
            'isNpc': True, 'bonus': 0,
            'provinces': make_provinces(c['pop']),
        }
    return d


def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print('save err:', e)


data = load_data()


def add_news(t):
    data['news'].insert(0, {'time': int(time.time()), 'text': t})
    data['news'] = data['news'][:50]


def find_alliance(c1, c2):
    for a in data.get('alliances', []):
        if str(c1) in a['members'] and str(c2) in a['members']:
            return a
    return None


def is_at_war(c1, c2):
    for w in data.get('wars', []):
        if {w['attacker'], w['defender']} == {str(c1), str(c2)}:
            return True
    return False


def province_income(p, c):
    inc = p['pop'] * 0.0001 + 20
    t = p.get('type', 'plain')
    if t in PROVINCE_TYPES:
        inc += PROVINCE_TYPES[t]['bonus'].get('treasury', 0)
    b = p.get('buildings', {})
    for k, cnt in b.items():
        if k == 'factory': inc += 500 * cnt
        elif k == 'market': inc += 300 * cnt
        elif k == 'bank': inc += 800 * cnt
        elif k == 'port': inc += 200 * cnt
    inc *= (1 + c['tech'] * 0.05) * (1 + c.get('bonus', 0))
    return inc


def country_income(c):
    return sum(province_income(p, c) for p in c['provinces'])


def tick():
    for c in data['countries'].values():
        income = country_income(c)
        expense = c['army'] * 0.05
        c['treas'] += income - expense
        if c['treas'] < 0:
            c['treas'] = 0
            c['stability'] -= 2
        for p in c['provinces']:
            t = p.get('type', 'plain')
            if t in PROVINCE_TYPES:
                bonus = PROVINCE_TYPES[t]['bonus']
                c['food'] += bonus.get('food', 0)
                c['metal'] += bonus.get('metal', 0)
                c['oil'] += bonus.get('oil', 0)
            b = p.get('buildings', {})
            for k, cnt in b.items():
                if k == 'farm': c['food'] += 200 * cnt
                elif k == 'mine': c['metal'] += 150 * cnt
                elif k == 'oilrig': c['oil'] += 100 * cnt
                elif k == 'barracks': c['army'] += 100 * cnt
                elif k == 'school': c['tech'] += 0.5 * cnt
                elif k == 'hospital': c['stability'] += 2 * cnt
                elif k == 'police': c['stability'] += 1 * cnt
                elif k == 'factory': c['stability'] -= 1 * cnt
                elif k == 'port': c['food'] += 100 * cnt
        c['stability'] = max(0, min(100, c['stability']))
        if c['food'] > c['pop'] / 500:
            growth = int((c['food'] / 500) * (c['stability'] / 100))
            c['pop'] += growth
            c['food'] -= growth * 5
        if c['isNpc'] and random.random() < 0.05:
            npc_action(c)
    process_wars()
    if random.random() < 0.1:
        random_event()
    save_data()


def npc_action(c):
    if not c['provinces']: return
    actions = []
    if c['treas'] > 500: actions.append('farm')
    if c['treas'] > 1000: actions.append('factory')
    if c['treas'] > 600: actions.append('barracks')
    if c['stability'] < 50: actions.append('police')
    if c['treas'] > 900: actions.append('mine')
    if c['treas'] > 2000: actions.append('wall')
    if not actions: return
    bkey = random.choice(actions)
    cost = BUILDINGS[bkey]['cost']
    if c['treas'] >= cost:
        c['treas'] -= cost
        p = random.choice(c['provinces'])
        p.setdefault('buildings', {})
        p['buildings'][bkey] = p['buildings'].get(bkey, 0) + 1


def process_wars():
    finished = []
    for w in data.get('wars', []):
        w['turns'] = w.get('turns', 0) + 1
        a = data['countries'].get(w['attacker'])
        d = data['countries'].get(w['defender'])
        if not a or not d:
            finished.append(w); continue
        a_power = a['army'] * (1 + a['tech'] * 0.1) * (a['stability'] / 100)
        d_power = d['army'] * (1 + d['tech'] * 0.1) * (d['stability'] / 100)
        for p in d['provinces']:
            wall = p.get('buildings', {}).get('wall', 0)
            d_power *= (1 + wall * 0.3)
        if random.random() < 0.5:
            d['army'] = max(0, d['army'] - int(d['army'] * 0.15))
            a['army'] = max(0, a['army'] - int(a['army'] * 0.08))
            d['stability'] -= 3
        else:
            a['army'] = max(0, a['army'] - int(a['army'] * 0.15))
            d['army'] = max(0, d['army'] - int(d['army'] * 0.08))
            a['stability'] -= 3
        if a['army'] < a['pop'] * 0.0001 or d['army'] < d['pop'] * 0.0001 or w['turns'] >= 10:
            winner, loser = (a, d) if a_power > d_power else (d, a)
            loot = int(loser['treas'] * 0.3)
            winner['treas'] += loot
            loser['treas'] -= loot
            add_news(f'Война {a["flag"]} {a["name"]} vs {d["flag"]} {d["name"]} окончена. Победил {winner["flag"]} {winner["name"]}, забрал {loot}💰')
            finished.append(w)
    for w in finished:
        data['wars'].remove(w)


def random_event():
    events = [
        ('Извержение вулкана в {name}!', lambda c: c.update({'stability': max(0, c['stability'] - 15)})),
        ('Найдено золото в {name}!', lambda c: c.update({'treas': c['treas'] + 3000})),
        ('Урожай в {name}!', lambda c: c.update({'food': c['food'] + 5000})),
        ('Бунт в {name}!', lambda c: c.update({'stability': max(0, c['stability'] - 20)})),
        ('Бум в {name}!', lambda c: c.update({'treas': c['treas'] + 5000})),
    ]
    ev, action = random.choice(events)
    c = random.choice(list(data['countries'].values()))
    try:
        action(c)
        add_news(ev.format(name=f'{c["flag"]} {c["name"]}'))
    except: pass


def start_tick():
    while True:
        time.sleep(60)
        try:
            tick()
        except Exception as e:
            print('tick err:', e)


threading.Thread(target=start_tick, daemon=True).start()


# ============================================================
# HTML — БЕЗ ЭМОДЗИ, ТОЛЬКО SVG ИКОНКИ
# ============================================================
HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#000000">
<title>RP Countries</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--bg:#000;--card:#1c1c1e;--card-2:#2c2c2e;--line:#2a2a2c;--text:#fff;--dim:#8e8e93;--muted:#48484a;--accent:#7c5cff;--accent-2:#5e5ce6;--green:#30d158;--red:#ff453a;--gold:#ffd60a;--blue:#0a84ff;--radius:16px}
body.theme-light{--bg:#f2f2f7;--card:#fff;--card-2:#e5e5ea;--line:#d1d1d6;--text:#000;--dim:#8e8e93;--muted:#c7c7cc}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.4;padding-bottom:calc(90px + env(safe-area-inset-bottom));letter-spacing:-.3px;-webkit-font-smoothing:antialiased}
.header{background:rgba(0,0,0,0.78);backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);border-bottom:.5px solid var(--line);position:sticky;top:0;z-index:50;padding:10px 16px;padding-top:calc(10px + env(safe-area-inset-top));display:flex;justify-content:space-between;align-items:center;min-height:52px}
body.theme-light .header{background:rgba(255,255,255,0.78)}
.header-left{display:flex;align-items:center;gap:10px}
.logo-icon{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-icon svg{width:20px;height:20px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.header-text .logo{font-size:16px;font-weight:700;letter-spacing:-.3px}
.header-text .sub{font-size:11px;color:var(--dim);margin-top:1px}
.badge{font-size:13px;font-weight:600;color:var(--accent);background:rgba(124,92,255,0.12);border:1px solid rgba(124,92,255,0.3);padding:5px 10px;border-radius:20px;display:flex;align-items:center;gap:5px}
.badge svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.4}
.container{padding:0 16px 16px;max-width:540px;margin:0 auto}
.large-title{font-size:34px;font-weight:800;letter-spacing:-.8px;padding:14px 0 12px}
.card{background:var(--card);border-radius:var(--radius);margin-bottom:14px;overflow:hidden}
.card-title{font-size:11px;font-weight:700;color:var(--dim);text-transform:uppercase;letter-spacing:1.2px;padding:16px 16px 8px}
.btn{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border:none;border-radius:14px;padding:14px 18px;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer;width:100%;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn:active{transform:scale(.98);opacity:.85}
.btn.secondary{background:var(--card-2);color:var(--text)}
.btn.small{padding:8px 14px;font-size:14px;margin:0;width:auto;border-radius:10px}
.btn:disabled{opacity:.4}
.row{display:flex;align-items:center;gap:12px;padding:13px 16px;border-top:.5px solid var(--line);cursor:pointer}
.row:active{background:var(--card-2)}
.row:first-child{border-top:none}
.row-icon{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;flex-shrink:0}
.row-icon svg{width:20px;height:20px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.row-icon.plain{background:linear-gradient(135deg,#d4a373,#a67c52)}
.row-icon.forest{background:linear-gradient(135deg,#2d6a4f,#1b4332)}
.row-icon.mountain{background:linear-gradient(135deg,#6c757d,#495057)}
.row-icon.desert{background:linear-gradient(135deg,#f4a261,#e76f51)}
.row-icon.coast{background:linear-gradient(135deg,#48cae4,#0077b6)}
.row-icon.city{background:linear-gradient(135deg,#8338ec,#3a86ff)}
.row-info{flex:1;min-width:0}
.row-title{font-size:15px;font-weight:600}
.row-sub{font-size:12px;color:var(--dim);margin-top:2px}
.row-chev{color:var(--muted);font-size:20px;font-weight:300}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat{background:var(--card);border-radius:var(--radius);padding:14px}
.stat-head{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.stat-head svg{width:14px;height:14px;stroke:var(--dim);fill:none;stroke-width:2}
.stat-k{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.6px;font-weight:600}
.stat-v{font-size:22px;font-weight:700;letter-spacing:-.5px}
.stat-v.gold{color:var(--gold)}
.stat-v.green{color:var(--green)}
.stat-v.purple{color:var(--accent)}
.stat-v.blue{color:var(--blue)}
.tab-bar{position:fixed;bottom:0;left:0;right:0;background:rgba(20,20,22,0.85);backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);border-top:.5px solid var(--line);display:flex;padding:6px 4px calc(8px + env(safe-area-inset-bottom));z-index:100;max-width:540px;margin:0 auto}
body.theme-light .tab-bar{background:rgba(255,255,255,0.85)}
.tab-item{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 2px;color:var(--dim);cursor:pointer;font-size:10px;font-weight:500;user-select:none}
.tab-item.active{color:var(--accent)}
.tab-item svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.tab-content{display:none}
.tab-content.active{display:block;animation:fade .3s}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;display:none;align-items:flex-end;justify-content:center}
.modal-overlay.open{display:flex;animation:fadeIn .2s}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{background:var(--card);border-radius:22px 22px 0 0;width:100%;max-width:540px;max-height:85vh;overflow-y:auto;padding-bottom:calc(20px + env(safe-area-inset-bottom));animation:slideUp .3s cubic-bezier(0.32,0.72,0,1)}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
.modal-header{display:flex;justify-content:space-between;align-items:center;padding:18px 20px;border-bottom:.5px solid var(--line);position:sticky;top:0;background:var(--card);z-index:1}
.modal-title{font-size:18px;font-weight:700}
.modal-close{background:var(--card-2);border:none;width:32px;height:32px;border-radius:16px;cursor:pointer;color:var(--text);font-size:16px;display:flex;align-items:center;justify-content:center}
.modal-body{padding:16px 20px}
.empty{text-align:center;padding:40px 20px;color:var(--dim);font-size:14px}
.toast{position:fixed;bottom:calc(110px + env(safe-area-inset-bottom));left:50%;transform:translateX(-50%) translateY(120%);background:rgba(44,44,46,0.96);backdrop-filter:blur(20px);color:#fff;padding:12px 20px;border-radius:14px;font-size:14px;z-index:999;opacity:0;transition:.25s;max-width:90vw;text-align:center;font-weight:500}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.error{background:rgba(255,69,58,0.96)}
.toast.success{background:rgba(48,209,88,0.96)}
.loader{width:24px;height:24px;border:2px solid var(--card-2);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;margin:60px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.building-row{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:.5px solid var(--line)}
.building-row:last-child{border:none}
.building-left{display:flex;align-items:center;gap:12px}
.building-icon{width:40px;height:40px;border-radius:10px;background:var(--card-2);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.building-icon svg{width:22px;height:22px;stroke:var(--accent);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.building-name{font-size:15px;font-weight:600}
.building-desc{font-size:12px;color:var(--dim);margin-top:2px}
.building-cost{font-size:14px;font-weight:700;color:var(--gold);margin-right:8px}
.chip{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:10px;font-size:11px;font-weight:700;margin-left:4px}
.chip.war{background:rgba(255,69,58,0.2);color:var(--red)}
.chip.ally{background:rgba(48,209,88,0.2);color:var(--green)}
.flag-circle{width:48px;height:48px;border-radius:50%;background:var(--card-2);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0}
.toggle{width:51px;height:31px;background:var(--card-2);border-radius:20px;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0}
.toggle.on{background:var(--green)}
.toggle::after{content:'';position:absolute;top:2px;left:2px;width:27px;height:27px;border-radius:50%;background:#fff;transition:transform .2s}
.toggle.on::after{transform:translateX(20px)}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="logo-icon">
      <svg viewBox="0 0 24 24"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/></svg>
    </div>
    <div class="header-text">
      <div class="logo">RP Countries</div>
      <div class="sub" id="subTitle">—</div>
    </div>
  </div>
  <div class="badge" id="headerBadge">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4.5a2.5 2.5 0 010 5H9"/></svg>
    <span id="badgeText">—</span>
  </div>
</div>

<div class="container">
  <div class="large-title" id="pageTitle">—</div>

  <div class="tab-content active" id="tab-game">
    <div id="gameContent"><div class="loader"></div></div>
  </div>

  <div class="tab-content" id="tab-provinces">
    <div id="provincesContent"></div>
  </div>

  <div class="tab-content" id="tab-diplomacy">
    <div id="diplomacyContent"></div>
  </div>

  <div class="tab-content" id="tab-news">
    <div id="newsContent"></div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-item active" data-tab="game" data-title="Игра">
    <svg viewBox="0 0 24 24"><path d="M3 12l9-9 9 9"/><path d="M5 10v10a1 1 0 001 1h12a1 1 0 001-1V10"/></svg>
    <span>Игра</span>
  </div>
  <div class="tab-item" data-tab="provinces" data-title="Регионы">
    <svg viewBox="0 0 24 24"><path d="M9 3L3 6v15l6-3 6 3 6-3V3l-6 3z"/><path d="M9 3v15M15 6v15"/></svg>
    <span>Регионы</span>
  </div>
  <div class="tab-item" data-tab="diplomacy" data-title="Дипломатия">
    <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/></svg>
    <span>Союзы</span>
  </div>
  <div class="tab-item" data-tab="news" data-title="Новости">
    <svg viewBox="0 0 24 24"><path d="M4 4h16v16H4z"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>
    <span>Новости</span>
  </div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modalTitle">—</div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// SVG icon library
const ICONS = {
  wheat: '<svg viewBox="0 0 24 24"><path d="M12 22V8"/><path d="M8 6l4-4 4 4"/><path d="M8 12l4-4 4 4"/><path d="M8 18l4-4 4 4"/></svg>',
  factory: '<svg viewBox="0 0 24 24"><path d="M2 20h20V10l-6 4V10l-6 4V6H4v14z"/><path d="M6 14h2M10 14h2M14 14h2"/></svg>',
  sword: '<svg viewBox="0 0 24 24"><path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6M16 16l4 4M19 21l2-2"/></svg>',
  book: '<svg viewBox="0 0 24 24"><path d="M4 4h7a3 3 0 013 3v13a2 2 0 00-2-2H4V4z"/><path d="M20 4h-7a3 3 0 00-3 3v13a2 2 0 012-2h8V4z"/></svg>',
  heart: '<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 10-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z"/></svg>',
  shield: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  pickaxe: '<svg viewBox="0 0 24 24"><path d="M14 10l-8 8-2 2 6-8"/><path d="M14 10l4-4 3-1-1 3-4 4"/><path d="M9 13l2 2"/></svg>',
  oil: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>',
  cart: '<svg viewBox="0 0 24 24"><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 2h3l3 12h10l3-8H6"/></svg>',
  bank: '<svg viewBox="0 0 24 24"><path d="M3 21h18M4 21V10M20 21V10M8 21V10M16 21V10M12 21V10"/><path d="M2 10l10-7 10 7H2z"/></svg>',
  wall: '<svg viewBox="0 0 24 24"><path d="M3 20V8h18v12"/><path d="M3 12h18M3 16h18"/><path d="M7 8V4M12 8V4M17 8V4"/></svg>',
  anchor: '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><path d="M12 7v14"/><path d="M5 12H3a9 9 0 009 9 9 9 0 009-9h-2"/></svg>',
  plain: '<svg viewBox="0 0 24 24"><path d="M2 18h20"/><path d="M6 18c2-4 4-6 6-6s4 2 6 6"/></svg>',
  forest: '<svg viewBox="0 0 24 24"><path d="M12 2L6 12h4l-3 6h10l-3-6h4z"/><path d="M12 18v4"/></svg>',
  mountain: '<svg viewBox="0 0 24 24"><path d="M2 20l7-12 4 6 3-4 6 10H2z"/></svg>',
  desert: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M2 20c4-2 8-2 10 0s6 2 10 0"/></svg>',
  coast: '<svg viewBox="0 0 24 24"><path d="M2 12c2-1 4-1 6 0s4 1 6 0 4-1 6 0"/><path d="M2 17c2-1 4-1 6 0s4 1 6 0 4-1 6 0"/><circle cx="18" cy="6" r="3"/></svg>',
  city: '<svg viewBox="0 0 24 24"><path d="M3 21h18V7l-6 3V7l-6 3V3H3v18z"/><path d="M6 12h1M6 16h1M11 12h1M11 16h1M16 12h1M16 16h1"/></svg>',
  coin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 10h4.5a2.5 2.5 0 010 5H9"/></svg>',
  people: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/></svg>',
  sword2: '<svg viewBox="0 0 24 24"><path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6M16 16l4 4M19 21l2-2"/></svg>',
  flask: '<svg viewBox="0 0 24 24"><path d="M9 2v6L4 20h16L15 8V2"/><path d="M9 2h6"/></svg>',
  food: '<svg viewBox="0 0 24 24"><path d="M12 22V8"/><path d="M8 6l4-4 4 4"/></svg>',
  metal: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>',
  oil2: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/></svg>',
  map: '<svg viewBox="0 0 24 24"><path d="M9 3L3 6v15l6-3 6 3 6-3V3l-6 3z"/><path d="M9 3v15M15 6v15"/></svg>',
};

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// FIX: UID через localStorage, чтобы не терялся
let UID = tg?.initDataUnsafe?.user?.id || 0;
if (UID) {
  localStorage.setItem('rp_uid', UID);
} else {
  const cached = localStorage.getItem('rp_uid');
  if (cached) UID = parseInt(cached);
}

let state = null;

async function api(path, body) {
  try {
    const r = await fetch(path, {
      method: body ? 'POST' : 'GET',
      headers: {'Content-Type': 'application/json'},
      body: body ? JSON.stringify({uid: UID, ...body}) : undefined
    });
    return await r.json();
  } catch(e) { return {error: 'network'}; }
}

function toast(msg, type='') {
  const el = document.getElementById('toast');
  el.textContent = msg; el.className = 'toast ' + type; el.classList.add('show');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('show'), 2200);
}

function fmt(n) {
  n = Math.floor(n);
  if (n >= 1e9) return (n/1e9).toFixed(1) + ' млрд';
  if (n >= 1e6) return (n/1e6).toFixed(1) + ' млн';
  if (n >= 1e3) return (n/1e3).toFixed(1) + ' тыс';
  return n.toString();
}

async function loadState() {
  const r = await api('/api/state');
  if (r.error) return;
  state = r;
  render();
}

function getMy() {
  if (!state || state.my_country_id === null) return null;
  return state.countries.find(c => c.id === state.my_country_id);
}

function provIncome(p, c) {
  let inc = p.pop * 0.0001 + 20;
  const t = p.type || 'plain';
  if (state.province_types[t]) inc += state.province_types[t].bonus.treasury || 0;
  const b = p.buildings || {};
  for (const [k, cnt] of Object.entries(b)) {
    if (!state.buildings[k]) continue;
    const eff = state.buildings[k].effect || {};
    inc += (eff.treasury || 0) * cnt;
  }
  inc *= (1 + c.tech * 0.05) * (1 + (c.bonus || 0));
  return inc;
}

function countryIncome(c) {
  let t = 0;
  for (const p of c.provinces) t += provIncome(p, c);
  return t;
}

function render() {
  const my = getMy();
  if (!my) { renderChoose(); return; }
  document.getElementById('badgeText').textContent = fmt(my.treas);
  document.getElementById('subTitle').textContent = my.flag + ' ' + my.name;
  document.getElementById('pageTitle').textContent = 'Игра';
  renderGame(my);
  renderProvinces(my);
  renderDiplomacy(my);
  renderNews();
}

function renderGame(my) {
  const income = countryIncome(my);
  const expense = my.army * 0.05;
  const myWars = state.wars.filter(w => w.attacker === String(my.id) || w.defender === String(my.id));
  const myAlliances = state.alliances.filter(a => a.members.includes(String(my.id)));

  document.getElementById('gameContent').innerHTML = `
    <div class="card" style="background:linear-gradient(135deg,rgba(124,92,255,0.18),rgba(94,92,230,0.05));border:1px solid rgba(124,92,255,0.3)">
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
          <div class="flag-circle">${my.flag}</div>
          <div style="flex:1">
            <div style="font-size:22px;font-weight:700">${my.name}</div>
            <div style="font-size:12px;color:var(--dim);margin-top:4px">
              ${myWars.length ? '<span class="chip war">ВОЙНА</span>' : ''}
              ${myAlliances.length ? '<span class="chip ally">'+myAlliances.length+' СОЮЗ</span>' : ''}
            </div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.8px;font-weight:600">Казна</div>
        <div style="font-size:38px;font-weight:800;color:var(--gold);line-height:1.1;margin-top:4px">${fmt(my.treas)}</div>
        <div style="font-size:14px;color:var(--green);margin-top:8px">+${fmt(income)} / -${fmt(expense)} = <b style="color:var(--text)">${fmt(income-expense)}/мин</b></div>
      </div>
    </div>

    <div class="grid2">
      <div class="stat"><div class="stat-head">${ICONS.people}<div class="stat-k">Население</div></div><div class="stat-v">${fmt(my.pop)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.sword2}<div class="stat-k">Армия</div></div><div class="stat-v">${fmt(my.army)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.flask}<div class="stat-k">Технологии</div></div><div class="stat-v purple">${Math.floor(my.tech)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.heart}<div class="stat-k">Стабильность</div></div><div class="stat-v green">${Math.floor(my.stability)}%</div></div>
      <div class="stat"><div class="stat-head">${ICONS.food}<div class="stat-k">Еда</div></div><div class="stat-v">${fmt(my.food)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.metal}<div class="stat-k">Металл</div></div><div class="stat-v">${fmt(my.metal)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.oil2}<div class="stat-k">Нефть</div></div><div class="stat-v">${fmt(my.oil)}</div></div>
      <div class="stat"><div class="stat-head">${ICONS.map}<div class="stat-k">Провинций</div></div><div class="stat-v blue">${my.provinces.length}</div></div>
    </div>

    <div class="card-title">Действия</div>
    <div class="card">
      <div class="row" onclick="openArmy()">
        <div class="row-icon">${ICONS.sword2}</div>
        <div class="row-info"><div class="row-title">Армия</div><div class="row-sub">Найм солдат</div></div>
        <div class="row-chev">›</div>
      </div>
      <div class="row" onclick="openTrade()">
        <div class="row-icon">${ICONS.cart}</div>
        <div class="row-info"><div class="row-title">Торговля</div><div class="row-sub">Продажа ресурсов</div></div>
        <div class="row-chev">›</div>
      </div>
      <div class="row" onclick="openWar()">
        <div class="row-icon">${ICONS.sword2}</div>
        <div class="row-info"><div class="row-title">Война</div><div class="row-sub">Объявить войну</div></div>
        <div class="row-chev">›</div>
      </div>
      <div class="row" onclick="openTop()">
        <div class="row-icon">${ICONS.bank}</div>
        <div class="row-info"><div class="row-title">Топ стран</div><div class="row-sub">Рейтинг по казне</div></div>
        <div class="row-chev">›</div>
      </div>
      <div class="row" onclick="openSettings()">
        <div class="row-icon">${ICONS.wall}</div>
        <div class="row-info"><div class="row-title">Настройки</div><div class="row-sub">Тема, вибрация</div></div>
        <div class="row-chev">›</div>
      </div>
    </div>
  `;
}

function renderChoose() {
  document.getElementById('pageTitle').textContent = 'Выбор страны';
  document.getElementById('subTitle').textContent = 'Выбери одну из 25';
  document.getElementById('badgeText').textContent = '—';
  document.getElementById('gameContent').innerHTML = `
    <div class="card" style="background:linear-gradient(135deg,rgba(124,92,255,0.12),rgba(94,92,230,0.03));border:1px solid rgba(124,92,255,0.2);padding:20px;text-align:center">
      <div style="font-size:18px;font-weight:700;margin-bottom:6px">Выбери свою страну</div>
      <div style="font-size:13px;color:var(--dim)">Выбор — навсегда. Поменять нельзя.</div>
    </div>
    <div class="card">
      ${state.countries.map(c => `
        <div class="row" onclick="${c.owner ? '' : `takeCountry(${c.id})`}">
          <div class="flag-circle">${c.flag}</div>
          <div class="row-info">
            <div class="row-title">${c.name}</div>
            <div class="row-sub">${fmt(c.pop)} чел · ${fmt(c.treas)}💰 · ${c.provinces.length} провинций</div>
          </div>
          <div class="row-chev">${c.owner ? '🔒' : '›'}</div>
        </div>
      `).join('')}
    </div>
  `;
  document.getElementById('provincesContent').innerHTML = '';
  document.getElementById('diplomacyContent').innerHTML = '';
  document.getElementById('newsContent').innerHTML = '';
}

async function takeCountry(cid) {
  if (!confirm('Выбрать эту страну? Поменять нельзя!')) return;
  const r = await api('/api/take', {cid});
  if (r.error === 'taken') return toast('Занята', 'error');
  if (r.error === 'already_have') return toast('Уже есть страна', 'error');
  if (r.ok) { toast('Страна твоя!', 'success'); loadState(); }
}

function renderProvinces(my) {
  document.getElementById('provincesContent').innerHTML = `
    <div class="card">
      ${my.provinces.map((p, i) => {
        const t = state.province_types[p.type] || {name:'?', icon:'plain'};
        const inc = provIncome(p, my);
        return `
          <div class="row" onclick="openProvince(${i})">
            <div class="row-icon ${t.icon}">${ICONS[t.icon] || ICONS.plain}</div>
            <div class="row-info">
              <div class="row-title">${p.name}</div>
              <div class="row-sub">${t.name} · ${fmt(p.pop)} чел · +${fmt(inc)}/мин</div>
            </div>
            <div class="row-chev">›</div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function openProvince(i) {
  const my = getMy();
  const p = my.provinces[i];
  const t = state.province_types[p.type] || {name:'?',desc:''};
  const b = p.buildings || {};
  const rows = Object.entries(b).map(([k, cnt]) =>
    `<div class="building-row"><div class="building-left"><div class="building-icon">${ICONS[state.buildings[k]?.icon] || ICONS.farm}</div><div class="building-name">${state.buildings[k]?.name || k}</div></div><div style="font-weight:700">×${cnt}</div></div>`
  ).join('');
  openModal(p.name, `
    <div style="font-size:14px;color:var(--dim);margin-bottom:14px">${t.name} — ${t.desc}</div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Население</span><b>${fmt(p.pop)}</b>
    </div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Доход</span><b style="color:var(--gold)">${fmt(provIncome(p, my))}/мин</b>
    </div>
    <div class="card-title">Здания</div>
    ${rows || '<div class="empty">Пока пусто</div>'}
    <button class="btn" style="margin-top:14px" onclick="closeModal();openBuildMenu(${i})">Построить</button>
  `);
}

function openBuildMenu(idx) {
  const my = getMy();
  openModal('Строительство', `
    <div style="font-size:13px;color:var(--dim);margin-bottom:6px">Провинция: <b style="color:var(--text)">${my.provinces[idx].name}</b></div>
    <div style="font-size:13px;color:var(--dim);margin-bottom:14px">Казна: <b style="color:var(--gold)">${fmt(my.treas)}</b></div>
    ${Object.entries(state.buildings).map(([k, b]) => `
      <div class="building-row">
        <div class="building-left">
          <div class="building-icon">${ICONS[b.icon] || ICONS.farm}</div>
          <div>
            <div class="building-name">${b.name}</div>
            <div class="building-desc">${b.desc}</div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="building-cost">${b.cost}</div>
          <button class="btn small" onclick="buildIn(${idx},'${k}')" ${my.treas < b.cost ? 'disabled' : ''}>+</button>
        </div>
      </div>
    `).join('')}
  `);
}

async function buildIn(idx, bkey) {
  const my = getMy();
  const r = await api('/api/build', {cid: my.id, prov_idx: idx, bkey});
  if (r.error === 'no_money') return toast(`Не хватает ${r.need}`, 'error');
  if (r.error === 'not_yours') return toast('Ошибка владельца', 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast('Построено', 'success');
  await loadState();
  openBuildMenu(idx);
}

async function openArmy() {
  const my = getMy();
  openModal('Армия', `
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Солдат</span><b>${fmt(my.army)}</b>
    </div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Казна</span><b style="color:var(--gold)">${fmt(my.treas)}</b>
    </div>
    <div style="font-size:13px;color:var(--dim);margin:14px 0 10px">Найм: 1 солдат = 2</div>
    <button class="btn" onclick="recruit(1000)">+1 000 солдат (2 000)</button>
    <button class="btn" onclick="recruit(5000)">+5 000 солдат (10 000)</button>
    <button class="btn" onclick="recruit(10000)">+10 000 солдат (20 000)</button>
  `);
}

async function recruit(n) {
  const my = getMy();
  const r = await api('/api/recruit', {cid: my.id, amount: n});
  if (r.error === 'no_money') return toast(`Нужно ${fmt(r.need)}`, 'error');
  if (r.error === 'not_yours') return toast('Ошибка владельца', 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast(`+${fmt(n)} солдат`, 'success');
  await loadState();
  openArmy();
}

function renderDiplomacy(my) {
  const myAlliances = state.alliances.filter(a => a.members.includes(String(my.id)));
  const myWars = state.wars.filter(w => w.attacker === String(my.id) || w.defender === String(my.id));

  let html = '';
  if (myWars.length) {
    html += '<div class="card-title">Активные войны</div><div class="card">';
    myWars.forEach(w => {
      const a = state.countries.find(c => c.id === parseInt(w.attacker));
      const d = state.countries.find(c => c.id === parseInt(w.defender));
      html += `<div class="row"><div class="row-icon">${ICONS.sword2}</div><div class="row-info"><div class="row-title">${a?.name}</div><div class="row-sub">vs ${d?.name}</div></div></div>`;
    });
    html += '</div>';
  }
  if (myAlliances.length) {
    html += '<div class="card-title">Твои союзы</div><div class="card">';
    myAlliances.forEach(a => {
      const allies = a.members.filter(m => m !== String(my.id)).map(m => state.countries.find(c => c.id === parseInt(m)));
      allies.forEach(al => {
        html += `<div class="row"><div class="row-icon">${ICONS.people}</div><div class="row-info"><div class="row-title">${al?.name}</div><div class="row-sub">Союзник</div></div></div>`;
      });
    });
    html += '</div>';
  }

  const others = state.countries.filter(c => c.id !== my.id && c.owner);
  html += '<div class="card-title">Предложить союз</div><div class="card">';
  if (!others.length) {
    html += '<div class="empty">Пока нет других игроков</div>';
  } else {
    others.forEach(c => {
      html += `<div class="row" onclick="offerAlly(${c.id})"><div class="flag-circle">${c.flag}</div><div class="row-info"><div class="row-title">${c.name}</div><div class="row-sub">Игрок</div></div><div class="row-chev">›</div></div>`;
    });
  }
  html += '</div>';

  document.getElementById('diplomacyContent').innerHTML = html;
}

async function offerAlly(cid) {
  const my = getMy();
  const r = await api('/api/ally', {cid: my.id, target: cid});
  if (r.error) return toast(r.error, 'error');
  toast('Союз заключён', 'success');
  await loadState();
}

function openWar() {
  const my = getMy();
  const others = state.countries.filter(c => c.id !== my.id);
  openModal('Объявить войну', `
    ${others.slice(0, 15).map(c => `
      <div class="row" onclick="declareWar(${c.id})">
        <div class="flag-circle">${c.flag}</div>
        <div class="row-info">
          <div class="row-title">${c.name}</div>
          <div class="row-sub">${fmt(c.army)} армии · ${fmt(c.treas)}</div>
        </div>
        <div class="row-chev" style="color:var(--red)">›</div>
      </div>
    `).join('')}
  `);
}

async function declareWar(cid) {
  if (!confirm('Объявить войну?')) return;
  const my = getMy();
  const r = await api('/api/war', {cid: my.id, target: cid});
  if (r.error) return toast(r.error, 'error');
  toast('Война объявлена!', 'success');
  await loadState();
  closeModal();
}

function openTrade() {
  const my = getMy();
  openModal('Торговля', `
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>Еда: ${fmt(my.food)}</span><span style="color:var(--gold)">1/шт</span></div>
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>Металл: ${fmt(my.metal)}</span><span style="color:var(--gold)">3/шт</span></div>
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>Нефть: ${fmt(my.oil)}</span><span style="color:var(--gold)">5/шт</span></div>
    <button class="btn" style="margin-top:14px" onclick="sell('food', 1000)">Продать 1000 еды</button>
    <button class="btn" onclick="sell('metal', 500)">Продать 500 металла</button>
    <button class="btn" onclick="sell('oil', 300)">Продать 300 нефти</button>
  `);
}

async function sell(res, amount) {
  const my = getMy();
  const r = await api('/api/sell', {cid: my.id, res, amount});
  if (r.error === 'not_yours') return toast('Ошибка владельца. Перезайди в игру.', 'error');
  if (r.error === 'not_enough') return toast('Недостаточно ресурса', 'error');
  if (r.error) return toast(r.error, 'error');
  toast(`+${fmt(r.money)}`, 'success');
  await loadState();
  openTrade();
}

function openTop() {
  const sorted = [...state.countries].sort((a, b) => b.treas - a.treas).slice(0, 10);
  openModal('Топ стран', sorted.map((c, i) => {
    const m = i === 0 ? '1' : i === 1 ? '2' : i === 2 ? '3' : `${i+1}`;
    return `<div class="row"><div style="width:38px;text-align:center;font-weight:700;font-size:16px;color:${i<3?'var(--gold)':'var(--dim)'}">${m}</div><div class="flag-circle">${c.flag}</div><div class="row-info"><div class="row-title">${c.name}</div><div class="row-sub">${c.provinces.length} провинций</div></div><div style="font-weight:700;color:var(--gold)">${fmt(c.treas)}</div></div>`;
  }).join(''));
}

function renderNews() {
  document.getElementById('newsContent').innerHTML = state.news.length === 0
    ? '<div class="card"><div class="empty">Пока пусто</div></div>'
    : '<div class="card">' + state.news.slice(0, 20).map(n => `<div style="padding:14px 16px;border-bottom:.5px solid var(--line);font-size:14px;line-height:1.5">${n.text}</div>`).join('') + '</div>';
}

function openSettings() {
  const theme = localStorage.getItem('rp_theme') || 'dark';
  openModal('Настройки', `
    <div class="row">
      <div class="row-icon">${ICONS.wall}</div>
      <div class="row-info"><div class="row-title">Тёмная тема</div></div>
      <div class="toggle ${theme === 'dark' ? 'on' : ''}" onclick="toggleTheme(this)"></div>
    </div>
    <div class="row">
      <div class="row-icon">${ICONS.people}</div>
      <div class="row-info"><div class="row-title">Вибрация</div></div>
      <div class="toggle on" onclick="this.classList.toggle('on')"></div>
    </div>
    <div style="padding:16px;font-size:12px;color:var(--dim);text-align:center;line-height:1.6">
      Твой ID: <b style="color:var(--text)">${UID}</b><br>
      Если кнопки не работают — перезайди в игру.
    </div>
  `);
}

function toggleTheme(el) {
  el.classList.toggle('on');
  const isDark = el.classList.contains('on');
  document.body.classList.toggle('theme-light', !isDark);
  localStorage.setItem('rp_theme', isDark ? 'dark' : 'light');
}

function openModal(t, b) {
  document.getElementById('modalTitle').textContent = t;
  document.getElementById('modalBody').innerHTML = b;
  document.getElementById('modal').classList.add('open');
  if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
}

function closeModal() { document.getElementById('modal').classList.remove('open'); }
document.getElementById('modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });

document.querySelectorAll('.tab-item').forEach(el => {
  el.onclick = () => {
    document.querySelectorAll('.tab-item').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(x => x.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-' + el.dataset.tab).classList.add('active');
    document.getElementById('pageTitle').textContent = el.dataset.title;
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
  };
});

if (localStorage.getItem('rp_theme') === 'light') document.body.classList.add('theme-light');

loadState();
setInterval(loadState, 5000);
</script>
</body>
</html>'''


# ============================================================
# API
# ============================================================
@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/api/state')
def api_state():
    uid = request.args.get('uid', type=int)
    return jsonify({
        'countries': list(data['countries'].values()),
        'news': data['news'][:20],
        'alliances': data.get('alliances', []),
        'wars': data.get('wars', []),
        'my_country_id': next((c['id'] for c in data['countries'].values() if c.get('owner') == uid), None),
        'buildings': BUILDINGS,
        'province_types': PROVINCE_TYPES,
    })


@app.route('/api/take', methods=['POST'])
def api_take():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    if not uid or cid not in data['countries']:
        return jsonify({'error': 'bad request'}), 400
    existing = next((c for c in data['countries'].values() if c.get('owner') == uid), None)
    if existing:
        return jsonify({'error': 'already_have'}), 400
    c = data['countries'][cid]
    if c.get('owner'):
        return jsonify({'error': 'taken'}), 400
    c['owner'] = uid
    c['isNpc'] = False
    add_news(f'{c["flag"]} {c["name"]}: новый правитель!')
    save_data()
    return jsonify({'ok': True})


@app.route('/api/build', methods=['POST'])
def api_build():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    prov_idx = d.get('prov_idx', 0)
    bkey = d.get('bkey')
    if not uid or cid not in data['countries'] or bkey not in BUILDINGS:
        return jsonify({'error': 'bad request'}), 400
    c = data['countries'][cid]
    if c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    if prov_idx >= len(c['provinces']):
        return jsonify({'error': 'no_prov'}), 400
    b = BUILDINGS[bkey]
    if c['treas'] < b['cost']:
        return jsonify({'error': 'no_money', 'need': b['cost'] - int(c['treas'])}), 400
    c['treas'] -= b['cost']
    p = c['provinces'][prov_idx]
    p.setdefault('buildings', {})
    p['buildings'][bkey] = p['buildings'].get(bkey, 0) + 1
    save_data()
    return jsonify({'ok': True})


@app.route('/api/recruit', methods=['POST'])
def api_recruit():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    amount = int(d.get('amount', 0))
    c = data['countries'].get(cid)
    if not c or c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    cost = amount * 2
    if c['treas'] < cost:
        return jsonify({'error': 'no_money', 'need': cost - int(c['treas'])}), 400
    c['treas'] -= cost
    c['army'] += amount
    save_data()
    return jsonify({'ok': True})


@app.route('/api/sell', methods=['POST'])
def api_sell():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    res = d.get('res')
    amount = int(d.get('amount', 0))
    c = data['countries'].get(cid)
    if not c or c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    prices = {'food': 1, 'metal': 3, 'oil': 5}
    if res not in prices:
        return jsonify({'error': 'bad_res'}), 400
    if c[res] < amount:
        return jsonify({'error': 'not_enough'}), 400
    c[res] -= amount
    money = amount * prices[res]
    c['treas'] += money
    save_data()
    return jsonify({'ok': True, 'money': money})


@app.route('/api/ally', methods=['POST'])
def api_ally():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    target = str(d.get('target'))
    c = data['countries'].get(cid)
    t = data['countries'].get(target)
    if not c or not t or c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    if not t.get('owner'):
        return jsonify({'error': 'NPC не принимает союзы'}), 400
    if is_at_war(cid, target):
        return jsonify({'error': 'Вы в войне'}), 400
    if find_alliance(cid, target):
        return jsonify({'error': 'Уже союз'}), 400
    data.setdefault('alliances', []).append({'members': [cid, target], 'time': int(time.time())})
    add_news(f'Союз: {c["flag"]} {c["name"]} и {t["flag"]} {t["name"]}')
    save_data()
    return jsonify({'ok': True})


@app.route('/api/war', methods=['POST'])
def api_war():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    target = str(d.get('target'))
    c = data['countries'].get(cid)
    t = data['countries'].get(target)
    if not c or not t or c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    if find_alliance(cid, target):
        return jsonify({'error': 'Нельзя атаковать союзника'}), 400
    if is_at_war(cid, target):
        return jsonify({'error': 'Уже в войне'}), 400
    data.setdefault('wars', []).append({'attacker': cid, 'defender': target, 'turns': 0, 'time': int(time.time())})
    add_news(f'{c["flag"]} {c["name"]} объявил войну {t["flag"]} {t["name"]}!')
    save_data()
    return jsonify({'ok': True})


@app.route('/health')
def health():
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('RP server started (iOS-style, SVG icons)')
    app.run(host='0.0.0.0', port=port)
