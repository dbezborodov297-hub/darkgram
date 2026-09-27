import json
import os
import time
import threading
import random
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'
CONTESTS_FILE = 'contests.json'
APPS_FILE = 'applications.json'
ADMINS_FILE = 'admins.json'

ADMIN_IDS = [8907438590] # твой ID — сюда впиши СВОЙ

ONLINE = {}
ONLINE_LOCK = threading.Lock()
ONLINE_TIMEOUT = 60


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
            'uid': uid,
            'name': '',
            'username': '',
            'joined': int(time.time()),
            'total_time': 0,
            'last_seen': 0,
            'posts_count': 0,
            'applications_count': 0,
            'accepted': 0,
            'rejected': 0,
            'accessory': 'none',
            'accent': 'none',
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
            admins[str(aid)] = {'uid': aid, 'name': 'Главный админ', 'main': True}
    return admins


def is_admin(uid):
    admins = get_admins()
    return str(uid) in admins


def save_admins(d):
    save_json(ADMINS_FILE, d)


# ==================== API ====================

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


@app.route('/api/player', methods=['POST', 'GET'])
def api_player():
    if request.method == 'POST':
        d = request.json or {}
        uid = d.get('uid')
        name = d.get('name', '')
        username = d.get('username', '')
    else:
        uid = request.args.get('uid')
        name = request.args.get('name', '')
        username = request.args.get('username', '')
    if not uid:
        return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    if name: u['name'] = name
    if username: u['username'] = username
    save_user(uid, u)
    return jsonify({
        'uid': u['uid'],
        'name': u['name'],
        'username': u.get('username', ''),
        'joined': u['joined'],
        'total_time': u['total_time'],
        'posts_count': u.get('posts_count', 0),
        'applications_count': u.get('applications_count', 0),
        'accepted': u.get('accepted', 0),
        'rejected': u.get('rejected', 0),
        'accessory': u.get('accessory', 'none'),
        'accent': u.get('accent', 'none'),
        'is_admin': is_admin(uid),
    })


@app.route('/api/save_profile', methods=['POST'])
def api_save_profile():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    if 'accessory' in d: u['accessory'] = d['accessory']
    if 'accent' in d: u['accent'] = d['accent']
    save_user(uid, u)
    return jsonify({'ok': True})


@app.route('/api/ping', methods=['POST'])
def api_ping():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    now = int(time.time())
    with ONLINE_LOCK:
        last = ONLINE.get(str(uid), 0)
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


# ==================== ПОСТЫ ====================

@app.route('/api/posts')
def api_posts():
    posts = load_json(POSTS_FILE, [])
    posts.sort(key=lambda x: x.get('created', 0), reverse=True)
    return jsonify(posts[:50])


@app.route('/api/posts/create', methods=['POST'])
def api_posts_create():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    text = (d.get('text') or '').strip()
    image = d.get('image')
    if not text and not image:
        return jsonify({'error': 'Пусто'}), 400
    posts = load_json(POSTS_FILE, [])
    p = {
        'id': int(time.time() * 1000),
        'author_id': uid,
        'author_name': d.get('name', 'Админ'),
        'text': text,
        'image': image,
        'created': int(time.time()),
        'likes': 0,
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
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    pid = d.get('post_id')
    posts = load_json(POSTS_FILE, [])
    posts = [p for p in posts if p.get('id') != pid]
    save_json(POSTS_FILE, posts)
    return jsonify({'ok': True})


# ==================== КОНКУРСЫ ====================

@app.route('/api/contests')
def api_contests():
    contests = load_json(CONTESTS_FILE, [])
    contests.sort(key=lambda x: x.get('created', 0), reverse=True)
    return jsonify(contests)


@app.route('/api/contests/create', methods=['POST'])
def api_contests_create():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    title = (d.get('title') or '').strip()
    desc = (d.get('description') or '').strip()
    fields = d.get('fields', ['name', 'photo', 'comment'])
    if not title:
        return jsonify({'error': 'Нужно название'}), 400
    contests = load_json(CONTESTS_FILE, [])
    c = {
        'id': int(time.time() * 1000),
        'title': title,
        'description': desc,
        'emoji': d.get('emoji', '🎨'),
        'fields': fields,
        'author_id': uid,
        'created': int(time.time()),
        'active': True,
        'closed': False,
    }
    contests.append(c)
    save_json(CONTESTS_FILE, contests)
    return jsonify({'ok': True, 'contest': c})


@app.route('/api/contests/close', methods=['POST'])
def api_contests_close():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    cid = d.get('contest_id')
    contests = load_json(CONTESTS_FILE, [])
    for c in contests:
        if c['id'] == cid:
            c['active'] = False
            c['closed'] = True
    save_json(CONTESTS_FILE, contests)
    return jsonify({'ok': True})


# ==================== ЗАЯВКИ ====================

@app.route('/api/applications', methods=['GET', 'POST'])
def api_applications():
    if request.method == 'GET':
        uid = request.args.get('uid')
        if not uid: return jsonify([])
        apps = load_json(APPS_FILE, [])
        if is_admin(uid):
            apps.sort(key=lambda x: x.get('created', 0), reverse=True)
            return jsonify(apps)
        my = [a for a in apps if str(a.get('user_id')) == str(uid)]
        my.sort(key=lambda x: x.get('created', 0), reverse=True)
        return jsonify(my)
    return jsonify({'error': 'method'}), 405


@app.route('/api/applications/create', methods=['POST'])
def api_applications_create():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    cid = d.get('contest_id')
    contests = load_json(CONTESTS_FILE, [])
    contest = next((c for c in contests if c['id'] == cid), None)
    if not contest:
        return jsonify({'error': 'Конкурс не найден'}), 400
    if contest.get('closed'):
        return jsonify({'error': 'Набор закрыт'}), 400

    apps = load_json(APPS_FILE, [])
    # проверка — уже подал заявку
    for a in apps:
        if a.get('contest_id') == cid and str(a.get('user_id')) == str(uid):
            return jsonify({'error': 'Ты уже подал заявку'}), 400

    u = get_user(uid)
    app_item = {
        'id': int(time.time() * 1000),
        'contest_id': cid,
        'contest_title': contest['title'],
        'contest_emoji': contest.get('emoji', '🎨'),
        'user_id': uid,
        'user_name': d.get('name') or u.get('name', ''),
        'user_username': d.get('username') or u.get('username', ''),
        'photo': d.get('photo'),
        'comment': (d.get('comment') or '').strip(),
        'accessory': u.get('accessory', 'none'),
        'status': 'pending',
        'reason': '',
        'created': int(time.time()),
        'decided_at': None,
    }
    apps.append(app_item)
    save_json(APPS_FILE, apps)

    u['applications_count'] = u.get('applications_count', 0) + 1
    save_user(uid, u)
    return jsonify({'ok': True, 'application': app_item})


@app.route('/api/applications/decide', methods=['POST'])
def api_applications_decide():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    aid = d.get('application_id')
    status = d.get('status')
    reason = (d.get('reason') or '').strip()
    if status not in ('accepted', 'rejected'):
        return jsonify({'error': 'bad status'}), 400
    if status == 'rejected' and not reason:
        return jsonify({'error': 'Укажи причину'}), 400

    apps = load_json(APPS_FILE, [])
    for a in apps:
        if a['id'] == aid:
            a['status'] = status
            a['reason'] = reason if status == 'rejected' else ''
            a['decided_at'] = int(time.time())
            user_id = a.get('user_id')
    save_json(APPS_FILE, apps)

    u = get_user(user_id)
    if status == 'accepted':
        u['accepted'] = u.get('accepted', 0) + 1
    else:
        u['rejected'] = u.get('rejected', 0) + 1
    save_user(user_id, u)
    return jsonify({'ok': True})


# ==================== АДМИНКА ====================

@app.route('/api/admins')
def api_admins():
    admins = get_admins()
    return jsonify(admins)


@app.route('/api/admins/add', methods=['POST'])
def api_admins_add():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    target = d.get('target_uid')
    name = d.get('target_name', 'Админ')
    if not target: return jsonify({'error': 'no target'}), 400
    admins = get_admins()
    if str(target) in admins and admins[str(target)].get('main'):
        return jsonify({'error': 'Нельзя менять главного'}), 400
    admins[str(target)] = {'uid': target, 'name': name, 'main': False}
    save_admins(admins)
    return jsonify({'ok': True})


@app.route('/api/admins/remove', methods=['POST'])
def api_admins_remove():
    d = request.json or {}
    uid = d.get('uid')
    if not is_admin(uid): return jsonify({'error': 'Нет доступа'}), 403
    target = str(d.get('target_uid'))
    admins = get_admins()
    if target in admins and admins[target].get('main'):
        return jsonify({'error': 'Нельзя удалить главного'}), 400
    if target in admins:
        del admins[target]
        save_admins(admins)
    return jsonify({'ok': True})


# ==================== СТАТИСТИКА ====================

@app.route('/api/stats')
def api_stats():
    users = load_json(USERS_FILE, {})
    posts = load_json(POSTS_FILE, [])
    contests = load_json(CONTESTS_FILE, [])
    apps = load_json(APPS_FILE, [])
    return jsonify({
        'users_total': len(users),
        'posts_total': len(posts),
        'contests_total': len(contests),
        'contests_active': sum(1 for c in contests if c.get('active') and not c.get('closed')),
        'applications_total': len(apps),
        'pending': sum(1 for a in apps if a.get('status') == 'pending'),
        'accepted': sum(1 for a in apps if a.get('status') == 'accepted'),
        'rejected': sum(1 for a in apps if a.get('status') == 'rejected'),
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
