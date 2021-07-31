"""
This is a echo bot.
It echoes any incoming text messages.
"""

import logging
import config

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

links = ['url1','url2','url3']

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!")

@dp.message_handler(commands=['url'])
async def echo(message: types.Message):
    button_yes = KeyboardButton('Да!')
    button_no = KeyboardButton('Нет!')
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(button_yes)
    keyboard.add(button_no)

    await message.answer(message.text, reply_markup=keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)