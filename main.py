import json
import logging
import os
import sys
from argparse import ArgumentParser
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import fngsapi

IN_DIGEST = 'IN_DIGEST'
IGNORED = 'IGNORED'
UNKNOWN = 'UNKNOWN'

BTN_YES = 'Да!'
BTN_NO = 'Нет!'
BTN_UNKNOWN = 'Не знаю'

ANSWER = 'Ответ принят'

GREETING = "Hi!\nI'm FossNews Bot!"

# Configure logging
logging.basicConfig(level=logging.DEBUG)

news = {}

CACHE_FILE = './cache.json'
TOKEN = ''
API_PASS = ''
ENDPOINT = ''

parser = ArgumentParser(description='Foss News Gathering Server Telegram Bot')
parser.add_argument('-с', '--token',
                    help='Config file (default: ./config.json)', dest='CONFIG', type=str, default='./config.json')
args = parser.parse_args()

try:
    API_PASS = os.environ['FOSS_API_PASS']
    TOKEN = os.environ['FOSS_TOKEN']
    config = json.loads(open(args.CONFIG, 'r').read())
    ENDPOINT = config['endpoint']
except Exception as e:
    sys.exit('No config!')

if len(API_PASS) == 0 or len(TOKEN) == 0 or len(ENDPOINT) == 0:
    sys.exit('No config!')

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f_read:
        tmp_file = f_read.read()
        if len(tmp_file) != 0:
            news = json.loads(tmp_file)

fngs = fngsapi.FNGS(ENDPOINT, API_PASS)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Keyboard "In digest?"
digest_keyboard = InlineKeyboardMarkup()
digest_include = InlineKeyboardButton(text='Включаем в дайджест?', callback_data='digest_include')
digest_yes = InlineKeyboardButton(text=BTN_YES, callback_data='digest_yes')
digest_no = InlineKeyboardButton(text=BTN_NO, callback_data='digest_no')
digest_unknown = InlineKeyboardButton(text=BTN_UNKNOWN, callback_data='digest_unknown')
digest_keyboard.add(digest_include)
digest_keyboard.row(digest_yes, digest_no)
digest_keyboard.row(digest_unknown)

# Keyboard "Is main?"
is_main_keyboard = InlineKeyboardMarkup()
is_main_text = InlineKeyboardButton(text='На главную?', callback_data='is_main_include')
is_main_yes = InlineKeyboardButton(text=BTN_YES, callback_data='is_main_yes')
is_main_no = InlineKeyboardButton(text=BTN_NO, callback_data='is_main_no')
is_main_unknown = InlineKeyboardButton(text=BTN_UNKNOWN, callback_data='is_main_unknown')
is_main_keyboard.add(is_main_text)
is_main_keyboard.row(is_main_yes, is_main_no)
is_main_keyboard.row(is_main_unknown)

# Keyboard next
next_keyboard = InlineKeyboardMarkup()
next_btn = InlineKeyboardButton(text='Оценить следующую новость', callback_data='next_news')
next_keyboard.add(next_btn)

# Keyboard empty
empty_keyboard = InlineKeyboardMarkup()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(GREETING, reply_markup=next_keyboard)
    fngs.new_user(message.from_user.id, message.from_user.username)


@dp.callback_query_handler()
async def answer(callback: types.CallbackQuery):
    if callback.data == 'next_news':
        tmp_news = fngs.get_news_by_id(callback.from_user.id)
        if tmp_news != 'empty':
            news[callback.from_user.id] = tmp_news
            with open(CACHE_FILE, 'w') as f_write:
                f_write.write(json.dumps(news))
            await callback.message.edit_text(
                f"{news[callback.from_user.id]['title']}\n{news[callback.from_user.id]['url']}",
                reply_markup=digest_keyboard)
            await callback.answer()
        else:
            await callback.answer('Пока что новостей нет...\nЗаходите позже')

    # "In digest?" block
    if callback.data == 'digest_include':
        await callback.answer(text='Включаем в дайджест?')
    try:
        if callback.data == 'digest_yes':
            fngs.digest_send_data(callback.from_user.id, news[callback.from_user.id]['id'], IN_DIGEST)
        elif callback.data == 'digest_no':
            fngs.digest_send_data(callback.from_user.id, news[callback.from_user.id]['id'], IGNORED)
        elif callback.data == 'digest_unknown':
            fngs.digest_send_data(callback.from_user.id, news[callback.from_user.id]['id'], UNKNOWN)
    except KeyError as e:
        logging.debug(e)
        await callback.message.edit_text(ANSWER, reply_markup=next_keyboard)
    if 'digest_' in callback.data and callback.data != 'digest_include':
        del news[callback.from_user.id]
        with open(CACHE_FILE, 'w') as f_write:
            f_write.write(json.dumps(news))
        await callback.answer()
        await callback.message.edit_text(ANSWER, reply_markup=next_keyboard)

    # cat_keyboard = InlineKeyboardMarkup()
    # cat_text = InlineKeyboardButton(text='Правильная категория?', callback_data='cat_text')
    # cat_current = InlineKeyboardButton(text=f"Текущая категория: {from_fngs['category']}",
    #                                    callback_data='is_cat_current')
    # cat_yes = InlineKeyboardButton(text='Да!', callback_data='cat_yes')
    # cat_no = InlineKeyboardButton(text='Нет!', callback_data='cat_no')
    # cat_keyboard.row(cat_text)
    # cat_keyboard.row(cat_current)
    # cat_keyboard.row(cat_yes, cat_no)
    #
    # # "Is main?" block
    # if callback.data == 'is_main_text':
    #     await callback.answer(text='На главную?')
    # elif callback.data == 'is_main_yes':
    #     await callback.answer(text='Спасибо!')
    #     result['is_main'] = 'yes'
    #     await callback.message.edit_reply_markup(reply_markup=iscat_keyboard)
    # elif callback.data == 'is_main_no':
    #     await callback.answer(text='Спасибо!')
    #     result['is_main'] = 'no'
    #     await callback.message.edit_reply_markup(reply_markup=iscat_keyboard)
    #
    # iscat_bad_keyboard = InlineKeyboardMarkup()
    # iscat_bad_text = InlineKeyboardButton(text='Какая категория лучше подходит?', callback_data='iscat_bad_text')
    # iscat_bad_keyboard.row(iscat_bad_text)
    # for cat in categories['categories']:
    #     iscat_bad_keyboard.add(InlineKeyboardButton(text=cat, callback_data=cat))
    # if callback.data == 'iscat_text':
    #     await callback.answer(text='Правильная категория?')
    # if callback.data in categories['categories']:
    #     result['category'] = callback.data


if __name__ == '__main__':
    executor.start_polling(dp)
