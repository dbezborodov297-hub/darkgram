 import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
MARKET_FILE = 'market.json'
GIFT_LIMITS_FILE = 'gift_limits.json'

WEBAPP_URL = 'https://darkgram-fkc2.onrender.com/'
ADMIN_IDS = [8907438590]

CLICK_REWARD = 0.1
CASE_PRICE = 100
MAX_LIMIT = 150

GIFTS = {
    'bear':     {'name': 'Медведь',  'emoji': '🐻', 'rarity': 'Common',    'chance': 25, 'price': 80,  'limit': 150},
    'rose':     {'name': 'Роза',     'emoji': '🌹', 'rarity': 'Common',    'chance': 24, 'price': 80,  'limit': 150},
    'cake':     {'name': 'Торт',     'emoji': '🎂', 'rarity': 'Common',    'chance': 20, 'price': 70,  'limit': 150},
    'candy':    {'name': 'Конфета',  'emoji': '🍬', 'rarity': 'Common',    'chance': 15, 'price': 100, 'limit': 150},
    'bread':    {'name': 'Хлеб',     'emoji': '🍞', 'rarity': 'Common',    'chance': 12, 'price': 90,  'limit': 150},
    'heart':    {'name': 'Сердце',   'emoji': '❤️', 'rarity': 'Rare',      'chance': 10, 'price': 150, 'limit': 150},
    'star':     {'name': 'Звезда',   'emoji': '⭐', 'rarity': 'Rare',      'chance': 8,  'price': 180, 'limit': 150},
    'crown':    {'name': 'Корона',   'emoji': '👑', 'rarity': 'Epic',      'chance': 4,  'price': 300, 'limit': 150},
    'diamond':  {'name': 'Алмаз',    'emoji': '💎', 'rarity': 'Epic',      'chance': 2,  'price': 350, 'limit': 150},
    'ring':     {'name': 'Кольцо',   'emoji': '💍', 'rarity': 'Legendary', 'chance': 1,  'price': 450, 'limit': 150},
    'rocket':   {'name': 'Ракета',   'emoji': '🚀', 'rarity': 'Legendary', 'chance': 1,  'price': 500, 'limit': 150},
    'beach':    {'name': 'Пляж',     'emoji': '🏖️', 'rarity': 'Legendary', 'chance': 0.5,'price': 550, 'limit': 150},
    'rosette':  {'name': 'Розетка',  'emoji': '🏵️', 'rarity': 'Legendary', 'chance': 0.5,'price': 650, 'limit': 150},
    'lollipop': {'name': 'Леденец',  'emoji': '🍭', 'rarity': 'Legendary', 'chance': 0.3,'price': 890, 'limit': 150},
    'cookie':   {'name': 'Печенье',  'emoji': '🍪', 'rarity': 'Legendary', 'chance': 0.3,'price': 920, 'limit': 150},
}

SKINS = {
    'candy': {
        'cupcake':  {'name': 'Кекс',      'emoji': '🧁', 'price': 2000},
        'icecream': {'name': 'Мороженое', 'emoji': '🍨', 'price': 1800},
        'sorbet':   {'name': 'Щербет',    'emoji': '🍧', 'price': 1500},
        'dango':    {'name': 'Данго',     'emoji': '🍡', 'price': 2500},
        'softice':  {'name': 'Мягкое',    'emoji': '🍦', 'price': 1700},
        'shortcake':{'name': 'Тортик',    'emoji': '🍰', 'price': 2200},
        'donut':    {'name': 'Пончик',    'emoji': '🍩', 'price': 1600},
        'choco':    {'name': 'Шоколад',   'emoji': '🍫', 'price': 2100},
    },
    'rose': {
        'bouquet':  {'name': 'Букет',     'emoji': '💐', 'price': 3500},
        'wilted':   {'name': 'Увядшая',   'emoji': '🥀', 'price': 3200},
        'hibiscus': {'name': 'Гибискус',  'emoji': '🌺', 'price': 3800},
        'tulip':    {'name': 'Тюльпан',   'emoji': '🌷', 'price': 3600},
        'lotus':    {'name': 'Лотос',     'emoji': '🪷', 'price': 4200},
        'blossom':  {'name': 'Сакура',    'emoji': '💮', 'price': 4000},
        'cherry':   {'name': 'Вишня',     'emoji': '🌸', 'price': 3700},
        'lavender': {'name': 'Лаванда',   'emoji': '🪻', 'price': 3400},
        'daisy':    {'name': 'Ромашка',   'emoji': '🌼', 'price': 3300},
    },
    'bread': {
        'flat':     {'name': 'Лепёшка',   'emoji': '🫓', 'price': 1500},
        'croissant':{'name': 'Круассан',  'emoji': '🥐', 'price': 1800},
        'baguette': {'name': 'Багет',     'emoji': '🥖', 'price': 1700},
        'bagel':    {'name': 'Бублик',    'emoji': '🥯', 'price': 1600},
        'waffle':   {'name': 'Вафля',     'emoji': '🧇', 'price': 1900},
        'pancake':  {'name': 'Блин',      'emoji': '🥞', 'price': 2000},
        'sandwich': {'name': 'Сэндвич',   'emoji': '🥪', 'price': 2200},
    },
}

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stats(): return load_json(STATS_FILE, {})
def save_stats(d): save_json(STATS_FILE, d)
def load_market(): return load_json(MARKET_FILE, [])
def save_market(d): save_json(MARKET_FILE, d)
def load_limits(): return load_json(GIFT_LIMITS_FILE, {})
def save_limits(d): save_json(GIFT_LIMITS_FILE, d)

def is_admin_id(user_id):
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def get_limit(gift_id):
    limits = load_limits()
    return limits.get(gift_id, 0)

def inc_limit(gift_id):
    limits = load_limits()
    limits[gift_id] = limits.get(gift_id, 0) + 1
    save_limits(limits)

def get_skin_limit(skin_id):
    limits = load_limits()
    return limits.get('skin_' + skin_id, 0)

def inc_skin_limit(skin_id):
    limits = load_limits()
    limits['skin_' + skin_id] = limits.get('skin_' + skin_id, 0) + 1
    save_limits(limits)

def find_user_by_username(username):
    if not username: return None
    username = username.lower().lstrip('@')
    stats = load_stats()
    for uid, data in stats.items():
        if (data.get('username') or '').lower() == username:
            return uid, data
    return None

def get_user(user_id, first_name='Аноним', username=''):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'irises': 0.0,
            'clicks': 0,
            'gifts': [],
            'skins': []
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        if 'clicks' not in stats[key]: stats[key]['clicks'] = 0
        if 'gifts' not in stats[key]: stats[key]['gifts'] = []
        if 'skins' not in stats[key]: stats[key]['skins'] = []
        if 'irises' not in stats[key]: stats[key]['irises'] = 0.0
    save_stats(stats)
    return stats[key]

def update_user(user_id, data):
    stats = load_stats()
    stats[str(user_id)] = data
    save_stats(stats)

def open_case(user_id):
    available = []
    for gid, g in GIFTS.items():
        used = get_limit(gid)
        if used < g.get('limit', MAX_LIMIT):
            available.append((gid, g))
    if not available:
        return None
    total = sum(g[1]['chance'] for g in available)
    r = random.uniform(0, total)
    acc = 0
    chosen_id = available[0][0]
    for gid, gdata in available:
        acc += gdata['chance']
        if r <= acc:
            chosen_id = gid
            break
    gift = GIFTS[chosen_id]
    unique_id = random.randint(1, 999999)
    user = get_user(user_id)
    gift_record = {
        'id': chosen_id, 'name': gift['name'], 'emoji': gift['emoji'],
        'rarity': gift['rarity'], 'unique': unique_id,
        'base_price': gift.get('price', 100),
        'opened_at': int(time.time() * 1000), 'on_market': False,
        'active_skin': None
    }
    user['gifts'].append(gift_record)
    update_user(user_id, user)
    inc_limit(chosen_id)
    return gift_record

def create_gift_by_id(gift_id, admin=False):
    if gift_id not in GIFTS: return None
    gift = GIFTS[gift_id]
    if not admin:
        if get_limit(gift_id) >= gift.get('limit', MAX_LIMIT):
            return None
        inc_limit(gift_id)
    return {
        'id': gift_id, 'name': gift['name'], 'emoji': gift['emoji'],
        'rarity': gift['rarity'], 'unique': random.randint(1, 999999),
        'base_price': gift.get('price', 100),
        'opened_at': int(time.time() * 1000), 'on_market': False,
        'active_skin': None
    }

def find_gift_in_user(user_id, unique):
    user = get_user(user_id)
    for g in user.get('gifts', []):
        if g.get('unique') == unique:
            return g
    return None

def get_skin_by_id(skin_id):
    for parent, skins in SKINS.items():
        if skin_id in skins:
            return parent, skins[skin_id]
    return None, None

def build_user_gift_view(user_id):
    user = get_user(user_id)
    result = []
    for g in user.get('gifts', []):
        item = dict(g)
        parent = g.get('id')
        available_skins = []
        if parent in SKINS:
            for sid, sdata in SKINS[parent].items():
                owned = any(s.get('skin_id') == sid and s.get('unique') == g.get('unique') for s in user.get('skins', []))
                available_skins.append({
                    'id': sid,
                    'name': sdata['name'],
                    'emoji': sdata['emoji'],
                    'price': sdata['price'],
                    'owned': owned,
                    'limit_used': get_skin_limit(sid),
                    'limit_max': MAX_LIMIT
                })
        item['available_skins'] = available_skins
        result.append(item)
    return result

TOKEN = '8883984473:AAF12ux76ov704A-CDbFAbBoDWp1rr3j_4k'
bot = telebot.TeleBot(TOKEN)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

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
            except Exception:
                continue
        self.send_response(404)
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0: return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/index.html') or self.path.startswith('/?'):
            self.send_html(); return

        if self.path == '/api/top':
            stats = load_stats()
            sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('irises', 0), reverse=True)[:20]
            result = []
            for i, (uid, data) in enumerate(sorted_stats, 1):
                result.append({'place': i, 'id': uid,
                               'first_name': data.get('first_name', 'Аноним'),
                               'username': data.get('username', ''),
                               'irises': round(data.get('irises', 0), 1)})
            self.send_json(result); return

        if self.path == '/api/market':
            market = load_market()
            market.sort(key=lambda x: x.get('listed_at', 0), reverse=True)
            self.send_json(market); return

        if self.path == '/api/gifts_catalog':
            catalog = []
            for gid, g in GIFTS.items():
                catalog.append({
                    'id': gid, 'name': g['name'], 'emoji': g['emoji'],
                    'rarity': g['rarity'], 'price': g.get('price', 100),
                    'limit_used': get_limit(gid),
                    'limit_max': g.get('limit', MAX_LIMIT)
                })
            self.send_json(catalog); return

        if self.path == '/api/skins_catalog':
            catalog = {}
            for parent, skins in SKINS.items():
                catalog[parent] = []
                for sid, sdata in skins.items():
                    catalog[parent].append({
                        'id': sid, 'name': sdata['name'], 'emoji': sdata['emoji'],
                        'price': sdata['price'],
                        'limit_used': get_skin_limit(sid),
                        'limit_max': MAX_LIMIT
                    })
            self.send_json(catalog); return

        if self.path == '/api/event':
            event = load_json('event.json', {'active': False, 'start': 0, 'multiplier': 2, 'bonus': 50})
            active = event.get('active', False)
            left = 0
            if active:
                left = max(0, int(1200 - (time.time() - event.get('start', 0))))
                if left <= 0: active = False
            self.send_json({
                'active': active, 'left': left,
                'multiplier': event.get('multiplier', 2),
                'bonus': event.get('bonus', 50)
            }); return

        if self.path.startswith('/api/gifts/'):
            try:
                user_id = self.path.split('/api/gifts/')[-1]
                self.send_json(build_user_gift_view(user_id)); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/user/'):
            try:
                user_id = self.path.split('/api/user/')[-1]
                stats = load_stats()
                user = stats.get(user_id, {})
                self.send_json({
                    'irises': round(user.get('irises', 0), 1),
                    'clicks': user.get('clicks', 0),
                    'first_name': user.get('first_name', 'Гость'),
                    'username': user.get('username', ''),
                    'gifts_count': len(user.get('gifts', [])),
                    'skins_count': len(user.get('skins', []))
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/admin/is_admin/'):
            try:
                user_id = self.path.split('/api/admin/is_admin/')[-1]
                self.send_json({'is_admin': is_admin_id(user_id)}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/users_list':
            stats = load_stats()
            users = []
            for uid, data in stats.items():
                users.append({
                    'id': uid,
                    'first_name': data.get('first_name', 'Аноним'),
                    'username': data.get('username', ''),
                    'irises': round(data.get('irises', 0), 1)
                })
            users.sort(key=lambda x: x['irises'], reverse=True)
            self.send_json(users[:200]); return

        if self.path.startswith('/api/admin/find_user'):
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                qs = parse_qs(parsed.query)
                q = (qs.get('q', [''])[0] or '').strip()
                admin_id = (qs.get('admin_id', [''])[0] or '').strip()
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                if not q:
                    self.send_json({'ok': False, 'error': 'empty_query'}); return
                result = None
                if q.lstrip('@').isdigit():
                    stats = load_stats()
                    uid = q.lstrip('@')
                    if uid in stats:
                        result = {'id': uid, **stats[uid]}
                else:
                    found = find_user_by_username(q)
                    if found:
                        result = {'id': found[0], **found[1]}
                if not result:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                self.send_json({'ok': True, 'user': {
                    'id': result['id'],
                    'first_name': result.get('first_name', 'Аноним'),
                    'username': result.get('username', ''),
                    'irises': round(result.get('irises', 0), 1),
                    'gifts_count': len(result.get('gifts', [])),
                    'skins_count': len(result.get('skins', []))
                }}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/stats':
            stats = load_stats()
            total_irises = sum(u.get('irises', 0) for u in stats.values())
            total_gifts = sum(len(u.get('gifts', [])) for u in stats.values())
            gifts_list = []
            for gid, g in GIFTS.items():
                gifts_list.append({'id': gid, 'name': g['name'], 'emoji': g['emoji'],
                                   'used': get_limit(gid), 'max': g.get('limit', MAX_LIMIT)})
            self.send_json({
                'users': len(stats),
                'total_irises': round(total_irises, 1),
                'total_gifts': total_gifts,
                'gifts_catalog': gifts_list
            }); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Darkgram is running')

    def do_POST(self):
        try:
            data = self.read_body()
        except:
            data = {}

        if self.path == '/api/click':
            try:
                user_id = str(data.get('user_id', ''))
                if not user_id:
                    self.send_json({'ok': False, 'error': 'no_user'}); return
                user = get_user(user_id)
                user['irises'] = round(user.get('irises', 0) + CLICK_REWARD, 2)
                user['clicks'] = user.get('clicks', 0) + 1
                update_user(user_id, user)
                self.send_json({'ok': True, 'irises': user['irises'], 'clicks': user['clicks']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/case/open':
            try:
                user_id = str(data.get('user_id', ''))
                if not user_id:
                    self.send_json({'ok': False, 'error': 'no_user'}); return
                user = get_user(user_id)
                if user.get('irises', 0) < CASE_PRICE:
                    self.send_json({'ok': False, 'error': 'not_enough'}); return
                gift = open_case(user_id)
                if not gift:
                    self.send_json({'ok': False, 'error': 'all_limits_reached'}); return
                user = get_user(user_id)
                user['irises'] = round(user.get('irises', 0) - CASE_PRICE, 2)
                update_user(user_id, user)
                self.send_json({'ok': True, 'gift': gift, 'irises': user['irises']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/skins/buy':
            try:
                user_id = str(data.get('user_id', ''))
                skin_id = data.get('skin_id')
                unique = data.get('unique')
                if not user_id or not skin_id or unique is None:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                parent, sdata = get_skin_by_id(skin_id)
                if not sdata:
                    self.send_json({'ok': False, 'error': 'skin_not_found'}); return
                if get_skin_limit(skin_id) >= MAX_LIMIT:
                    self.send_json({'ok': False, 'error': 'skin_limit_reached'}); return
                gift = find_gift_in_user(user_id, unique)
                if not gift or gift.get('id') != parent:
                    self.send_json({'ok': False, 'error': 'wrong_gift'}); return
                user = get_user(user_id)
                if user.get('irises', 0) < sdata['price']:
                    self.send_json({'ok': False, 'error': 'not_enough'}); return
                for s in user.get('skins', []):
                    if s.get('skin_id') == skin_id and s.get('unique') == unique:
                        self.send_json({'ok': False, 'error': 'already_owned'}); return
                user['irises'] = round(user.get('irises', 0) - sdata['price'], 2)
                user.setdefault('skins', []).append({
                    'skin_id': skin_id, 'unique': unique, 'bought_at': int(time.time() * 1000)
                })
                update_user(user_id, user)
                inc_skin_limit(skin_id)
                self.send_json({'ok': True, 'irises': user['irises']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/skins/apply':
            try:
                user_id = str(data.get('user_id', ''))
                skin_id = data.get('skin_id')
                unique = data.get('unique')
                if not user_id or unique is None:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                user = get_user(user_id)
                gift = find_gift_in_user(user_id, unique)
                if not gift:
                    self.send_json({'ok': False, 'error': 'gift_not_found'}); return
                if skin_id:
                    owned = any(s.get('skin_id') == skin_id and s.get('unique') == unique for s in user.get('skins', []))
                    if not owned:
                        self.send_json({'ok': False, 'error': 'not_owned'}); return
                gift['active_skin'] = skin_id
                update_user(user_id, user)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/market/sell':
            try:
                user_id = str(data.get('user_id', ''))
                unique = data.get('unique')
                price = float(data.get('price', 0))
                if not user_id or unique is None or price <= 0:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                gift = find_gift_in_user(user_id, unique)
                if not gift:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                if gift.get('on_market'):
                    self.send_json({'ok': False, 'error': 'already_on_market'}); return
                user = get_user(user_id)
                gift['on_market'] = True
                update_user(user_id, user)
                market = load_market()
                market.append({
                    'unique': unique, 'gift_id': gift.get('id'), 'name': gift.get('name'),
                    'emoji': gift.get('emoji'), 'rarity': gift.get('rarity'),
                    'base_price': gift.get('base_price', 100), 'price': price,
                    'seller_id': user_id, 'seller_name': user.get('first_name', 'Аноним'),
                    'seller_username': user.get('username', ''),
                    'listed_at': int(time.time() * 1000),
                    'active_skin': gift.get('active_skin')
                })
                save_market(market)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/market/cancel':
            try:
                user_id = str(data.get('user_id', ''))
                unique = data.get('unique')
                market = load_market()
                new_market = []
                found = False
                for lot in market:
                    if lot.get('unique') == unique and lot.get('seller_id') == user_id:
                        found = True; continue
                    new_market.append(lot)
                if not found:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                save_market(new_market)
                gift = find_gift_in_user(user_id, unique)
                if gift:
                    gift['on_market'] = False
                    user = get_user(user_id)
                    update_user(user_id, user)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/market/buy':
            try:
                buyer_id = str(data.get('user_id', ''))
                unique = data.get('unique')
                if not buyer_id or unique is None:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                market = load_market()
                lot = None
                for l in market:
                    if l.get('unique') == unique:
                        lot = l; break
                if not lot:
                    self.send_json({'ok': False, 'error': 'lot_not_found'}); return
                seller_id = lot.get('seller_id')
                if str(seller_id) == str(buyer_id):
                    self.send_json({'ok': False, 'error': 'own_lot'}); return
                price = float(lot.get('price', 0))
                buyer = get_user(buyer_id)
                if buyer.get('irises', 0) < price:
                    self.send_json({'ok': False, 'error': 'not_enough'}); return
                seller = get_user(seller_id)
                buyer['irises'] = round(buyer.get('irises', 0) - price, 2)
                buyer.setdefault('gifts', []).append({
                    'id': lot.get('gift_id'), 'name': lot.get('name'),
                    'emoji': lot.get('emoji'), 'rarity': lot.get('rarity'),
                    'unique': lot.get('unique'),
                    'base_price': lot.get('base_price', 100),
                    'opened_at': int(time.time() * 1000),
                    'on_market': False, 'bought_for': price,
                    'active_skin': lot.get('active_skin')
                })
                update_user(buyer_id, buyer)
                seller['irises'] = round(seller.get('irises', 0) + price, 2)
                seller['gifts'] = [g for g in seller.get('gifts', []) if g.get('unique') != unique]
                update_user(seller_id, seller)
                save_market([l for l in market if l.get('unique') != unique])
                self.send_json({'ok': True, 'price': price}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/gift/send':
            try:
                from_id = str(data.get('user_id', ''))
                to_id = str(data.get('to_user_id', ''))
                unique = data.get('unique')
                if not from_id or not to_id or unique is None:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                if str(to_id) == str(from_id):
                    self.send_json({'ok': False, 'error': 'self'}); return
                gift = find_gift_in_user(from_id, unique)
                if not gift:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                if gift.get('on_market'):
                    self.send_json({'ok': False, 'error': 'on_market'}); return
                sender = get_user(from_id)
                sender['gifts'] = [g for g in sender.get('gifts', []) if g.get('unique') != unique]
                update_user(from_id, sender)
                receiver = get_user(to_id)
                receiver.setdefault('gifts', []).append(gift)
                update_user(to_id, receiver)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/give_irises':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                target_id = str(data.get('target_id', ''))
                amount = float(data.get('amount', 0))
                if not target_id or amount == 0:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                target = get_user(target_id)
                target['irises'] = round(target.get('irises', 0) + amount, 2)
                update_user(target_id, target)
                self.send_json({'ok': True, 'irises': target['irises']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/take_irises':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                target_id = str(data.get('target_id', ''))
                amount = float(data.get('amount', 0))
                if not target_id or amount <= 0:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                target = get_user(target_id)
                target['irises'] = round(max(0, target.get('irises', 0) - amount), 2)
                update_user(target_id, target)
                self.send_json({'ok': True, 'irises': target['irises']}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/give_gift':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                target_id = str(data.get('target_id', ''))
                gift_id = data.get('gift_id', '')
                if not target_id or not gift_id:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                new_gift = create_gift_by_id(gift_id, admin=True)
                if not new_gift:
                    self.send_json({'ok': False, 'error': 'bad_gift'}); return
                target = get_user(target_id)
                target.setdefault('gifts', []).append(new_gift)
                update_user(target_id, target)
                self.send_json({'ok': True, 'gift': new_gift}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/broadcast':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                text = (data.get('text', '') or '').strip()
                if not text:
                    self.send_json({'ok': False, 'error': 'empty'}); return
                stats = load_stats()
                def do_broadcast():
                    for uid in list(stats.keys()):
                        try:
                            bot.send_message(int(uid), text, parse_mode='HTML')
                            time.sleep(0.05)
                        except: pass
                threading.Thread(target=do_broadcast, daemon=True).start()
                self.send_json({'ok': True, 'total': len(stats)}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/event/start':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                multiplier = int(data.get('multiplier', 2))
                bonus = int(data.get('bonus', 50))
                if multiplier < 1: multiplier = 1
                if multiplier > 10: multiplier = 10
                if bonus < 50: bonus = 50
                if bonus > 1500: bonus = 1500
                event = {'active': True, 'start': time.time(), 'multiplier': multiplier, 'bonus': bonus}
                save_json('event.json', event)
                stats = load_stats()
                for uid in stats:
                    stats[uid]['irises'] = round(stats[uid].get('irises', 0) + bonus, 2)
                save_stats(stats)
                self.send_json({'ok': True, 'multiplier': multiplier, 'bonus': bonus}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/admin/event/stop':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                save_json('event.json', {'active': False, 'start': 0, 'multiplier': 2, 'bonus': 50})
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        self.send_response(404)
        self.end_headers()

def run_http_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    get_user(user_id, first_name, username)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='Открыть Darkgram',
        web_app=types.WebAppInfo(url=f'{WEBAPP_URL}?user_id={user_id}')
    ))
    text = (
        f"<b>DARKGRAM</b>\n\n"
        f"Привет, <b>{first_name}</b>!\n\n"
        f"Кликай на ириску — получай ириски\n"
        f"Открывай кейсы — получай NFT\n"
        f"Покупай скины — украшай свои NFT\n"
        f"Торгуй NFT на рынке\n"
        f"Поднимайся в топ\n\n"
        f"Нажми кнопку ниже, чтобы играть"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        f"<b>ПОМОЩЬ</b>\n\n"
        f"<b>Кликер</b> — тапай ириску, получай +0.1 за клик\n"
        f"<b>Кейсы</b> — открывай за 100 ирисок, получай NFT\n"
        f"<b>Скины</b> — покупай и применяй к NFT\n"
        f"<b>Рынок</b> — покупай и продавай NFT\n"
        f"<b>Топ</b> — лучшие игроки\n\n"
        f"<b>Правила:</b>\n"
        f"• Не читерить\n• Не оскорблять игроков\n"
        f"• Ириски — игровая валюта без реальной ценности\n\n"
        f"<b>Конфиденциальность:</b>\n"
        f"Храним Telegram ID, имя, username — только для игры.\n\n"
        f"Открыть игру — /start"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    user_id = message.from_user.id
    user = get_user(user_id, message.from_user.first_name, message.from_user.username)
    text = (
        f"<b>ПРОФИЛЬ</b>\n\n"
        f"<b>{user.get('first_name')}</b>\n"
        f"{('@'+user['username']) if user.get('username') else '—'}\n\n"
        f"Ириски: <b>{round(user.get('irises', 0), 1)}</b>\n"
        f"Кликов: <b>{user.get('clicks', 0)}</b>\n"
        f"NFT: <b>{len(user.get('gifts', []))}</b>\n"
        f"Скинов: <b>{len(user.get('skins', []))}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['top'])
def cmd_top(message):
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "Пока пусто."); return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('irises', 0), reverse=True)[:15]
    text = "<b>ТОП</b>\n\n"
    for i, (uid, data) in enumerate(sorted_stats, 1):
        name = data.get('first_name') or 'Аноним'
        if data.get('username'): name = f"@{data['username']}"
        medal = '🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'<b>{i}.</b>'
        text += f"{medal} {name} — {round(data.get('irises', 0), 1)}\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['post'])
def cmd_post(message):
    user_id = message.from_user.id
    if not is_admin_id(user_id):
        return
    text = message.text.replace('/post', '').strip()
    if not text:
        bot.send_message(message.chat.id, "Использование: /post Текст рассылки")
        return
    stats = load_stats()
    sent = 0
    for uid in list(stats.keys()):
        try:
            bot.send_message(int(uid), text, parse_mode='HTML')
            sent += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"Разослано: {sent} из {len(stats)}")

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start', 'Открыть игру'),
            types.BotCommand('help', 'Помощь'),
            types.BotCommand('profile', 'Профиль'),
            types.BotCommand('top', 'Топ'),
        ])
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()       
