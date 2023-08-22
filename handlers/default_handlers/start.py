from keyboards.inline.keyboard import start_keyboard
from telebot.types import Message
from loader import bot
import main


@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    bot.send_message(message.from_user.id, "Привет! Я помогу вам подобрать лучший отель!\n\n"
                                           "Выберите, что вас интересует",
                     reply_markup=start_keyboard())
