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

ENDPOINT = 'https://habr.com' # TODO: replace to url from @gim6626

# Keyboard for answer
button_yes = InlineKeyboardButton(text='Да!', callback_data='yes')
button_no = InlineKeyboardButton(text='Нет!', callback_data='no')
keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
keyboard.insert(button_yes)
keyboard.insert(button_no)

# Keyboard after answer
empty_keyboard = InlineKeyboardMarkup()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm FossNews Bot!\n\nSend /url to get Link")

@dp.message_handler(commands=['url'])
async def echo(message: types.Message):
    link = 'https://habr.com'
    # link = requests.get(ENDPOINT)

    message_text = f'Link: {link}\n\nВключаем в дайджест?'

    await message.answer(message_text, reply_markup=keyboard)

@dp.callback_query_handler()
async def answer(callback: types.CallbackQuery):
    if callback.data == 'yes':
        await callback.answer(text='Спасибо!')
        await callback.message.edit_reply_markup(reply_markup=empty_keyboard)
        # TODO: add action to FNGS

    elif callback.data == 'no':
        await callback.answer(text='Cпасибо')
        await callback.message.edit_reply_markup(reply_markup=empty_keyboard)
        # TODO: add action to FNGS

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)