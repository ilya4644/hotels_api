from telebot import TeleBot
from telebot.storage import StateMemoryStorage
import config_data
import logging

logging.basicConfig(level=logging.ERROR)
logging.debug('The debug message is logged')

storage = StateMemoryStorage()
bot = TeleBot(token=config_data.config.BOT_TOKEN, state_storage=storage)

