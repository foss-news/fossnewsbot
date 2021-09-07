#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8:
from datetime import datetime
from gettext import translation  # Do not import gettext as `_` explicitly! See comment below.
import logging
import locale
import re
import sys
from typing import Any, Union

from aiogram import Bot, Dispatcher, executor, md, types
from requests import RequestException

from config import config
from fngs import Fngs


MARKER_DATE = config.get('marker.date', '🗓')
MARKER_LANG = config.get('marker.lang', '🌏')
MARKER_CATEGORY = config.get('marker.category', '🗂')
MARKER_INCLUDE = config.get('marker.include', '✅')
MARKER_EXCLUDE = config.get('marker.exclude', '⛔️')
MARKER_UNKNOWN = config.get('marker.unknown', '🤷🏻‍♂️')
MARKER_MAIN = config.get('marker.main', '❗️')
MARKER_SHORT = config.get('marker.short', '📃')
MARKER_ERROR = config.get('marker.error', '🤔')
KBD_COLUMNS = config.get('keyboard.columns', 3)
URL_CHANNEL = config.get('url.channel', 'https://t.me/permlug')
URL_CHAT = config.get('url.chat', 'https://t.me/permlug_chat')
LOCALEDIR = config.get('localedir', 'locales')

LANGUAGES = ['en', 'ru']
TEXTDOMAIN = 'fossnewsbot'
LOG_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warn=logging.WARNING,
    warning=logging.WARNING,
    error=logging.ERROR,
    critical=logging.CRITICAL,
)
DIGEST_STATE = dict(
    yes='IN_DIGEST',
    no='IGNORED',
    unknown='UNKNOWN',
)
DATA_SEP = '|'
RESULT_YES = 'yes'
RESULT_NO = 'no'
RESULT_UNKNOWN = 'unknown'
RESULT_KEEP = '<keep>'
RE_CATEGORY = re.compile(fr'^({MARKER_CATEGORY}\s+[^:]+:\s+)(.*)$', re.MULTILINE)


log = logging.getLogger('fossnewsbot')
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s - %(message)s',
    level=LOG_LEVELS.get(config.get('log.level', 'info'), logging.INFO),
)

translations = {lang: translation(TEXTDOMAIN, localedir=LOCALEDIR, languages=[lang]) for lang in LANGUAGES}
# Function `_` is added to the global namespace by method `install`.
# Do not define or import `_` as an alias for `gettext`!
translations['en'].install()

fngs = Fngs(config.fngs.endpoint, config.fngs.username, config.fngs.password)
try:
    fngs.fetch_token()
except RequestException as ex:
    log.critical('Cannot fetch FNGS token: %s', ex)
    sys.exit(1)

bot = Bot(token=config.bot.token, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)


def set_lang(lang: str) -> None:
    try:
        locale.setlocale(locale.LC_ALL, lang)
    except locale.Error as e:
        log.warning("Cannot set locale '%s': %s", lang, e)
    translations.get(lang, translations['en']).install()


def to_callback_data(*data: Any) -> str:
    return DATA_SEP.join(map(str, data))


def from_callback_data(data: str) -> list:
    return data.split(DATA_SEP)


def kbd_next() -> types.InlineKeyboardMarkup:
    kbd = types.InlineKeyboardMarkup()
    btn_next = types.InlineKeyboardButton(text=_('Next'), callback_data='next')
    kbd.add(btn_next)
    return kbd


def kbd_ternary(question: str, name: str, news_id: int) -> types.InlineKeyboardMarkup:
    kbd = types.InlineKeyboardMarkup()
    kbd.row(types.InlineKeyboardButton(text=question, callback_data=to_callback_data('?', question)))
    kbd.row(
        types.InlineKeyboardButton(text=_('Yes'), callback_data=to_callback_data(name, news_id, RESULT_YES)),
        types.InlineKeyboardButton(text=_('No'), callback_data=to_callback_data(name, news_id, RESULT_NO)))
    kbd.row(types.InlineKeyboardButton(text=_("Don't know"), callback_data=to_callback_data(name, news_id, RESULT_UNKNOWN)))
    return kbd


def kbd_list(question: str, name: str, news_id: int, values: list, columns: int) -> types.InlineKeyboardMarkup:
    kbd = types.InlineKeyboardMarkup()
    kbd.row(types.InlineKeyboardButton(text=question, callback_data=to_callback_data('?', question)))
    kbd.row(types.InlineKeyboardButton(text=_('Keep'), callback_data=to_callback_data(name, news_id, RESULT_KEEP)))

    padded_values = values + [None] * (columns - 1)
    for row in zip(*[padded_values[i::columns] for i in range(columns)]):
        kbd.row(*[types.InlineKeyboardButton(text=v['name'], callback_data=to_callback_data(name, news_id, v['id'], v['name'])) for v in row if v])

    return kbd


def kbd_include(news_id: int) -> types.InlineKeyboardMarkup:
    return kbd_ternary(_('Include in digest?'), 'include', news_id)


def kbd_main(news_id: int) -> types.InlineKeyboardMarkup:
    return kbd_ternary(_('Include in main news?'), 'main', news_id)


def kbd_category(news_id: int, categories: list) -> types.InlineKeyboardMarkup:
    return kbd_list(_('Choose category'), 'category', news_id, categories, KBD_COLUMNS)


def format_lang(lang: str) -> str:
    langs = dict(ENGLISH=_('English'), RUSSIAN=_('Russian'))
    return langs.get(lang, _('Unknown'))


def format_news(news: dict) -> str:
    dt = datetime.strptime(news['dt'], '%Y-%m-%dT%H:%M:%S%z').strftime('%c')
    lang = format_lang(news['language'])
    category = news['subcategory'] if news['subcategory'] else _('Unknown')
    return md.text(
        md.link(news['title'], news['url']),
        md.text(MARKER_DATE + ' ', md.italic(_('Date')), md.escape_md(': '), md.bold(dt), sep=''),
        md.text(MARKER_LANG + ' ', md.italic(_('Language')), md.escape_md(': '), md.bold(lang), sep=''),
        md.text(MARKER_CATEGORY + ' ', md.italic(_('Category')), md.escape_md(':', category), sep=''),
        sep='\n')


def result(icon: str, msg: str) -> str:
    return '\n' + md.text(icon, md.bold(msg))


def replace_category(text: str, category: str) -> str:
    return RE_CATEGORY.sub(lambda m: m[1] + md.strikethrough(m[2]) + ' ' + md.bold(md.escape_md(category)), text, count=1)


def confirm_category(text: str) -> str:
    return RE_CATEGORY.sub(lambda m: m[1] + md.bold(m[2]), text, count=1)


async def msg_next(msg: Union[types.Message, types.CallbackQuery]) -> None:
    cb = None
    user = msg.from_user
    if isinstance(msg, types.CallbackQuery):
        cb = msg
        msg = cb.message
        user = cb.from_user

    news = fngs.fetch_news(user.id, user.username)
    if news:
        text = format_news(news)
        await bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=kbd_include(news['id']))
        if cb:
            await msg.delete_reply_markup()
            await cb.answer()
    else:
        text = _('No news yet.\nPlease, try again later.')
        if cb:
            await cb.answer(text=text)
        else:
            await msg.answer(text=md.escape_md(text))


async def not_implemented(command: str, message: types.Message) -> None:
    # All `.` and `!` must be escaped by backslashes
    await message.answer(_(
        'Command {command} is not implemented yet\.\n'
        'But I have it in my backlog\! 😉\n'
        'Please, check {channel} and {chat} for updates\.'
    ).format(
        command=md.code(command),
        channel=md.link(_('channel'), URL_CHANNEL),
        chat=md.link(_('chat'), URL_CHAT)
    ), reply_markup=kbd_next())


async def error(callback: types.CallbackQuery) -> None:
    # All `.` and `!` must be escaped by backslashes
    text = md.text(MARKER_ERROR, _(
        'Something went wrong\.\n'
        'Please, press {next} and try again\.'
    ).format(
        next=md.bold(_('Next'))
    ))
    await callback.message.edit_text(text=text, disable_web_page_preview=True)
    await callback.message.edit_reply_markup(kbd_next())
    await callback.answer()


@dp.message_handler(commands=['start'])
async def start(message: types.Message) -> None:
    user = message.from_user
    set_lang(user.locale.language)
    fngs.register_user(user.id, user.username)
    await message.answer(md.escape_md(_(
        "Hi! I'm FOSS News Bot!\n"
        "I can send you news articles so you can help to categorize them for a new digest."
    )), reply_markup=kbd_next())


@dp.message_handler(commands=['next'])
async def next_news(message: types.Message) -> None:
    set_lang(message.from_user.locale.language)
    await msg_next(message)


@dp.message_handler(commands=['add'])
async def add(message: types.Message) -> None:
    set_lang(message.from_user.locale.language)
    await not_implemented('add', message)


@dp.callback_query_handler()
async def handler(callback: types.CallbackQuery) -> None:
    user = callback.from_user
    user_id = user.id
    username = user.username
    text = callback.message.md_text
    no_preview = False

    set_lang(user.locale.language)

    try:
        data = from_callback_data(callback.data)
        if data[0] == 'next':
            await msg_next(callback)
            return

        elif data[0] == '?':
            log.info("user %i: pressed question button '%s'", user_id, data[1])
            await callback.answer(data[1])
            return

        elif data[0] == 'include':
            attempt_id = fngs.send_digest_data(user_id, username, int(data[1]), DIGEST_STATE.get(data[2], 'UNKNOWN'))
            if data[2] == RESULT_YES:
                text += result(MARKER_INCLUDE, _('In digest'))
                markup = kbd_main(attempt_id)
            else:
                if data[2] == RESULT_NO:
                    text += result(MARKER_EXCLUDE, _('Not in digest'))
                else:
                    text += result(MARKER_UNKNOWN, _('Skip'))
                markup = kbd_next()
                no_preview = True

        elif data[0] == 'main':
            fngs.update_digest_data(user_id, int(data[1]), 'is_main', data[2] == RESULT_YES)
            if data[2] == RESULT_YES:
                text += result(MARKER_MAIN, _('Main'))
            else:
                text += result(MARKER_SHORT, _('Short'))
            markup = kbd_category(int(data[1]), fngs.fetch_categories())

        elif data[0] == 'category':
            if data[2] != RESULT_KEEP:
                fngs.update_digest_data(user_id, int(data[1]), 'subcategory', data[2])
                text = replace_category(text, data[3])
            else:
                text = confirm_category(text)
            markup = kbd_next()

        else:
            await error(callback)
            return

    except RequestException as e:
        r = e.response
        log.error('response: %i %s: %s', r.status_code, r.reason, r.text)
        await error(callback)

    except Exception as e:
        log.error(e)
        await error(callback)

    else:
        await callback.message.edit_text(text=text, disable_web_page_preview=no_preview)
        await callback.message.edit_reply_markup(markup)
        await callback.answer()


if __name__ == '__main__':
    executor.start_polling(dp)
