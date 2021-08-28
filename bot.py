import telebot
import time

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['count'])
def changing_title(message):
	nameOfGroup = "Среднеznaal "
	daysToCount = 307
	secondsInDay = 86400
	while daysToCount > 0 :
		bot.set_chat_title(message.chat.id, title=nameOfGroup+str(daysToCount))
		time.sleep(secondsInDay)
		daysToCount = daysToCount - 1
	
# RUN
bot.polling(none_stop=True)