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

# ============================================================
# ЗДАНИЯ
# ============================================================
BUILDINGS = {
    'farm':     {'name': '🌾 Ферма',      'cost': 300,  'desc': '+200 еды/мин',       'effect': {'food': 200}},
    'factory':  {'name': '🏭 Завод',      'cost': 800,  'desc': '+500💰/мин, -1 стаб.', 'effect': {'treasury': 500, 'stability': -1}},
    'barracks': {'name': '⚔️ Казармы',    'cost': 500,  'desc': '+100 армии/мин',      'effect': {'army': 100}},
    'school':   {'name': '🎓 Школа',      'cost': 1000, 'desc': '+0.5 тех./мин',       'effect': {'tech': 0.5}},
    'hospital': {'name': '🏥 Больница',   'cost': 700,  'desc': '+2 стаб./мин',        'effect': {'stability': 2}},
    'police':   {'name': '🚔 Полиция',    'cost': 400,  'desc': '+1 стаб./мин',        'effect': {'stability': 1}},
    'mine':     {'name': '⛏️ Шахта',      'cost': 600,  'desc': '+150 металла/мин',    'effect': {'metal': 150}},
    'oilrig':   {'name': '🛢️ Нефтевышка', 'cost': 900,  'desc': '+100 нефти/мин',      'effect': {'oil': 100}},
    'market':   {'name': '🏪 Рынок',      'cost': 700,  'desc': '+300💰/мин',          'effect': {'treasury': 300}},
    'bank':     {'name': '🏦 Банк',       'cost': 1500, 'desc': '+800💰/мин',          'effect': {'treasury': 800, 'income_bonus': 0.1}},
    'wall':     {'name': '🛡️ Стена',      'cost': 1200, 'desc': '+30% защиты',         'effect': {'defense': 0.3}},
    'port':     {'name': '⚓ Порт',       'cost': 1000, 'desc': '+200💰/+100 еды',     'effect': {'treasury': 200, 'food': 100}},
}

# ============================================================
# ТИПЫ ПРОВИНЦИЙ
# ============================================================
PROVINCE_TYPES = {
    'plain':    {'name': '🌾 Равнина',   'bonus': {'food': 500},    'desc': 'Много еды'},
    'forest':   {'name': '🌲 Лес',       'bonus': {'food': 200, 'metal': 100}, 'desc': 'Еда + металл'},
    'mountain': {'name': '⛰️ Горы',      'bonus': {'metal': 400},   'desc': 'Много металла'},
    'desert':   {'name': '🏜️ Пустыня',   'bonus': {'oil': 300},     'desc': 'Нефть'},
    'coast':    {'name': '🌊 Побережье', 'bonus': {'treasury': 400},'desc': 'Торговля'},
    'city':     {'name': '🏙️ Город',     'bonus': {'treasury': 600, 'pop': 5000}, 'desc': 'Экономика'},
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


def make_provinces(country_name, pop):
    """Создаёт 5 провинций для страны с разными типами."""
    types_pool = ['plain', 'forest', 'mountain', 'desert', 'coast', 'city']
    random.shuffle(types_pool)
    provinces = []
    for i in range(5):
        t = types_pool[i % len(types_pool)]
        provinces.append({
            'id': i,
            'name': f'Провинция {i+1}',
            'type': t,
            'pop': pop // 6,
            'buildings': {},
            'stability': 70,
        })
    return provinces


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
            'provinces': make_provinces(c['name'], c['pop']),
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


def get_my(uid):
    for c in data['countries'].values():
        if c.get('owner') == uid:
            return c
    return None


def get_country_by_id(cid):
    return data['countries'].get(str(cid))


def fmt(n):
    n = int(n)
    if n >= 1e9: return f'{n/1e9:.1f} млрд'
    if n >= 1e6: return f'{n/1e6:.1f} млн'
    if n >= 1e3: return f'{n/1e3:.1f} тыс'
    return str(n)


def province_income(prov, country):
    """Доход провинции за минуту."""
    inc = prov['pop'] * 0.0001 + 20
    # Бонус от типа
    t = prov.get('type', 'plain')
    if t in PROVINCE_TYPES:
        inc += PROVINCE_TYPES[t]['bonus'].get('treasury', 0)
    # Бонус от зданий
    b = prov.get('buildings', {})
    ib = 0
    for k, cnt in b.items():
        if k in BUILDINGS:
            eff = BUILDINGS[k].get('effect', {})
            inc += eff.get('treasury', 0) * cnt
            ib += eff.get('income_bonus', 0) * cnt
    inc *= (1 + country['tech'] * 0.05)
    inc *= (1 + ib)
    inc *= (1 + country.get('bonus', 0))
    return inc


def country_income(c):
    total = 0
    for p in c['provinces']:
        total += province_income(p, c)
    return total


def find_alliance(cid1, cid2):
    for a in data.get('alliances', []):
        if str(cid1) in a['members'] and str(cid2) in a['members']:
            return a
    return None


def is_at_war(cid1, cid2):
    for w in data.get('wars', []):
        if (w['attacker'] == str(cid1) and w['defender'] == str(cid2)) or \
           (w['attacker'] == str(cid2) and w['defender'] == str(cid1)):
            return True
    return False


# ============================================================
# ТИК
# ============================================================
def tick():
    for c in data['countries'].values():
        income = country_income(c)
        expense = c['army'] * 0.05
        c['treas'] += income - expense
        if c['treas'] < 0:
            c['treas'] = 0
            c['stability'] -= 2

        # Ресурсы и бонусы
        for p in c['provinces']:
            t = p.get('type', 'plain')
            if t in PROVINCE_TYPES:
                bonus = PROVINCE_TYPES[t]['bonus']
                c['food'] += bonus.get('food', 0)
                c['metal'] += bonus.get('metal', 0)
                c['oil'] += bonus.get('oil', 0)
                p['pop'] += bonus.get('pop', 0)

            b = p.get('buildings', {})
            for k, cnt in b.items():
                if k not in BUILDINGS: continue
                eff = BUILDINGS[k].get('effect', {})
                c['food'] += eff.get('food', 0) * cnt
                c['metal'] += eff.get('metal', 0) * cnt
                c['oil'] += eff.get('oil', 0) * cnt
                c['army'] += eff.get('army', 0) * cnt
                c['tech'] += eff.get('tech', 0) * cnt
                c['stability'] += eff.get('stability', 0) * cnt

        c['stability'] = max(0, min(100, c['stability']))

        # Рост населения
        if c['food'] > c['pop'] / 500:
            growth = int((c['food'] / 500) * (c['stability'] / 100))
            c['pop'] += growth
            c['food'] -= growth * 5
            # Распределяем по провинциям
            if c['provinces']:
                per = growth // len(c['provinces'])
                for p in c['provinces']:
                    p['pop'] += per

        # NPC
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
    if c['treas'] > 600 and c['army'] < 500000: actions.append('barracks')
    if c['stability'] < 50: actions.append('police')
    if c['treas'] > 900: actions.append('mine')
    if c['treas'] > 2000: actions.append('wall')
    if not actions: return
    bkey = random.choice(actions)
    cost = BUILDINGS[bkey]['cost']
    if c['treas'] >= cost:
        c['treas'] -= cost
        prov = random.choice(c['provinces'])
        prov.setdefault('buildings', {})
        prov['buildings'][bkey] = prov['buildings'].get(bkey, 0) + 1


def process_wars():
    finished = []
    for w in data.get('wars', []):
        w['turns'] = w.get('turns', 0) + 1
        a = get_country_by_id(w['attacker'])
        d = get_country_by_id(w['defender'])
        if not a or not d:
            finished.append(w); continue

        a_power = a['army'] * (1 + a['tech'] * 0.1) * (a['stability'] / 100)
        d_power = d['army'] * (1 + d['tech'] * 0.1) * (d['stability'] / 100)

        # Защита от стен
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

        # Проверяем конец войны
        if a['army'] < a['pop'] * 0.0001 or d['army'] < d['pop'] * 0.0001 or w['turns'] >= 10:
            winner, loser = (a, d) if a_power > d_power else (d, a)
            loot = int(loser['treas'] * 0.3)
            winner['treas'] += loot
            loser['treas'] -= loot

            # Забираем провинцию
            if loser['provinces'] and winner['provinces']:
                captured = loser['provinces'].pop(0)
                winner['provinces'].append(captured)
                cap_msg = f' и захватил провинцию «{captured["name"]}»'
            else:
                cap_msg = ''

            add_news(f'🏆 Война {a["flag"]} {a["name"]} vs {d["flag"]} {d["name"]} окончена! Победил {winner["flag"]} {winner["name"]}, забрал {fmt(loot)}💰{cap_msg}')
            finished.append(w)

    for w in finished:
        data['wars'].remove(w)


def random_event():
    events = [
        ('🌋 Извержение вулкана в {name}!', lambda c: (c.update({'stability': max(0, c['stability'] - 15)}), c.update({'pop': int(c['pop'] * 0.95)}))),
        ('💎 Найдено золото в {name}!', lambda c: c.update({'treas': c['treas'] + 3000})),
        ('🌾 Урожай в {name}!', lambda c: c.update({'food': c['food'] + 5000})),
        ('⚔️ Бунт в {name}!', lambda c: c.update({'stability': max(0, c['stability'] - 20)})),
        ('🎉 Бум в {name}!', lambda c: c.update({'treas': c['treas'] + 5000})),
        ('🦠 Эпидемия в {name}!', lambda c: c.update({'pop': int(c['pop'] * 0.93), 'stability': max(0, c['stability'] - 10)})),
    ]
    ev_text, action = random.choice(events)
    c = random.choice(list(data['countries'].values()))
    try:
        action(c)
        add_news(ev_text.format(name=f'{c["flag"]} {c["name"]}'))
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
# HTML
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
:root{--bg:#000;--card:#1c1c1e;--card-2:#2c2c2e;--line:#38383a;--text:#fff;--dim:#98989f;--muted:#636366;--accent:#bf5af2;--accent-2:#5e5ce6;--green:#30d158;--red:#ff453a;--gold:#ffd60a;--blue:#0a84ff;--radius:14px}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.4;padding-bottom:20px;letter-spacing:-.3px}
.header{background:rgba(0,0,0,0.75);backdrop-filter:saturate(180%) blur(30px);border-bottom:.5px solid var(--line);position:sticky;top:0;z-index:50;padding:10px 16px;padding-top:calc(10px + env(safe-area-inset-top));display:flex;justify-content:space-between;align-items:center}
.logo{font-size:17px;font-weight:700;background:linear-gradient(90deg,var(--accent),var(--accent-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.badge{font-size:13px;font-weight:600;color:var(--accent-2);background:rgba(191,90,242,0.12);border:1px solid rgba(191,90,242,0.25);padding:5px 10px;border-radius:20px}
.container{padding:16px;max-width:540px;margin:0 auto}
.card{background:var(--card);border-radius:var(--radius);margin-bottom:14px;overflow:hidden}
.card-title{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;padding:14px 16px 8px}
.btn{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border:none;border-radius:12px;padding:14px 18px;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer;width:100%;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn:active{transform:scale(.98);opacity:.85}
.btn.secondary{background:var(--card-2);color:var(--text)}
.btn.small{padding:8px 12px;font-size:14px;margin:0;width:auto}
.btn.danger{background:linear-gradient(135deg,#ff453a,#ff375f)}
.btn:disabled{opacity:.4}
.row{display:flex;align-items:center;gap:12px;padding:13px 16px;border-top:.5px solid var(--line);cursor:pointer}
.row:active{background:var(--card-2)}
.row:first-child{border-top:none}
.row-icon{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.row-info{flex:1;min-width:0}
.row-title{font-size:15px;font-weight:600}
.row-sub{font-size:12px;color:var(--dim);margin-top:2px}
.row-chev{color:var(--muted);font-size:20px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat{background:var(--card);border-radius:var(--radius);padding:14px}
.stat-k{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.6px;font-weight:600}
.stat-v{font-size:20px;font-weight:700;margin-top:4px}
.stat-v.gold{color:var(--gold)}
.stat-v.green{color:var(--green)}
.stat-v.purple{color:var(--accent-2)}
.stat-v.blue{color:var(--blue)}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;display:none;align-items:flex-end;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--card);border-radius:20px 20px 0 0;width:100%;max-width:540px;max-height:85vh;overflow-y:auto;padding-bottom:20px}
.modal-header{display:flex;justify-content:space-between;align-items:center;padding:18px 20px;border-bottom:.5px solid var(--line)}
.modal-title{font-size:18px;font-weight:700}
.modal-close{background:var(--card-2);border:none;width:30px;height:30px;border-radius:15px;cursor:pointer;color:var(--text);font-size:16px}
.modal-body{padding:16px 20px}
.empty{text-align:center;padding:40px 20px;color:var(--muted);font-size:14px}
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(120%);background:rgba(44,44,46,0.96);color:#fff;padding:12px 20px;border-radius:14px;font-size:14px;z-index:999;opacity:0;transition:.25s;max-width:90vw;text-align:center}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.error{background:rgba(255,69,58,0.96)}
.toast.success{background:rgba(48,209,88,0.96)}
.loader{width:24px;height:24px;border:2px solid var(--card-2);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;margin:40px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.building-row{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:.5px solid var(--line)}
.building-row:last-child{border:none}
.building-name{font-size:15px;font-weight:600}
.building-desc{font-size:12px;color:var(--dim);margin-top:2px}
.building-cost{font-size:14px;font-weight:700;color:var(--gold);margin-right:10px}
.war-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;background:rgba(255,69,58,0.2);color:var(--red);margin-left:4px}
.ally-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;background:rgba(48,209,88,0.2);color:var(--green);margin-left:4px}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🏛️ RP Countries</div>
  <div class="badge" id="headerBadge">—</div>
</div>
<div class="container" id="app"><div class="loader"></div></div>
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
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }
const UID = tg?.initDataUnsafe?.user?.id || 0;
let state = null;
async function api(path, body) {
  try {
    const r = await fetch(path, {method: body ? 'POST' : 'GET', headers: {'Content-Type': 'application/json'}, body: body ? JSON.stringify({uid: UID, ...body}) : undefined});
    return await r.json();
  } catch(e) { return {error: 'network'}; }
}
function toast(msg, type='') {
  const el = document.getElementById('toast');
  el.textContent = msg; el.className = 'toast ' + type; el.classList.add('show');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('show'), 2500);
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
  state = r; render();
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
  let ib = 0;
  for (const [k, cnt] of Object.entries(b)) {
    if (!state.buildings[k]) continue;
    const eff = state.buildings[k].effect || {};
    inc += (eff.treasury || 0) * cnt;
    ib += (eff.income_bonus || 0) * cnt;
  }
  inc *= (1 + c.tech * 0.05) * (1 + ib) * (1 + (c.bonus || 0));
  return inc;
}
function countryIncome(c) {
  let t = 0;
  for (const p of c.provinces) t += provIncome(p, c);
  return t;
}
function render() {
  const app = document.getElementById('app');
  const my = getMy();
  document.getElementById('headerBadge').textContent = my ? `${my.flag} ${fmt(my.treas)}💰` : '🌍 Выбор';
  if (!my) return renderChoose();
  const income = countryIncome(my);
  const expense = my.army * 0.05;
  const totalB = my.provinces.reduce((s, p) => s + Object.values(p.buildings || {}).reduce((a,b)=>a+b,0), 0);
  const myAlliances = state.alliances.filter(a => a.members.includes(String(my.id)));
  const myWars = state.wars.filter(w => w.attacker === String(my.id) || w.defender === String(my.id));

  app.innerHTML = `
    <div class="card" style="background:linear-gradient(135deg,rgba(191,90,242,0.15),rgba(94,92,230,0.05));border:1px solid rgba(191,90,242,0.25)">
      <div style="padding:18px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
          <div style="font-size:42px">${my.flag}</div>
          <div style="flex:1">
            <div style="font-size:20px;font-weight:700">${my.name}</div>
            <div style="font-size:12px;color:var(--dim);margin-top:2px">
              ${myWars.length ? '<span class="war-badge">⚔️ ВОЙНА</span>' : ''}
              ${myAlliances.length ? '<span class="ally-badge">🤝 '+myAlliances.length+'</span>' : ''}
            </div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--dim);text-transform:uppercase;font-weight:600">Казна</div>
        <div style="font-size:34px;font-weight:800;color:var(--gold);line-height:1.1;margin-top:4px">${fmt(my.treas)} 💰</div>
        <div style="font-size:13px;color:var(--green);margin-top:6px">+${fmt(income)} / -${fmt(expense)} = <b style="color:var(--text)">${fmt(income-expense)}💰/мин</b></div>
      </div>
    </div>
    <div class="grid2">
      <div class="stat"><div class="stat-k">👥 Население</div><div class="stat-v">${fmt(my.pop)}</div></div>
      <div class="stat"><div class="stat-k">⚔️ Армия</div><div class="stat-v">${fmt(my.army)}</div></div>
      <div class="stat"><div class="stat-k">🔬 Технологии</div><div class="stat-v purple">${Math.floor(my.tech)}</div></div>
      <div class="stat"><div class="stat-k">📊 Стабильность</div><div class="stat-v green">${Math.floor(my.stability)}%</div></div>
      <div class="stat"><div class="stat-k">🌾 Еда</div><div class="stat-v">${fmt(my.food)}</div></div>
      <div class="stat"><div class="stat-k">⛏️ Металл</div><div class="stat-v">${fmt(my.metal)}</div></div>
      <div class="stat"><div class="stat-k">🛢️ Нефть</div><div class="stat-v">${fmt(my.oil)}</div></div>
      <div class="stat"><div class="stat-k">🗺️ Провинций</div><div class="stat-v blue">${my.provinces.length}</div></div>
    </div>
    <button class="btn" onclick="openProvinces()">🗺️ Провинции (${my.provinces.length})</button>
    <div class="grid2">
      <button class="btn secondary" style="margin-bottom:0" onclick="openArmy()">⚔️ Армия</button>
      <button class="btn secondary" style="margin-bottom:0" onclick="openDiplomacy()">🤝 Дипломатия</button>
    </div>
    <div class="grid2">
      <button class="btn secondary" style="margin-bottom:0" onclick="openWars()">⚔️ Войны</button>
      <button class="btn secondary" style="margin-bottom:0" onclick="openTrade()">🛒 Торговля</button>
    </div>
    <button class="btn secondary" onclick="openNews()">📰 Новости</button>
    <button class="btn secondary" onclick="openTop()">🏆 Топ стран</button>
    <button class="btn secondary" onclick="openAll()">🌍 Все страны</button>
  `;
}
function renderChoose() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div style="text-align:center;padding:30px 0 20px">
      <div style="font-size:64px;margin-bottom:10px">🏛️</div>
      <div style="font-size:22px;font-weight:700;margin-bottom:6px">Выбери страну</div>
      <div style="font-size:14px;color:var(--dim)">⚠️ Выбор — навсегда!</div>
    </div>
    <div class="card">
      ${state.countries.map(c => `
        <div class="row" onclick="${c.owner ? '' : `takeCountry(${c.id})`}">
          <div class="row-icon">${c.flag}</div>
          <div class="row-info">
            <div class="row-title">${c.name}</div>
            <div class="row-sub">${fmt(c.pop)} чел · ${fmt(c.treas)}💰 · ${c.provinces.length} пров.</div>
          </div>
          <div class="row-chev">${c.owner ? '🔒' : '›'}</div>
        </div>
      `).join('')}
    </div>
  `;
}
async function takeCountry(cid) {
  if (!confirm('Выбрать эту страну? Поменять нельзя!')) return;
  const r = await api('/api/take', {cid});
  if (r.error === 'taken') return toast('🔒 Занята', 'error');
  if (r.error === 'already_have') return toast('Уже есть страна', 'error');
  if (r.ok) { toast('✅ Страна твоя!', 'success'); loadState(); }
}
function openProvinces() {
  const my = getMy();
  openModal('🗺️ Провинции', my.provinces.map((p, i) => {
    const t = state.province_types[p.type] || {name: '❓', desc: ''};
    const inc = provIncome(p, my);
    return `
      <div class="row" onclick="openProvince(${i})">
        <div class="row-icon" style="font-size:16px">${t.name.split(' ')[0]}</div>
        <div class="row-info">
          <div class="row-title">${p.name} <span style="color:var(--dim);font-weight:400">${t.name.split(' ').slice(1).join(' ')}</span></div>
          <div class="row-sub">${fmt(p.pop)} чел · +${fmt(inc)}💰/мин</div>
        </div>
        <div class="row-chev">›</div>
      </div>
    `;
  }).join(''));
}
function openProvince(i) {
  const my = getMy();
  const p = my.provinces[i];
  const t = state.province_types[p.type] || {name:'❓',desc:''};
  const b = p.buildings || {};
  const rows = Object.entries(b).map(([k, cnt]) =>
    `<div class="building-row"><div class="building-name">${state.buildings[k]?.name || k}</div><div style="font-weight:700">×${cnt}</div></div>`
  ).join('');
  openModal(`🗺️ ${p.name}`, `
    <div style="font-size:14px;color:var(--dim);margin-bottom:12px">${t.name} — ${t.desc}</div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Население</span><b>${fmt(p.pop)}</b>
    </div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Доход</span><b style="color:var(--gold)">${fmt(provIncome(p, my))}💰/мин</b>
    </div>
    <div class="card-title">Здания</div>
    ${rows || '<div class="empty">Пока пусто</div>'}
    <button class="btn" style="margin-top:14px" onclick="closeModal();openBuildMenu(${i})">🏗️ Построить</button>
  `);
}
function openBuildMenu(idx) {
  const my = getMy();
  openModal('🏗️ Строительство', `
    <div style="font-size:13px;color:var(--dim);margin-bottom:12px">Провинция: <b style="color:var(--text)">${my.provinces[idx].name}</b></div>
    <div style="font-size:13px;color:var(--dim);margin-bottom:12px">Казна: <b style="color:var(--gold)">${fmt(my.treas)}💰</b></div>
    ${Object.entries(state.buildings).map(([k, b]) => `
      <div class="building-row">
        <div>
          <div class="building-name">${b.name}</div>
          <div class="building-desc">${b.desc}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="building-cost">${b.cost}💰</div>
          <button class="btn small" onclick="buildIn(${idx},'${k}')" ${my.treas < b.cost ? 'disabled' : ''}>+</button>
        </div>
      </div>
    `).join('')}
  `);
}
async function buildIn(idx, bkey) {
  const my = getMy();
  const r = await api('/api/build', {cid: my.id, prov_idx: idx, bkey});
  if (r.error === 'no_money') return toast(`Не хватает ${r.need}💰`, 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast('✅ Построено', 'success');
  await loadState();
  openBuildMenu(idx);
}
async function openArmy() {
  const my = getMy();
  openModal('⚔️ Армия', `
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Солдат</span><b>${fmt(my.army)}</b>
    </div>
    <div style="display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--line)">
      <span style="color:var(--dim)">Казна</span><b style="color:var(--gold)">${fmt(my.treas)}💰</b>
    </div>
    <div style="font-size:13px;color:var(--dim);margin:12px 0">Найм: 1 солдат = 2💰</div>
    <button class="btn" onclick="recruit(1000)">+1 000</button>
    <button class="btn" onclick="recruit(5000)">+5 000</button>
    <button class="btn" onclick="recruit(10000)">+10 000</button>
  `);
}
async function recruit(n) {
  const my = getMy();
  const r = await api('/api/recruit', {cid: my.id, amount: n});
  if (r.error === 'no_money') return toast(`Нужно ${fmt(r.need)}💰`, 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast(`✅ +${fmt(n)} солдат`, 'success');
  await loadState();
  openArmy();
}
function openDiplomacy() {
  const my = getMy();
  const others = state.countries.filter(c => c.id !== my.id);
  openModal('🤝 Дипломатия', `
    <div class="card-title">Твои союзы</div>
    ${state.alliances.filter(a => a.members.includes(String(my.id))).map(a => {
      const allies = a.members.filter(m => m !== String(my.id)).map(m => state.countries.find(c => c.id === parseInt(m)));
      return `<div style="padding:10px 0;border-bottom:.5px solid var(--line);font-size:14px">🤝 ${allies.map(c => c?.flag + ' ' + c?.name).join(', ')}</div>`;
    }).join('') || '<div class="empty">Пока нет союзов</div>'}
    <div class="card-title">Предложить союз</div>
    ${others.map(c => `
      <div class="row" onclick="${c.owner ? `offerAlly(${c.id})` : ''}">
        <div class="row-icon">${c.flag}</div>
        <div class="row-info">
          <div class="row-title">${c.name}</div>
          <div class="row-sub">${c.owner ? '👤 Игрок' : '🤖 NPC'}</div>
        </div>
        <div class="row-chev">›</div>
      </div>
    `).join('')}
  `);
}
async function offerAlly(cid) {
  const my = getMy();
  const r = await api('/api/ally', {cid: my.id, target: cid});
  if (r.error) return toast(r.error, 'error');
  toast('🤝 Союз предложен', 'success');
  await loadState();
  openDiplomacy();
}
function openWars() {
  const my = getMy();
  const myWars = state.wars.filter(w => w.attacker === String(my.id) || w.defender === String(my.id));
  const others = state.countries.filter(c => c.id !== my.id);
  openModal('⚔️ Войны', `
    ${myWars.length ? '<div class="card-title">Активные войны</div>' + myWars.map(w => {
      const a = state.countries.find(c => c.id === parseInt(w.attacker));
      const d = state.countries.find(c => c.id === parseInt(w.defender));
      return `<div style="padding:12px 0;border-bottom:.5px solid var(--line)">${a?.flag} ${a?.name} ⚔️ ${d?.flag} ${d?.name}</div>`;
    }).join('') : ''}
    <div class="card-title">Объявить войну</div>
    ${others.map(c => `
      <div class="row" onclick="declareWar(${c.id})">
        <div class="row-icon">${c.flag}</div>
        <div class="row-info">
          <div class="row-title">${c.name}</div>
          <div class="row-sub">${fmt(c.army)}⚔️ · ${fmt(c.treas)}💰</div>
        </div>
        <div class="row-chev" style="color:var(--red)">⚔️</div>
      </div>
    `).join('')}
  `);
}
async function declareWar(cid) {
  if (!confirm('Объявить войну?')) return;
  const my = getMy();
  const r = await api('/api/war', {cid: my.id, target: cid});
  if (r.error) return toast(r.error, 'error');
  toast('⚔️ Война объявлена!', 'success');
  await loadState();
  openWars();
}
function openTrade() {
  const my = getMy();
  openModal('🛒 Торговля', `
    <div class="card-title">Продать ресурсы</div>
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>🌾 Еда: ${fmt(my.food)}</span><span>1💰/шт</span></div>
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>⛏️ Металл: ${fmt(my.metal)}</span><span>3💰/шт</span></div>
    <div style="display:flex;justify-content:space-between;padding:10px 0"><span>🛢️ Нефть: ${fmt(my.oil)}</span><span>5💰/шт</span></div>
    <button class="btn" onclick="sell('food', 1000)">Продать 1000 еды</button>
    <button class="btn" onclick="sell('metal', 500)">Продать 500 металла</button>
    <button class="btn" onclick="sell('oil', 300)">Продать 300 нефти</button>
  `);
}
async function sell(res, amount) {
  const my = getMy();
  const r = await api('/api/sell', {cid: my.id, res, amount});
  if (r.error) return toast(r.error, 'error');
  toast(`✅ +${fmt(r.money)}💰`, 'success');
  await loadState();
  openTrade();
}
function openNews() {
  openModal('📰 Новости', state.news.length === 0
    ? '<div class="empty">Пока пусто</div>'
    : state.news.map(n => `<div style="padding:10px 0;border-bottom:.5px solid var(--line);font-size:14px">${n.text}</div>`).join('')
  );
}
function openTop() {
  const sorted = [...state.countries].sort((a, b) => b.treas - a.treas).slice(0, 10);
  openModal('🏆 Топ стран', sorted.map((c, i) => {
    const m = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}.`;
    return `<div class="row"><div style="width:34px;text-align:center;font-weight:700">${m}</div><div class="row-info"><div class="row-title">${c.flag} ${c.name}</div><div class="row-sub">${c.provinces.length} пров.</div></div><div style="font-weight:700;color:var(--gold)">${fmt(c.treas)}💰</div></div>`;
  }).join(''));
}
function openAll() {
  openModal('🌍 Все страны', state.countries.map(c =>
    `<div class="row"><div class="row-icon">${c.flag}</div><div class="row-info"><div class="row-title">${c.name}</div><div class="row-sub">${c.owner ? '👤 Занята' : '🟢 Свободна'} · ${c.provinces.length} пров.</div></div></div>`
  ).join(''));
}
function openModal(t, b) {
  document.getElementById('modalTitle').textContent = t;
  document.getElementById('modalBody').innerHTML = b;
  document.getElementById('modal').classList.add('open');
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }
document.getElementById('modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });
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
    add_news(f'🤝 {c["flag"]} {c["name"]} и {t["flag"]} {t["name"]} заключили союз')
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
    add_news(f'⚔️ {c["flag"]} {c["name"]} объявил войну {t["flag"]} {t["name"]}!')
    save_data()
    return jsonify({'ok': True})


@app.route('/health')
def health():
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('RP server started with provinces, alliances, wars')
    app.run(host='0.0.0.0', port=port)
