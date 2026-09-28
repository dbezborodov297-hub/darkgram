import json
import os
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

USERS_FILE = 'users.json'
HISTORY_FILE = 'search_history.json'

START_TOKENS = 1000
DAILY_BONUS = 50
SEARCH_TOKENS = 1


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
            'tokens': START_TOKENS,
            'total_requests': 0, 'total_spent': 0,
            'joined': int(time.time()), 'last_bonus': 0,
            'history_enabled': True, 'vibration': True,
            'theme': 'dark', 'accent': 'purple',
            'font': 'medium', 'radius': 'md',
            'streak': 0, 'last_seen_day': '',
        }
        save_json(USERS_FILE, users)
    return users[key]


def save_user(uid, data):
    users = load_json(USERS_FILE, {})
    users[str(uid)] = data
    save_json(USERS_FILE, users)


@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


# ============ PLAYER ============
@app.route('/api/player', methods=['POST', 'GET'])
def api_player():
    if request.method == 'POST':
        d = request.json or {}
        uid = d.get('uid')
        name = d.get('name', '')
    else:
        uid = request.args.get('uid')
        name = request.args.get('name', '')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    if name: u['name'] = name

    now = int(time.time())
    today = datetime.now().date()

    # Ежедневный бонус + стрик
    bonus_given = False
    last_bonus = u.get('last_bonus', 0)
    last_seen_day = u.get('last_seen_day', '')
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    if last_bonus == 0:
        u['last_bonus'] = now
        u['last_seen_day'] = today_str
        u['streak'] = 1
    elif last_seen_day != today_str:
        u['tokens'] = u.get('tokens', 0) + DAILY_BONUS
        u['last_bonus'] = now
        bonus_given = True
        if last_seen_day == yesterday_str:
            u['streak'] = u.get('streak', 0) + 1
        else:
            u['streak'] = 1
        u['last_seen_day'] = today_str
    save_user(uid, u)

    return jsonify({
        'uid': u['uid'],
        'name': u.get('name', ''),
        'tokens': u.get('tokens', 0),
        'total_requests': u.get('total_requests', 0),
        'total_spent': u.get('total_spent', 0),
        'joined': u.get('joined', 0),
        'streak': u.get('streak', 0),
        'history_enabled': u.get('history_enabled', True),
        'vibration': u.get('vibration', True),
        'theme': u.get('theme', 'dark'),
        'accent': u.get('accent', 'purple'),
        'font': u.get('font', 'medium'),
        'radius': u.get('radius', 'md'),
        'daily_bonus': DAILY_BONUS if bonus_given else 0,
    })


@app.route('/api/save_settings', methods=['POST'])
def api_save_settings():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    for field in ['history_enabled', 'vibration', 'theme', 'accent', 'font', 'radius']:
        if field in d:
            u[field] = d[field]
    save_user(uid, u)
    return jsonify({'ok': True})


# ============ SEARCH ============
def tavily_search(query, max_results=5):
    start = time.time()
    try:
        r = requests.post(
            'https://api.tavily.com/search',
            json={
                'query': query,
                'search_depth': 'advanced',
                'max_results': max_results,
                'include_answer': False
            },
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', '')[:400],
                })
            return results, time.time() - start
        return [], time.time() - start
    except Exception as e:
        print('tavily err:', e)
        return [], time.time() - start


def ai_answer(query, sources):
    """Умный AI с структурой ответа."""
    start = time.time()
    try:
        context = ''
        for i, s in enumerate(sources, 1):
            context += f"[{i}] {s['title']}\n{s['content']}\n\n"

        prompt = f"""Вопрос: {query}

Найденные источники:
{context}

Структурируй ответ так:
1. Краткий ответ (1-2 предложения)
2. Подробнее (3-5 предложений с фактами)
3. Источники: [1], [2] в конце

Отвечай на русском, чётко и по делу."""

        for attempt in range(3):
            try:
                r = requests.post(
                    'https://text.pollinations.ai/openai',
                    json={
                        'model': 'openai',
                        'messages': [
                            {'role': 'system', 'content': 'Ты — умный AI-поисковик DeepSeek Darkgram. Даёшь структурированные ответы.'},
                            {'role': 'user', 'content': prompt}
                        ]
                    },
                    timeout=50
                )
                if r.status_code == 200:
                    data = r.json()
                    answer = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if answer and len(answer) > 10:
                        return answer, time.time() - start
            except Exception as e:
                print(f'ai attempt {attempt+1} err:', e)
                time.sleep(1)

        return None, time.time() - start
    except Exception as e:
        print('ai err:', e)
        return None, time.time() - start


@app.route('/api/search', methods=['POST'])
def api_search():
    d = request.json or {}
    uid = d.get('uid')
    query = (d.get('query') or '').strip()
    if not uid: return jsonify({'error': 'no uid'}), 400
    if not query: return jsonify({'error': 'Пустой запрос'}), 400

    u = get_user(uid)
    cost = SEARCH_TOKENS

    if u.get('tokens', 0) < cost:
        return jsonify({
            'error': 'tokens',
            'message': f'Недостаточно токенов. Нужно {cost}.',
            'tokens': u.get('tokens', 0),
            'cost': cost,
        }), 400

    total_start = time.time()
    sources, search_time = tavily_search(query, 5)
    answer, ai_time = ai_answer(query, sources)
    total_time = time.time() - total_start

    u['tokens'] = u.get('tokens', 0) - cost
    u['total_requests'] = u.get('total_requests', 0) + 1
    u['total_spent'] = u.get('total_spent', 0) + cost
    save_user(uid, u)

    result = {
        'ok': True,
        'query': query,
        'answer': answer or 'Не удалось получить ответ. Попробуй ещё раз.',
        'sources': sources,
        'search_time': round(search_time, 2),
        'ai_time': round(ai_time, 2),
        'total_time': round(total_time, 2),
        'cost': cost,
        'tokens_left': u['tokens'],
        'timestamp': int(time.time()),
    }

    if u.get('history_enabled', True):
        history = load_json(HISTORY_FILE, {})
        user_hist = history.get(str(uid), [])
        user_hist.insert(0, {
            'query': query,
            'answer': result['answer'][:300],
            'time': result['timestamp'],
            'cost': cost,
        })
        history[str(uid)] = user_hist[:50]
        save_json(HISTORY_FILE, history)

    return jsonify(result)


@app.route('/api/history')
def api_history():
    uid = request.args.get('uid')
    if not uid: return jsonify([])
    history = load_json(HISTORY_FILE, {})
    return jsonify(history.get(str(uid), [])[:50])


@app.route('/api/history/clear', methods=['POST'])
def api_history_clear():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    history = load_json(HISTORY_FILE, {})
    history[str(uid)] = []
    save_json(HISTORY_FILE, history)
    return jsonify({'ok': True})


@app.route('/api/stats')
def api_stats():
    uid = request.args.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    history = load_json(HISTORY_FILE, {})
    user_hist = history.get(str(uid), [])

    days = []
    today = datetime.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = int(datetime.combine(day, datetime.min.time()).timestamp())
        day_end = day_start + 86400
        spent = sum(h.get('cost', 0) for h in user_hist
                    if day_start <= h.get('time', 0) < day_end)
        count = sum(1 for h in user_hist
                    if day_start <= h.get('time', 0) < day_end)
        days.append({
            'date': day.strftime('%d.%m'),
            'day_short': ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][day.weekday()],
            'spent': spent,
            'count': count,
        })

    return jsonify({'days': days})


# ============ TOP ============
@app.route('/api/top')
def api_top():
    category = request.args.get('category', 'requests')
    uid = request.args.get('uid')

    users = load_json(USERS_FILE, {})
    arr = []
    for k, u in users.items():
        if not u.get('name') and not u.get('username'): continue
        arr.append({
            'uid': u.get('uid'),
            'name': u.get('name', 'Гость'),
            'username': u.get('username', ''),
            'requests': u.get('total_requests', 0),
            'spent': u.get('total_spent', 0),
            'streak': u.get('streak', 0),
            'tokens': u.get('tokens', 0),
        })

    if category == 'tokens':
        arr.sort(key=lambda x: x['spent'], reverse=True)
    elif category == 'streak':
        arr.sort(key=lambda x: x['streak'], reverse=True)
    else:
        arr.sort(key=lambda x: x['requests'], reverse=True)

    top = arr[:30]

    my_place = None
    my_data = None
    if uid:
        for i, u in enumerate(arr, 1):
            if str(u['uid']) == str(uid):
                my_place = i
                my_data = u
                break

    return jsonify({
        'top': top,
        'my_place': my_place,
        'my_data': my_data,
        'category': category,
    })


@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'time': int(time.time())})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
