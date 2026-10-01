import telebot
from telebot import types

TOKEN = '8471116013:AAG8fl1pV0hu1lV6VgZVMmitm-NM-iDjL54'
WEBAPP_URL = 'https://darkgram-2.onrender.com'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🏛️ Открыть игру',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(m.chat.id,
        '🏛️ <b>RP Countries</b>\n\n'
        'Выбери страну и правь ей.\n\n'
        'Жми кнопку 👇',
        parse_mode='HTML', reply_markup=kb)

if __name__ == '__main__':
    print('RP bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
