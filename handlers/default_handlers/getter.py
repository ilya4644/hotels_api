from telebot.types import Message
from loader import bot
from main import get_city, UserStates

comm = ["Низкая цена", "Высокая цена", "Лучшее предложение"]


@bot.message_handler(content_types=['text'])
def get_city_handler(message: Message):
	with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
		if result['command'] in comm:
			bot.register_next_step_handler(message, get_city(message))
