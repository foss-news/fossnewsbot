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

categories = ['cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'cat6']

# Keyboard "In digest?"
digest_text = InlineKeyboardButton(text='Включаем в дайджест?', callback_data='digest_text')
digest_yes = InlineKeyboardButton(text='Да!', callback_data='digest_yes')
digest_no = InlineKeyboardButton(text='Нет!', callback_data='digest_no')
digest_keyboard = InlineKeyboardMarkup()
digest_keyboard.add(digest_text)
digest_keyboard.row(digest_yes, digest_no)

# Keyboard "Is main?"
ismain_text = InlineKeyboardButton(text='На главную?', callback_data='ismain_text')
ismain_yes = InlineKeyboardButton(text='Да!', callback_data='ismain_yes')
ismain_no = InlineKeyboardButton(text='Нет!', callback_data='ismain_no')
ismain_keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
ismain_keyboard.add(ismain_text)
ismain_keyboard.row(ismain_yes, ismain_no)

# Keyboard next
next_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Оценить новую новость', callback_data='next_news'))

# Keyboard empty
empty_keyboard = InlineKeyboardMarkup()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Hi!\nI'm FossNews Bot!", reply_markup=next_keyboard)

@dp.callback_query_handler()
async def answer(callback: types.CallbackQuery):
    if callback.data == 'next_news':
        # link = requests.get(ENDPOINT+f'/article?bot_user={callback.message.from_user.id}') + parsing
        link = 'https://habr.com'
        message_text = f'Link: {link}'
        await callback.message.edit_text(message_text, reply_markup=digest_keyboard)

    # "In digest?" block
    elif callback.data == 'digest_text':
        await callback.answer(text='Включаем в дайджест?')
    elif callback.data == 'digest_yes':
        await callback.answer(text='Спасибо!')
        await callback.message.edit_reply_markup(reply_markup=ismain_keyboard)
        # TODO: add action to FNGS
    elif callback.data == 'digest_no':
        await callback.answer(text='Cпасибо!')
        await callback.message.edit_text('Ответ принят', reply_markup=next_keyboard)
        # TODO: add action to FNGS

    # "Is main?" block
    elif callback.data == 'ismain_text':
        await callback.answer(text='На главную?')
    elif callback.data == 'ismain_yes':
        await callback.answer(text='Спасибо!')
    elif callback.data == 'ismain_no':
        await callback.answer(text='Спасибо!')
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)