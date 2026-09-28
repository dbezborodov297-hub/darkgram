import json
import os
import time
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='webapp')
CORS(app)

HISTORY_FILE = 'search_history.json'


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


@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')


# ============ SEARCH ============
def tavily_search(query):
    """Поиск через Tavily (keyless)."""
    start = time.time()
    try:
        r = requests.post(
            'https://api.tavily.com/search',
            json={
                'query': query,
                'search_depth': 'basic',
                'max_results': 5,
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
    """AI-ответ через Pollinations."""
    start = time.time()
    try:
        context = ''
        for i, s in enumerate(sources, 1):
            context += f"[{i}] {s['title']}\n{s['content']}\n\n"

        prompt = f"""Вопрос: {query}

Найденные источники:
{context}

Дай краткий и точный ответ на основе источников. Пиши на русском. В конце можешь указать ссылки на источники в формате [1], [2]."""

        r = requests.post(
            'https://text.pollinations.ai/openai',
            json={
                'model': 'openai',
                'messages': [
                    {'role': 'system', 'content': 'Ты — AI-поисковик. Отвечай на русском, кратко и по делу.'},
                    {'role': 'user', 'content': prompt}
                ]
            },
            timeout=30
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
    query = (d.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'Пустой запрос'}), 400

    total_start = time.time()

    # 1. Поиск в интернете
    sources, search_time = tavily_search(query)

    # 2. AI-ответ
    answer, ai_time = ai_answer(query, sources)

    total_time = time.time() - total_start

    result = {
        'ok': True,
        'query': query,
        'answer': answer or 'Не удалось получить ответ. Попробуй ещё раз.',
        'sources': sources,
        'search_time': round(search_time, 2),
        'ai_time': round(ai_time, 2),
        'total_time': round(total_time, 2),
        'timestamp': int(time.time()),
    }

    # Сохраняем в историю
    history = load_json(HISTORY_FILE, [])
    history.insert(0, {
        'query': query,
        'answer': result['answer'][:500],
        'time': result['timestamp'],
    })
    save_json(HISTORY_FILE, history[:50])

    return jsonify(result)


@app.route('/api/history')
def api_history():
    history = load_json(HISTORY_FILE, [])
    return jsonify(history[:20])


@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'time': int(time.time())})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
