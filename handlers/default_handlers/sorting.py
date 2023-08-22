from telebot.types import Message, ReplyKeyboardRemove
from loader import bot
from main import UserStates

messages = ["низкая цена", "высокая цена", "лучшее предложение"]


@bot.message_handler(content_types=['text'], func=lambda message: message.text.lower() in messages)
def sorter_handler(message: Message):
    bot.set_state(message.from_user.id, UserStates.sort_order_distance, message.chat.id)
    bot.set_state(message.from_user.id, UserStates.sort_order, message.chat.id)
    bot.set_state(message.from_user.id, UserStates.command, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        result['command'] = message.text
        if message.text.lower() == messages[0]:
            bot.send_message(message.chat.id, "Вы выбрали поиск недорогих отелей. Введите город для поиска.", reply_markup=ReplyKeyboardRemove())
            result['sort_order_distance'] = False
            result['sort_order'] = 'PRICE_LOW_TO_HIGH'
        elif message.text.lower() == messages[1]:
            bot.send_message(message.chat.id, "Вы выбрали поиск дорогих отелей. Введите город для поиска.", reply_markup=ReplyKeyboardRemove())
            result['sort_order_distance'] = False
            result['sort_order'] = 'PRICE_HIGH_TO_LOW'
        else:
            bot.send_message(message.chat.id, "Вы выбрали поиск отелей, наиболее подходящих по цене и расположению от "
                                              "центра. Введите город для поиска.", reply_markup=ReplyKeyboardRemove())
            result['sort_order_distance'] = True
            result['sort_order'] = 'PRICE_LOW_TO_HIGH'
    from handlers.default_handlers.getter import get_city_handler
    bot.register_next_step_handler(message, get_city_handler)
