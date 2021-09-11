"""Inline reply keyboards for FOSS News Telegram Bot"""

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

from enum import Enum, unique
from typing import Optional, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .config import config


@unique
class Command(Enum):
    QUESTION = '?'
    NEXT = 'next'
    INCLUDE = 'include'
    IS_MAIN = 'is_main'
    TYPE = 'type'
    CATEGORY = 'category'


@unique
class Result(Enum):
    UNKNOWN = '?'
    YES = 'yes'
    NO = 'no'
    KEEP = 'keep'
    SET = '='


_DATA_SEP = ' '


def to_callback_data(cmd: Command, news_id: int = None, result: Result = None, value: str = None) -> str:
    data = cmd.value
    if news_id is not None:
        data += _DATA_SEP + str(news_id)
        if result is not None:
            data += _DATA_SEP + result.value
            if value is not None:
                data += _DATA_SEP + value

    return data


def from_callback_data(data: str) -> Tuple[Command, Optional[int], Optional[Result], Optional[str]]:
    d = data.split(_DATA_SEP)
    d += [None] * (4 - len(d))

    cmd = Command(d[0])
    news_id = int(d[1]) if d[1] else None
    result = Result(d[2]) if d[2] else None
    value = d[3]

    return cmd, news_id, result, value


def btn_question(question: str, news_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=question, callback_data=to_callback_data(Command.QUESTION, news_id, Result.UNKNOWN, question))


def _ternary(question: str, cmd: Command, news_id: int) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    kbd.row(btn_question(question, news_id))
    kbd.row(
        InlineKeyboardButton(text=_('Yes'), callback_data=to_callback_data(cmd, news_id, Result.YES)),
        InlineKeyboardButton(text=_('No'), callback_data=to_callback_data(cmd, news_id, Result.NO)))
    kbd.row(InlineKeyboardButton(text=_("Don't know"), callback_data=to_callback_data(cmd, news_id, Result.UNKNOWN)))

    return kbd


def _from_dict(question: str, cmd: Command, news_id: int, values: dict, lang: str = 'en',
               columns: int = 3) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    kbd.row(btn_question(question, news_id))
    kbd.row(InlineKeyboardButton(text=_('Keep'), callback_data=to_callback_data(cmd, news_id, Result.KEEP)))

    padded = list(values.keys()) + [None] * (columns - 1)
    for row in zip(*[padded[i::columns] for i in range(columns)]):
        kbd.row(*[InlineKeyboardButton(text=values[k][lang], callback_data=to_callback_data(cmd, news_id, Result.SET, k)) for k in row if k])

    return kbd


def next_news() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    btn_next = InlineKeyboardButton(text=_('Next'), callback_data='next')
    kbd.add(btn_next)

    return kbd


def include(news_id: int) -> InlineKeyboardMarkup:
    return _ternary(_('Include in digest?'), Command.INCLUDE, news_id)


def is_main(news_id: int) -> InlineKeyboardMarkup:
    return _ternary(_('Include in main news?'), Command.IS_MAIN, news_id)


def types(news_id: int, types_: dict, lang: str = 'en') -> InlineKeyboardMarkup:
    return _from_dict(_('Choose type'), Command.TYPE, news_id, types_, lang, config.keyboard.columns)


def categories(news_id: int, categories_: dict, lang: str = 'en') -> InlineKeyboardMarkup:
    return _from_dict(_('Choose category'), Command.CATEGORY, news_id, categories_, lang, config.keyboard.columns)
