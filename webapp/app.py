import json
import os
import time
import random
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
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
    d = {'countries': {}, 'news': [], 'last_tick': int(time.time())}
    for i, c in enumerate(COUNTRIES_25):
        d['countries'][str(i)] = {
            'id': i, 'name': c['name'], 'flag': c['flag'],
            'owner': None, 'pop': c['pop'], 'treas': c['treas'],
            'army': c['army'], 'tech': c['tech'], 'stability': 70,
            'food': 5000, 'metal': 2000, 'oil': 1000,
            'isNpc': True, 'cities': [],
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


# ============================================================
# HTML — ВНУТРИ ЭТОГО ЖЕ ФАЙЛА
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
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.4;padding-bottom:20px;letter-spacing:-.3px;-webkit-font-smoothing:antialiased}
.header{background:rgba(0,0,0,0.75);backdrop-filter:saturate(180%) blur(30px);-webkit-backdrop-filter:saturate(180%) blur(30px);border-bottom:.5px solid var(--line);position:sticky;top:0;z-index:50;padding:10px 16px;padding-top:calc(10px + env(safe-area-inset-top));display:flex;justify-content:space-between;align-items:center}
.logo{font-size:17px;font-weight:700;background:linear-gradient(90deg,var(--accent),var(--accent-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.badge{font-size:13px;font-weight:600;color:var(--accent-2);background:rgba(191,90,242,0.12);border:1px solid rgba(191,90,242,0.25);padding:5px 10px;border-radius:20px}
.container{padding:16px;max-width:540px;margin:0 auto}
.card{background:var(--card);border-radius:var(--radius);margin-bottom:14px;overflow:hidden}
.card-title{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;padding:14px 16px 8px}
.btn{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border:none;border-radius:12px;padding:14px 18px;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer;width:100%;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn:active{transform:scale(.98);opacity:.85}
.btn.secondary{background:var(--card-2);color:var(--text)}
.btn.small{padding:8px 12px;font-size:14px;margin:0;width:auto}
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
  el.textContent = msg;
  el.className = 'toast ' + type;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 2500);
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
function getMyCountry() {
  if (!state || state.my_country_id === null) return null;
  return state.countries.find(c => c.id === state.my_country_id);
}
function cityIncome(city) {
  let inc = city.pop * 0.0005 * 3600 + 50;
  const b = city.buildings || {};
  if (b.factory) inc += 300 * b.factory;
  return inc;
}
function countryIncome(c) {
  let t = 0;
  for (const city of c.cities) t += cityIncome(city);
  return t;
}
function render() {
  const app = document.getElementById('app');
  const my = getMyCountry();
  document.getElementById('headerBadge').textContent = my
    ? `${my.flag} ${fmt(my.treas)}💰`
    : '🌍 Выбор';
  if (!my) return renderChoose();
  const income = countryIncome(my);
  const totalB = my.cities.reduce((s, c) => s + Object.values(c.buildings || {}).reduce((a, b) => a + b, 0), 0);
  app.innerHTML = `
    <div class="card" style="background:linear-gradient(135deg,rgba(191,90,242,0.15),rgba(94,92,230,0.05));border:1px solid rgba(191,90,242,0.25)">
      <div style="padding:18px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
          <div style="font-size:42px">${my.flag}</div>
          <div>
            <div style="font-size:20px;font-weight:700">${my.name}</div>
            <div style="font-size:12px;color:var(--dim);margin-top:2px">Твоя страна</div>
          </div>
        </div>
        <div style="font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.8px;font-weight:600">Казна</div>
        <div style="font-size:34px;font-weight:800;color:var(--gold);line-height:1.1;margin-top:4px">${fmt(my.treas)} 💰</div>
        <div style="font-size:13px;color:var(--green);margin-top:6px">+${fmt(income)} 💰/час</div>
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
      <div class="stat"><div class="stat-k">🏙️ Города</div><div class="stat-v blue">${my.cities.length}</div></div>
    </div>
    <button class="btn" onclick="openBuildings()">🏗️ Строительство</button>
    <button class="btn secondary" onclick="openCities()">🏙️ Города</button>
    <button class="btn secondary" onclick="openNews()">📰 Новости</button>
    <button class="btn secondary" onclick="openTop()">🏆 Топ стран</button>
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
            <div class="row-sub">${fmt(c.pop)} чел · ${fmt(c.treas)}💰</div>
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
function openBuildings() {
  const my = getMyCountry();
  if (!my.cities.length) return toast('Нет городов', 'error');
  const city = my.cities[0];
  openModal('🏗️ Строительство', `
    <div style="font-size:13px;color:var(--dim);margin-bottom:12px">Город: <b style="color:var(--text)">${city.name}</b></div>
    <div style="font-size:13px;color:var(--dim);margin-bottom:12px">Казна: <b style="color:var(--gold)">${fmt(my.treas)}💰</b></div>
    ${Object.entries(state.buildings).map(([k, b]) => `
      <div class="building-row">
        <div>
          <div class="building-name">${b.name}</div>
          <div class="building-desc">${b.desc}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="building-cost">${b.cost}💰</div>
          <button class="btn small" onclick="buildIn(0,'${k}')" ${my.treas < b.cost ? 'disabled' : ''}>+</button>
        </div>
      </div>
    `).join('')}
  `);
}
async function buildIn(cityIdx, bkey) {
  const my = getMyCountry();
  const r = await api('/api/build', {cid: my.id, city_idx: cityIdx, bkey});
  if (r.error === 'no_money') return toast(`Не хватает ${r.need}💰`, 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast('✅ Построено', 'success');
  await loadState();
  openBuildings();
}
function openCities() {
  const my = getMyCountry();
  openModal('🏙️ Города', `
    ${my.cities.length === 0 ? '<div class="empty">Пока нет городов</div>' : ''}
    ${my.cities.map((city, i) => `
      <div class="row">
        <div class="row-icon">🏙️</div>
        <div class="row-info">
          <div class="row-title">${city.name}</div>
          <div class="row-sub">${fmt(city.pop)} чел · ${fmt(cityIncome(city))}💰/час</div>
        </div>
      </div>
    `).join('')}
    <button class="btn" style="margin-top:14px" onclick="foundCity()">➕ Основать город (5000💰)</button>
  `);
}
async function foundCity() {
  const my = getMyCountry();
  const r = await api('/api/found_city', {cid: my.id});
  if (r.error === 'no_money') return toast(`Нужно ${r.need}💰`, 'error');
  if (!r.ok) return toast('Ошибка', 'error');
  toast('✅ Город основан', 'success');
  await loadState();
  openCities();
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
    return `<div class="row"><div style="width:34px;text-align:center;font-weight:700">${m}</div><div class="row-info"><div class="row-title">${c.flag} ${c.name}</div></div><div style="font-weight:700;color:var(--gold)">${fmt(c.treas)}💰</div></div>`;
  }).join(''));
}
function openModal(t, b) {
  document.getElementById('modalTitle').textContent = t;
  document.getElementById('modalBody').innerHTML = b;
  document.getElementById('modal').classList.add('open');
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }
document.getElementById('modal').addEventListener('click', e => {
  if (e.target.id === 'modal') closeModal();
});
loadState();
setInterval(loadState, 5000);
</script>
</body>
</html>'''


@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/api/state')
def api_state():
    uid = request.args.get('uid', type=int)
    return jsonify({
        'countries': list(data['countries'].values()),
        'news': data['news'][:20],
        'my_country_id': next((c['id'] for c in data['countries'].values() if c.get('owner') == uid), None),
        'buildings': BUILDINGS,
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
    c['cities'].append({'name': 'Столица', 'pop': 500000, 'buildings': {}})
    add_news(f'{c["flag"]} {c["name"]}: новый правитель!')
    save_data()
    return jsonify({'ok': True})


@app.route('/api/build', methods=['POST'])
def api_build():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    city_idx = d.get('city_idx', 0)
    bkey = d.get('bkey')
    if not uid or cid not in data['countries'] or bkey not in BUILDINGS:
        return jsonify({'error': 'bad request'}), 400
    c = data['countries'][cid]
    if c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    b = BUILDINGS[bkey]
    if c['treas'] < b['cost']:
        return jsonify({'error': 'no_money', 'need': b['cost'] - int(c['treas'])}), 400
    c['treas'] -= b['cost']
    city = c['cities'][city_idx]
    city.setdefault('buildings', {})
    city['buildings'][bkey] = city['buildings'].get(bkey, 0) + 1
    save_data()
    return jsonify({'ok': True})


@app.route('/api/found_city', methods=['POST'])
def api_found_city():
    d = request.json or {}
    uid = d.get('uid')
    cid = str(d.get('cid'))
    if not uid or cid not in data['countries']:
        return jsonify({'error': 'bad request'}), 400
    c = data['countries'][cid]
    if c.get('owner') != uid:
        return jsonify({'error': 'not_yours'}), 403
    if c['treas'] < 5000:
        return jsonify({'error': 'no_money', 'need': 5000 - int(c['treas'])}), 400
    c['treas'] -= 5000
    name = f'Город-{len(c["cities"]) + 1}'
    c['cities'].append({'name': name, 'pop': 100000, 'buildings': {}})
    save_data()
    return jsonify({'ok': True})


@app.route('/health')
def health():
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('RP server started')
    app.run(host='0.0.0.0', port=port)
