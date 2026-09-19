import telebot
import json
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types

STATS_FILE = 'stats.json'
POSTS_FILE = 'posts_api.json'
GROUPS_FILE = 'groups.json'
MESSAGES_FILE = 'messages.json'
ONLINE_FILE = 'online_api.json'

ADMIN_IDS = [8907438590]
WEBAPP_URL = 'https://darkgram-fkc2.onrender.com/'
ONLINE_TIMEOUT = 300

TOKEN = '8901361348:AAFH5WEtT3gJy_rd2TYTbX1nDqCzOpMJ3Kw'

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
def load_messages(): return load_json(MESSAGES_FILE, {})
def save_messages(d): save_json(MESSAGES_FILE, d)
def load_online(): return load_json(ONLINE_FILE, {})
def save_online(d): save_json(ONLINE_FILE, d)

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

def mark_online(user_id, first_name='', username=''):
    try:
        online = load_online()
        online[str(user_id)] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'last_seen': int(time.time())
        }
        now = int(time.time())
        online = {k: v for k, v in online.items() if now - v.get('last_seen', 0) < ONLINE_TIMEOUT}
        save_online(online)
    except:
        pass

def get_online_count():
    online = load_online()
    now = int(time.time())
    return len([u for u in online.values() if now - u.get('last_seen', 0) < ONLINE_TIMEOUT])

def get_user(user_id, first_name='Аноним', username=''):
    stats = load_stats()
    key = str(user_id)
    if key not in stats:
        stats[key] = {
            'first_name': first_name or 'Аноним',
            'username': username or '',
            'bio': '', 'phone': '', 'avatar': ''
        }
    else:
        stats[key]['first_name'] = first_name or stats[key].get('first_name', 'Аноним')
        stats[key]['username'] = username or stats[key].get('username', '')
        if 'bio' not in stats[key]: stats[key]['bio'] = ''
        if 'phone' not in stats[key]: stats[key]['phone'] = ''
        if 'avatar' not in stats[key]: stats[key]['avatar'] = ''
    save_stats(stats)
    return stats[key]

def update_user(user_id, data):
    stats = load_stats()
    stats[str(user_id)] = data
    save_stats(stats)

def find_user_by_username(username):
    if not username: return None
    uname = username.lower().lstrip('@')
    stats = load_stats()
    for uid, data in stats.items():
        if (data.get('username') or '').lower() == uname:
            return uid, data
    return None

def chat_key(a, b):
    a, b = str(a), str(b)
    return '_'.join(sorted([a, b]))

def get_chat(a, b):
    messages = load_messages()
    return messages.get(chat_key(a, b), [])

def add_message(from_id, to_id, text):
    messages = load_messages()
    key = chat_key(from_id, to_id)
    if key not in messages:
        messages[key] = []
    msg = {
        'from': str(from_id),
        'to': str(to_id),
        'text': text,
        'ts': int(time.time() * 1000)
    }
    messages[key].append(msg)
    save_messages(messages)
    return msg

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
        for path in ['public/index.html', 'index.html']:
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

        if self.path == '/api/online':
            self.send_json({'count': get_online_count()}); return

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
                    'phone': u.get('phone', ''),
                    'avatar': u.get('avatar', '')
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/is_admin/'):
            try:
                user_id = self.path.split('/api/is_admin/')[-1]
                self.send_json({'is_admin': is_admin_id(user_id)}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/find/'):
            try:
                username = self.path.split('/api/find/')[-1]
                found = find_user_by_username(username)
                if not found:
                    self.send_json({'ok': False, 'error': 'not_found'}); return
                uid, u = found
                self.send_json({
                    'ok': True,
                    'user': {
                        'id': uid,
                        'first_name': u.get('first_name', 'Аноним'),
                        'username': u.get('username', ''),
                        'bio': u.get('bio', ''),
                        'avatar': u.get('avatar', '')
                    }
                }); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/chat/'):
            try:
                rest = self.path.split('/api/chat/')[-1]
                parts = rest.split('/')
                if len(parts) < 2:
                    self.send_json({'error': 'bad'}); return
                me, other = parts[0], parts[1]
                since = 0
                if len(parts) >= 3:
                    try: since = int(parts[2])
                    except: since = 0
                messages = get_chat(me, other)
                if since > 0:
                    messages = [m for m in messages if m.get('ts', 0) > since]
                self.send_json(messages); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path.startswith('/api/dialogs/'):
            try:
                user_id = str(self.path.split('/api/dialogs/')[-1])
                messages = load_messages()
                dialogs = {}
                for key, msgs in messages.items():
                    if not msgs: continue
                    parts = key.split('_')
                    if user_id not in parts: continue
                    other = parts[0] if parts[1] == user_id else parts[1]
                    last = msgs[-1]
                    if other not in dialogs or last.get('ts', 0) > dialogs[other].get('ts', 0):
                        dialogs[other] = last
                stats = load_stats()
                result = []
                for other_id, last in dialogs.items():
                    u = stats.get(other_id, {})
                    result.append({
                        'id': other_id,
                        'first_name': u.get('first_name', 'Аноним'),
                        'username': u.get('username', ''),
                        'avatar': u.get('avatar', ''),
                        'last_text': last.get('text', ''),
                        'last_ts': last.get('ts', 0)
                    })
                result.sort(key=lambda x: x['last_ts'], reverse=True)
                self.send_json(result); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Darkgram Bot is running')

    def do_POST(self):
        data = self.read_body()

        if self.path == '/api/heartbeat':
            try:
                user_id = str(data.get('user_id', ''))
                if user_id:
                    mark_online(user_id, data.get('first_name', ''), data.get('username', ''))
                self.send_json({'ok': True, 'online': get_online_count()}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/profile/save':
            try:
                user_id = str(data.get('user_id', ''))
                bio = str(data.get('bio', ''))[:500]
                phone = str(data.get('phone', ''))[:30]
                avatar = data.get('avatar', '')
                if not user_id:
                    self.send_json({'ok': False, 'error': 'no_user'}); return
                u = get_user(user_id)
                u['bio'] = bio
                u['phone'] = phone
                if avatar: u['avatar'] = avatar
                update_user(user_id, u)
                self.send_json({'ok': True}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/chat/send':
            try:
                from_id = str(data.get('from_id', ''))
                to_id = str(data.get('to_id', ''))
                text = str(data.get('text', '')).strip()[:1000]
                if not from_id or not to_id or not text:
                    self.send_json({'ok': False, 'error': 'bad'}); return
                if from_id == to_id:
                    self.send_json({'ok': False, 'error': 'self'}); return
                msg = add_message(from_id, to_id, text)
                self.send_json({'ok': True, 'msg': msg}); return
            except Exception as e:
                self.send_json({'error': str(e)}, 500); return

        if self.path == '/api/post/create':
            try:
                admin_id = str(data.get('user_id', ''))
                if not is_admin_id(admin_id):
                    self.send_json({'ok': False, 'error': 'not_admin'}); return
                text = str(data.get('text', '')).strip()
                media = data.get('media', '')
                media_type = data.get('media_type', '')
                if not text and not media:
                    self.send_json({'ok': False, 'error': 'empty'}); return
                post = {
                    'id': 'p_' + str(int(time.time() * 1000)),
                    'text': text, 'media': media, 'media_type': media_type,
                    'created_at': int(time.time() * 1000)
                }
                posts = load_posts()
                posts.append(post)
                save_posts(posts)
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
    media = post.get('media', '')
    media_type = post.get('media_type', '')
    for cid in list(groups.keys()):
        try:
            send_post_to_chat(int(cid), text, media, media_type)
            time.sleep(0.05)
        except: pass
    for uid in list(stats.keys()):
        try:
            send_post_to_chat(int(uid), text, media, media_type)
            time.sleep(0.05)
        except: pass

def send_post_to_chat(chat_id, text, media, media_type):
    try:
        if media and media_type == 'photo':
            bot.send_photo(chat_id, media, caption=text, parse_mode='HTML')
        elif media and media_type == 'video':
            bot.send_video(chat_id, media, caption=text, parse_mode='HTML')
        elif media:
            bot.send_document(chat_id, media, caption=text, parse_mode='HTML')
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
    mark_online(uid, message.from_user.first_name, message.from_user.username)
    get_user(uid, message.from_user.first_name, message.from_user.username)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        text='👤 Открыть профиль',
        web_app=types.WebAppInfo(url=f'{WEBAPP_URL}?user_id={uid}')
    ))
    text = (
        f"<b>DARKGRAM</b>\n\n"
        f"Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Открой профиль — там можно заполнить информацию о себе, общаться с другими и смотреть онлайн."
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
        f"• Загрузить аватарку\n"
        f"• Искать юзеров по @username\n"
        f"• Общаться в чате\n"
        f"• Смотреть онлайн"
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
