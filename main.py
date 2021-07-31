"""
This is a echo bot.
It echoes any incoming text messages.
"""

import logging
import config
import requests

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

ENDPOINT = 'https://habr.com'

button_yes = InlineKeyboardButton(text='Да!', callback_data='yes')
button_no = InlineKeyboardButton(text='Нет!', callback_data='no')
keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
keyboard.insert(button_yes)
keyboard.insert(button_no)

empty_keyboard = InlineKeyboardMarkup()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!")

@dp.message_handler(commands=['url'])
async def echo(message: types.Message):
    link = 'https://habr.com'

    message_text = f'Link: {link}\n\nВключаем в дайджест?'

    await message.answer(message_text, reply_markup=keyboard)

@dp.callback_query_handler()
async def answer(callback: types.CallbackQuery):
    if callback.data == 'yes':
        await callback.answer(text='Спасибо!')
        await callback.message.edit_reply_markup(reply_markup=empty_keyboard)

    elif callback.data == 'no':
        await callback.answer(text='Cпасибо')
        await callback.message.edit_reply_markup(reply_markup=empty_keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)