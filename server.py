import json
import os
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'
CONTESTS_FILE = 'contests.json'
APPS_FILE = 'applications.json'
ADMINS_FILE = 'admins.json'
MESSAGES_FILE = 'messages.json'
COMMENTS_FILE = 'comments.json'

ADMIN_IDS = [8907438590]

ONLINE = {}
ONLINE_LOCK = threading.Lock()
ONLINE_TIMEOUT = 60

DEFAULT_PERMS = {
    'posts': True,
    'contests': True,
    'applications': True,
    'delete': True,
    'stats': True,
    'admins': False,
}


def load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return default


def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'save {path} err:', e)


def get_user(uid):
    users = load_json(USERS_FILE, {})
    key = str(uid)
    if key not in users:
        users[key] = {
            'uid': uid, 'name': '', 'username': '',
            'joined': int(time.time()), 'total_time': 0, 'last_seen': 0,
            'posts_count': 0, 'applications_count': 0,
            'accepted': 0, 'rejected': 0,
            'avatar': None, 'avatar_bg': None,
            'chat_wallpaper': None,
            'chat_font': 'sf',
            'chat_bubble_color': 'blue',
            'chat_notifications': True,
            'chat_read_receipts': True,
            'language': 'ru',
            'blocked': [],
            'contacts': [],
            'pinned_chats': [],
        }
        save_json(USERS_FILE, users)
    return users[key]


def save_user(uid, data):
    users = load_json(USERS_FILE, {})
    users[str(uid)] = data
    save_json(USERS_FILE, users)


def get_admins():
    admins = load_json(ADMINS_FILE, {})
    for aid in ADMIN_IDS:
        if str(aid) not in admins:
            admins[str(aid)] = {
                'uid': aid, 'name': 'Главный админ',
                'main': True, 'perms': dict(DEFAULT_PERMS),
            }
    for aid, a in admins.items():
        if 'perms' not in a:
            a['perms'] = dict(DEFAULT_PERMS)
        if 'main' not in a:
            a['main'] = False
    return admins


def is_admin(uid):
    return str(uid) in get_admins()


def has_perm(uid, perm):
    admins = get_admins()
    a = admins.get(str(uid))
    if not a: return False
    if a.get('main'): return True
    return a.get('perms', {}).get(perm, False)


def save_admins(d):
    save_json(ADMINS_FILE, d)


def public_user(u):
    return {
        'uid': u.get('uid'),
        'name': u.get('name', ''),
        'username': u.get('username', ''),
        'avatar': u.get('avatar'),
        'is_admin': is_admin(u.get('uid')),
        'joined': u.get('joined', 0),
    }


@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


# ============ PLAYER ============
@app.route('/api/player', methods=['POST', 'GET'])
def api_player():
    if request.method == 'POST':
        d = request.json or {}
        uid = d.get('uid'); name = d.get('name', ''); username = d.get('username', '')
    else:
        uid = request.args.get('uid')
        name = request.args.get('name', '')
        username = request.args.get('username', '')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    if name: u['name'] = name
    if username: u['username'] = username
    save_user(uid, u)
    admins = get_admins()
    me_admin = admins.get(str(uid), {})
    return jsonify({
        'uid': u['uid'], 'name': u['name'], 'username': u.get('username', ''),
        'joined': u['joined'], 'total_time': u['total_time'],
        'posts_count': u.get('posts_count', 0),
        'applications_count': u.get('applications_count', 0),
        'accepted': u.get('accepted', 0), 'rejected': u.get('rejected', 0),
        'avatar': u.get('avatar'),
        'avatar_bg': u.get('avatar_bg'),
        'chat_wallpaper': u.get('chat_wallpaper'),
        'chat_font': u.get('chat_font', 'sf'),
        'chat_bubble_color': u.get('chat_bubble_color', 'blue'),
        'chat_notifications': u.get('chat_notifications', True),
        'chat_read_receipts': u.get('chat_read_receipts', True),
        'language': u.get('language', 'ru'),
        'blocked': u.get('blocked', []),
        'contacts': u.get('contacts', []),
        'pinned_chats': u.get('pinned_chats', []),
        'is_admin': is_admin(uid),
        'is_main_admin': me_admin.get('main', False),
        'perms': me_admin.get('perms', {}),
    })


@app.route('/api/user/<uid>')
def api_user_by_id(uid):
    users = load_json(USERS_FILE, {})
    if str(uid) not in users:
        return jsonify({'error': 'not found'}), 404
    return jsonify(public_user(users[str(uid)]))


@app.route('/api/users/search')
def api_users_search():
    q = (request.args.get('q') or '').strip().lower().replace('@', '')
    my_uid = request.args.get('uid')
    if not q: return jsonify([])
    users = load_json(USERS_FILE, {})
    results = []
    for uid, u in users.items():
        if str(uid) == str(my_uid): continue
        name = (u.get('name') or '').lower()
        uname = (u.get('username') or '').lower()
        if q in name or q in uname or q == str(uid):
            results.append(public_user(u))
        if len(results) >= 30: break
    results.sort(key=lambda u: (
        0 if u['username'].lower().startswith(q) else 1,
        0 if u['name'].lower().startswith(q) else 1,
        u['name'].lower()
    ))
    return jsonify(results[:20])


@app.route('/api/save_profile', methods=['POST'])
def api_save_profile():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    for field in ['avatar', 'avatar_bg', 'chat_wallpaper', 'chat_font',
                  'chat_bubble_color', 'chat_notifications', 'chat_read_receipts',
                  'language', 'blocked', 'contacts', 'pinned_chats']:
        if field in d:
            u[field] = d[field]
    save_user(uid, u)
    return jsonify({'ok': True})


@app.route('/api/block', methods=['POST'])
def api_block():
    d = request.json or {}
    uid = d.get('uid'); target = str(d.get('target'))
    if not uid or not target: return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    blocked = u.get('blocked', [])
    if target in blocked:
        blocked.remove(target); action = 'unblocked'
    else:
        blocked.append(target); action = 'blocked'
    u['blocked'] = blocked
    save_user(uid, u)
    return jsonify({'ok': True, 'action': action, 'blocked': blocked})


@app.route('/api/contact', methods=['POST'])
def api_contact():
    d = request.json or {}
    uid = d.get('uid'); target = str(d.get('target'))
    if not uid or not target: return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    contacts = u.get('contacts', [])
    if target in contacts:
        contacts.remove(target); action = 'removed'
    else:
        contacts.append(target); action = 'added'
    u['contacts'] = contacts
    save_user(uid, u)
    return jsonify({'ok': True, 'action': action, 'contacts': contacts})


@app.route('/api/pin_chat', methods=['POST'])
def api_pin_chat():
    d = request.json or {}
    uid = d.get('uid'); target = str(d.get('target'))
    if not uid or not target: return jsonify({'error': 'bad'}), 400
    u = get_user(uid)
    pinned = u.get('pinned_chats', [])
    if target in pinned:
        pinned.remove(target); action = 'unpinned'
    else:
        pinned.append(target); action = 'pinned'
    u['pinned_chats'] = pinned
    save_user(uid, u)
    return jsonify({'ok': True, 'action': action, 'pinned': pinned})


@app.route('/api/ping', methods=['POST'])
def api_ping():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    now = int(time.time())
    with ONLINE_LOCK:
        ONLINE[str(uid)] = now
    u = get_user(uid)
    last_seen = u.get('last_seen', 0)
    if last_seen > 0:
        delta = now - last_seen
        if 0 < delta < 300:
            u['total_time'] = u.get('total_time', 0) + delta
    u['last_seen'] = now
    save_user(uid, u)
    return jsonify({'ok': True})


@app.route('/api/online')
def api_online():
    now = time.time()
    with ONLINE_LOCK:
        active = [u for u, t in ONLINE.items() if now - t < ONLINE_TIMEOUT]
    return jsonify({'count': len(active)})


# ============ POSTS ============
@app.route('/api/posts')
def api_posts():
    posts = load_json(POSTS_FILE, [])
    posts.sort(key=lambda x: x.get('created', 0), reverse=True)
    comments = load_json(COMMENTS_FILE, {})
    for p in posts[:50]:
        p['comments_count'] = len(comments.get(str(p.get('id')), []))
    return jsonify(posts[:50])


@app.route('/api/posts/create', methods=['POST'])
def api_posts_create():
    d = request.json or {}
    uid = d.get('uid')
    if not has_perm(uid, 'posts'): return jsonify({'error': 'Нет доступа'}), 403
    text = (d.get('text') or '').strip()
    image = d.get('image')
    if not text and not image: return jsonify({'error': 'Пусто'}), 400
    posts = load_json(POSTS_FILE, [])
    p = {
        'id': int(time.time() * 1000), 'author_id': uid,
        'author_name': d.get('name', 'Админ'), 'text': text, 'image': image,
        'created': int(time.time()), 'likes': 0,
    }
    posts.append(p)
    save_json(POSTS_FILE, posts)
    u = get_user(uid)
    u['posts_count'] = u.get('posts_count', 0) + 1
    save_user(uid, u)
    return jsonify({'ok': True, 'post': p})


@app.route('/api/posts/delete', methods=['POST'])
def api_posts_delete():
    d = request.json or {}
    if not has_perm(d.get('uid'), 'delete'): return jsonify({'error': 'Нет доступа'}), 403
    pid = d.get('post_id')
    posts = load_json(POSTS_FILE, [])
    posts = [p for p in posts if p.get('id') != pid]
    save_json(POSTS_FILE, posts)
    comments = load_json(COMMENTS_FILE, {})
    if str(pid) in comments:
        del comments[str(pid)]
        save_json(COMMENTS_FILE, comments)
    return jsonify({'ok': True})


# ============ COMMENTS ============
@app.route('/api/comments/<post_id>')
def api_comments_get(post_id):
    comments = load_json(COMMENTS_FILE, {})
    arr = comments.get(str(post_id), [])
    arr.sort(key=lambda x: x.get('created', 0))
    return jsonify(arr)


@app.route('/api/comments/add', methods=['POST'])
def api_comments_add():
    d = request.json or {}
    uid = d.get('uid')
    post_id = str(d.get('post_id'))
    text = (d.get('text') or '').strip()
    if not uid or not post_id or not text:
        return jsonify({'error': 'bad'}), 400
    if len(text) > 1000:
        return jsonify({'error': 'Слишком длинно'}), 400
    comments = load_json(COMMENTS_FILE, {})
    if post_id not in comments:
        comments[post_id] = []
    u = get_user(uid)
    c = {
        'id': int(time.time() * 1000),
        'post_id': post_id,
        'user_id': uid,
        'user_name': u.get('name', 'Гость'),
        'user_username': u.get('username', ''),
        'user_avatar': u.get('avatar'),
        'is_admin': is_admin(uid),
        'text': text,
        'created': int(time.time()),
    }
    comments[post_id].append(c)
    if len(comments[post_id]) > 500:
        comments[post_id] = comments[post_id][-500:]
    save_json(COMMENTS_FILE, comments)
    return jsonify({'ok': True, 'comment': c})


@app.route('/api/comments/delete', methods=['POST'])
def api_comments_delete():
    d = request.json or {}
    uid = d.get('uid')
    post_id = str(d.get('post_id'))
    cid = d.get('comment_id')
    if not uid or not post_id or not cid:
        return jsonify({'error': 'bad'}), 400
    comments = load_json(COMMENTS_FILE, {})
    arr = comments.get(post_id, [])
    target = next((c for c in arr if c.get('id') == cid), None)
    if not target:
        return jsonify({'error': 'not found'}), 404
    if str(target.get('user_id')) != str(uid) and not has_perm(uid, 'delete'):
        return jsonify({'error': 'Нет прав'}), 403
    comments[post_id] = [c for c in arr if c.get('id') != cid]
    save_json(COMMENTS_FILE, comments)
    return jsonify({'ok': True})


# ============ CONTESTS ============
@app.route('/api/contests')
def api_contests():
    contests = load_json(CONTESTS_FILE, [])
    contests.sort(key=lambda x: x.get('created', 0), reverse=True)
    return jsonify(contests)


@app.route('/api/contests/create', methods=['POST'])
def api_contests_create():
    d = request.json or {}
    if not has_perm(d.get('uid'), 'contests'): return jsonify({'error': 'Нет доступа'}), 403
    title = (d.get('title') or '').strip()
    if not title: return jsonify({'error': 'Нужно название'}), 400
    contests = load_json(CONTESTS_FILE, [])
    c = {
        'id': int(time.time() * 1000), 'title': title,
        'description': (d.get('description') or '').strip(),
        'cover': d.get('cover'),
        'author_id': d.get('uid'),
        'created': int(time.time()), 'active': True, 'closed': False,
    }
    contests.append(c)
    save_json(CONTESTS_FILE, contests)
    return jsonify({'ok': True, 'contest': c})


# ============ APPLICATIONS ============
@app.route('/api/applications', methods=['GET'])
def api_applications():
    uid = request.args.get('uid')
    if not uid: return jsonify([])
    apps = load_json(APPS_FILE, [])
    if is_admin(uid):
        apps.sort(key=lambda x: x.get('created', 0), reverse=True)
        return jsonify(apps)
    my = [a for a in apps if str(a.get('user_id')) == str(uid)]
    my.sort(key=lambda x: x.get('created', 0), reverse=True)
    return jsonify(my)


@app.route('/api/applications/create', methods=['POST'])
def api_applications_create():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    cid = d.get('contest_id')
    contests = load_json(CONTESTS_FILE, [])
    contest = next((c for c in contests if c['id'] == cid), None)
    if not contest: return jsonify({'error': 'Конкурс не найден'}), 400
    if contest.get('closed'): return jsonify({'error': 'Набор закрыт'}), 400
    apps = load_json(APPS_FILE, [])
    for a in apps:
        if a.get('contest_id') == cid and str(a.get('user_id')) == str(uid):
            return jsonify({'error': 'Ты уже подал заявку'}), 400
    u = get_user(uid)
    item = {
        'id': int(time.time() * 1000), 'contest_id': cid,
        'contest_title': contest['title'],
        'user_id': uid, 'user_name': d.get('name') or u.get('name', ''),
        'user_username': d.get('username') or u.get('username', ''),
        'photo': d.get('photo'), 'comment': (d.get('comment') or '').strip(),
        'status': 'pending', 'reason': '', 'created': int(time.time()),
        'decided_at': None, 'seen': False,
    }
    apps.append(item)
    save_json(APPS_FILE, apps)
    u['applications_count'] = u.get('applications_count', 0) + 1
    save_user(uid, u)
    return jsonify({'ok': True, 'application': item})


@app.route('/api/applications/decide', methods=['POST'])
def api_applications_decide():
    d = request.json or {}
    if not has_perm(d.get('uid'), 'applications'): return jsonify({'error': 'Нет доступа'}), 403
    aid = d.get('application_id')
    status = d.get('status')
    reason = (d.get('reason') or '').strip()
    if status not in ('accepted', 'rejected'):
        return jsonify({'error': 'bad status'}), 400
    if status == 'rejected' and not reason:
        return jsonify({'error': 'Укажи причину'}), 400
    apps = load_json(APPS_FILE, [])
    user_id = None
    for a in apps:
        if a['id'] == aid:
            a['status'] = status
            a['reason'] = reason if status == 'rejected' else ''
            a['decided_at'] = int(time.time())
            a['seen'] = False
            user_id = a.get('user_id')
    save_json(APPS_FILE, apps)
    if user_id:
        u = get_user(user_id)
        if status == 'accepted':
            u['accepted'] = u.get('accepted', 0) + 1
        else:
            u['rejected'] = u.get('rejected', 0) + 1
        save_user(user_id, u)
    return jsonify({'ok': True})


# ============ ADMINS ============
@app.route('/api/admins')
def api_admins():
    return jsonify(get_admins())


@app.route('/api/admins/add', methods=['POST'])
def api_admins_add():
    d = request.json or {}
    uid = d.get('uid')
    admins = get_admins()
    me = admins.get(str(uid))
    if not me: return jsonify({'error': 'Нет доступа'}), 403
    if not me.get('main') and not me.get('perms', {}).get('admins'):
        return jsonify({'error': 'Только главный может выдавать админку'}), 403
    target = d.get('target_uid')
    name = d.get('target_name', 'Админ')
    perms = d.get('perms', dict(DEFAULT_PERMS))
    if not target: return jsonify({'error': 'no target'}), 400
    if str(target) in admins and admins[str(target)].get('main'):
        return jsonify({'error': 'Нельзя менять главного'}), 400
    admins[str(target)] = {
        'uid': target, 'name': name,
        'main': False, 'perms': perms,
    }
    save_admins(admins)
    return jsonify({'ok': True})


@app.route('/api/admins/update_perms', methods=['POST'])
def api_admins_update_perms():
    d = request.json or {}
    uid = d.get('uid')
    admins = get_admins()
    me = admins.get(str(uid))
    if not me: return jsonify({'error': 'Нет доступа'}), 403
    if not me.get('main') and not me.get('perms', {}).get('admins'):
        return jsonify({'error': 'Нет прав'}), 403
    target = str(d.get('target_uid'))
    perms = d.get('perms', {})
    if target in admins:
        if admins[target].get('main'):
            return jsonify({'error': 'Нельзя менять главного'}), 400
        admins[target]['perms'] = perms
        save_admins(admins)
    return jsonify({'ok': True})


@app.route('/api/admins/remove', methods=['POST'])
def api_admins_remove():
    d = request.json or {}
    uid = d.get('uid')
    admins = get_admins()
    me = admins.get(str(uid))
    if not me: return jsonify({'error': 'Нет доступа'}), 403
    if not me.get('main') and not me.get('perms', {}).get('admins'):
        return jsonify({'error': 'Нет прав'}), 403
    target = str(d.get('target_uid'))
    if target in admins and admins[target].get('main'):
        return jsonify({'error': 'Нельзя удалить главного'}), 400
    if target in admins:
        del admins[target]
        save_admins(admins)
    return jsonify({'ok': True})


# ============ STATS ============
@app.route('/api/stats')
def api_stats():
    users = load_json(USERS_FILE, {})
    posts = load_json(POSTS_FILE, [])
    contests = load_json(CONTESTS_FILE, [])
    apps = load_json(APPS_FILE, [])
    messages = load_json(MESSAGES_FILE, {})
    comments = load_json(COMMENTS_FILE, {})
    total_msgs = sum(len(m.get('messages', [])) for m in messages.values())
    total_comments = sum(len(a) for a in comments.values())
    return jsonify({
        'users_total': len(users), 'posts_total': len(posts),
        'contests_total': len(contests),
        'contests_active': sum(1 for c in contests if c.get('active') and not c.get('closed')),
        'applications_total': len(apps),
        'pending': sum(1 for a in apps if a.get('status') == 'pending'),
        'accepted': sum(1 for a in apps if a.get('status') == 'accepted'),
        'rejected': sum(1 for a in apps if a.get('status') == 'rejected'),
        'messages_total': total_msgs,
        'comments_total': total_comments,
    })


# ============ CHAT ============
def chat_key(a, b):
    a = str(a); b = str(b)
    return '_'.join(sorted([a, b]))


@app.route('/api/chat/list', methods=['GET'])
def api_chat_list():
    uid = request.args.get('uid')
    if not uid: return jsonify([])
    messages = load_json(MESSAGES_FILE, {})
    u_me = get_user(uid)
    pinned = u_me.get('pinned_chats', [])
    chats = []
    for key, chat in messages.items():
        if not chat.get('messages'): continue
        if str(uid) not in key.split('_'): continue
        other_id = [x for x in key.split('_') if x != str(uid)]
        if not other_id: continue
        other_id = other_id[0]
        u = get_user(other_id)
        last = chat['messages'][-1] if chat['messages'] else None
        unread = 0
        for m in chat['messages']:
            if str(m.get('to')) == str(uid) and not m.get('read'):
                unread += 1
        chats.append({
            'other': public_user(u),
            'last_message': last.get('text', '') if last else '',
            'last_time': last.get('created', 0) if last else 0,
            'unread': unread,
            'pinned': other_id in pinned,
        })
    chats.sort(key=lambda x: (not x['pinned'], -x['last_time']))
    return jsonify(chats)


@app.route('/api/chat/get', methods=['GET'])
def api_chat_get():
    uid = request.args.get('uid')
    other = request.args.get('other')
    if not uid or not other: return jsonify({'error': 'bad'}), 400
    key = chat_key(uid, other)
    messages = load_json(MESSAGES_FILE, {})
    chat = messages.get(key, {'messages': [], 'pinned_msg': None})
    if 'pinned_msg' not in chat:
        chat['pinned_msg'] = None
    changed = False
    for m in chat['messages']:
        if str(m.get('to')) == str(uid) and not m.get('read'):
            m['read'] = True
            changed = True
    if changed:
        messages[key] = chat
        save_json(MESSAGES_FILE, messages)
    other_u = get_user(other)
    u_me = get_user(uid)
    return jsonify({
        'other': public_user(other_u),
        'messages': chat['messages'][-200:],
        'pinned_msg': chat.get('pinned_msg'),
        'is_blocked': str(other) in u_me.get('blocked', []),
        'in_contacts': str(other) in u_me.get('contacts', []),
        'chat_pinned': str(other) in u_me.get('pinned_chats', []),
    })


@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    d = request.json or {}
    uid = d.get('uid')
    to = d.get('to')
    text = (d.get('text') or '').strip()
    if not uid or not to or not text:
        return jsonify({'error': 'bad'}), 400
    u_me = get_user(uid)
    if str(to) in u_me.get('blocked', []):
        return jsonify({'error': 'blocked'}), 400
    u_other = get_user(to)
    if str(uid) in u_other.get('blocked', []):
        return jsonify({'error': 'cannot send'}), 400
    key = chat_key(uid, to)
    messages = load_json(MESSAGES_FILE, {})
    if key not in messages:
        messages[key] = {'messages': [], 'pinned_msg': None}
    msg = {
        'id': int(time.time() * 1000),
        'from': uid, 'to': to,
        'text': text[:2000],
        'created': int(time.time()),
        'read': False,
    }
    messages[key]['messages'].append(msg)
    if len(messages[key]['messages']) > 500:
        messages[key]['messages'] = messages[key]['messages'][-500:]
    save_json(MESSAGES_FILE, messages)
    return jsonify({'ok': True, 'message': msg})


@app.route('/api/chat/pin_message', methods=['POST'])
def api_chat_pin_message():
    d = request.json or {}
    uid = d.get('uid'); other = d.get('other'); msg_id = d.get('msg_id')
    if not uid or not other: return jsonify({'error': 'bad'}), 400
    key = chat_key(uid, other)
    messages = load_json(MESSAGES_FILE, {})
    if key not in messages: return jsonify({'error': 'no chat'}), 400
    chat = messages[key]
    if msg_id is None:
        chat['pinned_msg'] = None
    else:
        for m in chat['messages']:
            if m.get('id') == msg_id:
                chat['pinned_msg'] = m
                break
    messages[key] = chat
    save_json(MESSAGES_FILE, messages)
    return jsonify({'ok': True, 'pinned_msg': chat.get('pinned_msg')})


@app.route('/api/chat/delete_message', methods=['POST'])
def api_chat_delete_message():
    d = request.json or {}
    uid = d.get('uid'); other = d.get('other'); msg_id = d.get('msg_id')
    if not uid or not other or not msg_id: return jsonify({'error': 'bad'}), 400
    key = chat_key(uid, other)
    messages = load_json(MESSAGES_FILE, {})
    if key not in messages: return jsonify({'error': 'no chat'}), 400
    chat = messages[key]
    chat['messages'] = [m for m in chat['messages']
                        if not (m.get('id') == msg_id and str(m.get('from')) == str(uid))]
    if chat.get('pinned_msg') and chat['pinned_msg'].get('id') == msg_id:
        chat['pinned_msg'] = None
    messages[key] = chat
    save_json(MESSAGES_FILE, messages)
    return jsonify({'ok': True})


@app.route('/api/chat/clear', methods=['POST'])
def api_chat_clear():
    d = request.json or {}
    uid = d.get('uid'); other = d.get('other')
    if not uid or not other: return jsonify({'error': 'bad'}), 400
    key = chat_key(uid, other)
    messages = load_json(MESSAGES_FILE, {})
    if key in messages:
        messages[key]['messages'] = []
        messages[key]['pinned_msg'] = None
        save_json(MESSAGES_FILE, messages)
    return jsonify({'ok': True})


@app.route('/api/chat/unread', methods=['GET'])
def api_chat_unread():
    uid = request.args.get('uid')
    if not uid: return jsonify({'count': 0})
    messages = load_json(MESSAGES_FILE, {})
    unread = 0
    for key, chat in messages.items():
        if str(uid) not in key.split('_'): continue
        for m in chat.get('messages', []):
            if str(m.get('to')) == str(uid) and not m.get('read'):
                unread += 1
    return jsonify({'count': unread})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
