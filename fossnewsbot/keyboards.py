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

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import config


__all__ = ['next_news', 'include', 'main', 'types', 'categories', 'from_callback_data', 'YES', 'NO', 'KEEP']

YES = 'yes'
NO = 'no'
UNKNOWN = '?'
KEEP = '<keep>'

_DATA_SEP = '|'


def to_callback_data(*data: Any) -> str:
    return _DATA_SEP.join(map(str, data))


def from_callback_data(data: str) -> list:
    return data.split(_DATA_SEP)


def _ternary(question: str, name: str, news_id: int) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    kbd.row(InlineKeyboardButton(text=question, callback_data=to_callback_data('?', question)))
    kbd.row(
        InlineKeyboardButton(text=_('Yes'), callback_data=to_callback_data(name, news_id, YES)),
        InlineKeyboardButton(text=_('No'), callback_data=to_callback_data(name, news_id, NO)))
    kbd.row(
        InlineKeyboardButton(text=_("Don't know"), callback_data=to_callback_data(name, news_id, UNKNOWN)))

    return kbd


def _from_dict(question: str, name: str, id_: int, values: dict, lang: str = 'en', columns: int = 3) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    kbd.row(InlineKeyboardButton(text=question, callback_data=to_callback_data('?', question)))
    kbd.row(InlineKeyboardButton(text=_('Keep'), callback_data=to_callback_data(name, id_, KEEP)))

    padded = list(values.keys()) + [None] * (columns - 1)
    for row in zip(*[padded[i::columns] for i in range(columns)]):
        kbd.row(*[InlineKeyboardButton(text=values[k][lang], callback_data=to_callback_data(name, id_, k)) for k in row if k])

    return kbd


def next_news() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardMarkup()
    btn_next = InlineKeyboardButton(text=_('Next'), callback_data='next')
    kbd.add(btn_next)

    return kbd


def include(news_id: int) -> InlineKeyboardMarkup:
    return _ternary(_('Include in digest?'), 'include', news_id)


def main(news_id: int) -> InlineKeyboardMarkup:
    return _ternary(_('Include in main news?'), 'main', news_id)


def types(news_id: int, types_: dict, lang: str = 'en') -> InlineKeyboardMarkup:
    return _from_dict(_('Choose type'), 'type', news_id, types_, lang, config.keyboard.columns)


def categories(news_id: int, categories_: dict, lang: str = 'en') -> InlineKeyboardMarkup:
    return _from_dict(_('Choose category'), 'category', news_id, categories_, lang, config.keyboard.columns)
