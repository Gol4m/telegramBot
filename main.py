TOKEN = '1952799568:AAG-OrUAkHmuoBkyn_VqaMfbtctCb5NzSxg'

import os
import time
import telebot
from flask import Flask, request


APP_URL = f'https://telegrammbotyara.herokuapp.com/{TOKEN}'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['count'])
def changing_title(message):
    nameOfGroup = "Среднеznaal "
    daysToCount = 307
    secondsInDay = 86400
    while daysToCount > 0:
        bot.set_chat_title(message.chat.id, title=nameOfGroup + str(daysToCount))
        time.sleep(secondsInDay)
        daysToCount = daysToCount - 1

@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))