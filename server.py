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

# Режимы поиска
SEARCH_MODES = {
    'turbo': {
        'name': 'Очень быстрый',
        'model': 'openai-fast',
        'tokens': 1,
        'sources': 2,
        'depth': 'basic',
        'prompt_extra': 'Отвечай максимально кратко, одним предложением.'
    },
    'fast': {
        'name': 'Быстрый',
        'model': 'openai',
        'tokens': 2,
        'sources': 3,
        'depth': 'basic',
        'prompt_extra': 'Отвечай кратко, 2-3 предложения.'
    },
    'balanced': {
        'name': 'Балансированный',
        'model': 'openai',
        'tokens': 3,
        'sources': 5,
        'depth': 'basic',
        'prompt_extra': 'Отвечай нормально, 3-5 предложений.'
    },
    'standard': {
        'name': 'Стандартный',
        'model': 'openai-large',
        'tokens': 5,
        'sources': 5,
        'depth': 'advanced',
        'prompt_extra': 'Дай развёрнутый ответ с фактами.'
    },
    'smart': {
        'name': 'Умный',
        'model': 'openai-large',
        'tokens': 8,
        'sources': 10,
        'depth': 'advanced',
        'prompt_extra': 'Дай глубокий анализ, рассмотри разные стороны вопроса.'
    },
}

DEFAULT_MODE = 'balanced'


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
            'search_mode': DEFAULT_MODE,
            'history_enabled': True,
            'vibration': True,
            'theme': 'dark',
            'accent': 'blue',
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
    # Ежедневный бонус
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
        'search_mode': u.get('search_mode', DEFAULT_MODE),
        'history_enabled': u.get('history_enabled', True),
        'vibration': u.get('vibration', True),
        'theme': u.get('theme', 'dark'),
        'accent': u.get('accent', 'blue'),
        'daily_bonus': DAILY_BONUS if bonus_given else 0,
    })


@app.route('/api/save_settings', methods=['POST'])
def api_save_settings():
    d = request.json or {}
    uid = d.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    u = get_user(uid)
    for field in ['search_mode', 'history_enabled', 'vibration', 'theme', 'accent']:
        if field in d:
            u[field] = d[field]
    save_user(uid, u)
    return jsonify({'ok': True})


# ============ SEARCH ============
def tavily_search(query, max_results=5, depth='basic'):
    start = time.time()
    try:
        r = requests.post(
            'https://api.tavily.com/search',
            json={
                'query': query,
                'search_depth': depth,
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
                    'content': item.get('content', '')[:300],
                })
            return results, time.time() - start
        return [], time.time() - start
    except Exception as e:
        print('tavily err:', e)
        return [], time.time() - start


def ai_answer(query, sources, mode_cfg):
    start = time.time()
    try:
        context = ''
        for i, s in enumerate(sources, 1):
            context += f"[{i}] {s['title']}\n{s['content']}\n\n"

        prompt = f"""Вопрос: {query}

Найденные источники:
{context}

{mode_cfg['prompt_extra']}
Отвечай на русском. Если уместно — укажи источники в формате [1], [2]."""

        r = requests.post(
            'https://text.pollinations.ai/openai',
            json={
                'model': mode_cfg['model'],
                'messages': [
                    {'role': 'system', 'content': 'Ты — AI-поисковик DeepSeek Darkgram. Отвечай чётко и по делу.'},
                    {'role': 'user', 'content': prompt}
                ]
            },
            timeout=60
        )

        if r.status_code == 200:
            data = r.json()
            answer = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            return answer, time.time() - start
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
    mode = u.get('search_mode', DEFAULT_MODE)
    if mode not in SEARCH_MODES:
        mode = DEFAULT_MODE
    cfg = SEARCH_MODES[mode]

    cost = cfg['tokens']
    if u.get('tokens', 0) < cost:
        return jsonify({
            'error': 'tokens',
            'message': f'Недостаточно токенов. Нужно {cost}, у тебя {u.get("tokens", 0)}.',
            'tokens': u.get('tokens', 0),
            'cost': cost,
        }), 400

    total_start = time.time()
    sources, search_time = tavily_search(query, cfg['sources'], cfg['depth'])
    answer, ai_time = ai_answer(query, sources, cfg)
    total_time = time.time() - total_start

    # Списываем токены
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
        'mode': mode,
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
            'mode': mode,
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


# ============ STATS / CHART ============
@app.route('/api/stats')
def api_stats():
    uid = request.args.get('uid')
    if not uid: return jsonify({'error': 'no uid'}), 400
    history = load_json(HISTORY_FILE, {})
    user_hist = history.get(str(uid), [])

    # График за 7 дней
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


@app.route('/api/modes')
def api_modes():
    return jsonify({k: {'name': v['name'], 'tokens': v['tokens'],
                         'sources': v['sources']}
                    for k, v in SEARCH_MODES.items()})


@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'time': int(time.time())})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
