import telebot
import json
import os
import requests
from telebot import types

TOKEN = '8747895563:AAGrxrG2y491FEM6acCtpnGk0YuH6e31VGA'
DATA_FILE = 'quotes.json'

bot = telebot.TeleBot(TOKEN)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_quote(messages):
    payload = {
        'type': 'quote',
        'format': 'png',
        'backgroundColor': '#1a1a2e',
        'messages': messages
    }
    try:
        r = requests.post(
            'https://quotly.vercel.app/generate',
            json=payload,
            timeout=20
        )
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print('QuotLy error:', e)
    return None


@bot.message_handler(commands=['q'])
def cmd_quote(m):
    if not m.reply_to_message:
        bot.reply_to(m, 'Ответь на сообщение и напиши /q')
        return

    replied = m.reply_to_message
    author = replied.from_user.first_name or 'Аноним'
    text = replied.text or replied.caption or ''

    if not text:
        bot.reply_to(m, 'Это сообщение не содержит текста')
        return

    msg = bot.reply_to(m, 'Делаю цитату...')

    messages = [{
        'entities': [],
        'avatar': True,
        'from': {
            'id': replied.from_user.id,
            'first_name': author,
            'last_name': replied.from_user.last_name or '',
            'username': replied.from_user.username or '',
            'name': author,
            'type': 'user'
        },
        'text': text
    }]

    image_bytes = make_quote(messages)

    if not image_bytes:
        bot.edit_message_text(
            'Не удалось создать цитату. Попробуй позже.',
            chat_id=m.chat.id,
            message_id=msg.message_id
        )
        return

    sent = bot.send_photo(
        m.chat.id,
        image_bytes,
        reply_to_message_id=replied.message_id
    )

    data = load_data()
    qid = str(sent.message_id)
    data[qid] = {'likes': 0, 'dislikes': 0, 'chat_id': m.chat.id}
    save_data(data)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton('👍 0', callback_data=f'like_{qid}'),
        types.InlineKeyboardButton('👎 0', callback_data=f'dislike_{qid}')
    )
    bot.edit_message_reply_markup(
        chat_id=m.chat.id,
        message_id=sent.message_id,
        reply_markup=kb
    )

    try:
        bot.delete_message(m.chat.id, msg.message_id)
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith('like_') or c.data.startswith('dislike_'))
def cb_vote(call):
    action, qid = call.data.split('_', 1)
    data = load_data()
    if qid not in data:
        bot.answer_callback_query(call.id, 'Цитата не найдена')
        return

    user_id = str(call.from_user.id)
    q = data[qid]

    if 'voted' not in q:
        q['voted'] = {}

    if user_id in q['voted']:
        prev = q['voted'][user_id]
        if prev == action:
            bot.answer_callback_query(call.id, 'Ты уже голосовал')
            return
        if prev == 'like':
            q['likes'] -= 1
        else:
            q['dislikes'] -= 1

    q['voted'][user_id] = action

    if action == 'like':
        q['likes'] += 1
    else:
        q['dislikes'] += 1

    data[qid] = q
    save_data(data)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(f'👍 {q["likes"]}', callback_data=f'like_{qid}'),
        types.InlineKeyboardButton(f'👎 {q["dislikes"]}', callback_data=f'dislike_{qid}')
    )
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb
    )
    bot.answer_callback_query(call.id, 'Голос учтён')


@bot.message_handler(commands=['qtop'])
def cmd_qtop(m):
    data = load_data()
    if not data:
        bot.reply_to(m, 'Пока нет цитат')
        return
    arr = []
    for qid, q in data.items():
        score = q.get('likes', 0) - q.get('dislikes', 0)
        arr.append((score, q.get('likes', 0), q.get('dislikes', 0), qid))
    arr.sort(reverse=True)
    text = 'ТОП ЦИТАТ\n\n'
    for i, (score, likes, dislikes, qid) in enumerate(arr[:10], 1):
        text += f'{i}. 👍 {likes} / 👎 {dislikes} (счёт: {score})\n'
    bot.reply_to(m, text)


if __name__ == '__main__':
    print('Quote bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
