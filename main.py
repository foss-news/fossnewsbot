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

from_fngs = {'link':'https://habr.com','id':'1','category':'news','subcategory':'source'}

categories = {'categories':['cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'cat6']}

subcategories = {'subcategories':['sub0','sub1','sub2','sub3','sub4','sub5','sub6','sub7','sub8','sub9','subA','subB','subC','subD','subE','subF']}

# Keyboard "In digest?"
digest_keyboard = InlineKeyboardMarkup()
digest_text = InlineKeyboardButton(text='Включаем в дайджест?', callback_data='digest_text')
digest_yes = InlineKeyboardButton(text='Да!', callback_data='digest_yes')
digest_no = InlineKeyboardButton(text='Нет!', callback_data='digest_no')
digest_keyboard.add(digest_text)
digest_keyboard.row(digest_yes, digest_no)

# Keyboard "Is main?"
ismain_keyboard = InlineKeyboardMarkup()
ismain_text = InlineKeyboardButton(text='На главную?', callback_data='ismain_text')
ismain_yes = InlineKeyboardButton(text='Да!', callback_data='ismain_yes')
ismain_no = InlineKeyboardButton(text='Нет!', callback_data='ismain_no')
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
    link = ''
    result = {'in_digest':'', 'is_main':'', 'category':from_fngs['category'], 'subcategory':from_fngs['subcategory']}
    if callback.data == 'next_news':
        # link = requests.get(ENDPOINT+f'/article?bot_user={callback.message.from_user.id}') + parsing
        link = 'https://habr.com'
        await callback.message.edit_text(f"Link: {from_fngs['link']}", reply_markup=digest_keyboard)

    # "In digest?" block
    elif callback.data == 'digest_text':
        await callback.answer(text='Включаем в дайджест?')
    elif callback.data == 'digest_yes':
        await callback.answer(text='Спасибо!')
        result['in_digest'] = 'yes'
        await callback.message.edit_reply_markup(reply_markup=ismain_keyboard)
        # TODO: add action to FNGS
    elif callback.data == 'digest_no':
        await callback.answer(text='Cпасибо!')
        result['in_digest'] = 'no'
        await callback.message.edit_text('Ответ принят', reply_markup=next_keyboard)
        # TODO: add action to FNGS

    iscat_keyboard = InlineKeyboardMarkup()
    iscat_text = InlineKeyboardButton(text='Правильная категория?', callback_data='iscat_text')
    iscat_current = InlineKeyboardButton(text=f"Текущая категория: {from_fngs['category']}", callback_data='iscat_current')
    iscat_yes = InlineKeyboardButton(text='Да!', callback_data='iscat_yes')
    iscat_no = InlineKeyboardButton(text='Нет!', callback_data='iscat_no')
    iscat_keyboard.row(iscat_text)
    iscat_keyboard.row(iscat_current)
    iscat_keyboard.row(iscat_yes, iscat_no)

    # "Is main?" block
    if callback.data == 'ismain_text':
        await callback.answer(text='На главную?')
    elif callback.data == 'ismain_yes':
        await callback.answer(text='Спасибо!')
        result['is_main'] = 'yes'
        await callback.message.edit_reply_markup(reply_markup=iscat_keyboard)
    elif callback.data == 'ismain_no':
        await callback.answer(text='Спасибо!')
        result['is_main'] = 'no'
        await callback.message.edit_reply_markup(reply_markup=iscat_keyboard)

    iscat_bad_keyboard = InlineKeyboardMarkup()
    iscat_bad_text = InlineKeyboardButton(text='Какая категория лучше подходит?', callback_data='iscat_bad_text')
    iscat_bad_keyboard.row(iscat_bad_text)
    for cat in categories['categories']:
        iscat_bad_keyboard.add(InlineKeyboardButton(text=cat, callback_data=cat))
    if callback.data == 'iscat_text':
        callback.answer(text='Правильная категория?')
    if callback.data in categories['categories']:
        result['category'] = callback.data

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)