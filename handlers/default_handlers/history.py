from telebot.types import Message

from database.database import User
from loader import bot


@bot.message_handler(commands=['history'])
def command_help(message: Message):
    bot.send_message(message.chat.id, text=f'<u>История поиска:</u>', parse_mode='html')
    history_str = ''
    i_num = 0
    for person in User.select():
        if person.telegram_id == message.from_user.id:
            i_num += 1
        history_str += f'#{i_num}\n' \
                       f'Время и дата: {str(person.date_command)}\n' \
                       f'Команда: {person.command}\n' \
                       f'Список отелей: {str(person.hotel_list)}\n\n'

    if history_str == '':
        bot.send_message(message.chat.id, text='Вы ничего не искали.\nИстория поиска пуста.')
    else:
        bot.send_message(message.chat.id, text=history_str)