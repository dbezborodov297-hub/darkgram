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

WEBAPP_URL = 'https://darkgram-fkc2.onrender.com/'
ADMIN_IDS = [8907438590]

CLICK_REWARD = 0.1
CASE_PRICE = 100

GIFTS = {
    'bear':     {'name': 'Медведь',  'emoji': '🐻', 'rarity': 'Common',    'chance': 25, 'price': 80},
    'rose':     {'name': 'Роза',     'emoji': '🌹', 'rarity': 'Common',    'chance': 24, 'price': 80},
    'cake':     {'name': 'Торт',     'emoji': '🎂', 'rarity': 'Common',    'chance': 20, 'price': 70},
    'heart':    {'name': 'Сердце',   'emoji': '❤️', 'rarity': 'Rare',      'chance': 14, 'price': 150},
    'star':     {'name': 'Звезда',   'emoji': '⭐', 'rarity': 'Rare',      'chance': 9,  'price': 180},
    'crown':    {'name': 'Корона',   'emoji': '👑', 'rarity': 'Epic',      'chance': 4,  'price': 300},
    'diamond':  {'name': 'Алмаз',    'emoji': '💎', 'rarity': 'Epic',      'chance': 2,  'price': 350},
    'ring':     {'name': 'Кольцо',   'emoji': '💍', 'rarity': 'Legendary', 'chance': 1,  'price': 450},
    'rocket':   {'name': 'Ракета',   'emoji': '🚀', 'rarity': 'Legendary', 'chance': 1,  'price': 500},
    'beach':    {'name': 'Пляж',     'emoji': '🏖️', 'rarity': 'Legendary', 'chance': 0.5,'price': 550},
    'rosette':  {'name': 'Розетка',  'emoji': '🏵️', 'rarity': 'Legendary', 'chance': 0.5,'price': 650},
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

def is_admin_id(user_id):
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

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
            'gifts': []
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        if 'clicks' not in stats[key]: stats[key]['clicks'] = 0
        if 'gifts' not in stats[key]: stats[key]['gifts'] = []
        if 'irises' not in stats[key]: stats[key]['irises'] = 0.0
    save_stats(stats)
    return stats[key]

def update_user(user_id, data):
    stats = load_stats()
    stats[str(user_id)] = data
    save_stats(stats)

def open_case(user_id):
    gifts_list = list(GIFTS.items())
    total = sum(g[1]['chance'] for g in gifts_list)
    r = random.uniform(0, total)
    acc = 0
    chosen_id = 'bear'
    for gid, gdata in gifts_list:
        acc += gdata['chance']
        if r <= acc:
            chosen_id = gid
            break
    gift = GIFTS[chosen_id]
    unique_id = random.randint(1, 99999)
    user = get_user(user_id)
    gift_record = {
        'id': chosen_id, 'name': gift['name'], 'emoji': gift['emoji'],
        'rarity': gift['rarity'], 'unique': unique_id,
        'base_price': gift.get('price', 100),
        'opened_at': int(time.time() * 1000), 'on_market': False
    }
    user['gifts'].append(gift_record)
    update_user(user_id, user)
    return gift_record

def create_gift_by_id(gift_id):
    if gift_id not in GIFTS: return None
    gift = GIFTS[gift_id]
    return {
        'id': gift_id, 'name': gift['name'], 'emoji': gift['emoji'],
        'rarity': gift['rarity'], 'unique': random.randint(1, 99999),
        'base_price': gift.get('price', 100),
        'opened_at': int(time.time() * 1000), 'on_market': False
    }

def find_gift_in_user(user_id, unique):
    user = get_user(user_id)
    for g in user.get('gifts', []):
        if g.get('unique') == unique:
            return g
    return None

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
        paths = [
            'public/index.html',
            'index.html',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'index.html'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'),
            os.path.join(os.getcwd(), 'public', 'index.html'),
            os.path.join(os.getcwd(), 'index.html'),
        ]
        for path in paths:
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
                print('HTML served from:', path)
                return
            except Exception:
                continue
        print('HTML not found in paths:', paths)
        print('CWD:', os.getcwd())
        try:
            print('Files in CWD:', os.listdir(os.getcwd()))
            if os.path.exists('public'):
                print('Files in public:', os.listdir('public'))
        except Exception as e:
            print('List error:', e)
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
                catalog.append({'id': gid, 'name': g['name'], 'emoji': g['emoji'],
                                'rarity': g['rarity'], 'price': g.get('price', 100)})
            self.send_json(catalog); return

        if self.path.startswith('/api/gifts/'):
            try:
                user_id = self.path.split('/api/gifts/')[-1]
                user = get_user(user_id)
                self.send_json(user.get('gifts', [])); return
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
                    'gifts_count': len(user.get('gifts', []))
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/admin/is_admin/'):
            try:
                user_id = self.path.split('/api/admin/is_admin/')[-1]
                self.send_json({'is_admin': is_admin_id(user_id)}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

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
                    'gifts_count': len(result.get('gifts', []))
                }}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

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
                user['irises'] = round(user.get('irises', 0) - CASE_PRICE, 2)
                update_user(user_id, user)
                gift = open_case(user_id)
                self.send_json({'ok': True, 'gift': gift, 'irises': user.get('irises', 0)}); return
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
                market = load_market()
                for lot in market:
                    if lot.get('unique') == unique and lot.get('seller_id') == user_id:
                        self.send_json({'ok': False, 'error': 'already_on_market'}); return
                user = get_user(user_id)
                gift['on_market'] = True
                update_user(user_id, user)
                lot = {'unique': unique, 'gift_id': gift.get('id'), 'name': gift.get('name'),
                       'emoji': gift.get('emoji'), 'rarity': gift.get('rarity'),
                       'base_price': gift.get('base_price', 100), 'price': price,
                       'seller_id': user_id, 'seller_name': user.get('first_name', 'Аноним'),
                       'seller_username': user.get('username', ''),
                       'listed_at': int(time.time() * 1000)}
                market.append(lot)
                save_market(market)
                self.send_json({'ok': True, 'lot': lot}); return
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
                buyer['gifts'].append({'id': lot.get('gift_id'), 'name': lot.get('name'),
                                       'emoji': lot.get('emoji'), 'rarity': lot.get('rarity'),
                                       'unique': lot.get('unique'),
                                       'base_price': lot.get('base_price', 100),
                                       'opened_at': int(time.time() * 1000),
                                       'on_market': False, 'bought_for': price})
                update_user(buyer_id, buyer)
                seller['irises'] = round(seller.get('irises', 0) + price, 2)
                seller['gifts'] = [g for g in seller.get('gifts', []) if g.get('unique') != unique]
                update_user(seller_id, seller)
                market = [l for l in market if l.get('unique') != unique]
                save_market(market)
                self.send_json({'ok': True, 'price': price}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/gift/send':
            try:
                from_id = str(data.get('user_id', ''))
                to_username = (data.get('to_username', '') or '').strip().lstrip('@')
                unique = data.get('unique')
                if not from_id or not to_username or unique is None:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                found = find_user_by_username(to_username)
                if not found:
                    self.send_json({'ok': False, 'error': 'user_not_found'}); return
                to_id, _ = found
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
                gift['on_market'] = False
                receiver = get_user(to_id)
                receiver['gifts'].append(gift)
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

        if self.path == '/api/admin/give_gift':
            try:
                admin_id = str(data.get('admin_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                target_id = str(data.get('target_id', ''))
                gift_id = data.get('gift_id', '')
                if not target_id or not gift_id:
                    self.send_json({'ok': False, 'error': 'bad_data'}); return
                new_gift = create_gift_by_id(gift_id)
                if not new_gift:
                    self.send_json({'ok': False, 'error': 'bad_gift'}); return
                target = get_user(target_id)
                target['gifts'].append(new_gift)
                update_user(target_id, target)
                self.send_json({'ok': True, 'gift': new_gift}); return
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
        text='🍬 Открыть Darkgram',
        web_app=types.WebAppInfo(url=f'{WEBAPP_URL}?user_id={user_id}')
    ))
    text = (
        f"🌟 <b>DARKGRAM</b> 🌟\n\n"
        f"👋 Привет, <b>{first_name}</b>!\n\n"
        f"🍬 Кликай на ириску — получай ириски\n"
        f"🎁 Открывай кейсы — получай NFT\n"
        f"🏪 Торгуй NFT на рынке\n"
        f"🏆 Поднимайся в топ\n\n"
        f"👇 Жми кнопку, чтобы играть"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        f"❓ <b>ПОМОЩЬ</b>\n\n"
        f"🍬 <b>Кликер</b> — тапай ириску, получай +0.1 за клик\n"
        f"🎁 <b>Кейсы</b> — открывай за 100 ирисок, получай NFT\n"
        f"🏪 <b>Рынок</b> — покупай и продавай NFT\n"
        f"🏆 <b>Топ</b> — лучшие игроки\n\n"
        f"📋 <b>Правила:</b>\n"
        f"• Не читерить\n• Не оскорблять игроков\n"
        f"• Ириски — игровая валюта без реальной ценности\n\n"
        f"🔒 <b>Конфиденциальность:</b>\n"
        f"Храним Telegram ID, имя, username — только для игры. "
        f"Не передаём третьим лицам.\n\n"
        f"🎮 Открыть игру — /start"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    user_id = message.from_user.id
    user = get_user(user_id, message.from_user.first_name, message.from_user.username)
    text = (
        f"👤 <b>ПРОФИЛЬ</b>\n\n"
        f"🌟 <b>{user.get('first_name')}</b>\n"
        f"📛 {('@'+user['username']) if user.get('username') else '—'}\n\n"
        f"🍬 Ириски: <b>{round(user.get('irises', 0), 1)}</b>\n"
        f"👆 Кликов: <b>{user.get('clicks', 0)}</b>\n"
        f"🎁 NFT: <b>{len(user.get('gifts', []))}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['top'])
def cmd_top(message):
    stats = load_stats()
    if not stats:
        bot.send_message(message.chat.id, "🏆 Пока пусто."); return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1].get('irises', 0), reverse=True)[:15]
    text = "🏆 <b>ТОП</b>\n\n"
    for i, (uid, data) in enumerate(sorted_stats, 1):
        name = data.get('first_name') or 'Аноним'
        if data.get('username'): name = f"@{data['username']}"
        medal = '🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'<b>{i}.</b>'
        text += f"{medal} {name} — {round(data.get('irises', 0), 1)} 🍬\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')

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
