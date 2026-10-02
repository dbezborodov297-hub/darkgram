import json
import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = 'block_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'scores': {}}

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print('save err:', e)

data = load_data()


# ============================================================
# HTML — Block Blast v2
# ============================================================
HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#0a0a1a">
<title>Block Blast</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;user-select:none;-webkit-user-select:none}
:root{
  --bg:#0a0a1a;--bg-2:#141428;--card:#1c1c3a;
  --text:#fff;--dim:#8e8ec0;--muted:#4a4a7a;
  --accent:#7c5cff;--accent-2:#5e5ce6;
  --gold:#ffd60a;--green:#30d158;--red:#ff453a;
}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display',sans-serif;font-size:16px;line-height:1.4;letter-spacing:-.3px;-webkit-font-smoothing:antialiased;position:fixed;width:100%}
.app{height:100vh;height:100dvh;display:flex;flex-direction:column;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom);overflow:hidden}

/* HEADER */
.top-bar{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;flex-shrink:0}
.score-box{text-align:center}
.score-label{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:1.2px;font-weight:700}
.score-value{font-size:32px;font-weight:800;letter-spacing:-1px;line-height:1;margin-top:2px}
.score-value.best{color:var(--gold)}
.icon-btn{width:42px;height:42px;border-radius:13px;background:var(--card);border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text)}
.icon-btn:active{transform:scale(.9)}
.icon-btn svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}

/* GRID */
.grid-wrap{flex:1;display:flex;align-items:center;justify-content:center;padding:8px;min-height:0}
.grid{display:grid;grid-template-columns:repeat(8,1fr);gap:4px;width:100%;max-width:min(92vw, 420px);aspect-ratio:1;background:var(--bg-2);padding:8px;border-radius:22px;position:relative;box-shadow:inset 0 2px 8px rgba(0,0,0,0.4)}
.cell{background:rgba(255,255,255,0.04);border-radius:8px;transition:background .15s;position:relative}
.cell.filled{border-radius:8px}
.cell.preview-ok{background:rgba(124,92,255,0.4)!important;box-shadow:inset 0 0 12px rgba(124,92,255,0.6)}
.cell.pop{animation:pop .35s ease-out}
@keyframes pop{0%{transform:scale(1.2);filter:brightness(2)}100%{transform:scale(0);opacity:0}}

/* 3D CUBES */
.cube{position:absolute;inset:0;border-radius:8px;overflow:hidden}
.cube::before{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,0.35) 0%,rgba(255,255,255,0.08) 45%,rgba(0,0,0,0.15) 100%);z-index:2;pointer-events:none}
.cube::after{content:'';position:absolute;top:6%;left:12%;width:24%;height:18%;background:rgba(255,255,255,0.55);border-radius:50%;filter:blur(2px);z-index:3;pointer-events:none}

/* COLORS THEMES */
.theme-classic .c-red{background:linear-gradient(180deg,#ff6b5e 0%,#ff3b30 45%,#c81e15 100%)}
.theme-classic .c-orange{background:linear-gradient(180deg,#ffb340 0%,#ff9500 45%,#c66b00 100%)}
.theme-classic .c-yellow{background:linear-gradient(180deg,#ffe066 0%,#ffcc00 45%,#c79c00 100%)}
.theme-classic .c-green{background:linear-gradient(180deg,#4cd964 0%,#34c759 45%,#1d8a3a 100%)}
.theme-classic .c-blue{background:linear-gradient(180deg,#3d9eff 0%,#007aff 45%,#0050b3 100%)}
.theme-classic .c-purple{background:linear-gradient(180deg,#c77dff 0%,#af52de 45%,#7a1f9e 100%)}
.theme-classic .c-pink{background:linear-gradient(180deg,#ff6b9d 0%,#ff2d55 45%,#b30030 100%)}

.theme-neon .c-red{background:linear-gradient(180deg,#ff4d6d 0%,#ff073a 45%,#a3001a 100%)}
.theme-neon .c-orange{background:linear-gradient(180deg,#ff9f45 0%,#ff6b00 45%,#a34100 100%)}
.theme-neon .c-yellow{background:linear-gradient(180deg,#faff5c 0%,#e6e600 45%,#8a8a00 100%)}
.theme-neon .c-green{background:linear-gradient(180deg,#5dff8a 0%,#00ff6a 45%,#009940 100%)}
.theme-neon .c-blue{background:linear-gradient(180deg,#4de1ff 0%,#00c8ff 45%,#0080a8 100%)}
.theme-neon .c-purple{background:linear-gradient(180deg,#c46bff 0%,#9500ff 45%,#5c0099 100%)}
.theme-neon .c-pink{background:linear-gradient(180deg,#ff5fa8 0%,#ff0066 45%,#a30040 100%)}

.theme-pastel .c-red{background:linear-gradient(180deg,#ffb3b3 0%,#ff8080 45%,#d14a4a 100%)}
.theme-pastel .c-orange{background:linear-gradient(180deg,#ffd4a3 0%,#ffb366 45%,#d18a3a 100%)}
.theme-pastel .c-yellow{background:linear-gradient(180deg,#ffef9f 0%,#ffe066 45%,#d1b93a 100%)}
.theme-pastel .c-green{background:linear-gradient(180deg,#b3e6c4 0%,#80d99e 45%,#4aa86e 100%)}
.theme-pastel .c-blue{background:linear-gradient(180deg,#b3d9ff 0%,#80bfff 45%,#4a8ad1 100%)}
.theme-pastel .c-purple{background:linear-gradient(180deg,#d9b3ff 0%,#b980ff 45%,#7a4ad1 100%)}
.theme-pastel .c-pink{background:linear-gradient(180deg,#ffb3d9 0%,#ff80bf 45%,#d14a8a 100%)}

.theme-dark .c-red{background:linear-gradient(180deg,#5c1a17 0%,#8b2622 45%,#b33933 100%)}
.theme-dark .c-orange{background:linear-gradient(180deg,#5c3a10 0%,#8b571a 45%,#b3762a 100%)}
.theme-dark .c-yellow{background:linear-gradient(180deg,#5c4d10 0%,#8b741a 45%,#b39a2a 100%)}
.theme-dark .c-green{background:linear-gradient(180deg,#14512a 0%,#1f7c40 45%,#2aa857 100%)}
.theme-dark .c-blue{background:linear-gradient(180deg,#103a5c 0%,#1a598b 45%,#2a7ab3 100%)}
.theme-dark .c-purple{background:linear-gradient(180deg,#3d1060 0%,#5c1a8b 45%,#7a2ab3 100%)}
.theme-dark .c-pink{background:linear-gradient(180deg,#5c1030 0%,#8b1a4a 45%,#b32a6a 100%)}

/* PIECES */
.pieces-area{display:flex;justify-content:space-around;align-items:center;padding:10px 8px 20px;gap:8px;flex-shrink:0;min-height:140px}
.piece-slot{flex:1;height:120px;display:flex;align-items:center;justify-content:center;position:relative}
.piece{display:grid;gap:4px;touch-action:none;transition:transform .15s;cursor:grab}
.piece.hidden{opacity:0;pointer-events:none}
.piece.dragging{position:fixed;pointer-events:none;z-index:1000;transform:scale(1.15);filter:drop-shadow(0 10px 20px rgba(0,0,0,0.5))}
.piece-cell{width:32px;height:32px;position:relative;border-radius:8px}
.piece-cell::before{content:'';position:absolute;inset:0;border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,0.35) 0%,rgba(255,255,255,0.08) 45%,rgba(0,0,0,0.15) 100%);z-index:2;pointer-events:none}
.piece-cell::after{content:'';position:absolute;top:6%;left:12%;width:24%;height:18%;background:rgba(255,255,255,0.55);border-radius:50%;filter:blur(2px);z-index:3;pointer-events:none}

/* OVERLAYS */
.overlay{position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);z-index:2000;display:none;align-items:center;justify-content:center;padding:20px}
.overlay.open{display:flex;animation:fadeIn .25s}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.panel{background:var(--card);border-radius:24px;padding:28px 24px;max-width:360px;width:100%;text-align:center;animation:popIn .3s cubic-bezier(0.32,0.72,0,1);max-height:85vh;overflow-y:auto}
@keyframes popIn{from{transform:scale(.85);opacity:0}to{transform:scale(1);opacity:1}}
.panel-icon{width:72px;height:72px;margin:0 auto 16px;border-radius:20px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center}
.panel-icon svg{width:38px;height:38px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.panel-icon.gold{background:linear-gradient(135deg,#ffd60a,#ff9500)}
.panel-icon.red{background:linear-gradient(135deg,#ff453a,#ff375f)}
.panel-title{font-size:26px;font-weight:800;letter-spacing:-.5px;margin-bottom:8px}
.panel-sub{font-size:14px;color:var(--dim);margin-bottom:20px;line-height:1.5}
.panel-score{font-size:48px;font-weight:800;color:var(--gold);letter-spacing:-1.5px;line-height:1;margin-bottom:6px}
.panel-best{font-size:13px;color:var(--dim);margin-bottom:24px}
.btn{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border:none;border-radius:14px;padding:15px 20px;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer;width:100%;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn:active{transform:scale(.97);opacity:.9}
.btn.secondary{background:var(--bg-2);color:var(--text)}
.btn svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}

/* TOP LIST */
.top-list{text-align:left;margin-top:6px}
.top-item{display:flex;align-items:center;gap:12px;padding:12px 4px;border-bottom:.5px solid var(--bg-2)}
.top-item:last-child{border:none}
.top-rank{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;background:var(--bg-2);color:var(--dim);flex-shrink:0}
.top-rank.g1{background:linear-gradient(135deg,#ffd60a,#ff9500);color:#1a1408}
.top-rank.g2{background:linear-gradient(135deg,#e0e0e0,#a8a8a8);color:#1a1408}
.top-rank.g3{background:linear-gradient(135deg,#cd7f32,#a05a1c);color:#fff}
.top-name{flex:1;font-size:15px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.top-score{font-weight:800;color:var(--gold);font-size:15px}

/* SETTINGS ROW */
.color-row{display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:.5px solid var(--bg-2);cursor:pointer}
.color-row:last-child{border:none}
.color-row.active{background:rgba(124,92,255,0.1);border-radius:12px;padding-left:12px;padding-right:12px}
.color-row-icon{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.color-row-info{flex:1;text-align:left}
.color-row-name{font-size:15px;font-weight:600}
.color-row-sub{font-size:12px;color:var(--dim);margin-top:2px}
.color-row-check{color:var(--accent);font-size:20px}
.swatch-row{display:flex;gap:6px;margin-top:4px}
.swatch{width:22px;height:22px;border-radius:6px}

/* TOAST */
.toast{position:fixed;bottom:180px;left:50%;transform:translateX(-50%) translateY(120%);background:rgba(28,28,58,0.98);border:1px solid rgba(124,92,255,0.4);color:#fff;padding:12px 22px;border-radius:14px;font-size:15px;font-weight:600;z-index:3000;opacity:0;transition:.25s;pointer-events:none;max-width:90vw;text-align:center}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.gold{border-color:var(--gold);color:var(--gold)}

/* SCORE POPUP */
.score-popup{position:fixed;pointer-events:none;font-size:28px;font-weight:800;color:var(--gold);z-index:1500;animation:scoreFloat 1s ease-out forwards;text-shadow:0 2px 12px rgba(255,214,10,0.7)}
@keyframes scoreFloat{0%{transform:translateY(0) scale(1);opacity:1}100%{transform:translateY(-80px) scale(1.4);opacity:0}}
</style>
</head>
<body class="theme-classic">
<div class="app">

  <div class="top-bar">
    <div style="width:42px"></div>
    <div style="display:flex;gap:32px;align-items:center">
      <div class="score-box">
        <div class="score-label">Счёт</div>
        <div class="score-value" id="score">0</div>
      </div>
      <div class="score-box">
        <div class="score-label">Рекорд</div>
        <div class="score-value best" id="best">0</div>
      </div>
    </div>
    <button class="icon-btn" onclick="openTop()">
      <svg viewBox="0 0 24 24"><path d="M8 21h8M12 17v4"/><path d="M17 4h3v3a5 5 0 01-5 5h-1"/><path d="M7 4H4v3a5 5 0 005 5h1"/><path d="M7 4h10v6a5 5 0 01-10 0V4z"/></svg>
    </button>
  </div>

  <div class="grid-wrap">
    <div class="grid" id="grid"></div>
  </div>

  <div class="pieces-area" id="piecesArea">
    <div class="piece-slot" id="slot0"></div>
    <div class="piece-slot" id="slot1"></div>
    <div class="piece-slot" id="slot2"></div>
  </div>

</div>

<!-- GAME OVER -->
<div class="overlay" id="gameoverOverlay">
  <div class="panel">
    <div class="panel-icon red"><svg viewBox="0 0 24 24"><path d="M12 2l3 6 6 1-4.5 4.5L18 20l-6-3-6 3 1.5-6.5L3 9l6-1z"/></svg></div>
    <div class="panel-title">Игра окончена</div>
    <div class="panel-sub">Ходов больше нет</div>
    <div class="panel-score" id="finalScore">0</div>
    <div class="panel-best" id="finalBest">Рекорд: 0</div>
    <button class="btn" onclick="restart()">
      <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 019-9 9 9 0 019 9 9 9 0 01-9 9"/><path d="M3 12l3-3m0 6l-3-3"/></svg>
      Играть снова
    </button>
    <button class="btn secondary" onclick="closeOverlay('gameoverOverlay');openSettings()">Настройки</button>
  </div>
</div>

<!-- TOP -->
<div class="overlay" id="topOverlay">
  <div class="panel">
    <div class="panel-icon gold"><svg viewBox="0 0 24 24"><path d="M8 21h8M12 17v4"/><path d="M17 4h3v3a5 5 0 01-5 5h-1"/><path d="M7 4H4v3a5 5 0 005 5h1"/><path d="M7 4h10v6a5 5 0 01-10 0V4z"/></svg></div>
    <div class="panel-title">Топ игроков</div>
    <div class="panel-sub">Лучшие результаты</div>
    <div class="top-list" id="topList"><div style="text-align:center;color:var(--dim);padding:20px">Загрузка...</div></div>
    <button class="btn secondary" style="margin-top:20px" onclick="closeOverlay('topOverlay')">Закрыть</button>
  </div>
</div>

<!-- SETTINGS -->
<div class="overlay" id="settingsOverlay">
  <div class="panel">
    <div class="panel-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg></div>
    <div class="panel-title">Настройки</div>
    <div class="panel-sub">Цвет кубиков</div>
    <div id="themeList"></div>
    <button class="btn secondary" style="margin-top:20px" onclick="closeOverlay('settingsOverlay')">Закрыть</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); if (tg.setHeaderColor) tg.setHeaderColor('#0a0a1a'); }

let UID = 0;
if (tg?.initDataUnsafe?.user?.id) {
  UID = tg.initDataUnsafe.user.id;
  localStorage.setItem('bb_uid', UID);
} else {
  UID = parseInt(localStorage.getItem('bb_uid') || '0');
}
const USER_NAME = tg?.initDataUnsafe?.user?.first_name || 'Игрок';

// ============================================================
// THEMES
// ============================================================
const THEMES = [
  {id:'classic', name:'Классика', sub:'Яркие цвета',
   colors:['#ff3b30','#ff9500','#ffcc00','#34c759','#007aff','#af52de','#ff2d55']},
  {id:'neon', name:'Неон', sub:'Кислотные оттенки',
   colors:['#ff073a','#ff6b00','#e6e600','#00ff6a','#00c8ff','#9500ff','#ff0066']},
  {id:'pastel', name:'Пастель', sub:'Мягкие тона',
   colors:['#ff8080','#ffb366','#ffe066','#80d99e','#80bfff','#b980ff','#ff80bf']},
  {id:'dark', name:'Тёмная', sub:'Приглушённые',
   colors:['#8b2622','#8b571a','#8b741a','#1f7c40','#1a598b','#5c1a8b','#8b1a4a']},
];

let currentTheme = localStorage.getItem('bb_theme') || 'classic';
function applyTheme(id) {
  document.body.className = 'theme-' + id;
  currentTheme = id;
  localStorage.setItem('bb_theme', id);
}

// ============================================================
// SHAPES
// ============================================================
const SHAPES = [
  [[0,0]],
  [[0,0],[0,1]],
  [[0,0],[1,0]],
  [[0,0],[0,1],[0,2]],
  [[0,0],[1,0],[2,0]],
  [[0,0],[0,1],[1,0]],
  [[0,0],[0,1],[1,1]],
  [[0,1],[1,0],[1,1]],
  [[0,0],[1,0],[1,1]],
  [[0,0],[0,1],[0,2],[0,3]],
  [[0,0],[1,0],[2,0],[3,0]],
  [[0,0],[0,1],[1,0],[1,1]],
  [[0,0],[0,1],[0,2],[1,0]],
  [[0,0],[0,1],[0,2],[1,2]],
  [[0,0],[1,0],[1,1],[1,2]],
  [[0,2],[1,0],[1,1],[1,2]],
  [[0,0],[1,0],[2,0],[2,1]],
  [[0,0],[0,1],[1,1],[2,1]],
  [[0,0],[0,1],[0,2],[0,3],[0,4]],
  [[0,0],[1,0],[2,0],[3,0],[4,0]],
];

const COLOR_CLASSES = ['c-red','c-orange','c-yellow','c-green','c-blue','c-purple','c-pink'];
const SIZE = 8;
let grid = [];
let score = 0;
let best = parseInt(localStorage.getItem('bb_best') || '0');
let pieces = [null, null, null];
let gameOver = false;

// ============================================================
// INIT
// ============================================================
function initGrid() {
  grid = Array(SIZE).fill(null).map(() => Array(SIZE).fill(null));
}

function renderGrid() {
  const g = document.getElementById('grid');
  g.innerHTML = '';
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const cell = document.createElement('div');
      cell.className = 'cell';
      if (grid[r][c]) {
        cell.classList.add('filled', grid[r][c]);
        const cube = document.createElement('div');
        cube.className = 'cube';
        cell.appendChild(cube);
      }
      g.appendChild(cell);
    }
  }
}

function renderPieces() {
  for (let i = 0; i < 3; i++) {
    const slot = document.getElementById('slot' + i);
    slot.innerHTML = '';
    if (!pieces[i]) continue;
    const p = pieces[i];
    const el = document.createElement('div');
    el.className = 'piece';
    el.dataset.idx = i;
    const rows = Math.max(...p.shape.map(s => s[0])) + 1;
    const cols = Math.max(...p.shape.map(s => s[1])) + 1;
    el.style.gridTemplateColumns = `repeat(${cols}, 32px)`;
    el.style.gridTemplateRows = `repeat(${rows}, 32px)`;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const has = p.shape.some(s => s[0] === r && s[1] === c);
        const cell = document.createElement('div');
        if (has) {
          cell.className = 'piece-cell ' + p.color;
        } else {
          cell.style.visibility = 'hidden';
        }
        el.appendChild(cell);
      }
    }
    attachDrag(el, i);
    slot.appendChild(el);
  }
}

function randomPiece() {
  const shape = SHAPES[Math.floor(Math.random() * SHAPES.length)];
  const color = COLOR_CLASSES[Math.floor(Math.random() * COLOR_CLASSES.length)];
  return {shape: shape.map(s => [...s]), color};
}

function refillPieces() {
  for (let i = 0; i < 3; i++) {
    if (!pieces[i]) pieces[i] = randomPiece();
  }
}

function checkGameOver() {
  for (const p of pieces) {
    if (!p) continue;
    if (canPlaceAnywhere(p)) return false;
  }
  return true;
}

function canPlaceAnywhere(piece) {
  const rows = Math.max(...piece.shape.map(s => s[0])) + 1;
  const cols = Math.max(...piece.shape.map(s => s[1])) + 1;
  for (let r = 0; r <= SIZE - rows; r++) {
    for (let c = 0; c <= SIZE - cols; c++) {
      if (canPlace(piece.shape, r, c)) return true;
    }
  }
  return false;
}

function canPlace(shape, row, col) {
  for (const [r, c] of shape) {
    const rr = row + r, cc = col + c;
    if (rr < 0 || rr >= SIZE || cc < 0 || cc >= SIZE) return false;
    if (grid[rr][cc]) return false;
  }
  return true;
}

// ============================================================
// DRAG & DROP — ФИКС: не пропадают соседние фигуры
// ============================================================
let dragState = null;

function attachDrag(el, idx) {
  el.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (gameOver || dragState) return;
    const piece = pieces[idx];
    if (!piece) return;

    const rect = el.getBoundingClientRect();
    const clone = el.cloneNode(true);
    clone.classList.add('dragging');
    clone.style.left = rect.left + 'px';
    clone.style.top = rect.top + 'px';
    clone.style.width = rect.width + 'px';
    clone.style.height = rect.height + 'px';
    document.body.appendChild(clone);

    el.style.visibility = 'hidden';

    dragState = {
      idx, piece, clone,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
      el: el,
      previewRow: null,
      previewCol: null
    };

    document.addEventListener('pointermove', onDragMove);
    document.addEventListener('pointerup', onDragEnd);
    document.addEventListener('pointercancel', onDragEnd);
  });
}

function onDragMove(e) {
  if (!dragState) return;
  e.preventDefault();
  const { clone, offsetX, offsetY, piece } = dragState;
  clone.style.left = (e.clientX - offsetX) + 'px';
  clone.style.top = (e.clientY - offsetY) + 'px';

  clearPreview();
  const gridEl = document.getElementById('grid');
  const gridRect = gridEl.getBoundingClientRect();
  const cellSize = gridRect.width / SIZE;

  const pieceLeft = e.clientX - offsetX;
  const pieceTop = e.clientY - offsetY;

  const col = Math.round((pieceLeft - gridRect.left) / cellSize);
  const row = Math.round((pieceTop - gridRect.top) / cellSize);

  if (canPlace(piece.shape, row, col)) {
    for (const [r, c] of piece.shape) {
      const idx = (row + r) * SIZE + (col + c);
      const cell = gridEl.children[idx];
      if (cell) cell.classList.add('preview-ok');
    }
    dragState.previewRow = row;
    dragState.previewCol = col;
  } else {
    dragState.previewRow = null;
    dragState.previewCol = null;
  }
}

function onDragEnd(e) {
  if (!dragState) return;
  document.removeEventListener('pointermove', onDragMove);
  document.removeEventListener('pointerup', onDragEnd);
  document.removeEventListener('pointercancel', onDragEnd);

  const { idx, piece, clone, previewRow, previewCol, el } = dragState;

  clone.remove();
  clearPreview();

  if (previewRow !== null && previewCol !== null) {
    placePiece(idx, piece, previewRow, previewCol);
  } else {
    // Возврат — показываем фигуру назад
    if (el) el.style.visibility = '';
  }

  dragState = null;
}

function clearPreview() {
  document.querySelectorAll('.cell.preview-ok').forEach(el => {
    el.classList.remove('preview-ok');
  });
}

// ============================================================
// PLACE PIECE
// ============================================================
function placePiece(idx, piece, row, col) {
  for (const [r, c] of piece.shape) {
    grid[row + r][col + c] = piece.color;
  }
  pieces[idx] = null;

  score += piece.shape.length;
  updateScoreUI();

  const cleared = clearLines();
  renderGrid();

  if (cleared > 0) {
    const bonus = cleared * 10;
    score += bonus;
    updateScoreUI();
    setTimeout(() => showScorePopup('+' + bonus), 150);
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  } else {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
  }

  setTimeout(() => {
    refillPieces();
    renderPieces();

    if (checkGameOver()) {
      setTimeout(() => showGameOver(), 400);
    }
  }, 250);
}

function updateScoreUI() {
  document.getElementById('score').textContent = score;
  if (score > best) {
    best = score;
    localStorage.setItem('bb_best', best);
    document.getElementById('best').textContent = best;
  }
}

function showScorePopup(text) {
  const el = document.createElement('div');
  el.className = 'score-popup';
  el.textContent = text;
  el.style.left = '50%';
  el.style.top = '45%';
  el.style.transform = 'translateX(-50%)';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1000);
}

// ============================================================
// CLEAR LINES
// ============================================================
function clearLines() {
  const toClear = new Set();
  for (let r = 0; r < SIZE; r++) {
    if (grid[r].every(c => c)) {
      for (let c = 0; c < SIZE; c++) toClear.add(r * SIZE + c);
    }
  }
  for (let c = 0; c < SIZE; c++) {
    let full = true;
    for (let r = 0; r < SIZE; r++) if (!grid[r][c]) { full = false; break; }
    if (full) {
      for (let r = 0; r < SIZE; r++) toClear.add(r * SIZE + c);
    }
  }

  const gridEl = document.getElementById('grid');
  toClear.forEach(i => {
    if (gridEl.children[i]) gridEl.children[i].classList.add('pop');
  });

  toClear.forEach(i => {
    const r = Math.floor(i / SIZE);
    const c = i % SIZE;
    grid[r][c] = null;
  });

  return toClear.size > 0 ? Math.round(toClear.size / SIZE) : 0;
}

// ============================================================
// GAME OVER
// ============================================================
async function showGameOver() {
  gameOver = true;
  document.getElementById('finalScore').textContent = score;
  document.getElementById('finalBest').textContent = 'Рекорд: ' + best;
  document.getElementById('gameoverOverlay').classList.add('open');
  if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');

  if (UID && score > 0) {
    try {
      await fetch('/api/score', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({uid: UID, name: USER_NAME, score: score})
      });
    } catch(e) {}
  }
}

function restart() {
  score = 0;
  gameOver = false;
  initGrid();
  renderGrid();
  pieces = [null, null, null];
  refillPieces();
  renderPieces();
  updateScoreUI();
  closeOverlay('gameoverOverlay');
}

// ============================================================
// TOP
// ============================================================
async function openTop() {
  document.getElementById('topOverlay').classList.add('open');
  const list = document.getElementById('topList');
  list.innerHTML = '<div style="text-align:center;color:var(--dim);padding:20px">Загрузка...</div>';
  try {
    const r = await fetch('/api/top');
    const d = await r.json();
    if (!d.top || d.top.length === 0) {
      list.innerHTML = '<div style="text-align:center;color:var(--dim);padding:20px">Пока никто не играл</div>';
      return;
    }
    list.innerHTML = d.top.map((u, i) => {
      const rc = i === 0 ? 'g1' : i === 1 ? 'g2' : i === 2 ? 'g3' : '';
      const me = String(u.uid) === String(UID) ? ' · ты' : '';
      return `<div class="top-item"><div class="top-rank ${rc}">${i+1}</div><div class="top-name">${esc(u.name || 'Игрок')}${me}</div><div class="top-score">${u.score}</div></div>`;
    }).join('');
  } catch(e) {
    list.innerHTML = '<div style="text-align:center;color:var(--red);padding:20px">Ошибка</div>';
  }
}

function esc(s) {
  return String(s || '').replace(/[<>&"]/g, ch => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'})[ch]);
}

// ============================================================
// SETTINGS — смена цветов
// ============================================================
function openSettings() {
  const list = document.getElementById('themeList');
  list.innerHTML = THEMES.map(t => `
    <div class="color-row ${currentTheme === t.id ? 'active' : ''}" onclick="selectTheme('${t.id}')">
      <div class="swatch-row">
        ${t.colors.map(c => `<div class="swatch" style="background:${c}"></div>`).join('')}
      </div>
      <div class="color-row-info">
        <div class="color-row-name">${t.name}</div>
        <div class="color-row-sub">${t.sub}</div>
      </div>
      ${currentTheme === t.id ? '<div class="color-row-check">✓</div>' : ''}
    </div>
  `).join('');
  document.getElementById('settingsOverlay').classList.add('open');
}

function selectTheme(id) {
  applyTheme(id);
  if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
  openSettings();
}

// ============================================================
// UI
// ============================================================
function closeOverlay(id) {
  document.getElementById(id).classList.remove('open');
}

function toast(msg, gold) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast' + (gold ? ' gold' : '');
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 2200);
}

// ============================================================
// START
// ============================================================
applyTheme(currentTheme);
document.getElementById('best').textContent = best;
initGrid();
renderGrid();
refillPieces();
renderPieces();
updateScoreUI();

// Кнопка настроек — долгое нажатие на рекорд
document.querySelector('.score-value.best').addEventListener('click', openSettings);
</script>
</body>
</html>'''


# ============================================================
# API
# ============================================================
@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/api/top')
def api_top():
    scores = data.get('scores', {})
    arr = []
    for uid, info in scores.items():
        arr.append({
            'uid': uid,
            'name': info.get('name', 'Игрок'),
            'score': info.get('score', 0),
        })
    arr.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'top': arr[:20]})


@app.route('/api/score', methods=['POST'])
def api_score():
    d = request.json or {}
    uid = d.get('uid')
    name = d.get('name', 'Игрок')
    score = int(d.get('score', 0))
    if not uid:
        return jsonify({'error': 'no uid'}), 400
    scores = data.setdefault('scores', {})
    key = str(uid)
    current = scores.get(key, {}).get('score', 0)
    if score > current:
        scores[key] = {'name': name, 'score': score}
        save_data()
        return jsonify({'ok': True, 'new_record': True})
    return jsonify({'ok': True, 'new_record': False})


@app.route('/health')
def health():
    return 'OK'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('Block Blast v2 server started')
    app.run(host='0.0.0.0', port=port)
