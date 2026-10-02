import telebot
from telebot import types

TOKEN = '8471116013:AAFoB4xMO372jegqWPlPbu432BbkVL24ZIs'
WEBAPP_URL = 'https://darkgram-2.onrender.com'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def cmd_start(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text='🎮 Играть в Block Blast',
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))
    bot.send_message(m.chat.id,
        '🎮 <b>Block Blast</b>\n\n'
        'Ставь блоки на поле.\n'
        'Заполняй линии — они исчезают!\n\n'
        'Жми кнопку 👇',
        parse_mode='HTML', reply_markup=kb)

if __name__ == '__main__':
    print('Bot started')
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
