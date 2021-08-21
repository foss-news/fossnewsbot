import logging
from config import *
import requests
import json
import datetime
from argparse import ArgumentParser

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configure logging
logging.basicConfig(level=logging.INFO)

# parser = ArgumentParser(description='Process some integers.')
# parser.add_argument('-t', help='Bot token')
# parser.add_argument('-e', help='Endpoint')

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

categories = {'categories':['cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'cat6']}

subcategories = {'subcategories':['sub0','sub1','sub2','sub3','sub4','sub5','sub6','sub7','sub8','sub9','subA','subB','subC','subD','subE','subF']}

# Keyboard "In digest?"
digest_keyboard = InlineKeyboardMarkup()
digest_text = InlineKeyboardButton(text='Включаем в дайджест?', callback_data='digest_include')
digest_yes = InlineKeyboardButton(text='Да!', callback_data='digest_yes')
digest_no = InlineKeyboardButton(text='Нет!', callback_data='digest_no')
digest_unknown = InlineKeyboardButton(text='Не знаю', callback_data='digest_unknown')
digest_keyboard.add(digest_text)
digest_keyboard.row(digest_yes, digest_no)
digest_keyboard.row(digest_unknown)

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

news = {}

data = {
        'username': 'tbot',
        'password': 'GfdtkLehjd'
    }
token = json.loads(requests.post(ENDPOINT+'token/', data=data).text)['access']
print('FNGS TOKEN', token)
header = {
        'Authorization': 'Bearer '+token,
    }

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Hi!\nI'm FossNews Bot!", reply_markup=next_keyboard)
    data = {
        'tid': message.from_user.id,
        'username': message.from_user.username
    }
    print(data)
    print('Telegram Bot user:', requests.post(f'{ENDPOINT}telegram-bot-user/', data=data, headers=header).status_code)

@dp.callback_query_handler()
async def answer(callback: types.CallbackQuery):
    data = {}
    # result = {'in_digest':'', 'is_main':'', 'category':from_fngs['category'], 'subcategory':from_fngs['subcategory']}
    if callback.data == 'next_news':
        user_id = requests.get(
                f'{ENDPOINT}telegram-bot-user-by-tid?tid={callback.from_user.id}', headers=header).json()['id']
        print('Is bot?', callback.from_user.id, callback.from_user.username, callback.from_user.is_bot, user_id)
        news[callback.from_user.id] = requests.get(
                f'{ENDPOINT}telegram-bot-one-random-not-categorized-foss-news-digest-record/?tbot-user-id={str(user_id)}', headers=header).json()
        print(news[callback.from_user.id])
        await callback.message.edit_text(
            f"{news[callback.from_user.id][0]['title']}\n{news[callback.from_user.id][0]['url']}",
            reply_markup=digest_keyboard)

    # "In digest?" block
    elif callback.data == 'digest_include':
        await callback.answer(text='Включаем в дайджест?')
    elif callback.data == 'digest_yes':
        await callback.message.edit_text('Ответ принят', reply_markup=next_keyboard)
        user_id = requests.get(
            f'{ENDPOINT}telegram-bot-user-by-tid/?tid={callback.from_user.id}', headers=header).json()['id']
        data['telegram_bot_user'] = user_id
        data['estimated_state'] = 'IN_DIGEST'
        data['digest_record'] = news[callback.from_user.id][0]['id']
        data['dt'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')
    elif callback.data == 'digest_no':
        await callback.message.edit_text('Ответ принят', reply_markup=next_keyboard)
        user_id = requests.get(
            f'{ENDPOINT}telegram-bot-user-by-tid/?tid={callback.from_user.id}', headers=header).json()['id']
        data['telegram_bot_user'] = user_id
        data['estimated_state'] = 'IGNORED'
        data['digest_record'] = news[callback.from_user.id][0]['id']
        data['dt'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')
    elif callback.data == 'digest_unknown':
        await callback.message.edit_text('Ответ принят', reply_markup=next_keyboard)
        user_id = requests.get(
            f'{ENDPOINT}telegram-bot-user-by-tid/?tid={callback.from_user.id}', headers=header).json()['id']
        data['telegram_bot_user'] = user_id
        data['estimated_state'] = 'UNKNOWN'
        data['digest_record'] = news[callback.from_user.id][0]['id']
        data['dt'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')
    await callback.answer()
    if 'digest_' in callback.data:
        print(data)
        print(requests.post(f'{ENDPOINT}telegram-bot-digest-record-categorization-attempt/', headers=header, data=data).text)
        # TODO: add action to FNGS

    # iscat_keyboard = InlineKeyboardMarkup()
    # iscat_text = InlineKeyboardButton(text='Правильная категория?', callback_data='iscat_text')
    # iscat_current = InlineKeyboardButton(text=f"Текущая категория: {from_fngs['category']}", callback_data='iscat_current')
    # iscat_yes = InlineKeyboardButton(text='Да!', callback_data='iscat_yes')
    # iscat_no = InlineKeyboardButton(text='Нет!', callback_data='iscat_no')
    # iscat_keyboard.row(iscat_text)
    # iscat_keyboard.row(iscat_current)
    # iscat_keyboard.row(iscat_yes, iscat_no)
    #
    # # "Is main?" block
    # if callback.data == 'ismain_text':
    #     await callback.answer(text='На главную?')
    # elif callback.data == 'ismain_yes':
    #     await callback.answer(text='Спасибо!')
    #     result['is_main'] = 'yes'
    #     await callback.message.edit_reply_markup(reply_markup=iscat_keyboard)
    # elif callback.data == 'ismain_no':
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
    executor.start_polling(dp, skip_updates=True)