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
            'uid': uid,
            'tokens': START_TOKENS,
            'total_requests': 0,
            'total_spent': 0,
            'joined': int(time.time()),
            'last_bonus': 0,
            'history_enabled': True,
            'vibration': True,
            'theme': 'dark',
            'accent': 'purple',
            'font': 'medium',
            'radius': 'md',
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
    else:
        uid = request.args.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    now = int(time.time())
    last_bonus = u.get('last_bonus', 0)
    bonus_given = False
    if last_bonus == 0:
        u['last_bonus'] = now
        save_user(uid, u)
    else:
        last_date = datetime.fromtimestamp(last_bonus).date()
        today = datetime.now().date()
        if last_date < today:
            u['tokens'] = u.get('tokens', 0) + DAILY_BONUS
            u['last_bonus'] = now
            bonus_given = True
            save_user(uid, u)

    return jsonify({
        'uid': u['uid'],
        'tokens': u.get('tokens', 0),
        'total_requests': u.get('total_requests', 0),
        'total_spent': u.get('total_spent', 0),
        'joined': u.get('joined', 0),
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
def tavily_search(query, max_results=3):
    start = time.time()
    try:
        r = requests.post(
            'https://api.tavily.com/search',
            json={
                'query': query,
                'search_depth': 'basic',
                'max_results': max_results,
                'include_answer': False
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', '')[:300],
                })
            return results, time.time() - start
        return [], time.time() - start
    except Exception as e:
        print('tavily err:', e)
        return [], time.time() - start


def ai_answer(query, sources):
    """Стабильная модель openai через Pollinations."""
    start = time.time()
    try:
        context = ''
        for i, s in enumerate(sources, 1):
            context += f"[{i}] {s['title']}\n{s['content']}\n\n"

        prompt = f"""Вопрос: {query}

Источники:
{context}

Дай краткий и точный ответ на русском, 2-4 предложения. Используй источники."""

        # Пробуем 2 раза
        for attempt in range(2):
            try:
                r = requests.post(
                    'https://text.pollinations.ai/openai',
                    json={
                        'model': 'openai',
                        'messages': [
                            {'role': 'system', 'content': 'Ты — AI-помощник DeepSeek Darkgram. Отвечай кратко на русском.'},
                            {'role': 'user', 'content': prompt}
                        ]
                    },
                    timeout=45
                )
                if r.status_code == 200:
                    data = r.json()
                    answer = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if answer and len(answer) > 5:
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
    sources, search_time = tavily_search(query, 3)
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


@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'time': int(time.time())})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
