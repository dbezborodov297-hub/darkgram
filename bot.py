import telebot
import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = '8514412667:AAHT9MHWYVDjIOn6m9IIHH5by9V12QvqmGU'
DATA_FILE = 'messages_data.json'

bot = telebot.TeleBot(TOKEN)

# Структура: { chat_id: { user_id: { name, messages: [timestamp1, timestamp2, ...] } } }
data = {}


def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}


def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print('save err:', e)


def track_message(chat_id, user_id, name):
    chat_key = str(chat_id)
    user_key = str(user_id)

    if chat_key not in data:
        data[chat_key] = {}
    if user_key not in data[chat_key]:
        data[chat_key][user_key] = {'name': name, 'messages': []}

    data[chat_key][user_key]['name'] = name
    data[chat_key][user_key]['messages'].append(int(time.time()))

    # Ограничим историю 90 днями, чтобы файл не пух
    cutoff = int(time.time()) - 90 * 86400
    data[chat_key][user_key]['messages'] = [
        t for t in data[chat_key][user_key]['messages'] if t > cutoff
    ]


def get_top(chat_id, period):
    """period: 'hour', 'day', 'week', 'month'"""
    now = int(time.time())
    if period == 'hour':
        cutoff = now - 3600
    elif period == 'day':
        cutoff = now - 86400
    elif period == 'week':
        cutoff = now - 7 * 86400
    elif period == 'month':
        cutoff = now - 30 * 86400
    else:
        cutoff = 0

    chat_key = str(chat_id)
    if chat_key not in data:
        return []

    result = []
    for user_key, info in data[chat_key].items():
        count = sum(1 for t in info['messages'] if t >= cutoff)
        if count > 0:
            result.append({
                'user_id': user_key,
                'name': info.get('name', 'Гость'),
                'count': count
            })

    result.sort(key=lambda x: x['count'], reverse=True)
    return result


def get_user_stats(chat_id, user_id, period):
    now = int(time.time())
    if period == 'hour':
        cutoff = now - 3600
    elif period == 'day':
        cutoff = now - 86400
    elif period == 'week':
        cutoff = now - 7 * 86400
    elif period == 'month':
        cutoff = now - 30 * 86400
    else:
        cutoff = 0

    chat_key = str(chat_id)
    user_key = str(user_id)

    if chat_key not in data or user_key not in data[chat_key]:
        return 0

    return sum(1 for t in data[chat_key][user_key]['messages'] if t >= cutoff)


def format_top(items, title, limit=10):
    if not items:
        return f'<b>{title}</b>\n\nПока нет данных.'

    lines = [f'<b>{title}</b>\n']
    for i, u in enumerate(items[:limit], 1):
        medal = ''
        if i == 1: medal = '🥇 '
        elif i == 2: medal = '🥈 '
        elif i == 3: medal = '🥉 '
        lines.append(f'{medal}{i}. {u["name"]} — <b>{u["count"]}</b>')

    return '\n'.join(lines)


# ============================================================
# КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['top'])
def cmd_top(m):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Эта команда работает только в группах.')
        return

    args = m.text.split()
    period = args[1] if len(args) > 1 else 'day'

    if period not in ('hour', 'day', 'week', 'month'):
        bot.reply_to(m, 'Используй: /top hour, /top day, /top week, /top month')
        return

    titles = {
        'hour': 'Топ за час',
        'day': 'Топ за день',
        'week': 'Топ за неделю',
        'month': 'Топ за месяц',
    }

    top = get_top(m.chat.id, period)
    text = format_top(top, titles[period])
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['me'])
def cmd_me(m):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Эта команда работает только в группах.')
        return

    uid = m.from_user.id
    name = m.from_user.first_name or 'Ты'

    hour = get_user_stats(m.chat.id, uid, 'hour')
    day = get_user_stats(m.chat.id, uid, 'day')
    week = get_user_stats(m.chat.id, uid, 'week')
    month = get_user_stats(m.chat.id, uid, 'month')

    text = (
        f'<b>📊 {name}</b>\n\n'
        f'За час: <b>{hour}</b>\n'
        f'За день: <b>{day}</b>\n'
        f'За неделю: <b>{week}</b>\n'
        f'За месяц: <b>{month}</b>'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['stats'])
def cmd_stats(m):
    if m.chat.type == 'private':
        bot.reply_to(m, 'Эта команда работает только в группах.')
        return

    chat_key = str(m.chat.id)
    if chat_key not in data:
        bot.reply_to(m, 'Пока нет данных. Начните общаться!')
        return

    total_users = len(data[chat_key])
    total_messages = sum(len(info['messages']) for info in data[chat_key].values())

    now = int(time.time())
    day_cutoff = now - 86400
    day_messages = sum(
        sum(1 for t in info['messages'] if t >= day_cutoff)
        for info in data[chat_key].values()
    )

    text = (
        f'<b>📈 Статистика группы</b>\n\n'
        f'Участников: <b>{total_users}</b>\n'
        f'Всего сообщений: <b>{total_messages}</b>\n'
        f'За последние 24 часа: <b>{day_messages}</b>'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['start', 'help'])
def cmd_start(m):
    text = (
        'Я считаю сообщения в группе.\n\n'
        '<b>Команды (работают в группе):</b>\n\n'
        '/top hour — топ за час\n'
        '/top day — топ за день\n'
        '/top week — топ за неделю\n'
        '/top month — топ за месяц\n'
        '/me — моя статистика\n'
        '/stats — общая статистика группы'
    )
    bot.send_message(m.chat.id, text, parse_mode='HTML')


# ============================================================
# ТРЕКЕР СООБЩЕНИЙ (в группах)
# ============================================================

@bot.message_handler(
    func=lambda m: m.chat.type in ('group', 'supergroup') and m.from_user and not m.text.startswith('/') if m.text else False,
    content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document', 'audio']
)
def track_group_message(m):
    if not m.from_user or m.from_user.is_bot:
        return

    name = m.from_user.first_name or 'Гость'
    if m.from_user.last_name:
        name += ' ' + m.from_user.last_name
    if m.from_user.username:
        name += f' (@{m.from_user.username})'

    track_message(m.chat.id, m.from_user.id, name)
    save_data()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == '__main__':
    load_data()
    print('Bot started. Tracking messages...')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
