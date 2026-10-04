import json
import os
import time
import random
import sqlite3
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB = 'gifts.db'
COOLDOWN = 120
START_STARS = 100

COUNTRIES = [
    ('🇦🇩','common'),('🇦🇱','common'),('🇦🇲','common'),('🇦🇹','common'),
    ('🇦🇿','common'),('🇧🇦','common'),('🇧🇬','common'),('🇧🇾','common'),
    ('🇨🇭','common'),('🇨🇿','common'),('🇩🇰','common'),('🇪🇪','common'),
    ('🇫🇮','common'),('🇬🇪','common'),('🇭🇷','common'),('🇭🇺','common'),
    ('🇮🇸','common'),('🇮🇪','common'),('🇱🇹','common'),('🇱🇻','common'),
    ('🇲🇩','common'),('🇲🇪','common'),('🇲🇰','common'),('🇳🇴','common'),
    ('🇵🇹','common'),('🇷🇴','common'),('🇷🇸','common'),('🇸🇰','common'),
    ('🇸🇮','common'),('🇸🇪','common'),('🇺🇦','common'),('🇬🇷','common'),
    ('🇨🇾','common'),('🇲🇹','common'),('🇱🇺','common'),('🇲🇨','common'),
    ('🇱🇮','common'),('🇸🇲','common'),('🇻🇦','common'),
    ('🇵🇱','rare'),('🇦🇷','rare'),('🇦🇺','rare'),('🇧🇪','rare'),
    ('🇧🇷','rare'),('🇨🇦','rare'),('🇨🇱','rare'),('🇨🇴','rare'),
    ('🇪🇬','rare'),('🇮🇱','rare'),('🇮🇩','rare'),('🇮🇷','rare'),
    ('🇰🇿','rare'),('🇲🇽','rare'),('🇲🇦','rare'),('🇳🇱','rare'),
    ('🇳🇿','rare'),('🇳🇬','rare'),('🇵🇰','rare'),('🇵🇪','rare'),
    ('🇵🇭','rare'),('🇸🇦','rare'),('🇿🇦','rare'),('🇰🇷','rare'),
    ('🇪🇸','rare'),('🇹🇭','rare'),('🇹🇷','rare'),('🇻🇳','rare'),
    ('🇦🇪','rare'),('🇲🇾','rare'),
    ('🇬🇧','epic'),('🇩🇪','epic'),('🇫🇷','epic'),('🇮🇹','epic'),
    ('🇯🇵','epic'),('🇮🇳','epic'),
    ('🇺🇸','legendary'),('🇷🇺','legendary'),('🇨🇳','legendary'),
]

RARITY_NAMES = {
    'common': '⚪ Обычная',
    'rare': '🔵 Редкая',
    'epic': '🟣 Эпическая',
    'legendary': '🟡 Легендарная',
}
RARITY_WEIGHT = {'common': 60, 'rare': 25, 'epic': 12, 'legendary': 3}
RARITY_MIN_PRICE = {'common': 5, 'rare': 25, 'epic': 100, 'legendary': 500}
RARITY_MAX_PRICE = {'common': 50, 'rare': 200, 'epic': 1000, 'legendary': 10000}

SEASONS = {
    1:  {'name': '🍂 Осенний листопад', 'emoji': '🍁'},
    2:  {'name': '🌧️ Дождливый ноябрь', 'emoji': '🌧️'},
    3:  {'name': '🌫️ Туманы',           'emoji': '🌫️'},
    4:  {'name': '❄️ Первый снег',       'emoji': '❄️'},
    5:  {'name': '🎃 Хэллоуин',          'emoji': '🎃'},
    6:  {'name': '🕸️ Тёмная осень',      'emoji': '🕸️'},
    7:  {'name': '🍄 Грибной сезон',     'emoji': '🍄'},
    8:  {'name': '🌰 Урожай',            'emoji': '🌰'},
    9:  {'name': '🍷 Виноград',          'emoji': '🍷'},
    10: {'name': '🦔 Ёжики',             'emoji': '🦔'},
    11: {'name': '🐿️ Белки',             'emoji': '🐿️'},
    12: {'name': '🦌 Олени',             'emoji': '🦌'},
    13: {'name': '🐺 Волки',             'emoji': '🐺'},
    14: {'name': '🦉 Совы',              'emoji': '🦉'},
    15: {'name': '🐻 Медведи',           'emoji': '🐻'},
    16: {'name': '🦊 Лисы',              'emoji': '🦊'},
    17: {'name': '🐇 Зайцы',             'emoji': '🐇'},
    18: {'name': '🦇 Летучие мыши',      'emoji': '🦇'},
    19: {'name': '🕷️ Пауки',            'emoji': '🕷️'},
    20: {'name': '🍁 Клён',              'emoji': '🍁'},
    21: {'name': '🌲 Хвойный лес',       'emoji': '🌲'},
    22: {'name': '🌳 Дуб',               'emoji': '🌳'},
    23: {'name': '🍂 Листва',            'emoji': '🍂'},
    24: {'name': '🥧 Пироги',            'emoji': '🥧'},
    25: {'name': '☕ Чай',               'emoji': '☕'},
    26: {'name': '🍵 Какао',             'emoji': '🍵'},
    27: {'name': '🕯️ Свечи',            'emoji': '🕯️'},
    28: {'name': '📚 Книги',             'emoji': '📚'},
    29: {'name': '🎨 Краски осени',      'emoji': '🎨'},
    30: {'name': '👑 Финал сезона',      'emoji': '👑'},
}
SEASON_START = 1730419200

POINTS_PER_CASE_MIN = 100
POINTS_PER_CASE_MAX = 500
POINTS_PER_BONUS = 2000

MAX_LEVEL = 20
LEVEL_BASE = 5000
LEVEL_STEP = 2500


def init_db():
    conn = sqlite3.connect(DB); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, name TEXT,
        last_case INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
        last_bonus INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 100,
        total_earned INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        username TEXT DEFAULT ''
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, flag TEXT, rarity TEXT, time INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_uid INTEGER, seller_name TEXT,
        flag TEXT, rarity TEXT, price INTEGER, time INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS season (
        uid INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        premium INTEGER DEFAULT 0,
        claimed TEXT DEFAULT ''
    )''')
    conn.commit(); conn.close()

init_db()


def roll_country():
    rarity = random.choices(list(RARITY_WEIGHT.keys()), weights=list(RARITY_WEIGHT.values()))[0]
    pool = [c for c in COUNTRIES if c[1] == rarity]
    return random.choice(pool)


# ============================================================
# HTML — ТОП
# ============================================================
HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#0a0a12">
<title>Топ игроков</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--bg:#0a0a12;--card:#141420;--card-2:#1c1c2e;--line:#252538;--text:#fff;--dim:#8e8eae;--muted:#4a4a6a;--gold:#ffd60a;--silver:#c0c0c0;--bronze:#cd7f32;--accent:#7c5cff;--accent-2:#5e5ce6;--green:#30d158;--red:#ff453a}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;-webkit-font-smoothing:antialiased;letter-spacing:-.3px}
body{padding-bottom:env(safe-area-inset-bottom);overflow-x:hidden}

.tabs{display:flex;justify-content:center;gap:8px;padding:12px 16px;padding-top:calc(12px + env(safe-area-inset-top));background:rgba(10,10,18,0.95);backdrop-filter:blur(20px);position:sticky;top:0;z-index:10}
.tab{padding:8px 20px;border-radius:20px;font-size:14px;font-weight:600;color:var(--dim);background:var(--card);cursor:pointer;transition:.2s}
.tab.active{color:#fff;background:linear-gradient(135deg,var(--accent),var(--accent-2))}

.podium{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:20px 8px 12px;align-items:end}
.podium-item{display:flex;flex-direction:column;align-items:center;gap:6px;position:relative}
.podium-avatar{width:58px;height:58px;border-radius:50%;background:linear-gradient(135deg,#333,#555);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px;color:#fff;border:3px solid var(--card-2);overflow:hidden;position:relative}
.podium-avatar img{width:100%;height:100%;object-fit:cover;border-radius:50%}
.podium-item.rank-1 .podium-avatar{border-color:var(--gold);width:72px;height:72px;font-size:26px;box-shadow:0 0 24px rgba(255,214,10,0.35)}
.podium-item.rank-2 .podium-avatar{border-color:var(--silver);box-shadow:0 0 16px rgba(192,192,192,0.25)}
.podium-item.rank-3 .podium-avatar{border-color:var(--bronze);box-shadow:0 0 16px rgba(205,127,50,0.25)}
.podium-name{font-size:12px;font-weight:600;color:#fff;text-align:center;max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.podium-stars{font-size:13px;font-weight:700;color:#fff;display:flex;align-items:center;gap:3px}
.podium-gifts{display:flex;gap:2px;justify-content:center}
.podium-gift{width:18px;height:18px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:11px;background:var(--card-2)}
.podium-block{width:100%;border-radius:10px 10px 0 0;display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:900;color:rgba(0,0,0,0.55);margin-top:4px}
.podium-item.rank-1 .podium-block{background:linear-gradient(180deg,#ffd60a,#e6a800);height:120px;color:#1a1408}
.podium-item.rank-2 .podium-block{background:linear-gradient(180deg,#e0e0e0,#a8a8a8);height:90px}
.podium-item.rank-3 .podium-block{background:linear-gradient(180deg,#e0955a,#a05a1c);height:70px;color:#fff}

.refresh{display:flex;align-items:center;justify-content:center;gap:8px;padding:18px 16px 14px;font-size:13px;color:var(--dim)}
.refresh svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}

.list{padding:0 12px 24px;display:flex;flex-direction:column;gap:6px}
.item{display:flex;align-items:center;gap:10px;padding:11px 12px;background:var(--card);border-radius:14px}
.item.me{background:linear-gradient(135deg,rgba(124,92,255,0.18),rgba(94,92,230,0.06));border:1px solid rgba(124,92,255,0.35)}
.item-rank{width:30px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.rank-medal{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;background:var(--card-2);color:var(--dim)}
.item-avatar{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#333,#555);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;flex-shrink:0;overflow:hidden}
.item-avatar img{width:100%;height:100%;object-fit:cover}
.item-info{flex:1;min-width:0}
.item-name{font-size:15px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item-gifts{display:flex;gap:3px;margin-top:3px}
.item-gift{width:18px;height:18px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:11px;background:var(--card-2)}
.item-stars{font-size:15px;font-weight:700;color:#fff;display:flex;align-items:center;gap:3px;flex-shrink:0}

.loader{display:flex;justify-content:center;padding:60px}
.loader div{width:24px;height:24px;border:2px solid var(--card-2);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:60px 20px;color:var(--dim);font-size:14px}
</style>
</head>
<body>

<div class="tabs">
  <div class="tab active" data-tab="stars" onclick="setTab('stars')">Общий</div>
  <div class="tab" data-tab="cases" onclick="setTab('cases')">Кейсы</div>
  <div class="tab" data-tab="spent" onclick="setTab('spent')">Траты</div>
</div>

<div id="app"><div class="loader"><div></div></div></div>

<script>
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); if (tg.setHeaderColor) tg.setHeaderColor('#0a0a12'); }

let UID = 0;
if (tg?.initDataUnsafe?.user?.id) {
  UID = tg.initDataUnsafe.user.id;
  localStorage.setItem('uid', UID);
} else {
  UID = parseInt(localStorage.getItem('uid') || '0');
}

let currentTab = 'stars';

function getInitial(name) {
  return (name || '?').trim().charAt(0).toUpperCase();
}

function esc(s) {
  return String(s || '').replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));
}

function fmt(n) {
  return Number(n || 0).toLocaleString('ru-RU');
}

function setTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  loadTop();
}

function render(data) {
  const app = document.getElementById('app');

  if (!data || data.length === 0) {
    app.innerHTML = '<div class="empty">🏆 Пока никто не играл</div>';
    return;
  }

  const top3 = data.slice(0, 3);
  const rest = data.slice(3);
  const podiumOrder = [top3[1], top3[0], top3[2]].filter(Boolean);

  let html = '<div class="podium">';

  podiumOrder.forEach((user) => {
    const realRank = top3.indexOf(user) + 1;
    const avatar = user.photo
      ? `<img src="${esc(user.photo)}" alt="">`
      : getInitial(user.name);
    html += `
      <div class="podium-item rank-${realRank}">
        <div class="podium-gifts">
          ${(user.gifts || []).slice(0,2).map(g => `<div class="podium-gift">${g}</div>`).join('')}
          ${user.count ? `<div class="podium-gift">×${user.count}</div>` : ''}
        </div>
        <div class="podium-avatar">${avatar}</div>
        <div class="podium-name">${esc(user.name)}</div>
        <div class="podium-stars">${fmt(user.value)} <span>★</span></div>
        <div class="podium-block">${realRank}</div>
      </div>
    `;
  });

  html += '</div>';

  html += `
    <div class="refresh">
      <svg viewBox="0 0 24 24"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
      Рейтинг обновится через 6 дней
    </div>
  `;

  html += '<div class="list">';
  rest.forEach((user, i) => {
    const rank = i + 4;
    const isMe = String(user.uid) === String(UID);
    const avatar = user.photo
      ? `<img src="${esc(user.photo)}" alt="">`
      : getInitial(user.name);
    html += `
      <div class="item ${isMe ? 'me' : ''}">
        <div class="item-rank"><div class="rank-medal">${rank}</div></div>
        <div class="item-avatar">${avatar}</div>
        <div class="item-info">
          <div class="item-name">${esc(user.name)}</div>
          <div class="item-gifts">
            ${(user.gifts || []).slice(0,2).map(g => `<div class="item-gift">${g}</div>`).join('')}
            ${user.count ? `<div class="item-gift">×${user.count}</div>` : ''}
          </div>
        </div>
        <div class="item-stars">${fmt(user.value)} <span>★</span></div>
      </div>
    `;
  });
  html += '</div>';

  app.innerHTML = html;
}

async function loadTop() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="loader"><div></div></div>';
  try {
    const r = await fetch('/api/top?type=' + currentTab + '&uid=' + UID);
    const d = await r.json();
    render(d.top || []);
  } catch(e) {
    app.innerHTML = '<div class="empty">❌ Ошибка загрузки</div>';
  }
}

loadTop();
setInterval(loadTop, 30000);
</script>
</body>
</html>'''


# ============================================================
# API
# ============================================================
@app.route('/')
@app.route('/top')
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/api/top')
def api_top():
    t = request.args.get('type', 'stars')

    conn = sqlite3.connect(DB); c = conn.cursor()

    if t == 'cases':
        c.execute('SELECT uid, name, total FROM users ORDER BY total DESC LIMIT 30')
        rows = c.fetchall()
        data = [{'uid': r[0], 'name': r[1], 'value': r[2], 'gifts': [], 'count': 0} for r in rows]
    elif t == 'spent':
        c.execute('SELECT uid, name, total_spent FROM users ORDER BY total_spent DESC LIMIT 30')
        rows = c.fetchall()
        data = [{'uid': r[0], 'name': r[1], 'value': r[2], 'gifts': [], 'count': 0} for r in rows]
    else:
        c.execute('SELECT uid, name, stars FROM users ORDER BY stars DESC LIMIT 30')
        rows = c.fetchall()
        data = []
        for r in rows:
            uid, name, stars = r
            # Считаем редкие флаги для иконок
            c.execute('''SELECT rarity, COUNT(*) FROM gifts 
                         WHERE uid=? AND rarity IN ('legendary','epic') 
                         GROUP BY rarity''', (uid,))
            rare = dict(c.fetchall())
            gifts = []
            if rare.get('legendary'):
                gifts.append('🟡')
            if rare.get('epic'):
                gifts.append('🟣')
            data.append({
                'uid': uid,
                'name': name,
                'value': stars,
                'gifts': gifts,
                'count': len(gifts),
            })

    conn.close()
    return jsonify({'top': data})


@app.route('/health')
def health():
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('Leaderboard app started')
    app.run(host='0.0.0.0', port=port)
