import telebot
import json
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
POSTS_FILE = 'posts_api.json'
GROUPS_FILE = 'groups.json'

ADMIN_IDS = [8907438590]

WEBAPP_URL = 'https://darkgram-fkc2.onrender.com/'

TOKEN = '8901361348:AAGYbuQL1Lm5kfXo4Awqd5z4BX8Sn4peF4o'

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
def load_posts(): return load_json(POSTS_FILE, [])
def save_posts(d): save_json(POSTS_FILE, d)
def load_groups(): return load_json(GROUPS_FILE, {})
def save_groups(d): save_json(GROUPS_FILE, d)

def is_admin_id(user_id):
    try:
        return int(user_id) in ADMIN_IDS
    except:
        return False

def remember_group(chat):
    try:
        if chat.type in ('group', 'supergroup'):
            groups = load_groups()
            cid = str(chat.id)
            if cid not in groups:
                groups[cid] = {'title': chat.title or 'Группа', 'added': int(time.time())}
                save_groups(groups)
    except:
        pass

def get_user(user_id, first_name='Аноним', username=''):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'bio': '',
            'phone': ''
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        if 'bio' not in stats[key]: stats[key]['bio'] = ''
        if 'phone' not in stats[key]: stats[key]['phone'] = ''
    save_stats(stats)
    return stats[key]

def update_user(user_id, data):
    stats = load_stats()
    stats[str(user_id)] = data
    save_stats(stats)

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
            except:
                continue
        self.send_response(404)
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0: return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except:
            return {}

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/index.html') or self.path.startswith('/?'):
            self.send_html(); return

        if self.path.startswith('/api/profile/'):
            try:
                user_id = self.path.split('/api/profile/')[-1]
                stats = load_stats()
                u = stats.get(user_id, {})
                self.send_json({
                    'id': user_id,
                    'first_name': u.get('first_name', 'Аноним'),
                    'username': u.get('username', ''),
                    'bio': u.get('bio', ''),
                    'phone': u.get('phone', '')
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/is_admin/'):
            try:
                user_id = self.path.split('/api/is_admin/')[-1]
                self.send_json({'is_admin': is_admin_id(user_id)}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/groups':
            self.send_json(load_groups()); return

        if self.path == '/api/posts':
            posts = load_posts()
            posts.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            self.send_json(posts[:20]); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Darkgram Bot is running')

    def do_POST(self):
        data = self.read_body()

        if self.path == '/api/profile/save':
            try:
                user_id = str(data.get('user_id', ''))
                bio = str(data.get('bio', ''))[:500]
                phone = str(data.get('phone', ''))[:30]
                if not user_id:
                    self.send_json({'ok': False, 'error': 'no_user'}); return
                u = get_user(user_id)
                u['bio'] = bio
                u['phone'] = phone
                update_user(user_id, u)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/post/create':
            try:
                admin_id = str(data.get('user_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                text = str(data.get('text', '')).strip()
                image = data.get('image', '')
                if not text and not image:
                    self.send_json({'ok': False, 'error': 'empty'}); return
                post = {
                    'id': 'p_' + str(int(time.time() * 1000)),
                    'text': text,
                    'image': image,
                    'created_at': int(time.time() * 1000)
                }
                posts = load_posts()
                posts.append(post)
                save_posts(posts)
                # Рассылка
                threading.Thread(target=broadcast_post, args=[post]).start()
                self.send_json({'ok': True, 'post': post}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        self.send_response(404)
        self.end_headers()

def broadcast_post(post):
    stats = load_stats()
    groups = load_groups()
    text = post.get('text', '')
    image = post.get('image', '')
    for cid in list(groups.keys()):
        try:
            send_post_to_chat(int(cid), text, image)
            time.sleep(0.05)
        except: pass
    for uid in list(stats.keys()):
        try:
            send_post_to_chat(int(uid), text, image)
            time.sleep(0.05)
        except: pass

def send_post_to_chat(chat_id, text, image):
    try:
        if image:
            bot.send_photo(chat_id, image, caption=text, parse_mode='HTML')
        else:
            bot.send_message(chat_id, text, parse_mode='HTML')
    except:
        try:
            bot.send_message(chat_id, text)
        except:
            pass

def run_http():
    port = int(os.environ.get('PORT', 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

@bot.message_handler(commands=['start'])
def cmd_start(message):
    remember_group(message.chat)
    uid = message.from_user.id
    get_user(uid, message.from_user.first_name, message.from_user.username)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='👤 Открыть профиль',
        web_app=types.WebAppInfo(url=f'{WEBAPP_URL}?user_id={uid}')
    ))

    text = (
        f"<b>DARKGRAM</b>\n\n"
        f"Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Открой свой профиль — там можно заполнить информацию о себе."
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(commands=['help'])
def cmd_help(message):
    remember_group(message.chat)
    text = (
        f"<b>ПОМОЩЬ</b>\n\n"
        f"👤 /start — открыть профиль в Mini App\n\n"
        f"В профиле можно:\n"
        f"• Указать «О себе»\n"
        f"• Указать номер телефона\n"
        f"• Посмотреть свой ID и @username"
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def set_commands():
    try:
        bot.set_my_commands([
            types.BotCommand('start', 'Открыть профиль'),
            types.BotCommand('help', 'Помощь'),
        ])
    except: pass

set_commands()
print('Darkgram Bot запущен')
bot.infinity_polling()
