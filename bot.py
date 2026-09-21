import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'

ADMIN_IDS = [8907438590]
TOKEN = '8872773404:AAEblXoLxAi1bGXVWtPNq3Tjmxb27JnlnOg'

START_IRISES = 100
PROMO_MIN = 30
PROMO_MAX = 130

SHOP_IDS = {
    'id_8889990': {'value': '8889990', 'price': 500,  'legendary': False},
    'id_5500300': {'value': '5500300', 'price': 800,  'legendary': False},
    'id_1234567': {'value': '1234567', 'price': 1200, 'legendary': False},
    'id_0000001': {'value': '0000001', 'price': 2000, 'legendary': True},
}

def load_json(f, d):
    if not os.path.exists(f): return d
    try:
        with open(f, 'r', encoding='utf-8') as fh: return json.load(fh)
    except: return d

def save_json(f, d):
    with open(f, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)

def load_stats(): return load_json(STATS_FILE, {})
def save_stats(d): save_json(STATS_FILE, d)

def gen_ai_id():
    return f"AI-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def gen_orcode():
    return f"{random.randint(1,999):03d}/{random.randint(1,999):03d}"

def gen_promo():
    return str(random.randint(1000, 9999))

def get_player(uid, fname='Anonymous', uname=''):
    stats = load_stats()
    k = str(uid)
    if k not in stats:
        stats[k] = {
            'first_name': fname or 'Anonymous',
            'username': uname or '',
            'irises': START_IRISES,
            'ai_id': None, 'orcode': None,
            'promo_code': None, 'promo_used': False,
            'owned_ids': [], 'active_id': None, 'verified': False
        }
    else:
        stats[k]['first_name'] = fname or stats[k].get('first_name', 'Anonymous')
        stats[k]['username'] = uname or stats[k].get('username', '')
        defaults = {
            'irises': START_IRISES,
            'ai_id': None, 'orcode': None,
            'promo_code': None, 'promo_used': False,
            'owned_ids': [], 'active_id': None, 'verified': False
        }
        for f, v in defaults.items():
            if f not in stats[k]: stats[k][f] = v
    save_stats(stats)
    return stats[k]

def update_player(uid, data):
    stats = load_stats()
    stats[str(uid)] = data
    save_stats(stats)

bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def send_html(self):
        paths = ['public/index.html', 'index.html']
        for path in paths:
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
                return
            except: continue
        self.send_response(404)
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0: return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except: return {}

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/index.html') or self.path.startswith('/?'):
            self.send_html(); return

        if self.path == '/api/health':
            self.send_json({'ok': True}); return

        if self.path == '/api/shop':
            items = []
            for sid, s in SHOP_IDS.items():
                items.append({
                    'id': sid, 'value': s['value'],
                    'price': s['price'], 'legendary': s['legendary']
                })
            self.send_json(items); return

        if self.path.startswith('/api/profile/'):
            try:
                user_id = self.path.split('/api/profile/')[-1]
                p = get_player(user_id)
                self.send_json({
                    'ok': True,
                    'first_name': p.get('first_name', 'Anonymous'),
                    'username': p.get('username', ''),
                    'irises': p.get('irises', START_IRISES),
                    'ai_id': p.get('ai_id'),
                    'orcode': p.get('orcode'),
                    'promo_code': p.get('promo_code'),
                    'promo_used': p.get('promo_used', False),
                    'owned_ids': p.get('owned_ids', []),
                    'active_id': p.get('active_id'),
                    'verified': p.get('verified', False)
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot running')

    def do_POST(self):
        data = self.read_body()

        if self.path == '/api/verify/start':
            try:
                user_id = str(data.get('user_id', ''))
                if not user_id:
                    self.send_json({'ok': False, 'error': 'no_user'}); return
                p = get_player(user_id)
                if p.get('verified') and p.get('ai_id'):
                    self.send_json({
                        'ok': True, 'already': True,
                        'ai_id': p['ai_id'], 'orcode': p['orcode'],
                        'promo_code': p['promo_code'],
                        'promo_used': p.get('promo_used', False)
                    }); return
                p['ai_id'] = gen_ai_id()
                p['orcode'] = gen_orcode()
                p['promo_code'] = gen_promo()
                p['verified'] = True
                update_player(user_id, p)
                self.send_json({
                    'ok': True, 'already': False,
                    'ai_id': p['ai_id'], 'orcode': p['orcode'],
                    'promo_code': p['promo_code'],
                    'promo_used': False
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/verify/promo':
            try:
                user_id = str(data.get('user_id', ''))
                code = str(data.get('code', '')).strip()
                if not user_id or not code:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                p = get_player(user_id)
                if not p.get('promo_code'):
                    self.send_json({'ok': False, 'error': 'no_verify'}); return
                if p.get('promo_used'):
                    self.send_json({'ok': False, 'error': 'already_used'}); return
                if code != p.get('promo_code'):
                    self.send_json({'ok': False, 'error': 'wrong_code'}); return
                reward = random.randint(PROMO_MIN, PROMO_MAX)
                p['irises'] = p.get('irises', 0) + reward
                p['promo_used'] = True
                update_player(user_id, p)
                self.send_json({'ok': True, 'reward': reward, 'irises': p['irises']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/shop/buy':
            try:
                user_id = str(data.get('user_id', ''))
                item_id = str(data.get('item_id', ''))
                if not user_id or not item_id:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                item = SHOP_IDS.get(item_id)
                if not item:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                p = get_player(user_id)
                owned = p.get('owned_ids', [])
                if item['value'] in owned:
                    self.send_json({'ok': False, 'error': 'already_owned'}); return
                price = item['price']
                if p.get('irises', 0) < price:
                    self.send_json({'ok': False, 'error': 'not_enough'}); return
                p['irises'] = p.get('irises', 0) - price
                owned.append(item['value'])
                p['owned_ids'] = owned
                p['active_id'] = item['value']
                update_player(user_id, p)
                self.send_json({
                    'ok': True, 'irises': p['irises'],
                    'active_id': p['active_id'], 'owned_ids': owned
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/shop/activate':
            try:
                user_id = str(data.get('user_id', ''))
                item_value = str(data.get('value', ''))
                if not user_id or not item_value:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                p = get_player(user_id)
                owned = p.get('owned_ids', [])
                if item_value not in owned:
                    self.send_json({'ok': False, 'error': 'not_owned'}); return
                p['active_id'] = item_value
                update_player(user_id, p)
                self.send_json({'ok': True, 'active_id': item_value}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        self.send_response(404)
        self.end_headers()

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    get_player(uid, m.from_user.first_name, m.from_user.username)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='🆔 Открыть Verify',
        web_app=types.WebAppInfo(url=f'https://otg-critic-bot.onrender.com/?user_id={uid}')
    ))
    text = (
        f"🆔 <b>VERIFY ID</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, <b>{m.from_user.first_name}</b>!\n\n"
        f"Тут ты можешь:\n"
        f"✅ Пройти верификацию\n"
        f"🎫 Получить промокод\n"
        f"💎 Купить крутой ID\n\n"
        f"👇 <i>Открой Mini App</i>"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(commands=['help'])
def cmd_help(m):
    text = (
        f"💬 <b>HELP</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🆔 /start — открыть Mini App\n\n"
        f"Внутри:\n"
        f"• Верификация ID\n"
        f"• Промокод (30-130 ирисок)\n"
        f"• Магазин ID"
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start','🆔 Открыть'),
            types.BotCommand('help','💬 Help'),
        ])
    except: pass

set_commands()
print('Bot started')
bot.infinity_polling()
