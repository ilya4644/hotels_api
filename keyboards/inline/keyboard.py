from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def start_keyboard():
    buttons = [
        KeyboardButton(text="Низкая цена"),
        KeyboardButton(text="Высокая цена"),
        KeyboardButton(text="Лучшее предложение")
    ]
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row_width = 3
    markup.add(*buttons)
    return markup
