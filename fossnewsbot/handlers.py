"""FOSS News Telegram Bot message handlers"""

#  Copyright (C) 2021 PermLUG
#
#  This file is part of fossnewsbot, FOSS News Telegram Bot.
#
#  fossnewsbot is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  fossnewsbot is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
from datetime import datetime
from typing import Union

from aiogram import Dispatcher, md
from aiogram.types import CallbackQuery, Message
from aiogram.utils.exceptions import CantParseEntities, InvalidQueryID
from requests import RequestException

from . import keyboards, log
from .core import bot, dispatcher, fngs
from .config import config
from .i18n import set_language
from .keyboards import Command, Result


DIGEST_STATE = {
    Result.YES: 'IN_DIGEST',
    Result.NO: 'IGNORED',
    Result.UNKNOWN: 'UNKNOWN',
}


def format_lang(lang: str) -> str:
    langs = dict(ENGLISH=_('English'), RUSSIAN=_('Russian'))
    return langs.get(lang, _('Unknown'))


def format_news(news: dict) -> str:
    dt = news['dt'] if news['dt'] else news['gather_dt']
    dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S%z').strftime('%x')
    lang = format_lang(news['language'])
    keywords = ', '.join([md.bold(k['name']) for k in news['title_keywords'] if not k['is_generic']])
    lines = [
        md.text(config.marker.count + ' ', md.italic(_('News left')), md.escape_md(': '), md.bold(news['count']), '\n', sep=''),
        md.link(news['title'], news['url']),
        md.text(config.marker.date + ' ', md.italic(_('Date')), md.escape_md(': '), md.bold(dt), sep=''),
        md.text(config.marker.lang + ' ', md.italic(_('Language')), md.escape_md(': '), md.bold(lang), sep=''),
    ]
    if keywords:
        lines.append(md.text(config.marker.keywords + ' ', md.italic(_('Keywords')), md.escape_md(': '), keywords, sep=''),)
    if config.features.types:
        type_ = news['category'] if news['category'] else _('Unknown')
        lines.append(md.text(config.marker.type + ' ', md.italic(_('Type')), md.escape_md(':', type_), sep=''))
    if config.features.categories:
        category = news['subcategory'] if news['subcategory'] else _('Unknown')
        lines.append(md.text(config.marker.category + ' ', md.italic(_('Category')), md.escape_md(':', category), sep=''))
    return md.text(*lines, sep='\n')


def update_text_attr(text: str, marker: str, value: str = None) -> str:
    def replace(m: re.Match) -> str:
        return m[1] + md.strikethrough(m[2]) + ' ' + md.bold(md.escape_md(value))

    def confirm(m: re.Match) -> str:
        return m[1] + md.bold(m[2])

    return re.sub(
        pattern=fr'^({marker}\s+[^:]+:\s+)(.*)$',
        repl=replace if value else confirm,
        string=text, count=1, flags=re.MULTILINE)


def append_result(icon: str, msg: str) -> str:
    return '\n' + md.text(icon, md.bold(msg))


async def msg_next(msg: Union[Message, CallbackQuery]) -> None:
    cb = None
    user = msg.from_user
    if isinstance(msg, CallbackQuery):
        cb = msg
        msg = cb.message
        user = cb.from_user

    news = fngs.fetch_news(user)
    if news:
        news['count'] = fngs.fetch_news_count(user)
        text = format_news(news)
        await bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=keyboards.include(news['id']))
        if cb:
            await msg.delete_reply_markup()
            await cb.answer()
    else:
        text = _('No news yet.\nPlease, try again later.')
        if cb:
            await cb.answer(text=text)
        else:
            await msg.answer(text=md.escape_md(text))


async def not_implemented(command: str, message: Message) -> None:
    # All `.` and `!` must be escaped by backslashes
    await message.answer(_(
        'Command {command} is not implemented yet\.\n'
        'But I have it in my backlog\! 😉\n'
        'Please, check {channel} and {chat} for updates\.'
    ).format(
        command=md.code(command),
        channel=md.link(_('channel'), config.url.channel),
        chat=md.link(_('chat'), config.url.chat)
    ), reply_markup=keyboards.next_news())


async def error(callback: CallbackQuery) -> None:
    # All `.` and `!` must be escaped by backslashes
    text = md.text(config.marker.error, _(
        'Something went wrong\.\n'
        'Please, press {next} and try again\.'
    ).format(
        next=md.bold(_('Next'))
    ))
    await callback.message.edit_text(text=text, disable_web_page_preview=True)
    await callback.message.edit_reply_markup(keyboards.next_news())
    await callback.answer()


@dispatcher.message_handler(commands=['start'])
async def start(message: Message) -> None:
    user = fngs.fetch_user(message.from_user)
    set_language(user.lang)
    await message.answer(md.escape_md(_(
        "Hi! I'm FOSS News Bot!\n"
        "I can send you news articles so you can help to categorize them for a new digest."
    )), reply_markup=keyboards.next_news())


@dispatcher.message_handler(commands=['next'])
async def next_news(message: Message) -> None:
    user = fngs.fetch_user(message.from_user)
    set_language(user.lang)
    await msg_next(message)


@dispatcher.message_handler(commands=['add'])
async def add(message: Message) -> None:
    user = fngs.fetch_user(message.from_user)
    set_language(user.lang)
    await not_implemented('add', message)


@dispatcher.callback_query_handler()
async def handler(callback: CallbackQuery) -> None:
    user = fngs.fetch_user(callback.from_user)
    text = callback.message.md_text
    markup = callback.message.reply_markup
    no_preview = False

    set_language(user.lang)

    try:
        cmd, news_id, result, value = keyboards.from_callback_data(callback.data)
        if cmd == Command.NEXT:
            await msg_next(callback)
            return

        elif cmd == Command.QUESTION:
            log.info("%s pressed question button '%s' for news_id=%i", user, value, news_id)
            await callback.answer(value)
            return

        elif cmd == Command.INCLUDE:
            attempt_id = fngs.send_attempt(user, news_id, DIGEST_STATE.get(result, 'UNKNOWN'))
            if result == Result.YES:
                text += append_result(config.marker.include, _('In digest'))
                if config.features.is_main or user.is_admin() or user.is_editor():
                    markup = keyboards.is_main(attempt_id)
                else:
                    keyboards.next_news()
            else:
                if result == result.NO:
                    text += append_result(config.marker.exclude, _('Not in digest'))
                else:
                    text += append_result(config.marker.unknown, _('Skip'))
                markup = keyboards.next_news()
                no_preview = True

        elif cmd == Command.IS_MAIN:
            fngs.update_attempt(user, news_id, 'is_main', result == Result.YES)
            if result == Result.YES:
                text += append_result(config.marker.is_main, _('Main'))
            else:
                text += append_result(config.marker.short, _('Short'))
            if config.features.types or user.is_admin() or user.is_editor():
                markup = keyboards.types(news_id, fngs.types, user.lang)
            else:
                markup = keyboards.next_news()

        elif cmd == Command.TYPE:
            if result == Result.SET:
                fngs.update_attempt(user, news_id, 'category', value)
                text = update_text_attr(text, config.marker.type, fngs.types[value][user.lang])
            else:
                text = update_text_attr(text, config.marker.type)
            if config.features.categories or user.is_admin() or user.is_editor():
                markup = keyboards.categories(news_id, fngs.categories, user.lang)
            else:
                markup = keyboards.next_news()

        elif cmd == Command.CATEGORY:
            if result == Result.SET:
                fngs.update_attempt(user, news_id, 'subcategory', value)
                text = update_text_attr(text, config.marker.category, fngs.categories[value][user.lang])
            else:
                text = update_text_attr(text, config.marker.category)
            markup = keyboards.next_news()

        else:
            await error(callback)
            return

    except (CantParseEntities, InvalidQueryID) as e:
        log.error(e)  # TODO: implement a better handling of a such kind of exceptions

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


async def on_startup(dp: Dispatcher):
    log.info('Starting up...')
    await bot.set_webhook(config.webhook.base + config.webhook.path)


async def on_shutdown(dp: Dispatcher):
    log.info('Shutting down...')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    log.info('Bye!')
